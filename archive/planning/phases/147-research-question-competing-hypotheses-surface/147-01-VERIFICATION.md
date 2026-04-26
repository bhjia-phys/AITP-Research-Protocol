---
phase: 147-research-question-competing-hypotheses-surface
plan: 01
status: passed
requirements-completed:
  - REQ-HYP-01
  - REQ-HYP-02
  - REQ-HYP-03
  - REQ-VERIFY-01
---

# Phase 147 Verification

## Status

passed

## Verification Evidence

- contract + documentation slice:
  - `python -m pytest research/knowledge-hub/tests/test_competing_hypotheses_contracts.py -q`
  - result: `2 passed`
- schema slice:
  - `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py -q`
  - result: `10 passed`
- replay slice:
  - `python -m pytest research/knowledge-hub/tests/test_topic_replay.py -q`
  - result: `2 passed`
- isolated acceptance:
  - `python research/knowledge-hub/runtime/scripts/run_competing_hypotheses_acceptance.py --json`
  - result: `success`
  - checks:
    - competing hypothesis count: `3`
    - leading hypothesis id: `hypothesis:weak-coupling`
    - deferred buffer present: `true`
    - follow-up subtopic count: `1`
    - excluded competing hypothesis count: `1`
- runtime acceptance harness slice:
  - `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "competing_hypotheses_acceptance" -q`
  - result: `1 passed, 32 deselected`
- runtime projection compatibility smoke:
  - `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "projection_helpers_write_valid_outputs" -q`
  - result: `1 passed, 12 deselected`
- runtime bundle schema/service smoke:
  - `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "runtime_protocol_bundle_matches_public_schema or topic_status_and_prepare_verification_surface_new_shell_fields" -q`
  - result: `1 passed, 129 deselected`

## Notes

- Verification stayed intentionally targeted to the new question-level
  competing-hypotheses surface.
- A broader `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -q`
  run still shows unrelated in-flight failures around paired-backend,
  control-plane, and layer-graph expectations in the current working tree, so
  those were not treated as Phase `147` regressions.
