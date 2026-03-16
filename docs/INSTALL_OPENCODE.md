# Install OpenCode Adapter

## Prerequisites

- Python 3.10+
- OpenCode installed locally

## Install the AITP runtime

From the repository root:

```bash
python -m pip install -e research/knowledge-hub
aitp doctor
```

## Install the OpenCode wrapper

```bash
aitp install-agent --agent opencode --scope user
```

This installs:

- the AITP command harness
- `/aitp`, `/aitp-resume`, `/aitp-loop`, and `/aitp-audit` command files
- an `mcp.aitp` local server entry when config mutation is allowed

## Recommended entrypoint

Use the loop-oriented path:

```bash
aitp loop --topic-slug <topic_slug> --human-request "<task>"
```

The installed OpenCode command bundle is designed to route existing topics
through `aitp loop` by default rather than through free-form browsing.

## Verify

OpenCode should now be able to:

- enter the AITP runtime through the installed commands
- read `runtime_protocol.generated.md` before doing deeper work
- refresh conformance on exit

## Manual fallback

If you want command files only, the reference assets still live at:

- `adapters/opencode/AITP_COMMAND_HARNESS.md`
- `adapters/opencode/commands/`

## Remove

See [`docs/UNINSTALL.md`](UNINSTALL.md).
