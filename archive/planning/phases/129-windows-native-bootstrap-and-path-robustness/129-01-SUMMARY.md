# Phase 129 Summary

Status: implemented on `main`

## Goal

Remove the Windows-native bootstrap and path assumptions that made adoption
quality drift between Codex, Claude Code, and OpenCode.

## What Landed

- Windows-native install and verify guidance across the runtime-specific docs
- `hooks/session-start.py` plus a Python-first `hooks/run-hook.cmd` path for
  Claude Code SessionStart
- repo-local launcher fallbacks in the install and quickstart surface for users
  not entering through WSL

## Outcome

Phase `129` is complete.
`v1.65` no longer assumes bash as the default Windows-native adoption path.
