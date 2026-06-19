"""MCP-facing record lifecycle tools for AITP v5.

Surface (plan->apply for the risky rehome operation; direct calls for supersede/audit):
- aitp_v5_build_rehome_plan     (read-only)
- aitp_v5_apply_rehome_plan     (requires explicit record ids; idempotent)
- aitp_v5_supersede_record      (single record; idempotent)
- aitp_v5_audit_record_routing  (read-only)
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from brain.v5.lifecycle_events import audit_routing, rehome_record, supersede_record
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_explicit_ids(record_ids: list[str]) -> None:
    if not isinstance(record_ids, list) or not record_ids:
        raise ValueError("record_ids must be a non-empty list of explicit ids")
    for rid in record_ids:
        if not isinstance(rid, str) or not rid:
            raise ValueError("record_ids must contain non-empty strings")
        if any(ch in rid for ch in "*?["):
            raise ValueError(f"record_ids must be explicit; glob/pattern not allowed: {rid!r}")


def aitp_v5_build_rehome_plan(
    base: str, *, record_ids: list[str], from_topic: str, to_topic: str,
    reason: str, operator: str = "operator",
) -> dict:
    """Read-only plan of what a rehome would do. Writes nothing."""

    _validate_explicit_ids(record_ids)
    init_workspace(Path(base))  # validate the workspace exists; no writes
    plan = []
    for rid in record_ids:
        plan.append({
            "record_id": rid,
            "from_topic": from_topic,
            "to_topic": to_topic,
            "action": "label_misrouted_and_add_pointer",
            "reason": reason,
            "operator": operator,
        })
    return {"ok": True, "plan": plan, "record_count": len(plan)}


def aitp_v5_apply_rehome_plan(
    base: str, *, record_ids: list[str], from_topic: str, to_topic: str,
    reason: str, operator: str = "operator", timestamp: str = "",
) -> dict:
    """Apply a rehome for explicit record ids. Idempotent — re-applying returns the same
    event ids and writes no new events."""

    _validate_explicit_ids(record_ids)
    ws = init_workspace(Path(base))
    ts = timestamp or _now()
    event_ids = []
    for rid in record_ids:
        event = rehome_record(
            ws, record_id=rid, subject_kind="claim",
            from_topic=from_topic, to_topic=to_topic,
            reason=reason, operator=operator, timestamp=ts,
        )
        event_ids.append(event.event_id)
    return {"ok": True, "event_ids": event_ids}


def aitp_v5_supersede_record(
    base: str, *, record_id: str, subject_kind: str, status: str,
    reason: str, operator: str = "operator", timestamp: str = "",
    replacement_ref: str = "",
) -> dict:
    ws = init_workspace(Path(base))
    event = supersede_record(
        ws, record_id=record_id, subject_kind=subject_kind, status=status,
        reason=reason, operator=operator, timestamp=timestamp or _now(),
        replacement_ref=replacement_ref,
    )
    return {"ok": True, **require_valid_public_surface("lifecycle_event_record", {"ok": True, **asdict(event)})}


def aitp_v5_audit_record_routing(base: str, *, topic_id: str) -> dict:
    ws = init_workspace(Path(base))
    data = audit_routing(ws, topic_id=topic_id)
    return {
        "ok": True,
        "topic_id": data["topic_id"],
        "events": [
            {
                "event_id": e.event_id, "event_type": e.event_type,
                "subject_record_id": e.subject_record_id, "subject_kind": e.subject_kind,
                "lifecycle_status": e.lifecycle_status, "reason": e.reason,
                "operator": e.operator, "timestamp": e.timestamp,
                "from_topic": e.from_topic, "to_topic": e.to_topic,
                "replacement_ref": e.replacement_ref,
            }
            for e in data["events"]
        ],
    }
