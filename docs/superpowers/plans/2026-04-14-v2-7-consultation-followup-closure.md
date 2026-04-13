# v2.7 Consultation-Followup Selection Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `consultation_followup` executable, durable, and able to select one bounded topic-local staged candidate so `next` / `status` advance beyond the generic consult prompt.

**Architecture:** Add one focused consultation-followup helper module, wire one service-level auto-action executor around existing `consult_l2(record_consultation=True)`, and make orchestration switch from generic `consultation_followup` to a candidate-specific follow-up action when the new selection artifact exists. Keep the milestone bounded: consult and candidate selection are automatic; deeper execution remains manual.

**Tech Stack:** Python 3.12, `pytest`, existing AITP runtime scripts, `consult_canonical_l2`, runtime topic artifacts, JSON + Markdown projections.

---

### Task 1: Reproduce The Dead-End With Failing Tests

**Files:**
- Modify: `research/knowledge-hub/tests/test_runtime_scripts.py`
- Modify: `research/knowledge-hub/tests/test_aitp_service.py`

- [ ] **Step 1: Write the failing isolated acceptance test**

```python
def test_consultation_followup_selection_acceptance_script_runs_on_isolated_work_root(self) -> None:
    with patch.object(
        sys,
        "argv",
        [
            "run_consultation_followup_selection_acceptance.py",
            "--work-root",
            str(work_root),
            "--register-arxiv-id",
            "2401.00001v2",
            "--registration-metadata-json",
            str(metadata_path),
            "--json",
        ],
    ):
        exit_code = self.consultation_followup_selection_acceptance.main()

    self.assertEqual(exit_code, 0)
```

- [ ] **Step 2: Write the failing service test**

```python
def test_execute_auto_actions_runs_consultation_followup_and_writes_selection_artifact(self) -> None:
    payload = self.service._execute_auto_actions(
        topic_slug="demo-topic",
        updated_by="aitp-cli",
        max_auto_steps=1,
        default_skill_queries=None,
    )
    self.assertEqual(payload["executed"][0]["action_type"], "consultation_followup")
    self.assertTrue(
        (self.service._runtime_root("demo-topic") / "consultation_followup_selection.active.json").exists()
    )
```

- [ ] **Step 3: Run the tests and verify they fail**

Run: `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "consultation_followup_selection_acceptance" -q`

Expected: `FAIL` because the acceptance script and route closure do not exist yet.

Run: `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "consultation_followup_and_writes_selection_artifact" -q`

Expected: `FAIL` because `execute_auto_actions()` does not support `consultation_followup`.

- [ ] **Step 4: Commit**

```bash
git add research/knowledge-hub/tests/test_runtime_scripts.py research/knowledge-hub/tests/test_aitp_service.py
git commit -m "test: cover consultation followup closure gap"
```

### Task 2: Add Focused Consultation-Followup Helpers

**Files:**
- Create: `research/knowledge-hub/knowledge_hub/consultation_followup_support.py`
- Modify: `research/knowledge-hub/tests/test_aitp_service.py`

- [ ] **Step 1: Write the failing helper-selection test**

```python
def test_select_bounded_consultation_candidate_prefers_topic_local_staged_hits(self) -> None:
    payload = {
        "staged_hits": [
            {"entry_id": "staging:topic-local", "topic_slug": "demo-topic", "title": "Local note", "path": "canonical/staging/entries/topic-local.json", "trust_surface": "staging"},
            {"entry_id": "staging:other-topic", "topic_slug": "other-topic", "title": "Other note", "path": "canonical/staging/entries/other-topic.json", "trust_surface": "staging"},
        ]
    }
    selected = select_bounded_consultation_candidate(topic_slug="demo-topic", consult_payload=payload)
    self.assertEqual(selected["selected_candidate_id"], "staging:topic-local")
    self.assertEqual(selected["status"], "selected")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "prefers_topic_local_staged_hits" -q`

Expected: `FAIL` because the helper module does not exist yet.

- [ ] **Step 3: Write the minimal helper module**

