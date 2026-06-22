# AITP Research Protocol Codex Plugin

This plugin connects Codex to a local checkout of
`bhjia-phys/AITP-Research-Protocol` and exposes the AITP v5 MCP tools plus two
Codex skills:

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

## Setup On Another Machine

Clone the AITP repo:

```powershell
git clone https://github.com/bhjia-phys/AITP-Research-Protocol.git
```

Set environment variables before launching Codex, or run the repo installer so
`~/.aitp/install-record.json` records them:

```powershell
$env:AITP_REPO_ROOT = "C:/path/to/AITP-Research-Protocol"
$env:AITP_TOPICS_ROOT = "C:/path/to/aitp-topics"
```

Or configure through the setup MCP tool:

```text
aitp_configure(repo_root="C:/path/to/AITP-Research-Protocol", topics_root="C:/path/to/aitp-topics")
```

The skills should call AITP v5 tools with `base=""` unless the user explicitly
provides a topics root. The MCP server resolves the empty base to
`AITP_TOPICS_ROOT`.

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
