# AITP For Codex App

Codex app can use AITP in two ways:

1. A project/user adapter install through `scripts/aitp-pm.py`.
2. A repository-backed Codex plugin from `plugins/aitp-research-protocol`.

Use the project-scope adapter when you want one research workspace to carry the
configuration for all local agents. Use the plugin when you want Codex App to
install AITP from a local marketplace and guide first-run configuration.

## Codex Plugin

This checkout ships a local marketplace at `.agents/plugins` and a plugin at
`plugins/aitp-research-protocol`.

From the repository root:

```powershell
codex plugin marketplace add .agents/plugins
codex plugin add aitp-research-protocol@aitp-local
```

Then restart Codex or open a new thread.

### First-Run Configuration

If the plugin cannot find an AITP repo checkout, it starts a setup-mode MCP
server rather than failing. Setup mode exposes:

- `aitp_config_status`
- `aitp_suggest_config`
- `aitp_configure`

Codex should ask for:

1. the local `AITP-Research-Protocol` checkout path,
2. the topics root where AITP should store typed records.

If the user has no topics-root preference, use `~/.aitp/topics`. The setup tool
writes `~/.aitp/codex-plugin-config.json`. After successful configuration,
restart Codex or open a new thread so the full `aitp_v5_*` tools load.

## Project/User Adapter Install

This checkout also provides a repository-local Codex adapter path:

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
