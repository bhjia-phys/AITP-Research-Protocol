# Runtime resume surface

This directory is the cross-layer runtime registry for AITP topics.

It is not a new epistemic layer.
It is a durable control surface that summarizes where a topic currently stands across `L1`, `L3`, `L4`, and `consultation`, so the next agent can resume from disk without reconstructing state by hand.

## Purpose

Use `runtime/` to answer three operational questions quickly:

1. what is the latest durable state of a topic,
2. which layer should resume next,
3. which concrete files should be opened first.

## Layout

- `topics/<topic_slug>/topic_state.json`
  - machine-readable topic snapshot
- `topics/<topic_slug>/resume.md`
  - human-readable resume brief
- `topics/<topic_slug>/interaction_state.json`
  - machine-readable human-input, autonomy, and layer-edit contract
- `topics/<topic_slug>/operator_console.md`
  - human-readable operator view of the active loops and editable surfaces
- `topics/<topic_slug>/loop_state.json`
  - latest loop-level execution summary
- `topics/<topic_slug>/loop_history.jsonl`
  - append-only history of loop runs
- `topics/<topic_slug>/unfinished_work.json`
  - machine-readable ordered unfinished-work index
- `topics/<topic_slug>/unfinished_work.md`
  - human-readable unfinished-work note
- `topics/<topic_slug>/next_action_decision.json`
  - authoritative machine-readable next-action decision
- `topics/<topic_slug>/next_action_decision.md`
  - human-readable next-action decision note
- `topics/<topic_slug>/action_queue_contract.generated.json`
  - generated queue-contract snapshot showing the current executable queue in declarative form
- `topics/<topic_slug>/action_queue_contract.generated.md`
  - human-readable queue-contract snapshot
- `topics/<topic_slug>/conformance_state.json`
  - machine-readable audit status for AITP runtime conformance
- `topics/<topic_slug>/conformance_report.md`
  - human-readable conformance report
- `topic_index.jsonl`
  - one-row registry for the latest known state of each topic
- `scripts/sync_topic_state.py`
  - helper that materializes the runtime state from existing layer artifacts
- `topics/<topic_slug>/action_queue.jsonl`
  - typed next-action queue derived from the current topic state
- `topics/<topic_slug>/agent_brief.md`
  - human-readable route and execution brief for the next agent
- `topics/<topic_slug>/selected_validation_route.json`
  - one selected validation lane for the current closed-loop step
- `topics/<topic_slug>/execution_task.json`
  - concrete execution handoff artifact for the external runtime
- `topics/<topic_slug>/execution_task.md`
  - human-readable execution handoff note with return-path contract
- `topics/<topic_slug>/execution_handoff_receipts.jsonl`
  - receipts for auto-dispatched external execution tasks
- `validation/topics/<topic_slug>/runs/<run_id>/execution_notes/codex_session.json`
  - tmux-backed Codex session state for a live external execution handoff
- `validation/topics/<topic_slug>/runs/<run_id>/execution_notes/codex_session_receipts.jsonl`
  - start/wait/submit/kill receipts for the live Codex session
- `scripts/orchestrate_topic.py`
  - internal topic bootstrap + resume orchestrator used by the public loop surface

## Rules

- `runtime/` does not replace layer-local source-of-truth files.
- `runtime/` only summarizes and points to those files.
- Every active topic should refresh its runtime state after a meaningful `L1`, `L3`, or `L4` update.
- The resume target should prefer the fallback route implied by the latest decision artifact when one exists.
- Runtime should expose the human-visible operator contract rather than forcing the next agent or human to reconstruct it manually.
- Runtime should materialize both an unfinished-work index and a next-action decision so the loop is inspectable rather than implicit.
- Runtime should prefer declared contracts when they exist and only fall back to heuristics when they do not.
- Runtime should also expose a conformance report so non-AITP operation becomes visible rather than implicit.
- Runtime may materialize one thin closed-loop control step, but it must never claim that heavy execution already happened unless a returned execution result artifact is present.

## Minimal required pointers

Each `topic_state.json` should point to:

