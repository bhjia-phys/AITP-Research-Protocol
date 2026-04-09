# Phase 39 Plan 01 Summary

Date: 2026-04-09
Status: Complete

## One-line outcome

Runtime interaction posture now consults `task_type`, so exploratory work and
target-driven execution no longer default to the same continuation style.

## What changed

- Made `_derive_interaction_contract()` consult explicit `task_type` after the
  stronger blocker/update gates.
- `open_exploration` now defaults to `free_explore` when no stronger gate is
  active.
- `target_driven_execution` keeps preferring `silent_continue` unless a
  checkpoint, blocking decision, clarification gate, or non-blocking update
  reason overrides it.

## Verification

- `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "task_type_biases_interaction_posture_even_without_exploration_keyword or target_driven_task_type_prefers_silent_continue" -q`
  - `2 passed`
- `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -q`
  - `15 passed`
- `python -m pytest research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_aitp_cli.py research/knowledge-hub/tests/test_aitp_cli_e2e.py research/knowledge-hub/tests/test_runtime_profiles_and_projections.py research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_l2_graph_activation.py research/knowledge-hub/tests/test_topic_start_regressions.py -q`
  - `136 passed`

## Physicist-Facing Judgment

From the perspective of a theoretical physicist, this phase matters because
AITP's runtime behavior is now more situation-aware:

1. open exploration can stay openly exploratory without the user having to
   repeat “explore” in every turn,
2. target-driven work no longer gets the same default continuation posture as
   idea-space discussion,
3. hard blockers still win first, so the system is not becoming lax where
   scientific trust matters.

## Next Step

Phase `40` should now focus on reusable `task_type × lane` guidance surfaces so
AITP can do more than merely label the job type; it should start carrying
different first-loop expectations for different kinds of physics work.
