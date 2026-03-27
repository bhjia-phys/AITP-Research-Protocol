# Decision Point Protocol

This file defines the public AITP contract for AITP-initiated questioning at
critical decision nodes.

The goal is not to create a background controller.
The goal is to make human checkpoints durable, inspectable, and resumable when
AITP needs a real choice rather than a silent heuristic.

## 1. Purpose

AITP already has a durable human steering surface through `control_note.md`.
That is the human-initiated side.

This protocol defines the AITP-initiated side:

- when AITP must ask a question,
- how that question is written to disk,
- when the question is blocking,
- and how the answer becomes a durable part of the topic history.

This protocol uses `decision-point.schema.json`.

## 2. Core object

A `decision_point` is a structured question with:

- a durable id,
- a topic slug,
- a phase,
- a layer context,
- a human-readable question,
- at least two options,
- explicit blocking semantics,
- an optional default option,
- a trigger rule,
- and an optional resolution object.

The canonical storage surface is:

- `runtime/topics/<topic_slug>/decision_points/<decision_point_file>.json`

The logical id remains the protocol id such as `dp:jones-ch4-route-choice`.
Implementations may map that id to a filesystem-safe filename when needed.

## 3. Lifecycle

The lifecycle is:

1. AITP reaches a decision node that is not already fixed by the active
   research-question, validation, or steering contract.
2. AITP emits a `decision_point` object into the topic runtime.
3. The pending question is surfaced to the operator through
   `runtime/topics/<topic_slug>/operator_console.md` under
   `## Pending Decision Points`.
4. The human resolves the decision by editing the JSON, using
   `aitp resolve-decision ...`, or by answering in chat and letting the agent
   materialize that answer.
5. The resolved decision point remains durable and should produce a matching
   `decision_trace`.

## 4. Mandatory triggers

AITP should emit a decision point when a real human choice is needed, including:

- scope change:
  the research question's scope, assumptions, or non-goals need revision
- method uncertainty:
  two or more competing methods have unclear trade-offs
- benchmark disagreement:
  a reproduced benchmark conflicts with the expected result
- promotion gate:
  any `L4 -> L2` promotion attempt
- direction ambiguity:
  the user's natural-language request is underspecified
- resource choice:
  local vs remote execution or another expensive execution choice matters
- gap recovery route:
  the loop must choose between `L0` follow-up, local refinement, or deferral

## 5. Forbidden shortcuts

AITP should not emit decision points for routine noise.

Do not emit a decision point for:

- routine file creation inside an already-scoped plan
- `L1` extraction work from a source that is already in scope
- any step where the active research-question contract already specifies the
  choice

Do not silently replace a real decision point with ad hoc chat prose if the
choice would matter in a later session.

## 6. Blocking semantics

The public interpretation must stay:

- `blocking: true`
  - AITP pauses the bounded loop
  - the agent must not continue substantive research work until the decision is
    resolved
- `blocking: false` with `default_option_index`
  - AITP may continue after a timeout or explicit skip using the declared
    default
- `blocking: false` without a default
  - AITP should warn that the choice remains open, but may continue if the
    operator does not answer

The storage surface is still only files plus agent-visible chat behavior.
This protocol does not authorize background pause/resume controllers.

## 7. Resolution surface

Humans may resolve a decision point by:

- editing the `decision_point` JSON to fill in `resolution`
- using:

```bash
aitp resolve-decision --topic-slug <topic_slug> --decision-id <dp_id> --option <index>
```

- or answering in natural language and letting the agent translate that answer
  into a durable resolution

Resolution should record:

- the chosen option index
- an optional human comment
- the resolution time
- and the resolver identity such as `human` or `auto_timeout`

## 8. Integration

This protocol extends `AUTONOMY_AND_OPERATOR_MODEL.md` by making the decision
loop a first-class operator-visible surface.

It also interacts with existing surfaces as follows:

- `control_note.md`
  - remains the human-initiated steering surface
  - if a decision point causes a true scope redirect, the resulting human
    decision should also update `control_note.md`
- `decision_trace`
  - every resolved non-trivial decision point should produce a
    `decision_trace`
- `operator_console.md`
  - should expose unresolved pending decision points directly

The practical rule is:

- `control_note.md` is the human asking AITP to redirect
- `decision_point` is AITP asking the human to choose

They are dual surfaces, not replacements for one another.

## 9. Charter alignment

The Charter already legitimizes explicit human checkpoints for high-impact
choices.

This protocol operationalizes that principle by making checkpoints durable,
queryable, and visible in the topic runtime rather than leaving them implicit in
chat memory.
