# Install Guide

This is the single install path for AITP v5.

## Prerequisites

- Python 3.10+
- Git
- At least one supported agent: Claude Code, Kimi Code, or Codex

## Install

```bash
git clone git@github.com:bhjia-phys/AITP-Research-Protocol.git
cd AITP-Research-Protocol
python scripts/aitp-pm.py install
```

For research workspaces, prefer a project-scope install so every agent uses the
same repository, topic store, and MCP entrypoint:

```bash
python scripts/aitp-pm.py install --agent all --scope project \
  --target-root /path/to/workspace \
  --topics-root /path/to/workspace/research/aitp-topics
```

The installer deploys v5 gateway skills, v5-safe hooks, and MCP configs. User
scope also registers a global `aitp` wrapper when possible; project scope does
not.

## Options

```bash
# Install for a specific agent only
python scripts/aitp-pm.py install --agent claude-code

# Project-level install
python scripts/aitp-pm.py install --scope project --target-root /path/to/workspace

# Custom topics directory
python scripts/aitp-pm.py install --topics-root /path/to/workspace/research/aitp-topics
```

## What Gets Installed

For Claude Code:
- v5-safe prompt/router hooks: `aitp-keyword-router.py` and
  `aitp-routing-guard.py`
- v5 adapter hooks: `aitp-v5-*.py`
- `using-aitp` and `aitp-runtime` gateway skills
- `.mcp.json` or user MCP config pointing at `brain/v5/native_mcp.py`

For Kimi Code:
- `using-aitp` and `aitp-runtime` gateway skills
- `.kimi/mcp.json` and `.kimi/config.toml` pointing at
  `brain/v5/native_mcp.py`

For Codex:
- `.codex/skills/using-aitp/` and `.codex/skills/aitp-runtime/`
- `.codex/mcp.json` and `.codex/config.toml` pointing at
  `brain/v5/native_mcp.py`

Legacy L0/L1/L3/L4 stage skills and lifecycle hooks are not deployed by
default. They are available only for explicit compatibility installs:

```bash
AITP_INSTALL_LEGACY_STAGE_SKILLS=1 python scripts/aitp-pm.py install ...
AITP_INSTALL_LEGACY_STAGE_HOOKS=1 python scripts/aitp-pm.py install ...
```

## Verify

```bash
python scripts/aitp-pm.py doctor
python scripts/aitp-pm.py status
```

The health check verifies Python dependencies, repository files, topics root,
v5 MCP entrypoints, project-scope consistency across Claude/Kimi/Codex, and
local stale residue that could route an agent back to old paths or legacy MCP.

## Agent Details

- [Claude Code](INSTALL_CLAUDE_CODE.md)
- [Kimi Code](INSTALL_KIMI_CODE.md)
- [Codex](INSTALL_CODEX.md)

After install verification, continue with:
- [QUICKSTART.md](QUICKSTART.md)
- [README.md](../README.md)
