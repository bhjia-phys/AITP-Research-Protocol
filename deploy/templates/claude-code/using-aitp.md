---
name: using-aitp
description: HIGHEST PRIORITY - Use for theoretical-physics research, topic continuation, paper learning, derivation work, validation planning, or study of physical systems. Enter AITP v5 before substantial work.
---

# Using AITP v5 - Claude Code

## Hard Gate

Use this skill before brainstorming, source reading, derivation, validation
planning, or long-running theoretical-physics work.

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

## Entry Procedure

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

4. If no topic exists, create a v5 topic, create the initial claim, bind a
   session, and get the v5 brief.
5. Load `aitp-runtime` and follow the typed brief fields, not old stage/gate
   fields.

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
