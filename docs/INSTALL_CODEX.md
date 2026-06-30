# Install Codex App Adapter

Status: repository-local adapter support is available through
`scripts/aitp-pm.py install --agent codex`, and a local Codex plugin is
available under `plugins/aitp-research-protocol`. The older public-package commands
(`aitp-kernel`, `aitp install-agent --agent codex`, and
`scripts/aitp-local.cmd install-agent`) are not valid for this checkout until
the missing `research/knowledge-hub/knowledge_hub` package source is restored.

## Install The Codex Plugin

The plugin route is the easiest Codex App entry point. It provides the AITP
gateway skills, launches the v5 MCP server, and falls back to a first-run setup
MCP if the local AITP checkout has not been configured yet.

From the repository root:

```powershell
codex plugin marketplace add .agents/plugins
codex plugin add aitp-research-protocol@aitp-local
codex plugin list --marketplace aitp-local
```

Then restart Codex or open a new thread.

On first use, the setup MCP exposes:

- `aitp_config_status`
- `aitp_suggest_config`
- `aitp_configure`

Codex should ask for the local `AITP-Research-Protocol` checkout path and the
topics root where typed records should live. The default topics root is
`~/.aitp/topics`. Configuration is saved to
`~/.aitp/codex-plugin-config.json`; after it is written, restart Codex or open a
new thread so the compact Codex AITP surface loads. The plugin launcher sets
`AITP_MCP_SURFACE=codex` by default; set `AITP_MCP_SURFACE=full` only for
kernel development or maintenance sessions that need the complete `aitp_v5_*`
surface.

The plugin resolves configuration in this order:

1. `AITP_REPO_ROOT` and `AITP_TOPICS_ROOT` environment variables.
2. `~/.aitp/codex-plugin-config.json`.
3. `~/.aitp/install-record.json` from `scripts/aitp-pm.py install`.
4. `vendor/AITP-Research-Protocol` inside the plugin directory.
5. The current working directory or one of its parents.

Remove the plugin with:

```powershell
codex plugin remove aitp-research-protocol@aitp-local
```

That removes the Codex plugin registration and local plugin cache. It does not
delete the AITP checkout, topics root, or adapter files installed with
`scripts/aitp-pm.py`.

## Install From This Checkout

Use `uv` unless your default `python` already has `pyyaml`, `jsonschema`, and
`fastmcp` installed:

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp `
  python scripts/aitp-pm.py install `
  --agent codex `
  --scope user
```

Project-local install:

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp `
  python scripts/aitp-pm.py install `
  --agent codex `
  --scope project `
  --target-root <workspace>
```

The installer deploys:

- Codex-native gateway skills from `deploy/codex/skills/`.
- Protocol skills from `skills/`, wrapped with a Codex adapter preamble that
  maps Claude/Kimi tool names to Codex behavior.
- A compatibility `mcp.json` beside each Codex skill root.
- A `[mcp_servers.aitp]` entry in the adjacent `config.toml`, using `uv` when
  available so the MCP server has its Python dependencies.
- Lightweight project hooks: `hooks/aitp-keyword-router.py`,
  `hooks/aitp-routing-guard.py`, and `hooks.json`. The router is an orientation
  reminder only. The guard blocks direct `Write`, `Edit`, and `MultiEdit` writes
  into AITP state stores.

Session-bound v5 bridge hooks are not enabled by this default Codex install.
Use `aitp-v5 adapter install-hooks codex <session-id> --settings
<workspace>/.codex/hooks.json` only when a concrete v5 session should receive
native pre-tool/post-tool lifecycle handling. Bridge hooks still cannot update
claim trust.

User-scope Codex skill roots are detected in this order when present:

- `%USERPROFILE%\.codex\skills`
- `%USERPROFILE%\.codex-home\skills`
- `%USERPROFILE%\.codex-switcher\skills`

If no Codex-specific root exists, the installer creates
`%USERPROFILE%\.codex\skills`.

## Verify

Run:

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp `
  python scripts/aitp-pm.py doctor

uv run --with pyyaml --with jsonschema --with fastmcp `
  python -m brain.v5.cli --help
```

Inspect deployed skills if needed:

```powershell
Get-ChildItem "$env:USERPROFILE\.codex\skills"
Get-ChildItem "$env:USERPROFILE\.codex-home\skills"
Get-ChildItem "$env:USERPROFILE\.codex-switcher\skills"
```

Codex should discover at least:

- `using-aitp`
- `aitp-runtime`

Check the Codex MCP registration:

```powershell
codex mcp get aitp
```

The `aitp` entry should show:

- `command: uv` when `uv` is installed, otherwise `command: python`
- `cwd: <AITP checkout>`
- `startup_timeout_sec: 60`
- `env: AITP_TOPICS_ROOT=...`

Run a real Codex MCP smoke test from a workspace that has AITP topics:

```powershell
codex exec --dangerously-bypass-approvals-and-sandbox `
  -C <workspace> `
  "Call the read-only AITP list topics tool with topics_root='<topics-root>' and report the topic count."
```

The startup log should include `mcp: aitp ready`, and the tool call should use
the Codex-exposed AITP tool namespace.

## Runtime Behavior

Codex does not use Claude-only tools such as `AskUserQuestion` and
`ToolSearch`. The Codex gateway skills say how to map those upstream protocol
phrases:

- Ask the user through Codex's available interaction surface.
- If no structured prompt tool is active, ask one concise plain-text question
  and wait.
- Map `mcp__aitp__aitp_*` examples to the actual AITP MCP tool names exposed
  by Codex.
- If MCP tools are unavailable, diagnose setup instead of manually mutating
  AITP topic state.

## Remove

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp `
  python scripts/aitp-pm.py uninstall `
  --agent codex `
  --scope user
```

For full cleanup guidance, see [UNINSTALL.md](UNINSTALL.md).
