"""
Streamlit front-end for the market-intelligence deep agent.

    uv run streamlit run 02_deep_agent_market_intel/streamlit_app.py

The agent architecture lives in market_intel.py -- this file is only UI. That
separation matters: you can test the pipeline without Streamlit, and swap the UI
without touching the agent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))

from market_intel import MODEL_CHOICES, build_pipeline, research_request  # noqa: E402
from research_tools import SANDBOX, ensure_sandbox  # noqa: E402

load_dotenv(override=True)  # finds .env in this folder, or any parent

st.set_page_config(page_title="Market Intelligence Agent", page_icon="📊", layout="wide")

# --------------------------------------------------------------------------
# Sidebar — configuration
# --------------------------------------------------------------------------
with st.sidebar:
    st.title("📊 Market Intelligence")
    st.caption("A deep agent with 3 subagents and a fact-checking critic loop.")

    st.subheader("Models")
    lead_label = st.selectbox("Lead (coordinator)", list(MODEL_CHOICES), index=0)
    worker_label = st.selectbox(
        "Subagents (researchers/writer/critic)",
        list(MODEL_CHOICES),
        index=0,
        help="A cheaper model here is a real cost lever — the coordinator does the thinking, "
        "the subagents do the volume.",
    )

    max_rounds = st.slider(
        "Max revision rounds", 0, 4, 2,
        help="Cap on the writer ↔ fact-checker loop. Always bound this — an unbounded "
        "critic loop can burn a lot of money.",
    )

    st.subheader("What to analyse")
    market = st.text_input("Market", value="Indian quick-commerce")
    companies_raw = st.text_area(
        "Companies (one per line)",
        value="Zepto\nBlinkit\nSwiggy Instamart",
        height=110,
    )
    companies = [c.strip() for c in companies_raw.splitlines() if c.strip()]

    st.divider()
    st.caption(f"Sandbox: `{SANDBOX.name}/`")
    if st.button("🗑️ Clear previous run", use_container_width=True):
        removed = 0
        for sub in ("output", "research"):
            for f in (SANDBOX / sub).glob("*"):
                if f.is_file():
                    f.unlink()
                    removed += 1
        st.success(f"Deleted {removed} file(s)")

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
st.title("Competitive Intelligence Report Generator")

if not companies:
    st.warning("Add at least one company in the sidebar.")
    st.stop()

st.markdown(
    f"**{market}** — comparing {', '.join(f'`{c}`' for c in companies)}  \n"
    f"Pipeline: `write_todos` → **{len(companies)}× competitor-researcher** → "
    f"**report-writer** *(analyst-report skill)* → **fact-checker** "
    f"→ up to **{max_rounds}** revision round(s)"
)

run = st.button("▶️ Run analysis", type="primary", use_container_width=True)

OUTPUT_PATH = "/output/market_report.md"

if run:
    ensure_sandbox()
    pipeline = build_pipeline(
        model=MODEL_CHOICES[lead_label],
        worker_model=MODEL_CHOICES[worker_label],
        max_rounds=max_rounds,
    )

    prompt = research_request(companies, market, OUTPUT_PATH)
    log_box = st.container()
    counters = {"searches": 0, "delegations": 0, "writes": 0}

    with st.status("Agent running… this takes several minutes", expanded=True) as status:
        final = None
        try:
            for chunk in pipeline.stream(
                {"messages": [{"role": "user", "content": prompt}]},
                config={"recursion_limit": 250},
                stream_mode="values",
            ):
                final = chunk
                msg = chunk["messages"][-1]

                for call in getattr(msg, "tool_calls", None) or []:
                    name, args = call["name"], call["args"]

                    if name == "write_todos":
                        lines = []
                        for todo in args.get("todos", []):
                            mark = {"completed": "✅", "in_progress": "⏳"}.get(todo.get("status"), "⬜")
                            lines.append(f"{mark} {todo.get('content')}")
                        log_box.markdown("**Plan**\n\n" + "\n\n".join(lines))

                    elif name == "task":
                        counters["delegations"] += 1
                        log_box.markdown(
                            f"🔀 **delegate → `{args.get('subagent_type')}`** — "
                            f"{str(args.get('description'))[:90]}"
                        )

                    elif name == "internet_search":
                        counters["searches"] += 1
                        log_box.markdown(f"🔎 `{args.get('query')}`")

                    elif name in ("write_file", "edit_file"):
                        counters["writes"] += 1
                        log_box.markdown(f"💾 `{args.get('file_path')}`")

                status.update(label="✅ Analysis complete", state="complete", expanded=False)
        except Exception as e:  # noqa: BLE001
            status.update(label=f"❌ Failed: {type(e).__name__}", state="error")
            st.exception(e)
            st.stop()

    c1, c2, c3 = st.columns(3)
    c1.metric("Delegations", counters["delegations"])
    c2.metric("Searches", counters["searches"])
    c3.metric("Files written", counters["writes"])

    if final:
        st.markdown("### Lead agent's summary")
        st.info(final["messages"][-1].content)

# --------------------------------------------------------------------------
# Results — always shown, so you can browse a previous run too
# --------------------------------------------------------------------------
st.divider()

report_file = SANDBOX / "output" / "market_report.md"
research_files = sorted((SANDBOX / "research").glob("*.md")) if (SANDBOX / "research").exists() else []
factchecks = [f for f in research_files if f.name.startswith("factcheck")]
sources = [f for f in research_files if not f.name.startswith("factcheck")]

tab_report, tab_research, tab_check = st.tabs(
    [f"📄 Report", f"🔬 Research ({len(sources)})", f"✅ Fact-check ({len(factchecks)})"]
)

with tab_report:
    if report_file.exists():
        text = report_file.read_text(encoding="utf-8")
        st.download_button("⬇️ Download report", text, file_name="market_report.md",
                           mime="text/markdown")
        st.markdown(text)
    else:
        st.info("No report yet — run an analysis.")

with tab_research:
    if not sources:
        st.info("No research files yet.")
    for f in sources:
        with st.expander(f"{f.name}  ({f.stat().st_size / 1024:.1f} KB)"):
            st.markdown(f.read_text(encoding="utf-8"))

with tab_check:
    if not factchecks:
        st.info("No fact-check reports yet.")
    for f in factchecks:
        with st.expander(f.name, expanded=True):
            st.markdown(f.read_text(encoding="utf-8"))
