---
name: using-aitp
description: HIGHEST PRIORITY - Use for theoretical-physics research, topic continuation, paper learning, derivation work, validation planning, or study of physical systems. Enter AITP v5 before substantial work.
---

# Using AITP v5

Use AITP before brainstorming, source reading, derivation, validation planning,
or long-running theoretical-physics work.

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

1. If a v5 session id is known, call
   `aitp_v5_get_execution_brief(base="{{TOPICS_ROOT}}", session_id=<session-id>)`.
   Then call
   `aitp_v5_get_claim_relation_map(base="{{TOPICS_ROOT}}", session_id=<session-id>)`
   before interpreting failures, blockers, support, limitations, or next
   scientific actions.
2. If only a legacy topic slug is known, use legacy discovery only to locate the
   topic, then migrate/bind v5 state before doing research. Prefer
   `aitp_v5_migrate_curated_legacy_topic_to_v5`; use
   `aitp_v5_migrate_legacy_topic_to_v5` for generic preservation.
3. If no topic exists, create a v5 topic, create the initial claim, bind a
   session, and get the v5 brief.
4. Load `aitp-runtime` and follow typed brief fields, not old stage/gate fields.

## Hard Rules

- Do not use old `stage`, `gate_status`, or `L0/L1/L3/L4` fields as v5 truth.
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
