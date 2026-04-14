# Phase 182.2 Plan: Fresh Post-Selection Route Choice Replay Proof

## Objective

Close `v2.8` with one replayable fresh-topic packet for post-selection route
choice closure.

## Plan

1. Add one isolated acceptance script that replays the fifth bounded continue
   step after selected-candidate advancement.
2. Assert that the same topic derives one bounded deeper route choice and
   exposes it on public surfaces.
3. Re-run the `v2.4` through `v2.7` acceptance chain to prove no regression.
