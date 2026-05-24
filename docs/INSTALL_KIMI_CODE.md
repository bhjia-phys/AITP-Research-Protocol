# Kimi Code AITP v5 Setup

Kimi Code integration has three parts:

1. Skills: install `using-aitp` and `aitp-runtime` from `deploy/templates/kimi-code/`.
2. MCP: configure Kimi Code to expose `brain/v5/native_mcp.py` as the `aitp` MCP server.
3. Hooks: merge AITP v5 lifecycle hooks into `.kimi/config.toml`.

Kimi's official docs describe user and project config files (`~/.kimi/config.toml`, `.kimi/config.toml`), MCP JSON files (`~/.kimi/mcp.json`, `.kimi/mcp.json`), lifecycle `[[hooks]]`, and project trust via `kimi trust`: <https://www.kimi.com/code/docs/>.

## MCP

Example project `.kimi/mcp.json`:

```json
{
  "mcpServers": {
    "aitp": {
      "command": "python",
      "args": [
        "C:/path/to/AITP-Research-Protocol/brain/v5/native_mcp.py"
      ]
    }
  }
}
```

## Hooks

From the AITP repo root:

```powershell
python -m brain.v5.cli --base <workspace> adapter install-hooks kimi-code <session-id> --settings .kimi/config.toml
python -m brain.v5.cli --base <workspace> adapter install-audit kimi-code --settings .kimi/config.toml
python -m brain.v5.cli adapter smoke-coverage
```

The installer preserves existing TOML by replacing only the marked AITP block:

```toml
# BEGIN AITP V5 KIMI HOOKS
[[hooks]]
event = "PreToolUse"
matcher = "*"
command = "..."

[[hooks]]
event = "PostToolUse"
matcher = "*"
command = "..."
# END AITP V5 KIMI HOOKS
```

## Contract

Kimi hooks are runtime guards. They may block unsafe pre-tool actions and write trace events after tool use, but they do not update claim trust. Scientific state still lives in typed v5 records.