```python
def derive_consultation_followup_query(*, topic_slug: str, topic_state: dict[str, Any], research_question_contract: dict[str, Any] | None) -> str:
    for candidate in (
        str((research_question_contract or {}).get("question") or "").strip(),
        str((research_question_contract or {}).get("title") or "").strip(),
        str(topic_state.get("title") or "").strip(),
        topic_slug.replace("-", " "),
    ):
        if candidate:
            return candidate
    return topic_slug.replace("-", " ")


def select_bounded_consultation_candidate(*, topic_slug: str, consult_payload: dict[str, Any]) -> dict[str, Any]:
    topic_local = [
        row for row in (consult_payload.get("staged_hits") or [])
        if str((row or {}).get("topic_slug") or "").strip() == topic_slug
    ]
    if not topic_local:
        return {"status": "no_selection", "selected_candidate_id": "", "selection_reason": "No topic-local staged hit was available."}
    winner = topic_local[0]
    return {
        "status": "selected",
        "selected_candidate_id": str(winner.get("entry_id") or winner.get("id") or ""),
        "selected_candidate_title": str(winner.get("title") or ""),
        "selected_candidate_path": str(winner.get("path") or ""),
        "selected_candidate_trust_surface": str(winner.get("trust_surface") or ""),
        "selected_candidate_topic_slug": str(winner.get("topic_slug") or ""),
        "selection_reason": "Selected the first topic-local staged hit from the bounded consultation result.",
    }
```

- [ ] **Step 4: Add selection payload and note renderers**

```python
def consultation_followup_selection_paths(runtime_root: Path) -> dict[str, Path]:
    return {
        "json": runtime_root / "consultation_followup_selection.active.json",
        "note": runtime_root / "consultation_followup_selection.active.md",
    }


def build_consultation_followup_selection_payload(
    *,
    topic_slug: str,
    run_id: str | None,
    query_text: str,
    retrieval_profile: str,
    consultation_paths: dict[str, str],
    consult_payload: dict[str, Any],
    selected: dict[str, Any],
    updated_by: str,
) -> dict[str, Any]:
    return {
        "topic_slug": topic_slug,
        "run_id": run_id,
        "status": selected["status"],
        "query_text": query_text,
        "retrieval_profile": retrieval_profile,
        "consultation_index_path": str(consultation_paths.get("consultation_index_path") or ""),
        "consultation_result_path": str(consultation_paths.get("consultation_result_path") or ""),
        "selected_candidate_id": selected.get("selected_candidate_id") or "",
        "selected_candidate_title": selected.get("selected_candidate_title") or "",
        "selected_candidate_path": selected.get("selected_candidate_path") or "",
        "selected_candidate_trust_surface": selected.get("selected_candidate_trust_surface") or "",
        "selected_candidate_topic_slug": selected.get("selected_candidate_topic_slug") or "",
        "selection_reason": selected.get("selection_reason") or "",
        "primary_hit_count": len(consult_payload.get("primary_hits") or []),
        "staged_hit_count": len(consult_payload.get("staged_hits") or []),
        "updated_by": updated_by,
    }


def render_consultation_followup_selection_markdown(payload: dict[str, Any]) -> str:
    return (
        "# Consultation followup selection\\n\\n"
        f"- Status: `{payload['status']}`\\n"
        f"- Query: `{payload['query_text']}`\\n"
        f"- Retrieval profile: `{payload['retrieval_profile']}`\\n"
        f"- Selected candidate: `{payload.get('selected_candidate_id') or '(none)'}`\\n"
        f"- Reason: {payload['selection_reason']}\\n"
    )
```

- [ ] **Step 5: Run the helper test to verify it passes**

Run: `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "prefers_topic_local_staged_hits" -q`

Expected: `PASS`

- [ ] **Step 6: Commit**

```bash
git add research/knowledge-hub/knowledge_hub/consultation_followup_support.py research/knowledge-hub/tests/test_aitp_service.py
git commit -m "feat: add consultation followup selection helpers"
```

### Task 3: Execute Consultation-Followup Inside The Auto Loop

**Files:**
- Modify: `research/knowledge-hub/knowledge_hub/aitp_service.py`
- Modify: `research/knowledge-hub/knowledge_hub/auto_action_support.py`
- Modify: `research/knowledge-hub/tests/test_aitp_service.py`

- [ ] **Step 1: Write the failing service-level executor test**

```python
def test_run_consultation_followup_records_consultation_receipt_and_selection(self) -> None:
    payload = self.service._run_consultation_followup(
        topic_slug="demo-topic",
        row={"handler_args": {"run_id": "demo-run"}, "action_type": "consultation_followup"},
        updated_by="aitp-cli",
    )
    self.assertIn("consultation", payload)
    self.assertIn("selection", payload)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "records_consultation_receipt_and_selection" -q`

