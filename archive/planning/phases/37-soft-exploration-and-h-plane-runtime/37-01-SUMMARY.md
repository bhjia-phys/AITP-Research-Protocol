# Phase 37 Plan 01 Summary

Date: 2026-04-09
Status: Complete

## One-line outcome

Runtime now distinguishes bounded exploratory continuation from ordinary route
continuation by supporting `free_explore` plus a lightweight
`exploration_window` carrier.

## What changed

- Added `free_explore` to the runtime interaction contract family.
- Added a lightweight exploration carrier:
  - `runtime/topics/<topic_slug>/exploration_window.json`
  - `runtime/topics/<topic_slug>/exploration_window.md`
- Exposed `exploration_window` in the runtime bundle and added it to
  `must_read_now` when bounded exploration is active.
- Kept checkpoint and writeback behavior unchanged:
  - blocking checkpoints still force `checkpoint_question`
  - writeback and validation hard gates are not softened

## Verification

- `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py -q`
  - `12 passed`
- `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "free_explore or supports_free_explore" -q`
  - `1 passed`
- `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -q`
  - `12 passed`
- `python -m pytest research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_aitp_cli.py research/knowledge-hub/tests/test_aitp_cli_e2e.py research/knowledge-hub/tests/test_runtime_profiles_and_projections.py research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_l2_graph_activation.py research/knowledge-hub/tests/test_topic_start_regressions.py -q`
  - `133 passed`

## Physicist-Facing Judgment

From the perspective of a theoretical physicist using AITP, this phase matters
because it reduces a real failure mode:

1. AITP can now say “I am still in bounded exploration” instead of pretending
   every non-blocking state is the same as route-following continuation.
2. Early idea work gets a durable but lightweight carrier instead of forcing
   premature formal closure.
3. Hard trust boundaries remain where they should be:
   validation, writeback, and blocking human decisions are still not softened.

## Remaining Limit

This is still a bounded first slice, not the final interaction model.

Later work can improve:
- exploration detection beyond keyword heuristics,
- richer `H-plane` timing and intervention semantics,
- and deeper task-type-aware orchestration.
