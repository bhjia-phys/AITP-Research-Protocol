# Phase 127 Summary

Status: implemented on `main`

## Goal

Make the install-verification surface report the same readiness, remediation,
and convergence truth for Codex, Claude Code, and OpenCode.

## What Landed

- a per-runtime verification and remediation contract in
  `research/knowledge-hub/knowledge_hub/runtime_support_matrix.py`
- top-level front-door convergence and repair metadata in
  `research/knowledge-hub/knowledge_hub/frontdoor_support.py`
- human-readable `aitp doctor` output that leads with front-door readiness,
  repair commands, and docs instead of raw nested payloads

## Outcome

Phase `127` is complete.
`v1.65` has one shared doctor truth surface for the three front-door runtimes.
