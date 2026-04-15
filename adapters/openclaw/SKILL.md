---
name: aitp-runtime
description: Enter the AITP runtime from OpenClaw so topic work remains auditable, resumable, and governed by the AITP charter.
---

# AITP Runtime For OpenClaw

Use this skill when the task belongs inside AITP rather than a free-form note
workflow.

## Start here

```bash
aitp loop --topic-slug <topic_slug> --human-request "<task>"
```

Then read `runtime_protocol.generated.md` before acting on the queue.

If the topic does not exist yet:

```bash
aitp bootstrap --topic "<topic>" --statement "<statement>"
```

If the idea is still vague after routing, ask clarification questions before
full execution. Tighten `scope`, `assumptions`, and `target_claims` first.

Use Phase 6 records during the run:

```bash
aitp emit-decision --topic-slug <topic_slug> --question "<question>" --options "<json>" --blocking false
aitp resolve-decision --topic-slug <topic_slug> --decision-id <dp_id> --option <index>
aitp resolve-checkpoint --topic-slug <topic_slug> --option <index> --comment "<why>"
aitp chronicle --topic-slug <topic_slug>
```

## Before finishing

```bash
aitp audit --topic-slug <topic_slug> --phase exit
```

## Hard rules

- If conformance fails, the run does not count as AITP work.
- Prefer durable contracts and control notes over fallback heuristics.
- Do not present exploratory output as validated reusable knowledge.
- Treat human checkpoints as decision points plus decision traces, not as disposable chat state.
