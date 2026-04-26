# Phase 165: Real Topic L0 To L2 End-To-End Validation

## Status

pending

## Goal

Validate one real idea through the current AITP implementation from initial
idea entry to an honest bounded outcome across the `L0 -> L1 -> L3 -> L4 -> L2`
research path, and turn every problem discovered during that run into explicit
GSD-tracked follow-up work.

## Background

AITP now has:

- a public install path and front-door verification surface
- a bounded first-run `bootstrap -> loop -> status` path
- a bounded quick-exploration entry path
- explicit runtime/control-plane/layer-graph surfaces
- explicit promotion, replay, statement-compilation, and Lean-bridge surfaces

But it still lacks one milestone that proves whether the current protocol and
implementation are genuinely useful on a real topic from an initial idea.

## Requirements

- run at least one real topic from an initial idea through the current public
  AITP entry surfaces
- capture the actual route, artifacts, friction, and outcome in a durable
  postmortem
- convert every discovered issue into explicit GSD-tracked follow-up work
- keep the milestone honest about whether the topic ended in `L2`,
  `promotion-ready`, or a blocked / deferred state

## Depends On

Phase 164 (`v1.90` route-transition authority visibility remains closed and is
available as part of the runtime read path)

## Deliverables

1. real-topic E2E execution runbook and issue-capture rules
2. one primary real-topic postmortem with durable artifact refs
3. one explicit issue ledger that routes findings into backlog / decimal-phase
   follow-up instead of leaving them implicit

## Plans

- [ ] `165-01`: execute one real-topic E2E route and capture all findings into
  GSD-visible artifacts
