# Install Claude Code Adapter

## Prerequisites

- an `aitp` executable on `PATH`
- a local Claude Code installation

## Install skill

```bash
mkdir -p ~/.claude/skills/aitp-runtime
cp adapters/claude-code/SKILL.md ~/.claude/skills/aitp-runtime/SKILL.md
```

## Install commands

```bash
mkdir -p ~/.claude/commands
cp adapters/claude-code/commands/aitp.md ~/.claude/commands/aitp.md
cp adapters/claude-code/commands/aitp-loop.md ~/.claude/commands/aitp-loop.md
cp adapters/claude-code/commands/aitp-audit.md ~/.claude/commands/aitp-audit.md
```

## Verify

Claude Code should be able to:

- route substantial research work through `aitp`
- read the runtime protocol bundle first
- refuse to count missing-conformance work as AITP work

## Remove

See [`docs/UNINSTALL.md`](UNINSTALL.md).
