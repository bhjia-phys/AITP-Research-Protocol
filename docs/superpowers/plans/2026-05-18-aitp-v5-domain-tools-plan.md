# AITP v5 Domain Tools Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide reusable theoretical-physics domain packs and safe tool recommendations without hard-coding user-facing topic types.

**Architecture:** Domain packs suggest question intents, risk signals, safe tool recipes, executor recommendations, and trust-card templates. They never weaken global truth standards and never become evidence by themselves. Tool runs produce auditable `ToolRunRecord` and `EvidenceRecord` objects.

Current implementation note: the safe executor catalog now includes
`formula_code_invariant_check`, a deterministic in-process formula-code
translation checker, and `failure_mode_basis_check`, a deterministic
in-process review-basis checker. The LibRPA/GW domain pack recommends
`recipe-librpa-gw-formula-code-invariant`; FQHE and LibRPA/GW domain packs also
recommend `recipe-fqhe-failure-mode-review-basis` and
`recipe-librpa-gw-failure-mode-review-basis`, so a passed
`failure_mode_review_result_record` can cite concrete tool/validation basis
rather than only prose.

**Tech Stack:** Python dataclasses, pytest, Markdown+YAML store, built-in deterministic executors.

---

## File Responsibility Map

- `brain/v5/domain_packs.py`: built-in pack definitions, persistence, recommendations.
- `brain/v5/tool_executors.py`: safe deterministic executors.
- `brain/v5/evidence.py`: evidence records linked to tool runs.
- `brain/v5/brief.py`: recommended executor actions in execution briefs.
- `tests/test_v5_domain_packs.py`: pack behavior.
- `tests/test_v5_evidence_tools.py`: executor/evidence behavior.
- `tests/test_v5_real_workflows.py`: FQHE and GW acceptance flows.

## Task 1: Domain Packs Suggest Tool Executors

**Files:**
- Modify: `tests/test_v5_domain_packs.py`
- Modify: `brain/v5/domain_packs.py`

- [ ] **Step 1: Write the failing test**

```python
def test_gw_domain_pack_recommends_code_method_executor():
    from brain.v5.domain_packs import suggest_tool_executors_for_claim
    from brain.v5.models import ClaimRecord

    claim = ClaimRecord(
        claim_id="claim-gw",
        topic_id="librpa-gw",
        statement="The self-energy kernel reproduces the GW benchmark.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="formula-code translation",
    )

    recommendations = suggest_tool_executors_for_claim(claim)

    assert recommendations
    assert recommendations[0]["domain"] == "gw_librpa"
    assert recommendations[0]["executor_id"] == "metric_table_check"
    assert "code_state_ids" in recommendations[0].get("required_context_refs", [])
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_domain_packs.py::test_gw_domain_pack_recommends_code_method_executor -q
```

Expected: fail until GW recommendations include safe executor metadata.

- [ ] **Step 3: Implement pack recommendation**

Add the recommendation inside `builtin_domain_packs()`; filter recommendations by `claim.evidence_profile`.

## Task 2: Execution Brief Surfaces Missing Evidence Executor

**Files:**
- Modify: `tests/test_v5_domain_packs.py`
- Modify: `brain/v5/brief.py`

- [ ] **Step 1: Write the failing test**

```python
def test_rigorous_code_claim_brief_recommends_executor_for_missing_evidence(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The self-energy kernel reproduces the GW benchmark.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="formula-code translation",
    )
    bind_session(ws, "s1", topic_id="librpa-gw", context_id="gw-methods", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    assert any(action["action"] == "execute_recommended_tool" for action in brief["next_action_candidates"])
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_domain_packs.py::test_rigorous_code_claim_brief_recommends_executor_for_missing_evidence -q
```

Expected: fail until brief action selection consults domain pack recommendations.

- [ ] **Step 3: Implement brief recommendation**

Use `suggest_tool_executors_for_claim(claim)` and match recommendations against missing action-budget outputs. The brief action must include `executor_id`, `recipe_id`, `supports_outputs`, and `input_schema`.

## Task 3: Domain Tool Run Produces Evidence

**Files:**
- Modify: `tests/test_v5_evidence_tools.py`
- Modify: `brain/v5/tool_executors.py`
- Modify: `brain/v5/evidence.py`

- [ ] **Step 1: Write the failing test**

```python
def test_metric_table_executor_creates_linked_evidence(tmp_path):
    from brain.v5.tool_executors import execute_registered_tool_result
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Counting matches the expected edge sequence.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size aliasing",
    )

    result = execute_registered_tool_result(
        ws,
        executor_id="metric_table_check",
        recipe_id="recipe-fqhe-counting-table",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        inputs={"metrics": [{"name": "level-0", "observed": 1, "expected": 1, "tolerance": 0}]},
        evidence_status="supports",
        supports_outputs=["evidence_or_provenance", "minimal_check"],
        evidence_type="toy_numeric",
    )

    assert result.tool_run.status == "passed"
    assert result.evidence is not None
    assert result.evidence.status == "supports"
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_evidence_tools.py::test_metric_table_executor_creates_linked_evidence -q
```

Expected: fail until executor result writes linked evidence.

- [ ] **Step 3: Verify and commit**

```powershell
pytest tests\test_v5_domain_packs.py tests\test_v5_evidence_tools.py tests\test_v5_real_workflows.py -q
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
git add brain/v5/domain_packs.py brain/v5/brief.py brain/v5/tool_executors.py brain/v5/evidence.py tests/test_v5_domain_packs.py tests/test_v5_evidence_tools.py tests/test_v5_real_workflows.py
git commit -m "feat(v5): add domain tool recommendations"
git push origin codex/aitp-v5-kernel-mvp
git push origin HEAD:main
```
