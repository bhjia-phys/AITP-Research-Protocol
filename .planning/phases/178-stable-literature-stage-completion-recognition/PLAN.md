# Phase 178 Plan: Stable Literature-Stage Completion Recognition

## Objective

Stop requeueing the same completed fresh-topic `literature_intake_stage` and
advance the route onto staged-`L2` review.

## Plan

1. Add a stable signature for the current literature-intake candidate set so a
   successful stage can be recognized after queue regeneration.
2. Persist that signature in staged-entry provenance and teach both the
   service-side auto-action path and runtime-side queue appender to skip
   requeueing when a matching staged signature already exists.
3. When the literature stage is already satisfied, advance the fallback
   next-action summary onto staged-`L2` review rather than the earlier L1-only
   wording.
4. Cover the repair with focused service and runtime-script regressions.
