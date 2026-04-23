---
name: skill-l3-gap-audit
description: L3 Study — gap_audit subplane. Actively find hidden assumptions, unstated approximations, and missing correspondence checks.
trigger: l3_subplane == "gap_audit" AND l3_mode == "study"
---

# Gap Audit (Study Mode)

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question, you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

You are auditing the source for gaps: hidden assumptions, unstated approximations, missing correspondence checks, and prerequisite knowledge gaps.

## Active artifact

`L3/gap_audit/active_gaps.md`

## What to do

Run the following audit checklist:

### 1. Unstated Assumptions
- What does the author assume without explicitly stating?
- Are there implicit symmetry assumptions? Gauge choices? Coordinate choices?
- Is there an unstated hierarchy of scales (e.g., "heavy field integrated out")?

### 2. Approximation Regimes
- For each approximation found in step_derive:
  - Is the regime of validity explicitly stated?
  - Is there a quantitative error estimate?
  - What happens at the boundary of the regime?

### 3. Correspondence Check (MOST IMPORTANT)
- For each result in the source:
  - Does it reduce to a known result in an appropriate limit?
  - Use `aitp_query_l2` to check if the limiting case exists in L2
  - If the limiting case is NOT in L2, flag it as a prerequisite gap
- If the paper does NOT do this check, that itself is a gap

### 4. Prerequisite Gaps
- For each concept/technique the paper uses:
  - Is it defined or derived in the paper?
  - If referenced: is it in L2? If not, flag as prerequisite gap
  - If the prerequisite is non-trivial and missing, note it for future study

### 5. Severity Assessment
For each gap found, assign severity:
- `blocking`: prevents understanding the paper's conclusions
- `important`: affects correctness of some claims
- `minor`: cosmetic or clarity issue
- `future_work`: interesting but not required for this study

Fill the artifact:
- `gap_count`: total gaps found
- `blocking_gaps`: comma-separated list of blocking gap descriptions (or "none")
- `## Unstated Assumptions`: list with severity
- `## Approximation Regimes`: each approximation + regime status
- `## Correspondence Check`: each result + limiting behavior + L2 status
- `## Prerequisite Gaps`: missing prerequisites with L2 status
- `## Severity Assessment`: summary table

## Quality gate

- All five checklist items are addressed (even if empty)
- Every gap has a severity level
- Correspondence check is attempted for every major result

## Flow Notebook — Incremental Update

Update `L3/tex/flow_notebook.tex`:
- Add gap audit findings to the **Gap Audit** section
- Flag any blocking gaps that need resolution

## Exit condition

Advance to **synthesis** when:
- `gap_count` is filled (can be 0)
- `blocking_gaps` is assessed (can be "none")
- Correspondence check section has entries for every major result
- All blocking gaps have a resolution plan or are deferred with reason

## Allowed transitions

- Forward: `synthesis`
- Backedges: `step_derive` (if gaps reveal derivation was incomplete)
