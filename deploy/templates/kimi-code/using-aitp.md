---
name: using-aitp
description: HIGHEST PRIORITY - Use for ANY theoretical-physics research, topic continuation, exploratory physics discussion, old-knowledge Q&A tied to project topics, prior topic progress/status inquiries, idea steering, paper learning, derivation work, validation planning, or study of physical systems. Classify request intensity before deciding read-only or write-capable flow.
---

# Using AITP v5 - Kimi Code

## Hard Gate

Use this skill before substantial theoretical-physics work. This includes
brainstorming that may become a route, literature exploration, derivation,
validation planning, prior-topic progress/status inquiries, old-knowledge Q&A
tied to a project topic, and long-running theoretical-physics work.

Do not treat chat summaries, Markdown notes, or generated hook config as scientific truth. AITP v5 truth comes from typed records, execution briefs, validation results, promotion packets, and approved memory entries.

## Environment

- AITP v5 runs through the native MCP entrypoint at `{{REPO_ROOT}}/brain/v5/native_mcp.py`.
- Kimi Code should expose the MCP server as `aitp`; typed tools are named
  `aitp_v5_*`.
- Project installs may also expose legacy-friendly discovery aliases
  `aitp_list_topics`, `aitp_get_execution_brief`, and `aitp_bootstrap_topic`
  from the same v5 native MCP server. Treat these aliases as discovery or
  bootstrap compatibility only; they are not the execution contract for v5 work.
- Current AITP project installs use `.kimi/config.toml` and `.kimi/skills/`.
- Newer Kimi Code installs may use `.kimi-code/config.toml`, `.kimi-code/mcp.json`, and `.kimi-code/skills/`.
- If the local Kimi CLI supports explicit paths, load project assets with `--config-file`, `--mcp-config-file`, and `--skills-dir`.
- On Windows terminals, set `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1` before `kimi mcp test` if the CLI crashes while printing Unicode status symbols.

## Entry Procedure

### Request Intensity

Classify the request before deciding how much AITP to load:

- Status or prior-progress inquiry: read-only recovery, execution brief, and
  claim relation map. Do not write unless the user asks for a handoff or an
  unresolved human checkpoint must be answered.
- Old-knowledge/textbook Q&A: answer normally if generic. If tied to a known
  topic or claim, restore brief plus relation map; write only durable sources,
  gaps, routes, or corrections.
- Light exploratory discussion: restore known topic context, but record only
  when a durable route, question, source, artifact, result, or gap emerges.
- Continuation, derivation, source reading, code/numerical work, validation,
  contradiction, final synthesis, trust update, or L2 promotion: restore the v5
  session and follow typed runtime gates.

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

0. If `ResearchAction` is available, open a WorkFrame before substantive AITP
   reads:
   `ResearchAction(open_work_frame, topic=<topic>, goal=<restore-or-research-goal>)`.
   After the execution brief and claim relation map are loaded, call
   `ResearchAction(compile_context_pack, work_frame_id=<frame-id>)` before final
   synthesis. If `ResearchAction` is not available, continue with the AITP MCP
   steps below.
1. If the request might belong to theoretical physics, call
   `aitp_v5_get_execution_brief` for the active session before doing
   substantive work.
   Also call `aitp_v5_get_claim_relation_map` for the same session before
   interpreting failures, blockers, support, limitations, or next actions.
2. If only a topic slug is known, first call
   `aitp_v5_build_workspace_recovery_audit` for that topic. If the row is
   `recovery_ready`, use the selected `session_id` and `active_claim_id`; then
   call `aitp_v5_get_execution_brief` and `aitp_v5_get_claim_relation_map` for
   that session. Do not migrate, create, bind, or update claim status during
   recovery when a ready v5 session already exists.
3. Use `aitp_list_topics` and `aitp_get_execution_brief` only to orient legacy
   topics after the v5 recovery audit has failed. Before substantive research,
   migrate/bind a v5 session with `aitp_v5_migrate_curated_legacy_topic_to_v5`
   for known curated topics, `aitp_v5_migrate_legacy_topic_to_v5` for generic
   preservation, or create a new v5 topic/claim/session with
   `aitp_v5_create_topic`, `aitp_v5_create_claim`, and
   `aitp_v5_bind_session`.
