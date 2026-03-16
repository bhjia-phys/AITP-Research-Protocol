# Install OpenClaw Adapter

## Prerequisites

- an `aitp` executable on `PATH`
- optional `aitp-mcp` executable for structured tool access
- a local OpenClaw installation

## Install skill

```bash
mkdir -p ~/.openclaw/skills/aitp-runtime
cp adapters/openclaw/SKILL.md ~/.openclaw/skills/aitp-runtime/SKILL.md
```

## Optional MCP registration

Register the `aitp` MCP server through your OpenClaw MCP bridge if you want
structured tool calls instead of CLI-only routing.

The exact bridge command depends on your OpenClaw setup. The public contract is:

- server name: `aitp`
- command: `aitp-mcp`

## Verify

OpenClaw should be able to:

- start topic work through `aitp bootstrap`, `aitp resume`, or `aitp loop`
- read the runtime protocol bundle before taking actions
- refresh `aitp audit` at exit

## Remove

See [`docs/UNINSTALL.md`](UNINSTALL.md).
