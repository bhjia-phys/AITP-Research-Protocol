# Phase 153: Hypothesis Route Transition Gate Surface

## Status

complete

## Goal

Close the next post-`v1.78` gap by turning route-transition eligibility into an
operator-visible gate surface.

## Background

AITP already has:

- question-level `competing_hypotheses`
- bounded `route_activation`, `route_reentry`, `route_handoff`, and
  `route_choice` visibility

But it still lacks one explicit place to say:

- whether the current route is allowed to transition right now
- whether yielding to the handoff candidate is blocked, available, or gated by
  a human checkpoint
- which durable artifact is the gate for that transition
- how that transition gate coexists with the current route choice and helper
  mechanisms

## Requirements

- derive one bounded route transition-gate summary from route choice plus
  existing checkpoint/helper state
- expose route-transition availability versus gating on runtime/replay surfaces
- keep the transition-gate surface coexistence with current route choice and
  helper mechanisms
- add one isolated acceptance lane for the bounded transition-gate path

## Depends On

Phase 152 (`v1.78` route choice visibility must remain closed and available as
the base layer)

## Deliverables

1. hypothesis route transition-gate runtime surface
2. replay/read-path visibility for route-transition availability versus gating
3. isolated acceptance and aligned docs/tests

## Plans

- [x] `153-01`: add route transition-gate summary to runtime/replay surfaces
  and isolated acceptance
