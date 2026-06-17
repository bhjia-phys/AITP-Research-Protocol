---
name: using-aitp
description: Highest-priority Codex app entry skill for theoretical-physics work: active research, exploratory physics discussion, old-knowledge Q&A tied to project topics, prior topic progress/status inquiries, topic continuation, paper learning, derivation work, validation planning, and research steering. Classify request intensity before deciding read-only or write-capable flow.
---

# Using AITP v5 In Codex App

## Role

This is the Codex app adapter entry point for AITP. Use it when the user asks
for theoretical-physics research work, exploratory physics discussion,
old-knowledge Q&A that touches a project topic, prior topic progress/status,
topic continuation, paper learning, derivation planning, validation, or
research steering.

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

1. Decide whether the request is physics research or project-linked physics
   context. If yes, enter AITP before brainstorming, code reading, paper
   reading, or answer synthesis.
2. Classify request intensity:
   - Status or prior-progress inquiry: read-only recovery, brief, and relation
     map. Do not write unless the user asks for a handoff or a returned human
     checkpoint must be resolved.
   - Old-knowledge/textbook Q&A: answer normally if generic. If tied to a known
     topic or claim, restore brief and relation map first; write only durable
     source, gap, route, or correction records.
   - Light exploratory discussion: read topic context when known, but only run
     recording navigation if a durable route, question, source, artifact,
     result, or gap emerges.
   - Continuation, derivation, source reading, code/numerical work, validation,
     contradiction, final synthesis, trust update, or L2 promotion: restore the
     v5 session, load `aitp-runtime`, and follow typed gates.

### Intent Matrix

Use the lightest AITP path that preserves truth.

| User intent | AITP read depth | Recording default | Escalate to write when |
|---|---|---|---|
| Generic textbook or old-knowledge Q&A | None, unless the answer names an existing topic or claim | No write | The answer corrects project memory, finds a durable gap, or introduces a reusable source |
| Project-linked old-knowledge Q&A | Recovery audit, brief, relation map | No write | The answer changes a claim boundary, source role, route, or proof/validation obligation |
| Prior progress/status inquiry | Recovery audit, brief, relation map, summaries | No write | User asks for a handoff/status artifact or resolves a human checkpoint |
| Light exploratory discussion | Topic context if known; classifier only after a durable moment appears | No write | User accepts a route/question, identifies a source, or exposes a reusable gap |
| Topic continuation or derivation | Brief, relation map, lightweight recording navigation; process graph only when needed | Write at durable moments | Source, artifact, result, proof obligation, route decision, or validation state changes |
| Code/numerical/literature execution | Brief, relation map, source/code context, recording navigation | Write provenance and outputs | Tool run completes, artifact appears, validation passes/fails, or anomaly is observed |
| Final claim/trust/L2/memory action | Brief, relation map, trust/promotion preflight | Human-gated write only | Explicit v5 gate and user decision allow it |

When unsure between two rows, choose the read-only row first and let the
recording classifier decide whether a durable moment exists. Do not create a
new topic, claim, session, or binding merely because a conversation is
interesting.

3. If the host exposes Hakimi/Kimi `ResearchAction`, open a WorkFrame before
   substantive AITP reads:
   `ResearchAction(open_work_frame, topic=<topic>, goal=<restore-or-research-goal>)`.
   After the execution brief and claim relation map are loaded, call
   `ResearchAction(compile_context_pack, work_frame_id=<frame-id>)` before final
   synthesis. If `ResearchAction` is not available, continue with the AITP MCP
   steps below.
4. If a v5 session id is already known, call
   `aitp_v5_get_execution_brief(base="{{TOPICS_ROOT}}", session_id=<session-id>)`.
   Then call `aitp_v5_get_claim_relation_map` for the same session before
   interpreting failures or deciding the next scientific action.
5. If only a topic slug is known, first call
   `aitp_v5_build_workspace_recovery_audit(base="{{TOPICS_ROOT}}", topics=[<topic>])`.
   If the row is `recovery_ready`, use that row's `session_id` and
   `active_claim_id`; then call the execution brief and claim relation map for
   the selected session. Do not migrate, create, bind, or update claim status
   during recovery when a ready v5 session already exists.
