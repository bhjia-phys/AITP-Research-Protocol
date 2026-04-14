# Phase 181.2 Plan: Fresh Consultation-Followup Selection Replay Proof

## Objective

Close `v2.7` with one replayable fresh-topic packet for consultation-followup
selection closure.

## Plan

1. Add one isolated acceptance script that replays the fourth bounded continue
   step after staged-L2 review.
2. Assert that consultation-followup executes, the selection artifact exists,
   and public `next` / `status` advance to the selected candidate summary.
3. Re-run the `v2.4`, `v2.5`, and `v2.6` acceptance chain to prove no
   regression.
