# Followup Lifecycle Protocol

Domain: Brain
Authority: subordinate to AITP SPEC S9.
References: runtime/DEFERRED_RUNTIME_CONTRACTS.md, GAP_RECOVERY_PROTOCOL.md.

---

## FL1. Role

The followup lifecycle manages two related patterns:
1. Sub-topic spawning and reintegration — when a parent topic needs separate
   investigation.
2. Deferred candidate buffering — when candidates are not yet actionable but
   should not be forgotten.

Both patterns ensure that research work is not lost across sessions, topics,
and time.

## FL2. Sub-Topic Spawning

### When to Spawn

A parent topic may spawn a child sub-topic when:
- the research question splits into independent sub-problems,
- a gap requires separate investigation with its own L0 sources,
- an external consultation is needed that merits its own topic lifecycle,
- a follow-up source recovery task needs dedicated execution.

### Spawn Contract

When spawning a child, the parent records:
- `parent_topic_slug` — the parent topic slug,
- `child_topic_slug` — the new child topic slug,
- `statement` — auto-generated topic statement (replaces `spawn_reason`),
- `return_packet` — what the child must deliver back to the parent,
- `reentry_targets` — which parent artifacts the child results update,
- `blocking` — NOT YET IMPLEMENTED. Currently all children are non-blocking.
- Additional fields: `parent_run_id`, `receipt_id`, `query`,
  `target_source_type`, `triggered_by_result_id`, `parent_gap_ids`,
  `parent_followup_task_ids`, `supporting_regression_question_ids`,
  `arxiv_id`, `source_id`, `human_request`, `runtime_root`,
  `return_packet_path`.

The child topic carries the return packet as a durable contract:
`runtime/topics/<child>/runtime/followup_return_packet.json`

### Child Lifecycle

The child follows a normal topic lifecycle (bootstrap -> loop -> ... -> complete)
with one additional obligation: before completion, the child must populate its
return packet with:
- results — what was discovered or resolved,
- return_status (code vocabulary):
  - `pending_reentry` — not yet returned,
  - `recovered_units` — returned with usable knowledge units,
  - `resolved_gap_update` — returned having resolved a gap,
  - `returned_with_gap` — returned but gaps remain,
  - `returned_unresolved` — returned without resolving.
- return_shape — validated against `acceptable_return_shapes` allowlist,
- artifacts produced,
- remaining gaps,
- supporting regression question IDs.

Note: The protocol originally defined statuses as
`resolved / partially_resolved / unresolved / blocked`. The implementation
uses a different taxonomy (see above). Both vocabularies are valid; the code
vocabulary is the canonical one.

### Return Shape Validation

The code validates return shapes against an `acceptable_return_shapes` allowlist:
- `recovered_units` — returned L2/L3 knowledge units,
- `resolved_gap_update` — gap resolved, parent gap map updated,
- `still_unresolved_packet` — no resolution, packet returned as-is.

### Reintegration

