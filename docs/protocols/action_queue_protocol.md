# Action Queue Protocol

Domain: Brain
Authority: subordinate to AITP SPEC S4.
Merges: DECISION_TRACE_PROTOCOL.md.
References: runtime/DECLARATIVE_RUNTIME_CONTRACTS.md,
runtime/DEFERRED_RUNTIME_CONTRACTS.md.

---

## AQ1. Role

The action queue is the ordered list of executable actions that the Brain
maintains for each topic. It bridges the closed-loop cycle to concrete work
items.

## AQ2. Queue Sources

Actions enter the queue from three sources:

1. **Heuristic generation** — the Brain infers the next action from topic state,
   research question, and unfinished work. Stored as `queue_source: "heuristic"`.
2. **Control note directive** — the human explicitly requests an action through
   a control note or operator console edit. Stored as `queue_source: "control_note"`.
3. **Declarative contract** — a deferred or declared runtime contract
   specifies an action to be executed when its conditions are met.
   Stored as `queue_source: "declared_contract"`.

Priority: control note > declared contract > heuristic.

## AQ3. Action Shape

### Protocol-Specified Fields
Every action in the queue should specify:

- `action_id` — stable identifier (format: `action:{topic_slug}:{index}`),
- `action_type` — what kind of action (source_acquisition, analysis, validation,
  promotion, gap_recovery, consultation, capability_improvement, ...),
- `description` — what the action does,
- `auto_runnable` — whether the action can execute without human approval,
- `status` — pending / in_progress / completed / failed.

### Implementation Fields (Actual)
The code generates queue rows with these fields:

```json
{
  "action_id": "action:{topic_slug}:{index}",
  "topic_slug": "...",
  "resume_stage": "L0|L1|L3|L4",
  "status": "pending",
  "action_type": "...",
  "summary": "...",
  "auto_runnable": true|false,
  "handler": null,
  "handler_args": {},
  "queue_source": "heuristic|control_note|declared_contract",
  "declared_contract_path": null
}
```

### Not Yet Implemented
The protocol envisions these fields on each action, but they are not present:
- `layer` — which layer the action targets (replaced by `resume_stage`),
- `mode` — which mode the action requires (tracked at runtime contract level, not per-action),
- `inputs` — what the action needs,
- `expected_outputs` — what the action should produce,
- `blocked_by` — inter-action blocking (only inter-topic blocking exists),
- `created_at`, `updated_at`.

## AQ4. Queue Shaping

### Priority Ordering
- Control-note actions override heuristic selection. The code does not reorder
  the queue itself; instead, `decide_next_action.py` overrides which action is
  *selected* when a control note directive is present.
- Unblockable actions (no blockers, auto-runnable) are preferred.
- Actions that unblock other actions: NOT YET IMPLEMENTED. The ranking policy
  (`policy_ranked_pending`) only distinguishes system blockers from non-blockers.

### Mode Compliance
- Actions must be compatible with the current mode envelope.
- If the mode is `discussion`, no verify or promote actions are queued.
- Mode transitions queue new action types.

### Dependency Resolution
- Respect inter-topic blocking relationships.
- **Circular dependency detection**: NOT YET IMPLEMENTED. No cycle-detection
  algorithm exists anywhere in the codebase.
- Prefer action orderings that maximize throughput.

### Queue Shaping Policies
The implementation provides queue shaping policies that suppress queue expansion
based on operator checkpoints, promotion routing, backedge transitions, and
human checkpoint requirements:
- `allow_capability_append` — allow capability improvement actions,
- `allow_runtime_append` — allow runtime contract actions,
- `allow_closed_loop_append` — allow closed-loop actions,
- `allow_literature_followup_append` — allow literature follow-up actions.

This policy system is NOT described in the original protocol.

## AQ5. Auto-Runnable Decision

An action is auto-runnable when:
- it is within the current mode envelope,
- it has no unresolved blockers,
- it does not require human approval (no L2 write, no direction change,
  no high-impact decision),
- it has bounded scope and resource requirements.

The Brain may execute auto-runnable actions without human checkpoint, but
must re-checkpoint when:
- the queue is exhausted,
- a mode transition is needed (handled indirectly by re-orchestration),
- an action fails,
- **stuckness is detected**: NOT YET IMPLEMENTED as an algorithm. "stuckness"
  appears as a keyword in trigger sets but has no detection logic in the
  auto-run loop.

## AQ6. Decision Trace

Every significant queue decision is recorded in a decision trace.

### Protocol-Specified Fields
- `decision_id` — stable identifier,
- `trigger` — what caused the decision,
- `decision` — what was decided,
- `rationale` — why,
- `alternatives_considered` — what else was possible,
- `created_at`.

### Implementation Fields (Actual)
The code uses a richer schema (`schemas/decision-trace.schema.json`):

```json
{
  "id": "dt:{topic_slug}:{index}",
  "topic_slug": "...",
  "timestamp": "...",
  "decision_summary": "...",
  "chosen": "...",
  "rationale": "...",
  "input_refs": [...],
  "context": "...",
  "decision_point_ref": "...",
  "options_considered": [{"option": "...", "pros": [...], "cons": [...]}],
  "would_change_if": "...",
  "output_refs": [...],
  "layer_transition": "...",
  "related_traces": [...]
}
```

The implementation schema is richer than the protocol describes. Vocabulary
mismatches: `decision_id` → `id`, `trigger` → `decision_point_ref` + `context`,
`decision` → `decision_summary` + `chosen`, `alternatives_considered` →
`options_considered` (with structured pros/cons), `created_at` → `timestamp`.

