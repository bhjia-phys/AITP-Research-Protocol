---
name: skill-l3-distill
description: L3 Distillation subplane — extract final claims from integrated results.
trigger: l3_activity == "distill"
---

# L3 Distillation

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question (clarification, scope, direction, missing info), you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

## Entry Profile Detection + Candidate Type Routing

Check the execution brief for `entry_profile`:

**learn_paper** → use source-derived candidates:
- Content is a single concept → `atomic_concept`
- Content is a step-by-step derivation → `derivation_chain`
- Content is a cross-formalism/domain mapping → `correspondence_link`
- Content is a unresolved gap → `open_question`
- Content is a failed reproduction → `negative_result`
- Default → `atomic_concept`

**explore_idea** → use novel research candidates:
- Content is a novel claim → `research_claim` (default)
- Content is a negative finding → `negative_result`

**l4_return** → same as explore_idea, trust basis accounts for L4 outcome.

If uncertain between two types, use `AskUserQuestion` to confirm with the human.

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

- **Back to integration** (`aitp_switch_l3_activity(activity="integrate")`):
  if the claim doesn't match the integrated findings
- **Back to analysis** (`aitp_switch_l3_activity(activity="derive")`): if the claim
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

## L3→L1 Feedback (MANDATORY)

When submitting a candidate via `aitp_submit_candidate`, use the `l1_feedback_*`
parameters to record discoveries back to L1:

- `l1_feedback_kind`: `convention` | `contradiction` | `cross_edge`
- `l1_feedback_content`: what was discovered (markdown)
- `l1_feedback_target`: specific L1 artifact name (optional, uses default for each kind)

This is the LAST chance to feed discoveries back to L1 before the candidate
goes to L4 validation. If the candidate itself represents a discovery that
changes L1 framing, record it now.

If you need to record feedback separately (not as part of candidate submission),
or if the feedback spans multiple kinds, use the standalone tool:
```
aitp_feedback_to_l1(
    topics_root, topic_slug,
    feedback_kind="convention",  # or contradiction, cross_edge
    content="...",
    source_l3_activity="distill",
    source_candidate_id="<slug>",
)
```

## Pre-Submission Hard Checks (MANDATORY)

Candidate submission now enforces **3-layer hard checks** in the harness
(`cmd_candidate_submit`). Verify ALL three layers before calling
`aitp_submit_candidate`:

### Layer 1: Activity gate
- Current `l3_activity` must be `distill` or `integrate`.
- Submitting from `derive` or `gap-audit` is hard-blocked.

### Layer 2: Artifact content checks
The harness checks real content (not template scaffolding) in:

| Artifact | Required heading | Min chars |
|----------|-----------------|-----------|
| derive or trace-derivation | `## Derivation Chains` | 50 |
| gap-audit | `## Correspondence Check` | 30 |
| integrate | `## Findings` | 50 |

Additionally, read `L3/integrate/active_integration.md` `## Open Obligations`:
- For `blocks claim: yes` → candidate CANNOT be submitted. Go back to analysis.
- For `blocks claim: no` → acknowledge in candidate's `evidence` field.

### Layer 3: Preflight + contract validation
Harness runs preflight (gate check, derivation chain, domain invariants) and
Pydantic contract validation on the candidate file.

### Backflow assessment record

Record under `## Pre-Submission Check` in `active_distillation.md`:

```markdown
### Pre-Submission Check
- Layer 1 (activity): distill — OK
- Layer 2 (artifact content):
  - Derivation Chains: present (N chars)
  - Correspondence Check (gap-audit): present (N chars)
  - Findings (integrate): present (N chars)
- Layer 2 (open obligations):
  - Blocking: <count> (<resolved/narrowed/pending>)
  - Non-blocking: <count>
  - Claim scope adjusted: yes/no — <details>
- Layer 3: pending harness execution
```

## Exit condition

When `active_distillation.md` has filled frontmatter fields `distilled_claim`,
`evidence_summary`, and `completion_status`, plus headings `## Distilled Claim`
and `## Evidence Summary`, the claim is ready.

**Gate note:** Set `completion_status: complete`. The L3 gate reports
`blocked_incomplete` if it is `draft` or missing. Cross-activity prerequisite
check also requires integrate AND gap-audit content before distill is gate-ready.

Choose one of:

1. **Standard path**: Pass the 3-layer pre-submission check above, then call
   `aitp_submit_candidate`. The harness hard-validates all three layers.
2. **Fast-track path**: Use `aitp_fast_track_claim` for results already validated
   in peer-reviewed literature or simple correspondence claims.

If the distill claim originated from an idea, call `aitp_promote_idea_to_candidate`
with `derivation_summary` and `evidence` to preserve provenance.

## Allowed transitions

- Forward: L4 adjudication. Call `aitp_submit_candidate(topics_root, topic_slug, candidate_id, title, claim, evidence, assumptions, validation_criteria)` to exit L3 and enter L4 validation.
- Backedges: `integrate`, `derive`, `gap-audit`
