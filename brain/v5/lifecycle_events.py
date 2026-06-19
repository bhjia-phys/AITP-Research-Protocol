"""Record lifecycle operations: rehome and supersede.

Every lifecycle change produces exactly one append-only ``lifecycle_event`` record under
``registry/lifecycle_events/``. Records themselves are never deleted; they gain lazy-
compatible frontmatter fields (see ``ClaimRecord`` / ``EvidenceRecord``). The relation-map
filters on ``lifecycle_status`` to exclude non-active records from the current conclusion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from brain.v5.ids import prefixed_id, short_hash
from brain.v5.models import ClaimRecord, EvidenceRecord, LifecycleEventRecord
from brain.v5.store import list_valid_records, read_record, write_record
from brain.v5.workspace import WorkspacePaths


_VALID_EVENT_TYPES = {"rehome", "supersede"}
_VALID_RECORD_STATUSES = {"active", "misrouted", "voided", "superseded", "duplicate"}
# supersede may only move a record OUT of active; "active" is never a valid supersede target
_SUPERSEDE_STATUSES = {"misrouted", "voided", "superseded", "duplicate"}
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


_KIND_TO_FAMILY = {"claim": "claims", "evidence": "evidence"}
_KIND_TO_RECORD_CLS = {"claim": ClaimRecord, "evidence": EvidenceRecord}


class LifecycleError(ValueError):
    """Raised when a lifecycle operation cannot be applied."""


def _load_subject(ws: WorkspacePaths, record_id: str, subject_kind: str):
    """Return (path, record_cls, loaded_record) for a registry subject.

    Loading the record here lets callers validate from_topic against the record's real
    topic_id and locate the topic-ledger copy, without a second read.
    """

    if subject_kind not in _KIND_TO_FAMILY:
        raise LifecycleError(f"unsupported subject_kind: {subject_kind!r}")
    family = _KIND_TO_FAMILY[subject_kind]
    path = ws.registry_dir(family) / f"{record_id}.md"
    if not path.exists():
        raise LifecycleError(f"record not found: {record_id}")
    cls = _KIND_TO_RECORD_CLS[subject_kind]
    record = read_record(path, cls)
    return path, cls, record


def _rewrite_subject_frontmatter(path: Path, cls, **overrides):
    """Re-read, update fields, re-write — preserving the body."""

    from dataclasses import fields

    from brain.v5.markdown import read_md

    fm, body = read_md(path)
    allowed = {f.name for f in fields(cls)}
    filtered = {k: v for k, v in fm.items() if k in allowed}
    record = cls(**filtered)
    for key, value in overrides.items():
        setattr(record, key, value)
    write_record(path, record, body=body)


def _append_cross_topic_pointer(ws: WorkspacePaths, *, to_topic: str, source_record_id: str, source_topic: str):
    pointer_id = prefixed_id("xref", f"{to_topic}:{source_record_id}", max_slug=60)
    pointer_path = ws.topic_dir(to_topic) / "claims" / "ledger" / f"{pointer_id}.md"
    if pointer_path.exists():
        return pointer_id
    # write a lightweight cross_topic_reference record as a dict (not a dataclass — keep minimal)
    fm = {
        "ok": True,
        "kind": "cross_topic_reference",
        "pointer_id": pointer_id,
        "source_record_id": source_record_id,
        "source_topic": source_topic,
        "target_topic": to_topic,
    }
    body = f"# Cross-topic reference\n\nPoints to `{source_record_id}` from topic `{source_topic}`.\n"
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    write_record(pointer_path, fm, body=body)
    return pointer_id


def rehome_record(
    ws: WorkspacePaths,
    *,
    record_id: str,
    subject_kind: str,
    from_topic: str,
    to_topic: str,
    reason: str,
    operator: str,
    timestamp: str,
) -> LifecycleEventRecord:
    """Re-attribute a record to ``to_topic`` by labeling it misrouted and adding a pointer.

    The record's file location and body are preserved; only frontmatter lifecycle fields
    are added. A pointer entry is appended in the target topic's claim ledger.

    Ordering: all validation first, then mutate the subject + ledger + pointer, and only
    write the lifecycle_event last. This way a mid-write failure cannot leave an orphan
    event that would make the idempotent retry return a no-op and wedge the rehome.
    """

    if not to_topic:
        raise LifecycleError("rehome requires to_topic")
    path, cls, rec = _load_subject(ws, record_id, subject_kind)
    # Validate from_topic matches the record's real birth topic (spec §5 step 1).
    rec_topic = getattr(rec, "topic_id", "")
    if from_topic != rec_topic:
        raise LifecycleError(
            f"from_topic {from_topic!r} does not match record topic_id {rec_topic!r}"
        )
    if not (ws.topic_dir(to_topic) / "topic.md").exists():
        raise LifecycleError(f"target topic not found: {to_topic}")

    # Compute the event id deterministically without writing, so the subject frontmatter
    # can carry the back-pointer before the event file is committed.
    event_id = _event_id("rehome", record_id, salt=_idempotency_salt(
        "rehome", to_topic=to_topic, lifecycle_status="rehomed", replacement_ref=""))

    # If an event for this key already exists, the rehome already landed; return it as a
    # no-op (do not re-mutate). This keeps re-applying a plan idempotent.
    existing = find_existing_event(
        list_lifecycle_events(ws),
        event_type="rehome", subject_record_id=record_id,
        salt=_idempotency_salt("rehome", to_topic=to_topic, lifecycle_status="rehomed", replacement_ref=""),
    )
    if existing is not None:
        return existing

    # 1) mutate subject frontmatter (idempotent: setting the same fields is safe)
    _rewrite_subject_frontmatter(
        path, cls,
        lifecycle_status="misrouted",
        rehome_target_topic=to_topic,
        rehome_event_id=event_id,
    )

    # 2) keep the source topic ledger copy consistent (claims have a second copy there)
    src_ledger_path = ws.topic_dir(from_topic) / "claims" / "ledger" / f"{record_id}.md"
    if src_ledger_path.exists():
        _rewrite_subject_frontmatter(
            src_ledger_path, cls,
            lifecycle_status="misrouted",
            rehome_target_topic=to_topic,
            rehome_event_id=event_id,
        )

    # 3) append the cross-topic pointer in the target topic ledger (idempotent on exists)
    _append_cross_topic_pointer(
        ws, to_topic=to_topic, source_record_id=record_id, source_topic=from_topic
    )

    # 4) write the lifecycle_event last; everything before this is recoverable on retry
    event = create_lifecycle_event(
        ws,
        event_type="rehome",
        subject_record_id=record_id,
        subject_kind=subject_kind,
        from_topic=from_topic,
        to_topic=to_topic,
        lifecycle_status="rehomed",
        reason=reason,
        operator=operator,
        timestamp=timestamp,
    )
    return event


def supersede_record(
    ws: WorkspacePaths,
    *,
    record_id: str,
    subject_kind: str,
    status: str,
    reason: str,
    operator: str,
    timestamp: str,
    replacement_ref: str = "",
) -> LifecycleEventRecord:
    """Mark a record misrouted/voided/superseded/duplicate. Optionally set replaced_by.

    ``status="active"`` is rejected: supersede only moves a record out of active.
    Ordering follows rehome_record: mutate subject + ledger first, write the event last.
    """

    if status not in _SUPERSEDE_STATUSES:
        raise LifecycleError(f"unknown supersede status: {status!r}")
    path, cls, rec = _load_subject(ws, record_id, subject_kind)

    overrides = {"lifecycle_status": status}
    if replacement_ref:
        overrides["replaced_by"] = replacement_ref
    _rewrite_subject_frontmatter(path, cls, **overrides)

    # keep the topic ledger copy consistent (claims have a second copy there)
    rec_topic = getattr(rec, "topic_id", "")
    if rec_topic:
        ledger_path = ws.topic_dir(rec_topic) / "claims" / "ledger" / f"{record_id}.md"
        if ledger_path.exists():
            _rewrite_subject_frontmatter(ledger_path, cls, **overrides)

    event = create_lifecycle_event(
        ws,
        event_type="supersede",
        subject_record_id=record_id,
        subject_kind=subject_kind,
        lifecycle_status=status,
        reason=reason,
        operator=operator,
        timestamp=timestamp,
        replacement_ref=replacement_ref,
    )
    return event


def list_cross_topic_pointers(ws: WorkspacePaths, topic_id: str) -> list[dict]:
    from brain.v5.markdown import read_md

    ledger_dir = ws.topic_dir(topic_id) / "claims" / "ledger"
    if not ledger_dir.exists():
        return []
    out = []
    for p in sorted(ledger_dir.glob("*.md")):
        fm, _b = read_md(p)
        if fm.get("kind") == "cross_topic_reference":
            out.append(dict(fm))
    return out


def audit_routing(ws: WorkspacePaths, *, topic_id: str) -> dict:
    """List every lifecycle_event that mentions ``topic_id`` as from_topic or to_topic,
    plus events whose subject record was born in ``topic_id`` (record.topic_id matches)."""

    events = list_lifecycle_events(ws)
    relevant = []
    for e in events:
        if e.from_topic == topic_id or e.to_topic == topic_id:
            relevant.append(e)
            continue
        # subject record born in this topic?
        if e.subject_kind in _KIND_TO_FAMILY:
            try:
                _path, _cls, rec = _load_subject(ws, e.subject_record_id, e.subject_kind)
                if getattr(rec, "topic_id", "") == topic_id:
                    relevant.append(e)
            except LifecycleError:
                continue
    relevant.sort(key=lambda e: (e.timestamp, e.event_id))
    return {"topic_id": topic_id, "events": relevant}


def lifecycle_history(ws: WorkspacePaths, *, record_id: str) -> dict:
    """Return all lifecycle_events for a single record, ordered by timestamp ascending."""

    events = [e for e in list_lifecycle_events(ws) if e.subject_record_id == record_id]
    events.sort(key=lambda e: (e.timestamp, e.event_id))
    return {"record_id": record_id, "events": events}
