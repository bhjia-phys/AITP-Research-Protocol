# AITP Research Protocol Codex Plugin

This plugin connects Codex to a local checkout of
`bhjia-phys/AITP-Research-Protocol` and exposes the AITP v5 MCP tools plus
three Codex skills:

- `using-aitp`
- `aitp-runtime`
- `configure-aitp`

## Portability

This is portable across machines, but it is not a standalone cloud package. The
plugin needs a local AITP kernel checkout.

Startup resolves paths in this order:

1. `AITP_REPO_ROOT` and `AITP_TOPICS_ROOT` environment variables.
2. `~/.aitp/codex-plugin-config.json` written by the first-run setup tools.
3. `~/.aitp/install-record.json` written by `scripts/aitp-pm.py install`.
4. `vendor/AITP-Research-Protocol` inside this plugin directory.
5. The current working directory or one of its parents.

If the launcher cannot find a repo checkout, it starts a setup-mode MCP server
instead of failing. Setup mode exposes:

- `aitp_config_status`
- `aitp_suggest_config`
- `aitp_configure`

Codex should ask the user for the repo checkout path and topics root, then call
`aitp_configure`.

If no topics root is configured, the launcher uses `~/.aitp/topics` and creates
it on first startup.

## Requirements

- Codex app with local plugins enabled.
- Python 3.10 or newer.
- `uv` on `PATH`.
- A local checkout of `AITP-Research-Protocol`.

## Install

Clone the AITP repo:

```powershell
git clone https://github.com/bhjia-phys/AITP-Research-Protocol.git
cd AITP-Research-Protocol
```

Add the repo-local marketplace and install the plugin:

```powershell
codex plugin marketplace add .agents/plugins
codex plugin add aitp-research-protocol@aitp-local
codex plugin list --marketplace aitp-local
```

Then restart Codex or open a new thread.

## First-Run Configuration

Set environment variables before launching Codex, run the repo installer so
`~/.aitp/install-record.json` records paths, or configure through the setup MCP
tool.

```powershell
$env:AITP_REPO_ROOT = "C:/path/to/AITP-Research-Protocol"
$env:AITP_TOPICS_ROOT = "C:/path/to/aitp-topics"
```

```text
aitp_configure(repo_root="C:/path/to/AITP-Research-Protocol", topics_root="C:/path/to/aitp-topics")
```

After configuration, restart Codex or open a new thread so the full `aitp_v5_*`
tool surface loads.

The skills should call AITP v5 tools with `base=""` unless the user explicitly
provides a topics root. The MCP server resolves the empty base to
`AITP_TOPICS_ROOT`.

## Use

In a Codex thread, use the plugin skills for AITP-backed work:

- Use `using-aitp` to enter a topic, check prior progress, or continue research.
- Use `aitp-runtime` once full `aitp_v5_*` tools are available.
- Use `configure-aitp` when the plugin is in setup mode or paths have moved.

AITP records are written under the configured topics root, not inside the
plugin cache.

## Remove

```powershell
codex plugin remove aitp-research-protocol@aitp-local
```

This removes the Codex plugin registration and local cache. It does not delete
the AITP checkout, topics root, or adapter files installed by
`scripts/aitp-pm.py`.

## Fully Self-Contained Option

For an offline or demo package, copy the AITP checkout into:

```text
vendor/AITP-Research-Protocol
```

That makes the plugin carry the kernel code, while the user's research store
still lives outside the plugin under `AITP_TOPICS_ROOT` or `~/.aitp/topics`.

## Validation

From the plugin root:

```powershell
python <path-to-plugin-creator>/scripts/validate_plugin.py .
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/launch_aitp_mcp.py
```

The second command starts the MCP server and waits for Codex/MCP input.
