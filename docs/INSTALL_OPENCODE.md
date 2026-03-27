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

## Preferred install

Follow [`.opencode/INSTALL.md`](../.opencode/INSTALL.md).

The public OpenCode path is:

1. add `aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git` to the `plugin` array in `opencode.json`;
2. restart OpenCode;
3. let the plugin inject `using-aitp` and register the AITP `skills/` path.

That is the recommended path because it matches the intended AITP UX:

- no `/aitp` command ritual for normal use;
- natural-language requests route through `using-aitp` first;
- AITP state becomes durable before substantive theory work starts.

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
