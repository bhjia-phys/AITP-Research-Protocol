# Phase 129: Windows-Native Bootstrap And Path Robustness - Context

**Recorded:** 2026-04-11
**Status:** Retrospectively documented after implementation

<domain>
## Phase Boundary

This phase removes the default Windows-native adoption traps that kept install
and first-run guidance from being symmetric across Codex, Claude Code, and
OpenCode.

The phase owns:

- Windows-native install and verify commands in docs
- Claude Code SessionStart behavior on Windows
- repo-local launcher fallbacks for users not entering through WSL

</domain>

<decisions>
## Implementation Decisions

### Windows Surface
- **D-01:** Do not assume bash as the default Claude Code SessionStart runner.
- **D-02:** Prefer a Python sidecar plus wrapper fallback for SessionStart on
  Windows.
- **D-03:** Publish `scripts\\aitp-local.cmd` fallback commands wherever the
  quickstart or install verification would otherwise be POSIX-only.

### Runtime Scope
- **D-04:** Keep Codex, Claude Code, and OpenCode aligned as front-door
  runtimes.
- **D-05:** Leave OpenClaw as a specialized lane and do not expand this phase
  into OpenClaw parity.

</decisions>

<canonical_refs>
## Canonical References

- `docs/INSTALL_CODEX.md`
- `docs/INSTALL_CLAUDE_CODE.md`
- `docs/INSTALL_OPENCODE.md`
- `.codex/INSTALL.md`
- `.opencode/INSTALL.md`
- `hooks/run-hook.cmd`
- `hooks/session-start.py`
- `research/knowledge-hub/knowledge_hub/agent_install_support.py`
- `research/knowledge-hub/tests/test_agent_bootstrap_assets.py`

</canonical_refs>

<deferred>
## Deferred Ideas

- Packaging and PATH-level global install cleanup beyond repo-local launchers
  remains future work.

</deferred>

---

*Phase: 129-windows-native-bootstrap-and-path-robustness*