6. Use legacy discovery or migration only when the recovery audit reports no
   usable v5 session/active claim:
   `aitp_v5_migrate_curated_legacy_topic_to_v5` for known curated topics, or
   `aitp_v5_migrate_legacy_topic_to_v5` for a generic preservation pass.
7. If no topic matches, create a v5 topic, create an initial claim, bind a
   session, and then get the v5 execution brief.
8. Follow the v5 brief and load `aitp-runtime` for the typed-record loop.

Use these logical tool calls, mapped to the actual Codex tool names:

```text
aitp_v5_get_execution_brief(base="{{TOPICS_ROOT}}", session_id=<session-id>)
aitp_v5_get_claim_relation_map(base="{{TOPICS_ROOT}}", session_id=<session-id>)
aitp_v5_build_workspace_recovery_audit(base="{{TOPICS_ROOT}}", topics=[<topic>])
aitp_v5_migrate_curated_legacy_topic_to_v5(
  base="{{TOPICS_ROOT}}",
  topic_dir="{{TOPICS_ROOT}}/<legacy-topic-slug>"
)
aitp_v5_create_topic(base="{{TOPICS_ROOT}}", topic_id=<slug>, context_id=<context>, title=<title>)
aitp_v5_create_claim(base="{{TOPICS_ROOT}}", topic_id=<slug>, statement=<claim>, evidence_profile=<profile>, confidence_state="hypothesis", active_uncertainty=<uncertainty>)
aitp_v5_bind_session(base="{{TOPICS_ROOT}}", session_id=<session-id>, topic_id=<slug>, context_id=<context>, active_claim=<claim-id>)
```

## Progressive Recording Navigation

Do not make AITP write on every chat step. Trigger navigation only at durable
research moments: known-topic session start, active claim creation/change,
durable source identity/location, completed tool run, produced artifact,
observed result/anomaly/negative result, proof or validation gap, route pivot,
final answer about an active claim, trust/promotion request, or session-end
handoff.

Use the progressive sequence, mapped to the actual Codex tool names:

```text
aitp_v5_build_workspace_recording_audit(base="{{TOPICS_ROOT}}")      # read-only, if placement is unclear
aitp_v5_classify_recording_candidate(base="{{TOPICS_ROOT}}", ...)    # read-only
aitp_v5_get_recording_navigation_state(base="{{TOPICS_ROOT}}", session_id=<session-id>, claim_id=<claim-id>)  # read-only
aitp_v5_expand_recording_slot(base="{{TOPICS_ROOT}}", session_id=<session-id>, slot=<slot>, claim_id=<claim-id>)  # read-only
<existing typed write or preflight tool named by the slot expansion>
aitp_v5_verify_recording_effect(base="{{TOPICS_ROOT}}", session_id=<session-id>, expected_refs=[...])  # read-only
```

If the live Codex MCP surface is stale and these navigator tools are not
exposed, use the CLI fallback for read-only navigation and only mutate through
available typed v5 write tools. Never manually edit topic-state files.

Do not run the progressive navigator for generic explanation, vague
brainstorming, duplicate status summaries, or source/file scans that do not
change a claim, route, gap, artifact, or validation state. If a light
discussion becomes research, first restate the durable moment in one sentence,
then classify that candidate.

## Hard Rules

- When `ResearchAction` is available, do not make substantial MCP/file/shell
  recovery calls before opening a WorkFrame; otherwise those calls are not
  attached to the research recovery context.
- Do not manually inspect AITP topic state just to determine what exists. Ask
  AITP for a v5 session brief or use legacy discovery only for migration.
- Do not manually edit AITP topic-state files. Use AITP tools for topic state.
- Do not treat old `stage`, `gate_status`, or `L0/L1/L3/L4` fields as v5 truth.
- Do not call `bind_session`, migration, topic creation, or claim-status writes
  merely to restore an existing topic. Recovery is read-only until the user asks
  for a state-changing action or the audit shows no usable v5 binding.
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
