# Uninstall

Remove the AITP adapter assets you installed.

If you also installed the runtime itself, remove it with:

```bash
python -m pip uninstall aitp-kernel
```

## OpenClaw

```bash
rm -rf ~/.openclaw/skills/using-aitp
rm -rf ~/.openclaw/skills/aitp-runtime
```

Also remove any `aitp` MCP bridge entry from your OpenClaw configuration.

## Codex

If you installed through native skill discovery:

```bash
rm ~/.agents/skills/aitp
```

If you used `aitp install-agent` instead:

```bash
rm -rf ~/.codex/skills/using-aitp
rm -rf ~/.codex/skills/aitp-runtime
rm -rf ~/.codex-home/skills/using-aitp
rm -rf ~/.codex-home/skills/aitp-runtime
```

Also remove any `aitp` MCP registration if you added one.

## Claude Code

Plugin-managed install:

```bash
rm -rf ~/.claude/plugins/aitp
```

Compatibility install:

```bash
rm -rf ~/.claude/skills/using-aitp
rm -rf ~/.claude/skills/aitp-runtime
rm -rf ~/.claude/hooks/session-start
rm -rf ~/.claude/hooks/run-hook.cmd
rm -rf ~/.claude/hooks/hooks.json
```

Then remove the corresponding `SessionStart` hook block from `~/.claude/settings.json` if you used the compatibility installer.

## OpenCode

Plugin-managed install:

```bash
rm -f ~/.config/opencode/plugins/aitp.js
```

Compatibility install:

```bash
rm -rf ~/.config/opencode/skills/using-aitp
rm -rf ~/.config/opencode/skills/aitp-runtime
rm -f ~/.config/opencode/plugins/aitp.js
```

Also remove any `aitp` MCP entry from the OpenCode configuration file.
