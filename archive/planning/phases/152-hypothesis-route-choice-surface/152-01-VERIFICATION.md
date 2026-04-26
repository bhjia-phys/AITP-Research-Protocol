---
phase: 152-hypothesis-route-choice-surface
plan: 01
status: passed
requirements-completed:
  - REQ-HCHOICE-01
  - REQ-HCHOICE-02
  - REQ-HCHOICE-03
  - REQ-VERIFY-01
---

# Phase 152 Verification

## Status

passed

## Verification Evidence

- compile slice:
  - `python -m compileall research/knowledge-hub/knowledge_hub/runtime_read_path_support.py research/knowledge-hub/knowledge_hub/runtime_bundle_support.py research/knowledge-hub/knowledge_hub/topic_replay.py research/knowledge-hub/knowledge_hub/kernel_markdown_renderers.py research/knowledge-hub/runtime/scripts/run_hypothesis_route_choice_acceptance.py research/knowledge-hub/tests/test_hypothesis_route_choice_contracts.py research/knowledge-hub/tests/test_runtime_scripts.py research/knowledge-hub/tests/test_topic_replay.py research/knowledge-hub/tests/test_schema_contracts.py`
  - result: `compiled successfully`
- contract + replay + schema slice:
  - `python -m pytest research/knowledge-hub/tests/test_hypothesis_route_choice_contracts.py research/knowledge-hub/tests/test_hypothesis_route_handoff_contracts.py research/knowledge-hub/tests/test_hypothesis_route_reentry_contracts.py research/knowledge-hub/tests/test_hypothesis_route_activation_contracts.py research/knowledge-hub/tests/test_hypothesis_branch_routing_contracts.py research/knowledge-hub/tests/test_topic_replay.py research/knowledge-hub/tests/test_schema_contracts.py -q`
  - result: `18 passed`
- isolated acceptance:
  - `python research/knowledge-hub/runtime/scripts/run_hypothesis_route_choice_acceptance.py --json`
  - result: `success`
  - checks:
    - choice status: `stay_local`
    - active local hypothesis id: `hypothesis:weak-coupling`
    - primary handoff candidate id: `hypothesis:symmetry-breaking`
    - auto reintegrated parent: `false`
    - auto reactivated candidate: `false`
- runtime acceptance harness slice:
  - `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "hypothesis_route_choice_acceptance or hypothesis_route_handoff_acceptance" -q`
  - result: `2 passed, 36 deselected`
- backward-compatibility slices:
  - `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "runtime_protocol_bundle_matches_public_schema or topic_status_and_prepare_verification_surface_new_shell_fields" -q`
  - result: `1 passed, 129 deselected`
  - `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "projection_helpers_write_valid_outputs" -q`
  - result: `1 passed, 12 deselected`

## Notes

- Verification stayed intentionally targeted to the new route choice surface and
  its immediate runtime/replay/schema dependencies.
- No full knowledge-hub suite rerun was performed in this step because the repo
  still contains unrelated in-flight working-tree changes outside Phase `152`.
