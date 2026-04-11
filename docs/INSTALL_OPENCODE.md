# Install OpenCode Adapter

OpenCode should use AITP through a plugin, not through `/aitp` command bundles.

## Prerequisites

- OpenCode installed locally
- Python 3.10+

## Install the AITP runtime

From the repository root:

```bash
python -m pip install -e research/knowledge-hub
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

That is the recommended path because it matches the intended AITP UX:

- no `/aitp` command ritual for normal use;
- natural-language requests route through `using-aitp` first;
- ordinary topic work should remain in a light runtime profile unless a real
  escalation trigger fires;
- AITP state becomes durable before substantive theory work starts.

This is already plugin-first, but still repo-sourced rather than marketplace
one-click.

## Compatibility install

If you want local copied assets in a workspace or user config root:

```bash
aitp install-agent --agent opencode --scope project --target-root /path/to/theory-workspace
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
- route current-topic continuation and steering through AITP before substantive work.

Use `aitp doctor --json` to verify whether OpenCode is ready through the
preferred `opencode.json` plugin entry or only through a partial/stale
workspace compatibility surface.
The same JSON report now also exposes `control_plane_contracts` and
`control_plane_surfaces` so OpenCode-side operators can find the unified
architecture docs plus the runtime audit/status commands that inspect live
topics.

Useful follow-up commands once a topic exists:

```bash
aitp capability-audit --topic-slug <topic_slug>
aitp paired-backend-audit --topic-slug <topic_slug>
aitp h-plane-audit --topic-slug <topic_slug>
```

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
