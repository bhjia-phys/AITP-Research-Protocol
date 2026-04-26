# Phase 38 Plan 01 Summary

Date: 2026-04-09
Status: Complete

## One-line outcome

AITP now exposes `task_type` in runtime and topic artifacts, so exploratory,
conjectural, and target-driven work are no longer collapsed into one implicit
mode.

## What changed

- Added bounded `task_type` inference with the first operational set:
  - `open_exploration`
  - `conjecture_attempt`
  - `target_driven_execution`
- Wrote `task_type` through:
  - research contract
  - idea packet
  - runtime active research contract
  - topic synopsis
- Extended runtime/topic schemas so `task_type` is now contract-visible.

## Verification

- `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py -q`
  - `12 passed`
- `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "task_type" -q`
  - `1 passed`
- `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py research/knowledge-hub/tests/test_schema_contracts.py -q`
  - `25 passed`
- `python -m pytest research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_aitp_cli.py research/knowledge-hub/tests/test_aitp_cli_e2e.py research/knowledge-hub/tests/test_runtime_profiles_and_projections.py research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_l2_graph_activation.py research/knowledge-hub/tests/test_topic_start_regressions.py -q`
  - `134 passed`

## Physicist-Facing Judgment

From the perspective of a theoretical physicist using AITP, this phase matters
because the system can now explicitly say what kind of job it thinks it is
doing:

1. open exploration is no longer merely inferred from the current tone of the
   request,
2. conjectural bridge-sharpening is no longer flattened into generic work,
3. target-driven execution can now be distinguished from discussion-oriented
   work before deeper routing logic is added.

## Remaining Limit

`task_type` is now visible, but runtime interaction has not yet been fully made
task-type-aware.

That is the job of Phase `39`.
