# Adapter Assets

These files are compatibility pointers into the AITP v5 host integrations.
Every supported integration uses `brain/v5/native_mcp.py` and `aitp_v5_*`
typed tools. Legacy L0-L4 MCP and stage writes are not adapter runtimes.

Codex is the default interactive research host.

| Agent | Adapter Doc | V5 Assets | Status |
|-------|-------------|-----------|--------|
| Codex | `adapters/codex/SKILL.md` | `deploy/codex/`, `plugins/aitp-research-protocol/` | default |
| Claude Code | `adapters/claude-code/SKILL.md` | `deploy/templates/claude-code/`, `hooks/` | supported |
| OpenCode | `adapters/opencode/SKILL.md` | `deploy/templates/opencode/aitp-plugin.js` | reference integration |
| OpenClaw | `adapters/openclaw/SKILL.md` | manual v5 MCP connection only | no dedicated lifecycle installer |

Use the adapter-specific installer or configuration described by its reference.
Do not infer a shared executable, hook lifecycle, or capability set across hosts.
