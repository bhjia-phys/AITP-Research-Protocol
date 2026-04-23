# AITP Agent Execution Bridge — Implementation Plan

## Problem Statement

AITP has well-specified layer semantics (L0→L1→L3→L4→L2) and internal write-back
methods in `aitp_service.py`, but the MCP tool surface does **not** expose
entry points for the most common agent actions during real research:

| Agent action | AITP spec says to do this | MCP tool exists? |
|---|---|---|
| Write a candidate to L3 ledger | L3-I/P/A sub-plane output | **No** |
| Submit numerical result as L4 return | Closed-loop `await_external_result` | **No** |
| Register a code artifact as evidence | Paired backend artifact | Manual only |
| Declare a finding with assumptions | Candidate `claim/evidence/assumptions` | **No** |
| Transition mode (explore→learn→implement) | Mode envelope S6 | Via control_note only |

**Consequence**: agents bypass AITP and write free-form research output,
producing empty candidate ledgers, empty iteration journals, and no L4 returns —
exactly what happened in the HS-like chaos topic.

## Architecture Constraints

1. **Two MCP servers**: `knowledge-hub` (hub_* tools in `mcp_server.py`) and
   `aitp` (aitp_* tools in `aitp_mcp_server.py`). New research-writeback tools
   belong in `aitp_mcp_server.py`.
2. **Service layer**: all business logic lives in `aitp_service.py` class
   `AITPService`. Private methods (`_replace_candidate_row`,
   `_load_candidate`, `_append_notebook_entry`) already implement the write-back;
   they just need thin MCP wrappers.
3. **Registration pattern**: `@aitp_tool(access="write")` decorator, then a
   `try/except` body calling `service.<method>(...)`, returning `_ok(**result)` or
   `_err(str(exc))`.
4. **Candidate ledger path**: `topics/<slug>/L3/runs/<run_id>/candidate_ledger.jsonl`
5. **Notebook auto-update**: `_replace_candidate_row` already calls
   `_maybe_record_candidate_derivation` and `_append_notebook_entry` — so any
   candidate write automatically updates the research notebook.

## Improvement 1: Candidate Writer MCP Tool (Priority: CRITICAL)

### Why

Without a candidate write path, the L3↔L4 loop is broken at step 0. The agent
has no structured way to declare findings, which means `_replace_candidate_row`
is never called, which means `research_notebook.tex` stays empty.

### Tool: `aitp_write_candidate`

**File to modify**: `aitp_mcp_server.py`
**Service method to add**: `AITPService.write_candidate()`

```python
@aitp_tool(access="write")
def aitp_write_candidate(
    topic_slug: str,
    title: str,
    claim_type: str,                           # "numerical"|"analytical"|"literature"|"conjecture"
    summary: str,
    evidence: str | None = None,               # free-text evidence description
    assumptions: list[str] | None = None,
    origin_refs: list[dict] | None = None,     # [{"path": ..., "title": ...}]
    trust_level: str = "provisional",          # "provisional"|"supported"|"validated"
    status: str = "active",
    candidate_id: str | None = None,           # auto-generated if None
    run_id: str | None = None,                 # auto-resolved if None
    sub_plane: str | None = None,              # "L3-I"|"L3-P"|"L3-A"|"L3-R"|"L3-D"
    question: str | None = None,               # adjudication question for derivation types
    updated_by: str = "aitp-mcp",
) -> str:
```

**Service method implementation**:

```python
def write_candidate(
    self,
    *,
    topic_slug: str,
    title: str,
    claim_type: str,
    summary: str,
    evidence: str | None = None,
    assumptions: list[str] | None = None,
    origin_refs: list[dict] | None = None,
    trust_level: str = "provisional",
    status: str = "active",
    candidate_id: str | None = None,
    run_id: str | None = None,
    sub_plane: str | None = None,
    question: str | None = None,
    updated_by: str = "aitp-mcp",
) -> dict[str, Any]:
```

