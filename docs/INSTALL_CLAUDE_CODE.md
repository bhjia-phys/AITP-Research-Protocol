# Install Claude Code Adapter

Claude Code should use AITP through SessionStart bootstrap plus a native AITP
MCP server, not through `/aitp`-style command bundles.

## Prerequisites

- Claude Code installed locally
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

Install the user-scope SessionStart assets:

```bash
aitp install-agent --agent claude-code --scope user
```

Windows-native equivalent:

```cmd
scripts\aitp-local.cmd install-agent --agent claude-code --scope user
```

The intended outer behavior matches Superpowers:

- SessionStart injects `using-aitp`;
- Claude Code can call native `mcp__aitp__...` tools for structured AITP actions;
- natural-language theory requests enter AITP before substantive work;
- current-topic continuation and steering stay natural-language first.
- ordinary topic work should remain in a light runtime profile unless a real
  escalation trigger fires.

This is the preferred path because Claude Code should not need a custom
`/aitp` command vocabulary for normal AITP use. The session should already be
inside the right routing discipline before substantial work begins.
The same install now also writes the canonical Claude MCP registration so AITP
runtime actions are available as native Claude tools instead of shell-only
fallbacks.

On Windows-native, the generated hook wrapper now prefers a Python
`session-start.py` sidecar before any bash fallback, so Git Bash is no longer
the expected default dependency for SessionStart bootstrap.

## Workspace-local compatibility install

If you want local copied assets inside a project workspace instead of the user
profile:

```bash
aitp install-agent --agent claude-code --scope project --target-root /path/to/theory-workspace
```

Windows-native example:

```cmd
scripts\aitp-local.cmd install-agent --agent claude-code --scope project --target-root D:\theory-workspace
```

Windows-native user-scope alternative:

```cmd
scripts\aitp-local.cmd install-agent --agent claude-code --scope user
```

This now writes:

- `.claude.json`
- `.claude/skills/using-aitp/`
- `.claude/skills/aitp-runtime/`
- `.claude/skills/aitp-runtime/AITP_MCP_SETUP.md`
- `.mcp.json`
- `.claude/hooks/session-start`
- `.claude/hooks/session-start.py`
- `.claude/hooks/run-hook.cmd`
- `.claude/hooks/hooks.json`
- `.claude/settings.json`

It no longer writes `.claude/commands/aitp*.md` by default.

## Verify

Claude Code should now:

- inject `using-aitp` at SessionStart;
- expose an `aitp` MCP server through Claude Code's native tool layer;
- route substantial theory work through AITP before response;
- follow `runtime_protocol.generated.md` after routing succeeds;
- inspect active human-choice surfaces with `aitp interaction --topic-slug <topic_slug> --json` or the native AITP MCP surface;
- resolve formal decision points with `aitp resolve-decision ...`;
- resolve operator checkpoints with `aitp resolve-checkpoint ...`.

Use `aitp doctor --json` to verify not just file presence but also whether the
Claude bootstrap assets still match the canonical hook files and whether
`.claude/settings.json` still wires the expected SessionStart command.
The same JSON report should show:

- `runtime_support_matrix.runtimes.claude_code.status` as `ready`
- `runtime_support_matrix.runtimes.claude_code.remediation` when the Claude
  row needs repair
- `claude_mcp_surface.user_mcp_server_matches_canonical` when the user-scope
  Claude MCP registration is current
- `claude_mcp_surface.project_mcp_server_matches_canonical` when the
  workspace-local `.mcp.json` compatibility surface is current
- `runtime_support_matrix.deep_execution_parity.runtimes.claude_code.status`
  as `probe_available` once the bounded Claude runtime probe is present
- `runtime_convergence.front_door_runtimes_converged` when the full front-door
  adoption surface is aligned
- `control_plane_contracts` and `control_plane_surfaces` so Claude-side
  operators can find the unified architecture docs plus the runtime
  audit/status commands that inspect live topics

If the Claude row is not `ready`, run the command in
`runtime_support_matrix.runtimes.claude_code.remediation.command`, then rerun
`runtime_support_matrix.runtimes.claude_code.remediation.followup_command`.
You can also inspect the native MCP registration directly with:

```bash
claude mcp list
```

To run the bounded deep-execution probe explicitly:

```bash
python research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py --runtime claude_code --json
```

That report should stay limitation-heavy: it proves the SessionStart bootstrap
receipt, native MCP availability, plus bounded AITP runtime artifacts, but it
does not yet claim full
live-Claude parity with the Codex baseline.

Useful follow-up commands once a topic exists:

```bash
aitp capability-audit --topic-slug <topic_slug>
aitp paired-backend-audit --topic-slug <topic_slug>
aitp h-plane-audit --topic-slug <topic_slug>
```

After the Claude Code row is `ready`, continue with the shared first-run guide:

- [`docs/QUICKSTART.md`](QUICKSTART.md)

If you are migrating from an older setup, remove any legacy `.claude/commands/aitp*.md`
bundle so SessionStart bootstrap is the only default entry.

## Manual fallback

If bootstrap is unavailable:

```bash
aitp session-start "<task>"
```

## Remove

See [`docs/UNINSTALL.md`](UNINSTALL.md).
