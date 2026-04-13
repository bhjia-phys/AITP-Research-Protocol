from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _bootstrap_loop_context(
    self,
    *,
    topic_slug: str | None,
    topic: str | None,
    statement: str | None,
    run_id: str | None,
    control_note: str | None,
    updated_by: str,
    human_request: str | None,
    skill_queries: list[str] | None,
    research_mode: str | None,
) -> dict[str, Any]:
    scheduler_selection = None
    resolved_topic_slug = topic_slug
    if not resolved_topic_slug and not topic:
        scheduler_selection = self.select_next_topic(updated_by=updated_by)
        resolved_topic_slug = str(scheduler_selection.get("selected_topic_slug") or "").strip() or None
        if not resolved_topic_slug:
            raise ValueError("Provide topic_slug or topic.")

    active_control_note = control_note
    bootstrap = self.orchestrate(
        topic_slug=resolved_topic_slug,
        topic=topic,
        statement=statement,
        run_id=run_id,
        control_note=active_control_note,
        updated_by=updated_by,
        human_request=human_request,
        skill_queries=skill_queries or [],
        research_mode=research_mode,
    )
    resolved_topic_slug = bootstrap["topic_slug"]
    resolved_run_id = self._resolve_run_id(resolved_topic_slug, run_id)
    steering_artifacts = self.materialize_steering_from_human_request(
        topic_slug=resolved_topic_slug,
        run_id=resolved_run_id,
        human_request=human_request,
        updated_by=updated_by,
        topic_state=bootstrap.get("topic_state"),
        control_note=active_control_note,
    )
    if steering_artifacts.get("requires_reorchestrate"):
        active_control_note = str(steering_artifacts.get("control_note_path") or active_control_note or "").strip() or active_control_note
        bootstrap = self.orchestrate(
            topic_slug=resolved_topic_slug,
            run_id=resolved_run_id,
            control_note=active_control_note,
            updated_by=updated_by,
            skill_queries=skill_queries or [],
            human_request=human_request,
            research_mode=research_mode,
        )
        resolved_run_id = self._resolve_run_id(resolved_topic_slug, run_id)

    return {
        "scheduler_selection": scheduler_selection,
        "bootstrap": bootstrap,
        "resolved_topic_slug": resolved_topic_slug,
        "resolved_run_id": resolved_run_id,
        "active_control_note": active_control_note,
        "steering_artifacts": steering_artifacts,
    }


def _execute_loop_auto_actions(
    self,
    *,
    topic_slug: str,
    run_id: str | None,
    active_control_note: str | None,
    updated_by: str,
    human_request: str | None,
    skill_queries: list[str] | None,
    max_auto_steps: int,
    research_mode: str | None,
) -> dict[str, Any]:
    executed_auto_actions: list[dict[str, Any]] = []
    auto_queue_path = str(self._runtime_root(topic_slug) / "action_queue.jsonl")
    remaining_pending = 0
    remaining_budget = max_auto_steps

    while remaining_budget > 0:
        auto_step = self._execute_auto_actions(
            topic_slug=topic_slug,
            updated_by=updated_by,
            max_auto_steps=1,
            default_skill_queries=skill_queries,
        )
        auto_queue_path = auto_step["queue_path"]
        remaining_pending = auto_step["remaining_pending"]
        if not auto_step["executed"]:
            break
        executed_auto_actions.extend(auto_step["executed"])
        remaining_budget -= 1
        if any(step.get("status") != "completed" for step in auto_step["executed"]):
            break
        if remaining_budget <= 0:
            break
        self.orchestrate(
            topic_slug=topic_slug,
            run_id=run_id,
            control_note=active_control_note,
            updated_by=updated_by,
            skill_queries=skill_queries or [],
            human_request=human_request,
            research_mode=research_mode,
        )

    if executed_auto_actions:
        self.orchestrate(
            topic_slug=topic_slug,
            run_id=run_id,
            control_note=active_control_note,
            updated_by=updated_by,
            skill_queries=skill_queries or [],
            human_request=human_request,
            research_mode=research_mode,
        )
        auto_queue_path = str(self._runtime_root(topic_slug) / "action_queue.jsonl")
        remaining_pending = sum(
            1
            for row in _read_jsonl(Path(auto_queue_path))
            if str(row.get("status") or "").strip() == "pending"
        )

    return {
        "queue_path": auto_queue_path,
        "executed": executed_auto_actions,
        "remaining_pending": remaining_pending,
    }


