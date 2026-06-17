---
name: using-aitp
description: HIGHEST PRIORITY - Use for theoretical-physics research, topic continuation, exploratory physics discussion, old-knowledge Q&A tied to a project topic, prior topic progress/status inquiries, paper learning, derivation work, validation planning, or study of physical systems. Classify request intensity before deciding read-only or write-capable flow.
---

# Using AITP v5

Use AITP before substantial theoretical-physics work. This includes active
research, exploratory discussion that may become a route, paper learning,
source reading, derivation, validation planning, prior-topic progress/status
inquiries, and old-knowledge Q&A that touches an existing project topic.

AITP v5 truth comes from typed records: topics, sessions, claims, evidence,
artifacts, validation contracts/results, proof obligations, trust updates, and
approved L2 memory. Generated summaries, claim relation maps, hook configs, old
Markdown stages, and chat summaries are orientation only.

## Environment

- AITP v5 MCP entrypoint: `{{REPO_ROOT}}/brain/v5/native_mcp.py`
- v5 workspace base: `{{TOPICS_ROOT}}`
- Canonical v5 store: `{{TOPICS_ROOT}}/.aitp/`; workspace-root `.aitp/`
  is not the v5 topic store.
- Typed tools are named `aitp_v5_*`.
- Legacy aliases (`aitp_list_topics`, `aitp_get_execution_brief`,
  `aitp_bootstrap_topic`) are discovery/bootstrap compatibility only.

## Entry Procedure

### Request Intensity

First classify the user request. This prevents AITP from becoming heavy while
still keeping research state recoverable.

- **Status or prior-progress inquiry**: use read-only recovery only. Call the
  workspace recovery audit when the topic is unknown or ambiguous, then brief
  and relation map for the selected session. Do not write unless the user asks
  to record a handoff or the brief exposes an unresolved human checkpoint.
- **Old-knowledge or textbook Q&A**: if the question is generic and not tied to
  a known topic, answer normally and do not mutate AITP. If it is tied to a
  topic or may affect a claim, restore brief plus relation map, answer with
  boundaries, and write only if the answer produces a durable source, gap,
  route, or correction.
- **Light exploratory physics discussion**: restore/read topic context when a
  topic is known. Use the recording candidate classifier before writing.
  Brainstorming without an accepted route, source, artifact, result, or gap is
  read-only.
- **Topic continuation, derivation, source reading, code/numerical work, or
  validation**: restore brief and relation map, then use the progressive
  recording navigator at durable moments.
- **Final claim synthesis, contradiction, trust update, L2 promotion, or memory
  request**: restore brief and relation map, run the relevant preflight or
  human checkpoint, and never self-approve trust or promotion.

### Intent Matrix

Use the lightest AITP path that preserves truth.

| User intent | AITP read depth | Recording default | Escalate to write when |
|---|---|---|---|
| Generic textbook or old-knowledge Q&A | None, unless the answer names an existing topic/claim | No write | The answer corrects project memory, finds a durable gap, or introduces a reusable source |
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
1. If a v5 session id is known, call
   `aitp_v5_get_execution_brief(base="{{TOPICS_ROOT}}", session_id=<session-id>)`.
   Then call
   `aitp_v5_get_claim_relation_map(base="{{TOPICS_ROOT}}", session_id=<session-id>)`
   before interpreting failures, blockers, support, limitations, or next
   scientific actions.
2. If only a topic slug is known, first call
   `aitp_v5_build_workspace_recovery_audit(base="{{TOPICS_ROOT}}", topics=[<topic>])`.
   If the row is `recovery_ready`, use that row's `session_id` and
   `active_claim_id`; then call the execution brief and claim relation map for
   the selected session. Do not migrate, create, bind, or update claim status
   during recovery when a ready v5 session already exists.
3. Use legacy discovery or migration only when the recovery audit reports no
   usable v5 session/active claim. Prefer
   `aitp_v5_migrate_curated_legacy_topic_to_v5` for curated legacy topics; use
   `aitp_v5_migrate_legacy_topic_to_v5` for generic preservation.
4. If no topic exists, create a v5 topic, create the initial claim, bind a
   session, and get the v5 brief.
5. Load `aitp-runtime` and follow typed brief fields, not old stage/gate fields.

## Progressive Recording Navigation

Do not record every step. Trigger AITP navigation only at durable moments:
session start for a known continuation, active claim creation/change, durable
source identity/location, completed tool run, produced artifact, observed
result/anomaly/negative result, proof or validation gap, route pivot, final
answer about an active claim, trust/promotion request, or session-end handoff.

When such a moment occurs:

1. If placement is unclear, call
   `aitp_v5_build_workspace_recording_audit(base="{{TOPICS_ROOT}}")`.
2. Classify the candidate with `aitp_v5_classify_recording_candidate`.
3. If the decision is `ignore` or `defer`, do not write.
4. If the decision is `navigate`, call
   `aitp_v5_get_recording_navigation_state` for the active session.
5. Expand exactly one first-level slot with `aitp_v5_expand_recording_slot`.
6. Call the named existing typed write or preflight tool.
7. Verify the result with `aitp_v5_verify_recording_effect`.

The audit, classifier, navigation state, slot expansion, and verification
surfaces are read-only. Only the deepest typed write/preflight tool may mutate
kernel state, and it still cannot update claim trust unless the explicit trust
gate allows it.

Do not run the progressive navigator for generic explanation, vague
brainstorming, duplicate status summaries, or source/file scans that do not
change a claim, route, gap, artifact, or validation state. If a light
discussion becomes research, first restate the durable moment in one sentence,
then classify that candidate.

## Hard Rules

- When `ResearchAction` is available, do not make substantial MCP/file/shell
  recovery calls before opening a WorkFrame; otherwise those calls are not
  attached to the research recovery context.
- Do not use old `stage`, `gate_status`, or `L0/L1/L3/L4` fields as v5 truth.
- Do not call `bind_session`, migration, topic creation, or claim-status writes
  merely to restore an existing topic. Recovery is read-only until the user asks
  for a state-changing action or the audit shows no usable v5 binding.
- Do not promote to L2 from summaries, reports, or chat.
- Do not turn application/runtime failures into algorithm evidence. Use the
  claim relation map's `cannot_say`, `not_tested_by`, blockers, and next valid
  actions before summarizing a restored session.
- Preserve uncertainty, negative results, failed attempts, and unresolved gaps.
- Ask the user normally if no structured question tool is available; never
  self-approve a human gate.

## Fallback Commands

```powershell
python -m brain.v5.cli --base "{{TOPICS_ROOT}}" brief <session-id>
python -m brain.v5.cli --base "{{TOPICS_ROOT}}" relation-map <session-id>
python -m brain.v5.cli --base "{{TOPICS_ROOT}}" workspace inventory --workspace-root "{{TARGET_ROOT}}"
python -m brain.v5.cli --base "{{TOPICS_ROOT}}" workspace migration-plan --workspace-root "{{TARGET_ROOT}}"
python -m brain.v5.cli --base "{{TOPICS_ROOT}}" workspace old-store-manifest --workspace-root "{{TARGET_ROOT}}"
python -m brain.v5.cli --base "{{TOPICS_ROOT}}" legacy curated-known-topics
python scripts/aitp-pm.py doctor
```
