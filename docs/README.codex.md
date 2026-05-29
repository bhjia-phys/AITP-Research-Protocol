# AITP For Codex App

Codex app uses AITP through native skill discovery plus an AITP MCP server.
This checkout now provides a repository-local Codex adapter path:

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py install --agent codex --scope user
```

Then restart Codex.

## What Gets Installed

- `using-aitp`: Codex-native front-door routing for theory work.
- `aitp-runtime`: Codex-native runtime loop for L0 -> L1 -> L3 -> L4 -> L2.
- Wrapped protocol skills from `skills/`, with a Codex adapter preamble.
- `mcp.json` next to the Codex skill root for compatibility.
- `[mcp_servers.aitp]` in the adjacent `config.toml`, which is the Codex
  CLI/App path used by current local stdio MCP startup.

The installer uses Codex-specific roots such as `~/.codex/skills`,
`~/.codex-home/skills`, or `~/.codex-switcher/skills`. It does not rely on the
shared `~/.agents/skills` root by default, so Kimi/other agent deployments are
not clobbered.

## Current Checkout Caveat

Do not use the older public-package commands from stale docs:

```text
python -m pip install aitp-kernel
aitp install-agent --agent codex --scope user
scripts\aitp-local.cmd install-agent --agent codex --scope user
```

Those commands require a package entrypoint that is not present in this
checkout. Use `scripts/aitp-pm.py install --agent codex` instead.

## Verify

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py doctor
```

The Codex section should show `using-aitp/SKILL.md`, `aitp-runtime/SKILL.md`,
`config.toml [mcp_servers.aitp]: OK`, and the compatibility `mcp.json`.

For a direct MCP startup smoke test against Codex's active config:

```powershell
codex mcp get aitp
codex exec --dangerously-bypass-approvals-and-sandbox -C <workspace> "Call the read-only AITP list topics tool with topics_root='<topics-root>' and report the topic count."
```

Expected startup evidence in the `codex exec` output:

```text
mcp: aitp ready
```

For full instructions, see [INSTALL_CODEX.md](INSTALL_CODEX.md).