def _resolve_loop_auto_step_budget(
    self,
    *,
    topic_slug: str,
    updated_by: str,
    human_request: str | None,
    requested_max_auto_steps: int,
    load_profile: str | None,
) -> dict[str, Any]:
    if requested_max_auto_steps <= 0:
        return {
            "requested_max_auto_steps": requested_max_auto_steps,
            "applied_max_auto_steps": requested_max_auto_steps,
            "auto_step_budget_reason": "explicit_budget_disabled",
        }

    preview_protocol = self._materialize_runtime_protocol_bundle(
        topic_slug=topic_slug,
        updated_by=updated_by,
        human_request=human_request,
        load_profile=load_profile,
        requested_max_auto_steps=requested_max_auto_steps,
        applied_max_auto_steps=requested_max_auto_steps,
        auto_step_budget_reason="requested_budget",
    )
    bundle_path = Path(preview_protocol["runtime_protocol_path"])
    bundle = json.loads(bundle_path.read_text(encoding="utf-8")) if bundle_path.exists() else {}
    human_posture = bundle.get("human_interaction_posture") or {}
    runtime_mode = str(bundle.get("runtime_mode") or "")
    active_submode = str(bundle.get("active_submode") or "")

    applied_max_auto_steps = requested_max_auto_steps
    auto_step_budget_reason = "requested_budget"
    if bool(human_posture.get("requires_human_input_now")):
        auto_step_budget_reason = "human_checkpoint_active"
    elif runtime_mode == "verify" and active_submode == "iterative_verify":
        applied_max_auto_steps = max(requested_max_auto_steps, 16)
        auto_step_budget_reason = "iterative_verify_auto_extension"

    return {
        "requested_max_auto_steps": requested_max_auto_steps,
        "applied_max_auto_steps": applied_max_auto_steps,
        "auto_step_budget_reason": auto_step_budget_reason,
    }


def _finalize_loop_outcome(
    self,
    *,
    bootstrap: dict[str, Any],
    topic_slug: str,
    run_id: str | None,
    updated_by: str,
    human_request: str | None,
    max_auto_steps: int,
    applied_max_auto_steps: int,
    auto_step_budget_reason: str,
    load_profile: str | None,
    entry_audit: dict[str, Any],
    auto_actions: dict[str, Any],
    steering_artifacts: dict[str, Any],
    scheduler_selection: dict[str, Any] | None,
) -> dict[str, Any]:
    capability = self.capability_audit(topic_slug=topic_slug, updated_by=updated_by)
    trust = None
    if run_id:
        try:
            trust = self.audit_operation_trust(
                topic_slug=topic_slug,
                run_id=run_id,
                updated_by=updated_by,
            )
        except FileNotFoundError:
            trust = None
    exit_audit = self.audit(topic_slug=topic_slug, phase="exit", updated_by=updated_by)
    current_topic_memory = self.remember_current_topic(
        topic_slug=topic_slug,
        updated_by=updated_by,
        source="run_topic_loop",
        human_request=human_request,
    )

    loop_state = {
        "topic_slug": topic_slug,
        "run_id": run_id,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "human_request": human_request or "",
        "max_auto_steps": max_auto_steps,
        "requested_max_auto_steps": max_auto_steps,
        "applied_max_auto_steps": applied_max_auto_steps,
        "auto_step_budget_reason": auto_step_budget_reason,
        "bootstrap_runtime_root": bootstrap["runtime_root"],
        "entry_conformance": (entry_audit.get("conformance_state") or {}).get("overall_status"),
        "exit_conformance": (exit_audit.get("conformance_state") or {}).get("overall_status"),
        "capability_status": capability.get("overall_status"),
        "trust_status": trust.get("overall_status") if trust else "missing",
        "promotion_gate_status": str((self._load_promotion_gate(topic_slug) or {}).get("status") or "not_requested"),
        "auto_actions_executed": auto_actions["executed"],
        "remaining_pending_actions": auto_actions["remaining_pending"],
        "steering": steering_artifacts,
        "current_topic_memory": current_topic_memory,
    }
    resolved_load_profile, load_profile_reason = self._resolve_load_profile(
        explicit_load_profile=load_profile,
        human_request=human_request,
        topic_state=bootstrap.get("topic_state"),
    )
    self._persist_load_profile_state(
        topic_slug=topic_slug,
        load_profile=resolved_load_profile,
        reason=load_profile_reason,
        updated_by=updated_by,
    )
    loop_state["load_profile"] = resolved_load_profile
    loop_state["load_profile_reason"] = load_profile_reason

    loop_state_path = self._loop_state_path(topic_slug)
    loop_history_path = self._loop_history_path(topic_slug)
    _write_json(loop_state_path, loop_state)
    history_rows = _read_jsonl(loop_history_path)
    history_rows.append(loop_state)
    _write_jsonl(loop_history_path, history_rows)
    protocol_paths = self._materialize_runtime_protocol_bundle(
        topic_slug=topic_slug,
        updated_by=updated_by,
        human_request=human_request,
        load_profile=resolved_load_profile,
        requested_max_auto_steps=max_auto_steps,
        applied_max_auto_steps=applied_max_auto_steps,
        auto_step_budget_reason=auto_step_budget_reason,
    )
    runtime_bundle = _read_json(Path(protocol_paths["runtime_protocol_path"])) or {}
    loop_state["loop_detection"] = runtime_bundle.get("loop_detection") or {}
    _write_json(loop_state_path, loop_state)
    history_rows[-1] = loop_state
    _write_jsonl(loop_history_path, history_rows)
    return {
        "topic_slug": topic_slug,
        "run_id": run_id,
        "load_profile": resolved_load_profile,
        "scheduler": scheduler_selection,
        "bootstrap": bootstrap,
        "entry_audit": entry_audit,
        "auto_actions": auto_actions,
        "capability_audit": capability,
        "trust_audit": trust,
        "exit_audit": exit_audit,
        "loop_state_path": str(loop_state_path),
        "loop_history_path": str(loop_history_path),
        "loop_state": loop_state,
        "steering_artifacts": steering_artifacts,
        "current_topic_memory": current_topic_memory,
        "runtime_protocol": protocol_paths,
    }


