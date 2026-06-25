"""CLI handlers for ``aitp-v5 record {rehome,supersede,audit-routing,lifecycle}``.

Every command requires an explicit record id (or topic for audit). No glob, no fuzzy
match, no batch by pattern.
"""

from __future__ import annotations

from datetime import datetime, timezone

from brain.v5.lifecycle_events import (
    audit_routing,
    lifecycle_history,
    plan_rehome,
    plan_supersede,
    rehome_record,
    supersede_record,
)
from brain.v5.workspace import init_workspace


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_record_rehome(args) -> dict:
    ws = init_workspace(args.base)
    if getattr(args, "dry_run", False):
        return plan_rehome(
            ws,
            record_id=args.record_id,
            subject_kind=args.kind,
            from_topic=args.from_topic,
            to_topic=args.to_topic,
            reason=args.reason,
            operator=args.operator or "cli",
            timestamp=args.timestamp or _now(),
        )
    event = rehome_record(
        ws,
        record_id=args.record_id,
        subject_kind=args.kind,
        from_topic=args.from_topic,
        to_topic=args.to_topic,
        reason=args.reason,
        operator=args.operator or "cli",
        timestamp=args.timestamp or _now(),
    )
    return {"ok": True, "event_id": event.event_id, "event_type": event.event_type}


def cmd_record_supersede(args) -> dict:
    ws = init_workspace(args.base)
    if getattr(args, "dry_run", False):
        return plan_supersede(
            ws,
            record_id=args.record_id,
            subject_kind=args.kind,
            status=args.status,
            reason=args.reason,
            operator=args.operator or "cli",
            timestamp=args.timestamp or _now(),
            replacement_ref=args.replacement_ref or "",
        )
    event = supersede_record(
        ws,
        record_id=args.record_id,
        subject_kind=args.kind,
        status=args.status,
        reason=args.reason,
        operator=args.operator or "cli",
        timestamp=args.timestamp or _now(),
        replacement_ref=args.replacement_ref or "",
    )
    return {"ok": True, "event_id": event.event_id, "event_type": event.event_type}


def cmd_record_audit_routing(args) -> dict:
    ws = init_workspace(args.base)
    data = audit_routing(ws, topic_id=args.topic)
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


def cmd_record_lifecycle(args) -> dict:
    ws = init_workspace(args.base)
    data = lifecycle_history(ws, record_id=args.record_id)
    return {
        "ok": True,
        "record_id": data["record_id"],
        "events": [
            {
                "event_id": e.event_id, "event_type": e.event_type,
                "lifecycle_status": e.lifecycle_status, "reason": e.reason,
                "operator": e.operator, "timestamp": e.timestamp,
                "from_topic": e.from_topic, "to_topic": e.to_topic,
                "replacement_ref": e.replacement_ref,
                "supersedes_event": e.supersedes_event,
            }
            for e in data["events"]
        ],
    }