- intake status,
- latest feedback run status,
- latest validation decision,
- next-actions file when present,
- consultation index,
- active control-plane note when present.

## Resume semantics

The important distinction is:

- `last_materialized_stage`
  - the latest stage that emitted durable artifacts
- `resume_stage`
  - the stage where the next real work should continue

These are often different.
For example, an `L4` run may end with a `deferred` verdict that sends work back to `L3`.

## Current workflow

1. run `python3 research/adapters/openclaw/scripts/aitp_loop.py --topic-slug <topic_slug> --max-steps 1`
2. open `runtime/topics/<topic_slug>/resume.md`, `operator_console.md`, `unfinished_work.md`, and `next_action_decision.md`
3. follow `resume_stage`, `unfinished_work`, and the selected next-action decision
4. after new work lands, advance the loop again instead of hand-maintaining runtime state

When you want to reduce heuristic behavior further, use:

- `feedback/.../next_actions.contract.json` for an explicit L3 action queue
- `runtime/.../next_action_decision.contract.json` for an explicit next-action choice

For internal runtime work, the lower-level orchestrator still exists:

```bash
python3 runtime/scripts/orchestrate_topic.py \
  --topic-slug haldane-shastry-chaos-transition
```

For the minimal closed-loop v1, the external executor returns one JSON artifact at:

- `validation/topics/<topic_slug>/runs/<run_id>/returned_execution_result.json`
- `validation/topics/<topic_slug>/runs/<run_id>/execution_notes/`
- `validation/topics/<topic_slug>/runs/<run_id>/execution_notes/codex_session.json`
- `validation/topics/<topic_slug>/runs/<run_id>/execution_notes/codex_session_receipts.jsonl`
- `validation/topics/<topic_slug>/runs/<run_id>/literature_followup_receipts.jsonl`

The current OpenClaw adapter launches `codex exec` through a tmux-backed session controller so the
execution lane stays operator-visible even while the runtime waits for the returned result artifact.
Use:

```bash
python3 research/adapters/openclaw/scripts/codex_session_controller.py \
  status --metadata-path validation/topics/<topic_slug>/runs/<run_id>/execution_notes/codex_session.json
```

to inspect that live session, and swap `status` for `log`, `submit`, or `kill` when intervention is needed.

If the external executor leaves durable artifacts but misses the required return JSON, the OpenClaw handoff adapter may recover a truthful `partial` result so the runtime can ingest evidence instead of stalling. That recovery path must remain explicitly non-promotional and limitation-heavy.

The result contract template lives at:

- `validation/templates/execution-result.template.json`

Bounded literature follow-up search can be auto-run from emitted query records:

- `runtime/scripts/run_literature_followup.py`

When a capability gap needs external skill discovery, add one or more queries:

```bash
python3 research/adapters/openclaw/scripts/aitp_loop.py \
  --topic-slug haldane-shastry-chaos-transition \
  --skill-query "scientific problem selection" \
  --max-steps 1
```

Heartbeat should schedule the loop, not maintain a parallel state machine.
Prefer declaring this in the workspace heartbeat policy and running:

```bash
aitp loop --updated-by openclaw-heartbeat --max-auto-steps 1 --json
```

or, when the topic is explicit:

```bash
aitp loop --topic-slug <topic_slug> --updated-by openclaw-heartbeat --max-auto-steps 1 --json
```

Keep `HEARTBEAT_AITP.md` in the workspace root as the durable note that tells heartbeat when AITP should run.

For compatibility or explicit adapter-owned heartbeat receipts, you can still use:

```bash
python3 research/adapters/openclaw/scripts/heartbeat_bridge.py
```

which resolves the best unfinished topic and delegates to `aitp_loop.py --max-steps 1`.

## Constraint

The runtime surface is only useful if it remains thin and truthful.

Do not store large copied notes here.
Store summaries, stage decisions, and exact file pointers.

Use `runtime/CONTROL_NOTE_CONTRACT.md` when a human wants to redirect or pause
the loop through a durable steering note.

Use `runtime/DECLARATIVE_RUNTIME_CONTRACTS.md` when you want queue/decision
selection to be authored explicitly instead of inferred.