Decision traces are append-only. They are not edited after creation (implicitly
enforced by write-only pattern, no defensive immutability check).

## AQ7. Unfinished Work Index

The Brain maintains an index of all incomplete actions:
- pending actions (not yet started),
- in-progress actions (started but not completed),
- blocked actions (waiting on dependencies),
- deferred actions (parked with reactivation conditions).

This index is the primary surface for "what is left to do" queries.

## AQ8. Pending Decisions

When an action requires human input before it can proceed, the Brain creates
a pending decision.

### Protocol-Specified Fields (per decision)
- `decision_id`,
- `question` — what needs to be answered,
- `options` — possible choices,
- `trigger_rule` — what created this decision,
- `blocking` — whether other actions are blocked by this decision,
- `status` — unresolved / resolved / expired.

### Implementation Fields (Actual)
The `pending_decisions.json` uses an aggregate summary format:

```json
{
  "topic_slug": "...",
  "pending_count": 0,
  "blocking_count": 0,
  "unresolved_ids": [],
  "latest_resolved_trace_ref": "",
  "latest_resolved_summary": "",
  "updated_at": "...",
  "updated_by": "..."
}
```

Individual decision points are stored separately under `decision_points/`
directory with their own schema (see `decision_point_handler.py`), with fields
matching the protocol's per-decision intent: `id`, `question`, `options`,
`status`, `trigger_rule`, `blocking`.

Pending decisions are presented to the human through the popup gate protocol.

## AQ9. Declarative and Deferred Contracts

### Declarative Contracts
Actions that are authored explicitly by the human, not inferred by the Brain.
These live in `runtime/DECLARATIVE_RUNTIME_CONTRACTS.md`.

The implementation also supports a declared action contract mechanism
(`next_actions.contract.json`) that overrides heuristic queue synthesis, and
a separate decision contract override (`next_action_decision.contract.json`)
that overrides the next-action decision.

### Deferred Contracts
Actions that are parked with reactivation conditions. These live in
`runtime/DEFERRED_RUNTIME_CONTRACTS.md`.

Reactivation conditions currently support:
- source-based (`source_ids_any`) — reactivate when sources appear,
- text-based (`text_contains_any`) — reactivate on content match,
- event-based (`child_topics_any`) — reactivate on child topic presence.

NOT YET IMPLEMENTED:
- time-based reactivation (reactivate after a date),
- state-based reactivation (reactivate when topic reaches a specific stage).

Deferred actions are not forgotten. They remain inspectable in the queue.

## AQ10. Queue Construction Pipeline

The implementation constructs queues through a multi-phase pipeline NOT
described in the original protocol:

1. **Closed-loop actions** — select_route, materialize_task, dispatch_execution_task,
   await_execution_result, ingest_execution_result phases.
2. **Post-promotion followup routing** — multi-step routing after promotion with
   incrementally escalating thresholds.
3. **Followup subtopic spawning and reintegration** — spawn child topics and
   process their return packets.
4. **Auto-promotion pipeline** — automatically generate promotion actions when
   coverage, consensus, and regression gates pass.
5. **Candidate split contracts** — decompose wide/mixed candidates.
6. **Lean bridge preparation** — refresh formal proof-state sidecars.
7. **Topic completion gate** — assess when a topic is done.
8. **Literature intake staging** — with SHA1 signature deduplication.
9. **Obsolete action pruning** — remove stale promotion and source-expansion actions.

Additional surfaces generated during orchestration:
- `interaction_state.json`,
- `operator_console.md`,
- `agent_brief.md`.

## AQ11. Topic Loop Lifecycle

The entry/exit lifecycle for topic loops is NOT in the original protocol but
is implemented in `topic_loop_support.py`:
- Entry audit: capability audit, trust audit, load profile resolution,
- Loop state persistence between iterations,
- Exit conditions and topic completion assessment,
- Re-checkpoint after each auto-step batch.

## AQ12. Implementation Status

### Currently implemented
- Three queue sources (heuristic, control_note, declared_contract) with priority.
- Action queue rows with action_id, action_type, summary, auto_runnable, status.
- Decision traces with richer-than-protocol schema.
- Pending decisions (aggregate summary + individual decision points).
- Control note override for action selection.
- Queue shaping policies (capability, runtime, closed_loop, literature append).
- Closed-loop execution pipeline (5 phases).
- Post-promotion followup routing.
- Followup subtopic spawning and reintegration.
- Auto-promotion pipeline.
- Candidate split contracts.
- Literature intake staging with deduplication.
- Obsolete action pruning.
- Compatibility path projection (dual-path layout).
- Topic loop lifecycle (entry/exit audit, loop state persistence).

### Not yet implemented
- Per-action `layer` field (replaced by `resume_stage`).
- Per-action `mode` field (tracked at runtime contract level).
- Per-action `inputs` and `expected_outputs` fields.
- Inter-action `blocked_by` (only inter-topic blocking exists).
- Per-action `created_at` and `updated_at` timestamps.
- Circular dependency detection.
- Unblocking-throughput optimization.
- Stuckness detection algorithm.
- Time-based and state-based deferred reactivation.
- Bounded scope and resource requirement checking for auto-runnable decisions.

## AQ13. What the Queue Should Not Do

- Silently reorder actions to avoid human checkpoints.
- Auto-execute actions that require human approval.
- Drop failed actions without recording the failure.
- Invent actions not grounded in the research question or control note.
- Treat queue exhaustion as topic completion.