Internal logic:
1. Resolve `run_id` → use current run from `topic_state.json` if not provided.
2. Generate `candidate_id` if not provided: `cand-<short-uuid>`.
3. Build the candidate row dict matching the existing schema:
   ```json
   {
     "candidate_id": "cand-abc123",
     "title": "...",
     "summary": "...",
     "claim_type": "numerical",
     "evidence": "...",
     "assumptions": ["..."],
     "origin_refs": [{"path": "...", "title": "..."}],
     "trust_level": "provisional",
     "status": "active",
     "promotion_status": "not_promoted",
     "sub_plane": "L3-A",
     "question": "...",
     "created_at": "2026-04-19T...",
     "updated_at": "2026-04-19T...",
     "updated_by": "aitp-mcp"
   }
   ```
4. Call `self._replace_candidate_row(topic_slug, run_id, candidate_id, row)`.
   This automatically:
   - Writes to `candidate_ledger.jsonl`
   - Mirrors derivation-type candidates to `derivation_records`
   - Appends a `candidate_update` entry to the research notebook

**Validation rules**:
- `title` and `claim_type` are required.
- `claim_type` must be one of: `numerical`, `analytical`, `literature`, `conjecture`.
- `trust_level` must be one of: `provisional`, `supported`, `validated`.
- If `candidate_id` is provided and exists in the ledger, update in place (idempotent).
- If `candidate_id` is provided but does not exist, create new with that ID.

## Improvement 2: L4 Return Submission Tool (Priority: CRITICAL)

### Why

When an agent runs numerical code (e.g., exact diagonalization for gap ratios),
the results need to flow back into the closed-loop as an L4 return. Currently
there is no tool to submit code results as L4 returns — the `returned_execution_result.json`
file is never written by agents.

### Tool: `aitp_submit_l4_return`

**File to modify**: `aitp_mcp_server.py`
**Service method to add**: `AITPService.submit_l4_return()`

```python
@aitp_tool(access="write")
def aitp_submit_l4_return(
    topic_slug: str,
    result_summary: str,
    result_classification: str = "success",   # "success"|"partial"|"failed"
    artifact_paths: list[str] | None = None,  # paths to result files (plots, data)
    candidate_ids: list[str] | None = None,   # candidates this result validates
    numerical_evidence: dict | None = None,   # structured numerical results
    contradiction_detected: bool = False,
    notes: str | None = None,
    run_id: str | None = None,
    updated_by: str = "aitp-mcp",
) -> str:
```

**Service method implementation**:

Internal logic:
1. Resolve `run_id` from current topic state if not provided.
2. Build the L4 return payload:
   ```json
   {
     "status": "completed",
     "classification": "success",
     "result_summary": "...",
     "artifact_paths": ["results/level_spacing.png", ...],
     "validated_candidates": ["cand-abc123"],
     "numerical_evidence": {
       "gap_ratio_mean": 0.535,
       "system_sizes": [6, 8, 10, 12],
       "critical_alpha_estimate": 1.85
     },
     "contradiction_detected": false,
     "notes": "...",
     "completed_at": "2026-04-19T...",
     "updated_by": "aitp-mcp"
   }
   ```
3. Write to `L4/runs/<run_id>/returned_execution_result.json`.
4. Update `iteration_journal.json` entry status from `pending_l4_return` to `returned`.
5. Call `_append_notebook_entry` with `kind="l4_return"`.
6. If `contradiction_detected`, set the closed-loop routing decision to `revise`.

**Key files to create/update**:
- `L4/runs/<run_id>/returned_execution_result.json` — main return payload
- `L4/runs/<run_id>/results/` — directory for artifact copies/references
- `L3/iteration_journal.json` — status update

## Improvement 3: Candidate Query Tool (Priority: HIGH)

### Why

Agents need to inspect existing candidates (e.g., to check deduplication, see
trust levels, or find candidates ready for promotion). Currently there is no
read-only query tool for the candidate ledger.

### Tool: `aitp_list_candidates`

```python
@aitp_tool(access="read")
def aitp_list_candidates(
    topic_slug: str,
    run_id: str | None = None,
    status: str | None = None,        # filter by status
    claim_type: str | None = None,    # filter by claim_type
    trust_level: str | None = None,   # filter by trust_level
    promotion_status: str | None = None,
    updated_by: str = "aitp-mcp",
) -> str:
```

