# Phase 134 Summary

Status: implemented on `main`

## Goal

Define the deep-execution parity contract and land one shared Codex-baseline
acceptance harness for the runtime-parity milestone.

## What Landed

- `runtime_support_matrix` now distinguishes front-door install readiness from
  `deep_execution_parity` status
- `aitp doctor` human-readable output now surfaces deep-execution parity as a
  separate contract instead of silently implying a green install row is enough
- a new shared harness,
  `research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py`,
  now proves the Codex baseline path and returns honest `probe_pending` results
  for Claude Code and OpenCode until their dedicated phases land
- runtime and install docs now name the new parity surface explicitly

## Outcome

Phase `134` is complete.
`v1.67` now has a shared parity vocabulary and one reusable baseline acceptance
entrypoint before runtime-specific probe work begins.
