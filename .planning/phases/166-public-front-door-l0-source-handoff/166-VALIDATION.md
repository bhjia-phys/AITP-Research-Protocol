---
phase: 166
slug: public-front-door-l0-source-handoff
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-13
---

# Phase 166 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `research/knowledge-hub/pyproject.toml` |
| **Quick run command** | `python -m pytest research/knowledge-hub/tests/test_aitp_mcp_server.py research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_topic_replay.py -q` |
| **Full suite command** | `python -m pytest research/knowledge-hub/tests/test_aitp_mcp_server.py research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_topic_replay.py research/knowledge-hub/tests/test_runtime_scripts.py -q` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest research/knowledge-hub/tests/test_aitp_mcp_server.py research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_topic_replay.py -q`
- **After every plan wave:** Run `python -m pytest research/knowledge-hub/tests/test_aitp_mcp_server.py research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_topic_replay.py research/knowledge-hub/tests/test_runtime_scripts.py -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 166-01-01 | 01 | 1 | REQ-L0HAND-01 | unit | `python -m pytest research/knowledge-hub/tests/test_aitp_mcp_server.py -q` | ✅ | ⬜ pending |
| 166-01-02 | 01 | 1 | REQ-L0HAND-01 | unit | `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "topic_shell_surfaces" -q` | ✅ | ⬜ pending |
| 166-01-03 | 01 | 1 | REQ-L0HAND-02 | unit | `python -m pytest research/knowledge-hub/tests/test_topic_replay.py -q` | ✅ | ⬜ pending |
| 166-01-04 | 01 | 1 | REQ-L0HAND-01, REQ-L0HAND-02 | integration | `python -m pytest research/knowledge-hub/tests/test_aitp_mcp_server.py research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_topic_replay.py research/knowledge-hub/tests/test_runtime_scripts.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

- All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-13
