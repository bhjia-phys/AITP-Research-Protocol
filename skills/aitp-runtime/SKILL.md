---
name: aitp-runtime
description: Use after AITP routing has claimed the task; continue theory work through the runtime bundle instead of ad hoc browsing or free-form synthesis.
---

# AITP Runtime

## Environment gate (mandatory first step)

- Confirm the task already belongs inside AITP.
- If bootstrap already ran, continue from the generated runtime bundle.
- If bootstrap did not run, use `aitp session-start "<task>"` to materialize routing and then return here.

## Workflow

1. Resume or materialize runtime state through `aitp session-start`, `aitp loop`, `aitp resume`, or `aitp bootstrap` when needed.
2. Read `runtime_protocol.generated.md`.
3. Read the files listed under `Must read now`.
4. Treat `session_start.generated.md` as a routing audit artifact when it exists; it is backend state, not a user ritual.
5. Keep `innovation_direction.md` and `control_note.md` current before touching the active queue.
6. Expand consultation, promotion, capability, or deferred surfaces only when the runtime bundle names them.
7. Register reusable operations with `aitp operation-init ...`.
8. Use `aitp baseline ...`, `aitp atomize ...`, and `aitp trust-audit ...` before claiming reusable method progress.
9. Use `aitp request-promotion ...` plus explicit approval for human-reviewed `L2`.
10. Use `aitp coverage-audit ...` before `aitp auto-promote ...` for theory-formal `L2_auto`.
11. Close bounded work with `aitp audit --topic-slug <topic_slug> --phase exit`.

## Hard rules

- Missing conformance means the work does not count as AITP work.
- Current-topic routing, steering updates, trust gates, and promotion gates are durable state, not optional reminders.
- Do not silently upgrade exploratory output into reusable knowledge.
- Do not bypass the runtime bundle with ad hoc file browsing once AITP has claimed the task.

## Common commands

```bash
aitp session-start "<task>"
aitp loop --topic-slug <topic_slug> --human-request "<task>"
aitp resume --topic-slug <topic_slug> --human-request "<task>"
aitp bootstrap --topic "<topic>" --statement "<statement>"
aitp operation-init --topic-slug <topic_slug> --run-id <run_id> --title "<operation>" --kind numerical
aitp trust-audit --topic-slug <topic_slug> --run-id <run_id>
aitp request-promotion --topic-slug <topic_slug> --candidate-id <candidate_id> --backend-id backend:theoretical-physics-knowledge-network
aitp approve-promotion --topic-slug <topic_slug> --candidate-id <candidate_id>
aitp coverage-audit --topic-slug <topic_slug> --candidate-id <candidate_id> --source-section <section> --covered-section <section>
aitp auto-promote --topic-slug <topic_slug> --candidate-id <candidate_id> --target-backend-root <tpkn_root>
aitp audit --topic-slug <topic_slug> --phase exit
```
