"""Normalize real host events and dispatch them through bounded v5 surfaces."""

from __future__ import annotations

import hashlib
import json
from types import MappingProxyType
from typing import Callable, Mapping

from brain.v5.context_injection_contracts import ContextInjectionRequest
from brain.v5.context_injection_events import prepare_context_injection
from brain.v5.host_lifecycle_contracts import HostLifecycleDispatch, HostLifecycleEvent
from brain.v5.host_lifecycle_normalization import normalize_host_lifecycle_event
from brain.v5.paths import WorkspacePaths
from brain.v5.research_moment_contracts import (
    ResearchEvent,
    normalize_research_event,
)
from brain.v5.research_scope_contracts import canonical_typed_ref
from brain.v5.workspace import get_session_binding


_OPERATION_ALLOWLIST = MappingProxyType(
    {
        "session_start": MappingProxyType(
            {"prepare_context_injection": "runtime_write"}
        ),
        "prompt_submit": MappingProxyType(
            {"prepare_context_injection": "runtime_write"}
        ),
        "pre_tool": MappingProxyType(
            {"delegate_existing_pre_tool_policy": "read_only"}
        ),
        "post_tool": MappingProxyType(
            {
                "append_hook_trace_event": "runtime_write",
                "delegate_existing_post_tool_trace": "read_only",
                "dispatch_validated_research_moment": "policy_bounded_write",
            }
        ),
        "session_end": MappingProxyType({"plan_session_closeout": "read_only"}),
    }
)


def host_lifecycle_operation_allowlist() -> Mapping[str, Mapping[str, str]]:
    """Return the immutable operation/effect boundary for normalized host events."""

    return _OPERATION_ALLOWLIST


def authorize_host_lifecycle_operation(
    event: HostLifecycleEvent,
    operation: str,
) -> str:
    """Return the declared effect or fail closed before any host-driven action."""

    _require_event(event)
    operation = _required_text(operation, "operation")
    effect = _OPERATION_ALLOWLIST.get(event.logical_event, {}).get(operation)
    if effect is None:
        raise PermissionError(
            f"operation {operation!r} is not allowed for {event.logical_event!r}"
        )
    return effect


def begin_research_turn(
    ws: WorkspacePaths,
    event: HostLifecycleEvent,
    *,
    deliver_context: Callable[[str], None] | None = None,
) -> HostLifecycleDispatch:
    """Prepare bounded recall only for an already-bound research session."""

    _require_event(event)
    if event.logical_event not in {"session_start", "prompt_submit"}:
        raise ValueError("begin_research_turn requires a start or prompt event")
    if deliver_context is not None and not callable(deliver_context):
        raise TypeError("deliver_context must be callable")
    authorize_host_lifecycle_operation(event, "prepare_context_injection")
    event, route_failure = _resolved_lifecycle_event(ws, event)
    if route_failure is not None:
        return route_failure
    binding, failure = _bound_session(ws, event)
    if failure is not None:
        return failure

    from brain.v5.host_lifecycle_facade import host_lifecycle_capability

    capability = host_lifecycle_capability(event.host)
    objective = event.objective_payload
    exact_refs = tuple(
        sorted(
            set(event.subject_refs)
            | set(_typed_refs(objective.get("exact_refs", ()), "exact_refs"))
        )
    )
    request = ContextInjectionRequest(
        event_id=event.event_id,
        event_type=(
            "SessionStart"
            if event.logical_event == "session_start"
            else "ResearchTurnStart"
        ),
        host=event.host,
        host_session_id=event.host_session_id,
        session_id=event.session_id,
        topic_id=binding.topic_id,
        context_profile=str(objective.get("context_profile", "auto")),
        research_relevant=objective.get("research_relevant", True),
        host_supports_session_start=any(
            item.logical_event == "session_start"
            for item in capability.automatic_events
        ),
        objective_text=str(objective.get("objective_text", "")),
        user_goal=str(objective.get("user_goal", "")),
        focus_set_ref=str(objective.get("focus_set_ref", "")),
        program_id=str(objective.get("program_id", "")),
        include_cross_topic_discovery=objective.get(
            "include_cross_topic_discovery", False
        ),
        recall_audit_ref=str(objective.get("recall_audit_ref", "")),
        exact_refs=exact_refs,
    )
    receipt = prepare_context_injection(ws, request, deliver=deliver_context)
    status = {
        "injected": "context_injected",
        "prepared": "context_prepared",
        "delivery_started": "context_delivery_uncertain",
        "ignored_not_research_relevant": "context_ignored",
    }.get(receipt.injection_status, "context_receipt_recorded")
    return _dispatch(
        event,
        topic_id=binding.topic_id,
        status=status,
        operation="prepare_context_injection",
        reason_codes=("bounded_context_receipt",),
        receipt_id=receipt.receipt_id,
        receipt_status=receipt.injection_status,
        runtime_write=True,
    )


