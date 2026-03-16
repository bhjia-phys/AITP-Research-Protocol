# Communication contract

This file defines how layers communicate without collapsing into copied summaries or chat-only state.

## 1. Communication categories

There are three kinds of cross-layer communication.

### Routing edges

These move work from one stage to the next.

Examples:
- `L0 -> L1`
- `L1 -> L3`
- `L3 -> L4`
- `L4 -> L2`
- `L4 -> L3`

### Consultation edges

These are read-only or comparison-oriented edges.

Examples:
- `L2 -> L1`
- `L2 -> L3`
- `L2 -> L4`
- `L0 -> later layers` when more source acquisition is needed

Consultation edges now have a dedicated protocol surface under:
- `consultation/`

### Writeback edges

These create or update durable target-layer objects.

Examples:
- `L1 -> L2` in low-risk cases
- `L4 -> L2` after adjudication
- `L4 -> L3` when work returns to exploration

## 2. Core rule

Cross-layer communication should pass:
- ids,
- paths,
- short summaries,
- typed references,
- explicit decision metadata,

instead of copying whole object bodies.

The base reusable communication object is `object_ref`.

See:
- `schemas/object-ref.schema.json`

## 3. Critical edge definitions

### L1 -> L3

Purpose:
- escalate source-bound understanding into active research work.

Minimum handoff object:
- `candidate_seed`

Required contents:
- `candidate_seed_id`
- `source_refs`
- `claim_refs`
- `question`
- `proposed_candidate_type`
- `reason_for_escalation`

See:
- `schemas/candidate-seed.schema.json`

### L3 -> L4

Purpose:
- submit an explicit candidate for adjudication.

Minimum handoff object:
- `candidate`

Required contents:
- `candidate_id`
- `candidate_type`
- `question`
- `origin_refs`
- `assumptions`
- `proposed_validation_route`
- `intended_l2_targets`

See:
- `feedback/CANDIDATE.md`
- `feedback/schemas/candidate.schema.json`

### L4 -> L2

Purpose:
- promote a validated candidate into one or more canonical units.

Minimum handoff object:
- `promotion_decision`

Required contents:
- `decision_id`
- `candidate_id`
- `route`
- `verdict`
- `promoted_units`
- `evidence_refs`
- `reason`

See:
- `validation/schemas/promotion-decision.schema.json`

### L2 -> L3

Purpose:
- seed active research with reusable memory.

Minimum handoff object:
- `object_ref`

Typical uses:
- retrieve a method,
- retrieve a derivation object,
- retrieve a workflow,
- retrieve a bridge,
- retrieve a warning note.

### L2 -> L1

Purpose:
- normalize terminology and catch known traps during provisional understanding.

Minimum handoff object:
- `object_ref`

Typical uses:
- concept lookup,
- claim comparison,
- warning lookup,
- workflow reuse.

### L2 -> L4

Purpose:
- shape adjudication with prior accepted checks and known limits.

Minimum handoff object:
- `object_ref`

Typical uses:
- validation pattern retrieval,
- contradiction comparison,
- scope and regime comparison,
- warning reuse.

## 4. First-class L2 consultation protocol

The source-of-truth for non-trivial `L2` consultation now lives under:
- `consultation/`

For non-trivial consultation that changes a stage artifact or decision, emitting request/result/application artifacts there is mandatory.

One complete consultation should produce:
- `consult_request`
- `consult_result`
- `consult_application`

The base intent is:
- request what memory is needed,
- record what `L2` returned,
- record what was actually applied.

See:
- `L2_CONSULTATION_PROTOCOL.md`
- `consultation/README.md`
- `consultation/schemas/consult-request.schema.json`
- `consultation/schemas/consult-result.schema.json`
- `consultation/schemas/consult-application.schema.json`

## 5. Stage-local consultation projections

When a stage wants a compact local view, it may still log a projection in:
- `intake/topics/<topic_slug>/l2_consultation_log.jsonl`
- `feedback/topics/<topic_slug>/runs/<run_id>/l2_consultation_log.jsonl`
- `validation/topics/<topic_slug>/runs/<run_id>/l2_consultation_log.jsonl`

These logs are now:
- local readability surfaces,
- projections of the protocol source-of-truth,
- not the authoritative place to define consultation semantics.

See:
- `schemas/consultation-record.schema.json`

## 6. Layer 0 call-back communication

Later layers may call back into Layer 0 when they need:
- more sources,
- a cleaner snapshot,
- transcript retrieval,
- web re-open,
- a newly discovered citation trail.

The communication target is still a `source_item` or source query request, not a free-form wish list.

See:
- `L0_SOURCE_LAYER.md`
- `schemas/source-item.schema.json`

## 7. Communication anti-patterns

Do not:
- copy full source text into every later layer,
- duplicate whole candidates inside validation notes,
- dump whole validation notes into Layer 2,
- use chat as the only record of what moved between layers,
- treat an external note vault as an implicit communication bus,
- treat a bare retrieval list as if it already proves application.

## 8. Operational reading

The architecture should be read as:
- `L0` provides source substrate,
- `L1` creates provisional understanding,
- `L2` acts as active memory,
- `L3` forms research candidates,
- `L4` adjudicates and routes writeback.

The communication contract is what keeps these surfaces coordinated without merging them into one undifferentiated notebook.
