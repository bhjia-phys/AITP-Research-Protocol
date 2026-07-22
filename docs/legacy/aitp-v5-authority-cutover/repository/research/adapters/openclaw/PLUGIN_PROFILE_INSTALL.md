# OpenClaw AITP Plugin Install

This document defines the current install surface for taking the AITP OpenClaw adapter into another OpenClaw workspace.
The public repository guarantees the plugin, the AITP kernel/adapter trees, and
any shipped seed files. If the source workspace also contains richer
workspace-root profile notes or `research-bot` templates, the installer copies
them too; if they are absent, it skips those optional legacy surfaces instead of
failing.

## What gets installed

The installer seeds up to three things together:

1. the OpenClaw plugin itself
2. workspace profile files at the root, when they exist in the source workspace
3. the minimal AITP kernel / adapter surface needed for `aitp` to run inside the target workspace

It intentionally does **not** copy live topic runtime state such as:

- `research/knowledge-hub/runtime/topics/**`
- `research/knowledge-hub/validation/topics/**`
- `research/knowledge-hub/feedback/topics/**`
- `research/knowledge-hub/consultation/topics/**`
- `research/knowledge-hub/intake/topics/**`
- `research/knowledge-hub/source-layer/topics/**`
- `research/knowledge-hub/data/topics/**`

The plugin is installed as a **workspace-local extension** under `.openclaw/extensions/aitp-openclaw-runtime/`.
It does **not** use `openclaw plugins install`, because that command currently targets the user-level OpenClaw state under `~/.openclaw/` rather than the target workspace.

## One command

From the source workspace:

```bash
python3 research/adapters/openclaw/scripts/install_openclaw_plugin.py \
  --target-root /path/to/other-openclaw-workspace
```

Windows-native equivalent from the repository root:

```cmd
scripts\install-openclaw-plugin-local.cmd --target-root D:\other-openclaw-workspace
```

If the target already has an older copy and you want to refresh it:

```bash
python3 research/adapters/openclaw/scripts/install_openclaw_plugin.py \
  --target-root /path/to/other-openclaw-workspace \
  --force
```

Windows-native:

```cmd
scripts\install-openclaw-plugin-local.cmd --target-root D:\other-openclaw-workspace --force
```

If the target should also inherit the local `mcporter` config from this machine:

```bash
python3 research/adapters/openclaw/scripts/install_openclaw_plugin.py \
  --target-root /path/to/other-openclaw-workspace \
  --copy-mcporter
```

Use `--copy-mcporter` only when the target is on the same host or the referenced local paths are still valid.

If you also want one OpenClaw profile to immediately point at that workspace and enable the plugin:

```bash
python3 research/adapters/openclaw/scripts/install_openclaw_plugin.py \
  --target-root /path/to/other-openclaw-workspace \
  --openclaw-profile aitp-prod
```

That profile-scoped step is optional because OpenClaw tracks workspace selection in the chosen profile config rather than in the workspace itself.

## Installing into the current workspace

If you are installing into the same workspace that already contains the source files, use:

```bash
python3 research/adapters/openclaw/scripts/install_openclaw_plugin.py \
  --target-root /home/bhj/OpenClaw-Workspaces/research
```

In that self-install case, the installer now skips mutable seed files by default so it does not reset live queues, inbox state, or the runtime topic index.

If you explicitly want to reset those mutable files in the same workspace, add:

```bash
--allow-self-seed
```

If you are installing into another workspace but still want to preserve its existing mutable state, add:

```bash
--skip-seeds
```

## What the plugin exposes

The installed OpenClaw plugin bundles:

- skill: `aitp-runtime`
- tools:
  - `aitp_doctor`
  - `aitp_state`
  - `aitp_audit`
  - `aitp_bootstrap`
  - `aitp_resume`
  - `aitp_loop`

These tools are thin wrappers around the installed `aitp` CLI and always execute against the target workspace's own `research/knowledge-hub`.

## Seed policy

When those files are present in the source workspace, the installer keeps the
research-brain profile and resets mutable state to clean seeds such as:

- `research-bot/state/briefing-status.json`
- `research-bot/state/inbox.jsonl`
- `research-bot/state/action-queue.jsonl`
- `research-bot/state/research-leads.jsonl`
- `research-bot/state/seen.json`
- `research/knowledge-hub/runtime/topic_index.jsonl`

This keeps the target reproducible and operator-readable without leaking the
current workspace's live queues or runs. If the public source repo does not
ship those legacy profile/state files, the installer skips them and still
installs the plugin plus the minimal AITP kernel surface.

## Minimal verification

After install, verify inside the target workspace:

```bash
openclaw plugins list --json
AITP_KERNEL_ROOT="$PWD/research/knowledge-hub" AITP_REPO_ROOT="$PWD" aitp doctor --json
```

On Windows-native, the simplest repo-root smoke test before entering the target
workspace is:

```cmd
scripts\aitp-local.cmd doctor --json
```

Then run a bounded loop check:

```bash
AITP_KERNEL_ROOT="$PWD/research/knowledge-hub" AITP_REPO_ROOT="$PWD" \
  aitp loop --updated-by openclaw-heartbeat --max-auto-steps 1 --json
```

If the workspace is fresh and has no topic yet, bootstrap one first:

```bash
AITP_KERNEL_ROOT="$PWD/research/knowledge-hub" AITP_REPO_ROOT="$PWD" \
  aitp bootstrap --topic "Test topic" --statement "Smoke test the plugin install." --json
```
