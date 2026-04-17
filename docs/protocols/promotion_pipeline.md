# Promotion Pipeline

Domain: Point (Promotion)
Authority: subordinate to AITP SPEC S8.
References: canonical/PROMOTION_POLICY.md, canonical/L2_STAGING_PROTOCOL.md.

---

## P1. Role

The promotion pipeline governs how candidates advance from L3 through L4
validation to L2 canonical storage. It ensures reusable knowledge is earned,
not assumed.

## P2. Promotion Flow

### Current Implementation: Three-Step Model

The pipeline operates as a three-step flow:

| Step | Status | Description |
|------|--------|-------------|
| 1 | `pending_human_approval` | Candidate is staged and awaiting review |
| 2 | `approved` | Gate has been approved (human or auto) |
| 3 | `promoted` | Content written to L2 or L2_auto |

### Aspirational: Four-Stage Counting Model

The target architecture is a four-stage counting state machine:

| Stage | Name | Counter | Description |
|-------|------|---------|-------------|
| 1 | `candidate` | 0 | Fresh candidate in L3-D |
| 2 | `validated` | 2 | Passed L4 validation at least twice |
| 3 | `promotion_ready` | 3 | Validated + integration complete + human not objected |
| 4 | `promoted` | 4 | Human explicitly approved L2 write |

Migration to the four-stage model is a future implementation milestone.

## P3. Gate Resolution

### Human Approval Gate

The standard promotion path requires human approval:

1. Candidate enters `pending_human_approval` status.
2. Gate payload is assembled with validation results and context.
3. Human reviews and decides: approve, reject, or request revision.
4. On approval: status advances to `approved`, then `promoted`.

Gate resolution checks `gate_payload["status"] == "approved"`.

### Auto-Promotion Gate

When the topic's trust boundary permits auto-advance:

1. Auto-promotion validates theory-packet artifacts and source-policy flags.
2. If criteria are objectively met, the gate is set to `status: "approved"`
   with `review_mode: "ai_auto"`.
3. Content is promoted to the `L2_auto` canonical layer (see P4).

Auto-promotion conditions:
- all validation criteria are objectively met (no subjective judgment needed),
- the topic's trust boundary explicitly permits auto-advance,
- the candidate is bounded and does not mix independent claims,
- no open gaps remain,
- no unresolved contradictions exist.

## P4. L2 Auto Canonical Layer

Auto-promoted content is written to `L2_auto`, a separate canonical layer
distinct from the human-reviewed `L2`.

Properties of L2_auto:
- Uses `review_mode: "ai_auto"` to distinguish from human-reviewed content.
- Subject to the same unit-family semantics as L2.
- May be promoted to L2 (human-reviewed) through a subsequent human approval.
- Maintains the same promotion trace requirements.

This separation ensures that auto-promoted content is tracked distinctly
without weakening the evidence discipline of human-reviewed L2.

## P5. Staging Bridge

Staged candidates (non-feedback-run) may be promoted through a bridge artifact:

1. The `materialize_selected_candidate_promotion_bridge` function creates a
   bridge artifact linking the staged candidate to the promotion pipeline.
2. The bridge carries the candidate context, validation results, and any
   split contract information.
3. The bridge is resolved through the normal gate resolution process.

This enables candidates that were created outside of the feedback-run loop
to enter the promotion pipeline.

## P6. Continue-Decision Readiness Proxy

The system counts "continue" decisions in `innovation_decisions.jsonl` as a
readiness proxy for promotion-adjacent actions:

- >= 2 continue decisions: candidate may enter staging.
- >= 3 continue decisions: candidate is eligible for auto-promotion (if policy
  permits).
- >= 4 continue decisions: candidate is strongly recommended for promotion
  review.

These thresholds act as heuristic readiness signals, not as substitutes for
the formal validation requirements.

## P7. Wide Candidate Handling

If a candidate mixes several independent claims:

1. Do not promote as one object.
2. Detect `split_required` and block the candidate.
3. Emit a split contract (see feedback/SPLIT_PROTOCOL.md).
4. After splitting, individual bounded children may be promoted separately.

Current behavior: the entire candidate is blocked when `split_required` is
detected. Individual child promotion after splitting is not yet implemented.

## P8. Post-Promotion Formalization

After promotion, the orchestrator may schedule follow-up actions:

1. **Formalization followup** — if the promoted content has theory-packet
   artifacts, schedule formal verification work.
2. **Proof repair review** — if promotion involved proof-level content,
   schedule a proof repair review.

These post-promotion actions ensure that promoted content continues to
improve in rigor.

## P9. Promotion Trace

Every promotion must leave a trace:
- candidate id,
- validation results that supported the promotion,
- regression question/oracle ids (if applicable),
- human approval record or ai_auto review mode marker,
- any conditions or caveats,
- the resulting L2 or L2_auto unit ids.

Schema: `schemas/promotion-trace.schema.json`.

## P10. Promotion Blockers

A candidate is blocked from promotion when:
- any declared validation criterion has not been met,
- there are unresolved contradictions,
- the candidate is wider than its validation scope,
- required regression questions have not passed,
- child follow-up topics have not been reintegrated,
- the topic completion state is not `promotion-ready`.

Blockers must be recorded durably, not hidden in commentary.

## P11. Implementation Status

### Currently implemented
- Three-step flow (pending_human_approval -> approved -> promoted).
- Human approval gate with gate payload resolution.
- Auto-promotion with L2_auto canonical layer.
- Staging bridge for non-feedback-run candidates.
- Continue-decision counting as readiness proxy.
- Wide candidate detection and blocking.
- Post-promotion formalization followup.
- Promotion trace recording.
- Promotion blocker detection.

### Not yet implemented
- Four-stage counting state machine (P2 aspirational model).
- Individual child promotion after candidate splitting.
- Stage counter thresholds (0/2/3/4).

## P12. What the Pipeline Should Not Do

- Auto-promote to L2 (human-reviewed) without human approval.
- Treat coverage as a substitute for validation.
- Promote wide candidates without splitting.
- Skip the promotion trace.
- Weaken validation criteria to make a candidate pass.
- Treat narrative plausibility as a promotion justification.
