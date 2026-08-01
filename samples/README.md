# Sample output

Real, unedited artefacts from a single pipeline run — so you can see what the system produces
without spending anything to run it.

**Run configuration:** market *Indian quick-commerce*, companies *Zepto* and *Blinkit*, model
`claude-haiku-4-5` for both lead and subagents, revision rounds capped at 1.

| File | What it is | Written by |
|---|---|---|
| [terminal_output.txt](terminal_output.txt) | The live delegation trail | lead agent |
| [zepto.md](zepto.md) · [blinkit.md](blinkit.md) | Raw research, one file per company | `competitor-researcher` ×2 |
| [market_report.md](market_report.md) | The deliverable — 7 sections, 49 citations | `report-writer` |
| [factcheck_1.md](factcheck_1.md) | First audit — **verdict: FAIL** | `fact-checker` |
| [factcheck_revised.md](factcheck_revised.md) | Re-audit after revision — all issues resolved | `fact-checker` |

## Why the fact-check files are the interesting part

The first audit **rejected** the draft. It didn't just check that citations existed — it
recalculated figures against the underlying research and caught errors the writer had introduced:

> **ISSUE #1: Mathematical Error in Revenue Growth Claim — CRITICAL**
> **Claim:** "Revenue has grown 4.8x since FY24 to ₹22,623.58 crore in FY26"
> **Actual Calculation:** 22,623.58 ÷ 4,454.52 = **5.08x**, NOT 4.8x
> Both `zepto.md` and the report cite the exact same revenue figures; the multiplier is
> mathematically wrong.

> **ISSUE #2: Zepto Valuation Timeline Error — CRITICAL**
> **Claim:** "from $3.6B to $7B in 12 months"
> Series E: $3.6B, June 2024. Series G: $7B, October 2025. **Actual duration: 16 months**,
> not 12. Confirmed by independent search (The Hindu, CNBC TV18, Outlook Business).

Those issues went back to `report-writer`, and the re-audit confirmed each fix. That loop — a
critic with a fresh context, its own web search, and instructions to reject when uncertain — is
what separates this from a research agent that simply sounds confident.

## Honest caveats

- Generated with the **cheapest** model to keep the demo affordable. `claude-sonnet-5` produces
  noticeably better analysis.
- `factcheck_1.md` carries a hallucinated header date (*"January 15, 2026"*). The agent was not
  given a date tool — a real gap, and exactly the kind of thing the Project 1 `get_today` tool
  exists to solve.
- Figures are only as good as what Tavily surfaced on the day of the run. The report's
  *Confidence & Limitations* section documents 10 gaps it could not close, which is the intended
  behaviour rather than a shortcoming.
