# Uninstall

Remove AITP from your AI agents.

## Automatic (recommended)

From the AITP repository checkout:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py uninstall \
  --agent all \
  --scope project \
  --target-root /path/to/workspace
```

This removes generated hooks, skills, and MCP configs for the recorded
project-scope install. It reads the install record at
`~/.aitp/install-record.json` to know what was deployed.

For user-scope installs, use:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py uninstall \
  --agent all \
  --scope user
```

If a user-scope install registered the global `aitp` wrapper, this shorter
command may also be available:

```bash
aitp uninstall
```

Options:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py uninstall \
  --agent claude-code \
  --scope project \
  --target-root /path/to/workspace

uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py uninstall \
  --agent codex \
  --scope user
```

Uninstall does not delete the AITP repository checkout or the topics root that
contains research records.

## Manual cleanup

If `aitp uninstall` is unavailable, remove these paths manually:

### Claude Code (user scope)

```bash
rm -rf ~/.claude/hooks/session-start.py
rm -rf ~/.claude/hooks/compact.py
rm -rf ~/.claude/hooks/stop.py
rm -rf ~/.claude/hooks/run-hook.cmd
rm -rf ~/.claude/hooks/hooks.json
rm -rf ~/.claude/hooks/aitp-keyword-router.py
rm -rf ~/.claude/hooks/aitp-routing-guard.py
rm -rf ~/.claude/skills/using-aitp
rm -rf ~/.claude/skills/aitp-runtime
```

Then edit `~/.claude/settings.json` to remove AITP hook blocks
(SessionStart, UserPromptSubmit, PreToolUse blocks with `aitp` in the command).

Remove the AITP entry from your MCP config (`~/.claude/mcp.json` or
`~/.claude.json`):

```bash
claude mcp remove aitp
```

### Kimi Code (user scope)

```bash
rm -rf ~/.kimi/skills/using-aitp
rm -rf ~/.kimi/skills/aitp-runtime
rm -rf ~/.kimi-code/skills/using-aitp
rm -rf ~/.kimi-code/skills/aitp-runtime
```

Remove `[mcp.servers.aitp]` section from `~/.kimi/config.toml` and the
`aitp` entry from `~/.kimi/mcp.json`. For migrated Kimi Code installs, remove
the marked AITP hook block from `~/.kimi-code/config.toml` and the `aitp`
entry from `~/.kimi-code/mcp.json` if those files exist.

### Codex App Plugin

If you installed the repository-backed Codex plugin, remove it separately:

```bash
codex plugin remove aitp-research-protocol@aitp-local
```

If you no longer want Codex to see the local marketplace, remove that source:

```bash
codex plugin marketplace remove aitp-local
```

Removing the plugin does not delete `~/.aitp/codex-plugin-config.json`, the AITP
checkout, or the topics root. Delete those manually only when you no longer need
the configuration or research records.

### Project scope

Same paths but under `<workspace>/.claude/`, `<workspace>/.codex/`,
`<workspace>/.kimi/`, or `<workspace>/.kimi-code/` instead of `~/`. Also check
the project `.mcp.json` for an `aitp` server entry.

### CLI wrapper

```bash
rm -f ~/.local/bin/aitp        # Linux/macOS
# or delete aitp.cmd from your Python Scripts folder on Windows
```

### Install record

```bash
rm -f ~/.aitp/install-record.json
```
