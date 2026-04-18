from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .topic_truth_root_support import compatibility_projection_path
from .loop_detection_support import should_force_human_checkpoint
from .popup_support import detect_popup_trigger
from .mode_envelope_support import check_forbidden_shortcuts, check_layer_permission


def _read_json(path: Path) -> dict[str, Any] | None:
    target = path
    if not target.exists():
        compatibility_path = compatibility_projection_path(path)
        if compatibility_path is None or not compatibility_path.exists():
            return None
        target = compatibility_path
    return json.loads(target.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    rendered = "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(rendered, encoding="utf-8")


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def execute_auto_actions(
    self,
    *,
    topic_slug: str,
    updated_by: str,
    max_auto_steps: int,
    default_skill_queries: list[str] | None,
) -> dict[str, Any]:
    queue_path, queue_rows = self._load_action_queue(topic_slug)
    operator_checkpoint = _read_json(self._operator_checkpoint_paths(topic_slug)["json"]) or {}
    if str(operator_checkpoint.get("status") or "").strip() == "requested":
        remaining = sum(1 for row in queue_rows if row.get("status") == "pending")
        return {
            "queue_path": str(queue_path),
            "executed": [],
            "remaining_pending": remaining,
            "checkpoint_blocking": True,
            "checkpoint_kind": str(operator_checkpoint.get("checkpoint_kind") or ""),
            "checkpoint_note_path": str(operator_checkpoint.get("note_path") or ""),
        }

    stuckness = should_force_human_checkpoint(self, topic_slug, updated_by=updated_by)
    if stuckness.get("force_human_checkpoint"):
        remaining = sum(1 for row in queue_rows if row.get("status") == "pending")
        return {
            "queue_path": str(queue_path),
            "executed": [],
            "remaining_pending": remaining,
            "stuckness_blocking": True,
            "stuckness_reason": stuckness.get("reason") or "repeated_action_pattern",
            "stuckness_recommendation": stuckness.get("recommendation") or "",
        }

    popup_check = detect_popup_trigger(
        topic_slug=topic_slug,
        promotion_gate=_read_json(self._promotion_gate_paths(topic_slug)["json"]),
        operator_checkpoint=operator_checkpoint,
        pending_decision_points=[],
        h_plane_payload=None,
    )
    if popup_check.get("needs_popup"):
        remaining = sum(1 for row in queue_rows if row.get("status") == "pending")
        return {
            "queue_path": str(queue_path),
            "executed": [],
            "remaining_pending": remaining,
            "popup_blocking": True,
            "popup_kind": popup_check.get("popup_kind") or "",
            "popup_priority": popup_check.get("priority") or 0,
            "popup_summary": popup_check.get("summary") or "",
        }

    runtime_protocol = self._materialize_runtime_protocol_bundle(
        topic_slug=topic_slug,
        updated_by=updated_by,
    )
    runtime_payload = _read_json(Path(runtime_protocol["runtime_protocol_path"])) or {}
    runtime_mode = str(runtime_payload.get("runtime_mode") or "").strip()
    transition_posture = runtime_payload.get("transition_posture") or {}
    transition_kind = str(transition_posture.get("transition_kind") or "").strip()
    transition_reason = str(transition_posture.get("transition_reason") or "").strip()
    transition_triggers = {
        str(item).strip()
        for item in (transition_posture.get("triggered_by") or [])
        if str(item).strip()
    }
    allowed_backedge_auto_actions: set[str] = set()
    if "capability_gap_blocker" in transition_triggers:
        allowed_backedge_auto_actions.add("skill_discovery")
    if "non_trivial_consultation" in transition_triggers:
        allowed_backedge_auto_actions.add("consultation_followup")
    queue_rows = self._maybe_append_literature_intake_stage_action(
        topic_slug=topic_slug,
        queue_rows=queue_rows,
        runtime_payload=runtime_payload,
    )

    executed: list[dict[str, Any]] = []
    steps_used = 0

    for row in queue_rows:
        if row.get("status") != "pending":
            continue
        action_type = row.get("action_type")
        if not row.get("auto_runnable"):
            if action_type == "consultation_followup" and self._consultation_followup_auto_ready(topic_slug):
                row["auto_runnable"] = True
            else:
                continue
        if steps_used >= max_auto_steps:
            continue
        if transition_kind == "backedge_transition" and action_type not in allowed_backedge_auto_actions:
            continue
        shortcut_check = check_forbidden_shortcuts(
            runtime_mode=runtime_mode,
            action_type=str(action_type or ""),
            action_summary=str(row.get("summary") or ""),
        )
        if not shortcut_check.get("allowed"):
            continue
        explicit_layer = str((row.get("handler_args") or {}).get("layer") or "").strip()
        if explicit_layer:
            layer_check = check_layer_permission(runtime_mode=runtime_mode, target_layer=explicit_layer)
            if not layer_check.get("allowed"):
                continue
        started_at = _now_iso()
        result: dict[str, Any]
        try:
            if action_type == "skill_discovery":
                queries = row.get("handler_args", {}).get("queries") or default_skill_queries or []
                if not queries:
                    raise RuntimeError("No skill discovery queries were provided.")
                result = self._discover_skills(
                    topic_slug=topic_slug,
                    queries=[str(query) for query in queries],
                    updated_by=updated_by,
                )
            elif action_type == "conformance_audit":
                result = self.audit(topic_slug=topic_slug, phase="entry", updated_by=updated_by)
            elif action_type == "literature_followup_search":
                result = self._run_literature_followup(
                    topic_slug=topic_slug,
                    row=row,
                    updated_by=updated_by,
                )
            elif action_type == "consultation_followup":
                result = self._run_consultation_followup(
                    topic_slug=topic_slug,
                    row=row,
                    updated_by=updated_by,
                )
            elif action_type == "literature_intake_stage":
                result = self._run_literature_intake_stage(
                    topic_slug=topic_slug,
                    row=row,
                    updated_by=updated_by,
                )
            elif action_type == "apply_candidate_split_contract":
                result = self.apply_candidate_split_contract(
                    topic_slug=topic_slug,
                    run_id=(row.get("handler_args") or {}).get("run_id"),
                    updated_by=updated_by,
                )
            elif action_type == "reactivate_deferred_candidate":
                result = self.reactivate_deferred_candidates(
                    topic_slug=topic_slug,
                    run_id=(row.get("handler_args") or {}).get("run_id"),
                    entry_id=(row.get("handler_args") or {}).get("entry_id"),
                    updated_by=updated_by,
                )
            elif action_type == "spawn_followup_subtopics":
                result = self.spawn_followup_subtopics(
                    topic_slug=topic_slug,
                    run_id=(row.get("handler_args") or {}).get("run_id"),
                    query=(row.get("handler_args") or {}).get("query"),
                    receipt_id=(row.get("handler_args") or {}).get("receipt_id"),
                    updated_by=updated_by,
                )
            elif action_type == "reintegrate_followup_subtopic":
                result = self.reintegrate_followup_subtopic(
                    topic_slug=topic_slug,
                    child_topic_slug=str((row.get("handler_args") or {}).get("child_topic_slug") or ""),
                    run_id=(row.get("handler_args") or {}).get("run_id"),
                    updated_by=updated_by,
                )
            elif action_type == "assess_topic_completion":
                result = self.assess_topic_completion(
                    topic_slug=topic_slug,
                    run_id=(row.get("handler_args") or {}).get("run_id"),
                    updated_by=updated_by,
                )
            elif action_type == "prepare_lean_bridge":
                result = self.prepare_lean_bridge(
                    topic_slug=topic_slug,
                    run_id=(row.get("handler_args") or {}).get("run_id"),
                    candidate_id=(row.get("handler_args") or {}).get("candidate_id"),
                    updated_by=updated_by,
                )
            elif action_type == "auto_promote_candidate":
                result = self.auto_promote_candidate(
                    topic_slug=topic_slug,
                    candidate_id=str((row.get("handler_args") or {}).get("candidate_id") or ""),
                    run_id=(row.get("handler_args") or {}).get("run_id"),
                    promoted_by=updated_by,
                    backend_id=(row.get("handler_args") or {}).get("backend_id"),
                    target_backend_root=(row.get("handler_args") or {}).get("target_backend_root"),
                    domain=(row.get("handler_args") or {}).get("domain"),
                    subdomain=(row.get("handler_args") or {}).get("subdomain"),
                    source_id=(row.get("handler_args") or {}).get("source_id"),
                    source_section=(row.get("handler_args") or {}).get("source_section"),
                    source_section_title=(row.get("handler_args") or {}).get("source_section_title"),
                    notes=(row.get("handler_args") or {}).get("notes"),
                )
            elif row.get("handler"):
                result = self._run_generic_auto_handler(
                    topic_slug=topic_slug,
                    row=row,
                    updated_by=updated_by,
                )
            else:
                raise RuntimeError(f"Unsupported auto action type: {action_type}")
            row["status"] = "completed"
            row["started_at"] = started_at
            row["completed_at"] = _now_iso()
            row["result"] = result
        except Exception as exc:  # noqa: BLE001
            row["status"] = "failed"
            row["started_at"] = started_at
            row["completed_at"] = _now_iso()
            row["error"] = str(exc)
            result = {"error": str(exc)}
        executed.append(
            {
                "action_id": row.get("action_id"),
                "action_type": action_type,
                "status": row.get("status"),
                "result": result,
            }
        )
        steps_used += 1

    _write_jsonl(queue_path, queue_rows)
    for action in executed:
        try:
            from .research_notebook_support import append_notebook_entry
            l3_root = self._l3_root(topic_slug)
            append_notebook_entry(
                l3_root,
                kind="auto_action",
                title=str(action.get("action_type") or "action"),
                status=str(action.get("status") or ""),
                details={
                    "action_id": action.get("action_id"),
                    "action_type": action.get("action_type"),
                },
            )
        except Exception:
            pass
    remaining = sum(1 for row in queue_rows if row.get("status") == "pending")
    if transition_kind == "backedge_transition" and not executed:
        return {
            "queue_path": str(queue_path),
            "executed": [],
            "remaining_pending": remaining,
            "transition_blocking": True,
            "runtime_mode": runtime_mode or None,
            "transition_kind": transition_kind or None,
            "transition_reason": transition_reason or None,
            "runtime_protocol_path": runtime_protocol["runtime_protocol_path"],
        }
    return {
        "queue_path": str(queue_path),
        "executed": executed,
        "remaining_pending": remaining,
    }
