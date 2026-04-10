# Migrate AITP Local Install

Use this guide when your machine is in a mixed AITP state:

- the canonical repo already has the new CLI, skills, plugins, and runtime
- but your default `aitp` still points at an older editable install
- or your local workspace still exposes old command-harness entrypoints

## What mixed install looks like

Typical symptoms:

- `aitp --help` does not show `new-topic`, `status`, `next`, `work`, `current-topic`, or `session-start`
- `python -m pip show aitp-kernel` points to an older editable install such as a private workspace checkout
- Codex skills are partially new, but Claude or OpenCode are not fully converged
- the workspace root still contains files such as:
  - `AITP_COMMAND_HARNESS.md`
  - `AITP_MCP_CONFIG.json`
  - `aitp.md`
  - `aitp-loop.md`
  - `aitp-resume.md`
  - `aitp-audit.md`

## What the migration command does

Run:

```bash
aitp migrate-local-install --workspace-root /path/to/Theoretical-Physics --json
```

On Windows:

```cmd
aitp migrate-local-install --workspace-root D:\BaiduSyncdisk\Theoretical-Physics --json
```

Default behavior:

1. inspect the current local install with `pip show aitp-kernel`
2. if the editable install is not the canonical repo, uninstall the old package and reinstall from:
   - `AITP-Research-Protocol/research/knowledge-hub`
3. refresh user-level Codex, Claude Code, and OpenCode AITP assets
4. explicitly enable the OpenCode AITP plugin in `~/.config/opencode/opencode.json`
5. back up and remove workspace-root legacy harness files
6. back up and remove any user-level Claude `aitp*.md` legacy command bundles
7. run doctor logic before and after, then return a structured report
8. report front-door runtime convergence before and after for Codex, Claude Code, and OpenCode

## Backups

Unless you pass `--backup-root`, backups are written to:

```text
<workspace-root>/archive/aitp-local-migration/<timestamp>/
```

This includes:

- workspace-root legacy harness files
- user-level Claude legacy `aitp*.md` command files when present

## Verify after migration

Run:

```bash
aitp doctor --workspace-root /path/to/Theoretical-Physics --json
```

The local install is considered converged when:

- `overall_status` is `clean`
- `package.editable_project_location` points to the canonical repo
- Codex skills are present and match canonical text
- Claude hook surfaces are present
- OpenCode plugin is actually enabled in `opencode.json`
- no workspace-root legacy harness files remain active
- `runtime_convergence_after.front_door_runtimes_converged` is `true`

The migration report now also includes:

- `runtime_convergence_before.status_by_runtime`
- `runtime_convergence_after.status_by_runtime`

so you can see exactly which front-door runtimes were repaired and which ones
still need manual follow-up.

## Notes

- This migration preserves the `Theoretical-Physics` workspace as the working directory you use day to day.
- What changes is the underlying AITP install source and the active local agent-entry surfaces.
- This does not remove AITP compatibility entrypoints such as `aitp-codex` from the package itself. It only removes old local front-door surfaces from the active workspace path.
