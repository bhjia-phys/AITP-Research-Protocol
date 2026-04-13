---
phase: 168
slug: analytical-check-rows-and-review-contract-expansion
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-13
---

# Phase 168 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `research/knowledge-hub/pyproject.toml` |
| **Quick run command** | `python -m pytest research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_audit_analytical_review_writes_durable_artifact_and_updates_candidate research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_prepare_verification_analytical_uses_analytical_review_as_primary_bundle -q` |
| **CLI command** | `python -m pytest research/knowledge-hub/tests/test_aitp_cli.py -k "analytical_review" -q` |
| **E2E command** | `python -m pytest research/knowledge-hub/tests/test_aitp_cli_e2e.py::AITPCLIE2ETests::test_analytical_review_cli_writes_artifact_and_becomes_primary_bundle_surface -q` |
| **Compatibility command** | `python research/knowledge-hub/runtime/scripts/run_analytical_judgment_surface_acceptance.py --json` |
| **Phase command** | `python -m pytest research/knowledge-hub/tests/test_aitp_cli.py -k "analytical_review" research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_audit_analytical_review_writes_durable_artifact_and_updates_candidate research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_prepare_verification_analytical_uses_analytical_review_as_primary_bundle research/knowledge-hub/tests/test_aitp_cli_e2e.py::AITPCLIE2ETests::test_analytical_review_cli_writes_artifact_and_becomes_primary_bundle_surface -q` |
| **Estimated runtime** | ~90 seconds |

---

## Sampling Rate

- **After parser/dispatch changes:** Run `python -m pytest research/knowledge-hub/tests/test_aitp_cli.py -k "analytical_review" -q`
- **After artifact/rollup changes:** Run `python -m pytest research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_audit_analytical_review_writes_durable_artifact_and_updates_candidate research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_prepare_verification_analytical_uses_analytical_review_as_primary_bundle -q`
- **After public-flow changes:** Run `python -m pytest research/knowledge-hub/tests/test_aitp_cli_e2e.py::AITPCLIE2ETests::test_analytical_review_cli_writes_artifact_and_becomes_primary_bundle_surface -q`
- **After phase wave completion:** Run the phase command and `python research/knowledge-hub/runtime/scripts/run_analytical_judgment_surface_acceptance.py --json`
- **Before `$gsd-verify-work`:** Both the phase command and the compatibility command must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 168-01-01 | 01 | 1 | REQ-ANX-01 | unit | `python -m pytest research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_audit_analytical_review_writes_durable_artifact_and_updates_candidate research/knowledge-hub/tests/test_aitp_cli.py -k "analytical_review" -q` | ✅ | ⬜ pending |
| 168-01-02 | 01 | 1 | REQ-ANX-01, REQ-ANX-02 | unit | `python -m pytest research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_audit_analytical_review_writes_durable_artifact_and_updates_candidate research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_prepare_verification_analytical_uses_analytical_review_as_primary_bundle -q` | ✅ | ⬜ pending |
| 168-01-03 | 01 | 1 | REQ-ANX-02 | e2e | `python -m pytest research/knowledge-hub/tests/test_aitp_cli_e2e.py::AITPCLIE2ETests::test_analytical_review_cli_writes_artifact_and_becomes_primary_bundle_surface -q` | ✅ | ⬜ pending |
| 168-01-04 | 01 | 1 | REQ-ANX-01, REQ-ANX-02 | integration | `python -m pytest research/knowledge-hub/tests/test_aitp_cli.py -k "analytical_review" research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_audit_analytical_review_writes_durable_artifact_and_updates_candidate research/knowledge-hub/tests/test_aitp_service.py::AITPServiceTests::test_prepare_verification_analytical_uses_analytical_review_as_primary_bundle research/knowledge-hub/tests/test_aitp_cli_e2e.py::AITPCLIE2ETests::test_analytical_review_cli_writes_artifact_and_becomes_primary_bundle_surface -q` | ✅ | ⬜ pending |
| 168-01-05 | 01 | 1 | REQ-ANX-01, REQ-ANX-02 | acceptance-compat | `python research/knowledge-hub/runtime/scripts/run_analytical_judgment_surface_acceptance.py --json` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing analytical-review CLI, service, validation-bundle, and acceptance
  surfaces already exist and can be reused directly.
- No new harness bootstrap is required before execution; Phase `168` rides on
  the current isolated temp-kernel flows.

---

## Manual-Only Verifications

- None. Phase `168` stays inside targeted automated coverage. The new bounded
  proof lane remains Phase `168.1`, while the existing analytical judgment
  acceptance script acts as a compatibility guard here.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-13
