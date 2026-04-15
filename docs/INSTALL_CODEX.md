# Install Codex Adapter

Codex should use AITP through native skill discovery, not through wrappers.

## Prerequisites

- Codex CLI
- Python 3.10+
- Git only if you want the repo-backed contributor path

## Install the AITP runtime

For the public install path:

```bash
python -m pip install aitp-kernel
aitp --version
aitp doctor
```

The runtime requirements in `research/knowledge-hub/requirements.txt` now use
bounded version ranges rather than fully open-ended dependency specifiers.

If this machine previously used an older workspace-backed editable install,
first converge the local install:

- [`docs/MIGRATE_LOCAL_INSTALL.md`](MIGRATE_LOCAL_INSTALL.md)

## Preferred install

Install the user-scope Codex assets directly:

```bash
aitp install-agent --agent codex --scope user
```

Windows-native equivalent:

```cmd
scripts\aitp-local.cmd install-agent --agent codex --scope user
```

That keeps the public Codex path clone-free: install the package once, install
the skills, restart Codex, then let native skill discovery route the session.

What this means in practice:

- the user just talks naturally;
- `using-aitp` decides whether the request must become AITP state first;
- `aitp-runtime` is loaded only after routing succeeds;
- ordinary topic work should stay light unless something important forces a
  deeper runtime expansion;
- `aitp session-start "<task>"` becomes a fallback, not the normal front door.

## Repo-backed contributor path

If you want symlinked skills that track a local checkout while you edit the
repository itself, follow [`.codex/INSTALL.md`](../.codex/INSTALL.md).

## Workspace-local compatibility install

If you want workspace-local copied skills instead of a symlink:

```bash
aitp install-agent --agent codex --scope project --target-root /path/to/theory-workspace
```

User-scope copied-assets alternative:

```bash
aitp install-agent --agent codex --scope user
```

Windows-native example:

```cmd
scripts\aitp-local.cmd install-agent --agent codex --scope project --target-root D:\theory-workspace
```

Windows-native user-scope alternative:

```cmd
scripts\aitp-local.cmd install-agent --agent codex --scope user
```

This now writes only:

- `.agents/skills/using-aitp/`
- `.agents/skills/aitp-runtime/`
- `.agents/skills/aitp-runtime/AITP_MCP_SETUP.md`

It no longer writes `aitp-codex` or workspace wrapper binaries by default.

## Verify

Codex should now be able to:

- auto-trigger `using-aitp` for natural-language theory requests;
- treat `继续这个 topic` as current-topic continuation before asking for a slug;
- translate steering language into durable AITP steering updates;
- follow `runtime_protocol.generated.md` after routing succeeds;
- inspect active human-choice surfaces with `aitp interaction --topic-slug <topic_slug> --json`;
- resolve formal decision points with `aitp resolve-decision ...`;
- resolve operator checkpoints with `aitp resolve-checkpoint ...`.

Minimal sanity checks:

```bash
aitp doctor
ls -la ~/.agents/skills/aitp
```

Windows (PowerShell), inspect the skills root and confirm either the `aitp`
junction or copied `using-aitp` / `aitp-runtime` folders are present:

```powershell
Get-ChildItem "$env:USERPROFILE\.agents\skills"
```

For the structured runtime view, use:

```bash
aitp doctor --json
```

That report should show:

- Codex as the current baseline runtime
- `runtime_support_matrix.runtimes.codex.status` as `ready`
- `runtime_convergence.front_door_runtimes_converged` when the whole
  Codex/Claude Code/OpenCode front door is aligned
- `runtime_support_matrix.runtimes.codex.remediation` for the exact Codex
  repair command if the row is not `ready`
- `control_plane_contracts` and `control_plane_surfaces` for the unified
  architecture docs plus the runtime audit/status commands for live topics

If the Codex row is not `ready`, run the command in
`runtime_support_matrix.runtimes.codex.remediation.command`, then rerun
`runtime_support_matrix.runtimes.codex.remediation.followup_command`.

Useful follow-up commands once a topic exists:

```bash
aitp capability-audit --topic-slug <topic_slug>
aitp paired-backend-audit --topic-slug <topic_slug>
aitp h-plane-audit --topic-slug <topic_slug>
```

After the Codex row is `ready`, continue with the shared first-run guide:

- [`docs/QUICKSTART.md`](QUICKSTART.md)

## Manual fallback

If bootstrap does not fire, use:

```bash
aitp session-start "<task>"
```

## Remove

See [`docs/UNINSTALL.md`](UNINSTALL.md).
