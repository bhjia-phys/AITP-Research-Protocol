# Phase 144: L1 Assumption Ledger And Reading Depth Surface

## Status

pending

## Goal

Close the still-open `999.27` intake-honesty remainder by making
source-backed assumptions, recorded reading depth, and shallow/conflicting
evidence first-class on the real `L1` operator path.

## Background

`v1.64` already closed one bounded slice of `999.27` through
`method_specificity_rows`, but the assumption/depth side of the same intake
story is only partially surfaced today.

The codebase already contains:

- `assumption_rows`
- reading-depth labels
- helper-level conflict/ambiguity signals

but they have not yet been closed as their own acceptance-backed milestone in
the way `method_specificity_rows` already has.

## Requirements

- extend the existing `l1_source_intake` path instead of creating a parallel
  intake artifact
- make assumption and reading-depth evidence visible through production
  `status` / runtime read paths
- keep shallow/conflicting evidence explicit rather than flattening it away
- add one isolated acceptance lane plus targeted docs/tests for this exact
  surface

## Depends On

Phase 143 (`v1.69` closure must complete first)

## Deliverables

1. strengthened `L1` assumption/depth operator surface
2. one isolated acceptance script for the assumption/depth lane
3. aligned runtime docs and contract tests

## Plans

- [ ] `144-01`: close the `L1` assumption/depth surface, acceptance lane, and docs
