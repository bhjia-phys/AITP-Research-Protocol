---
name: skill-l3-step-derive
description: L3 Study — step_derive subplane. Trace every derivation step with explicit justification.
trigger: l3_subplane == "step_derive" AND l3_mode == "study"
---

# Step Derive (Study Mode)

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question, you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

You are tracing every derivation in the source, step by step, with explicit justification for each step.

## Active artifact

`L3/step_derive/active_derivation.md`

## What to do

For each derivation chain in the source:

1. **Identify the chain** — what is being derived? What is the starting point and endpoint?
2. **Trace each step** — for every transformation in the derivation:
   - Write the step in your own notation (consistent with `convention_snapshot.md`)
   - Tag the justification_type:
     - `definition` — applying a definition
     - `theorem` — invoking a known theorem
     - `approximation` — taking an approximation (state the regime)
     - `physical_principle` — applying a physical law or principle
     - `algebraic_identity` — purely algebraic manipulation
     - `limit` — taking a limit (state what goes to what)
     - `assumption` — introducing an assumption (state what and why)
   - Note any unstated assumptions or implicit steps
3. **Feynman self-check** — for each step:
   - Cover the next step and try to derive it yourself
   - If you cannot, mark it as a gap
4. **Fill the artifact**:
   - `derivation_count`: number of derivation chains traced
   - `all_steps_justified`: "yes" only if every step has a justification_type
   - `## Derivation Chains`: overview of each chain (start -> end, key steps)
   - `## Step-by-Step Trace`: the detailed trace
   - `## Feynman Self-Check`: results of the self-check
   - `## Unresolved Steps`: steps where justification is unclear

## Quality gate

Before advancing:
- Every derivation step has a `justification_type`
- Feynman self-check is attempted for every non-trivial step
- `all_steps_justified` is honestly assessed
- Any steps where you could not reproduce the derivation are flagged

## Exit condition

Advance to **gap_audit** when:
- `derivation_count` > 0
- Every derivation chain has a step-by-step trace
- Feynman self-check section is filled

## Allowed transitions

- Forward: `gap_audit`
- Backedges: `source_decompose` (if decomposition was insufficient)
