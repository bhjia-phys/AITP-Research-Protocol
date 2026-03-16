# Install Codex Adapter

## Prerequisites

- an `aitp` executable on `PATH`
- optional `aitp-mcp` executable
- a local Codex CLI installation

## Install skill

```bash
mkdir -p ~/.codex/skills/aitp-runtime
cp adapters/codex/SKILL.md ~/.codex/skills/aitp-runtime/SKILL.md
```

If your setup uses `~/.codex-home/skills/`, copy the same directory there as
well.

## Verify

Codex should be able to:

- enter topic work through the AITP runtime surface
- read `runtime_protocol.generated.md`
- treat missing conformance as a hard failure for AITP work

## Remove

See [`docs/UNINSTALL.md`](UNINSTALL.md).
