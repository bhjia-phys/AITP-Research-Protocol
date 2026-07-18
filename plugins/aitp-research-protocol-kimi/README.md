# AITP Research Protocol - Kimi Code Plugin

Kimi Code plugin for the local AITP v5 theoretical-physics research operating
memory.

The package:

- registers the `aitp` MCP server with the compact 10-tool research surface,
- ships the `using-aitp`, `aitp-runtime`, and `configure-aitp` Skills,
- auto-loads `using-aitp` at session start,
- exposes setup-only tools when no AITP checkout is configured.

The default is `AITP_MCP_SURFACE=codex`. This is a shared host-neutral compact
facade whose public names retain the `aitp_v5_codex_*` prefix for compatibility.
Set `AITP_MCP_SURFACE=full` explicitly only for kernel development or
maintenance.

## Requirements

- Kimi Code CLI with plugin support (`/plugins`).
- `uv` on `PATH`.
- A local checkout of `AITP-Research-Protocol`.

## Install

From Kimi Code:

```text
/plugins install F:/AI_Workspace/repos/AITP-Research-Protocol/plugins/aitp-research-protocol-kimi
```

Or browse the repo-local marketplace catalog:

```text
/plugins marketplace F:/AI_Workspace/repos/AITP-Research-Protocol/plugins/marketplace.kimi.json
```

Then run `/reload` or open a new session. Kimi Code uses a managed user-level
copy; reinstall the plugin to pick up changes from this directory.

## First-Run Configuration

If no AITP checkout is configured, the MCP server exposes only
`aitp_config_status`, `aitp_suggest_config`, and `aitp_configure`. Configure the
repository and topics root, then run `/reload` so the compact Kimi Code AITP
surface loads.

The launcher resolves the repository root in this order:

1. `AITP_REPO_ROOT`
2. `~/.aitp/kimi-plugin-config.json`
3. `~/.aitp/install-record.json`
4. the packaged `vendor/AITP-Research-Protocol` checkout

It resolves the topics root from `AITP_TOPICS_ROOT`, the Kimi plugin config,
the install record, or `~/.aitp/topics`. Kimi and Codex plugin configuration
files remain separate.

## Interaction With Project-Scope Installs

Do not run this plugin together with a project-scope AITP install in the same
workspace because both register an MCP server named `aitp`. This includes
project MCP configuration under `.kimi/config.toml` or
`.kimi-code/config.toml`.

Either skip the plugin in that workspace or disable only its MCP server and
keep the skills:

```text
/plugins mcp disable aitp-research-protocol aitp
```

Plugin MCP registration is distinct from project lifecycle-hook installation.
A Kimi hook may be installed and audited separately, only with explicit user
approval, and is runtime metadata rather than canonical research state.

## Update

Plugins do not auto-update. Re-run `/plugins install <path>` or accept the
marketplace update, then run `/reload`.

## Layout

- `kimi.plugin.json` - Kimi Code plugin manifest
- `scripts/launch_aitp_mcp_kimi.py` - launcher and first-run setup mode
- `skills/` - `using-aitp`, `aitp-runtime`, and `configure-aitp`
