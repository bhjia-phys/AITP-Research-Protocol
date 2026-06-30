# Claude Code MCP setup

Claude Code should expose an `aitp` MCP server so AITP v5 runtime actions are
available as native structured tools.

For project installs, the authoritative MCP config is the workspace `.mcp.json`
written by `aitp-pm.py install` or `aitp-pm.py update`.

Expected project config path:

- `{{TARGET_ROOT}}/.mcp.json`

Install or refresh the project adapter with:

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python {{REPO_ROOT}}/scripts/aitp-pm.py install --agent claude-code --scope project --target-root {{TARGET_ROOT}} --topics-root {{TOPICS_ROOT}}
```

The active MCP entrypoint must be:

```text
{{REPO_ROOT}}/brain/v5/native_mcp.py
```

Verify with:

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python {{REPO_ROOT}}/scripts/aitp-pm.py doctor
```

The legacy `brain/mcp_server.py` is compatibility-only. Do not install it as
the active MCP server for AITP 1.0.0/v5 work.
