# Claude Code MCP setup

Claude Code should expose an `aitp` MCP server so AITP v5 runtime actions are
available as native structured tools.

For this project install, the authoritative MCP config is the workspace
`.mcp.json` written by `aitp-pm.py install/update`.

Expected project config path:

- `{{TARGET_ROOT}}/.mcp.json`

Equivalent v5 entry:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp python {{REPO_ROOT}}/brain/v5/native_mcp.py
```

Verify with:

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python {{REPO_ROOT}}/scripts/aitp-pm.py doctor
```

The legacy `brain/mcp_server.py` is compatibility-only. Do not install it as
the active MCP server for new v5 work.
