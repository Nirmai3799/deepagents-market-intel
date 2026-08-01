# Competitive Market Intelligence Agent

A multi-agent research system. Name a market and some companies; it researches each one, writes a
structured analyst report, then **fact-checks its own report against the sources** and revises it
until the claims hold up.

Built with **DeepAgents** (LangChain / LangGraph). Ships with a Streamlit UI.

---

## The problem

Competitive research is slow, and naive automation of it fails in a specific, predictable way.

Point a single LLM agent at "research these five competitors and write me a report" and it breaks:

- **Context exhaustion.** Every web-search result stays in the conversation. By competitor four
  it's carrying thousands of tokens of irrelevant history, and quality collapses.
- **No plan.** It wanders, repeats searches, and forgets what it already covered.
- **Nowhere to put work.** Findings have to live in the context window because there's no disk.
- **Hallucinated citations.** It writes confident numbers with plausible-looking sources, and
  nothing checks them.

Each of those has a specific architectural fix, and this project is built around the four.

---

## What it produces

A 7-section analyst report, every claim carrying a source URL, plus the raw research files behind it
and the fact-checker's audit trail:

```
sandbox/
├── research/
│   ├── zepto.md              raw findings, one file per company
│   ├── blinkit.md
│   ├── swiggy_instamart.md
│   └── factcheck_1.md        the critic's audit of the draft
└── output/
    └── market_report.md      the deliverable
```

The report follows a house style enforced by an **Agent Skill**, including a mandatory
*"Confidence & Limitations"* section — so what the agent *couldn't* verify is stated rather than
quietly omitted.

---

## Architecture

```
                        lead agent  (coordinates only — keeps a clean context)
                             │
      ┌──────────────────────┼──────────────────────┐
      │                      │                      │
competitor-researcher   report-writer          fact-checker
  × N, one per company   follows the            adversarial;
  context-quarantined    analyst-report SKILL   has its own search tool
      │                      │                      │
      ▼                      ▼                      │
/research/<company>.md   /output/report.md  ◄───────┘
                                        FAIL → revise (max 2 rounds)
```

The lead **never sees raw search results**. Each researcher burns its own context window on
searches, writes findings to disk, and returns a short summary. That is *context quarantine*, and
it's the single most important idea here.

---

## Quick start

```powershell
uv sync                          # installs deps + Python 3.12
copy .env.example .env           # then paste your API keys into .env
uv run python check_setup.py     # verifies keys with live API calls

uv run streamlit run streamlit_app.py     # the UI
```

