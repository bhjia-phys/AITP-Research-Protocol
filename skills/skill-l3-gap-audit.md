---
name: skill-l3-gap-audit
description: L3 Gap Audit — find hidden assumptions, unstated approximations, missing correspondence checks, and prerequisite gaps. HARD PREREQUISITE for integrate and distill — gate blocks advance without completed gap-audit content.
trigger: l3_activity == "gap-audit"
---

# Gap Audit

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question, you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

## Entry Profile Detection

Check the execution brief for `entry_profile`:
- **`explore_idea`** → Scenario A: audit own derivation
- **`learn_paper`** → Scenario B: audit a paper's derivation
Both use the same 5-step checklist below, with different emphasis.

---

You are auditing for gaps. This applies equally to two scenarios:

**A. Novel derivation** — after deriving a result, audit assumptions, approximations,
regime boundaries, correspondence to known limits.

**B. Source study** — after tracing a paper's derivation, audit unstated assumptions,
prerequisite gaps, internal inconsistencies, regime mismatches.

## Active artifact

`L3/gap-audit/active_gaps.md`

## Pre-Audit: Map the derivation

Before auditing, understand the current state:

1. Check available inference rules:
   ```
   aitp_list_inference_rules(topics_root)
   ```
   Steps using rules not in the registry are automatically gapped.

2. Traverse the derivation to find blocking steps:
   ```
   aitp_traverse_derivation(topics_root, topic_slug)
   ```
   Steps marked as `non_auditable` or with missing dependencies are your
   audit starting points.

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
  - Use `aitp_query_l2_graph` to check if the limiting case exists in L2
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

### 6. Lane-Specific Checks (explore_idea only)

**formal_theory lane** — additionally audit:
- Axiom closure: are all starting postulates listed?
- Ward identity satisfaction: for gauge theories
- Analytic structure preservation: does each step preserve retarded/advanced analyticity?
- Regularization independence: does the result survive regulator removal?
- Sign/chirality convention consistency

**code_method lane** — additionally audit:
- Compilation completeness on target machine
- Numerical sanity (order-of-magnitude estimates)
- Convergence with respect to all relevant parameters

Fill the artifact:
- `gap_count`: total gaps found
- `blocking_gaps`: comma-separated list of blocking gap descriptions (or "none")
- `## Unstated Assumptions`: list with severity
- `## Approximation Regimes`: each approximation + regime status
- `## Correspondence Check`: each result + limiting behavior + L2 status
- `## Prerequisite Gaps`: missing prerequisites with L2 status
- `## Severity Assessment`: summary table

## Requesting Missing Evidence

If a gap can only be filled with additional source material (a paper section
you haven't downloaded, a code file you haven't traced, a derivation step
the source handwaves):

```
aitp_request_source_evidence(
    topics_root, topic_slug,
    required_claim="<what equation/statement needs support>",
    required_regime="<under what conditions>",
    reason="<why this gap is blocking>",
)
```

This creates a pending request in `L0/pending_requests/` that will be picked
up on the next L0 pass. The execution brief shows pending requests so the
agent knows to resolve them.

## Quality gate

- All five checklist items are addressed (even if empty)
- Every gap has a severity level
- Correspondence check is attempted for every major result
- Blocking gaps that need source evidence have requests filed

## L3→L1 Feedback (MANDATORY)

If gap audit discovers **blocking** or **important** gaps that L1 should have caught:
- New convention/notation not in `convention_snapshot.md` → call `aitp_feedback_to_l1` with `feedback_kind="convention"`
- Source contradiction or internal inconsistency → call `aitp_feedback_to_l1` with `feedback_kind="contradiction"`
- Cross-source dependency not in `source_cross_map.md` → call `aitp_feedback_to_l1` with `feedback_kind="cross_edge"`

**Never skip this.** Even if no gaps found, record that fact with a brief note.

## Exit condition

Advance to **integrate** when:
- `gap_count` is filled (can be 0)
- `blocking_gaps` is assessed (can be "none")
- `completion_status` is set to `complete` (gate reports `blocked_incomplete` otherwise)
- Correspondence check section has entries for every major result
- All blocking gaps have a resolution plan or are deferred with reason

## Retreat Decision Tree (MANDATORY for blocking gaps)

When gap-audit discovers **blocking** gaps, the agent MUST route to the appropriate
retreat action. Do NOT just record the gap and continue — blocking gaps require
a concrete resolution plan with a stage transition.

### Decision rules:

1. **Missing source material** (key paper not in L0, code file not traced, equation from unregistered source):
   → `aitp_retreat_to_l0(reason="gap-audit: <specific gap>")`
   → Register the missing source, parse its TOC, extract relevant sections
   → Return to L3: `aitp_advance_to_l3` will restore the gap-audit position

2. **Wrong framing or missing conventions** (notation ambiguity, contradictory convention, missing question scope):
   → `aitp_retreat_to_l1(reason="gap-audit: <specific framing issue>", retreat_feedback_kind="convention", retreat_feedback="<detail>")`
   → Revise L1 artifacts (convention_snapshot, question_contract, contradiction_register)
   → Return to L3: `aitp_advance_to_l3` restores gap-audit position

3. **Derivation incomplete** (missing steps, unjustified leaps, steps with `gap_marker` set):
   → Backedge to `derive` via `aitp_switch_l3_activity(activity="derive")`
   → Fix the derivation, re-record steps with proper justification
   → Return to gap-audit: `aitp_switch_l3_activity(activity="gap-audit")`

4. **Correspondence check fails** (result doesn't match known limit in L2):
   → Query L2 more thoroughly: `aitp_query_l2(query="<limit>")`
   → If L2 has contradictory evidence → file contradiction: `aitp_record_contradiction(...)`
   → If L2 knowledge insufficient → mark as `important`, proceed with caution, flag for human review
   → If derivation is wrong → backedge to `derive` (rule 3)

5. **Prerequisite gap** (technique/concept not in L2 and not derivable from L1 sources):
   → `aitp_request_source_evidence(required_claim="<prerequisite>", reason="<why blocking>")`
   → This creates a pending request visible in execution brief
   → If the prerequisite is critical, treat as missing source material (rule 1)

### After retreat resolution:
Return to L3 via `aitp_advance_to_l3`. The `retreat_checkpoint` in state.md preserves:
- Which L3 activity was active (`l3_activity`)
- Which candidates existed
- When the retreat happened and why

The agent should then re-run gap-audit on the updated derivation to verify the gap is resolved.

## Allowed transitions

- Forward: `integrate`, `distill` — call `aitp_switch_l3_activity(activity="integrate")` or `aitp_switch_l3_activity(activity="distill")` to advance. (gap-audit is a hard prerequisite — the gate blocks
  integrate and distill if gap-audit content is missing)
- Backedges: `derive` (if gaps reveal derivation was incomplete)
- Retreat: `retreat_to_l0`, `retreat_to_l1` (via the decision tree above)
