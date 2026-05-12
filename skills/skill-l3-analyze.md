---
name: skill-l3-analyze
description: L3 Derivation — execute derivations, trace source derivations, run calculations. trace-derivation is derive-equivalent — both share the same gate and candidate-submission path.
trigger: l3_activity == "derive" or l3_activity == "trace-derivation"
---

# L3 Derivation (derive / trace-derivation)

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question (clarification, scope, direction, missing info), you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

This skill covers two derive-equivalent activities (they share the same gate and
candidate-submission path — both artifacts are checked for `## Derivation Chains`):

**`derive`** — execute your own derivations, calculations, and analysis.

**`trace-derivation`** (derive-equivalent, replaces deprecated study mode
`step_derive`) — step-by-step tracing of a source paper's derivation. The harness
treats derive and trace-derivation as equivalent: gate checks and candidate-submission
content checks accept either artifact.
Every step must record:
- `source_ref`: exact equation/page where this step lives in the source
- `justification_type`: definition | theorem | approximation | physical_principle |
  algebraic_identity | limit | assumption | conjecture | gap | numerical_evidence
- `rigor_level`: rigorous | heuristic | handwaving | conjectured

For trace-derivation, record steps using `aitp_create_derivation_step` and
verify with `aitp_verify_derivation_step` / `aitp_verify_derivation_chain`.

---

## Entry Profile Detection

Check the execution brief for `entry_profile`:
- **`explore_idea`** → derive (own derivation, derivation_round / numerical_or_benchmark_round)
- **`learn_paper`** → trace-derivation (source tracing, source_restoration_round)
- **`continue_work`** → resume whichever was in progress
- **`l4_return`** → patch derivation gaps from L4 review

In learn_paper mode, additionally track:
- **Coverage**: which sections of the source have been traced (use `source_toc_map` from L1)
- **Feynman self-test**: after tracing a derivation chain, cover the source and try to reconstruct blind. Differences = understanding gaps.

## Anomaly Detection → Diagnose Escape Hatch

If you encounter unexpected behavior (NaN, oscillations, deviation > threshold):
1. Try 1-3 quick fixes within derive (parameter adjustment, re-run)
2. If root cause unclear after 3 attempts, switch to diagnose:
   ```
   aitp_switch_l3_activity(activity="diagnose", reason="anomaly: <description>")
   ```

---

You are in the derivation workspace of L3.

## Collaborative Discussion (MANDATORY)

Before and during analysis, you MUST discuss with the human. Analysis is not a
solo activity — the human is a physicist who should guide interpretation.

Use AskUserQuestion at these checkpoints:

1. **Pre-analysis check-in**: Present what you're about to compute.
   Ask: "I'm about to <computation>. Is this the right first step, or should we
   start with something else?"
2. **Intermediate results**: When results come in, don't just record them silently.
   Ask: "Here's what I found: <results>. Does this match your expectation? Any
   anomalies I should investigate?"
3. **Anomaly discussion**: If something unexpected appears, STOP and discuss.
   Ask: "There's an anomaly at <point>: <description>. Should we investigate this
   further, or is it expected from the physics?"
4. **Post-analysis debrief**: Before advancing to integration.
   Ask: "Analysis complete. Key findings: <summary>. Anything I missed or should
   look at differently before we integrate?"

For post-L4 return analysis, add these additional discussion points:
- "L4 found these gaps: <gaps>. Which should we prioritize fixing?"
- "The quantitative discrepancy is <X>. Do you think this is normalization or physics?"
- "Should we write new scripts to address criterion <N> before re-submitting?"

The human may add more discussion rounds at any time. Do NOT rush to fill the artifact.

## Escape Hatches

At ANY point during analysis, you may offer these back-paths via AskUserQuestion:

- **Back to plan** (`aitp_switch_l3_activity(activity="plan")`): if the derivation
  reveals the plan needs adjustment
- **Back to ideate** (`aitp_switch_l3_activity(activity="ideate")`): if the derivation
  reveals the idea itself is flawed
- **Retreat to L1** (`aitp_retreat_to_l1`): if analysis reveals missing sources
  or wrong conventions
- **Query L2** (`aitp_query_l2`): check if similar results exist, compare
  against known validated results

## Active artifact

`L3/derive/active_derivation.md`

## Round Type (MANDATORY frontmatter field)

Set `round_type` in `active_derivation.md` frontmatter to one of:

| Round type | When to use | Mandatory blocks |
|---|---|---|
| `derivation_round` | Advancing a derivation, closing a proof/identity chain | `derivation_spine`, `assumptions_and_regime`, `open_obligation_list` |
| `source_restoration_round` | Recovering a source-local derivation or definition | `target_source_location`, `source_anchor_table`, `l3_restoration` |
| `numerical_or_benchmark_round` | Running or reviewing bounded numerical tests | `test_plan`, `observable_definition`, `pass_conditions`, `anomaly_analysis` |
| `synthesis_round` | Consolidating what a phase has taught the topic | `what_was_learned`, `current_best_statements`, `excluded_routes_summary` |

If the analysis spans multiple types, pick the PRIMARY one. Cross-type obligations
(e.g., convention_ledger, source_anchor_table) apply whenever the content requires them.

## Step-Level Derivation Discipline (formal_theory lane)

For `derivation_round` in `formal_theory` lane, every derivation step MUST have these
fields recorded in the body under `## Derivation Spine`:

```markdown
### Step N: <label>
- **Equation**: <the mathematical transformation>
- **Justification**: <why this step is valid>
- **Step origin**: `source_statement` | `l3_completion` | `conjecture`
- **Source anchor**: <page/section/equation number> (required if origin is source_statement)
- **Assumption dependencies**: <list assumptions this step relies on>
- **Open gap**: <note if anything is missing or uncertain>
```

