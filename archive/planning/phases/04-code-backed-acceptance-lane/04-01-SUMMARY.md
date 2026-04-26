---
phase: 04-code-backed-acceptance-lane
plan: 01
subsystem: runtime
tags: [aitp, code-method, acceptance, benchmark-first, tfim]
requires:
  - phase: 03-strategy-memory-integration
    provides: runtime-visible strategy memory
provides:
  - real TFIM code-method acceptance script
  - benchmark-first code-backed exemplar
  - docs/runbook entry points for the new lane
affects: [phase-04, code-method-lane, acceptance]
tech-stack:
  added: [TFIM code-method acceptance script]
  patterns: [benchmark-first code-backed acceptance]
key-files:
  created: [research/knowledge-hub/runtime/scripts/run_tfim_benchmark_code_method_acceptance.py]
  modified: [research/knowledge-hub/README.md, research/knowledge-hub/runtime/README.md, research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md, research/knowledge-hub/tests/test_l2_backend_contracts.py]
key-decisions:
  - "Use a cross-platform Python acceptance script instead of a shell-only smoke path for the code-method exemplar."
patterns-established:
  - "Code-backed acceptance should start from a bounded exact benchmark and then record trust/state inside AITP."
requirements-completed: [ACC-01]
duration: 25min
completed: 2026-03-31
---

# Phase 4: Code-Backed Acceptance Lane Summary

**The TFIM exact-diagonalization helper now has a real benchmark-first `code_method` acceptance lane inside AITP**

## Performance

- **Duration:** 25 min
- **Started:** 2026-03-31T05:55:00+08:00
- **Completed:** 2026-03-31T06:20:00+08:00
- **Tasks:** 1
- **Files modified:** 5

## Accomplishments
- Added a real TFIM benchmark-first code-method acceptance script.
- Wired the new lane into kernel/runtime docs and the test runbook.
- Verified the script by actually running it successfully.

## Task Commits

Each task was completed in the working tree without atomic git commits in this session.

1. **Task 1: Land a real TFIM benchmark-first code-method acceptance script** - `(uncommitted)`

**Plan metadata:** `(retroactive summary)`

## Files Created/Modified
- `research/knowledge-hub/runtime/scripts/run_tfim_benchmark_code_method_acceptance.py` - real code-method acceptance script
- `research/knowledge-hub/README.md` - code-method acceptance docs
- `research/knowledge-hub/runtime/README.md` - runtime acceptance docs
- `research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md` - runbook entry
- `research/knowledge-hub/tests/test_l2_backend_contracts.py` - existence/doc coverage

## Decisions Made
- The first code-backed exemplar should be benchmark-first and cross-platform, not a shell-only smoke path.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The first run failed because the acceptance script did not create its config/results/notes directories before copying the TFIM config template.
- This was fixed in the script before the successful acceptance run.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The repo now has a real code-method exemplar and can safely document the AITP x GSD coexistence rule around it.

---
*Phase: 04-code-backed-acceptance-lane*
*Completed: 2026-03-31*
