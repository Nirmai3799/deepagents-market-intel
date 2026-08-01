"""
The market-intelligence pipeline, extracted from the notebooks into one module.

Notebooks are for learning; this is the thing you'd actually ship. Both
`streamlit_app.py` and any script import `build_pipeline()` from here, so the
agent architecture is defined in exactly one place.

Architecture:

    lead (coordinator, clean context)
     |-- competitor-researcher   x N, one per company, context-quarantined
     |-- report-writer           follows the analyst-report SKILL
     \\-- fact-checker            adversarial, has its own search tool
"""

from __future__ import annotations

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from research_tools import SANDBOX, ensure_sandbox, internet_search

DEFAULT_MODEL = "anthropic:claude-sonnet-5"

MODEL_CHOICES = {
    "Claude Sonnet 5 (balanced - recommended)": "anthropic:claude-sonnet-5",
    "Claude Haiku 4.5 (cheapest - for testing)": "anthropic:claude-haiku-4-5",
    "Claude Opus 5 (best reasoning - priciest)": "anthropic:claude-opus-5",
    "GPT-5.4 mini (OpenAI)": "openai:gpt-5.4-mini",
}


# --------------------------------------------------------------------------
# Subagents. Each is a plain dict -- see deepagents.SubAgent for the schema.
# The `description` is what the LEAD reads when deciding whether to delegate,
# so it is prompt engineering, not documentation.
# --------------------------------------------------------------------------

def _competitor_researcher(model: str) -> dict:
    return {
        "name": "competitor-researcher",
        "description": (
            "Researches ONE company in depth and writes /research/<company>.md. "
            "Delegate one call per company -- never two companies in one call. "
            "Returns a short summary plus the file path."
        ),
        "system_prompt": """You research exactly ONE company, thoroughly.

Run at least 4 internet_search calls from different angles: business model,
funding/financials, market position, and risks.

Write to /research/<company_lowercase>.md with sections:
  # <Company> / ## Business model / ## Financials & funding / ## Market position / ## Risks / ## Sources

Put the source URL inline next to every single claim. If you could not confirm
something, write [unverified] -- never guess a number.

FINAL REPLY: 5-8 bullets of key findings plus the file path. Keep it short --
the detail belongs in the file, not in your reply.""",
        "model": model,
    }


def _report_writer(model: str) -> dict:
    return {
        "name": "report-writer",
        "description": (
            "Writes the final client-facing report from existing /research/ files, following the "
            "analyst-report house style. Use AFTER all research is done. Can also revise an "
            "existing report when given fact-checker issues to fix."
        ),
        "system_prompt": """You write the final report.

1. FIRST read /skills/analyst-report/SKILL.md in full and follow it exactly.
   Its structure is mandatory -- do not invent your own sections.
2. Read every file in /research/ with read_file. Those are your only facts.
3. Write the report to the path you were given.

Never introduce a fact that is not in the research files. If the research says
[unverified], your report says [unverified] too -- do not upgrade uncertainty
into confidence.

If you were given fact-checker issues, fix EVERY one and say what you changed.""",
        "model": model,
    }


def _fact_checker(model: str) -> dict:
    return {
        "name": "fact-checker",
        "description": (
            "Adversarially verifies a finished report: checks every claim is sourced and that "
            "sources actually support the claims. Returns PASS or FAIL with a numbered issue "
            "list. Use after report-writer, before showing anything to the user."
        ),
        "system_prompt": """You are an adversarial fact-checker. Your job is to BREAK the report,
not to approve it. A critic who wants to approve is useless.

Given a report path:
1. read_file the report.
2. read_file the /research/ files it was built from.
3. Extract every quantitative or factual claim.
4. For each one check:
   - Is there a source URL?
   - Does the research file actually support it, or was it embellished?
   - Is inference being presented as fact?
   - Was an [unverified] item quietly upgraded to a confident claim?
5. Use internet_search to independently spot-check the 3 most load-bearing numbers.
   Checking that a URL merely EXISTS is not fact-checking.
6. Confirm the report has all 7 required sections from the analyst-report skill,
   including a non-empty "Confidence & Limitations".

Write your findings to /research/factcheck_<n>.md.

FINAL REPLY format -- exactly this:

VERDICT: PASS   (or)   VERDICT: FAIL
ISSUES:
1. <section> - <what is wrong> - <what would fix it>
2. ...

Default to FAIL when you are unsure. Only PASS when every claim is sourced and
supported, and the structure is complete.""",
        # Give the critic its own search tool -- without it, it can only check that
        # a URL is PRESENT, not that it supports the claim. That's a linter, not a critic.
        "tools": [internet_search],
        "model": model,
    }


def lead_prompt(max_rounds: int = 2) -> str:
    return f"""You are the lead analyst. You COORDINATE; you do not research or write.

## Pipeline -- follow exactly
1. write_todos with your plan.
2. RESEARCH: one `task` to competitor-researcher per company. Send them in the
   same turn so they run concurrently. Do NOT call internet_search yourself.
3. WRITE: one `task` to report-writer, telling it the output path.
4. VERIFY: one `task` to fact-checker with the report path.
5. If the verdict is FAIL: send the issues back to report-writer to fix, then
   re-run fact-checker.
   HARD LIMIT: at most {max_rounds} revision rounds. After that, accept the report
   and record the unresolved issues in its "Confidence & Limitations" section.
6. Report to the user: the final path, the verdict, and how many rounds it took.

Keep your own replies short. The detail lives in the files.
"""


def build_pipeline(
    model: str = DEFAULT_MODEL,
    worker_model: str | None = None,
    max_rounds: int = 2,
):
    """Assemble the full pipeline.

    Args:
        model: Model for the lead coordinator.
        worker_model: Model for the subagents. Defaults to `model`. Setting this
            to a cheaper model is a real cost lever -- smart coordinator,
            cheap workers.
        max_rounds: Cap on writer <-> fact-checker revision rounds. ALWAYS bound
            this; an unbounded critic loop can burn a lot of money.
    """
    ensure_sandbox()
    workers = worker_model or model

    return create_deep_agent(
        model=model,
        tools=[internet_search],
        system_prompt=lead_prompt(max_rounds),
        subagents=[
            _competitor_researcher(workers),
            _report_writer(workers),
            _fact_checker(workers),
        ],
        # virtual_mode=True is important: on deepagents 0.4.11 it defaults to
        # None (== False), which would let the agent write outside the sandbox.
        backend=FilesystemBackend(root_dir=SANDBOX, virtual_mode=True),
        skills=["/skills/"],
    )


def research_request(companies: list[str], market: str, output_path: str) -> str:
    """Build the user-facing prompt for a run."""
    listed = ", ".join(companies)
    return (
        f"Produce a competitive intelligence report on the {market} market, "
        f"covering {listed}. Write it to {output_path}."
    )