def run_topic_loop(
    self,
    *,
    topic_slug: str | None = None,
    topic: str | None = None,
    statement: str | None = None,
    run_id: str | None = None,
    control_note: str | None = None,
    updated_by: str = "aitp-cli",
    human_request: str | None = None,
    skill_queries: list[str] | None = None,
    max_auto_steps: int = 4,
    research_mode: str | None = None,
    load_profile: str | None = None,
) -> dict[str, Any]:
    loop_context = _bootstrap_loop_context(
        self,
        topic_slug=topic_slug,
        topic=topic,
        statement=statement,
        run_id=run_id,
        control_note=control_note,
        updated_by=updated_by,
        human_request=human_request,
        skill_queries=skill_queries,
        research_mode=research_mode,
    )
    resolved_topic_slug = loop_context["resolved_topic_slug"]
    resolved_run_id = loop_context["resolved_run_id"]
    entry_audit = self.audit(topic_slug=resolved_topic_slug, phase="entry", updated_by=updated_by)
    auto_step_budget = _resolve_loop_auto_step_budget(
        self,
        topic_slug=resolved_topic_slug,
        updated_by=updated_by,
        human_request=human_request,
        requested_max_auto_steps=max_auto_steps,
        load_profile=load_profile,
    )
    auto_actions = _execute_loop_auto_actions(
        self,
        topic_slug=resolved_topic_slug,
        run_id=resolved_run_id,
        active_control_note=loop_context["active_control_note"],
        updated_by=updated_by,
        human_request=human_request,
        skill_queries=skill_queries,
        max_auto_steps=auto_step_budget["applied_max_auto_steps"],
        research_mode=research_mode,
    )
    return _finalize_loop_outcome(
        self,
        bootstrap=loop_context["bootstrap"],
        topic_slug=resolved_topic_slug,
        run_id=resolved_run_id,
        updated_by=updated_by,
        human_request=human_request,
        max_auto_steps=max_auto_steps,
        applied_max_auto_steps=auto_step_budget["applied_max_auto_steps"],
        auto_step_budget_reason=auto_step_budget["auto_step_budget_reason"],
        load_profile=load_profile,
        entry_audit=entry_audit,
        auto_actions=auto_actions,
        steering_artifacts=loop_context["steering_artifacts"],
        scheduler_selection=loop_context["scheduler_selection"],
    )
