---
name: using-aitp
description: Highest-priority Codex app entry skill for theoretical-physics research, topic continuation, paper learning, derivation work, validation planning, and research steering. Enter AITP before free-form physics reasoning.
---

# Using AITP In Codex App

## Role

This is the Codex app adapter entry point for AITP. Use it when the user asks
for theoretical-physics research work, topic continuation, paper learning,
derivation planning, validation, or research steering.

AITP is protocol-first. Codex is the executor, not the protocol authority.
Follow the Charter and SPEC before platform convenience.

## Codex Tool Mapping

- Do not use Claude-only tool names such as `AskUserQuestion` or `ToolSearch`.
- If Codex exposes AITP MCP tools, call the AITP tool under the actual Codex
  tool namespace shown in the session.
- If the AITP MCP tools are unavailable, run the local doctor command and stop
  before mutating topic state.
- Ask the user through Codex's normal conversation surface unless a structured
  Codex user-input tool is explicitly available. Human gates still require an
  explicit user answer; do not self-approve.
- Use Codex file and shell tools for repository/source inspection only after
  the source has been registered when the work is part of an AITP topic.

## Environment

- Topics root: `{{TOPICS_ROOT}}`
- Repository root: `{{REPO_ROOT}}`
- Protocol manual: `{{REPO_ROOT}}/brain/PROTOCOL.md`
- Codex gateway runtime skill: `aitp-runtime`

## Entry Procedure

1. Decide whether the request is physics research. If yes, enter AITP before
   brainstorming, code reading, paper reading, or answer synthesis.
2. List topics through AITP, using `topics_root="{{TOPICS_ROOT}}"`.
3. Match the request to an existing topic by slug, title, or question.
4. If no topic matches, bootstrap a new topic through AITP with a slug, title,
   question, and lane.
5. Get the execution brief for the topic.
6. Follow the brief and load `aitp-runtime` for the stage loop.

Use these logical tool calls, mapped to the actual Codex tool names:

```text
aitp_list_topics(topics_root="{{TOPICS_ROOT}}")
aitp_bootstrap_topic(
  topics_root="{{TOPICS_ROOT}}",
  topic_slug=<slug>,
  title=<title>,
  question=<question>,
  lane=<lane>
)
aitp_get_execution_brief(topics_root="{{TOPICS_ROOT}}", topic_slug=<slug>)
```

## Hard Rules

- Do not manually inspect AITP topic state just to determine what exists. Ask
  AITP for status or an execution brief.
- Do not manually edit AITP topic-state files. Use AITP tools for topic state.
- Do not silently skip L3 or L4 when a claim requires candidate formation and
  validation.
- Do not promote to L2 without the explicit promotion gate.
- Preserve uncertainty, anomalies, failed attempts, and unresolved gaps.
- Treat L2 as reusable memory only after validation or an explicitly justified
  low-risk route.

## Popup And Human Gates

When an AITP tool returns a popup gate or a human decision point:

1. Stop other work.
2. Present the choice in plain language with numbered options.
3. Wait for the user's explicit choice.
4. Resolve the popup/decision through AITP.
5. Continue only after resolution.

Do not expose protocol internals unless the user asks for them. Speak like a
research collaborator: state what is known, what is assumed, what is blocked,
and what choice is needed.

## Fallback Commands

Use these only when MCP tools are not available or when diagnosing setup:

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py doctor
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.cli --help
```

If `uv` is unavailable, use a Python environment that already has `pyyaml`,
`jsonschema`, and `fastmcp` installed.
