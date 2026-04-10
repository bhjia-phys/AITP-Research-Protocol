# Install Claude Code Adapter

Claude Code should use AITP through SessionStart bootstrap, not through
`/aitp`-style command bundles.

## Prerequisites

- Claude Code installed locally
- Python 3.10+

## Install the AITP runtime

From the repository root:

```bash
python -m pip install -e research/knowledge-hub
aitp doctor
```

If this machine previously used an older workspace-backed editable install,
first converge the local install:

- [`docs/MIGRATE_LOCAL_INSTALL.md`](MIGRATE_LOCAL_INSTALL.md)

## Preferred install

Install the AITP Claude plugin from this repository so Claude Code can load:

- `.claude-plugin/plugin.json`
- `hooks/hooks.json`
- `hooks/session-start`
- `skills/using-aitp/`
- `skills/aitp-runtime/`

The intended outer behavior matches Superpowers:

- SessionStart injects `using-aitp`;
- natural-language theory requests enter AITP before substantive work;
- current-topic continuation and steering stay natural-language first.
- ordinary topic work should remain in a light runtime profile unless a real
  escalation trigger fires.

This is the preferred path because Claude Code should not need a custom
`/aitp` command vocabulary for normal AITP use. The session should already be
inside the right routing discipline before substantial work begins.

This is currently a plugin skeleton plus runtime install, not a marketplace
one-click package. The product direction is still plugin-first.

## Compatibility install

If you want local copied assets instead of plugin-managed assets:

```bash
aitp install-agent --agent claude-code --scope project --target-root /path/to/theory-workspace
```

This now writes:

- `.claude/skills/using-aitp/`
- `.claude/skills/aitp-runtime/`
- `.claude/skills/aitp-runtime/AITP_MCP_SETUP.md`
- `.claude/hooks/session-start`
- `.claude/hooks/run-hook.cmd`
- `.claude/hooks/hooks.json`
- `.claude/settings.json`

It no longer writes `.claude/commands/aitp*.md` by default.

## Verify

Claude Code should now:

- inject `using-aitp` at SessionStart;
- route substantial theory work through AITP before response;
- follow `runtime_protocol.generated.md` after routing succeeds.

Use `aitp doctor --json` to verify not just file presence but also whether the
Claude bootstrap assets still match the canonical hook files and whether
`.claude/settings.json` still wires the expected SessionStart command.

If you are migrating from an older setup, remove any legacy `.claude/commands/aitp*.md`
bundle so SessionStart bootstrap is the only default entry.

## Manual fallback

If bootstrap is unavailable:

```bash
aitp session-start "<task>"
```

## Remove

See [`docs/UNINSTALL.md`](UNINSTALL.md).