4. Read the execution brief and follow its risk, claim, evidence, validation, and next-action fields.
   Read the claim relation map as the read-only conclusion-boundary layer; it
   cannot update claim trust.
5. For every meaningful result, use typed writes:
   - `aitp_v5_record_physics_object`
   - `aitp_v5_record_object_relation`
   - `aitp_v5_record_evidence`
   - `aitp_v5_record_tool_run`
   - `aitp_v5_create_validation_contract`
   - `aitp_v5_record_validation_result`
   - `aitp_v5_record_sensemaking_report`
6. Before trust changes or L2 memory promotion, use the v5 trust/promotion gate. Never promote from a summary alone.

## Progressive Recording Navigation

Do not write AITP records at every chat step. Trigger navigation at durable
moments: known-topic session start, active claim creation/change, durable source
identity/location, completed tool run, produced artifact, observed result or
anomaly, negative result, proof or validation gap, route pivot, final answer
about an active claim, trust/promotion request, or session-end handoff.

Use this sequence, mapped to the available Kimi/Hakimi tool names:

```text
aitp_v5_build_workspace_recording_audit(base="{{TOPICS_ROOT}}")      # read-only, if placement is unclear
aitp_v5_classify_recording_candidate(base="{{TOPICS_ROOT}}", ...)    # read-only
aitp_v5_get_recording_navigation_state(base="{{TOPICS_ROOT}}", session_id=<session-id>, claim_id=<claim-id>)  # read-only
aitp_v5_expand_recording_slot(base="{{TOPICS_ROOT}}", session_id=<session-id>, slot=<slot>, claim_id=<claim-id>)  # read-only
<existing typed write or preflight tool named by the slot expansion>
aitp_v5_verify_recording_effect(base="{{TOPICS_ROOT}}", session_id=<session-id>, expected_refs=[...])  # read-only
```

Audit, classifier, navigation, slot expansion, and verification surfaces cannot
update claim trust. Only the deepest typed write or preflight tool may mutate
kernel state, and trust still requires explicit trust/human gates.

Do not run the progressive navigator for generic explanation, vague
brainstorming, duplicate status summaries, or source/file scans that do not
change a claim, route, gap, artifact, or validation state. If a light
discussion becomes research, first restate the durable moment in one sentence,
then classify that candidate.

## Kimi Hook Installation

Generate or merge project-local Kimi hooks from the v5 kernel:

```powershell
python -m brain.v5.cli --base <workspace> adapter install-hooks kimi-code <session-id> --settings <workspace>/.kimi/config.toml
python -m brain.v5.cli --base <workspace> adapter install-hooks kimi-code <session-id> --settings <workspace>/.kimi-code/config.toml
```

Audit the installed Kimi config:

```powershell
python -m brain.v5.cli --base <workspace> adapter install-audit kimi-code --settings <workspace>/.kimi/config.toml
python -m brain.v5.cli --base <workspace> adapter install-audit kimi-code --settings <workspace>/.kimi-code/config.toml
```

The installed hooks are lifecycle guards only. They can block risky pre-tool actions and append post-tool trace events, but they cannot update claim trust.

## Working Style

- Talk naturally with the researcher, but record durable scientific content as typed records.
- Keep definitions, claims, evidence, tool runs, validation contracts, validation results, and sensemaking separate.
- Record negative results and failure modes immediately.
- If Kimi hooks are unavailable, continue through MCP tools and note the hook gap as runtime metadata only.

## Red Flags

Stop and re-enter AITP v5 if you catch yourself saying:

- "I can make substantial recovery calls before opening the available WorkFrame."
- "I can answer this research question directly without a brief."
- "This summary is enough to promote memory."
- "The hook config says this happened, so the claim is validated."
- "This runtime/application failure proves the algorithm works or fails."
- "I need to bind or update claim status just to restore an existing ready topic."
- "I'll record the tool run later."
