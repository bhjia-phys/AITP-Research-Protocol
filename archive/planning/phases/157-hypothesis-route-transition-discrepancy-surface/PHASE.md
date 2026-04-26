# Phase 157: Hypothesis Route Transition Discrepancy Surface

## Status

complete

## Goal

Close the next post-`v1.82` gap by turning inconsistent route-transition state
into an operator-visible discrepancy surface.

## Background

AITP already has:

- question-level `competing_hypotheses`
- bounded `route_activation`, `route_reentry`, `route_handoff`, and
  `route_choice` visibility
- bounded `route_transition_gate`, `route_transition_intent`,
  `route_transition_receipt`, and `route_transition_resolution` visibility

But it still lacks one explicit place to say:

- whether the bounded transition state is internally inconsistent
- which upstream route artifacts disagree with the current resolved transition
  outcome
- how severe that discrepancy is for the current operator path
- how that discrepancy coexists with the current resolution and helper
  mechanisms

## Requirements

- derive one bounded route transition-discrepancy summary from route transition
  resolution plus upstream route artifacts
- expose route-transition discrepancy through runtime/read-path/replay surfaces
- keep the transition-discrepancy surface coexistence with current
  transition-resolution and helper mechanisms
- add one isolated acceptance lane for the bounded transition-discrepancy path

## Depends On

Phase 156 (`v1.82` route transition-resolution visibility must remain closed and
available as the base layer)

## Deliverables

1. hypothesis route transition-discrepancy runtime surface
2. replay/read-path visibility for explicit inconsistent transition state
3. isolated acceptance and aligned docs/tests

## Plans

- [x] `157-01`: add route transition-discrepancy summary to runtime/replay
  surfaces and isolated acceptance
