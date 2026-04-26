# Phase 135 Summary

Status: implemented on `main`

## Goal

Land one honest Claude Code deep-execution probe that enters through the
supported SessionStart bootstrap surface and records the remaining bounded gap
from the Codex baseline.

## What Landed

- `research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py`
  now contains a real `claude_code` probe that:
  - installs Claude assets into a temp `.claude` project root
  - exercises the Windows-native `run-hook.cmd` SessionStart wrapper when
    available
  - routes a real natural-language `session-start` plus `status` flow through
    an isolated kernel root
  - emits `matches_codex_baseline` and `falls_short_of_codex_baseline`
- `runtime_support_matrix` now reports Claude Code deep execution as
  `probe_available` instead of `probe_pending` when the Claude front door is
  already ready
- `aitp doctor` still keeps Claude Code in the pending parity set rather than
  falsely closing the milestone
- runtime docs and Claude install docs now explain how to run the bounded
  Claude probe and what gap it still leaves open

## Outcome

Phase `135` is complete.
`v1.67` now has a bounded Claude Code deep-execution probe and can move on to
the corresponding OpenCode probe in Phase `136`.
