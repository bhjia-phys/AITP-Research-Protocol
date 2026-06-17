---
name: using-aitp
description: HIGHEST PRIORITY - Use for theoretical-physics research, exploratory physics discussion, old-knowledge Q&A tied to project topics, prior topic progress/status inquiries, topic continuation, paper learning, derivation work, validation planning, or study of physical systems. Classify request intensity before deciding read-only or write-capable flow.
---

# Using AITP v5 - Claude Code

## Hard Gate

Use this skill before substantial theoretical-physics work. This includes
brainstorming that may become a route, source reading, derivation, validation
planning, prior-topic progress/status inquiries, old-knowledge Q&A tied to a
project topic, and long-running theoretical-physics work.

AITP v5 truth comes from typed records: topics, sessions, claims, evidence,
artifacts, validation contracts/results, proof obligations, trust updates, and
approved L2 memory. Generated summaries, claim relation maps, adapter packets,
hook configs, old Markdown stages, and chat summaries are orientation only.

## Environment

- AITP v5 MCP entrypoint: `{{REPO_ROOT}}/brain/v5/native_mcp.py`
- v5 workspace base: `{{TOPICS_ROOT}}`
- Canonical v5 store: `{{TOPICS_ROOT}}/.aitp/`; workspace-root `.aitp/`
  is not the v5 topic store.
- Typed tools are named `mcp__aitp__aitp_v5_*` when exposed by Claude Code.
- Legacy aliases (`mcp__aitp__aitp_list_topics`,
  `mcp__aitp__aitp_get_execution_brief`, `mcp__aitp__aitp_bootstrap_topic`) are
  discovery/bootstrap compatibility only.
- Legacy L0-L4 write tools are read-only guards by default. If an old `aitp_*`
  write call returns `legacy_aitp_writes_disabled`, do not retry it; continue
  through v5 migration/binding and typed `mcp__aitp__aitp_v5_*` writes.

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

0. If the host exposes Hakimi/Kimi `ResearchAction`, open a WorkFrame before
   substantive AITP reads:
   `ResearchAction(open_work_frame, topic=<topic>, goal=<restore-or-research-goal>)`.
   After the execution brief and claim relation map are loaded, call
   `ResearchAction(compile_context_pack, work_frame_id=<frame-id>)` before final
   synthesis. If `ResearchAction` is not available, continue with the AITP MCP
   steps below.
1. If a v5 session id is known, call:

```text
mcp__aitp__aitp_v5_get_execution_brief(base="{{TOPICS_ROOT}}", session_id=<session-id>)
mcp__aitp__aitp_v5_get_claim_relation_map(base="{{TOPICS_ROOT}}", session_id=<session-id>)
```

2. If only a topic slug is known, first call the recovery audit:

```text
mcp__aitp__aitp_v5_build_workspace_recovery_audit(base="{{TOPICS_ROOT}}", topics=[<topic>])
```

If the row is `recovery_ready`, use that row's `session_id` and
`active_claim_id`; then call the execution brief and claim relation map for the
selected session. Do not migrate, create, bind, or update claim status during
recovery when a ready v5 session already exists.

3. Use legacy discovery or migration only when the recovery audit reports no
   usable v5 session/active claim:

```text
mcp__aitp__aitp_v5_migrate_curated_legacy_topic_to_v5(
  base="{{TOPICS_ROOT}}",
  topic_dir="{{TOPICS_ROOT}}/<legacy-topic-slug>"
)
```

For topics without a curated spec, use
`mcp__aitp__aitp_v5_migrate_legacy_topic_to_v5` as a preservation pass and then
write typed claims/status/gaps explicitly.
Do not write new progress back into old L0/L1/L3/L4 files.

4. If no topic exists, create a v5 topic, create the initial claim, bind a
   session, and get the v5 brief.
5. Load `aitp-runtime` and follow the typed brief fields, not old stage/gate
   fields.

## Progressive Recording Navigation

