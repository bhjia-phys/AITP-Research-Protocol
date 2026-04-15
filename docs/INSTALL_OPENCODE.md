# Install OpenCode Adapter

OpenCode should use AITP through a plugin, not through `/aitp` command bundles.

## Prerequisites

- OpenCode installed locally
- Python 3.10+

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

Follow [`.opencode/INSTALL.md`](../.opencode/INSTALL.md).

The public OpenCode path is:

1. add `aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git` to the `plugin` array in `opencode.json`;
2. restart OpenCode;
3. let the plugin inject `using-aitp` and register the AITP `skills/` path.

On Windows-native, the default user config path is typically:

- `%USERPROFILE%\.config\opencode\opencode.json`

That is the recommended path because it matches the intended AITP UX:

- no `/aitp` command ritual for normal use;
- natural-language requests route through `using-aitp` first;
- ordinary topic work should remain in a light runtime profile unless a real
  escalation trigger fires;
- AITP state becomes durable before substantive theory work starts.

This is the preferred OpenCode path today: public kernel install from PyPI,
plugin activation through `opencode.json`, no editable install required.

## Workspace-local compatibility install

If you want local copied assets in a workspace or user config root:

```bash
aitp install-agent --agent opencode --scope project --target-root /path/to/theory-workspace
```

User-scope copied-assets alternative:

```bash
aitp install-agent --agent opencode --scope user
```

Windows-native example:

```cmd
scripts\aitp-local.cmd install-agent --agent opencode --scope project --target-root D:\theory-workspace
```

Windows-native user-scope alternative:

```cmd
scripts\aitp-local.cmd install-agent --agent opencode --scope user
```

This now writes:

- `.opencode/skills/using-aitp/`
- `.opencode/skills/aitp-runtime/`
- `.opencode/skills/aitp-runtime/AITP_MCP_SETUP.md`
- `.opencode/plugins/aitp.js`
- optional MCP config

It no longer writes `AITP_COMMAND_HARNESS.md` or `/aitp*` command files by default.

## Verify

OpenCode should now:

- inject `using-aitp` through `experimental.chat.system.transform`;
- register the AITP skills path through the plugin `config` hook;
- route current-topic continuation and steering through AITP before substantive work;
- expose interaction inspection through `aitp interaction --topic-slug <topic_slug> --json`;
- expose formal decision resolution through `aitp resolve-decision ...`;
- expose operator-checkpoint resolution through `aitp resolve-checkpoint ...`.

Use `aitp doctor --json` to verify whether OpenCode is ready through the
preferred `opencode.json` plugin entry or only through a partial/stale
workspace compatibility surface.
The same JSON report should show:

- `runtime_support_matrix.runtimes.opencode.status` as `ready`
- `runtime_support_matrix.runtimes.opencode.remediation` when the OpenCode row
  needs repair or preferred-plugin convergence is only recommended
- `runtime_support_matrix.deep_execution_parity.runtimes.opencode.status`
  as `probe_available` once the bounded OpenCode runtime probe is present
- `runtime_convergence.front_door_runtimes_converged` when the full front-door
  adoption surface is aligned
- `control_plane_contracts` and `control_plane_surfaces` so OpenCode-side
  operators can find the unified architecture docs plus the runtime
  audit/status commands that inspect live topics

If the OpenCode row is not `ready`, or if its remediation status is
`recommended`, run the command in
`runtime_support_matrix.runtimes.opencode.remediation.command`, then rerun
`runtime_support_matrix.runtimes.opencode.remediation.followup_command`.

To run the bounded deep-execution probe explicitly:

```bash
python research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py --runtime opencode --json
```

That report should stay limitation-heavy: it proves the plugin hook receipts
plus bounded AITP runtime artifacts, but it does not yet claim full live
OpenCode parity with the Codex baseline.

Useful follow-up commands once a topic exists:

```bash
aitp capability-audit --topic-slug <topic_slug>
aitp paired-backend-audit --topic-slug <topic_slug>
aitp h-plane-audit --topic-slug <topic_slug>
```

After the OpenCode row is `ready`, continue with the shared first-run guide:

- [`docs/QUICKSTART.md`](QUICKSTART.md)

If you are migrating from an older AITP setup, remove legacy `/aitp*` command
bundles from your OpenCode workspace so the plugin-first path is the only
default surface.

## Manual fallback

If bootstrap is unavailable:

```bash
aitp session-start "<task>"
```

## Remove

See [`docs/UNINSTALL.md`](UNINSTALL.md).
