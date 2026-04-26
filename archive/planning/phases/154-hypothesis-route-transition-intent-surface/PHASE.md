# Phase 154: Hypothesis Route Transition Intent Surface

## Status

complete

## Goal

Close the next post-`v1.79` gap by turning route-transition eligibility into an
operator-visible transition-intent surface.

## Background

AITP already has:

- question-level `competing_hypotheses`
- bounded `route_activation`, `route_reentry`, `route_handoff`, and
  `route_choice` visibility
- bounded `route_transition_gate` visibility

But it still lacks one explicit place to say:

- what source route would yield to what target route once the gate clears
- whether that transition intent is only proposed, blocked, or checkpoint-held
- which durable artifact carries that declarative transition intent
- how that intent coexists with the current gate and helper mechanisms

## Requirements

- derive one bounded route transition-intent summary from route choice plus
  existing route-transition-gate state
- expose route-transition intent through runtime/read-path/replay surfaces
- keep the transition-intent surface coexistence with current route gate and
  helper mechanisms
- add one isolated acceptance lane for the bounded transition-intent path

## Depends On

Phase 153 (`v1.79` route transition-gate visibility must remain closed and
available as the base layer)

## Deliverables

1. hypothesis route transition-intent runtime surface
2. replay/read-path visibility for explicit source-to-target transition intent
3. isolated acceptance and aligned docs/tests

## Plans

- [x] `154-01`: add route transition-intent summary to runtime/replay surfaces
  and isolated acceptance
