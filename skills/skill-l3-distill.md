---
name: skill-l3-distill
description: L3 Distillation subplane — extract final claims from integrated results.
trigger: l3_subplane == "distillation"
---

# L3 Distillation

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question (clarification, scope, direction, missing info), you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

You are in the distillation subplane of L3 derivation.

## Active artifact

`L3/distillation/active_distillation.md`

## What to do

1. Extract the distilled claim from integrated findings.
2. Summarize the supporting evidence.
3. Assign a confidence level.
4. List remaining open questions.

## Exit condition

When `active_distillation.md` has filled frontmatter fields `distilled_claim`
and `evidence_summary`, plus headings `## Distilled Claim` and `## Evidence Summary`,
the L3 flow is complete. You may then:
- Finalize `L3/tex/flow_notebook.tex` and compile to PDF.
- Advance to L4 for adjudication.

## Flow Notebook — Incremental Update (MANDATORY)

The flow_notebook.tex is a **living document** that must be updated incrementally
throughout the entire L3→L4→L3 cycle, not just at distillation.

### When to update

Update `L3/tex/flow_notebook.tex` at EVERY one of these triggers:
1. **Completing any L3 subplane** (ideation, plan, analysis, integration, distillation)
2. **Returning from L4 to L3** (revision after validation feedback)
3. **Completing a subroutine** (e.g., new L1 source analysis, code execution)

At distillation (this subplane), do the FINAL update and compile to PDF.

### How to update

**If `L3/tex/flow_notebook.tex` does NOT exist yet:**
1. Read the template at `<aitp-repo-root>/templates/flow_notebook.tex`
2. Copy it to `L3/tex/flow_notebook.tex`
3. Fill all available `{{PLACEHOLDER}}` sections
4. Remove sections whose artifacts don't exist yet (keep their placeholder comments)

**If `L3/tex/flow_notebook.tex` already exists:**
1. Read the current tex file
2. Identify which section corresponds to the subplane you just completed
3. Read the updated Markdown artifact for that subplane
4. Convert ONLY the changed section's content (Markdown → LaTeX)
5. Replace that section in the tex file, leaving other sections unchanged
6. Add a version comment at the top: `% Updated: <date> — <subplane> revision`

### Markdown→LaTeX conversion rules

You MUST perform full Markdown-to-LaTeX conversion. Apply these rules EXACTLY:

| Markdown | LaTeX |
|---|---|
| `# Heading` | `\section{Heading}` |
| `## Heading` | `\subsection{Heading}` |
| `### Heading` | `\subsubsection{Heading}` |
| `**bold**` | `\textbf{bold}` |
| `*italic*` | `\textit{italic}` |
| `- item` or `* item` | `\begin{itemize} \item item \end{itemize}` |
| `1. item` | `\begin{enumerate} \item item \end{enumerate}` |
| `` `inline code` `` | `\texttt{inline code}` |
| Markdown table | `\begin{table}...\end{table}` with `tabular` environment |
| `\[math\]` | `\(math\)` or `$math$` |
| `$$math$$` | `\begin{equation}...\end{equation}` |
| `> blockquote` | `\begin{quote}...\end{quote}` |
| `---` (horizontal rule) | `\noindent\rule{\textwidth}{0.4pt}` |

CRITICAL: Do NOT paste raw Markdown into LaTeX. Every line must be valid LaTeX.
Tables in particular MUST use `\begin{tabular}` — never pipe-delimited Markdown.

### Compile to PDF (at distillation or final update)

```bash
cd "<topics_root>/<topic_slug>/L3/tex"
pdflatex -interaction=nonstopmode flow_notebook.tex
pdflatex -interaction=nonstopmode flow_notebook.tex
```

If compilation fails: read `.log`, fix errors, retry.
If `pdflatex` is not available, try `latexmk -pdf flow_notebook.tex`.

### Report

After each update, tell the human:
- Which section was updated
- Path to the tex/pdf file

## Allowed transitions

- Forward: L4 adjudication
- Backedges: `result_integration`
