# Install OpenClaw Adapter

## Prerequisites

- Python 3.10+
- OpenClaw installed locally
- optional `mcporter` if you want structured MCP access

## Install the AITP runtime

From the repository root:

```bash
python -m pip install -e research/knowledge-hub
aitp doctor
```

## Install the OpenClaw wrapper

```bash
aitp install-agent --agent openclaw --scope user
```

This installs:

- the `aitp-runtime` OpenClaw skill
- an MCP setup note or MCP bridge registration, depending on environment

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
- refresh `aitp audit` at exit

## Reference plugin assets

Reference OpenClaw plugin assets live under:

- `research/adapters/openclaw/`

The CLI wrapper path above is currently the default supported standalone install
path. The richer workspace-seeding plugin assets are present as reference
material and can be promoted further later.

## Remove

See [`docs/UNINSTALL.md`](UNINSTALL.md).
