---
name: using-aitp
description: Use when a request might be theoretical-physics research, topic continuation, idea steering, paper learning, derivation work, or validation planning; enter AITP before any substantial response.
---

# Using AITP

## Environment gate (mandatory first step)

- Confirm the task is happening in an AITP-enabled workspace, repo clone, or installed agent runtime.
- If the workspace has native bootstrap support, treat this skill as already active at session start.
- If native bootstrap is unavailable, fall back to `aitp session-start "<task>"`.

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
5. If the user changes direction, scope, or control intent in natural language, translate that into `innovation_direction.md` and `control_note.md` updates before execution continues.
6. Preserve the lightweight runtime minimum even in small sessions:
   - `topic_state.json`
   - `operator_console.md`
   - `research_question.contract.json`
   - `control_note.md`
7. After AITP routing is materialized, load `aitp-runtime` and follow `runtime_protocol.generated.md`.

## Allowed exception

- If the task is AITP repo maintenance rather than AITP-governed research execution, work directly on the codebase.
- Even then, preserve the layer model, runtime artifacts, audits, promotion gates, and trust semantics.

## Red flags

- "I can just answer this research question directly."
- "This topic change is small enough to skip routing."
- "I will read files first and decide later whether AITP applies."

If one of these is true, stop and enter AITP first.