Steps missing `equation` + `justification` + `step_origin` are flagged as
`non_auditable`. The analysis is NOT ready to advance until ALL derivation steps
are auditable OR explicitly marked with open_gap notes explaining what is missing.

## Source Anchor Table

When any derivation step references a source (paper, book, lecture), record an entry
under `## Source Anchor Table`:

```markdown
| Step | Source | Location | What source says | L3 completed? |
|------|--------|----------|-------------------|---------------|
| Step 3 | Redlich (1984) | Eq. (2.17) | $\Delta S_{CS} = ...$ | yes |
| Step 5 | Witten (2016) | p.12, below Eq. (3.4) | parity transformation rule | no |
```

This makes it explicit which steps come from sources vs. which are L3-completed.

## Lane-Specific Verification

### formal_theory lane

Use `aitp_verify_derivation_step` and `aitp_verify_derivation_chain` with SymPy.
Steps missing `equation` + `justification` + `step_origin` are `non_auditable`.
The analysis is NOT ready to advance until ALL derivation steps are auditable OR
explicitly marked with `open_gap` notes explaining what is missing.

Additionally use: `aitp_verify_dimensions` (dimensional analysis), `aitp_verify_algebra`
(algebraic identity check), `aitp_verify_limit` (correspondence principle).

### code_method lane

Do NOT use `aitp_verify_derivation_step` for symbolic verification. SymPy cannot handle
matrix/integral physics expressions (produces `'Equality' and 'Equality'` errors).

Verification for code_method is:
1. **Source anchoring**: Each step records `source_ref` to exact code location (file:line).
   A step anchored to real code with a correct formula is `source_anchored`.
2. **Numerical verification at L4**: Compile, run with known inputs, compare output to
   expected (literature/symmetry/limit). Record in `L4/outputs/`.
3. If a step has `justification_type = "gap"`, it MUST have a `gap_marker` with a
   concrete plan for resolution.

When recording steps via `aitp_create_derivation_step` for code_method:
- Set `rigor_level` based on code clarity and formula correctness (not algebraic proof)
- Use `justification_type = "definition"` for variable assignments, `"algebraic_identity"`
  for matrix multiplications, `"physical_principle"` for physics formulas
- `source_ref` MUST point to file:line range

### toy_numeric lane

Same as code_method for verification: source anchoring + numerical validation at L4.
Additionally check: dimensional consistency of inputs/outputs, reproducibility across
random seeds, behavior at known limits.

## Derivation Navigation and Visualization

### Traversing the derivation DAG

As your derivation grows, navigate the dependency graph:

```
aitp_traverse_derivation(topics_root, topic_slug, chain_id="default")
```

Returns the full derivation tree — which steps depend on which, where
cycles exist, and which steps are blocking downstream progress.

### Visualizing the chain

```
aitp_visualize_derivation_chain(topics_root, topic_slug, chain_id="default")
```

Renders the derivation as a directed graph. Use when the human asks
"show me the derivation structure" or when debugging complex dependencies.

### Pre-derivation estimation

Before executing a derivation step, sanity-check with order-of-magnitude:

```
aitp_estimate_order(topics_root, topic_slug, quantity="<name>", expression="<LaTeX>")
```

### Checking available inference rules

Know what proof techniques are registered:

```
aitp_list_inference_rules(topics_root)
```

If a step uses a rule not in the registry, the verification tools can't validate it.

## What to do

1. Set `round_type` in frontmatter.
2. Execute the planned derivation steps with step-level discipline.
3. Record the method used, results so far, and source anchors.
4. Use `aitp_traverse_derivation` to check dependencies and blocking steps.
5. Flag any anomalies or unexpected findings.
6. For failed routes, use the Failure Route Template below.
7. Do not finalize claims yet.

## Failure Route Template

When a derivation route fails, record it under `## Failed Routes`:

```markdown
### <route name>
- **Why it looked plausible**: <what made this route seem worth trying>
- **Exact failure point**: <where exactly the reasoning broke down>
- **Lesson**: <what was learned from the failure>
- **Revive conditions**: <under what circumstances this route might work>
```

Failed routes are NOT discarded — they prevent future sessions from repeating dead ends.

## Post-L4 Return Analysis

If you are returning to analysis after L4 validation (post-L4 return), your analysis must:

1. **Read the L4 review** at `L4/reviews/<candidate_id>.md` — note all check results,
   caveats, and quantitative discrepancies.
2. **Assess validation quality** — were checks independent? Were any criterion relying
   on stored data rather than fresh computation? Note gaps.
3. **Record findings** in `L3/derive/active_derivation.md`:
   - What was validated conclusively
   - What had caveats (normalization differences, finite-size limitations)
   - What remains open (larger L, different operators, thermodynamic limit)
## Exit condition

Advance to **integrate** when `active_derivation.md` has filled frontmatter fields
`derivation_count`, `all_steps_justified`, and `completion_status`, plus headings
`## Derivation Chains` and `## Step-by-Step Trace`.

**Gate note:** The L3 gate reports `blocked_incomplete` until `completion_status`
is set to `complete`. Advancing to integrate also requires gap-audit completion
(the integrate gate checks for gap-audit content as a cross-activity prerequisite).

Candidate submission is **not allowed from derive** — derive was removed from
`_DIRECT_SUBMIT_ACTIVITIES`. Use integrate or distill to submit candidates.

## Allowed transitions

- Forward: `integrate`, `gap-audit` — call `aitp_switch_l3_activity(activity="integrate")` or `aitp_switch_l3_activity(activity="gap-audit")` to advance.
- Backedges: `ideate`, `plan`
