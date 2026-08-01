"""
Run this first:   uv run python check_setup.py

Verifies that (a) the packages installed at the right versions and (b) each API
key in .env actually works. Fix anything marked [FAIL] before running the agent.
"""

import os

from dotenv import load_dotenv

load_dotenv(override=True)

OK, BAD, WARN = "[ OK ]", "[FAIL]", "[WARN]"

PINNED_DEEPAGENTS = "0.4.11"


def check_packages() -> bool:
    try:
        import deepagents
        import langchain
        from deepagents import create_deep_agent  # noqa: F401

        print(f"{OK} langchain {langchain.__version__}")
        version = deepagents.__version__
        if version == PINNED_DEEPAGENTS:
            print(f"{OK} deepagents {version}")
        else:
            print(f"{WARN} deepagents {version} (expected {PINNED_DEEPAGENTS})")
            print("      Defaults differ between versions -- see README 'Version pinning'.")
            print("      On 0.7.x you also need middleware=[TodoListMiddleware()] for write_todos.")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"{BAD} package import failed: {e}")
        return False


def check_key(name: str, required: bool = True) -> bool:
    """A key counts as present only if set and not still a placeholder."""
    value = os.getenv(name, "")
    if not value or value.endswith("..."):
        marker = BAD if required else WARN
        suffix = "" if required else " (optional)"
        print(f"{marker} {name} not set in .env{suffix}")
        return False
    print(f"{OK} {name} found ({value[:8]}...{value[-4:]})")
    return True


def check_anthropic() -> None:
    from langchain_anthropic import ChatAnthropic

    try:
        reply = ChatAnthropic(model="claude-haiku-4-5", max_tokens=64).invoke(
            "Reply with exactly: pong"
        )
        print(f"{OK} Anthropic call succeeded -> {reply.content!r}")
    except Exception as e:  # noqa: BLE001
        print(f"{BAD} Anthropic call failed: {type(e).__name__}: {e}")


def check_tavily() -> None:
    from langchain_tavily import TavilySearch

    try:
        results = TavilySearch(max_results=1).invoke({"query": "what is an AI agent"})
        n = len(results.get("results", [])) if isinstance(results, dict) else 0
        print(f"{OK} Tavily search succeeded -> {n} result(s)")
    except Exception as e:  # noqa: BLE001
        print(f"{BAD} Tavily call failed: {type(e).__name__}: {e}")


def check_skills() -> None:
    """Skills fail SILENTLY if the frontmatter name != folder name."""
    import re
    from pathlib import Path

    skills_dir = Path(__file__).parent / "sandbox" / "skills"
    found = sorted(skills_dir.glob("*/SKILL.md")) if skills_dir.exists() else []
    if not found:
        print(f"{WARN} no skills found under sandbox/skills/")
        return

    for skill_md in found:
        folder = skill_md.parent.name
        text = skill_md.read_text(encoding="utf-8")
        fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
        if not fm:
            print(f"{BAD} skill {folder!r}: no YAML frontmatter -- will be silently skipped")
            continue
        match = re.search(r"^name:\s*(.+)$", fm.group(1), re.M)
        name = match.group(1).strip() if match else ""
        if name == folder:
            print(f"{OK} skill {folder!r} valid")
        else:
            print(f"{BAD} skill {folder!r}: frontmatter name is {name!r} -- must match the "
                  f"folder name or the skill is silently skipped")


if __name__ == "__main__":
    print("=" * 60)
    print("1. PACKAGES")
    print("=" * 60)
    if not check_packages():
        raise SystemExit("Packages are broken -- run `uv sync` again.")

    print("\n" + "=" * 60)
    print("2. KEYS IN .env")
    print("=" * 60)
    has_anthropic = check_key("ANTHROPIC_API_KEY")
    has_tavily = check_key("TAVILY_API_KEY")
    check_key("OPENAI_API_KEY", required=False)

    print("\n" + "=" * 60)
    print("3. LIVE API CALLS")
    print("=" * 60)
    if has_anthropic:
        check_anthropic()
    if has_tavily:
        check_tavily()

    print("\n" + "=" * 60)
    print("4. AGENT SKILLS")
    print("=" * 60)
    check_skills()

    print("\nDone. Everything must say [ OK ] before you start.")
