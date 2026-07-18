"""Shared explicit-envelope bridge from real post-tool hooks to Research Moments."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from brain.v5.host_lifecycle_facade import (
    dispatch_host_lifecycle_event,
    host_lifecycle_capability,
    normalize_host_lifecycle_event,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.research_moment_facade import research_event_from_mapping


def process_explicit_hook_research_moment(
    ws: WorkspacePaths,
    platform_payload: Mapping[str, Any],
    *,
    host: str,
    session_id: str,
) -> dict[str, Any] | None:
    """Apply only a top-level, complete event envelope; never infer from tool output."""

    if not isinstance(platform_payload, Mapping):
        raise TypeError("platform hook payload must be a mapping")
    event_payload = platform_payload.get("aitp_research_event")
    if event_payload is None:
        return None
    try:
        if not isinstance(event_payload, Mapping):
            raise TypeError("aitp_research_event must be a mapping")
        research_event = research_event_from_mapping(event_payload)
        capability = host_lifecycle_capability(host)
        native_post_tool = next(
            (
                event.native_event
                for event in capability.automatic_events
                if event.logical_event == "post_tool"
            ),
            None,
        )
        if native_post_tool is None:
            raise ValueError(f"host {host!r} has no automatic post-tool event")
        host_event = normalize_host_lifecycle_event(
            host,
            native_post_tool,
            {
                "event_id": research_event.source_event_id,
                "host_session_id": research_event.host_session_id,
                "occurred_at": research_event.occurred_at,
                "topic_id": research_event.topic_id,
                "subject_refs": list(research_event.subject_refs),
                "tool_name": _tool_name(platform_payload),
                "status": _status(platform_payload),
            },
            session_id=session_id,
        )
        dispatch = dispatch_host_lifecycle_event(
            ws,
            host_event,
            research_event=research_event,
            actor=RecordActor(
                actor_type="tool",
                actor_id=f"{capability.host}-post-tool-research-moment",
                host=capability.host,
            ),
        )
        return asdict(dispatch)
    except Exception as exc:  # noqa: BLE001 - post-tool hooks must degrade safely.
        return {
            "kind": "research_moment_hook_diagnostic",
            "status": "rejected",
            "reason_code": "invalid_explicit_research_event",
            "error_type": type(exc).__name__,
            "orientation_only": True,
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
        }


def _tool_name(payload: Mapping[str, Any]) -> str:
    value = payload.get("tool_name")
    if isinstance(value, str) and value.strip():
        return value.strip()
    tool = payload.get("tool")
    if isinstance(tool, Mapping):
        value = tool.get("name")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "unknown_tool"


def _status(payload: Mapping[str, Any]) -> str:
    value = payload.get("status")
    return value.strip() if isinstance(value, str) and value.strip() else "unknown"


__all__ = ["process_explicit_hook_research_moment"]
