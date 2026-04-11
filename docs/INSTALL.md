# Install Guide

This is the consolidated install index for AITP.

## Common baseline

All supported runtime surfaces share the same kernel install step:

```bash
python -m pip install -e research/knowledge-hub
aitp doctor
```

Common prerequisites:

- Git
- Python 3.10+
- the runtime surface you actually want to use locally

The runtime package currently declares `python_requires=">=3.10"` in
`research/knowledge-hub/setup.py`.

## Pick your runtime

- Codex: [`docs/INSTALL_CODEX.md`](INSTALL_CODEX.md)
- OpenCode: [`docs/INSTALL_OPENCODE.md`](INSTALL_OPENCODE.md)
- Claude Code: [`docs/INSTALL_CLAUDE_CODE.md`](INSTALL_CLAUDE_CODE.md)
- OpenClaw: [`docs/INSTALL_OPENCLAW.md`](INSTALL_OPENCLAW.md)

## Migration and cleanup

- older editable-install migration:
  [`docs/MIGRATE_LOCAL_INSTALL.md`](MIGRATE_LOCAL_INSTALL.md)
- adapter/runtime removal:
  [`docs/UNINSTALL.md`](UNINSTALL.md)

## Verification

After installation, run:

```bash
aitp doctor
aitp doctor --json
```

Use the runtime-specific install docs above when you need platform-specific
bootstrap details after the shared kernel install succeeds.
