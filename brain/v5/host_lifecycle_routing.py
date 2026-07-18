"""Resolve dynamic host lifecycle events before session-bound operations."""

from __future__ import annotations

from dataclasses import dataclass, replace

from brain.v5.dynamic_host_routing import resolve_host_research_route
from brain.v5.host_lifecycle_contracts import HostLifecycleEvent
from brain.v5.host_route_cache import (
    read_host_route_mapping,
    write_host_route_mapping,
)
from brain.v5.host_route_contracts import HostRouteRequest
from brain.v5.paths import WorkspacePaths


@dataclass(frozen=True)
class LifecycleRouteResolution:
    event: HostLifecycleEvent
    status: str
    reason_codes: tuple[str, ...]


def resolve_host_lifecycle_route(
    ws: WorkspacePaths,
    event: HostLifecycleEvent,
) -> LifecycleRouteResolution:
    if event.routing_mode != "dynamic":
        return LifecycleRouteResolution(event, "selected", ("explicit_session_pin",))

    request = _route_request(ws, event)
    if event.logical_event == "prompt_submit":
        return _resolve_fresh_prompt(ws, event, request)

    mapping = read_host_route_mapping(ws, request)
    if mapping is not None:
        if event.session_id and event.session_id != mapping.selected_session_id:
            return LifecycleRouteResolution(
                replace(event, session_id="", topic_id="", route_status="conflict"),
                "conflict",
                ("event_session_conflicts_with_runtime_route",),
            )
        return LifecycleRouteResolution(
            replace(
                event,
                session_id=mapping.selected_session_id,
                topic_id=mapping.selected_topic_id,
                route_status="selected",
            ),
            "selected",
            ("exact_runtime_route_reverified",),
        )
    if event.logical_event == "session_start":
        return _resolve_fresh_prompt(ws, event, request)
    unresolved = (
        event.route_status
        if event.route_status in {"ambiguous", "coverage_blocked", "conflict"}
        else "workspace_recovery"
    )
    return LifecycleRouteResolution(
        replace(event, session_id="", topic_id="", route_status=unresolved),
        unresolved,
        ("exact_runtime_route_required",),
    )


def _resolve_fresh_prompt(ws, event, request):
    decision = resolve_host_research_route(ws, request)
    if decision.status != "selected":
        return LifecycleRouteResolution(
            replace(
                event,
                session_id="",
                topic_id="",
                route_status=decision.status,
            ),
            decision.status,
            decision.reason_codes,
        )
    reason_codes = list(decision.reason_codes)
    if event.host and event.host_session_id:
        try:
            write_host_route_mapping(ws, _continuity_request(request), decision)
        except (OSError, TypeError, ValueError):
            reason_codes.append("runtime_route_mapping_not_stored")
    return LifecycleRouteResolution(
        replace(
            event,
            session_id=decision.selected_session_id,
            topic_id=decision.selected_topic_id,
            route_status="selected",
        ),
        "selected",
        tuple(reason_codes),
    )


def _continuity_request(request: HostRouteRequest) -> HostRouteRequest:
    return replace(
        request,
        explicit_topic_ids=(),
        explicit_session_ids=(),
        exact_refs=(),
        pinned_session_id="",
    )


def _route_request(ws, event):
    objective = event.objective_payload
    summary = str(
        objective.get("objective_text")
        or objective.get("user_goal")
        or f"research lifecycle {event.logical_event}"
    )
    research_relevant = objective.get("research_relevant", True)
    semantic = (
        {
            "task_kind": "topic_continuation",
            "needs_prior_research_state": True,
            "should_use_aitp": "required",
        }
        if research_relevant
        else {
            "task_kind": "generic_question",
            "is_generic_textbook_question": True,
            "should_use_aitp": "not_required",
        }
    )
    exact_refs = tuple(objective.get("exact_refs", ()))
    if event.logical_event in {"prompt_submit", "session_start"}:
        exact_refs = tuple(dict.fromkeys((*exact_refs, *event.subject_refs)))
    return HostRouteRequest(
        request_summary=summary,
        host=event.host,
        host_session_id=event.host_session_id,
        project_root=str(objective.get("project_root") or ws.base),
        current_path=str(objective.get("current_path") or ""),
        repo_id=str(objective.get("repo_id") or ""),
        branch=str(objective.get("branch") or ""),
        exact_refs=exact_refs,
        routing_mode="dynamic",
        semantic_assessment=semantic,
    )


__all__ = ["LifecycleRouteResolution", "resolve_host_lifecycle_route"]
