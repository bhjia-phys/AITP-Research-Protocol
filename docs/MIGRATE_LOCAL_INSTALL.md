# Migrate AITP Local Install

Use this guide when your machine is in a mixed AITP state:

- the canonical repo already has the new CLI, skills, plugins, and runtime
- but your default `aitp` still points at an older editable install
- or your local workspace still exposes old command-harness entrypoints

If you are not keeping a repo-backed local workflow, the simpler public-package
migration is:

```bash
python -m pip uninstall aitp-kernel
python -m pip install aitp-kernel
aitp --version
aitp doctor
```

For both the public-package path and the editable local-dev path, the durable
home for your private topic state should be `~/.aitp/kernel`
(`%USERPROFILE%\\.aitp\\kernel` on Windows). The repo itself should stay public
project material, not the long-term home of your personal research data.

Use the rest of this guide only when you want to keep a canonical local
checkout plus its agent surfaces.

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
   - Claude Code now also refreshes the native AITP MCP registration in
     `~/.claude.json`
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
- Claude MCP registration is present and canonical
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
- Your personal kernel should continue to live at `~/.aitp/kernel` unless you intentionally override it with `--kernel-root`.
- This does not remove AITP compatibility entrypoints such as `aitp-codex` from the package itself. It only removes old local front-door surfaces from the active workspace path.
- This command is intentionally repo-backed. For a clean public-package path,
  prefer `python -m pip install aitp-kernel` instead of reinstalling the editable repo.
