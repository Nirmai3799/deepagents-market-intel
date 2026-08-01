---
name: analyst-report
description: House style and required structure for a competitive intelligence report. Use this whenever writing a final client-facing report or market analysis document to /output/. Do not use it for raw research notes.
---

# Analyst Report — House Style

## Required structure

Every report follows this exact section order. Do not add, remove, or reorder sections.

```markdown
# <Market> — Competitive Intelligence Report
*Prepared <YYYY-MM-DD> · Sources as of <YYYY-MM-DD>*

## 1. Executive Summary
## 2. Market Overview
## 3. Competitor Profiles
## 4. Comparative Analysis
## 5. Strategic Outlook
## 6. Confidence & Limitations
## 7. Sources
```

## Section rules

**1. Executive Summary** — Exactly 3–5 bullets. Each bullet states a *conclusion*, not a topic.
Write "Blinkit leads on dark-store density but at the worst unit economics of the three", not
"Discussion of dark-store density". A reader who stops here must still get the answer.

**2. Market Overview** — Size, growth rate, structural dynamics. Two paragraphs maximum.

**3. Competitor Profiles** — One `###` subsection per company, each covering business model,
scale/financials, positioning, and key risk. Keep every profile to the same depth: uneven depth
reads as bias.

**4. Comparative Analysis** — Must open with a Markdown table:

| Company | Business model | Funding / valuation | Market position | Key risk |
|---|---|---|---|---|

Then 3–5 numbered findings that are only visible *by comparison*. A fact about one company alone
does not belong here.

**5. Strategic Outlook** — Who is best positioned, and why. Commit to a view and give the reasoning
chain. Include what would have to change for you to be wrong.

**6. Confidence & Limitations** — State plainly what you could not verify, where the data is stale,
and which claims rest on a single source. This section is mandatory and must never be empty.

**7. Sources** — Numbered list of every URL used, each with a one-line note on what it supported.

## Evidence rules

- Every number carries an inline citation marker `[n]` mapping to section 7.
- Any figure you could not confirm is written as `[unverified]`. Never silently drop it, and never
  present it as fact.
- Separate **fact** from **inference** in the prose. "Revenue grew 40% [3]" is a fact;
  "which suggests the discounting strategy is working" is inference — mark it as such.
- Never estimate a number the sources did not state. Write `[not disclosed]`.

## Tone

Direct and specific. No hedging filler ("it is important to note that"), no marketing adjectives
("revolutionary", "game-changing"), no bullet lists longer than 7 items. Prefer concrete numbers to
qualitative descriptions wherever a number exists.