Expected: `FAIL` because `_run_consultation_followup()` does not exist yet.

- [ ] **Step 3: Implement `_run_consultation_followup()`**

```python
def _run_consultation_followup(self, *, topic_slug: str, row: dict[str, Any], updated_by: str) -> dict[str, Any]:
    run_id = str((row.get("handler_args") or {}).get("run_id") or self._resolve_run_id(topic_slug, None) or "").strip() or None
    topic_state = self.get_runtime_state(topic_slug)
    research_question_contract = read_json(self._runtime_root(topic_slug) / "research_question.contract.json")
    query_text = derive_consultation_followup_query(
        topic_slug=topic_slug,
        topic_state=topic_state,
        research_question_contract=research_question_contract,
    )
    consult_payload = self.consult_l2(
        query_text=query_text,
        retrieval_profile="l1_provisional_understanding",
        include_staging=True,
        topic_slug=topic_slug,
        stage="L3",
        run_id=run_id,
        updated_by=updated_by,
        record_consultation=True,
    )
    selected = select_bounded_consultation_candidate(topic_slug=topic_slug, consult_payload=consult_payload)
    selection_payload = build_consultation_followup_selection_payload(
        topic_slug=topic_slug,
        run_id=run_id,
        query_text=query_text,
        retrieval_profile="l1_provisional_understanding",
        consultation_paths=consult_payload["consultation"],
        consult_payload=consult_payload,
        selected=selected,
        updated_by=updated_by,
    )
    paths = consultation_followup_selection_paths(self._runtime_root(topic_slug))
    write_json(paths["json"], selection_payload)
    write_text(paths["note"], render_consultation_followup_selection_markdown(selection_payload))
    return {"consultation": consult_payload["consultation"], "selection": selection_payload}
```

- [ ] **Step 4: Teach `execute_auto_actions()` the new branch**

```python
elif action_type == "consultation_followup":
    result = self._run_consultation_followup(
        topic_slug=topic_slug,
        row=row,
        updated_by=updated_by,
    )
```

- [ ] **Step 5: Run the targeted tests**

Run: `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "consultation_followup" -q`

Expected: `PASS`

- [ ] **Step 6: Commit**

```bash
git add research/knowledge-hub/knowledge_hub/aitp_service.py research/knowledge-hub/knowledge_hub/auto_action_support.py research/knowledge-hub/tests/test_aitp_service.py
git commit -m "feat: execute consultation followup auto action"
```

### Task 4: Advance Queue Materialization To A Candidate-Specific Follow-Up

**Files:**
- Modify: `research/knowledge-hub/runtime/scripts/orchestrate_topic.py`
- Modify: `research/knowledge-hub/runtime/scripts/orchestrator_contract_support.py`
- Modify: `research/knowledge-hub/runtime/scripts/sync_topic_state.py`
- Modify: `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
- Modify: `research/knowledge-hub/tests/test_runtime_scripts.py`

- [ ] **Step 1: Write the failing next/status advancement test**

```python
def test_advances_from_consultation_followup_to_selected_candidate_summary(self) -> None:
    payload = self.consultation_followup_selection_acceptance.main()
    self.assertEqual(payload["next"]["selected_action_type"], "selected_consultation_candidate_followup")
    self.assertIn("Review the selected staged candidate", payload["next"]["selected_action_summary"])
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "selected_candidate_summary" -q`

Expected: `FAIL` because orchestration still returns the generic consultation action.

- [ ] **Step 3: Make `consultation_followup` auto-runnable in the narrow `v2.7` lane**

```python
"action_type": "consultation_followup",
"summary": "Consult the topic-local staged L2 memory and choose one bounded candidate before deeper execution.",
"auto_runnable": True,
"handler_args": {"run_id": topic_state.get("latest_run_id")},
```

- [ ] **Step 4: Replace the generic consult action when a selection artifact exists**

```python
if selection_payload and str(selection_payload.get("status") or "") == "selected":
    queue.append(
        {
            "action_id": f"action:{topic_state['topic_slug']}:selected-consultation-candidate",
            "topic_slug": topic_state["topic_slug"],
            "resume_stage": topic_state["resume_stage"],
            "status": "pending",
            "action_type": "selected_consultation_candidate_followup",
            "summary": (
                f"Review the selected staged candidate `{selection_payload['selected_candidate_id']}` "
                "and decide whether to split, validate, or promote it before deeper execution."
            ),
            "auto_runnable": False,
            "handler_args": {"candidate_id": selection_payload["selected_candidate_id"]},
        }
    )
