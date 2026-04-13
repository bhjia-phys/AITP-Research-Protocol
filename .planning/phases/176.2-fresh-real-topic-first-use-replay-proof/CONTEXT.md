# Context: Phase 176.2 Fresh Real-Topic First-Use Replay Proof

## Why this phase exists

Phase `176` repaired fresh-topic `session-start` routing. Phase `176.1`
repaired Windows-safe source registration and immediate post-registration source
visibility. The last bounded step of `v2.2` is to replay those two fixes on one
fresh first-use lane so the milestone closes with a mechanical proof package
rather than chat-memory claims.

## What this phase must prove

- a fresh real-topic request can start from the public first-run lane
- the same lane can continue into first-source registration
- after registration, status surfaces immediately expose `source_count >= 1`
- the replay is mechanical and script-backed

## Files in scope

- `research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py`
- `research/knowledge-hub/tests/test_runtime_scripts.py`

## Boundaries

- Do not widen the scientific claim set; this is an operator-path replay proof
  only.
- Do not redesign the bounded L0 handoff text after registration; the proof is
  about fresh first-use correctness, not post-registration planner semantics.