You need an **Anthropic** (or OpenAI) key and a **[Tavily](https://tavily.com)** key — Tavily has a
free tier and is the web-search backend.

To learn how it works, run the notebooks in order:

```powershell
uv run jupyter lab 1_deep_agent_basics.ipynb    # Parts 1-2
uv run jupyter lab 3_skills_and_critic.ipynb    # Part 3
```

> **VS Code users:** select the kernel **`Python (agents-projects)`** (top-right).

---

## How it works — step by step

### Part 1 — What makes an agent "deep"

`create_deep_agent` is a normal agent plus a built-in harness. You write one tool
(`internet_search`); it supplies nine more:

| Capability | Built-in tools | Fixes |
|---|---|---|
| **Planning** | `write_todos` | Wandering, repeated work |
| **Filesystem** | `ls` `read_file` `write_file` `edit_file` `glob` `grep` | Context exhaustion |
| **Shell** | `execute` | — |
| **Delegation** | `task` | Context exhaustion (Part 2) |
| **Skills** | `SKILL.md` folders | Prompt bloat (Part 3) |

```python
create_deep_agent(
    model=MODEL,
    tools=[internet_search],
    system_prompt=RESEARCHER_PROMPT,
    backend=FilesystemBackend(root_dir=SANDBOX, virtual_mode=True),
)
```

**The system prompt must explicitly tell it to use the filesystem.** A deep agent that isn't told
to write files just answers in chat, and you gain nothing.

#### ⚠️ `virtual_mode=True` is not optional

On `deepagents 0.4.11` this argument defaults to `None`, which behaves as `False`:

| | `virtual_mode=False` (the default) | `virtual_mode=True` (what we use) |
|---|---|---|
| `/output/x.md` | writes to your **real filesystem root** | writes to `sandbox/output/x.md` |
| `../../secrets` | **escapes the sandbox** | blocked |

Always pass it explicitly. (It's a guardrail, not a container — don't hand an agent tools you'd be
unhappy to see misused.)

### Part 2 — Subagents and context quarantine

The notebook deliberately runs three companies through a *single* agent first, so you can watch the
context bloat happen. Then it fixes it.

A subagent is a dict:

```python
{
    "name": "competitor-researcher",
    "description": "Researches ONE company in depth and writes /research/<company>.md. "
                   "Delegate one call per company — never two companies in one call.",
    "system_prompt": "...",
    "model": MODEL,      # optional — can differ from the lead's
}
```

The **`description` is a prompt, not documentation** — the lead reads it to decide whether to
delegate. Make it vague and the lead does the work itself, and you lose the entire benefit.

Because `model` is per-subagent, a cheap worker model with a smart coordinator is a real cost
lever.

### Part 3 — Skills and the critic loop

**Skills = progressive disclosure.** A skill is a folder containing a `SKILL.md`:

```
sandbox/skills/
├── analyst-report/SKILL.md     report structure + evidence rules
└── swot-analysis/SKILL.md      a rigorous, non-generic SWOT method
```

At startup the agent sees only each skill's `name` + `description` — about 15 tokens. When it
judges one relevant it reads the full file itself. So a 2,000-word style guide costs nothing until
it's needed, and you can have twenty skills without drowning the context window.

```python
create_deep_agent(..., skills=["/skills/"])
```

> ⚠️ **Skills fail silently.** The `name:` in the YAML frontmatter must match the parent folder
> name exactly, and the frontmatter must parse. Get either wrong and the skill is skipped with only
> a log warning. Verify — the notebook has a cell that checks this.

**The critic loop.** Nothing so far verifies anything: the agent writes *"revenue grew 40% [3]"*
and we take its word. Self-review doesn't help — an agent checking its own work is reading its own
reasoning and already believes the claim.

So the `fact-checker` is a separate subagent with a **fresh context** and **its own search tool**.
It re-reads the report cold, extracts every claim, checks it against the research files, and
independently spot-checks the most load-bearing numbers. Two design choices make it work:

1. **It gets `internet_search`.** Without it, it can only confirm a URL is *present*, not that it
   *supports the claim* — that's a formatting linter, not a fact-checker.
2. **It's told to default to FAIL when unsure.** A critic that wants to approve is worthless.

On FAIL, the issues go back to `report-writer` for revision, then re-check — **capped at 2 rounds**.
Always bound a critic loop; a strict critic and a stubborn writer will otherwise ping-pong until
they hit the recursion limit.

### Part 4 — The UI

[streamlit_app.py](streamlit_app.py) wraps the pipeline. It streams the agent's plan, delegations,
searches, and file writes live, then presents the report, research files, and fact-check audit in
tabs.

The sidebar sets **lead** and **subagent** models independently, and the revision-round cap.

The UI imports `build_pipeline()` from [market_intel.py](market_intel.py) — the agent architecture
is defined in exactly one place, so it's testable without Streamlit and the UI is swappable.

---

## Project layout

| File | Role |
|---|---|
| [1_deep_agent_basics.ipynb](1_deep_agent_basics.ipynb) | Parts 1–2 — deep agents, filesystem, subagents |
| [3_skills_and_critic.ipynb](3_skills_and_critic.ipynb) | Part 3 — skills, fact-checker loop |
| [market_intel.py](market_intel.py) | The pipeline: 3 subagents + `build_pipeline()` |
| [streamlit_app.py](streamlit_app.py) | UI only — imports the pipeline |
| [research_tools.py](research_tools.py) | The one custom tool + `show_tools()` / `run_agent()` debug helpers |
| `sandbox/skills/*/SKILL.md` | `analyst-report`, `swot-analysis` |
| `sandbox/output/`, `sandbox/research/` | Agent-generated (git-ignored) |

---

## Adapting it

**Different domain** — the architecture is domain-agnostic. Swap the subagent prompts and the
`SKILL.md` files and the same lead/researcher/writer/critic shape works for due diligence, academic
literature review, or vendor evaluation.

**More rigour** — add a `financial-analyst` subagent, or a second critic with a different lens
(a completeness critic that asks "what's missing?" catches different failures than a fact-checker).

**New output format** — write a new `SKILL.md`. No code change, no redeploy. That's the payoff of
skills.

---

## Notes on cost

The full pipeline runs three researchers, a writer, a fact-checker, and possibly revision rounds —
that's a lot of model calls.

| Model | $/1M in | $/1M out | Use for |
|---|---|---|---|
| `claude-haiku-4-5` | $1 | $5 | Rehearsing — output is worse, machinery identical |
| `claude-sonnet-5` | $3 | $15 | Default |
| `claude-opus-5` | $5 | $25 | Best reasoning |

Rehearse on Haiku before spending on Sonnet. Optionally enable LangSmith tracing in `.env` to see
exactly where the tokens go.

## Version pinning

`deepagents` is pinned to **exactly** `0.4.11`, not `>=`. Its defaults change between minor
versions in ways that fail silently:

- On **0.7.x**, `write_todos` is no longer auto-included for Anthropic models — your agent loses
  its planning tool with no error. (Fix: `middleware=[TodoListMiddleware()]`.)
- `FilesystemBackend(virtual_mode=...)` changed default in **0.5.0**.

A `>=` constraint would silently give a future reader a different agent than the one that was
tested. Hence `show_tools()` — print an agent's tool list rather than assuming it.

## Stack

Python 3.12 · uv · deepagents 0.4.11 · langchain 1.3 · langgraph 1.2 · Tavily · Streamlit ·
Anthropic / OpenAI
