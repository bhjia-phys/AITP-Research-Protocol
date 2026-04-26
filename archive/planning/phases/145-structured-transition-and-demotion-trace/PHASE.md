# Phase 145: Structured Transition And Demotion Trace

## Status

pending

## Goal

Close the runtime-history gap by making forward and backward layer transitions
first-class, durable, and replayable instead of leaving them implicit across
`resume_stage`, `last_materialized_stage`, and scattered runtime notes.

## Background

The current runtime can tell the operator where a topic is now, but not the
full bounded path that got it there.

Existing surfaces already include:

- `resume_stage`
- `last_materialized_stage`
- `promotion_trace.latest.json`
- `topic_replay_bundle`

But they still do not close:

- explicit backward layer moves
- demotion reasons with evidence refs
- one structured answer to “what was overturned and why?”

## Requirements

- add one structured transition log for layer moves
- let demotion/backtrack reasons stay explicit and durable
- surface the history through runtime-facing replay/read paths
- add one isolated acceptance lane for the new history path

## Depends On

Phase 144 (`v1.70` closure must complete first)

## Deliverables

1. structured transition/demotion runtime artifact(s)
2. replay/read-path exposure for those artifacts
3. isolated acceptance and aligned docs/tests

## Plans

- [ ] `145-01`: add runtime transition/demotion trace, replay surface, and isolated acceptance
