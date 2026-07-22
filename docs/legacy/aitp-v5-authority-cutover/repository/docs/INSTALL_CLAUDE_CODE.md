# Install Claude Code Adapter

Claude Code should use AITP through the v5 native MCP server and v5-safe
project hooks. Legacy SessionStart/stage hooks are compatibility-only and are
not installed by default.

## Install

From the AITP repo:

```bash
python scripts/aitp-pm.py install --agent claude-code
```

For a research workspace, prefer project scope:

```bash
python scripts/aitp-pm.py install --agent claude-code --scope project \
  --target-root /path/to/workspace \
  --topics-root /path/to/workspace/research/aitp-topics
```

Project-scope installs write under `<workspace>/.claude/` and register MCP in
`<workspace>/.mcp.json`. User-scope installs write under `~/.claude/`.

## What Gets Installed

Default v5 install:
- `hooks/aitp-keyword-router.py`: keyword/topic orientation only
- `hooks/aitp-routing-guard.py`: blocks direct `Write`, `Edit`, and
  `MultiEdit` topic-file writes until v5 routing is confirmed
- `hooks/aitp-v5-claude-hook.py` and related `aitp-v5-*` adapter hooks for
  explicit session-bound lifecycle/pre-tool/post-tool integration; these files
  are not wired by the default project install
- `skills/using-aitp/SKILL.md`
- `skills/aitp-runtime/SKILL.md`
- `settings.json` hook wiring for the v5-safe router/guard only
- project `.mcp.json` or user MCP config pointing at `brain/v5/native_mcp.py`

The old `session-start.py`, `compact.py`, `stop.py`, `aitp-l4-watchdog.py`, and
`run-hook.cmd` lifecycle stack is not deployed by default. Use
`AITP_INSTALL_LEGACY_STAGE_HOOKS=1` only when deliberately maintaining an old
L0/L1/L3/L4 Markdown workspace.

## Verify

```bash
python scripts/aitp-pm.py doctor
python scripts/aitp-pm.py status
```

The doctor check requires:
- the active MCP entrypoint to be `brain/v5/native_mcp.py`
- `settings.json` to contain v5-safe hook commands
- no legacy stage hook command in active settings
- no local project residue pointing at old paths or legacy MCP

## How It Works

1. `UserPromptSubmit` provides orientation when AITP/theory keywords appear.
2. The agent binds or migrates into a v5 topic/session before research work.
3. `PreToolUse` prevents direct writes into AITP topic files unless v5 routing
   has been confirmed.
4. Research execution uses `aitp_v5_get_execution_brief` and typed v5 records.
5. Summaries, hooks, and old Markdown stage fields are orientation-only.
6. Hooks must not update claim trust or act as an evidence recording channel.

## Session-Bound v5 Hook Settings

For a specific v5 session, the typed adapter can generate Claude Code hook
settings:

```powershell
python -m brain.v5.cli --base <topics-root> adapter hook-settings claude-code <session-id> --output .claude/settings.local.json
```

To merge session-bound settings into an existing settings file:

```powershell
python -m brain.v5.cli --base <topics-root> adapter install-hooks claude-code <session-id> --settings .claude/settings.local.json
```

The generated hook entries call `hooks/aitp_v5_claude_hook.py` for
`SessionStart`, `PreToolUse`, and `PostToolUse`. These hooks emit process
guards and trace events. They do not update claim trust; trust changes still
require kernel preflight, validation, and human checkpoints.

## Manual MCP Setup

If you wire MCP manually, use the v5 entrypoint:

```json
{
  "mcpServers": {
    "aitp": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "pyyaml",
        "--with",
        "jsonschema",
        "--with",
        "fastmcp",
        "python",
        "/path/to/AITP-Research-Protocol/brain/v5/native_mcp.py"
      ],
      "cwd": "/path/to/AITP-Research-Protocol",
      "env": {
        "AITP_TOPICS_ROOT": "/path/to/workspace/research/aitp-topics"
      }
    }
  }
}
```

Do not install `brain/mcp_server.py` as the active MCP server for v5 work.
