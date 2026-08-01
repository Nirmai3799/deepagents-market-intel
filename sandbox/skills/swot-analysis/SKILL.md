---
name: swot-analysis
description: Method for producing a rigorous, non-generic SWOT analysis of a company. Use when asked for a SWOT, a strengths/weaknesses breakdown, or a structural assessment of competitive position. Skip for simple company summaries.
---

# SWOT — the version that isn't useless

Most SWOTs are four lists of vague adjectives. This method produces one a strategist would act on.

## The two rules that matter

**1. Internal vs external is not negotiable.**
Strengths and Weaknesses are things the company *controls*. Opportunities and Threats exist in the
world whether the company acts or not.

- "Strong brand" → Strength (they built it)
- "Growing market" → Opportunity (it grew regardless of them)
- A common error: putting "competition is intense" under Weaknesses. It's a Threat.

**2. Every entry needs evidence and a "so what".**
Format each entry as:

```
- <Claim> — <evidence with source [n]> → <consequence>
```

Example:

```
- Highest dark-store density in metros — 1,000+ stores vs Zepto's ~700 [4] → structurally
  lower delivery cost per order in exactly the markets that drive profitability
```

Reject any entry you cannot write this way. "Good technology" with no evidence and no consequence
is filler — delete it.

## Quality bar

| Test | Fails if... |
|---|---|
| **Specificity** | The entry would apply to any company in the sector. "Strong team" fails. |
| **Falsifiability** | There's no observation that could disprove it. |
| **Asymmetry** | It's true of every competitor equally — then it's market context, not a strength. |
| **Evidence** | No source. Mark `[unverified]` rather than deleting, so the gap is visible. |

## Sizing

3–5 entries per quadrant. Fewer means you didn't research enough; more means you didn't prioritise.
Order each quadrant by materiality, most consequential first.

## Required output

```markdown
## SWOT — <Company>

### Strengths (internal, advantageous)
### Weaknesses (internal, disadvantageous)
### Opportunities (external, advantageous)
### Threats (external, disadvantageous)

### The strategic tension
<2-4 sentences: which weakness most endangers their biggest opportunity, or which threat
most exploits their biggest weakness. This is the part a strategist actually reads.>
```

The **strategic tension** section is mandatory. A SWOT without it is a list, not an analysis.
