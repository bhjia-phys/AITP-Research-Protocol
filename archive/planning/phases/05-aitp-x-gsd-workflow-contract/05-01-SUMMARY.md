---
phase: 05-aitp-x-gsd-workflow-contract
plan: 01
subsystem: docs
tags: [aitp, gsd, workflow, routing]
requires:
  - phase: 04-code-backed-acceptance-lane
    provides: a real code-backed exemplar that needs an explicit routing rule
provides:
  - explicit AITP x GSD coexistence note
  - README entrypoints for the coexistence rule
affects: [phase-05, repo-entrypoints, workflow]
tech-stack:
  added: [workflow contract doc]
  patterns: [repo-work vs topic-work routing rule]
key-files:
  created: [docs/AITP_GSD_WORKFLOW_CONTRACT.md]
  modified: [README.md, research/knowledge-hub/README.md, research/knowledge-hub/tests/test_agent_bootstrap_assets.py]
key-decisions:
  - "Use AITP for topic-governed research even when the topic includes code, and use GSD for implementing AITP itself."
patterns-established:
  - "Code as research evidence belongs to AITP; code as repo maintenance belongs to GSD."
requirements-completed: [ACC-02]
duration: 15min
completed: 2026-03-31
---

# Phase 5: AITP x GSD Workflow Contract Summary

**The repository now has an explicit rule for when work belongs to GSD repo execution versus AITP topic execution**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-31T06:20:00+08:00
- **Completed:** 2026-03-31T06:35:00+08:00
- **Tasks:** 1
- **Files modified:** 4

## Accomplishments
- Wrote the AITP x GSD coexistence contract.
- Linked it from the root and kernel READMEs.
- Added a test that keeps the routing note discoverable.

## Task Commits

Each task was completed in the working tree without atomic git commits in this session.

1. **Task 1: Write and wire the AITP x GSD workflow contract** - `(uncommitted)`

**Plan metadata:** `(retroactive summary)`

## Files Created/Modified
- `docs/AITP_GSD_WORKFLOW_CONTRACT.md` - coexistence and routing rule
- `README.md` - root entry link
- `research/knowledge-hub/README.md` - kernel entry link
- `research/knowledge-hub/tests/test_agent_bootstrap_assets.py` - README/link coverage

## Decisions Made
- Code inside a research topic remains AITP work; only repo implementation of AITP itself belongs to GSD.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The milestone is complete and ready for `gsd-complete-milestone` or next-milestone planning.

---
*Phase: 05-aitp-x-gsd-workflow-contract*
*Completed: 2026-03-31*
