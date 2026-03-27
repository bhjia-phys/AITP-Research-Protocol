# Session Chronicle Protocol

This file defines the public AITP contract for a human-readable narrative
summary of one AITP session.

The chronicle is not an audit replacement.
It is the operator-facing answer surface for "what happened, why, and what is
next?"

## 1. Purpose

AITP sessions often leave many durable artifacts.
That is necessary, but it is not sufficient for later human understanding.

This protocol defines a narrative companion that summarizes:

- where the topic started,
- what actions were taken,
- which decisions mattered,
- what problems appeared,
- where the topic ended,
- and what should happen next.

This protocol uses `session-chronicle.schema.json`.

## 2. Chronicle vs conformance report

The two surfaces serve different purposes:

- `conformance_report.md`
  - machine-audit-focused
  - asks whether the required artifacts and gates were present
- `session_chronicle.md`
  - human-understanding-focused
  - asks what happened, why it happened, and what remains open

Do not collapse these surfaces into one note.

## 3. When chronicles are created

A chronicle should be created:

- at `aitp audit --phase exit`
- or at `aitp complete-topic`

Implementations may also materialize or refresh a chronicle when the operator
explicitly asks for a session summary.

## 4. Storage surface

The canonical storage surface is:

- `runtime/topics/<topic_slug>/chronicles/<chronicle_file>.md`

with a companion:

- `runtime/topics/<topic_slug>/chronicles/<chronicle_file>.json`

The JSON follows the schema.
The Markdown is the primary operator-facing narrative surface.

## 5. Markdown template

```markdown
# Session Chronicle: <topic_slug>

**Session**: <chronicle_id>
**Date**: <session_start>
**Duration**: <session_end - session_start>

## Summary
<2-3 sentence narrative>

## Starting State
<Where the topic was when this session began>

## Actions Taken
- **<action>**: <result> -> [<artifacts>]

## Decisions Made
- <decision_trace_ref>: <one-line summary>

## Problems Encountered
- <problem>: <resolution | still open>

## Ending State
<Where the topic is now>

## Next Steps
1. <next action>

## Open Decision Points
- <decision_point_ref>: <question summary> [UNRESOLVED]
```

## 6. Query support

Chronicles are the primary surface for post-hoc human questions such as:

- what did we do last session on topic `X`
- why did this session stop here
- what is still open before the next step

Chronicles should cite relevant decision traces rather than repeating the whole
decision history inline.

## 7. Integration

Chronicles should integrate with:

- `decision_trace`
  - for the key decisions made in the session
- `decision_point`
  - for any unresolved operator questions
- `topic_state.json`
  - for the topic slug and current state snapshot

Chronicles should not silently replace the underlying runtime artifacts they
summarize.
