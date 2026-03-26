# Install Codex Adapter

## Prerequisites

- Python 3.10+
- Codex CLI installed locally

## Install the AITP runtime

From the repository root:

```bash
python -m pip install -e research/knowledge-hub
aitp doctor
```

On Windows-native, you can also verify the repo-local launchers directly:

```cmd
scripts\aitp-local.cmd doctor
scripts\aitp-codex-local.cmd --help
```

## Install the Codex wrapper

```bash
aitp install-agent --agent codex --scope user
```

This installs:

- the `using-aitp` skill as the conversation-level AITP gatekeeper
- the `aitp-runtime` skill into your active Codex skill roots
- the `aitp` MCP registration when supported

If you want a separate theory workspace to run bare `codex` in an AITP-first
way, install the project skill into that workspace root:

```bash
aitp install-agent --agent codex --scope project --target-root /path/to/theory-workspace
```

That writes:

- `.agents/skills/using-aitp/`
- `.agents/skills/aitp-runtime/`
- workspace-local wrappers under `.agents/bin/`

- `aitp`
- `aitp.cmd`
- `aitp-codex`
- `aitp-codex.cmd`
- `aitp-mcp`
- `aitp-mcp.cmd`

Windows-native example:

```cmd
scripts\aitp-local.cmd install-agent --agent codex --scope project --target-root D:\theory-workspace
```

The generated `.agents\bin\aitp.cmd` and `.agents\bin\aitp-codex.cmd` wrappers
pin `AITP_KERNEL_ROOT` to the cloned repository and do not depend on WSL.

## Recommended entrypoints

For normal topic work:

```bash
aitp loop --topic "<topic>" --human-request "<task>"
```

For Codex-driven implementation or execution:

```bash
aitp-codex --topic-slug <topic_slug> "<task>"
```

If the operator changes direction mid-topic, persist that steering update
before continuing:

```bash
aitp steer-topic --topic-slug <topic_slug> --innovation-direction "<new direction>" --decision continue
aitp-codex --topic-slug <topic_slug> "Continue the topic under updated direction: <new direction>"
```

Codex also recognizes the natural-language shortcut:

```text
continue this topic, direction changed to <new direction>
继续这个 topic，方向改成 <new direction>
```

and translates it into the equivalent AITP steering update plus resume flow.

## Verify

Codex should now be able to:

- use `using-aitp` to decide whether the task must enter AITP before any substantial response
- enter topic work through the AITP runtime surface
- read `runtime_protocol.generated.md`
- read `promotion_gate.md` when a candidate is approaching Layer 2
- treat missing conformance as a hard failure for AITP work
- use `aitp-codex` as the stronger wrapper path for coding tasks
- require `innovation_direction.md` and the paired `control_note` to be updated when the human changes novelty direction or scope
- require `aitp request-promotion ...` plus human approval before `aitp promote ...`

## Manual fallback

If you do not want config mutation, the reference skill still lives at:

- `adapters/codex/SKILL.md`

## Remove

See [`docs/UNINSTALL.md`](UNINSTALL.md).
