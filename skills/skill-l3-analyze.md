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

## Active artifact

`L3/analysis/active_analysis.md`

## What to do

1. Execute the planned derivation steps.
2. Record the method used and results so far.
3. Flag any anomalies or unexpected findings.
4. Do not finalize claims yet.

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
