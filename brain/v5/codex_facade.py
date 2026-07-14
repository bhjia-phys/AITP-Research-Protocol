'Codex App facade surfaces for compact, progressive AITP v5 use.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/codex_facade/part_01.py",
    "_compat_shards/codex_facade/part_02.py",
    "_compat_shards/codex_facade/part_03.py",
    "_compat_shards/codex_facade/part_04.py",
    "_compat_shards/codex_facade/part_05.py",
    ),
)
del _load_module_shards

from typing import Any as _Any

from brain.v5.lifecycle_facade import (
    LifecycleFacadeError as _LifecycleFacadeError,
    apply_session_closeout as _apply_session_closeout,
    coalesce_candidate_batch as _coalesce_candidate_batch,
    context_transition_receipt as _context_transition_receipt,
    plan_session_closeout as _plan_session_closeout,
    stage_candidate as _stage_candidate,
    start_session as _start_session,
)


_codex_autoroute_without_lifecycle = codex_autoroute
_codex_enter_context_without_lifecycle = codex_enter_context
_codex_expand_context_without_lifecycle = codex_expand_context
_codex_recording_step_without_lifecycle = codex_recording_step
_codex_record_apply_without_lifecycle = codex_record_apply
_codex_closeout_without_lifecycle = codex_closeout


def codex_autoroute(
    ws,
    *,
    request_summary: str,
    session_id: str = "",
    topics: list[str] | None = None,
    visible_files: list[str] | None = None,
    recent_tool_summary: str = "",
    semantic_assessment: dict[str, _Any] | None = None,
) -> dict[str, _Any]:
    payload = _codex_autoroute_without_lifecycle(
        ws,
        request_summary=request_summary,
        session_id=session_id,
        topics=topics,
        visible_files=visible_files,
        recent_tool_summary=recent_tool_summary,
        semantic_assessment=semantic_assessment,
    )
    payload["disclosure_level"] = "route_hint"
    payload["context_receipt"] = _context_transition_receipt(
        session_id,
        "request",
        "route_hint",
    )
    payload.pop("resume_card", None)
    return payload


def codex_enter_context(
    ws,
    *,
    session_id: str = "",
    topics: list[str] | None = None,
    request_summary: str = "",
    process_mode: str = "auto",
    payload_profile: str = "minimal",
    max_lines: int = 60,
    candidate_limit: int = 3,
) -> dict[str, _Any]:
    payload = _codex_enter_context_without_lifecycle(
        ws,
        session_id=session_id,
        topics=topics,
        request_summary=request_summary,
        process_mode=process_mode,
        payload_profile=payload_profile,
        max_lines=max_lines,
        candidate_limit=candidate_limit,
    )
    clean_session = str(session_id or "").strip()
    if clean_session:
        try:
            started = _start_session(ws.base, clean_session)
        except _LifecycleFacadeError as exc:
            payload["session_start_error"] = f"{type(exc).__name__}: {exc}"
        else:
            payload["session_start"] = started
            payload["disclosure_level"] = "startup_orientation"
            payload["context_receipt"] = started["context_receipt"]
    return payload


def codex_expand_context(
    ws,
    *,
    session_id: str,
    expansion: str,
    claim_id: str = "",
    max_lines: int = 60,
    limit: int = 60,
    style: str = "jhep",
    objective_text: str = "",
    user_goal: str = "",
    record_refs: list[str] | tuple[str, ...] | None = None,
    offset: int = 0,
) -> dict[str, _Any]:
    payload = _codex_expand_context_without_lifecycle(
        ws,
        session_id=session_id,
        expansion=expansion,
        claim_id=claim_id,
        max_lines=max_lines,
        limit=limit,
        style=style,
        objective_text=objective_text,
        user_goal=user_goal,
        record_refs=record_refs,
        offset=offset,
    )
    selected = str(payload.get("expansion") or expansion).strip().lower().replace("-", "_")
    disclosure = "exact_expansion" if selected == "record_refs" else "normal_research"
    payload["disclosure_level"] = disclosure
    payload["context_receipt"] = _context_transition_receipt(
        session_id,
        "startup_orientation",
        disclosure,
    )
    return payload


