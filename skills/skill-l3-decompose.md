---
name: skill-l3-decompose
description: L3 Study — source_decompose subplane. Break a source into atomic claims.
trigger: l3_subplane == "source_decompose" AND l3_mode == "study"
---

# Source Decompose (Study Mode)

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question, you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

You are decomposing a source (paper, book chapter, lecture notes) into atomic claims.

## Active artifact

`L3/source_decompose/active_decomposition.md`

## What to do

1. **Identify the source** — confirm which source from L0 you are decomposing.
2. **Read the source** — use available tools (arxiv-latex-mcp, web reader) to access the full text.
3. **Decompose into atomic claims** — for each distinct claim in the source:
   - Restate it in your own words (not copy-paste).
   - Tag it: `definition | theorem | approximation | physical_principle | numerical_result | conjecture`
   - Check L2: does a similar concept already exist? (`aitp_query_l2`)
   - Mark: `confirmed_existing` (found in L2) or `new_to_l2`
4. **Fill the artifact**:
   - `source_ref`: which L0 source (source_id)
   - `claim_count`: number of atomic claims
   - `## Atomic Claims`: numbered list, each with claim_type and L2 status
   - `## Claim-Concept Map`: which claims map to which physics concepts
   - `## L2 Overlap Check`: summary of what already exists vs. what is new

## Quality gate

Before advancing, verify:
- Every claim is restated in simple language (Feynman criterion)
- Every claim has a type tag
- L2 overlap check is completed for all claims

## Flow Notebook — Incremental Update

Before advancing out of this subplane, update `L3/tex/flow_notebook.tex`:
1. If file does NOT exist: copy template from `<aitp-repo-root>/templates/flow_notebook.tex`.
2. Fill the **Source Decomposition** section with the claim inventory.
3. Leave other sections as `{{PLACEHOLDER}}`.

## Exit condition

Advance to **step_derive** when:
- `source_ref` is filled
- `claim_count` > 0
- `## Atomic Claims` has at least one entry
- L2 overlap check is completed

## Allowed transitions

- Forward: `step_derive`
- Backedges: none (entry subplane)
