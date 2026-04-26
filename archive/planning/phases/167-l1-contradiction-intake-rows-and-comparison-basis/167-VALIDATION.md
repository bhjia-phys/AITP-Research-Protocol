---
phase: 167
slug: l1-contradiction-intake-rows-and-comparison-basis
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-13
---

# Phase 167 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `research/knowledge-hub/pyproject.toml` |
| **Quick run command** | `python -m pytest research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_source_backed_l1_intake research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_l1_conflict_candidates -q` |
| **Schema command** | `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py -q` |
| **Phase command** | `python -m pytest research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_source_backed_l1_intake research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_l1_conflict_candidates research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_runtime_scripts.py::RuntimeScriptTests::test_l1_assumption_depth_acceptance_script_runs_on_isolated_work_root -q` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_source_backed_l1_intake research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_l1_conflict_candidates -q`
- **After schema changes:** Run `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py -q`
- **After phase wave completion:** Run `python -m pytest research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_source_backed_l1_intake research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_l1_conflict_candidates research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_runtime_scripts.py::RuntimeScriptTests::test_l1_assumption_depth_acceptance_script_runs_on_isolated_work_root -q`
- **Before `$gsd-verify-work`:** The full phase command must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 167-01-01 | 01 | 1 | REQ-L1CON-01 | unit | `python -m pytest research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_source_backed_l1_intake research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_l1_conflict_candidates -q` | ✅ | ⬜ pending |
| 167-01-02 | 01 | 1 | REQ-L1CON-02 | unit | `python -m pytest research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_source_backed_l1_intake research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_l1_conflict_candidates -q` | ✅ | ⬜ pending |
| 167-01-03 | 01 | 1 | REQ-L1CON-01, REQ-L1CON-02 | schema | `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py -q` | ✅ | ⬜ pending |
| 167-01-04 | 01 | 1 | REQ-L1CON-01, REQ-L1CON-02 | integration | `python -m pytest research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_source_backed_l1_intake research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_ensure_topic_shell_surfaces_persists_l1_conflict_candidates research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_runtime_scripts.py::RuntimeScriptTests::test_l1_assumption_depth_acceptance_script_runs_on_isolated_work_root -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing service, schema, and acceptance-script coverage already exercises
  the current contradiction candidate chain.
- No new harness bootstrap is required before execution.

---

## Manual-Only Verifications

- None. Phase `167` stays fully inside targeted automated coverage; the bounded
  proof lane is deferred to Phase `167.1`.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 90s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-13
