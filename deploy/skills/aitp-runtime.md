---
name: aitp-runtime
description: Use after AITP v5 routing has claimed a theoretical-physics task; continue through typed records, validation gates, and trust-controlled memory.
---

# AITP Runtime v5

Every research turn starts by restoring typed state:

```text
brief = aitp_v5_get_execution_brief(base="{{TOPICS_ROOT}}", session_id=<session-id>)
relation_map = aitp_v5_get_claim_relation_map(base="{{TOPICS_ROOT}}", session_id=<session-id>)
```

Then decide from the brief:

- `current_focus`: active claim, confidence state, evidence profile, uncertainty
- `flow_profile`: fluid/guided/rigorous/adversarial route
- `risk_assessment` and `action_budget`: how heavy evidence must be
- `evidence_coverage`: missing required outputs
- `next_action_candidates`: safe next actions
- `forbidden_now`: actions blocked until evidence, validation, or a human gate

Use the claim relation map as the conclusion-boundary layer. Read
`supported_by`, `limited_by`, `not_tested_by`, `contradicted_by`,
`current_conclusion.can_say`, `current_conclusion.cannot_say`,
`current_blockers`, and `next_valid_actions` before deciding whether a failure
supports, limits, or does not test the active claim.

If the only available packet is a legacy stage brief, migrate or bind a v5
session first. Legacy stages are historical orientation, not the runtime loop.

## Typed Record Boundaries

- `execution_brief` is the working control panel.
- `claim_relation_map` is a read-only recovery boundary; it is not evidence by
  itself and cannot update claim trust.
- Reference locations and summaries are orientation until linked to evidence.
- A validation result supports only the exact checks and failure modes it covers.
- Partial validation should be narrow, not a broad pass.
- Claim confidence, trust updates, and L2 memory require explicit v5 gates.

## Legacy Topics

1. Use legacy aliases only to discover the slug.
2. Prefer `aitp_v5_migrate_curated_legacy_topic_to_v5` for known curated topics.
3. Use `aitp_v5_migrate_legacy_topic_to_v5` for generic preservation.
4. Continue from the v5 session id returned by migration.

## Physics Validation Discipline

Before treating a result as strong, check dimensional consistency, algebraic
consistency, limiting cases, symmetry or Ward identities, conservation laws,
approximation validity, numerical convergence, benchmarks, and explicit failure
modes where applicable.

Do not bury a failed check in prose. Record it as typed state.
