# Install Claude Code Adapter

## Prerequisites

- Python 3.10+
- Claude Code installed locally

## Install the AITP runtime

From the repository root:

```bash
python -m pip install -e research/knowledge-hub
aitp doctor
```

## Install the Claude Code wrapper

```bash
aitp install-agent --agent claude-code --scope user
```

This installs:

- the `aitp-runtime` skill under `~/.claude/skills/aitp-runtime/`
- command files under `~/.claude/commands/`
- an MCP setup note for the optional `aitp-mcp` tool surface

## Recommended entrypoint

Use:

```bash
aitp loop --topic-slug <topic_slug> --human-request "<task>"
```

Use `aitp bootstrap ...` only to create a new topic shell, then return to the
loop.

## Verify

Claude Code should now be able to:

- route substantial research work through `aitp`
- read the runtime protocol bundle first
- refuse to count missing-conformance work as AITP work

## Manual fallback

Reference assets still live at:

- `adapters/claude-code/SKILL.md`
- `adapters/claude-code/commands/`

## Remove

See [`docs/UNINSTALL.md`](UNINSTALL.md).
