# OpenClaw AITP agent entrypoint

This file defines the minimal executable entrypoint an OpenClaw-side agent should use when it wants to enter AITP as a routed workflow rather than as ad hoc file browsing.

## Purpose

An agent should be able to:
- bootstrap a new topic,
- register incoming sources,
- resume an existing topic,
- advance the current runtime loop,
- and read one generated brief before doing deeper work.

## Primary command

Use the OpenClaw-native single-entry loop:

```bash
python3 research/adapters/openclaw/scripts/aitp_loop.py --help
```

Typical resume usage by slug:

```bash
python3 research/adapters/openclaw/scripts/aitp_loop.py \
  --topic-slug haldane-shastry-chaos-transition \
  --run-id 2026-03-12-otoc-krylov-extension \
  --control-note /home/bhj/projects/repos/Theoretical-Physics/obsidian-markdown/11\ L4\ Validation/active/2026-03-12_hs-chaos-otoc-krylov-validation.md \
  --human-request "Continue the current topic and keep the runtime state operator-visible." \
  --max-steps 1
```

Typical resume usage with active-topic default:

```bash
python3 research/adapters/openclaw/scripts/aitp_loop.py
```

The loop resolves the best unfinished topic from `research/knowledge-hub/runtime/topic_index.jsonl`, materializes fresh runtime state through the internal orchestrator, optionally dispatches allowlisted auto actions, and refreshes exit conformance.

Typical bootstrap usage with sources:

```bash
python3 research/adapters/openclaw/scripts/aitp_loop.py \
  --topic "Haldane-Shastry chaos transition" \
  --statement "Extend the current note with OTOC and Krylov diagnostics." \
  --local-note-path /home/bhj/Theoretical-Physics/obsidian-markdown/04\ 平时的记录/可积与混沌/Haldane-Shastry\ SU\(N\)\ Chain/Haldane-Shastry\ SU\(N\)\ Chain.md \
  --arxiv-id 2104.09514 \
  --skill-query "scientific problem selection" \
  --max-steps 1
```

`python3 research/adapters/openclaw/scripts/aitp_topic_runner.py ...` remains as a compatibility wrapper and now delegates to the same loop surface.

## Outputs

The delegated orchestrator materializes:
- `research/adapters/openclaw/state/heartbeat_state.json`
- `research/adapters/openclaw/state/heartbeat_history.jsonl`
- `runtime/topics/<topic_slug>/topic_state.json`
- `runtime/topics/<topic_slug>/resume.md`
- `runtime/topics/<topic_slug>/action_queue.jsonl`
- `runtime/topics/<topic_slug>/agent_brief.md`
- `runtime/topics/<topic_slug>/interaction_state.json`
- `runtime/topics/<topic_slug>/operator_console.md`
- `runtime/topics/<topic_slug>/loop_state.json`
- `runtime/topics/<topic_slug>/loop_history.jsonl`
- `runtime/topics/<topic_slug>/selected_validation_route.json` when a closed-loop route has been selected
- `runtime/topics/<topic_slug>/execution_task.json` when a closed-loop execution handoff has been materialized
- `runtime/topics/<topic_slug>/execution_task.md` when a closed-loop execution handoff note has been materialized
- `runtime/topics/<topic_slug>/execution_handoff_receipts.jsonl` when the external execution lane is auto-dispatched
- `runtime/topics/<topic_slug>/conformance_state.json`
- `runtime/topics/<topic_slug>/conformance_report.md`
- `runtime/topics/<topic_slug>/skill_discovery.json` when `--skill-query` is used
- `runtime/topics/<topic_slug>/skill_recommendations.md` when `--skill-query` is used
- `runtime/topics/<topic_slug>/action_receipts.jsonl` when allowlisted auto actions are dispatched
- `validation/topics/<topic_slug>/runs/<run_id>/returned_execution_result.json` as the external result-ingest contract
- `validation/topics/<topic_slug>/runs/<run_id>/execution_notes/` for external-lane prompt, tmux-session metadata, logs, and final report
- `validation/topics/<topic_slug>/runs/<run_id>/execution_notes/codex_session.json` for the live/background Codex session state
- `validation/topics/<topic_slug>/runs/<run_id>/execution_notes/codex_session_receipts.jsonl` for start/wait/submit/kill receipts
- `validation/topics/<topic_slug>/runs/<run_id>/results/result_manifest.json` after result ingestion
- `validation/topics/<topic_slug>/runs/<run_id>/decision_ledger.jsonl` after result ingestion
- `validation/topics/<topic_slug>/runs/<run_id>/literature_followup_receipts.jsonl` when bounded follow-up search runs

