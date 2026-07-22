# AITP Research Protocol — Kimi Code Plugin

Kimi Code plugin for the local AITP 1.0 v5 physics research graph kernel.
It mirrors the Codex plugin (`../aitp-research-protocol/`) for Kimi Code hosts:

- declares the `aitp` MCP server (full `aitp_v5_*` tool surface),
- ships the `using-aitp` / `aitp-runtime` / `configure-aitp` skills,
- auto-loads `using-aitp` at session start (`sessionStart.skill`),
- provides a first-run setup mode (`aitp_config_status`, `aitp_suggest_config`,
  `aitp_configure`) when no AITP checkout is configured yet.

## Requirements

- Kimi Code CLI with plugin support (`/plugins`).
- `uv` on `PATH` (the MCP server runs through `uv run --with ...`).
- A local checkout of `AITP-Research-Protocol` (first-run setup can also clone
  or locate one).

## Install

From Kimi Code:

```text
/plugins install F:/AI_Workspace/repos/AITP-Research-Protocol/plugins/aitp-research-protocol-kimi
```

or browse the repo-local marketplace catalog:

```text
/plugins marketplace F:/AI_Workspace/repos/AITP-Research-Protocol/plugins/marketplace.kimi.json
```

Then run `/reload` (or open a new session).

Kimi Code installs plugins per user (all projects) and always runs the managed
copy; re-install to pick up changes from this directory.

## First-Run Configuration

If no AITP checkout is configured, the MCP server starts in setup mode and
exposes only `aitp_config_status`, `aitp_suggest_config`, and `aitp_configure`.
Tell Kimi where your `AITP-Research-Protocol` checkout is (or let it clone
`https://github.com/bhjia-phys/AITP-Research-Protocol.git`), then run `/reload`
so the full `aitp_v5_*` tools load.

Configuration is stored in `~/.aitp/kimi-plugin-config.json`, independent from
the Codex plugin's `~/.aitp/codex-plugin-config.json`.

## Interaction With Project-Scope Installs

Do not run this plugin together with a project-scope AITP install in the same
workspace: both register an MCP server named `aitp`. In workspaces that already
have a project-level AITP MCP config (for example the `Theoretical-Physics`
workspace with `.kimi-code/config.toml`), either skip installing this plugin or
disable only its MCP server and keep the skills:

```text
/plugins mcp disable aitp-research-protocol aitp
```

## Update

Plugins do not auto-update. Re-run `/plugins install <path>` (or accept the
update offered in the `/plugins` marketplace tab) and `/reload`.

## Layout

- `kimi.plugin.json` — Kimi Code plugin manifest
- `scripts/launch_aitp_mcp_kimi.py` — MCP launcher with first-run setup mode
- `skills/` — `using-aitp`, `aitp-runtime`, `configure-aitp`
