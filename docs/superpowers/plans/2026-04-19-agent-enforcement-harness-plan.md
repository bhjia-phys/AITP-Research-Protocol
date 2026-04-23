# GSD Plan: Agent Enforcement Harness

Status: active
Created: 2026-04-19
Scope: Implement the Brain enforcement contract (B14) from brain_protocol.md
Division: GSD per AITP_GSD_WORKFLOW_CONTRACT.md (this is repo work, not research)

---

## W1: MCP Write-Back Tools

Priority: CRITICAL (blocks everything else — no enforcement without escape valve)

### W1.1: `aitp_write_candidate` MCP tool

**Files:**
- `research/knowledge-hub/knowledge_hub/aitp_mcp_server.py` — add tool function
- `research/knowledge-hub/knowledge_hub/aitp_service.py` — add `write_candidate()` public method

**Schema:**
```python
@aitp_tool(access="write")
def aitp_write_candidate(
    topic_slug: str,
    title: str,
    claim_type: str,                           # numerical|analytical|literature|conjecture
    summary: str,
    evidence: str | None = None,
    assumptions: list[str] | None = None,
    origin_refs: list[dict] | None = None,     # [{"path": "...", "title": "..."}]
    trust_level: str = "provisional",          # provisional|supported|validated
    status: str = "active",
    candidate_id: str | None = None,           # auto-generated if None
    run_id: str | None = None,                 # auto-resolved if None
    sub_plane: str | None = None,              # L3-I|L3-P|L3-A|L3-R|L3-D
    question: str | None = None,
    updated_by: str = "aitp-mcp",
) -> str:
```

**Implementation:**
1. `write_candidate()` in `aitp_service.py` wraps `_replace_candidate_row()`
2. Auto-generate `candidate_id` via `uuid4` if not provided
3. Auto-resolve `run_id` from `topic_state.json` if not provided
4. Validate `claim_type` and `trust_level` against allowed values
5. Build row dict with `promotion_status="not_promoted"`, timestamps
6. Call `self._replace_candidate_row(topic_slug, run_id, candidate_id, row)`
   — this auto-updates notebook and derivation records

**Tests:** `research/knowledge-hub/tests/test_aitp_mcp_server.py`
- Happy path: write one candidate, verify ledger entry
- Idempotent: write same candidate_id twice → overwrite
- Validation: bad claim_type → error
- Side effects: verify notebook entry appended

### W1.2: `aitp_submit_l4_return` MCP tool

**Files:**
- `research/knowledge-hub/knowledge_hub/aitp_mcp_server.py` — add tool function
- `research/knowledge-hub/knowledge_hub/aitp_service.py` — add `submit_l4_return()` public method

**Schema:**
```python
@aitp_tool(access="write")
def aitp_submit_l4_return(
    topic_slug: str,
    result_summary: str,
    result_classification: str = "success",    # success|partial|failed
    artifact_paths: list[str] | None = None,
    candidate_ids: list[str] | None = None,
    numerical_evidence: dict | None = None,
    contradiction_detected: bool = False,
    notes: str | None = None,
    run_id: str | None = None,
    updated_by: str = "aitp-mcp",
) -> str:
```

**Implementation:**
1. Resolve `run_id` from topic state if not provided
2. Build L4 return payload with classification, artifacts, evidence
3. Write to `L4/runs/<run_id>/returned_execution_result.json`
4. Update `iteration_journal.json` entries from `pending_l4_return` to `returned`
5. Call `_append_notebook_entry(kind="l4_return", ...)`
6. If `contradiction_detected`, flag in interaction state

**Tests:**
- Happy path: submit return, verify file created
- Journal update: verify status change
- Notebook entry: verify appended

### W1.3: `aitp_list_candidates` MCP tool

**Files:** same as above

**Schema:**
```python
@aitp_tool(access="read")
def aitp_list_candidates(
    topic_slug: str,
    run_id: str | None = None,
    status: str | None = None,
    claim_type: str | None = None,
    trust_level: str | None = None,
    updated_by: str = "aitp-mcp",
) -> str:
```

Read from `candidate_ledger.jsonl`, apply filters, return matching rows.

### W1.4: `aitp_register_artifact` MCP tool

**Files:** same as above

**Schema:**
```python
@aitp_tool(access="write")
def aitp_register_artifact(
    topic_slug: str,
    artifact_path: str,
    artifact_kind: str,                        # plot|data|script|log|derivation
    description: str,
    linked_candidates: list[str] | None = None,
    run_id: str | None = None,
    updated_by: str = "aitp-mcp",
) -> str:
```

Register in `artifact_registry.jsonl`, update linked candidates' origin_refs.

---

## W2: PostToolUse Research-Output Detector

Priority: HIGH (enforcement layer for detecting bypassed output)

**File:** `C:\Users\samur\.claude\hooks\aitp-research-output-detector.py`

