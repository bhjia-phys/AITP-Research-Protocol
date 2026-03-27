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
5. Keep the lightweight runtime minimum current even when the full runtime bundle is not present:
   - `topic_state.json`
   - `operator_console.md`
   - `research_question.contract.json`
   - `control_note.md`
6. Keep `innovation_direction.md` and `control_note.md` current before touching the active queue.
7. Before substantive work, check unresolved decision points. If any pending item is `blocking: true`, stop and ask the human instead of continuing execution.
8. Emit a decision point when a real route choice appears and the active contract does not already settle it.
9. After a non-trivial resolution, materialize a paired decision trace so later "why did AITP do this?" questions can be answered from durable records instead of chat memory.
10. Maintain a session chronicle as the operator-facing narrative surface:
    - reuse the current open chronicle or create one
    - record notable actions, problems, and decision-trace refs during the session
    - finalize the chronicle when the bounded session exits
11. Expand consultation, promotion, capability, or deferred surfaces only when the runtime bundle names them.
12. Register reusable operations with `aitp operation-init ...`.
13. Use `aitp baseline ...`, `aitp atomize ...`, and `aitp trust-audit ...` before claiming reusable method progress.
14. Use `aitp request-promotion ...` plus explicit approval for human-reviewed `L2`.
15. Use `aitp coverage-audit ...` before `aitp auto-promote ...` for theory-formal `L2_auto`.
16. Close bounded work with `aitp audit --topic-slug <topic_slug> --phase exit`.

## Hard rules

- Missing conformance means the work does not count as AITP work.
- Current-topic routing, steering updates, trust gates, and promotion gates are durable state, not optional reminders.
- Do not silently upgrade exploratory output into reusable knowledge.
- Do not bypass the runtime bundle with ad hoc file browsing once AITP has claimed the task.
- "AITP pause" means the agent asks the human in chat and records the decision point; it does not mean a background controller or hidden event loop exists.
- Decision traces and chronicles are first-class runtime records, not optional prose summaries.

## Common commands

```bash
aitp session-start "<task>"
aitp loop --topic-slug <topic_slug> --human-request "<task>"
aitp resume --topic-slug <topic_slug> --human-request "<task>"
aitp bootstrap --topic "<topic>" --statement "<statement>"
aitp emit-decision --topic-slug <topic_slug> --question "<question>" --options "<json>" --blocking false
aitp resolve-decision --topic-slug <topic_slug> --decision-id <dp_id> --option <index>
aitp list-decisions --topic-slug <topic_slug> --pending-only
aitp trace-decision --topic-slug <topic_slug> --summary "<summary>" --chosen "<choice>" --rationale "<why>"
aitp chronicle --topic-slug <topic_slug>
aitp operation-init --topic-slug <topic_slug> --run-id <run_id> --title "<operation>" --kind numerical
aitp trust-audit --topic-slug <topic_slug> --run-id <run_id>
aitp request-promotion --topic-slug <topic_slug> --candidate-id <candidate_id> --backend-id backend:theoretical-physics-knowledge-network
aitp approve-promotion --topic-slug <topic_slug> --candidate-id <candidate_id>
aitp coverage-audit --topic-slug <topic_slug> --candidate-id <candidate_id> --source-section <section> --covered-section <section>
aitp auto-promote --topic-slug <topic_slug> --candidate-id <candidate_id> --target-backend-root <tpkn_root>
aitp audit --topic-slug <topic_slug> --phase exit
```
