---
name: using-aitp
description: HIGHEST PRIORITY - Use for ANY theoretical-physics research, topic continuation, idea steering, paper learning, derivation work, validation planning, or study of physical systems. Enter AITP v5 before any substantial response.
---

# Using AITP v5 - Kimi Code

## Hard Gate

Use this skill before brainstorming, literature exploration, derivation, validation planning, or long-running theoretical-physics work.

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

1. If the request might belong to theoretical physics, call
   `aitp_v5_get_execution_brief` for the active session before doing
   substantive work.
   Also call `aitp_v5_get_claim_relation_map` for the same session before
   interpreting failures, blockers, support, limitations, or next actions.
2. If no active v5 session is known, use `aitp_list_topics` and
   `aitp_get_execution_brief` only to orient legacy topics. Before doing
   substantive research, migrate/bind a v5 session with
   `aitp_v5_migrate_curated_legacy_topic_to_v5` for known curated topics,
   `aitp_v5_migrate_legacy_topic_to_v5` for generic preservation, or create a
   new v5 topic/claim/session with `aitp_v5_create_topic`,
   `aitp_v5_create_claim`, and `aitp_v5_bind_session`.
3. Read the execution brief and follow its risk, claim, evidence, validation, and next-action fields.
   Read the claim relation map as the read-only conclusion-boundary layer; it
   cannot update claim trust.
4. For every meaningful result, use typed writes:
   - `aitp_v5_record_physics_object`
   - `aitp_v5_record_object_relation`
   - `aitp_v5_record_evidence`
   - `aitp_v5_record_tool_run`
   - `aitp_v5_create_validation_contract`
   - `aitp_v5_record_validation_result`
   - `aitp_v5_record_sensemaking_report`
5. Before trust changes or L2 memory promotion, use the v5 trust/promotion gate. Never promote from a summary alone.

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

- "I can answer this research question directly without a brief."
- "This summary is enough to promote memory."
- "The hook config says this happened, so the claim is validated."
- "This runtime/application failure proves the algorithm works or fails."
- "I'll record the tool run later."
