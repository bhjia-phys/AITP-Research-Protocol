# Install Guide

The single install path for AITP.

## Prerequisites

- Python 3.10+
- Git
- An AI agent (Claude Code, Kimi Code)

## Install

```bash
git clone git@github.com:bhjia-phys/AITP-Research-Protocol.git
cd AITP-Research-Protocol
python scripts/aitp-pm.py install
```

The installer detects your installed AI agents, prompts for where to store
research topics, and deploys hooks, skills, and MCP configs automatically.

After install, the `aitp` command is available globally:

```bash
aitp doctor     # Full health check
aitp status     # Show what's installed and file health
```

## Options

```bash
# Install for a specific agent only
python scripts/aitp-pm.py install --agent claude-code

# Project-level install (writes to workspace/.claude/ instead of ~/.claude/)
python scripts/aitp-pm.py install --scope project

# Custom topics directory
python scripts/aitp-pm.py install --topics-root /path/to/your/topics
```

## What gets installed

For Claude Code (user scope):
- `~/.claude/hooks/` — session-start, keyword router, routing guard
- `~/.claude/skills/using-aitp/` — routes theory requests into AITP
- `~/.claude/skills/aitp-runtime/` — protocol execution loop
- `~/.claude/settings.json` — hook configuration (merged, not replaced)
- `~/.claude/mcp.json` or user MCP config — AITP MCP server registration

For Kimi Code (user scope):
- `~/.kimi/skills/using-aitp/` and `~/.kimi/skills/aitp-runtime/`
- `~/.kimi/mcp.json` and `~/.kimi/config.toml`

## Verify

```bash
aitp doctor
```

Checks: Python version, dependencies, repo integrity, topics root,
Claude Code hooks/skills/settings, Kimi Code MCP/config.

## Agent-specific details

- [Claude Code](INSTALL_CLAUDE_CODE.md)
- [Kimi Code](INSTALL_CLAUDE_CODE.md) — same pattern, different paths

Additional agent adapters are documented in `adapters/`. They are not
yet integrated into the `aitp-pm.py` one-click installer.

## Next steps

After install verification, continue with:
- [QUICKSTART.md](QUICKSTART.md) — your first research topic
- [README.md](../README.md) — protocol overview
