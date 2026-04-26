# Phase 136 Summary

Status: implemented on `main`

## Goal

Land one honest OpenCode deep-execution probe that enters through the
supported plugin bootstrap surface and records the remaining bounded gap from
the Codex baseline.

## What Landed

- `research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py`
  now contains a real `opencode` probe that:
  - installs OpenCode assets into a temp `.opencode` project root
  - executes the real OpenCode plugin module with Node
  - runs the plugin `config` hook and
    `experimental.chat.system.transform` hook to capture a real bootstrap
    receipt
  - routes a real natural-language `session-start` plus `status` flow through
    an isolated kernel root
  - emits `matches_codex_baseline` and `falls_short_of_codex_baseline`
- `runtime_support_matrix` now reports OpenCode deep execution as
  `probe_available` instead of `probe_pending` when the OpenCode front door is
  already ready
- install/runtime docs now explain how to run the bounded OpenCode probe and
  what gap it still leaves open

## Outcome

Phase `136` is complete.
`v1.67` now has bounded deep-execution probes for both Claude Code and
OpenCode, so the next step is the closure and cross-runtime audit in
Phase `137`.
