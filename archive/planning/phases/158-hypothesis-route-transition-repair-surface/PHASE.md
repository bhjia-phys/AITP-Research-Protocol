# Phase 158: Hypothesis Route Transition Repair Surface

## Status

complete

## Goal

Close the next post-`v1.83` gap by turning transition discrepancy into an
operator-visible transition-repair surface.

## Background

AITP already has:

- question-level `competing_hypotheses`
- bounded `route_activation`, `route_reentry`, `route_handoff`, and
  `route_choice` visibility
- bounded `route_transition_gate`, `route_transition_intent`,
  `route_transition_receipt`, `route_transition_resolution`, and
  `route_transition_discrepancy` visibility

But it still lacks one explicit place to say:

- what bounded repair plan the operator should follow when discrepancy is present
- which route artifacts should be corrected first
- how that repair plan relates back to the current discrepancy
- how that repair plan coexists with the current helper mechanisms

## Requirements

- derive one bounded route transition-repair summary from route transition
  discrepancy plus current route artifacts
- expose route-transition repair through runtime/read-path/replay surfaces
- keep the transition-repair surface coexistence with current
  transition-discrepancy and helper mechanisms
- add one isolated acceptance lane for the bounded transition-repair path

## Depends On

Phase 157 (`v1.83` route transition-discrepancy visibility must remain closed
and available as the base layer)

## Deliverables

1. hypothesis route transition-repair runtime surface
2. replay/read-path visibility for explicit bounded transition repair plan
3. isolated acceptance and aligned docs/tests

## Plans

- [x] `158-01`: add route transition-repair summary to runtime/replay surfaces
  and isolated acceptance
