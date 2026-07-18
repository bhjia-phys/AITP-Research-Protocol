"""Normalize raw host lifecycle payloads into bounded typed events."""

from __future__ import annotations

from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from brain.v5.host_lifecycle_contracts import HostLifecycleEvent
from brain.v5.research_moment_contracts import normalize_timestamp
from brain.v5.research_scope_contracts import canonical_typed_ref


_OBJECTIVE_TEXT_FIELDS = frozenset(
    {
        "context_profile",
        "focus_set_ref",
        "objective_text",
        "project_root",
        "current_path",
        "repo_id",
        "branch",
        "program_id",
        "recall_audit_ref",
        "user_goal",
    }
)
_OBJECTIVE_BOOL_FIELDS = frozenset(
    {"include_cross_topic_discovery", "research_relevant"}
)
_PROCESS_TEXT_FIELDS = frozenset(
    {
        "artifact_ref",
        "code_state_ref",
        "source_ref",
        "status",
        "tool_name",
        "tool_run_ref",
    }
)


def normalize_host_lifecycle_event(
    host: str,
    native_event: str,
    payload: Mapping[str, Any],
    *,
    session_id: str = "",
    routing_mode: str = "pinned_compat",
    route_status: str = "",
) -> HostLifecycleEvent:
    """Reduce a host payload to stable identity and explicitly allowlisted fields."""

    from brain.v5.host_lifecycle_facade import host_lifecycle_capability

    capability = host_lifecycle_capability(host)
    native_event = _required_text(native_event, "native_event")
    routing_mode = _routing_mode(routing_mode)
    session_id = (
        _optional_text(session_id, "session_id")
        if routing_mode == "dynamic"
        else _required_text(session_id, "session_id")
    )
    route_status = _optional_text(route_status, "route_status") or (
        "unresolved" if routing_mode == "dynamic" else "selected"
    )
    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")

    event_id = _required_text(payload.get("event_id"), "event_id")
    host_session_id = _required_text(
        payload.get("host_session_id"), "host_session_id"
    )
    automatic_event = next(
        (
            event
            for event in capability.automatic_events
            if event.native_event == native_event
        ),
        None,
    )
    fallback = next(
        (
            item
            for item in capability.fallbacks
            if item.operation == native_event
        ),
        None,
    )
    if automatic_event is None and fallback is None:
        raise ValueError(
            f"host {host!r} does not expose lifecycle event {native_event!r}"
        )

    occurred_at = payload.get("occurred_at")
    if occurred_at is None:
        occurred_at = datetime.now(timezone.utc).isoformat()
    else:
        occurred_at = normalize_timestamp(occurred_at, "occurred_at")
    logical_event = (
        automatic_event.logical_event
        if automatic_event is not None
        else fallback.unsupported_event
    )
    return HostLifecycleEvent(
        event_id=event_id,
        logical_event=logical_event,
        native_event=native_event,
        occurred_at=occurred_at,
        host=capability.host,
        host_session_id=host_session_id,
        session_id=session_id,
        topic_id=_optional_text(payload.get("topic_id"), "topic_id"),
        subject_refs=_typed_refs(payload.get("subject_refs", ()), "subject_refs"),
        objective_payload=MappingProxyType(_objective_payload(payload)),
        process_payload=MappingProxyType(_process_payload(payload)),
        automatic=automatic_event is not None,
        origin="host_native" if automatic_event is not None else "explicit_fallback",
        routing_mode=routing_mode,
        route_status=route_status,
    )


def _objective_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field in _OBJECTIVE_TEXT_FIELDS:
        if field in payload:
            result[field] = _optional_text(payload[field], field)
    for field in _OBJECTIVE_BOOL_FIELDS:
        if field in payload:
            if not isinstance(payload[field], bool):
                raise TypeError(f"{field} must be a boolean")
            result[field] = payload[field]
    if "exact_refs" in payload:
        result["exact_refs"] = _typed_refs(payload["exact_refs"], "exact_refs")
    return dict(sorted(result.items()))


def _process_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field in _PROCESS_TEXT_FIELDS:
        if field in payload:
            result[field] = _optional_text(payload[field], field)
    if "exit_code" in payload:
        value = payload["exit_code"]
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("exit_code must be an integer")
        result["exit_code"] = value
    return dict(sorted(result.items()))


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


def _routing_mode(value: object) -> str:
    mode = _required_text(value, "routing_mode").casefold()
    if mode not in {"dynamic", "pinned", "pinned_compat"}:
        raise ValueError(f"unsupported routing mode: {mode}")
    return mode


__all__ = ["normalize_host_lifecycle_event"]
