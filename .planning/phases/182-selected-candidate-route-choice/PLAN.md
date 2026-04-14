# Phase 182 Plan: Selected-Candidate Route Choice

## Objective

Advance beyond the selected staged-candidate summary by deriving one bounded
deeper route choice from durable candidate-selection state.

## Plan

1. Add a route-choice rule that reads the selected consultation-followup
   artifact and picks one bounded next route.
2. Persist that route choice as a durable runtime artifact rather than only a
   transient queue guess.
3. Cover the change with a focused queue-materialization regression.