def closeout_session(
    ws: WorkspacePaths,
    event: HostLifecycleEvent,
    *,
    actor: object | None = None,
) -> HostLifecycleDispatch:
    """Expose the reviewed closeout planning boundary without applying it."""

    del actor
    _require_event(event)
    if event.logical_event != "session_end":
        raise ValueError("closeout_session requires a session_end event")
    if event.automatic:
        raise ValueError("automatic session closeout is not supported")
    authorize_host_lifecycle_operation(event, "plan_session_closeout")
    event, route_failure = _resolved_lifecycle_event(ws, event)
    if route_failure is not None:
        return route_failure
    binding, failure = _bound_session(ws, event)
    if failure is not None:
        return failure
    return _dispatch(
        event,
        topic_id=binding.topic_id,
        status="plan_only",
        operation="plan_session_closeout",
        reason_codes=("human_review_required", "automatic_closeout_unsupported"),
    )


def dispatch_host_lifecycle_event(
    ws: WorkspacePaths,
    event: HostLifecycleEvent,
    *,
    actor: object | None = None,
    deliver_context: Callable[[str], None] | None = None,
    research_event: ResearchEvent | None = None,
) -> HostLifecycleDispatch:
    """Route one normalized event without adding scientific writer logic."""

    _require_event(event)
    if event.logical_event in {"session_start", "prompt_submit"}:
        return begin_research_turn(ws, event, deliver_context=deliver_context)
    if event.logical_event == "session_end":
        return closeout_session(ws, event, actor=actor)
    event, route_failure = _resolved_lifecycle_event(ws, event)
    if route_failure is not None:
        return route_failure
    binding, failure = _bound_session(ws, event)
    if failure is not None:
        return failure
    if event.logical_event == "pre_tool":
        authorize_host_lifecycle_operation(
            event, "delegate_existing_pre_tool_policy"
        )
        return _dispatch(
            event,
            topic_id=binding.topic_id,
            status="policy_only",
            operation="delegate_existing_pre_tool_policy",
            reason_codes=("existing_host_policy_owner",),
        )
    if event.logical_event == "post_tool":
        if research_event is not None:
            return _dispatch_validated_research_moment(
                ws,
                event,
                research_event,
                actor=actor,
                topic_id=binding.topic_id,
            )
        authorize_host_lifecycle_operation(
            event, "delegate_existing_post_tool_trace"
        )
        return _dispatch(
            event,
            topic_id=binding.topic_id,
            status="trace_only",
            operation="delegate_existing_post_tool_trace",
            reason_codes=("exact_process_capture_not_requested",),
        )
    raise ValueError(f"unsupported logical lifecycle event: {event.logical_event!r}")


def _dispatch_validated_research_moment(
    ws: WorkspacePaths,
    host_event: HostLifecycleEvent,
    research_event: ResearchEvent,
    *,
    actor: object | None,
    topic_id: str,
) -> HostLifecycleDispatch:
    authorize_host_lifecycle_operation(host_event, "dispatch_validated_research_moment")
    if actor is None:
        raise ValueError("a typed actor is required to apply a host research moment")
    event = normalize_research_event(research_event)
    identity_checks = (
        (event.host, host_event.host, "host does not match host event"),
        (event.host_session_id, host_event.host_session_id, "host session does not match host event"),
        (event.session_id, host_event.session_id, "session does not match host event"),
        (event.topic_id, topic_id, "topic does not match session binding"),
        (event.source_event_id, host_event.event_id, "source event does not match host event"),
    )
    for actual, expected, message in identity_checks:
        if actual != expected:
            raise ValueError(f"research event {message}")

    from brain.v5.research_moments import (
        apply_research_moment_decision,
        decide_research_moment,
    )

    decision = decide_research_moment(ws, event)
    receipt = apply_research_moment_decision(ws, decision, actor=actor)
    return _dispatch(
        host_event,
        topic_id=topic_id,
        status=f"moment_{receipt.status}",
        operation="dispatch_validated_research_moment",
        reason_codes=decision.reason_codes,
        receipt_id=receipt.receipt_id,
        receipt_status=receipt.status,
        runtime_write=True,
        canonical_write=decision.declared_effect == "kernel_write" and bool(receipt.record_refs),
    )


