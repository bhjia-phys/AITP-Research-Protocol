# Phase 150: Hypothesis Route Re-entry Surface

## Status

passed

## Goal

Close the next post-`v1.75` gap by turning parked-route reactivation and return
conditions into an operator-visible route re-entry surface.

## Background

AITP already has:

- question-level `competing_hypotheses`
- explicit per-hypothesis route metadata
- bounded `route_activation` visibility for the active local route
- deferred buffer reactivation conditions
- follow-up subtopic return packet semantics

But it still lacks one explicit place to say:

- what would reactivate a parked deferred-route hypothesis
- whether a parked route is still waiting or already re-entry-ready
- what a follow-up-route hypothesis is expected to return before parent-topic
  reintegration
- how those re-entry conditions relate to the existing deferred buffer and
  follow-up return artifacts

## Requirements

- derive one bounded route re-entry summary from existing deferred-buffer and
  follow-up return metadata linked to parked hypotheses
- expose deferred reactivation conditions and follow-up return readiness on
  runtime/replay surfaces
- keep the re-entry surface coexistence with the current deferred-reactivation
  helpers, follow-up subtopics, and route-activation surface
- add one isolated acceptance lane for the bounded route re-entry path

## Depends On

Phase 149 (`v1.75` route-activation visibility must remain closed and
available as the base layer)

## Deliverables

1. hypothesis route re-entry runtime surface
2. replay/read-path visibility for deferred reactivation and follow-up return
   readiness
3. isolated acceptance and aligned docs/tests

## Plans

- [x] `150-01`: add route re-entry summary to runtime/replay surfaces and
  isolated acceptance
