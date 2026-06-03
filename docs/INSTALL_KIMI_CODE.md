# Kimi Code AITP v5 Setup

Kimi Code integration has three parts:

1. Skills: install `using-aitp` and `aitp-runtime` from `deploy/templates/kimi-code/`.
2. MCP: configure Kimi Code to expose `brain/v5/native_mcp.py` as the `aitp` MCP server.
3. Hooks: merge AITP v5 lifecycle hooks into the project Kimi TOML config.

Kimi's official docs describe configuration, MCP, hooks, and skills:
<https://www.kimi.com/code/docs/>. Existing AITP workspaces use project-local
`.kimi/` paths. Newer Kimi Code docs and migrated installs may use
`.kimi-code/` for project MCP, hooks, and skills. Keep both paths in sync when
supporting both CLIs.

## MCP

Example project `.kimi-code/mcp.json`:

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

If your installed Kimi CLI still reads the legacy project path, use the same
JSON in `.kimi/mcp.json`, or rely on the existing global file at
`~/.kimi/mcp.json`.

Some Kimi CLI builds also support global MCP registration:

```powershell
kimi mcp add --transport stdio aitp -- python C:/path/to/AITP-Research-Protocol/brain/v5/native_mcp.py
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
kimi mcp test aitp
```

The UTF-8 variables avoid Windows GBK console failures when Kimi prints Unicode status symbols.

## Hooks

From the AITP repo root:

```powershell
python -m brain.v5.cli --base <workspace> adapter install-hooks kimi-code <session-id> --settings <workspace>/.kimi/config.toml
python -m brain.v5.cli --base <workspace> adapter install-hooks kimi-code <session-id> --settings <workspace>/.kimi-code/config.toml
python -m brain.v5.cli --base <workspace> adapter install-audit kimi-code --settings <workspace>/.kimi/config.toml
python -m brain.v5.cli --base <workspace> adapter install-audit kimi-code --settings <workspace>/.kimi-code/config.toml
python -m brain.v5.cli adapter smoke-coverage
```

`--settings` is resolved by the current shell. Use an absolute path, or run the
command from the theory workspace root when passing `.kimi/...` or
`.kimi-code/...`.

Run Kimi from the workspace root. If your build supports explicit paths, load
the project assets directly:

```powershell
kimi --work-dir <workspace> --config-file .kimi-code/config.toml --mcp-config-file .kimi-code/mcp.json --skills-dir .kimi-code/skills
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

## Theory Workspace Checklist

For a Windows theory workspace such as `F:/AI_Workspace/Theoretical-Physics`:

1. Copy `deploy/templates/kimi-code/using-aitp.md` to
   `.kimi-code/skills/using-aitp/SKILL.md` and, if needed, mirror it to
   `.kimi/skills/using-aitp/SKILL.md`.
2. Copy `deploy/templates/kimi-code/aitp-runtime.md` to
   `.kimi-code/skills/aitp-runtime/SKILL.md` and, if needed, mirror it to
   `.kimi/skills/aitp-runtime/SKILL.md`.
3. Write `.kimi-code/mcp.json` with the `aitp` server pointing at the checked
   out AITP repo and with `AITP_TOPICS_ROOT` pointing at the workspace topics
   directory.
4. Generate hooks for both `.kimi/config.toml` and `.kimi-code/config.toml` if
   the machine has both legacy and migrated Kimi installations.
5. Audit both hook configs and run a host-readiness check when the Kimi CLI is
   available.
