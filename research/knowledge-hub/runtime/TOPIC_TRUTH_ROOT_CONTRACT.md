# Topic Truth Root Contract

Status: active runtime contract

Scope: topic-owned state layout, Markdown authority, and compatibility projections.

## 1. Single Topic Root

Each topic owns one truth root:

- `topics/<topic_slug>/`

This folder is the only topic-owned root that humans should treat as authoritative.

## 2. Required Layout

Each topic root may contain:

- `topics/<topic_slug>/runtime/`
- `topics/<topic_slug>/L0/`
- `topics/<topic_slug>/L1/`
- `topics/<topic_slug>/L2/`
- `topics/<topic_slug>/L3/`
- `topics/<topic_slug>/L4/`
- `topics/<topic_slug>/consultation/`
- `topics/<topic_slug>/logs/`

Layer intent:

- `runtime/` keeps the live operator-facing and control-plane surfaces.
- `L0/` keeps source registration and source-local artifacts.
- `L1/` keeps intake and vault-style compiled reading state.
- `L2/` keeps promoted reusable knowledge.
- `L3/` keeps plan, execution, and feedback runs.
- `L4/` keeps validation runs and bounded review artifacts.

## 3. Markdown Authority

Human-readable state must be written as Markdown inside the topic root whenever a surface is intended for operator reading, review, planning, or later continuation.

Examples:

- `topics/<topic_slug>/runtime/topic_dashboard.md`
- `topics/<topic_slug>/runtime/operator_checkpoint.active.md`
- `topics/<topic_slug>/runtime/runtime_protocol.generated.md`
- `topics/<topic_slug>/L3/runs/<run_id>/next_actions.md`
- `topics/<topic_slug>/L4/runs/<run_id>/validation_summary.md`

Rule:

- if a human may need to read, review, steer, or resume from it, there must be a Markdown surface in the topic root.

## 4. JSON And JSONL Role

JSON and JSONL remain allowed, but they are machine-facing companions, not the primary human truth surface.

Use them for:

- structured runtime state
- append-only ledgers
- schemas, manifests, and deterministic replay inputs
- compatibility with scripts, MCP tools, and adapters

Do not treat a machine-facing JSON file as the only durable operator surface when the workflow requires human review or steering.

## 5. Compatibility Projection Rule

Legacy paths such as these may still exist during migration:

- `runtime/topics/<topic_slug>/...`
- `source-layer/topics/<topic_slug>/...`
- `intake/topics/<topic_slug>/...`
- `feedback/topics/<topic_slug>/...`
- `validation/topics/<topic_slug>/...`
- `consultation/topics/<topic_slug>/...`

These are compatibility projections only.

Operator-facing references, docs, runtime summaries, and adapter guidance should point at `topics/<topic_slug>/...` first.

## 6. Decision Rule For New Work

When adding or editing a topic-owned artifact:

1. Put the authoritative file under `topics/<topic_slug>/...`.
2. Write a Markdown companion when a human will read it.
3. Add JSON or JSONL only when structured machine state is actually needed.
4. Treat any legacy-root copy as a projection, not the source of truth.

## 7. One-Line Memory

`topics/<topic_slug>/...` is the topic truth root; Markdown is the human authority; JSON is the machine companion.
