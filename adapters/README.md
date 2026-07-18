# Adapter Assets

These files are compatibility pointers into the AITP v5 host integrations.
Every supported integration uses `brain/v5/native_mcp.py` and `aitp_v5_*`
typed tools. Legacy L0-L4 MCP and stage writes are not adapter runtimes.

Codex is the default interactive research host.

| Agent | Adapter Doc | V5 Assets | Repository capability |
|-------|-------------|-----------|-----------------------|
| Codex | `adapters/codex/SKILL.md` | `deploy/codex/`, `plugins/aitp-research-protocol/`, `.codex/hooks.json` installer | default host; pre/post-tool owner plus explicit first-turn fallback |
| Claude Code | `adapters/claude-code/SKILL.md` | `deploy/templates/claude-code/`, `hooks/` | SessionStart and pre/post-tool owner |
| Kimi Code | `adapters/kimi-code/SKILL.md` | `plugins/aitp-research-protocol-kimi/` plus project hook installer | user-level MCP/Skill package; project SessionStart and pre/post-tool owner |
| OpenCode | `adapters/opencode/SKILL.md` | Skill-path bootstrap plus `.opencode/plugins/aitp-v5.js` installer | pre/post-tool plugin owner plus explicit first-turn fallback |
| OpenClaw | `adapters/openclaw/SKILL.md` | manual v5 MCP connection only | no dedicated lifecycle installer |

Use the adapter-specific installer or configuration described by its reference.
Do not infer a shared executable, hook lifecycle, or capability set across hosts.
This table describes repository support; it is not an installation or readiness
claim for the current workspace. Use `adapter install-audit` and
`adapter host-readiness` before reporting a host as ready.