def codex_recording_step(
    ws,
    *,
    session_id: str,
    event_type: str,
    summary: str = "",
    topic_id: str = "",
    claim_id: str = "",
    touched_refs: list[str] | None = None,
    produced_artifacts: list[str] | None = None,
    tool_call_id: str = "",
    risk_hint: str = "",
    slot: str = "",
    candidate: dict[str, _Any] | None = None,
    expected_refs: list[str] | None = None,
) -> dict[str, _Any]:
    payload = _codex_recording_step_without_lifecycle(
        ws,
        session_id=session_id,
        event_type=event_type,
        summary=summary,
        topic_id=topic_id,
        claim_id=claim_id,
        touched_refs=touched_refs,
        produced_artifacts=produced_artifacts,
        tool_call_id=tool_call_id,
        risk_hint=risk_hint,
        slot=slot,
        candidate=candidate,
        expected_refs=expected_refs,
    )
    decision = str(payload.get("classification", {}).get("decision") or "")
    payload["runtime_write_executed"] = False
    if candidate is not None and decision in {"navigate", "checkpoint"}:
        try:
            staged = _stage_candidate(ws.base, candidate)
        except Exception as exc:  # noqa: BLE001 - preserve classification on staging failure.
            payload["recording_candidate_staging_error"] = f"{type(exc).__name__}: {exc}"
        else:
            payload["recording_candidate_staging"] = staged
            payload["runtime_write_executed"] = True
    return payload


def codex_record_apply(
    ws,
    *,
    session_id: str,
    slot: str,
    payload: dict[str, _Any] | None = None,
    event_type: str = "",
    summary: str = "",
    claim_id: str = "",
    expected_refs: list[str] | None = None,
) -> dict[str, _Any]:
    selected = str(slot or "").strip().lower().replace("-", "_")
    if selected == "recording_batch":
        values = dict(payload or {})
        milestone_id = str(values.get("milestone_id") or "")
        batch = _coalesce_candidate_batch(
            ws.base,
            session_id,
            milestone_id,
            actor=values.get("actor"),
        )
        return {
            **batch,
            "kind": "codex_record_apply",
            "session_id": session_id,
            "slot": "recording_batch",
            "batch_surface": batch,
            "kernel_state_change": "recording_candidate_batch_record",
        }
    return _codex_record_apply_without_lifecycle(
        ws,
        session_id=session_id,
        slot=slot,
        payload=payload,
        event_type=event_type,
        summary=summary,
        claim_id=claim_id,
        expected_refs=expected_refs,
    )


def codex_closeout(
    ws,
    *,
    session_id: str,
    summary: str,
    apply: bool = False,
    claim_id: str = "",
    run_id: str = "",
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    changed_files: list[str] | None = None,
    generated_artifacts: list[dict] | None = None,
    validation_commands: list[str] | None = None,
    durable_observations: list[str] | None = None,
    claim_boundary: dict | None = None,
    next_blockers: list[str] | None = None,
    artifact_specs: list[dict] | None = None,
    source_specs: list[dict] | None = None,
    tool_run_specs: list[dict] | None = None,
    sensemaking_summary: str = "",
    source_refs: list[str] | None = None,
    lifecycle_request: dict[str, _Any] | None = None,
    lifecycle_plan: dict[str, _Any] | None = None,
    lifecycle_plan_id: str = "",
    lifecycle_actor: dict[str, _Any] | None = None,
) -> dict[str, _Any]:
    if lifecycle_request is not None and lifecycle_plan is not None:
        raise ValueError("lifecycle_request and lifecycle_plan are mutually exclusive")
    if lifecycle_request is not None:
        plan = _plan_session_closeout(ws.base, lifecycle_request)
        return {
            "ok": True,
            "kind": "codex_closeout",
            "mode": "lifecycle_plan",
            "session_id": session_id,
            "session_closeout_plan": plan,
            "write_executed": False,
            "kernel_state_change": "none",
            "trust_update_forbidden": True,
            "summary_inputs_trusted": False,
            "orientation_only": True,
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
        }
    if lifecycle_plan is not None:
        applied = _apply_session_closeout(
            ws.base,
            lifecycle_plan,
            lifecycle_plan_id,
            actor=lifecycle_actor,
        )
        return {
            "ok": True,
            "kind": "codex_closeout",
            "mode": "lifecycle_apply",
            "session_id": session_id,
            "session_closeout_apply": applied,
            "write_executed": True,
            "kernel_state_change": "session_closeout_record",
            "trust_update_forbidden": True,
            "summary_inputs_trusted": False,
            "orientation_only": False,
            "can_update_kernel_state": True,
            "can_update_claim_trust": False,
        }
    return _codex_closeout_without_lifecycle(
        ws,
        session_id=session_id,
        summary=summary,
        apply=apply,
        claim_id=claim_id,
        run_id=run_id,
        inputs=inputs,
        outputs=outputs,
        changed_files=changed_files,
        generated_artifacts=generated_artifacts,
        validation_commands=validation_commands,
        durable_observations=durable_observations,
        claim_boundary=claim_boundary,
        next_blockers=next_blockers,
        artifact_specs=artifact_specs,
        source_specs=source_specs,
        tool_run_specs=tool_run_specs,
        sensemaking_summary=sensemaking_summary,
        source_refs=source_refs,
    )
