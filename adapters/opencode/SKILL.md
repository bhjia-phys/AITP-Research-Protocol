---
name: aitp-opencode-adapter
description: Reference note for the OpenCode adapter surface; the active bootstrap lives in ~/.config/opencode/plugins/aitp.js and reuses the canonical v5 skill content.
---

# OpenCode Adapter Reference

The OpenCode path is plugin-first, equivalent to Claude Code's SessionStart
hook:

1. Install `deploy/templates/opencode/aitp-plugin.js` as
   `~/.config/opencode/plugins/aitp.js`.
2. Add the `aitp` MCP server to global `~/.config/opencode/opencode.json`.
3. Add `aitp_v5_*` to the workspace `opencode.json` tool allowlist.
4. On chat initialization, `experimental.chat.system.transform` injects the
   adapted canonical `using-aitp` skill.

## Architecture

OpenCode uses plugin-based injection instead of Claude Code hooks:

| Layer | Claude Code | OpenCode |
|---|---|---|
| Gateway injection | `hooks/session_start.py` emits stdout JSON | `plugins/aitp.js` uses `system.transform` |
| Compact reinjection | `hooks/compact.py` | Agent recalls through bounded `aitp_v5_*` context tools |
| Skill source | `deploy/templates/claude-code/using-aitp.md` | Same file, adapted at injection time |
| MCP tools | `mcp__aitp__aitp_v5_*` | `aitp_v5_*` |
| User questions | `AskUserQuestion` | `question` |
| Tool discovery | `ToolSearch` | Not needed because configured tools are visible |

## Tool Adaptation

The plugin reads `deploy/templates/claude-code/using-aitp.md` and applies these
runtime transformations:

- `mcp__aitp__aitp_v5_*` -> `aitp_v5_*`
- `AskUserQuestion` -> `question`
- `"multiSelect"` -> `"multiple"`
- `{{TOPICS_ROOT}}` and `{{REPO_ROOT}}` -> resolved paths
- remove `ToolSearch` references, which do not apply to OpenCode

The OpenCode adapter therefore shares one canonical v5 skill source with
Claude Code.

## Research Behavior

During OpenCode research:

1. Resolve the v5 workspace and use
   `aitp_v5_build_workspace_recovery_audit` when only a topic is known.
2. Restore the selected session with `aitp_v5_get_execution_brief` and bounded
   relation/context expansion before drawing conclusions from prior work.
3. Treat summaries, hooks, old L0-L4 files, and adapter text as orientation,
   never as claim evidence or trust support.
4. Record durable research moments through typed `aitp_v5_*` writes; do not
   write new progress into the legacy stage machine.
5. Keep trust, promotion, installation, and destructive mutations behind their
   explicit human or validation checkpoints.
6. Use the `question` tool when structured user input is required.

## Config Reference

Global `~/.config/opencode/opencode.json`:

```json
{
  "mcp": {
    "aitp": {
      "type": "local",
      "command": ["python", "<AITP_REPO>/brain/v5/native_mcp.py"],
      "enabled": true
    }
  },
  "tools": { "aitp_v5_*": true }
}
```

Workspace `opencode.json`:

```json
{
  "tools": { "aitp_v5_*": true }
}
```
