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

## AITP v5 hook settings

Repo-backed v5 workspaces can generate a Claude Code settings template from the
typed adapter packet:

```powershell
aitp-v5 --base <workspace> adapter hook-settings claude-code <session-id> --output .claude/settings.local.json
```

To preserve existing Claude Code settings and append only missing AITP v5 hook
entries, use the merge installer:

```powershell
aitp-v5 --base <workspace> adapter install-hooks claude-code <session-id> --settings .claude/settings.local.json
```

The generated settings use Claude Code `PreToolUse` and `PostToolUse` hook
entries that call:

```text
hooks/aitp_v5_claude_hook.py
```

`PostToolUse` persists process trace events through
`.aitp/runtime/hook_trace_events.jsonl`. These events are durable process
history, not evidence records and not claim-confidence updates.

`PreToolUse` maps Claude tool JSON into a v5 typed pre-tool decision. Destructive,
remote, or expensive Bash commands produce `permissionDecision=deny` with a
required human checkpoint; ordinary web/literature tool use produces
`permissionDecision=allow` plus a logged AITP hook decision. AITP MCP calls are
also mapped into v5 actions: unqualified direct
`aitp_v5_apply_trust_update` calls are denied with
`required_actions=["aitp_v5_preflight_trust_update"]`; a direct trust apply is
only allowed through the hook when the tool input carries both a trusted
`source_kind` and a `trust-preflight-*` token. The kernel still validates the
token during `aitp_v5_apply_trust_update`. Typed writes such as
`aitp_v5_record_evidence` are allowed and logged as `record_evidence`.
Validation and L2 promotion MCP calls are checked against the active v5
workspace context before the tool runs: the hook resolves the typed claim,
evidence refs, and linked or requested code-state records and reuses kernel
policy to warn or deny.

MCP clients can call:

```text
aitp_v5_write_claude_code_hook_settings(base, session_id, output_path)
aitp_v5_install_claude_code_hook_settings(base, session_id, settings_path)
```

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
