# Phase 40 Plan 01 Summary

Date: 2026-04-09
Status: Complete

## One-line outcome

AITP now exposes a dedicated `task_type × lane` guidance surface, so the
runtime can say how different kinds of physics jobs should organize their first
loop instead of only labeling the job type.

## What changed

- Added `task_type_lane_guidance.json` and `task_type_lane_guidance.md` under
  the runtime topic root.
- Added a dedicated runtime bundle surface:
  - `task_type`
  - `lane`
  - normalized `lane_family`
  - summary
  - L0/L1/L3/L4/L2 writeback expectations
  - recommended first moves
  - human interaction bias
- Implemented distinct guidance for at least:
  - `open_exploration × formal_theory`
  - `conjecture_attempt × model_numeric`
  - `target_driven_execution × code_and_materials`

## Verification

- `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py -q`
  - `12 passed`
- `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "task_type_by_lane_guidance" -q`
  - `1 passed`
- `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py research/knowledge-hub/tests/test_schema_contracts.py -q`
  - `28 passed`
- `python -m pytest research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_aitp_cli.py research/knowledge-hub/tests/test_aitp_cli_e2e.py research/knowledge-hub/tests/test_runtime_profiles_and_projections.py research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_l2_graph_activation.py research/knowledge-hub/tests/test_topic_start_regressions.py -q`
  - `137 passed`

## Physicist-Facing Judgment

From the perspective of a theoretical physicist, this phase matters because
AITP can now articulate different first-loop expectations for different
research situations:

1. open formal-theory exploration is guided toward broader intake and route
   comparison,
2. conjectural model-numeric work is guided toward a smallest honest benchmark
   and a first real check,
3. target-driven code-and-materials work is guided toward narrowed sources,
   one hardened route, and an explicit benchmark burden.

## Next Step

Phase `41` should connect these guidance surfaces to collaborator routing and
human override so the user can steer AITP cleanly without collapsing back into
opaque control-note behavior.