Do not write AITP records at every chat step. Trigger navigation at durable
moments: known-topic session start, active claim creation/change, durable source
identity/location, completed tool run, produced artifact, observed result or
anomaly, negative result, proof or validation gap, route pivot, final answer
about an active claim, trust/promotion request, or session-end handoff.

Use this sequence:

```text
mcp__aitp__aitp_v5_build_workspace_recording_audit(base="{{TOPICS_ROOT}}")      # read-only, if placement is unclear
mcp__aitp__aitp_v5_classify_recording_candidate(base="{{TOPICS_ROOT}}", ...)    # read-only
mcp__aitp__aitp_v5_get_recording_navigation_state(base="{{TOPICS_ROOT}}", session_id=<session-id>, claim_id=<claim-id>)  # read-only
mcp__aitp__aitp_v5_expand_recording_slot(base="{{TOPICS_ROOT}}", session_id=<session-id>, slot=<slot>, claim_id=<claim-id>)  # read-only
<existing typed write or preflight tool named by the slot expansion>
mcp__aitp__aitp_v5_verify_recording_effect(base="{{TOPICS_ROOT}}", session_id=<session-id>, expected_refs=[...])  # read-only
```

Audit, classifier, navigation, slot expansion, and verification surfaces cannot
update claim trust. Only the deepest typed write or preflight tool may mutate
kernel state, and trust still requires explicit trust/human gates.

Do not run the progressive navigator for generic explanation, vague
brainstorming, duplicate status summaries, or source/file scans that do not
change a claim, route, gap, artifact, or validation state. If a light
discussion becomes research, first restate the durable moment in one sentence,
then classify that candidate.

## Required Typed Writes

Record durable scientific content as typed records:

- sources and papers: reference location or registered source
- files and reports: artifact record
- definitions and objects: physics object
- equations and relations: object relation
- numerical/code work: code state, tool recipe, tool run, evidence
- checks: validation contract and validation result
- open theorem/review gaps: proof obligation
- maturity observations: claim status
- interpretation: sensemaking report, not validation

Before changing trust or L2 memory, use v5 trust preflight, validation coverage,
promotion packet, and human checkpoint gates.

## Hard Rules

- When `ResearchAction` is available, do not make substantial MCP/file/shell
  recovery calls before opening a WorkFrame; otherwise those calls are not
  attached to the research recovery context.
- Do not use old `stage`, `gate_status`, or `L0/L1/L3/L4` fields as v5 truth.
- Do not enable `AITP_LEGACY_ENABLE_WRITES=1` during normal research; it is for
  migration debugging and historical tests only.
- Do not call `bind_session`, migration, topic creation, or claim-status writes
  merely to restore an existing topic. Recovery is read-only until the user asks
  for a state-changing action or the audit shows no usable v5 binding.
- Do not promote to L2 from summaries, reports, or chat.
- Do not turn application/runtime failures into algorithm evidence. Use the
  claim relation map's `cannot_say`, `not_tested_by`, blockers, and next valid
  actions before summarizing a restored session.
- Do not treat hook config or hook traces as scientific evidence by themselves.
- Preserve uncertainty, negative results, failed attempts, and unresolved gaps.
- Ask the user normally if no structured question tool is available; never
  self-approve a human gate.

## Fallback Commands

Use these only when MCP tools are unavailable or setup is being diagnosed:

```powershell
python -m brain.v5.cli --base "{{TOPICS_ROOT}}" brief <session-id>
python -m brain.v5.cli --base "{{TOPICS_ROOT}}" relation-map <session-id>
python -m brain.v5.cli --base "{{TOPICS_ROOT}}" workspace inventory --workspace-root "{{TARGET_ROOT}}"
python -m brain.v5.cli --base "{{TOPICS_ROOT}}" workspace migration-plan --workspace-root "{{TARGET_ROOT}}"
python -m brain.v5.cli --base "{{TOPICS_ROOT}}" workspace old-store-manifest --workspace-root "{{TARGET_ROOT}}"
python -m brain.v5.cli --base "{{TOPICS_ROOT}}" legacy curated-known-topics
python scripts/aitp-pm.py doctor
```
