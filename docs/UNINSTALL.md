# Uninstall

Remove the adapter assets you installed.

## OpenClaw

```bash
rm -rf ~/.openclaw/skills/aitp-runtime
```

Also remove any `aitp` MCP bridge entry from your OpenClaw configuration.

## Codex

```bash
rm -rf ~/.codex/skills/aitp-runtime
rm -rf ~/.codex-home/skills/aitp-runtime
```

Also remove any `aitp` MCP registration if you added one.

## Claude Code

```bash
rm -rf ~/.claude/skills/aitp-runtime
rm -f ~/.claude/commands/aitp.md
rm -f ~/.claude/commands/aitp-loop.md
rm -f ~/.claude/commands/aitp-audit.md
```

## OpenCode

```bash
rm -f ~/.config/opencode/commands/AITP_COMMAND_HARNESS.md
rm -f ~/.config/opencode/commands/aitp.md
rm -f ~/.config/opencode/commands/aitp-loop.md
rm -f ~/.config/opencode/commands/aitp-audit.md
```

Also remove any `aitp` MCP entry from the OpenCode configuration file.
