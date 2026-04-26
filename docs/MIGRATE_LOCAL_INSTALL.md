# Migrate Local Install

> **Status:** The `aitp migrate-local-install` command is planned but not yet
> implemented in `aitp-pm.py`. Use the manual migration steps below.

## When to use this guide

Your machine is in a mixed AITP state:
- Old workspace-backed editable install
- Legacy `aitp*.md` command bundles still present
- Skills are partially deployed across different agent roots

## Manual migration

### 1. Clean up old install

```bash
# Remove any old pip install
python -m pip uninstall aitp-kernel

# Remove legacy command bundles
rm -f ~/.claude/commands/aitp*.md
rm -f <workspace>/AITP_COMMAND_HARNESS.md
rm -f <workspace>/AITP_MCP_CONFIG.json
rm -f <workspace>/aitp.md
rm -f <workspace>/aitp-loop.md
rm -f <workspace>/aitp-resume.md
rm -f <workspace>/aitp-audit.md
```

### 2. Run uninstall to clean old agent configs

```bash
python scripts/aitp-pm.py uninstall
```

### 3. Fresh install

```bash
python scripts/aitp-pm.py install
```

### 4. Verify

```bash
aitp doctor
```

## What the planned `migrate-local-install` command will do

When implemented, it will:
1. Inspect current install state
2. Uninstall old editable packages
3. Refresh all agent assets (Claude Code, Kimi Code)
4. Back up and remove legacy harness files
6. Report front-door convergence before/after

## Notes

- This preserves your `Theoretical-Physics` workspace
- Your research topics in `aitp-topics/` are never touched by install/uninstall
- The repo stays public project material; personal research data stays in topics root
