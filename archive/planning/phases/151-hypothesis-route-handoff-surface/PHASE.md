# Phase 151: Hypothesis Route Handoff Surface

## Status

passed

## Goal

Close the next post-`v1.76` gap by turning re-entry-ready parked routes into an
operator-visible handoff surface for concrete next-step decisions.

## Background

AITP already has:

- question-level `competing_hypotheses`
- explicit per-hypothesis route metadata
- bounded `route_activation` visibility for the active local route
- bounded `route_reentry` visibility for parked-route waiting versus readiness

But it still lacks one explicit place to say:

- which re-entry-ready parked route should become a concrete next-step handoff
  candidate
- which ready parked routes should remain parked despite being technically
  ready
- how ready parked routes relate to the current local action and queue
- how these handoff candidates coexist with the deferred-reactivation and
  follow-up reintegration helpers

## Requirements

- derive one bounded route handoff summary from the current local route plus
  ready parked-route signals
- expose ready parked-route handoff candidates and keep-parked decisions on
  runtime/replay surfaces
- keep the handoff surface coexistence with the current action queue,
  route_activation, route_reentry, and existing helper mechanisms
- add one isolated acceptance lane for the bounded route handoff path

## Depends On

Phase 150 (`v1.76` route re-entry visibility must remain closed and available
as the base layer)

## Deliverables

1. hypothesis route handoff runtime surface
2. replay/read-path visibility for ready parked-route handoff candidates
3. isolated acceptance and aligned docs/tests

## Plans

- [x] `151-01`: add route handoff summary to runtime/replay surfaces and
  isolated acceptance