## Current scope

The OpenClaw-side entrypoint now handles:
- topic bootstrap shells,
- Layer 0 arXiv intake,
- Layer 0 local-note intake,
- runtime-state refresh,
- typed action-queue generation,
- loop-state and loop-history materialization,
- operator-visible runtime artifacts,
- optional external-skill discovery materialization,
- bounded auto-dispatch of allowlisted runtime actions.

It does not yet replace research judgment.
The agent still needs to decide how to satisfy non-trivial pending actions.

The minimal closed-loop v1 now supports:
- selecting one validation route,
- materializing one execution handoff task,
- auto-dispatching that task to Codex when `needs_human_confirm=false`,
- launching that Codex task inside a tmux-backed session so the operator can inspect logs or intervene while the loop waits for completion,
- ingesting one returned execution result artifact,
- recovering a truthful `partial` returned result when durable execution artifacts exist but the external lane omitted the required return JSON,
- writing a bounded decision + follow-up surface without claiming scientific success by default,
- auto-running bounded arXiv follow-up search for emitted literature queries.

When the blocker is a missing workflow or tool capability, the agent should use:

- `research/adapters/openclaw/SKILL_ADAPTATION_PROTOCOL.md`
- `research/adapters/openclaw/scripts/discover_external_skills.py`

before concluding that the current runtime cannot proceed.

Allowlisted queue dispatch remains available as an internal subcommand:

```bash
python3 research/adapters/openclaw/scripts/dispatch_action_queue.py \
  --topic-slug <topic_slug>
```

To let one cron/runner advance multiple honest steps in sequence, increase `--max-actions`:

```bash
python3 research/adapters/openclaw/scripts/dispatch_action_queue.py \
  --topic-slug <topic_slug> \
  --max-actions 5
```

Heartbeat should usually be declared in the workspace `HEARTBEAT.md` and advance one bounded step through the canonical CLI:

```bash
AITP_KERNEL_ROOT="$PWD/research/knowledge-hub" AITP_REPO_ROOT="$PWD" \
  aitp loop --updated-by openclaw-heartbeat --max-auto-steps 1 --json
```

If the topic is already clear:

```bash
AITP_KERNEL_ROOT="$PWD/research/knowledge-hub" AITP_REPO_ROOT="$PWD" \
  aitp loop --topic-slug <topic_slug> --updated-by openclaw-heartbeat --max-auto-steps 1 --json
```

Keep `HEARTBEAT_AITP.md` in the workspace root as the durable policy note for when heartbeat should choose AITP and how it should acknowledge progress.

The compatibility bridge remains available when you want explicit adapter-owned scheduler receipts:

```bash
python3 research/adapters/openclaw/scripts/heartbeat_bridge.py \
  --topic-slug <topic_slug>
```

The bridge resolves the best unfinished topic when no slug is provided and delegates to `aitp_loop.py --max-steps 1`. It also maintains adapter-owned scheduler state in `research/adapters/openclaw/state/heartbeat_state.json` and `research/adapters/openclaw/state/heartbeat_history.jsonl`.

To inspect or control a running Codex execution session directly:

```bash
python3 research/adapters/openclaw/scripts/codex_session_controller.py \
  status --metadata-path validation/topics/<topic_slug>/runs/<run_id>/execution_notes/codex_session.json

python3 research/adapters/openclaw/scripts/codex_session_controller.py \
  log --metadata-path validation/topics/<topic_slug>/runs/<run_id>/execution_notes/codex_session.json

python3 research/adapters/openclaw/scripts/codex_session_controller.py \
  submit --metadata-path validation/topics/<topic_slug>/runs/<run_id>/execution_notes/codex_session.json --text y

python3 research/adapters/openclaw/scripts/codex_session_controller.py \
  kill --metadata-path validation/topics/<topic_slug>/runs/<run_id>/execution_notes/codex_session.json
```

At session close, refresh the conformance audit explicitly when needed:

```bash
python3 research/knowledge-hub/runtime/scripts/audit_topic_conformance.py \
  --topic-slug <topic_slug> \
  --phase exit
```
