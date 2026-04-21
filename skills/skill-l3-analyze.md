---
name: skill-l3-analyze
description: L3 Analysis subplane — execute derivations and calculations.
trigger: l3_subplane == "analysis"
---

# L3 Analysis

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question (clarification, scope, direction, missing info), you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

You are in the analysis subplane of L3 derivation.

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

- **Back to planning** (`aitp_advance_l3_subplane(target="planning")`): if analysis
  reveals the plan needs adjustment
- **Back to ideation** (`aitp_advance_l3_subplane(target="ideation")`): if analysis
  reveals the idea itself is flawed
- **Retreat to L1** (`aitp_retreat_to_l1`): if analysis reveals missing sources
  or wrong conventions
- **Query L2** (`aitp_query_knowledge`): check if similar results exist, compare
  against known validated results

## Active artifact

`L3/analysis/active_analysis.md`

## Round Type (MANDATORY frontmatter field)

Set `round_type` in `active_analysis.md` frontmatter to one of:

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

## What to do

1. Set `round_type` in frontmatter.
2. Execute the planned derivation steps with step-level discipline.
3. Record the method used, results so far, and source anchors.
4. Flag any anomalies or unexpected findings.
5. For failed routes, use the Failure Route Template below.
6. Do not finalize claims yet.

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

If you entered this subplane via `aitp_return_to_l3_from_l4` (check `l4_return_reason`
in state.md), your analysis must:

1. **Read the L4 review** at `L4/reviews/<candidate_id>.md` — note all check results,
   caveats, and quantitative discrepancies.
2. **Assess validation quality** — were checks independent? Were any criterion relying
   on stored data rather than fresh computation? Note gaps.
3. **Record findings** in `L3/analysis/active_analysis.md`:
   - What was validated conclusively
   - What had caveats (normalization differences, finite-size limitations)
   - What remains open (larger L, different operators, thermodynamic limit)
4. **Update flow_notebook.tex** with the L4 analysis section.

## Flow Notebook — Incremental Update (MANDATORY)

Before advancing out of this subplane, update `L3/tex/flow_notebook.tex`:

1. **If file does NOT exist**: copy template from `<aitp-repo-root>/templates/flow_notebook.tex`
   to `L3/tex/flow_notebook.tex`, fill the **Analysis** section, leave other sections as
   `{{PLACEHOLDER}}` comments.
2. **If file already exists**: update ONLY the Analysis section from `active_analysis.md`
   using Markdown→LaTeX conversion rules (see skill-l3-distill for full rules table).
   Add version comment: `% Updated: <date> — analysis revision`.

Do NOT compile to PDF yet. Compilation happens at distillation.

## Exit condition

Advance to **result_integration** when `active_analysis.md` has filled frontmatter fields
`analysis_statement` and `method`, plus headings `## Analysis Statement` and `## Method`,
AND `flow_notebook.tex` has been updated.

## Allowed transitions

- Forward: `result_integration`
- Backedges: `ideation`, `planning`
