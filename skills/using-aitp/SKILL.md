---
name: using-aitp
description: Use when a request might be theoretical-physics research, topic continuation, idea steering, paper learning, derivation work, or validation planning; enter AITP before any substantial response.
---

# Using AITP

## Environment gate (mandatory first step)

- Confirm the task is happening in an AITP-enabled workspace, repo clone, or installed agent runtime.
- If the workspace has native bootstrap support, treat this skill as already active at session start.
- If native bootstrap is unavailable, fall back to `aitp session-start "<original user request>"`.
- Do not shorten that fallback into a bare topic title or a paraphrased summary when routing matters.

## When to use

- The user asks to study or continue a physics topic.
- The user says `继续这个 topic`, `current topic`, `this topic`, or equivalent.
- The user asks to change direction, refine scope, set validation, or update steering.
- The user asks to learn papers, evaluate an idea, recover a derivation, plan formalization, or build a bounded research loop.

## Hard gate

- If there is even a small chance the request is real theoretical-physics research rather than plain coding, enter AITP first.
- Do not start with free-form browsing, synthesis, or editing when the task belongs inside AITP.
- Treat natural-language steering as state, not chat decoration. If the user changes direction, update durable steering before deeper work.
- If the idea is vague, do not jump straight into `L0-L4`; run clarification first.

## Conversation style rules

- Do not expose protocol jargon to the user. Avoid phrases like `decision_point`, `L2 consultation`, `load profile`, or `runtime surface`.
- Ask in plain language, as if you are a research collaborator choosing the next route together.
- By default ask one question at a time. Only ask more than one when a single answer would still leave the route materially ambiguous.
- If the user already gave enough direction, do not ask a clarification question just to satisfy a protocol step.
- If the user says `you decide`, `just go`, `直接做`, or equivalent, stop clarifying, record the authorization durably, and continue.
- When giving options, explain the routes and tradeoffs in natural language instead of exposing JSON-style labels or schema fields.

## Clarification sub-protocol

1. Tighten the active `research_question.contract.json` before substantive execution whenever `scope`, `assumptions`, or `target_claims` are still vague.
2. Ask at most 3 clarification rounds, with 1-3 questions per round.
3. Prefer questions that remove the biggest ambiguity first: scope, assumptions, target claims, benchmark surface, or validation route.
4. When runtime state already exists, materialize these questions as decision points with:
   - `phase: clarification`
   - `trigger_rule: direction_ambiguity`
   - `blocking: false` unless the question is truly execution-critical
5. If the human says `just go`, `skip clarification`, or equivalent, proceed honestly and mark any still-missing critical fields as `clarification_deferred: true`.
6. Only enter normal `L0-L4` routing after clarification is complete or explicitly skipped.

## Routing rules

1. Resolve durable current-topic memory first.
2. Interpret `继续这个 topic`, `continue this topic`, `this topic`, and `current topic` as current-topic references before asking for a slug.
3. Fall back to the latest topic only when current-topic memory is missing.
4. If the user opens a new topic in natural language, extract the title and let AITP materialize the topic shell.
5. If native bootstrap times out while opening a new topic, retry through `aitp session-start "<original user request>"` or `aitp session-start --topic "<extracted title>" "<original user request>"`.
6. Do not replace a failed front-door bootstrap by manually editing runtime files, source-layer files, or topic artifacts unless the user explicitly asked for repository maintenance rather than topic execution.
7. If the user changes direction, scope, or control intent in natural language, translate that into `innovation_direction.md` and `control_note.md` updates before execution continues.
8. Preserve the lightweight runtime minimum even in small sessions:
   - `topic_state.json`
   - `operator_console.md`
   - `research_question.contract.json`
   - `control_note.md`
9. After AITP routing is materialized, load `aitp-runtime` and follow `runtime_protocol.generated.md`.
10. Before the first `aitp-runtime` step, ensure research mode and load profile are recorded by loading `aitp-research-classifier` and `aitp-load-profile-resolver` skills and calling `aitp_record_classification` for each classification.
10. report the current human-control posture in plain language before deeper work.
11. If no active checkpoint is present, continue bounded execution instead of asking ritual permission again.
12. When the topic is entering report-writing, derivation restoration, or round-by-round scientific narration, load the relevant repo skills:
   - `aitp-problem-framing`
   - `aitp-derivation-discipline`
   - `aitp-l3-l4-round`
   - `aitp-current-claims-auditor`
   - `aitp-topic-report-author`

## Popup gate protocol (mandatory before every topic action)

1. Immediately after resolving the current topic, call `aitp_get_popup(topic_slug=<current>)`.
2. If the returned `needs_popup` is `false`, continue normally.
3. If `needs_popup` is `true`, a human-blocking gate is active. **Stop all other work.**
4. **Present the popup using the pre-built `ask_user_question` field from the response.** The `aitp_get_popup` response contains an `ask_user_question` object that is already formatted for direct use:
   - **Claude Code**: Call the built-in `AskUserQuestion` tool with the `ask_user_question.questions` array as the `questions` parameter. Use `ask_user_question.choice_index_map` to translate the 0-based response back to the popup's `choice_index` for `aitp_resolve_popup`.
   - **OpenCode**: Call the built-in `question` tool with the same `questions` payload. Map the response through `choice_index_map` identically.
   - **Kimi Code CLI**: Call the built-in `AskUserQuestion` tool with the `ask_user_question.questions` array. Map the 0-based response back via `ask_user_question.choice_index_map` to the popup's `choice_index` for `aitp_resolve_popup`.
   - **Fallback (no structured question tool)**: Render the popup as a numbered list from `popup.choices`, ask the user to reply with a number, then map to `choice_index` via `choice_index_map`.
5. If `ask_user_question.inspect_path` is non-empty and the user asks for details, read that file and re-present the popup.
6. Once the user chooses, call `aitp_resolve_popup_choice(topic_slug=<current>, choice_index=<mapped index>, comment="<brief rationale>")`.
7. If the user declines to choose or defers, do NOT proceed past the gate. Wait for an explicit choice.
8. Only after `needs_popup` is `false` (or a successful resolution clears the gate) should you continue with `loop`, `resume`, or deeper AITP work.
9. This check is mandatory at:
   - The very start of every topic-bound interaction.
   - After every `aitp_run_topic_loop`, `aitp_resume_topic`, or `aitp_bootstrap_topic` call.
   - Whenever the user says anything that might advance or alter topic state.
10. **Hard rule**: You MUST NOT skip this check. You MUST NOT silently continue past a popup. You MUST NOT answer the research question instead of presenting the popup. A popup means AITP requires a human decision before any further work.

## Allowed exception

- If the task is AITP repo maintenance rather than AITP-governed research execution, work directly on the codebase.
- Even then, preserve the layer model, runtime artifacts, audits, promotion gates, and trust semantics.

## Red flags

- "I can just answer this research question directly."
- "This topic change is small enough to skip routing."
- "I will read files first and decide later whether AITP applies."

If one of these is true, stop and enter AITP first.
