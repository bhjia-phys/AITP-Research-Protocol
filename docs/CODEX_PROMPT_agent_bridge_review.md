# Codex Review Prompt: AITP Agent Execution Bridge

## Task

Review and implement the AITP Agent Execution Bridge improvements described in
`docs/AGENT_EXECUTION_BRIDGE_PLAN.md`. The goal is to add MCP tools that let AI
agents actually follow the AITP research protocol instead of bypassing it.

## Context

The AITP (AI-assisted Theoretical Physics) protocol defines a layered research
pipeline (L0→L1→L3→L4→L2) with a candidate ledger, iteration journal, and
auto-generated research notebook. The problem: agents can read protocol state
but cannot write back research findings through the protocol. The MCP tool
surface is read-heavy — no tools exist for writing candidates or submitting
numerical results as L4 returns. This means the candidate ledger stays empty,
the research notebook stays empty, and agents do free-form research outside the
protocol.

## Files to Review

### Must read first (in order):
1. `docs/AGENT_EXECUTION_BRIDGE_PLAN.md` — the implementation plan
2. `docs/AITP_SPEC.md` sections S3 (Layer Model), S6 (Mode Envelope), S7 (Closed-Loop) — authoritative spec
3. `docs/protocols/L3_execution_protocol.md` — L3 sub-planes and candidate management
4. `docs/protocols/closed_loop_protocol.md` — closed-loop state machine

### Code files to review:
5. `research/knowledge-hub/knowledge_hub/aitp_mcp_server.py` — MCP tool registration (add new tools here)
6. `research/knowledge-hub/knowledge_hub/aitp_service.py` — service layer (add new methods here)
   - Key methods to understand:
     - `_replace_candidate_row()` (line ~5790) — writes candidate to ledger + auto-updates notebook
     - `_load_candidate()` (line ~5774) — reads candidate from ledger
     - `_append_notebook_entry()` (line ~788) — appends to research notebook
     - `_candidate_ledger_path()` (line ~907) — path resolution for ledger
     - `_materialize_minimum_l4_package()` (line ~8913) — L4 package materialization
7. `research/knowledge-hub/knowledge_hub/mcp_server.py` — reference for FastMCP pattern
8. `research/knowledge-hub/knowledge_hub/research_notebook_support.py` — notebook auto-generation
9. `research/knowledge-hub/tests/test_aitp_mcp_server.py` — existing tests (extend)

## Implementation Priority

### Priority 1 (CRITICAL — do these first):

**1. `aitp_write_candidate` MCP tool**

Add to `aitp_mcp_server.py`:
- Decorator: `@aitp_tool(access="write")`
- Parameters: `topic_slug, title, claim_type, summary, evidence, assumptions, origin_refs, trust_level, status, candidate_id, run_id, sub_plane, question, updated_by`
- Logic: build a candidate row dict, call `service._replace_candidate_row()`

Add to `aitp_service.py`:
- New public method `write_candidate()` that wraps `_replace_candidate_row()`
- Auto-generate `candidate_id` if not provided (use `cand-<uuid4[:8]>`)
- Auto-resolve `run_id` from topic state if not provided
- Validate `claim_type` ∈ {numerical, analytical, literature, conjecture}
- Validate `trust_level` ∈ {provisional, supported, validated}
- Set `promotion_status: "not_promoted"`, timestamps

**2. `aitp_submit_l4_return` MCP tool**

Add to `aitp_mcp_server.py`:
- Parameters: `topic_slug, result_summary, result_classification, artifact_paths, candidate_ids, numerical_evidence, contradiction_detected, notes, run_id, updated_by`
- Logic: write `returned_execution_result.json` to `L4/runs/<run_id>/`, update iteration journal

Add to `aitp_service.py`:
- New public method `submit_l4_return()`
- Write JSON payload to `L4/runs/<run_id>/returned_execution_result.json`
- Update `iteration_journal.json` entries from `pending_l4_return` to `returned`
- Append notebook entry with `kind="l4_return"`
- If `contradiction_detected`, flag in interaction state

### Priority 2 (HIGH):

**3. `aitp_list_candidates` MCP tool**

Read-only tool to query the candidate ledger with filters.
Uses `_load_candidate()` pattern but returns all matching rows.

**4. `aitp_register_artifact` MCP tool**

Register code outputs (plots, data files) as evidence linked to candidates.

### Priority 3 (MEDIUM):

**5. Agent Execution Bridge document** (`docs/AGENT_EXECUTION_BRIDGE.md`)

A human-readable guide mapping runtime state to concrete agent actions.

## Conventions to Follow

- Use the existing `@aitp_tool(access="...")` decorator pattern
- Return `_ok(**result)` on success, `_err(str(exc))` on failure
- Use `try/except Exception` wrapping (consistent with existing tools)
- Import `uuid4` from `uuid` for auto-generated IDs
- Timestamps in ISO 8601 format
- Keep tool parameter names consistent with existing schema fields
- All new service methods should be public (no leading underscore) since they're called from MCP tools
- Existing private methods (`_replace_candidate_row`, etc.) remain private — new public methods wrap them

## Testing Requirements

For each new tool:
1. Add a test function to `tests/test_aitp_mcp_server.py`
2. Test the happy path (successful write)
3. Test validation failures (bad claim_type, missing required fields)
4. Test idempotent updates (write candidate with same ID twice → overwrite)
5. Verify side effects: candidate_ledger.jsonl written, notebook entry appended

## Verification Checklist

After implementation, verify:
- [ ] `aitp_write_candidate` creates entries in `candidate_ledger.jsonl`
- [ ] `aitp_write_candidate` triggers notebook auto-update via `_replace_candidate_row`
- [ ] `aitp_submit_l4_return` writes `returned_execution_result.json`
- [ ] `aitp_list_candidates` returns filtered candidate rows
- [ ] `aitp_register_artifact` creates artifact registry entries
- [ ] All new tools have corresponding tests
- [ ] No existing tools or tests are broken
- [ ] Tool schemas are discoverable via `aitp_list_tool_manifest`

## Out of Scope

- Do NOT modify `_replace_candidate_row`, `_append_notebook_entry`, or any
  existing private methods — they work correctly.
- Do NOT modify `research_notebook_support.py` — it already handles notebook
  generation from ledger entries.
- Do NOT change the FastMCP registration mechanism or `aitp_tool` decorator.
- Do NOT add new dependencies beyond `uuid` (stdlib).
