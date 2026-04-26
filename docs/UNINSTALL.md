# Uninstall

Remove AITP from your AI agents.

## Automatic (recommended)

```bash
aitp uninstall
```

This removes hooks, skills, MCP configs, and the CLI wrapper from all
installed agents. It reads the install record at `~/.aitp/install-record.json`
to know exactly what was deployed.

Options:

```bash
aitp uninstall --agent claude-code    # Remove from Claude Code only
aitp uninstall --scope project        # Remove project-level install
```

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
```

Remove `[mcp.servers.aitp]` section from `~/.kimi/config.toml` and the
`aitp` entry from `~/.kimi/mcp.json`.

### Project scope

Same paths but under `<workspace>/.claude/` or `<workspace>/.kimi/` instead
of `~/`.

### CLI wrapper

```bash
rm -f ~/.local/bin/aitp        # Linux/macOS
# or delete aitp.cmd from your Python Scripts folder on Windows
```

### Install record

```bash
rm -f ~/.aitp/install-record.json
```
