---
name: aitp-runtime
description: Use after AITP routing has claimed the task; continue theory work through the runtime bundle instead of ad hoc browsing or free-form synthesis.
---

# AITP Runtime

## Environment gate (mandatory first step)

- Confirm the task already belongs inside AITP.
- If bootstrap already ran, continue from the generated runtime bundle.
- If bootstrap did not run, use `aitp session-start "<original user request>"` to materialize routing and then return here.
- Do not replace the original user request with a bare title or a compressed paraphrase when using that fallback.

## Workflow

1. Resume or materialize runtime state through `aitp session-start`, `aitp loop`, `aitp resume`, or `aitp bootstrap` when needed.
2. **Classification step**: Before the first loop/resume call, load and apply the classification skills:
   - Load `aitp-research-classifier` → reason about research mode → call `aitp_record_classification(topic_slug, "research_mode", ...)`.
   - Load `aitp-load-profile-resolver` → reason about load profile → call `aitp_record_classification(topic_slug, "load_profile", ...)`.
   - When the action queue is being materialized, load `aitp-action-classifier` → reason about action type → call `aitp_record_classification(topic_slug, "action_type", ...)`.
   - When runtime mode is being selected, load `aitp-runtime-mode-selector` → reason about mode and submode → call `aitp_record_classification` for each.
3. Read `runtime_protocol.generated.md`.
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
17. report the current human-control posture in plain language before deeper work.
18. If no active checkpoint is present, continue bounded execution instead of asking ritual permission again.
19. If iterative verify is active, keep the L3-L4 loop moving until success, a real blocker, or a real human checkpoint appears.
20. If bootstrap tooling fails, recover by rerunning the canonical CLI front door; do not hand-edit runtime artifacts or source-layer records just to simulate progress.
21. For physics-style report writing and derivation-heavy topic communication, explicitly load the repo subskills:
    - `aitp-problem-framing`
    - `aitp-derivation-discipline`
    - `aitp-l3-l4-round`
    - `aitp-current-claims-auditor`
    - `aitp-topic-report-author`
22. Treat those subskills as content-generation aids; keep Python/runtime responsible for durable state, gates, and notebook compilation.

## Popup gate rule (all interactive sessions — mandatory)

When the AITP runtime hits a human gate (promotion approval, operator checkpoint, decision point, or H-plane steering), you MUST surface it as an interactive popup. You MUST NOT silently continue past a gate.

1. **Before every loop/resume/bootstrap call**, call `aitp_get_popup` for the target `topic_slug`.
2. If `needs_popup` is `true`:
   - STOP. Do not call `aitp_run_topic_loop`, `aitp_bootstrap_topic`, or `aitp_resume_topic` yet.
   - Use the pre-built `ask_user_question` field from the response.
     - **Claude Code**: Pass `ask_user_question.questions` directly to the `AskUserQuestion` tool. Map the 0-based response back via `ask_user_question.choice_index_map`.
     - **Kimi Code CLI**: Pass `ask_user_question.questions` to the `AskUserQuestion` tool. Map the 0-based response back via `ask_user_question.choice_index_map`.
   - If `ask_user_question.inspect_path` is non-empty and the user wants details, read that file and re-present the popup.
   - When the user chooses, call `aitp_resolve_popup` with the mapped `choice_index`.
3. **After every loop/resume/bootstrap call**, call `aitp_get_popup` again. The loop may have materialized a new gate.
4. Only proceed with deeper execution once `needs_popup` is `false`.
5. **Hard rule**: You MUST NOT skip the popup check. You MUST NOT answer the research question instead of presenting the popup. A popup means AITP requires a human decision before any further automated work.

## Conversation style rules

- Do not say things like `I am emitting a decision_point` or `I am switching to the full load profile`.
- Surface checkpoints as ordinary research dialogue, for example:
  - `There are two reasonable routes here. I can tighten the benchmark first, or I can push directly to the larger-system scan.`
- Keep checkpoint questions short and route-changing.
- If the user says `you decide`, `just go`, or `直接做`, treat that as authorization to proceed, then write the durable trace in the background.
- Do not append protocol-compliance commentary to ordinary user-facing answers unless the user explicitly asks for protocol state.

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
