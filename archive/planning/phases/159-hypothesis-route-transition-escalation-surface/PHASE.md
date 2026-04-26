# Phase 159: Hypothesis Route Transition Escalation Surface

## Status

complete

## Goal

Close the next post-`v1.84` gap by turning transition repair into an
operator-visible transition-escalation surface.

## Background

AITP already has:

- question-level `competing_hypotheses`
- bounded `route_activation`, `route_reentry`, `route_handoff`, and
  `route_choice` visibility
- bounded `route_transition_gate`, `route_transition_intent`,
  `route_transition_receipt`, `route_transition_resolution`,
  `route_transition_discrepancy`, and `route_transition_repair` visibility

But it still lacks one explicit place to say:

- when bounded transition repair should escalate into a human checkpoint
- which repair state triggered that escalation
- how that escalation relates back to the current repair plan
- how that escalation coexists with the current helper mechanisms

## Requirements

- derive one bounded route transition-escalation summary from route transition
  repair plus operator-checkpoint context
- expose route-transition escalation through runtime/read-path/replay surfaces
- keep the transition-escalation surface coexistence with current
  transition-repair and helper mechanisms
- add one isolated acceptance lane for the bounded transition-escalation path

## Depends On

Phase 158 (`v1.84` route transition-repair visibility must remain closed and
available as the base layer)

## Deliverables

1. hypothesis route transition-escalation runtime surface
2. replay/read-path visibility for explicit bounded escalation state
3. isolated acceptance and aligned docs/tests

## Plans

- [x] `159-01`: add route transition-escalation summary to runtime/replay
  surfaces and isolated acceptance
