"""Record lifecycle operations: rehome and supersede.

Every lifecycle change produces exactly one append-only ``lifecycle_event`` record under
``registry/lifecycle_events/``. Records themselves are never deleted; they gain lazy-
compatible frontmatter fields (see ``ClaimRecord`` / ``EvidenceRecord``). The relation-map
filters on ``lifecycle_status`` to exclude non-active records from the current conclusion.
"""

from __future__ import annotations

from typing import Iterable

from brain.v5.ids import prefixed_id, short_hash
from brain.v5.models import LifecycleEventRecord
from brain.v5.store import list_valid_records, write_record
from brain.v5.workspace import WorkspacePaths


_VALID_EVENT_TYPES = {"rehome", "supersede"}
_VALID_RECORD_STATUSES = {"active", "misrouted", "voided", "superseded", "duplicate"}
# events may carry "rehomed" to express the action even though records use "misrouted"
_VALID_EVENT_STATUSES = _VALID_RECORD_STATUSES | {"rehomed"}


def _event_id(event_type: str, subject_record_id: str, *, salt: str) -> str:
    raw = f"{event_type}:{subject_record_id}:{salt}"
    digest = short_hash(raw, 8)
    slug_base = f"{event_type}-{subject_record_id}"
    return prefixed_id("ev", slug_base, max_slug=60) + "-" + digest


def _idempotency_salt(event_type: str, **fields) -> str:
    if event_type == "rehome":
        return f"rehome|{fields.get('to_topic', '')}"
    # supersede
    return f"supersede|{fields.get('lifecycle_status', '')}|{fields.get('replacement_ref', '')}"


def list_lifecycle_events(ws: WorkspacePaths) -> list[LifecycleEventRecord]:
    return list_valid_records(ws.registry_dir("lifecycle_events"), LifecycleEventRecord)


def find_existing_event(
    events: Iterable[LifecycleEventRecord],
    *,
    event_type: str,
    subject_record_id: str,
    salt: str,
) -> LifecycleEventRecord | None:
    target = _event_id(event_type, subject_record_id, salt=salt)
    for event in events:
        if event.event_id == target:
            return event
    return None


def find_latest_supersede_for(
    events: Iterable[LifecycleEventRecord], subject_record_id: str
) -> LifecycleEventRecord | None:
    matches = [e for e in events if e.event_type == "supersede" and e.subject_record_id == subject_record_id]
    if not matches:
        return None
    # the most recently written supersede (highest in lexicographic timestamp)
    return max(matches, key=lambda e: (e.timestamp, e.event_id))


def create_lifecycle_event(
    ws: WorkspacePaths,
    *,
    event_type: str,
    subject_record_id: str,
    subject_kind: str,
    lifecycle_status: str,
    reason: str,
    operator: str,
    timestamp: str,
    from_topic: str = "",
    to_topic: str = "",
    replacement_ref: str = "",
) -> LifecycleEventRecord:
    """Create a lifecycle_event record, idempotently.

    Idempotency key:
      - rehome: (subject_record_id, "rehome", to_topic)
      - supersede: (subject_record_id, "supersede", lifecycle_status, replacement_ref)

    Re-applying the same key returns the existing event and writes nothing.
    A supersede with a *different* status writes a new event chained via supersedes_event
    to the previous latest supersede for the same subject.
    """

    if event_type not in _VALID_EVENT_TYPES:
        raise ValueError(f"unknown event_type: {event_type!r}")
    if lifecycle_status not in _VALID_EVENT_STATUSES:
        raise ValueError(f"unknown lifecycle_status: {lifecycle_status!r}")
    if event_type == "rehome" and not to_topic:
        raise ValueError("rehome requires to_topic")

    salt = _idempotency_salt(
        event_type, to_topic=to_topic, lifecycle_status=lifecycle_status, replacement_ref=replacement_ref
    )
    existing_events = list_lifecycle_events(ws)
    existing = find_existing_event(
        existing_events, event_type=event_type, subject_record_id=subject_record_id, salt=salt
    )
    if existing is not None:
        return existing

    chain = ""
    if event_type == "supersede":
        prev = find_latest_supersede_for(existing_events, subject_record_id)
        if prev is not None:
            chain = prev.event_id

    event = LifecycleEventRecord(
        event_id=_event_id(event_type, subject_record_id, salt=salt),
        event_type=event_type,
        subject_record_id=subject_record_id,
        subject_kind=subject_kind,
        lifecycle_status=lifecycle_status,
        reason=reason,
        operator=operator,
        timestamp=timestamp,
        from_topic=from_topic,
        to_topic=to_topic,
        replacement_ref=replacement_ref,
        supersedes_event=chain,
    )
    path = ws.registry_dir("lifecycle_events") / f"{event.event_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        f"# Lifecycle event: {event_type}\n\n"
        f"- Subject: `{subject_record_id}` ({subject_kind})\n"
        f"- Reason: {reason}\n"
        f"- Operator: {operator} @ {timestamp}\n"
    )
    if from_topic or to_topic:
        body += f"- Topic: {from_topic or '-'} -> {to_topic or '-'}\n"
    if replacement_ref:
        body += f"- Replacement: `{replacement_ref}`\n"
    write_record(path, event, body=body)
    return event
