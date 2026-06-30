---
name: using-aitp
description: Enter the local AITP v5 research protocol from Codex for theoretical-physics work, topic continuation, prior progress checks, paper reading, derivations, validation, and trust-controlled research memory.
---

# Using AITP v5 In Codex

Use this skill whenever the user asks for theoretical-physics research work, a project-linked physics explanation, prior topic status, topic continuation, paper learning, derivation work, validation planning, or research steering.

AITP is protocol-first. Codex is the executor; the AITP typed records under the configured topics root are the authority.

## First-Run Setup

Before using research tools in a new installation, check whether the AITP MCP server is in setup mode:

```text
aitp_config_status()
```

If that tool exists and reports `configured=false`, do not proceed with research calls yet. Ask the user for:

1. The local `AITP-Research-Protocol` checkout path.
2. The topics root where AITP should store records.

Offer the default topics root `~/.aitp/topics` if the user does not already have a project store. Then call:

```text
aitp_configure(repo_root=<repo path>, topics_root=<topics path or empty>)
```

After successful configuration, tell the user to restart the MCP server or open a new Codex thread so the compact Codex AITP surface loads. If the user does not have a checkout, offer to clone `https://github.com/bhjia-phys/AITP-Research-Protocol.git` into a user-chosen directory before calling `aitp_configure`.

## Local Wiring

- Repository root: resolved by the plugin launcher from `AITP_REPO_ROOT`, `~/.aitp/install-record.json`, or `vendor/AITP-Research-Protocol`.
- Topics root and v5 base: resolved by the launcher from `AITP_TOPICS_ROOT`, `~/.aitp/install-record.json`, or the default `~/.aitp/topics`.
- Canonical v5 store: `<topics-root>/.aitp/`.
- MCP entrypoint: `<repo-root>/brain/v5/native_mcp.py`.
- Codex plugin MCP surface: `AITP_MCP_SURFACE=codex` by default. Use `AITP_MCP_SURFACE=full` only for kernel development or maintenance.
- Fallback CLI: `uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.v5.cli`

The workspace-root `.aitp/` directory is runtime/local state; do not treat it as the v5 topic store.

When the exact topics root is unknown, pass `base=""` to AITP v5 tools. The MCP server resolves the empty base to `AITP_TOPICS_ROOT`.

## Entry Rules

1. If the request is generic textbook knowledge and does not touch a project topic, answer normally.
2. If only setup tools are exposed, complete first-run setup before any AITP research operation.
3. If the request touches an existing topic, claim, source, route, artifact, or gap, restore AITP context before answering.
4. First call `aitp_v5_codex_tool_catalog(profile="entry")` if the available surface is unclear.
5. For known sessions, call `aitp_v5_codex_enter(base="", session_id=<session-id>, request_summary=<user request>)` first. Expand through `aitp_v5_codex_expand`, not by dumping the full graph.
6. If only a topic slug is known, call `aitp_v5_codex_enter(base="", topics=[<topic>], request_summary=<user request>)`. Use a `recovery_ready` row's session and claim before creating or migrating anything.
7. If no usable v5 session exists, use v5 migration or topic/claim/session creation tools through a full-kernel maintenance surface only after user confirmation. Do not write progress into old L0/L1/L3/L4 files.
8. Load `aitp-runtime` before active continuation, derivation, validation, numerical work, final synthesis, trust updates, L2 promotion, literature registration, writing, or closeout.

## Intensity Policy

- Status or prior-progress inquiry: read-only recovery, context pack, and concise summary. Expand to brief/relation map only when the answer depends on full boundary detail. Do not write unless the user asks for a durable handoff or resolves a human checkpoint.
- Project-linked old-knowledge Q&A: restore context first; write only durable corrections, sources, gaps, route changes, or claim-boundary changes.
- Light exploratory discussion: read topic context when known; write only after a durable route, question, source, artifact, result, or gap emerges.
- Continuation, derivation, source reading, code/numerical work, validation, contradiction, final synthesis, trust update, or L2 promotion: follow typed gates through AITP v5 tools.

When unsure, choose the read-only path first.

## Hard Rules

- Do not manually edit AITP topic-state files.
- Do not treat legacy `stage`, `gate_status`, or L0-L4 files as v5 truth.
- Do not enable `AITP_LEGACY_ENABLE_WRITES=1` during normal research.
- Do not create or bind a session merely to restore an existing topic if recovery already finds a usable session.
- Do not turn runtime/setup failures into algorithm or physics evidence.
- Do not treat an AITP context pack as evidence, validation, L2 memory, or claim-trust support.
- Do not promote to L2 without v5 trust preflight, validation coverage, and the explicit human gate.
- Preserve uncertainty, failed attempts, anomalies, and open gaps.

## Human Gates

When an AITP tool returns a human decision point:

1. Stop other work.
2. Present the choices plainly.
3. Wait for the user's explicit answer.
4. Resolve the decision through AITP.
5. Continue only after resolution.

## Fallback Diagnostics

Use these only when MCP tools are unavailable or setup is suspect:

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py doctor
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.v5.cli --base "$env:AITP_TOPICS_ROOT" status context-pack <session-id>
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.v5.cli --base "$env:AITP_TOPICS_ROOT" brief <session-id>
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.v5.cli --base "$env:AITP_TOPICS_ROOT" relation-map <session-id>
```
