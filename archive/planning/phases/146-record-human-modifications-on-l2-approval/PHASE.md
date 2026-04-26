# Phase 146: Record Human Modifications On L2 Approval

## Status

pending

## Goal

Close the promotion-gate evaluator-divergence gap by recording what a human
changed when approving an `L2` promotion, not just that they approved it.

## Background

`promotion_gate.json` already records:

- who requested approval
- who approved or rejected
- the gate status

But it still does not answer:

- what the human changed before approval
- why the human changed it
- whether the approved result materially diverged from the submitted candidate

Now that `v1.71` records structured transition/demotion history, this is the
next clean bounded human-override signal to make durable.

## Requirements

- record optional structured human modification rows on approval
- keep them visible in `promotion_gate` plus replay/read paths
- keep unchanged approvals explicit as unchanged rather than pretending all
  approvals are modified
- add one isolated modified-approval acceptance lane

## Depends On

Phase 145 (`v1.71` closure must complete first)

## Deliverables

1. promotion-gate human modification record
2. replay/read-path visibility for modified approvals
3. isolated acceptance and aligned docs/tests

## Plans

- [ ] `146-01`: add human modification capture on approval, replay surface, and isolated acceptance