def _bound_session(ws: WorkspacePaths, event: HostLifecycleEvent):
    if not ws.session_path(event.session_id).is_file():
        return None, _dispatch(
            event,
            topic_id="",
            status="unbound_session",
            operation="orientation_required",
            reason_codes=("session_binding_not_found",),
        )
    try:
        binding = get_session_binding(ws, event.session_id)
    except FileNotFoundError:
        return None, _dispatch(
            event,
            topic_id="",
            status="unbound_session",
            operation="orientation_required",
            reason_codes=("session_binding_not_found",),
        )
    if event.topic_id and event.topic_id != binding.topic_id:
        return None, _dispatch(
            event,
            topic_id=binding.topic_id,
            status="binding_mismatch",
            operation="orientation_required",
            reason_codes=("event_topic_does_not_match_session_binding",),
        )
    return binding, None


def _resolved_lifecycle_event(ws: WorkspacePaths, event: HostLifecycleEvent):
    from brain.v5.host_lifecycle_routing import resolve_host_lifecycle_route

    resolution = resolve_host_lifecycle_route(ws, event)
    if resolution.status == "selected":
        return resolution.event, None
    status = {
        "ambiguous": "route_ambiguous",
        "coverage_blocked": "route_coverage_blocked",
        "conflict": "route_conflict",
        "outside_aitp": "route_not_required",
    }.get(resolution.status, "route_required")
    operation = {
        "pre_tool": "delegate_existing_pre_tool_policy",
        "post_tool": "delegate_existing_post_tool_trace",
        "session_end": "route_before_closeout",
    }.get(event.logical_event, "route_before_context_injection")
    return resolution.event, _dispatch(
        resolution.event,
        topic_id="",
        status=status,
        operation=operation,
        reason_codes=resolution.reason_codes,
    )


def _dispatch(
    event: HostLifecycleEvent,
    *,
    topic_id: str,
    status: str,
    operation: str,
    reason_codes: tuple[str, ...],
    receipt_id: str = "",
    receipt_status: str = "",
    runtime_write: bool = False,
    canonical_write: bool = False,
) -> HostLifecycleDispatch:
    basis = {
        "event_id": event.event_id,
        "operation": operation,
        "status": status,
        "topic_id": topic_id,
    }
    digest = hashlib.sha256(
        json.dumps(basis, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return HostLifecycleDispatch(
        dispatch_id=f"host-dispatch-{digest[:24]}",
        event_id=event.event_id,
        logical_event=event.logical_event,
        host=event.host,
        host_session_id=event.host_session_id,
        session_id=event.session_id,
        topic_id=topic_id,
        status=status,
        operation=operation,
        reason_codes=reason_codes,
        routing_mode=event.routing_mode,
        route_status=event.route_status,
        receipt_id=receipt_id,
        receipt_status=receipt_status,
        runtime_write=runtime_write,
        canonical_write=canonical_write,
    )


def _typed_refs(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{label} must be a list or tuple")
    try:
        return tuple(sorted({canonical_typed_ref(item)[0] for item in value}))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must contain typed refs: {exc}") from exc


def _required_text(value: object, label: str) -> str:
    text = _optional_text(value, label)
    if not text:
        if label == "event_id":
            raise ValueError("host lifecycle events require a stable event_id")
        raise ValueError(f"{label} must be a non-empty string")
    return text


def _optional_text(value: object, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    text = value.strip()
    if len(text.encode("utf-8")) > 65536:
        raise ValueError(f"{label} must be at most 65536 UTF-8 bytes")
    return text


def _require_event(event: HostLifecycleEvent) -> None:
    if not isinstance(event, HostLifecycleEvent):
        raise TypeError("event must be a HostLifecycleEvent")


__all__ = [
    "HostLifecycleDispatch",
    "HostLifecycleEvent",
    "authorize_host_lifecycle_operation",
    "begin_research_turn",
    "closeout_session",
    "dispatch_host_lifecycle_event",
    "host_lifecycle_operation_allowlist",
    "normalize_host_lifecycle_event",
]
