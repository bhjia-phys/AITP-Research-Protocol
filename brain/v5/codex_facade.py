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


def codex_route_intent(
    ws,
    *,
    request_summary: str,
    session_id: str = "",
    topics: list[str] | None = None,
    visible_files: list[str] | None = None,
    recent_tool_summary: str = "",
    semantic_assessment: dict[str, _Any] | None = None,
) -> dict[str, _Any]:
    """Run the bounded heuristic/semantic intent guard without route resolution."""

    return _codex_autoroute_without_lifecycle(
        ws,
        request_summary=request_summary,
        session_id=session_id,
        topics=topics,
        visible_files=visible_files,
        recent_tool_summary=recent_tool_summary,
        semantic_assessment=semantic_assessment,
    )


def codex_autoroute(
    ws,
    *,
    request_summary: str,
    session_id: str = "",
    topics: list[str] | None = None,
    visible_files: list[str] | None = None,
    recent_tool_summary: str = "",
    semantic_assessment: dict[str, _Any] | None = None,
    host: str = "",
    host_session_id: str = "",
    project_root: str = "",
    current_path: str = "",
    repo_id: str = "",
    branch: str = "",
    exact_refs: list[str] | tuple[str, ...] | None = None,
    pinned_session_id: str = "",
    routing_mode: str = "dynamic",
) -> dict[str, _Any]:
    payload = codex_route_intent(
        ws,
        request_summary=request_summary,
        session_id=session_id,
        topics=topics,
        visible_files=visible_files,
        recent_tool_summary=recent_tool_summary,
        semantic_assessment=semantic_assessment,
    )
    dynamic_requested = bool(
        host
        or host_session_id
        or project_root
        or current_path
        or repo_id
        or branch
        or exact_refs
        or pinned_session_id
        or routing_mode != "dynamic"
    )
    if ws is not None and dynamic_requested:
        from brain.v5.dynamic_host_routing import resolve_host_research_route
        from brain.v5.host_route_cache import write_host_route_mapping
        from brain.v5.host_route_contracts import HostRouteRequest, route_decision_payload

        route_request = HostRouteRequest(
            request_summary=request_summary,
            host=host,
            host_session_id=host_session_id,
            project_root=project_root or str(ws.base),
            current_path=current_path,
            repo_id=repo_id,
            branch=branch,
            visible_files=tuple(visible_files or ()),
            explicit_topic_ids=tuple(topics or ()),
            explicit_session_ids=((session_id,) if session_id else ()),
            exact_refs=tuple(exact_refs or ()),
            pinned_session_id=pinned_session_id,
            routing_mode=routing_mode,
            semantic_assessment=semantic_assessment or {},
        )
        route = resolve_host_research_route(ws, route_request)
        payload["host_route_decision"] = route_decision_payload(route)
        _compose_host_route(payload, route, request_summary=request_summary)
        payload["runtime_continuity"] = {"status": "not_stored"}
        if route.status == "selected" and host and host_session_id:
            try:
                mapping = write_host_route_mapping(ws, route_request, route)
            except (OSError, TypeError, ValueError):
                payload["runtime_continuity"] = {
                    "status": "not_stored",
                    "reason": "runtime_mapping_write_failed",
                }
            else:
                payload["runtime_continuity"] = {
                    "status": "stored",
                    "namespace_sha256": mapping.namespace_sha256,
                    "index_generation": mapping.index_generation,
                    "expires_at": mapping.expires_at,
                    "canonical_write_allowed": False,
                    "can_update_claim_trust": False,
                }
    payload["disclosure_level"] = "route_hint"
    payload["context_receipt"] = _context_transition_receipt(
        str(payload.get("session_id") or session_id),
        "request",
        "route_hint",
    )
    payload.pop("resume_card", None)
    return payload


def _compose_host_route(payload, route, *, request_summary: str) -> None:
    status = route.status
    payload["canonical_write_allowed"] = False
    payload["route_status"] = status
    payload["truth_source"] = "typed_host_route_decision"
    payload["reason_codes"] = list(
        dict.fromkeys([*payload.get("reason_codes", []), *route.reason_codes])
    )
    if status == "outside_aitp":
        payload["decision"] = "answer_without_aitp"
        payload["aitp_required_before_answer"] = False
        payload["safe_to_answer_without_aitp"] = True
        payload["recommended_next_tool"] = "none"
        payload["recommended_args"] = {}
        payload["recommended_sequence"] = []
        return

    payload["aitp_required_before_answer"] = True
    payload["safe_to_answer_without_aitp"] = False
    if status == "selected":
        session_id = route.selected_session_id
        topic_id = route.selected_topic_id
        enter_args = {
            "base": "",
            "session_id": session_id,
            "topics": [topic_id],
            "request_summary": request_summary,
            "process_mode": payload.get("process_mode", "auto"),
            "payload_profile": "minimal",
        }
        payload["decision"] = "enter_existing_session"
        payload["session_id"] = session_id
        payload["topics"] = [topic_id]
        payload["recommended_next_tool"] = "aitp_v5_codex_enter"
        payload["recommended_args"] = enter_args
        payload["recommended_sequence"] = [
            {
                "tool": "aitp_v5_codex_enter",
                "arguments": enter_args,
                "state_effect": "read_only",
            },
            {
                "tool": "aitp_v5_codex_expand",
                "arguments": {
                    "base": "",
                    "session_id": session_id,
                    "expansion": "timeline",
                },
                "state_effect": "read_only",
                "condition": "after entering the exact selected session",
            },
        ]
        return
    if status == "workspace_recovery":
        payload["decision"] = "recover_workspace"
        payload["recommended_next_tool"] = "aitp_v5_codex_enter"
        payload["recommended_args"] = {
            "base": "",
            "request_summary": request_summary,
            "process_mode": payload.get("process_mode", "auto"),
            "payload_profile": "minimal",
        }
        payload["recommended_sequence"] = [
            {
                "tool": "aitp_v5_codex_enter",
                "arguments": payload["recommended_args"],
                "state_effect": "read_only",
            }
        ]
        return
    payload["decision"] = {
        "ambiguous": "choose_research_session",
        "conflict": "resolve_route_conflict",
        "coverage_blocked": "repair_route_coverage",
    }[status]
    payload["recommended_next_tool"] = "none"
    payload["recommended_args"] = {}
    payload["recommended_sequence"] = []


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
