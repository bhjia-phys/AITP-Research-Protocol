# Phase 148: Hypothesis Branch Routing Surface

## Status

passed

## Goal

Close the next post-`v1.73` gap by making branch intent explicit per competing
hypothesis on the active topic surface.

## Background

AITP already has:

- question-level `competing_hypotheses`
- deferred candidate parking and reactivation
- follow-up subtopics and reintegration
- innovation-direction steering with continue/branch/redirect decisions

But it still lacks one explicit place to say:

- this hypothesis stays on the current topic branch
- this hypothesis should park in deferred form
- this hypothesis deserves a follow-up branch
- this hypothesis is excluded and should not own an active branch

## Requirements

- add bounded branch-routing metadata per competing hypothesis
- keep route kind and target summary explicit on runtime/replay surfaces
- make the new routing surface coexist with steering, deferred candidates, and
  follow-up subtopics
- add one isolated acceptance lane for the bounded hypothesis-routing path

## Depends On

Phase 147 (`v1.73` closure must remain closed and available as the base layer)

## Deliverables

1. hypothesis branch-routing research-question/runtime surface
2. replay/read-path visibility for active versus parked hypothesis routes
3. isolated acceptance and aligned docs/tests

## Plans

- [x] `148-01`: add hypothesis branch-routing metadata to question/runtime surfaces and isolated acceptance
