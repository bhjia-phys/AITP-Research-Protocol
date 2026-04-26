# Phase 149: Hypothesis Route Activation Surface

## Status

passed

## Goal

Close the next post-`v1.74` gap by turning explicit hypothesis route metadata
into an operator-visible route-activation surface.

## Background

AITP already has:

- question-level `competing_hypotheses`
- explicit per-hypothesis route metadata
- deferred candidate parking
- follow-up subtopics
- innovation-direction steering

But it still lacks one explicit place to say:

- what the active local-route hypothesis implies for the concrete next step
- what parked deferred-route hypotheses are currently waiting on
- what follow-up-route hypotheses imply for current operator attention
- how those route obligations relate to the existing action queue

## Requirements

- derive one bounded route-activation summary from explicit hypothesis routes
- expose active local-route action versus parked-route obligations on
  runtime/replay surfaces
- keep the activation surface coexistence with the current action queue,
  steering, deferred candidates, and follow-up subtopics
- add one isolated acceptance lane for the bounded route-activation path

## Depends On

Phase 148 (`v1.74` routing visibility must remain closed and available as the
base layer)

## Deliverables

1. hypothesis route-activation runtime surface
2. replay/read-path visibility for active versus parked-route obligations
3. isolated acceptance and aligned docs/tests

## Plans

- [x] `149-01`: add hypothesis route activation summary to runtime/replay surfaces and isolated acceptance
