# Install OpenClaw Adapter

> **Status:** OpenClaw adapter assets exist in `adapters/` and `deploy/templates/`,
> but OpenClaw is not yet integrated into the `aitp-pm.py` one-click installer.
> Use manual setup below.

## Manual setup

Copy skills into your OpenClaw workspace:

```bash
mkdir -p <workspace>/skills/aitp-runtime
cp deploy/templates/claude-code/aitp-runtime.md <workspace>/skills/aitp-runtime/SKILL.md
cp deploy/templates/claude-code/aitp-mcp-setup.md <workspace>/skills/aitp-runtime/AITP_MCP_SETUP.md
```

Also register the AITP MCP bridge in your OpenClaw configuration.

Reference plugin assets live under `research/adapters/openclaw/`.

## Verify

Check that the skills are present and MCP registration is correct.

## Remove

Delete the copied skill directories and MCP bridge entries.
See [UNINSTALL.md](UNINSTALL.md).
