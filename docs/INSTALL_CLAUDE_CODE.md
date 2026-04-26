# Install Claude Code Adapter

Claude Code uses AITP through SessionStart bootstrap plus a native AITP
MCP server.

## Prerequisites

- Claude Code installed locally
- Python 3.10+

## Install

From the AITP repo:

```bash
python scripts/aitp-pm.py install --agent claude-code
```

Or if `aitp` is already on PATH:

```bash
aitp install --agent claude-code
```

Options:

```bash
aitp install --agent claude-code --scope user      # User-level (default)
aitp install --agent claude-code --scope project    # Project-level
aitp install --agent claude-code --topics-root /path/to/topics
```

## What gets installed

**User scope** (`~/.claude/`):
- `hooks/session-start.py`, `hooks/compact.py`, `hooks/stop.py` — lifecycle hooks
- `hooks/run-hook.cmd` — Windows hook launcher
- `hooks/aitp-keyword-router.py` — routes theory keywords at prompt submit
- `hooks/aitp-routing-guard.py` — prevents bypassing AITP for topic edits
- `skills/using-aitp/SKILL.md` — entry skill for theory requests
- `skills/aitp-runtime/SKILL.md` — protocol execution loop
- `settings.json` — merged hook configuration (SessionStart, UserPromptSubmit, PreToolUse)

**Project scope** (`<workspace>/.claude/`):
- Same hooks and skills under the workspace
- `.mcp.json` — MCP server registration for the project

## Verify

```bash
aitp doctor
```

This checks:
- Hook files present and match canonical versions
- Skills deployed correctly
- `settings.json` wires the expected SessionStart, UserPromptSubmit, PreToolUse hooks
- MCP server registration is correct
- Topics root is configured

Or inspect directly:

```bash
ls ~/.claude/hooks/
ls ~/.claude/skills/
claude mcp list
```

## How it works

1. **SessionStart**: Claude Code loads `using-aitp` skill at startup
2. **UserPromptSubmit**: AITP keyword router checks if the request is theory research
3. **PreToolUse**: Routing guard prevents Write/Edit to AITP topic files outside the protocol
4. **MCP tools**: `mcp__aitp__aitp_*` tools available for structured protocol actions

The expected UX:
- Natural-language theory requests enter AITP before substantive work
- `Continue this topic` routes to the current topic automatically
- Ordinary topic work stays in a light runtime profile
- The agent follows the protocol stages guided by `aitp_get_execution_brief`

## Manual MCP setup

If you prefer to wire the MCP server manually, add to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "aitp": {
      "command": "python",
      "args": ["/path/to/AITP-Research-Protocol/brain/mcp_server.py"]
    }
  }
}
```

Then `/reload-plugins` in Claude Code.

## Remove

```bash
aitp uninstall --agent claude-code
```

Or see [UNINSTALL.md](UNINSTALL.md) for manual cleanup.
