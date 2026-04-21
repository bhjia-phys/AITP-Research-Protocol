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

## Collaborative Discussion (MANDATORY)

Before distilling the final claim, you MUST discuss with the human about claim scope
and confidence. The claim is what gets validated — get it right.

Use AskUserQuestion at these checkpoints:

1. **Draft claim review**: Present the proposed distilled claim.
   Ask: "Here's my draft claim: <claim>. Is this too broad? Too narrow? Should we
   qualify it with specific conditions?"
2. **Evidence sufficiency**: Discuss whether evidence supports the claim.
   Ask: "The evidence for this claim is: <evidence>. Is it strong enough, or should
   we narrow the claim to match what we can actually support?"
3. **Open questions handling**: Discuss what to exclude from the claim.
   Ask: "These open questions remain: <questions>. Should any of them be resolved
   before we submit, or are they appropriately flagged as future work?"
4. **Claim finalization**: Before submitting candidate.
   Ask: "Final claim: <claim>. Confidence: <level>. Submit for L4 validation?"

The human may add more discussion rounds at any time. Do NOT rush to fill the artifact.

## Escape Hatches

At ANY point during distillation, you may offer these back-paths via AskUserQuestion:

- **Back to integration** (`aitp_advance_l3_subplane(target="result_integration")`):
  if the claim doesn't match the integrated findings
- **Back to analysis** (`aitp_advance_l3_subplane(target="analysis")`): if the claim
  needs more computational support
- **Retreat to L1** (`aitp_retreat_to_l1`): if distillation reveals fundamental
  framing problems
- **Query L2** (`aitp_query_knowledge`): check if this claim contradicts or
  duplicates existing validated knowledge

## Active artifact

`L3/distillation/active_distillation.md`

## What to do

1. Extract the distilled claim from integrated findings.
2. Summarize the supporting evidence.
3. Assign a confidence level.
4. List remaining open questions.

## Unfinished-Work Backflow Check (MANDATORY)

Before submitting a candidate via `aitp_submit_candidate`, you MUST check:

1. Read `L3/result_integration/active_integration.md` — look at `## Open Obligations`.
2. For each obligation marked `blocks claim: yes`:
   - If the claim depends on it → the candidate CANNOT be submitted. Go back to analysis.
   - If the claim can be scoped to avoid it → narrow the claim and document the scoping.
3. For each obligation marked `blocks claim: no`:
   - Acknowledge it in the candidate's `evidence` field as a known limitation.
4. Record the backflow assessment in `active_distillation.md` under `## Obligation Check`:

```markdown
### Obligation Check
- Checked against: active_integration.md ## Open Obligations
- Blocking obligations: <count> (<resolved/narrowed/pending>)
- Non-blocking acknowledged: <count>
- Claim scope adjusted: yes/no — <details>
```

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
