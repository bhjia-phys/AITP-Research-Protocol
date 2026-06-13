---
name: using-aitp
description: Highest-priority Codex app entry skill for theoretical-physics research, topic continuation, paper learning, derivation work, validation planning, and research steering. Enter AITP before free-form physics reasoning.
---

# Using AITP v5 In Codex App

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
- Current project installs expose v5 typed tools (`aitp_v5_*`) through the v5
  native MCP entrypoint. Legacy-friendly aliases (`aitp_list_topics`,
  `aitp_get_execution_brief`, `aitp_bootstrap_topic`) may exist only for
  discovery/bootstrap compatibility; do not use a legacy stage brief as the
  execution contract for new work.
- The claim relation map (`aitp_v5_get_claim_relation_map`, or
  `aitp-v5 relation-map <session-id>` as CLI fallback) is a read-only recovery
  surface. Use it to separate support, limitations, non-testing failures,
  blockers, and next valid actions. It cannot update claim trust.
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
- v5 workspace base: `{{TOPICS_ROOT}}`
- Canonical v5 store: `{{TOPICS_ROOT}}/.aitp/`; workspace-root `.aitp/`
  is not the v5 topic store.
- Protocol manual: `{{REPO_ROOT}}/brain/PROTOCOL.md`
- Codex gateway runtime skill: `aitp-runtime`

## Entry Procedure

1. Decide whether the request is physics research. If yes, enter AITP before
   brainstorming, code reading, paper reading, or answer synthesis.
2. If a v5 session id is already known, call
   `aitp_v5_get_execution_brief(base="{{TOPICS_ROOT}}", session_id=<session-id>)`.
   Then call `aitp_v5_get_claim_relation_map` for the same session before
   interpreting failures or deciding the next scientific action.
3. If only a legacy topic slug is known, use legacy discovery only to find the
   topic, then migrate/bind a v5 session before doing research:
   `aitp_v5_migrate_curated_legacy_topic_to_v5` for known curated topics, or
   `aitp_v5_migrate_legacy_topic_to_v5` for a generic preservation pass.
4. If no topic matches, create a v5 topic, create an initial claim, bind a
   session, and then get the v5 execution brief.
5. Follow the v5 brief and load `aitp-runtime` for the typed-record loop.

Use these logical tool calls, mapped to the actual Codex tool names:

```text
aitp_v5_get_execution_brief(base="{{TOPICS_ROOT}}", session_id=<session-id>)
aitp_v5_get_claim_relation_map(base="{{TOPICS_ROOT}}", session_id=<session-id>)
aitp_v5_migrate_curated_legacy_topic_to_v5(
  base="{{TOPICS_ROOT}}",
  topic_dir="{{TOPICS_ROOT}}/<legacy-topic-slug>"
)
aitp_v5_create_topic(base="{{TOPICS_ROOT}}", topic_id=<slug>, context_id=<context>, title=<title>)
aitp_v5_create_claim(base="{{TOPICS_ROOT}}", topic_id=<slug>, statement=<claim>, evidence_profile=<profile>, confidence_state="hypothesis", active_uncertainty=<uncertainty>)
aitp_v5_bind_session(base="{{TOPICS_ROOT}}", session_id=<session-id>, topic_id=<slug>, context_id=<context>, active_claim=<claim-id>)
```

## Hard Rules

- Do not manually inspect AITP topic state just to determine what exists. Ask
  AITP for a v5 session brief or use legacy discovery only for migration.
- Do not manually edit AITP topic-state files. Use AITP tools for topic state.
- Do not treat old `stage`, `gate_status`, or `L0/L1/L3/L4` fields as v5 truth.
- Do not turn application/runtime failures into algorithm evidence. Use the
  claim relation map's `cannot_say`, `not_tested_by`, blockers, and next valid
  actions before summarizing a restored session.
- Do not promote to L2 without v5 trust preflight, validation coverage, and the
  explicit promotion/human gate.
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

Use these only when MCP tools are not available, when diagnosing setup, or when
the MCP tool surface shown in Codex does not match the protocol text:

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py doctor
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.v5.cli --base "{{TOPICS_ROOT}}" brief <session-id>
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.v5.cli --base "{{TOPICS_ROOT}}" relation-map <session-id>
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.v5.cli --base "{{TOPICS_ROOT}}" workspace inventory --workspace-root "{{TARGET_ROOT}}"
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.v5.cli --base "{{TOPICS_ROOT}}" workspace migration-plan --workspace-root "{{TARGET_ROOT}}"
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.v5.cli --base "{{TOPICS_ROOT}}" workspace old-store-manifest --workspace-root "{{TARGET_ROOT}}"
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.v5.cli --base "{{TOPICS_ROOT}}" legacy curated-known-topics
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.cli state show <topic>
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.cli gate check <topic>
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.cli --help
```

If `uv` is unavailable, use a Python environment that already has `pyyaml`,
`jsonschema`, and `fastmcp` installed.
