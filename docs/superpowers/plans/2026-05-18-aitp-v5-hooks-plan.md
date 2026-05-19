# AITP v5 Hooks Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make hooks lightweight lifecycle helpers that log by default and block only explicit high-risk protocol violations.

**Architecture:** Hook code calls `brain/v5/policy.py`, `brain/v5/hooks.py`, and `brain/v5/trace.py`; it does not implement separate policy. Hook outputs stay short and machine-readable so Codex, Claude Code, OpenCode, and shell wrappers can use the same decisions.

**Tech Stack:** Python standard library, pytest, JSON-friendly dataclasses, optional shell wrappers after kernel tests pass.

---

## File Responsibility Map

- `brain/v5/hooks.py`: pure hook decision helpers.
- `brain/v5/policy.py`: non-negotiable protocol guards.
- `brain/v5/trace.py`: append-only trace event records.
- `tests/test_v5_hooks.py`: hook behavior.
- `tests/test_v5_policy.py`: policy behavior invoked by hooks.
- `tests/test_v5_trace_audit.py`: trace/audit behavior after hook events.

## Task 1: PreToolUse Blocks Only Real High Risk

**Files:**
- Modify: `tests/test_v5_hooks.py`
- Modify: `brain/v5/hooks.py`

- [ ] **Step 1: Write the failing test**

```python
def test_pre_tool_use_warns_low_risk_policy_issue_but_blocks_high_risk():
    from brain.v5.hooks import decide_pre_tool_use
    from brain.v5.policy import PolicyDecision, PolicyReason

    decision = PolicyDecision(
        allowed=False,
        reasons=[PolicyReason(policy_id="needs_evidence", severity="warning", message="record evidence")],
        required_actions=["record_evidence"],
    )

    low = decide_pre_tool_use(action="discuss_claim", risk_level="guided", policy_decision=decision)
    high = decide_pre_tool_use(action="promote_to_l2", risk_level="adversarial", policy_decision=decision)

    assert low.block is False
    assert low.mode == "warn"
    assert high.block is True
    assert high.mode == "block"
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_hooks.py::test_pre_tool_use_warns_low_risk_policy_issue_but_blocks_high_risk -q
```

Expected: fail if hooks do not distinguish risk/action severity.

- [ ] **Step 3: Implement minimal decision logic**

In `brain/v5/hooks.py`, block when policy severity is hard block, risk is rigorous/adversarial, or the action is one of promotion, harness patch, destructive action, remote execution, or expensive compute.

- [ ] **Step 4: Verify**

```powershell
pytest tests\test_v5_hooks.py tests\test_v5_policy.py -q
```

Expected: all pass.

## Task 2: PostToolUse Emits Trace Events, Not Claims

**Files:**
- Modify: `tests/test_v5_hooks.py`
- Modify: `brain/v5/hooks.py`

- [ ] **Step 1: Write the failing test**

```python
def test_post_tool_use_event_is_trace_not_evidence_record():
    from brain.v5.hooks import post_tool_use_trace_event

    event = post_tool_use_trace_event(
        session_id="s1",
        topic_id="fqhe",
        risk_level="guided",
        claim_id="claim-1",
        tool_name="metric_table_check",
        evidence_status="supports",
    )

    assert event.event_type == "tool_run_recorded"
    assert event.payload["tool_name"] == "metric_table_check"
    assert "summary" in event.payload
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_hooks.py::test_post_tool_use_event_is_trace_not_evidence_record -q
```

Expected: fail until the hook creates the compact trace event.

- [ ] **Step 3: Implement minimal event builder**

Return a `TraceEvent`; do not write evidence from this helper. Evidence writing belongs to tool-run kernel functions.

- [ ] **Step 4: Verify**

```powershell
pytest tests\test_v5_hooks.py tests\test_v5_trace_audit.py -q
```

Expected: all pass.

## Task 3: PreCommit Requires Tests For Harness Changes

**Files:**
- Modify: `tests/test_v5_hooks.py`
- Modify: `brain/v5/hooks.py`

- [ ] **Step 1: Write the failing test**

```python
def test_pre_commit_blocks_harness_change_without_test_reference():
    from brain.v5.hooks import decide_pre_commit

    decision = decide_pre_commit(
        changed_files=["brain/v5/policy.py"],
        test_refs=[],
        evolution_note="tighten policy after incident",
    )

    assert decision.block is True
    assert "add_regression_test" in decision.required_actions
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_hooks.py::test_pre_commit_blocks_harness_change_without_test_reference -q
```

Expected: fail until pre-commit decision enforces tests.

- [ ] **Step 3: Verify and commit**

```powershell
pytest tests\test_v5_hooks.py tests\test_v5_policy.py tests\test_v5_trace_audit.py -q
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
git add brain/v5/hooks.py tests/test_v5_hooks.py
git commit -m "feat(v5): add lightweight hook decisions"
git push origin codex/aitp-v5-kernel-mvp
git push origin HEAD:main
```
