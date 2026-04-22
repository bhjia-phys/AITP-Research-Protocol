# Claude Code MCP setup

Claude Code should expose an `aitp` MCP server so AITP runtime actions are available as native structured tools.

Expected config path:

- `{{USER_HOME}}/.claude.json`

Equivalent Claude CLI command:

```bash
claude mcp add-json -s user aitp '{"command":"python","args":["{{REPO_ROOT}}/brain/mcp_server.py"]}'
```

Verify with:

```bash
claude mcp list
```
