---
name: skill-l3-distill
description: L3 Distillation subplane — extract final claims from integrated results.
trigger: l3_activity == "distillation"
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

- **Back to integration** (`aitp_switch_l3_activity(target="result_integration")`):
  if the claim doesn't match the integrated findings
- **Back to analysis** (`aitp_switch_l3_activity(target="analysis")`): if the claim
  needs more computational support
- **Retreat to L1** (`aitp_retreat_to_l1`): if distillation reveals fundamental
  framing problems
- **Query L2** (`aitp_query_l2`): check if this claim contradicts or
  duplicates existing validated knowledge

## Active artifact

`L3/distill/active_distillation.md`

## What to do

1. Extract the distilled claim from integrated findings.
2. Summarize the supporting evidence.
3. Assign a confidence level.
4. List remaining open questions.

## Unfinished-Work Backflow Check (MANDATORY)

Before submitting a candidate via `aitp_submit_candidate`, you MUST check:

1. Read `L3/integrate/active_integration.md` — look at `## Open Obligations`.
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
the claim is ready. Choose one of:

1. **Standard path**: Submit candidate (`aitp_submit_candidate`), then advance to
   L4 for adversarial review. Use for novel claims requiring validation.
2. **Fast-track path**: Use `aitp_fast_track_claim` directly. Use for results
   already validated in peer-reviewed literature or simple correspondence claims.

If the current distill claim originated from an idea (e.g. via `aitp_submit_idea`),
call `aitp_promote_idea_to_candidate` with `derivation_summary` and `evidence`
instead of directly calling `aitp_submit_candidate`. This preserves provenance
back to the original idea.

## Allowed transitions

- Forward: L4 adjudication
- Backedges: `result_integration`
