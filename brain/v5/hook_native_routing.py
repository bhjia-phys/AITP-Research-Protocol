"""Route native Claude/Kimi lifecycle payloads before session-bound work."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

from brain.v5.host_lifecycle_dispatch import dispatch_host_lifecycle_event
from brain.v5.host_lifecycle_facade import host_lifecycle_capability
from brain.v5.host_lifecycle_normalization import normalize_host_lifecycle_event


@dataclass(frozen=True)
class NativeHookRoute:
    status: str
    session_id: str
    topic_id: str
    event_payload: dict[str, Any]
    diagnostic: dict[str, Any]

    @property
    def selected(self) -> bool:
        return self.status == "selected" and bool(self.session_id and self.topic_id)


def resolve_native_hook_route(
    ws,
    *,
    host: str,
    command: str,
    payload: dict[str, Any],
    routing_mode: str,
    pinned_session_id: str,
    project_root: str,
) -> NativeHookRoute:
    if routing_mode != "dynamic":
        try:
            binding = _binding(ws, pinned_session_id)
        except (FileNotFoundError, TypeError, ValueError):
            return NativeHookRoute(
                status="unbound_session",
                session_id=pinned_session_id,
                topic_id="",
                event_payload=dict(payload),
                diagnostic=_diagnostic(
                    status="unbound_session",
                    routing_mode=routing_mode,
                    session_id=pinned_session_id,
                    topic_id="",
                    reason_codes=("session_binding_not_found",),
                ),
            )
        return NativeHookRoute(
            status="selected",
            session_id=pinned_session_id,
            topic_id=binding.topic_id,
            event_payload=dict(payload),
            diagnostic=_diagnostic(
                status="selected",
                routing_mode=routing_mode,
                session_id=pinned_session_id,
                topic_id=binding.topic_id,
                reason_codes=("explicit_session_pin",),
            ),
        )

    try:
        event_payload = standardize_dynamic_host_payload(
            host=host,
            command=command,
            payload=payload,
            project_root=project_root,
        )
    except ValueError:
        return _unresolved(payload, "host_session_identity_required")
    logical_event = command.replace("-", "_")
    capability = host_lifecycle_capability(host)
    native_event = capability.event(logical_event).native_event
    event = normalize_host_lifecycle_event(
        host,
        native_event,
        event_payload,
        routing_mode="dynamic",
    )
    dispatch = dispatch_host_lifecycle_event(ws, event)
    diagnostic = {
        "kind": "host_route_dispatch",
        "ok": True,
        **asdict(dispatch),
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    selected = dispatch.route_status == "selected" and bool(
        dispatch.session_id and dispatch.topic_id
    )
    return NativeHookRoute(
        status="selected" if selected else dispatch.route_status,
        session_id=dispatch.session_id if selected else "",
        topic_id=dispatch.topic_id if selected else "",
        event_payload=event_payload,
        diagnostic=diagnostic,
    )


def validate_native_hook_routing_args(parser, args) -> None:
    if args.routing_mode == "dynamic" and args.session_id:
        parser.error("dynamic routing does not accept --session-id")
    if args.routing_mode in {"pinned", "pinned_compat"} and not args.session_id:
        parser.error(f"{args.routing_mode} routing requires --session-id")


def standardize_dynamic_host_payload(
    *,
    host: str,
    command: str,
    payload: dict[str, Any],
    project_root: str,
) -> dict[str, Any]:
    host_session_id = _first_string(
        payload,
        "host_session_id",
        "session_id",
        "conversation_id",
        "thread_id",
        "chat_id",
    )
    if not host_session_id:
        raise ValueError("dynamic hook payload requires host session identity")
    return _normalized_payload(
        host=host,
        command=command,
        payload=payload,
        host_session_id=host_session_id,
        project_root=project_root,
    )


def _normalized_payload(
    *,
    host: str,
    command: str,
    payload: dict[str, Any],
    host_session_id: str,
    project_root: str,
) -> dict[str, Any]:
    normalized = dict(payload)
    normalized["event_id"] = _first_string(
        payload,
        "event_id",
        "tool_use_id",
        "tool_call_id",
        "call_id",
        "request_id",
    ) or _derived_event_id(host, host_session_id, command, payload)
    normalized["host_session_id"] = host_session_id
    normalized["project_root"] = _first_string(payload, "project_root", "cwd") or project_root
    current_path = _first_string(payload, "current_path", "cwd")
    if current_path:
        normalized["current_path"] = current_path
    tool_name = _first_string(payload, "tool_name", "name")
    if tool_name:
        normalized["tool_name"] = tool_name
    return normalized


def _derived_event_id(
    host: str,
    host_session_id: str,
    command: str,
    payload: dict[str, Any],
) -> str:
    projection = {
        "host": host,
        "host_session_id": host_session_id,
        "command": command,
        "hook_event_name": _first_string(payload, "hook_event_name", "event_name"),
        "tool_name": _first_string(payload, "tool_name", "name"),
        "transcript_path": _first_string(payload, "transcript_path"),
    }
    digest = hashlib.sha256(
        json.dumps(projection, ensure_ascii=True, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return f"native-{digest[:32]}"


def _unresolved(payload: dict[str, Any], reason: str) -> NativeHookRoute:
    return NativeHookRoute(
        status="workspace_recovery",
        session_id="",
        topic_id="",
        event_payload=dict(payload),
        diagnostic=_diagnostic(
            status="workspace_recovery",
            routing_mode="dynamic",
            session_id="",
            topic_id="",
            reason_codes=(reason,),
        ),
    )


def _diagnostic(
    *,
    status: str,
    routing_mode: str,
    session_id: str,
    topic_id: str,
    reason_codes: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "kind": "native_hook_route",
        "status": status,
        "routing_mode": routing_mode,
        "session_id": session_id,
        "topic_id": topic_id,
        "reason_codes": list(reason_codes),
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _binding(ws, session_id: str):
    from brain.v5.workspace import get_session_binding

    return get_session_binding(ws, session_id)


def _first_string(payload: dict[str, Any], *fields: str) -> str:
    for field in fields:
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


__all__ = [
    "NativeHookRoute",
    "resolve_native_hook_route",
    "standardize_dynamic_host_payload",
    "validate_native_hook_routing_args",
]
