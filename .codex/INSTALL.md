# Installing AITP For Codex App

This file is the Codex-facing install note for a repo-backed checkout.

The current checkout does not contain the public `aitp-kernel` package source
advertised by older docs. Use the repository-local installer or the v5 kernel
module path.

## Install Codex Skills

From the repository root:

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py install --agent codex --scope user
```

Project-local install:

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py install --agent codex --scope project --target-root <workspace>
```

Restart Codex after installation.

## What This Does

- Copies Codex-native gateway skills from `deploy/codex/skills/`.
- Copies protocol skills from `skills/` with a Codex adapter preamble.
- Writes a best-effort `mcp.json` beside each Codex skill root.
- Records the install in `%USERPROFILE%\.aitp\install-record.json`.

Codex-specific skill roots are preferred:

- `%USERPROFILE%\.codex\skills`
- `%USERPROFILE%\.codex-home\skills`
- `%USERPROFILE%\.codex-switcher\skills`

If none exists, the installer creates `%USERPROFILE%\.codex\skills`.

## Verify

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py doctor
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.cli --help
python -m brain.v5.cli --help
```

Expected Codex assets:

- `using-aitp/SKILL.md`
- `aitp-runtime/SKILL.md`
- `mcp.json` containing an `aitp` MCP server entry

## AITP v5 Hook Bridge

AITP v5 adapter packets expose `runtime_hook_installation`. Codex can use this
field to generate explicit guard-call instructions for:

- `pre_commit`
- `pre_tool`
- `post_tool`

The generated bridge is orientation-only. It must keep
`summary_inputs_trusted=false` and cannot update kernel state by itself. Trust
changes still require typed v5 kernel records.

Repo-backed v5 workspaces can materialize the same bridge directly from an
adapter packet:

```powershell
python -m brain.v5.cli --base <workspace> adapter hook-bridge codex <session-id> --output .codex/AITP_V5_HOOK_BRIDGE.md
```

The command builds the Codex adapter packet, reads its
`runtime_hook_installation`, writes the bridge file, and returns a contracted
`codex_hook_bridge` payload. MCP clients should use
`aitp_v5_write_codex_hook_bridge`.

When a `post_tool` guard call emits a `hook_trace_event`, persist the payload
through the v5 trace bridge instead of copying it into notes or summaries:

```powershell
python -m brain.v5.cli --base <workspace> trace hook-event persist --payload-json '<hook_trace_event_json>'
```

MCP clients should use `aitp_v5_persist_hook_trace_event`. This records process
history in `.aitp/runtime/hook_trace_events.jsonl`; it does not create evidence
or change claim trust.

## Important Codex Behavior

Codex does not use Claude-only `AskUserQuestion` or `ToolSearch` names. The
deployed Codex skills map those protocol instructions to Codex behavior:

- Ask the user normally unless a structured Codex input tool is active.
- Wait for explicit user approval at human gates.
- Use actual Codex MCP tool names for AITP tools.
- Do not manually edit AITP topic state if the MCP tools are unavailable.

## Uninstall

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py uninstall --agent codex --scope user
```