```

- [ ] **Step 5: Add runtime pointers and must-read support**

```python
"selected_consultation_candidate_path": relative_path(topic_runtime_root / "consultation_followup_selection.active.json", knowledge_root),
"selected_consultation_candidate_note_path": relative_path(topic_runtime_root / "consultation_followup_selection.active.md", knowledge_root),
```

```python
if selected_action_type == "selected_consultation_candidate_followup" and selected_consultation_candidate_note_path:
    must_read_now.insert(0, {"path": selected_consultation_candidate_note_path, "reason": "Read the durable consultation-followup selection before choosing the next deeper candidate action."})
```

- [ ] **Step 6: Run the runtime tests**

Run: `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "consultation_followup_selection_acceptance or selected_candidate_summary" -q`

Expected: `PASS`

- [ ] **Step 7: Commit**

```bash
git add research/knowledge-hub/runtime/scripts/orchestrate_topic.py research/knowledge-hub/runtime/scripts/orchestrator_contract_support.py research/knowledge-hub/runtime/scripts/sync_topic_state.py research/knowledge-hub/knowledge_hub/runtime_bundle_support.py research/knowledge-hub/tests/test_runtime_scripts.py
git commit -m "feat: advance consultation followup to selected candidate"
```

### Task 5: Add One Isolated Acceptance Script And Re-Run The Chain

**Files:**
- Create: `research/knowledge-hub/runtime/scripts/run_consultation_followup_selection_acceptance.py`
- Modify: `research/knowledge-hub/tests/test_runtime_scripts.py`

- [ ] **Step 1: Write the failing acceptance script**

```python
def main() -> int:
    raise SystemExit("not implemented")
```

- [ ] **Step 2: Run the acceptance test to verify it fails**

Run: `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "consultation_followup_selection_acceptance" -q`

Expected: `FAIL`

- [ ] **Step 3: Implement the acceptance script**

```python
check(
    str(post_consult_next.get("selected_action_type") or "") == "selected_consultation_candidate_followup",
    "Expected `next` to advance from consultation_followup to the selected candidate summary.",
)
check(
    "Review the selected staged candidate" in str(post_consult_next.get("selected_action_summary") or ""),
    "Expected `next` summary to name the selected staged candidate.",
)
check(selection_payload_path.exists(), "Expected consultation_followup_selection.active.json to be materialized.")
```

- [ ] **Step 4: Run the regression slice**

Run: `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "consultation_followup_selection_acceptance or staged_l2_advancement_acceptance_script_runs_on_isolated_work_root or staged_l2_reentry_acceptance_script_runs_on_isolated_work_root or first_source_followthrough_acceptance_script_runs_on_isolated_work_root" -q`

Expected: `PASS`

Run: `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "consultation_followup or continue_recorded_as_steady" -q`

Expected: `PASS`

Run: `python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "continue_recorded_h_plane_as_steady" -q`

Expected: `PASS`

Run: `node D:/BaiduSyncdisk/Theoretical-Physics/.codex-home/get-shit-done/bin/gsd-tools.cjs roadmap analyze`

Expected: current milestone phases parse cleanly with no missing details.

- [ ] **Step 5: Commit**

```bash
git add research/knowledge-hub/runtime/scripts/run_consultation_followup_selection_acceptance.py research/knowledge-hub/tests/test_runtime_scripts.py
git commit -m "test: prove consultation followup selection closure"
```

## Self-Review

- Spec coverage: helper selection, auto execution, durable receipts, candidate-specific `next/status`, and regression all map to Tasks 1-5.
- Placeholder scan: no unresolved placeholders remain.
- Type consistency: `consultation_followup_selection.active.json|md`, `consultation_followup`, and `selected_consultation_candidate_followup` are used consistently across all tasks.

Plan complete and saved to `docs/superpowers/plans/2026-04-14-v2-7-consultation-followup-closure.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
