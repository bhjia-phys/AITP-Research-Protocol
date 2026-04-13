---
status: passed
phase: 167-l1-contradiction-intake-rows-and-comparison-basis
updated: 2026-04-13T12:50:39.8191397+08:00
---

# Phase 167 Verification

## Goal Verdict

Passed. The phase goal was to upgrade the existing `L1` contradiction intake
path into richer, source-backed contradiction rows with explicit comparison
basis while preserving the current `contradiction_candidates` chain. The row
contract, derivation path, and schema surfaces now do that on a green targeted
baseline.

## Must-Haves

- [x] contradiction rows stay source-backed and pairwise
- [x] contradiction rows now carry explicit comparison-basis context instead of
  only a thin `detail` string
- [x] existing contradiction-aware acceptance wiring remains compatible

## Evidence

- `python -m pytest research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_source_backed_l1_intake research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_l1_conflict_candidates -q`
  - `2 passed`
- `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py -q`
  - `11 passed`
- `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py::RuntimeScriptTests::test_l1_assumption_depth_acceptance_script_runs_on_isolated_work_root -q`
  - `1 passed`
- `python -m pytest research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_source_backed_l1_intake research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_l1_conflict_candidates research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_runtime_scripts.py::RuntimeScriptTests::test_l1_assumption_depth_acceptance_script_runs_on_isolated_work_root -q`
  - `14 passed`

## Notes

- The richer contradiction-row contract was added to all three relevant schema
  surfaces:
  - `schemas/research-question.schema.json`
  - `schemas/topic-synopsis.schema.json`
  - `research/knowledge-hub/runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`
- The phase intentionally leaves broad runtime/read-path wording and the
  milestone proof lane to Phase `167.1`.
