# Install OpenCode Adapter

## Prerequisites

- an `aitp` executable on `PATH`
- optional `aitp-mcp`
- a local OpenCode installation

## Install command harness

```bash
mkdir -p ~/.config/opencode/commands
cp adapters/opencode/AITP_COMMAND_HARNESS.md ~/.config/opencode/commands/AITP_COMMAND_HARNESS.md
cp adapters/opencode/commands/aitp.md ~/.config/opencode/commands/aitp.md
cp adapters/opencode/commands/aitp-loop.md ~/.config/opencode/commands/aitp-loop.md
cp adapters/opencode/commands/aitp-audit.md ~/.config/opencode/commands/aitp-audit.md
```

## Optional MCP registration

Add a local MCP server entry that points to:

- server name: `aitp`
- command: `aitp-mcp`

## Verify

OpenCode should be able to:

- enter the AITP runtime through the installed commands
- read `runtime_protocol.generated.md` before doing deeper work
- refresh conformance on exit

## Remove

See [`docs/UNINSTALL.md`](UNINSTALL.md).
