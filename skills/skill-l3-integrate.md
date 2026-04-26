---
name: skill-l3-integrate
description: L3 Result Integration subplane — combine analysis into findings.
trigger: l3_activity == "result_integration"
---

# L3 Result Integration

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question (clarification, scope, direction, missing info), you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

You are in the result integration subplane of L3 derivation.

## Collaborative Discussion (MANDATORY)

Before integrating results, you MUST discuss with the human about what the results mean.
Do NOT just combine numbers into a summary.

Use AskUserQuestion at these checkpoints:

1. **Cross-check discussion**: Present how different analysis results relate.
   Ask: "The OTOC says <X> and Krylov says <Y>. Are these consistent with each other?
   Do you see the same picture I do?"
2. **Gap identification**: Discuss what's missing.
   Ask: "Here are the gaps I've identified: <gaps>. Are there others? Which are
   blocking vs. nice-to-have?"
3. **Consistency with priors**: Compare against known results.
   Ask: "Our findings <vs.> the Chen-Zhou prediction / HS integrable limit / prior work.
   Does the comparison hold up? Any tensions?"
4. **Integration confirmation**: Before advancing to distillation.
   Ask: "The integrated picture is: <summary>. Ready to distill a claim, or do we
   need more analysis first?"

The human may add more discussion rounds at any time. Do NOT rush to fill the artifact.

## Escape Hatches

At ANY point during integration, you may offer these back-paths via AskUserQuestion:

- **Back to analysis** (`aitp_switch_l3_activity(target="analysis")`): if integration
  reveals analysis gaps
- **Back to planning** (`aitp_switch_l3_activity(target="planning")`): if integration
  reveals the plan was incomplete
- **Retreat to L1** (`aitp_retreat_to_l1`): if integration reveals fundamental
  framing issues
- **Query L2** (`aitp_query_l2`): compare integrated findings against
  validated global knowledge

## Active artifact

`L3/integrate/active_integration.md`

## Claim Readiness Assessment (MANDATORY)

Before advancing to distillation, assess the readiness of each finding. Set
`claim_readiness` in `active_integration.md` frontmatter to one of:

### `blocked`
Use when any supporting analysis has a hard-blocking gap:
- Missing derivation steps (non_auditable steps in formal_theory)
- Source restorations without anchors
- Numerical results without setup/observable/pass conditions
- Dependence on literature without source anchoring

Consequences: this finding may NOT be distilled into a candidate. It must
appear in `## Open Obligations` with a repair plan.

### `qualified`
Use when the finding is informative but carries explicit caveats:
- Normalization bridges still open
- Finite-size or regime limitations acknowledged
- Partial source gaps (some steps anchored, some not)

Consequences: may be distilled as a bounded working statement, but the
candidate MUST include `validity_regime`, `depends_on`, `breaks_if`, and
`still_unclosed` fields.

### `stable`
Use when the supporting analysis has no hard-blocking gaps and no unexplained
contradictions that would make the wording scientifically misleading.

Consequences: may be distilled into a candidate for L4 validation.

Record the assessment in the body under `## Claim Readiness`:
```markdown
### <finding name>: <readiness level>
- **Reason**: <why this readiness level>
- **Blocking gaps** (if blocked): <list>
- **Caveats** (if qualified): <list>
```

## Open Obligations Tracking (MANDATORY)

Under `## Open Obligations`, list every missing obligation that blocks claim use:

```markdown
- [ ] <obligation description>
  - Source: <which analysis round / derivation step>
  - Blocks claim: yes/no
  - Recommended next step: <what to do>
```

These flow into distillation as a quality gate — distillation must acknowledge
all open obligations before submitting a candidate.

## What to do

1. Combine analysis results into coherent findings.
2. Run consistency checks against L1 conventions and anchors.
3. Assess claim readiness (blocked/qualified/stable) for each finding.
4. List open obligations with blocking status.
5. Do not distill yet.

## Exit condition

Advance to **distillation** when `active_integration.md` has filled frontmatter fields
`integration_statement`, `findings`, and `claim_readiness`, plus headings `## Integration Statement`,
`## Findings`, `## Claim Readiness`, and `## Open Obligations`.

## Allowed transitions

- Forward: `distillation`
- Backedges: `analysis`
