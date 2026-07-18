# AITP Harness Feedback Problem Capture Design

Status: implemented correction slice, AITP v5

## Problem

Real research sessions expose AITP and host-integration weaknesses before the
system has enough reviewed evidence to optimize itself. AITP must preserve the
observed friction as a reviewable problem without pretending that the research
session has designed, implemented, or approved an engineering change.

Reusable-workflow signals require an especially strict boundary. Harness
Feedback does not create a Skill candidate or request Skill distillation. The
M4 Skill lifecycle independently derives procedural candidates from validated
typed research records. A feedback case may report that workflow recording or
Skill discovery behaved poorly, but it is never evidence for a Skill package.

## Scope

This slice provides one Markdown-backed typed family:

- Capture observed friction, expected and actual behavior, research impact,
  reproducibility steps, host/runtime context, exact source refs, and a proposed
  review direction.
- Link the case to an affected capability and optional record family/topic.
- Preserve reviewer/status, duplicate, related-case, and supersession metadata.
- Keep all engineering, Skill, and scientific-trust authority explicitly false.
- Aggregate recurring cases in a derived read-only review view.

## Non-Goals

- Do not author a harness or AITP optimization plan during research.
- Do not create a code patch, Skill candidate, Skill package preview,
  distillation request, install plan, or install action.
- Do not update evidence, validation, memory promotion, baseline acceptance, or
  claim trust.
- Do not create separate friction/workflow/schema/automation/proposal families.
- Do not solve the broader theory-discussion insight knowledge-base layer here.

## Architecture

```text
real research observation
        |
        v
HarnessFeedbackCaseRequest
        |
        v
registry/harness_feedback_cases/<case-id>.md
        |
        +--> exact typed ref and Markdown dossier
        +--> read-only recurring-case review view
        +--> later human engineering review

validated procedural research records
        |
        v
independent M4 Skill lifecycle
```

There is intentionally no arrow from a Harness Feedback case to the Skill
lifecycle. Human engineering review may later improve AITP or the harness. Any
future Skill candidate must still be independently derived and validated from
the research graph.

## Identity And Revision

- A source fingerprint binds topic, problem type, host, affected capability and
  family, and source refs.
- A content fingerprint binds the full observed request.
- Replaying the same source/content is idempotent.
- Changed information for the same source requires compare-and-swap revision or
  an explicit related case.
- A new source fingerprint can be linked only through explicit existing
  `harness_feedback_case:*` refs.
- Revisions preserve the original creation time and pin their predecessor hash.

## Authority Contract

Every case keeps these values fixed:

- `requires_human_review=true`
- `orientation_only=true`
- `can_modify_harness=false`
- `produces_harness_optimization_plan=false`
- `produces_skill_implementation_plan=false`
- `can_emit_skill_artifacts=false`
- `can_install_skill=false`
- `can_install_skill_artifacts=false`
- `can_update_claim_trust=false`

The renderer contains only observed facts, reproduction, traceability, proposed
direction, and the review boundary. It does not render an implementation plan
or downstream action artifact.

## Runtime Surfaces

- Model: `HarnessFeedbackCaseRecord`
- Family: `harness_feedback_cases`
- Writer: `record_harness_feedback_case(...) -> WriteResult`
- Renderer: `render_harness_feedback_case(record)`
- Review: `build_harness_feedback_review_view(ws)`
- CLI: `aitp-v5 harness-feedback record --request-json-file <path>` and
  `aitp-v5 harness-feedback review-view`
- Full MCP: `aitp_v5_record_harness_feedback_case` and
  `aitp_v5_build_harness_feedback_review_view`

The compact MCP surface remains unchanged at ten tools. Historical bundle,
problem-dossier, and extractor-plan public-surface validators are read-only
compatibility readers; their runtime builders are removed.

## Topic-Specific Fixtures

Production runtime contains no fixed NiO case id, topic path, or workflow
content. The NiO example lives only in
`tests/fixtures/v5_harness_feedback/nio_case.json` with expected Markdown.

## Acceptance Criteria

- One typed family covers every Harness Feedback problem type.
- Same facts are idempotent; changed facts require explicit revision/relation.
- Every engineering, Skill, and trust authority flag is rejected if set true.
- Negative tests fail every candidate, patch, preview, install, and distillation
  path if the Harness Feedback writer attempts to call it.
- CLI/full MCP expose generic recording and read-only review only.
- Capability registry, public surfaces, architecture budgets, and compact MCP
  counts remain consistent.
