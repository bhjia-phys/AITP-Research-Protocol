---
name: aitp-runtime
description: Enter the local AITP kernel from OpenClaw through the bundled plugin tools or the installed `aitp` CLI so the run stays auditable, resumable, and conformance-checked.
---

# AITP Runtime For OpenClaw

Use this skill when the task belongs inside AITP rather than a free-form note workflow.

## Preferred entry

If the OpenClaw plugin is loaded, prefer the typed tools:

- `aitp_doctor`
- `aitp_state`
- `aitp_bootstrap`
- `aitp_resume`
- `aitp_loop`
- `aitp_audit`

## CLI fallback

If the plugin tools are unavailable, use the installed CLI from the workspace root:

```bash
AITP_KERNEL_ROOT="$PWD/research/knowledge-hub" AITP_REPO_ROOT="$PWD" \
  aitp loop --topic-slug <topic_slug> --human-request "<task>"
```

For a new topic:

```bash
AITP_KERNEL_ROOT="$PWD/research/knowledge-hub" AITP_REPO_ROOT="$PWD" \
  aitp bootstrap --topic "<topic>" --statement "<statement>"
```

## Before finishing

```bash
AITP_KERNEL_ROOT="$PWD/research/knowledge-hub" AITP_REPO_ROOT="$PWD" \
  aitp audit --topic-slug <topic_slug> --phase exit
```

## Trust gates

- Reusable operations require `aitp operation-init ...` and `aitp trust-audit ...`
- Numerical novelty requires `aitp baseline ...`
- Theory-method understanding requires `aitp atomize ...`

## Workspace assumptions

- Workspace root contains `AGENTS.md` and `research/knowledge-hub/`
- The OpenClaw plugin profile installer has seeded the current workspace
- Heartbeat should prefer `AITP_KERNEL_ROOT="$PWD/research/knowledge-hub" AITP_REPO_ROOT="$PWD" aitp loop --updated-by openclaw-heartbeat --max-auto-steps 1 --json`