Reads from `candidate_ledger.jsonl`, applies filters, returns matching rows.

## Improvement 4: Code Artifact Registration (Priority: MEDIUM)

### Why

When agents run Python scripts that produce plots/data, these artifacts should
be registered as evidence linked to candidates. Currently there is no structured
way to do this.

### Tool: `aitp_register_artifact`

```python
@aitp_tool(access="write")
def aitp_register_artifact(
    topic_slug: str,
    artifact_path: str,               # relative or absolute path to the artifact
    artifact_kind: str,               # "plot"|"data"|"script"|"log"|"derivation"
    description: str,
    linked_candidates: list[str] | None = None,  # candidate_ids this supports
    run_id: str | None = None,
    updated_by: str = "aitp-mcp",
) -> str:
```

Internal logic:
1. Register the artifact in `L3/runs/<run_id>/artifact_registry.jsonl`.
2. If `linked_candidates` provided, update those candidates' `origin_refs`.
3. Copy or symlink the artifact into the run's results directory.

## Improvement 5: Agent Execution Bridge Document (Priority: HIGH)

### Why

Even with MCP tools, agents need a concrete mapping from runtime state
(agent_brief.md, runtime_protocol.generated.md) to concrete actions. This is
the "missing manual" that tells an agent: "you are in mode X at layer Y, here
are the exact tool calls you should make."

### File to create: `docs/AGENT_EXECUTION_BRIDGE.md`

Content structure:
1. **State interpretation table**: given `mode`+`layer`+`submode`, what actions are available
2. **Candidate lifecycle**: create → update → submit L4 → promote
3. **Mode transition guide**: when and how to switch explore→learn→implement
4. **Common agent workflows**:
   - "I ran a numerical simulation" → call `aitp_write_candidate` + `aitp_submit_l4_return`
   - "I found a relevant paper" → call `hub_ingest_sources` + `aitp_write_candidate(claim_type="literature")`
   - "I have a result ready for L2" → call `aitp_request_promotion`
5. **Failure recovery**: what to do when stuck, how to use popup/decision tools

## Implementation Order

| Step | Improvement | Files | Estimated LOC |
|---|---|---|---|
| 1 | Candidate writer | `aitp_mcp_server.py`, `aitp_service.py` | ~80 |
| 2 | L4 return submission | `aitp_mcp_server.py`, `aitp_service.py` | ~90 |
| 3 | Candidate query | `aitp_mcp_server.py`, `aitp_service.py` | ~40 |
| 4 | Artifact registration | `aitp_mcp_server.py`, `aitp_service.py` | ~60 |
| 5 | Execution bridge doc | `docs/AGENT_EXECUTION_BRIDGE.md` | ~200 |

Steps 1-2 are the critical path — without them, no research can flow through AITP.

## Testing Strategy

1. **Unit tests** in `tests/test_aitp_mcp_server.py`:
   - Test each new tool with a minimal topic fixture
   - Verify candidate ledger JSONL is written correctly
   - Verify notebook entry is appended
   - Verify L4 return file is created with correct schema
   - Verify idempotent candidate update (same ID = overwrite)

2. **Integration test**: replay the HS-like chaos workflow using the new tools:
   - Bootstrap topic → write 6 candidates (one per diagnostic) → submit L4 return → verify notebook is populated

3. **Acceptance test script**: add a `run_agent_bridge_acceptance.py` to
   `_bundle/runtime/scripts/` that exercises the full candidate lifecycle.

## Key Integration Points

- `_replace_candidate_row()` (line 5790 in `aitp_service.py`) — already handles
  ledger write, derivation mirror, notebook append. The new MCP tool just builds
  the row dict and calls this.
- `_append_notebook_entry()` (line 788) — auto-called by `_replace_candidate_row`.
- `_materialize_minimum_l4_package()` (line 8913) — existing L4 materialization;
  the new tool writes the `returned_execution_result.json` that this expects.
- `research_notebook_support.py` — `append_notebook_entry()` handles the actual
  LaTeX generation. No changes needed here.
- `@aitp_tool(access="write")` decorator pattern (line 28 of `aitp_mcp_server.py`) —
  reuse existing registration mechanism.
