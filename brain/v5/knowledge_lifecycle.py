"""Exact append-only lifecycle events for promoted knowledge and insight."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from brain.v5.ids import prefixed_id
from brain.v5.models import InsightRecord, LifecycleEventRecord, PhysicsAssertionRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.record_envelope import RecordActor
from brain.v5.record_lifecycle_models import KnowledgeLifecycleProjection
from brain.v5.record_repository import RecordRepository, WriteResult


_ACTIONS = frozenset({"demote", "invalidate", "supersede"})
_STATUS = {"demote": "voided", "invalidate": "voided", "supersede": "superseded"}
_EFFECTIVE_STATUS = {
    "demote": "demoted",
    "invalidate": "invalidated",
    "supersede": "superseded",
}


def record_knowledge_lifecycle_event(
    ws: WorkspacePaths,
    *,
    subject_ref: PinnedRecordRef,
    action: str,
    reason: str,
    operator: str,
    timestamp: str,
    actor: RecordActor,
    replacement_ref: PinnedRecordRef | None = None,
) -> WriteResult:
    """Append one exact lifecycle event without rewriting the subject record."""

    if action not in _ACTIONS:
        raise ValueError(f"unsupported knowledge lifecycle action: {action}")
    subject = _current_subject(ws, subject_ref)
    replacement = None
    if action == "supersede":
        if replacement_ref is None:
            raise ValueError("supersede requires an exact replacement_ref")
        replacement = _current_subject(ws, replacement_ref)
        if type(replacement) is not type(subject) or replacement.topic_id != subject.topic_id:
            raise ValueError("replacement must preserve knowledge record kind and topic")
    elif replacement_ref is not None:
        raise ValueError(f"{action} does not accept a replacement_ref")

    history = _history(ws, subject_ref)
    predecessor = _unique_leaf(ws, history) if history else None
    identity = (
        f"{subject_ref.record_ref}:{subject_ref.content_hash}:{action}:"
        f"{replacement_ref.content_hash if replacement_ref else ''}:"
        f"{predecessor.content_hash if predecessor else ''}"
    )
    event = LifecycleEventRecord(
        event_id=prefixed_id("knowledge-lifecycle", identity, max_slug=72),
        event_type="supersede",
        subject_record_id=subject_ref.record_ref.split(":", 1)[1],
        subject_kind=subject.kind,
        lifecycle_status=_STATUS[action],
        reason=reason,
        operator=operator,
        timestamp=timestamp,
        replacement_ref=replacement_ref.record_ref if replacement_ref else "",
        supersedes_event=(
            predecessor.record_ref.split(":", 1)[1] if predecessor else ""
        ),
        subject_ref=asdict(subject_ref),
        replacement_ref_pin=asdict(replacement_ref) if replacement_ref else {},
        lifecycle_action=action,
        supersedes_event_ref=asdict(predecessor) if predecessor else {},
        effect_policy="knowledge_visibility_only_no_claim_trust",
    )
    return RecordRepository(ws, actor=actor).write(
        "lifecycle_events",
        event,
        body=f"# Knowledge Lifecycle: {action}\n\n{reason}\n",
    )


def project_knowledge_lifecycle(
    ws: WorkspacePaths,
    subject_ref: PinnedRecordRef,
) -> KnowledgeLifecycleProjection:
    """Project one subject's effective status without mutating canonical records."""

    try:
        _current_subject(ws, subject_ref)
        history = _history(ws, subject_ref)
        if not history:
            return _projection(subject_ref, "active", active=True)
        leaf = _unique_leaf(ws, history)
        event = get_record_version(ws, leaf).record
        if not isinstance(event, LifecycleEventRecord):
            raise ValueError("active lifecycle event has an unexpected record type")
        replacement = _coerce_optional_pin(event.replacement_ref_pin)
        return _projection(
            subject_ref,
            _EFFECTIVE_STATUS.get(event.lifecycle_action, event.lifecycle_status),
            active=False,
            active_event_ref=leaf.record_ref,
            replacement=replacement,
        )
    except Exception as exc:  # noqa: BLE001 - lifecycle projection fails closed.
        return _projection(
            subject_ref,
            "blocked_invalid_history",
            active=False,
            blocking_reasons=(str(exc),),
        )


def _current_subject(ws: WorkspacePaths, pin: PinnedRecordRef) -> Any:
    if pin_current_record(ws, pin.record_ref) != pin:
        raise ValueError("knowledge lifecycle subject pin is stale")
    record = get_record_version(ws, pin).record
    if not isinstance(record, (PhysicsAssertionRecord, InsightRecord)):
        raise ValueError("knowledge lifecycle supports physics assertions and insights only")
    return record


def _history(
    ws: WorkspacePaths,
    subject_ref: PinnedRecordRef,
) -> tuple[tuple[PinnedRecordRef, LifecycleEventRecord], ...]:
    report = RecordRepository(ws, actor=_audit_actor()).list("lifecycle_events")
    if report.malformed:
        raise ValueError("lifecycle event registry contains malformed records")
    expected = asdict(subject_ref)
    rows = []
    for record in report.records:
        if not isinstance(record, LifecycleEventRecord) or record.subject_ref != expected:
            continue
        pin = pin_current_record(ws, f"lifecycle_event:{record.event_id}")
        rows.append((pin, record))
    return tuple(rows)


def _unique_leaf(
    ws: WorkspacePaths,
    history: tuple[tuple[PinnedRecordRef, LifecycleEventRecord], ...],
) -> PinnedRecordRef:
    pins = {pin for pin, _record in history}
    predecessors = set()
    successor_counts: dict[PinnedRecordRef, int] = {}
    for _pin, record in history:
        predecessor = _coerce_optional_pin(record.supersedes_event_ref)
        if predecessor is None:
            continue
        if predecessor not in pins:
            raise ValueError("knowledge lifecycle history has a dangling predecessor")
        predecessors.add(predecessor)
        successor_counts[predecessor] = successor_counts.get(predecessor, 0) + 1
    if any(count > 1 for count in successor_counts.values()):
        raise ValueError("knowledge lifecycle history has multiple active branches")
    leaves = pins.difference(predecessors)
    if len(leaves) != 1:
        raise ValueError("knowledge lifecycle history does not have one active leaf")
    return next(iter(leaves))


def _coerce_optional_pin(value: Any) -> PinnedRecordRef | None:
    if not value:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("knowledge lifecycle dependency must be an exact pin")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=int(value.get("revision") or 0),
    )


def _projection(
    subject: PinnedRecordRef,
    status: str,
    *,
    active: bool,
    active_event_ref: str = "",
    replacement: PinnedRecordRef | None = None,
    blocking_reasons: tuple[str, ...] = (),
) -> KnowledgeLifecycleProjection:
    return KnowledgeLifecycleProjection(
        subject_ref=subject.record_ref,
        subject_content_hash=subject.content_hash,
        effective_status=status,
        active=active,
        active_event_ref=active_event_ref,
        replacement_ref=replacement.record_ref if replacement else "",
        replacement_content_hash=replacement.content_hash if replacement else "",
        blocking_reasons=blocking_reasons,
    )


def _audit_actor() -> RecordActor:
    return RecordActor(actor_type="system", actor_id="knowledge-lifecycle-audit", host="aitp-v5")
