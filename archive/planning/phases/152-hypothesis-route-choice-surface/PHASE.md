# Phase 152: Hypothesis Route Choice Surface

## Status

passed

## Goal

Close the next post-`v1.77` gap by turning the current local route plus the
primary parked-route handoff candidate into one hypothesis-aware route-choice
surface.

## Background

AITP already has:

- question-level `competing_hypotheses`
- explicit per-hypothesis route metadata
- bounded `route_activation` visibility for the active local route
- bounded `route_reentry` visibility for parked-route waiting versus readiness
- bounded `route_handoff` visibility for the primary parked-route handoff
  candidate

But it still lacks one explicit place to say:

- whether the current local route should stay local or yield to the handoff
  candidate
- how the current route choice relates to the primary handoff candidate
- how that choice interacts with the existing `current_route_choice` and
  `next_bounded_action` surfaces
- how the choice remains declarative before any automatic runtime mutation

## Requirements

- derive one bounded route choice summary from the active local route plus the
  primary handoff candidate
- expose stay-local versus yield-to-handoff choice on runtime/replay surfaces
- keep the choice surface coexistence with the current `current_route_choice`,
  `route_activation`, `route_reentry`, and `route_handoff` surfaces
- add one isolated acceptance lane for the bounded route-choice path

## Depends On

Phase 151 (`v1.77` route handoff visibility must remain closed and available as
the base layer)

## Deliverables

1. hypothesis route choice runtime surface
2. replay/read-path visibility for stay-local versus yield-to-handoff choice
3. isolated acceptance and aligned docs/tests

## Plans

- [x] `152-01`: add route choice summary to runtime/replay surfaces and
  isolated acceptance
