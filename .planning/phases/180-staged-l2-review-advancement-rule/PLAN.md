# Phase 180 Plan: Staged-L2 Review Advancement Rule

## Objective

Advance beyond the static staged-L2 review summary when the operator continues
after that review point.

## Plan

1. Add a queue rule that detects a later `continue` decision after the latest
   topic-local staged entry.
2. When that condition holds, replace the old staged-review fallback with a new
   bounded post-review route.
3. Cover the change with a focused queue-materialization regression.
