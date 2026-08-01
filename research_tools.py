"""
The ONE custom tool our deep agent needs: web search.

Everything else it uses -- write_todos, ls, read_file, write_file, edit_file,
glob, grep, task -- is built into deepagents. That is the whole point of the
library: you supply domain tools, it supplies the harness.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from langchain_core.tools import tool
from langchain_tavily import TavilySearch

# The agent's whole world lives under here. FilesystemBackend anchors to it,
# so when the agent writes "/output/report.md" it really lands in
# 02_deep_agent_market_intel/sandbox/output/report.md
SANDBOX = Path(__file__).parent / "sandbox"


@tool
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> dict:
    """Search the web and return results with titles, URLs, and content snippets.

    Use this for every factual claim about a company: revenue, funding, product
    launches, market share, leadership changes, pricing.

    Args:
        query: A specific, targeted search query. Prefer "Zomato Q3 2026 revenue"
            over "Zomato information" -- narrow queries return far better results.
        max_results: How many results to return (1-10). Use 3 for a quick check,
            8 when researching something in depth.
        topic: "news" for recent events and announcements, "finance" for
            financial and market data, "general" for everything else.
        include_raw_content: Set True to get the full page text instead of just a
            snippet. Use sparingly -- it consumes a lot of context.
    """
    return TavilySearch(
        max_results=max_results,
        topic=topic,
        include_raw_content=include_raw_content,
    ).invoke({"query": query})


def ensure_sandbox() -> Path:
    """Create the sandbox folders the agent expects. Safe to call repeatedly."""
    (SANDBOX / "output").mkdir(parents=True, exist_ok=True)
    (SANDBOX / "research").mkdir(parents=True, exist_ok=True)
    (SANDBOX / "skills").mkdir(parents=True, exist_ok=True)
    return SANDBOX


def show_tools(agent, label: str = "agent") -> list[str]:
    """Print the tools an agent actually exposes.

    Get in the habit of calling this on every agent you build. The available tool
    set varies by deepagents version and by model profile -- `write_todos`, for
    instance, is automatic on deepagents 0.4.x but not on 0.7.x. Verify, never assume.
    """
    names = sorted({t.name for t in agent.nodes["tools"].bound._tools_by_name.values()})
    print(f"{label} exposes {len(names)} tools:")
    print("   " + ", ".join(names))
    return names


def run_agent(agent, prompt: str, recursion_limit: int = 150):
    """Stream an agent run, printing each tool call as it happens.

    `.invoke()` gives you a black box; `.stream()` lets you watch the agent think.
    This is the single most useful debugging habit for agents.
    """
    final = None
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": prompt}]},
        config={"recursion_limit": recursion_limit},
        stream_mode="values",
    ):
        final = chunk
        msg = chunk["messages"][-1]

        for call in getattr(msg, "tool_calls", None) or []:
            name, args = call["name"], call["args"]
            if name == "write_todos":
                print("\n  PLAN:")
                for todo in args.get("todos", []):
                    mark = {"completed": "x", "in_progress": ">"}.get(todo.get("status"), " ")
                    print(f"    [{mark}] {todo.get('content')}")
            elif name == "task":
                print(f"  DELEGATE -> {args.get('subagent_type')}: {str(args.get('description'))[:65]}")
            elif name == "internet_search":
                print(f"  SEARCH   -> {args.get('query')}")
            elif name in ("write_file", "edit_file"):
                print(f"  {name.upper():9}-> {args.get('file_path')}")
            elif name == "read_file":
                print(f"  READ     -> {args.get('file_path')}")
            else:
                print(f"  {name:9}-> {str(args)[:65]}")
    return final


def show_tree(root: Path | None = None, prefix: str = "") -> None:
    """Print the sandbox as a tree, so you can SEE what the agent produced."""
    root = root or SANDBOX
    if not root.exists():
        print(f"(nothing at {root})")
        return
    entries = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name))
    for i, entry in enumerate(entries):
        last = i == len(entries) - 1
        branch = "\\-- " if last else "|-- "
        if entry.is_dir():
            print(f"{prefix}{branch}{entry.name}/")
            show_tree(entry, prefix + ("    " if last else "|   "))
        else:
            kb = entry.stat().st_size / 1024
            print(f"{prefix}{branch}{entry.name}  ({kb:.1f} KB)")
