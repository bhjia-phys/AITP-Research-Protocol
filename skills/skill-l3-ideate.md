---
name: skill-l3-ideate
description: L3 Ideation subplane — generate and record research ideas.
trigger: l3_subplane == "ideation"
---

# L3 Ideation

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question (clarification, scope, direction, missing info), you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

You are in the ideation subplane of L3 derivation.

## Active artifact

`L3/ideation/active_idea.md`

## What to do

1. Record the central idea statement.
2. Explain why this idea is worth pursuing (motivation).
3. Note prior work and risks.
4. Do not start planning or analysis yet.

## Flow Notebook — Incremental Update (MANDATORY)

Before advancing out of this subplane, update `L3/tex/flow_notebook.tex`:

1. **If file does NOT exist**: copy template from `<aitp-repo-root>/templates/flow_notebook.tex`
   to `L3/tex/flow_notebook.tex`, fill the **Ideation** section, leave other sections as
   `{{PLACEHOLDER}}` comments.
2. **If file already exists**: update ONLY the Ideation section from `active_idea.md`
   using Markdown→LaTeX conversion rules (see skill-l3-distill for full rules table).
   Add version comment: `% Updated: <date> — ideation revision`.

Do NOT compile to PDF yet. Compilation happens at distillation.

## Exit condition

Advance to **planning** when `active_idea.md` has filled frontmatter fields
`idea_statement` and `motivation`, plus headings `## Idea Statement` and `## Motivation`,
AND `flow_notebook.tex` has been updated.

## Allowed transitions

- Forward: `planning`
- Backedges: none (this is the entry subplane)
