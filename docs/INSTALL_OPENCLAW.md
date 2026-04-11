# Install OpenClaw Adapter

## Prerequisites

- Python 3.10+
- OpenClaw installed locally
- optional `mcporter` if you want structured MCP access

## Install the AITP runtime

For the public install path:

```bash
python -m pip install aitp-kernel
aitp --version
aitp doctor
```

On Windows-native, if you are working from a local checkout, you can also
verify the repo-local launcher directly:

```cmd
scripts\aitp-local.cmd doctor
```

## Install the OpenClaw wrapper

```bash
aitp install-agent --agent openclaw --scope user
```

This installs:

- the `aitp-runtime` OpenClaw skill
- an MCP setup note or MCP bridge registration, depending on environment

If you want a workspace-local OpenClaw skill surface, install it into the target
workspace root:

```bash
aitp install-agent --agent openclaw --scope project --target-root /path/to/openclaw-workspace
```

That writes:

- `skills/aitp-runtime/SKILL.md`
- `skills/aitp-runtime/AITP_MCP_SETUP.md`

Windows-native example:

```cmd
scripts\aitp-local.cmd install-agent --agent openclaw --scope project --target-root D:\openclaw-workspace
```

For the richer workspace-local plugin seed path, use the repo-local installer:

```cmd
scripts\install-openclaw-plugin-local.cmd --target-root D:\openclaw-workspace --json
```

## Recommended entrypoint

OpenClaw should start substantial AITP work through:

```bash
aitp loop --topic-slug <topic_slug> --human-request "<task>"
```

Use `aitp bootstrap ...` only to create a new topic shell, then return to the
loop.

## Verify

OpenClaw should now be able to:

- start topic work through `aitp bootstrap`, `aitp resume`, or preferably `aitp loop`
- read the runtime protocol bundle before taking actions
- surface `promotion_gate.json` / `promotion_gate.md` for human approval on Feishu or other operator channels
- refresh `aitp audit` at exit
- request approval before any `L2` writeback and only then run `aitp promote ...`

## Reference plugin assets

Reference OpenClaw plugin assets live under:

- `research/adapters/openclaw/`

The CLI install path above is the lightest supported route. The plugin installer
is the richer workspace-seeding path when you want `.openclaw/extensions/`,
seeded profile files, and the adapter-owned workspace bootstrap.

## Remove

See [`docs/UNINSTALL.md`](UNINSTALL.md).