**Logic:**
```python
# PostToolUse hook
# Input: tool_name, tool_input, tool_output
#
# After Bash:
#   1. Check if stdout/stderr mentions result files (.png, .csv, .dat, .pdf)
#   2. Check if command was python/script execution (not git, ls, etc.)
#   3. If output detected and AITP topic is active:
#      → Create unregistered_output marker
#      → Inject: "Research output detected at {paths}. Call aitp_write_candidate
#         to register it before continuing."
#
# After Write:
#   1. Check if file is .tex, .py plot code, or analysis output
#   2. If outside AITP topic directory and topic is active:
#      → Inject: "File written outside AITP. Consider registering via
#         aitp_write_candidate or aitp_register_artifact."
#
# After aitp_write_candidate or aitp_submit_l4_return:
#   → Clear unregistered_output marker
```

**Registration:** Add to `settings.json` hooks.PreToolUse or create new PostToolUse entry.

---

## W3: Stop Hook Unregistered-Output Check

Priority: HIGH (final enforcement — block session end with unregistered work)

**File:** `C:\Users\samur\.claude\hooks\aitp-stop-guard.py`

**Logic:**
```python
# Stop hook
# 1. Check if AITP session is active (session_active marker exists)
# 2. Check unregistered_output marker
# 3. If unregistered output exists:
#    → Block with: "You have unregistered research output. Call
#       aitp_write_candidate or aitp_submit_l4_return before ending."
#    → Return {"decision": "block", "reason": "..."}
# 4. If all registered:
#    → Allow stop
```

**Registration:** Add to `settings.json` hooks.Stop.

---

## W4: Agent Brief Write-Back Template

Priority: HIGH (makes loop output actionable)

**File:** `research/knowledge-hub/knowledge_hub/_bundle/runtime/scripts/interaction_surface_support.py`
(or wherever `build_agent_brief` is defined)

**Change:** In the agent brief generation, add a "Required write-back actions" section:

```markdown
## Required write-back actions

You are currently at **L3-A (analysis)**.

After completing your computation, you MUST:
1. Call `aitp_write_candidate(topic_slug="...", title="...", claim_type="numerical",
   summary="...", evidence="...", origin_refs=[...])`
2. Call `aitp_submit_l4_return(topic_slug="...", result_summary="...",
   artifact_paths=[...])`

Do NOT proceed to the next loop cycle without these calls.
```

The section content depends on the current layer and submode, using the mapping
from B14.6.

---

## W5: Skill Update — Write-Back Rules

Priority: MEDIUM (reinforces but doesn't enforce)

**File:** Skill `using-aitp` SKILL.md

**Add section:**
```markdown
## Research write-back (MANDATORY)

After producing ANY numerical result, plot, derivation, or finding through code
execution or analysis, you MUST register it via AITP MCP tools:

- Numerical result → `aitp_write_candidate(claim_type="numerical")`
- Analytical finding → `aitp_write_candidate(claim_type="analytical")`
- Literature insight → `aitp_write_candidate(claim_type="literature")`
- Completed computation → `aitp_submit_l4_return()`
- Plot/data file → `aitp_register_artifact()`

Pattern: run code → read output → write_candidate → submit_l4_return

The PostToolUse hook will remind you. The Stop hook will block session end
if you forget.
```

---

## Execution Waves

### Wave 1 (Critical path — W1.1 + W1.2)
- [ ] W1.1: `aitp_write_candidate` service method
- [ ] W1.1: `aitp_write_candidate` MCP tool
- [ ] W1.1: Tests for write_candidate
- [ ] W1.2: `aitp_submit_l4_return` service method
- [ ] W1.2: `aitp_submit_l4_return` MCP tool
- [ ] W1.2: Tests for submit_l4_return

### Wave 2 (Enforcement — W2 + W3)
- [ ] W2: PostToolUse research-output detector hook
- [ ] W3: Stop hook unregistered-output check
- [ ] Register both hooks in settings.json

### Wave 3 (UX — W1.3 + W1.4 + W4 + W5)
- [ ] W1.3: `aitp_list_candidates` MCP tool + tests
- [ ] W1.4: `aitp_register_artifact` MCP tool + tests
- [ ] W4: Agent brief write-back template
- [ ] W5: Skill write-back rules section

### Wave 4 (Integration test)
- [ ] Replay HS-like chaos workflow using new tools
- [ ] Verify: 6 candidates written, 1 L4 return submitted, notebook populated
- [ ] Verify: enforcement hooks block bypass correctly

---

## Acceptance Criteria

1. Agent can call `aitp_write_candidate` and see entry in `candidate_ledger.jsonl`
2. Agent can call `aitp_submit_l4_return` and see `returned_execution_result.json`
3. Research notebook auto-updates after each candidate write
4. PostToolUse hook detects unregistered output and injects reminder
5. Stop hook blocks session end with unregistered output
6. Existing tests pass (no regressions)
7. HS-like chaos topic can be replayed through the new tools end-to-end
