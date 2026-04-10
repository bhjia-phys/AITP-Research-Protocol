# Topic replay protocol

Status: draft

This file defines a derived topic replay bundle for human study and review.

## 1. Why this exists

AITP already preserves durable topic artifacts.

That is enough for the system to resume a topic, but it is not yet the same as
giving a human an easy way to study:

- what the topic was about,
- what it concluded,
- what to read first,
- and where the authoritative artifacts live.

This protocol adds that missing replay/study layer.

## 2. Core stance

The topic replay bundle is:

- derived,
- human-readable,
- on-demand,
- and explicitly non-authoritative.

It should help a human learn a topic from disk.
It must not become a new truth source.

## 3. Outputs

For topic `<topic_slug>`, the replay bundle should materialize:

- `runtime/topics/<topic_slug>/topic_replay_bundle.json`
- `runtime/topics/<topic_slug>/topic_replay_bundle.md`

## 4. Minimum contents

A valid replay bundle should contain:

- topic overview
- current position and last durable state
- key conclusions or completion posture
- reusable outputs when present
- ordered reading path
- authoritative artifact pointers
- explicit missing-artifact notices when necessary

## 5. Source priority

Replay generation should prefer these sources when present:

1. `topic_synopsis.json`
2. `topic_state.json`
3. `research_question.contract.json|md`
4. `validation_review_bundle.active.json|md`
5. `topic_completion.json|md`
6. `topic_skill_projection.active.json|md`
7. `runtime_protocol.generated.json|md`
8. `resume.md`

The replay bundle may summarize them.
It may not replace them.

## 6. Reading-path rule

The replay bundle should give the human an explicit reading order.

The reading path should prefer:

- one current-state entry surface
- one question/scope surface
- one review/completion surface
- one reusable-output surface when available
- one deeper runtime/read-order surface for further digging

## 7. Honesty rule

If a topic lacks one or more expected artifacts, the replay bundle should say
so directly.

It should not patch the gap with invented prose.

## 8. Relationship to `L2`

The replay bundle is not the same thing as `L2`.

- `L2` stores reusable promoted knowledge
- topic replay explains one topic's trajectory and reading path

Replay may point at `L2` outputs, but does not replace them.

## 9. Relationship to `L5`

The replay bundle is also not the same thing as `L5`.

- replay is for learning and review
- `L5` is for publication-grade output

Replay may support later `L5`, but it is not manuscript production.

## 10. One-line doctrine

Topic replay should help a human study a topic from durable artifacts without
changing what the authoritative artifacts actually are.
