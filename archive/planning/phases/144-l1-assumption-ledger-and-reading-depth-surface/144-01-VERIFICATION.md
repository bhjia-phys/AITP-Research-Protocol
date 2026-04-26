---
phase: 144-l1-assumption-ledger-and-reading-depth-surface
plan: 01
status: passed
requirements-completed:
  - REQ-L1INTAKE-01
  - REQ-L1INTAKE-02
  - REQ-L1INTAKE-03
  - REQ-VERIFY-01
---

# Phase 144 Verification

## Status

passed

## Verification Evidence

- assumption/depth contract tests:
  - `python -m pytest research/knowledge-hub/tests/test_l1_assumption_depth_contracts.py -q`
  - result: `2 passed`
- isolated acceptance:
  - `python research/knowledge-hub/runtime/scripts/run_l1_assumption_depth_acceptance.py --json`
  - result: `success`
  - checks:
    - assumption rows: `2`
    - reading depths: `thesis:weak-coupling-note=full_read`, `paper:strong-coupling-abstract=abstract_only`
    - contradiction candidates: `2`
- runtime acceptance harness slice:
  - `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "l1_assumption_depth_acceptance" -q`
  - result: `1 passed, 29 deselected`
- targeted existing `L1` shell regression:
  - `python -m pytest research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_source_backed_l1_intake -q`
  - result: `1 passed`
- isolation sanity check for the pre-existing method-specificity acceptance:
  - `python research/knowledge-hub/runtime/scripts/run_l1_method_specificity_acceptance.py --json`
  - result: `success`

## Notes

- Verification stayed intentionally targeted to the new `L1` assumption/depth
  surface plus one existing source-backed intake regression.
- I did not run the full knowledge-hub suite in this step because the repo
  still contains unrelated in-flight working-tree changes outside Phase `144`.
