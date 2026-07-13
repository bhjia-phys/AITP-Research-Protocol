# Compatibility shard 2 for lifecycle_events.
from __future__ import annotations

def plan_supersede(
    ws: WorkspacePaths,
    *,
    record_id: str,
    subject_kind: str,
    status: str,
    reason: str,
    operator: str,
    timestamp: str,
    replacement_ref: str = "",
) -> dict:
    """Dry-run preview of a supersede: run all validation, write nothing."""

    from dataclasses import fields as _fields

    if status not in _SUPERSEDE_STATUSES:
        raise LifecycleError(f"unknown supersede status: {status!r}")
    _path, cls, _rec = _load_subject(ws, record_id, subject_kind)
    declared = {f.name for f in _fields(cls)}
    would_set = [field for field in ("lifecycle_status", "replaced_by") if field in declared]
    salt = _idempotency_salt(
        "supersede", to_topic="", lifecycle_status=status, replacement_ref=replacement_ref
    )
    event_id = _event_id("supersede", record_id, salt=salt)
    return {
        "ok": True,
        "dry_run": True,
        "kind": "lifecycle_supersede_plan",
        "would_write_event_id": event_id,
        "event_type": "supersede",
        "subject_record_id": record_id,
        "subject_kind": subject_kind,
        "status": status,
        "replacement_ref": replacement_ref,
        "reason": reason,
        "operator": operator,
        "timestamp": timestamp,
        "would_mutate_subject_frontmatter": would_set,
        "writes_nothing": True,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }
