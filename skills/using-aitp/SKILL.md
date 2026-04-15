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
10. report the current human-control posture in plain language before deeper work.
11. If no active checkpoint is present, continue bounded execution instead of asking ritual permission again.

## Popup gate protocol (mandatory before every topic action)

1. Immediately after resolving the current topic, call `aitp_get_topic_popup(topic_slug=<current>)`.
2. If the returned `kind` is `"none"`, continue normally.
3. If `kind` is not `"none"`, a human-blocking gate is active. **Stop all other work.**
4. Present the popup using the best native UI available in the current environment:
   - **Claude Code**: Call the built-in `AskUserQuestion` tool with:
     - `question`: the popup `title` + a newline + the `summary`
     - `options`: an array mapping each popup `options` entry to `{label: <option label>, description: <option description>}`
     - `multi_select`: false
     - Append a final fallback option `{label: "Defer / View details", description: "Pause and let me read more before deciding"}` if useful.
   - **OpenCode**: Call the built-in `question` tool with an equivalent structured payload (question text + options list). If the native `question` tool is unavailable, fall back to rendering the options as a numbered Markdown list and reading the reply.
   - **Other environments (fallback)**: Render the popup as natural-language text:
     - State the `title` and `summary` in plain language.
     - List the `options` (usually 2–4), explaining the trade-off of each route.
     - Ask the user to pick one option.
5. Once the user chooses, map the selected option back to its 0-based index in the original `popup.options` array, then call `aitp_resolve_popup_choice(topic_slug=<current>, choice=<that index>, comment="<brief rationale>")`.
6. If the user declines to choose, defers, or picks the defer option, treat that as a pause and do not proceed past the gate.
7. Only after `kind == "none"` (or a successful resolution returns a clear next step) should you continue with `status`, `next`, or deeper AITP work.
8. This applies at:
   - The very start of every topic-bound interaction.
   - After any `aitp loop`, `aitp next`, or `aitp status` return.
   - Whenever the user says anything that might advance or alter topic state.

## Allowed exception

- If the task is AITP repo maintenance rather than AITP-governed research execution, work directly on the codebase.
- Even then, preserve the layer model, runtime artifacts, audits, promotion gates, and trust semantics.

## Red flags

- "I can just answer this research question directly."
- "This topic change is small enough to skip routing."
- "I will read files first and decide later whether AITP applies."

If one of these is true, stop and enter AITP first.