When the child completes (or at the parent's request):
1. The parent reads the child's return packet.
2. The return shape is validated.
3. Reintegration requirements are enforced:
   - `must_write_back_parent_gaps` — write gap updates to parent,
   - `must_update_reentry_targets` — update parent artifacts,
   - `must_not_patch_parent_directly` — use proper reintegration path,
   - `requires_child_topic_summary` — child summary must be present.
4. The parent integrates the results into its own artifacts.
5. The parent records a reintegration receipt with:
   - `parent_topic_slug`, `parent_run_id`, `child_topic_slug`,
   - `receipt_id`, `return_status`, `accepted_return_shape`,
   - `reentry_targets`, `parent_gap_ids`, `parent_followup_task_ids`,
   - `supporting_regression_question_ids`, `return_artifact_paths`,
   - `child_topic_completion_status`, `child_topic_summary`,
   - `gap_writeback_required`, `reentry_update_required`, `summary`.

6. After reintegration, the parent's topic completion is re-assessed
   automatically.

Reintegration is a separate durable receipt, not a hidden side effect of the
child topic completing.

Storage: `runtime/topics/<parent>/runtime/followup_reintegration.jsonl`

### Blocking vs Non-Blocking Children

- **Blocking child**: parent pauses the relevant work stream until the child
  returns. NOT YET IMPLEMENTED.
- **Non-blocking child**: parent continues without waiting. When the child
  completes, the parent receives a notification and decides whether to
  reintegrate immediately or defer. This is the current default behavior.

## FL3. Deferred Candidate Buffer

### What Gets Deferred

Candidates may be deferred when:
- prerequisites are not yet available (missing source, missing capability),
- the current topic scope does not cover them,
- they are out of scope for the current session but may become relevant later,
- a follow-up task is needed before the candidate can be evaluated,
- a candidate split produces unresolved fragments.

### Deferred Candidate Record

Every deferred candidate records:
- `entry_id` — the buffer entry identifier,
- `source_candidate_id` — the original candidate identifier,
- `title`, `summary` — human-readable description,
- `reason` — why it was deferred,
- `reactivation_conditions` — when it should wake up,
- `status` — `buffered` / `reactivated` (note: `expired` not yet implemented),
- `required_l2_types` — which L2 unit types this candidate would produce,
- `reactivation_candidate` — pre-materialized candidate payload for reactivation,
- `activated_candidate_id` — ID after activation,
- `activated_at` — timestamp of activation,
- `notes` — additional context.

Note: `priority` and `deferred_at` fields from the original protocol are not
yet implemented. `candidate_id` is called `entry_id` in the code.

### Reactivation Conditions

Three types of reactivation conditions:

1. **Source-based**: `source_ids_any`
   - Reactivate when any of the listed sources are registered in the topic.
   - Example: deferred until the primary reference is acquired.

2. **Text-based**: `text_contains_any`
   - Reactivate when the topic's text content matches any of the patterns.
   - Example: deferred until the topic discusses a specific concept.

3. **Event-based**: `child_topics_any`
   - Reactivate when any of the listed child topics complete.
   - Example: deferred until a follow-up investigation returns results.

Currently only OR logic is supported (any single condition match triggers
reactivation). AND logic for combining conditions is NOT YET IMPLEMENTED.

### Reactivation Check

The Brain checks reactivation conditions:
- when explicitly called (`reactivate_deferred_candidates`),
- when a new source is registered (NOT YET AUTO-TRIGGERED),
- when a child topic completes (NOT YET AUTO-TRIGGERED),
- at topic resume / session start (NOT YET AUTO-TRIGGERED).

If any condition is met, the candidate is reactivated and placed back in the
action queue.

### Expiration

NOT YET IMPLEMENTED. Deferred candidates currently persist indefinitely.
The protocol envisions expiration dates and `expired` status transitions.

No deferred candidate should be silently dropped without a status change.

## FL4. Candidate Split Contract

When a candidate mixes several independent claims:

1. `apply_candidate_split_contract` processes the split.
2. Individual bounded children are created in the candidate ledger.
3. Unresolved fragments are buffered in the deferred buffer.
4. Split receipts record the operation.
5. Fingerprint deduplication prevents duplicate child candidates.

## FL5. Consultation Followup

A separate followup pattern for consultation-based workflow:

1. Derive a query from topic state (`derive_consultation_followup_query`).
2. Select a bounded candidate from staged L2 hits
   (`select_bounded_consultation_candidate`).
3. Build a selection payload with retrieval profile, trust surface, and
   consultation index context.
4. Render markdown summary for human review.

This pattern is implemented in `consultation_followup_support.py` but was not
part of the original protocol design.

## FL6. Gap Writeback Queue

A separate queue for tracking which reintegrations require gap writeback to
the parent:

- `followup_gap_writeback.jsonl` / `.md` — durable gap writeback records.
- Each entry links a reintegration to specific parent gaps that need updating.
- Separate from the reintegration receipt for traceability.

## FL7. Gap Recovery Routing

When a gap is discovered during research:

1. Classify the gap kind:
   - `missing_source` — need more literature or source material,
   - `missing_derivation` — need to complete a derivation,
   - `missing_capability` — need a new tool or method,
   - `contradiction` — conflicting results need resolution.

2. Route the gap:
   - `missing_source` -> spawn follow-up source task or child topic,
   - `missing_derivation` -> queue derivation action in current topic,
   - `missing_capability` -> enter capability loop or defer,
   - `contradiction` -> open conflict record, route to family fusion or gap
     recovery.

Gap classification and routing are NOT YET IMPLEMENTED as a first-class
dispatch mechanism. The `gap_map.md` renderer exists but does not emit gap
kinds.

See: `GAP_RECOVERY_PROTOCOL.md` for full recovery workflow.

## FL8. Followup Source Task

When a gap requires new source material:
- Create a follow-up source task with explicit search parameters.
- Route to L0 discovery and registration.
- Results may spawn a new child topic or enrich the current topic's L0.

The task records:
- `task_id`,
- `gap_id` (what gap it addresses),
- `search_parameters`,
- `status` (pending / in_progress / completed / failed),
- `results` (what was found),
- `created_at`, `updated_at`.

NOT YET IMPLEMENTED as a standalone data structure. Literature follow-up
queries in `closed_loop_v1.py` provide partial coverage.

## FL9. Implementation Status

### Currently implemented
- Sub-topic spawning with rich spawn contract (14+ fields).
- Child lifecycle with return packet population.
- Return shape validation against allowlist.
- Reintegration with structured receipt (20+ fields).
- Reintegration requirements policy enforcement.
- Automatic topic completion re-assessment after reintegration.
- Deferred candidate buffer with reactivation conditions (OR logic only).
- Candidate split contract with fingerprint deduplication.
- Consultation followup pattern.
- Gap writeback queue.
- Literature follow-up queries (partial coverage).

### Not yet implemented
- Blocking/non-blocking child semantics.
- `priority` and `deferred_at` fields on buffer entries.
- Expiration dates and `expired` status on deferred candidates.
- AND logic for reactivation conditions.
- Auto-triggered reactivation on source register / child complete / session start.
- Gap classification and routing as first-class dispatch.
- Followup source task as standalone data structure.
- `spawn_reason` field on spawn contract.

## FL10. What the Followup Lifecycle Should Not Do

- Silently drop deferred candidates.
- Reintegrate child results without a durable receipt.
- Block the parent indefinitely on a non-blocking child.
- Spawn children without a clear return packet.
- Treat child completion as automatic reintegration.
- Forget about deferred items across sessions.
