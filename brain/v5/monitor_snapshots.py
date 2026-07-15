"""Append-only canonical monitor snapshots and exact history projection."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from typing import Any, Mapping, Sequence

from brain.v5.models import MonitorSnapshotRecord, ToolRunRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WriteResult


class MonitorSnapshotConflict(RuntimeError):
    """Raised when one deterministic snapshot identity is reused with new facts."""


@dataclass(frozen=True)
class MonitorHistory:
    tool_run_ref: PinnedRecordRef
    status: str
    snapshot_refs: tuple[PinnedRecordRef, ...]
    records: tuple[MonitorSnapshotRecord, ...]
    latest_snapshot_ref: PinnedRecordRef | None
    checked_count: int
    errors: tuple[str, ...] = ()
    compatibility_warnings: tuple[str, ...] = ()
    orientation_only: bool = True
    can_create_scientific_evidence: bool = False
    can_update_claim_trust: bool = False


def monitor_snapshot_id(record: MonitorSnapshotRecord) -> str:
    """Return the canonical id for one exact collector observation."""

    basis = {
        "tool_run_ref": record.tool_run_ref,
        "tool_run_hash": record.tool_run_hash,
        "tool_run_revision": record.tool_run_revision,
        "collector_id": record.collector_id,
        "collector_version": record.collector_version,
        "captured_at": record.captured_at,
        "sequence": record.sequence,
    }
    encoded = json.dumps(basis, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"monitor-snapshot-{hashlib.sha256(encoded).hexdigest()}"


def record_monitor_snapshot_v2(
    ws: WorkspacePaths,
    record: MonitorSnapshotRecord,
    *,
    actor: RecordActor,
) -> WriteResult:
    """Persist one immutable observation, enforcing exact sequence and scope."""

    _validate_snapshot_shape(record)
    run_pin = _run_pin(record)
    run = get_record_version(ws, run_pin).record
    if not isinstance(run, ToolRunRecord):
        raise ValueError("monitor tool_run_ref must pin a tool run")
    if (
        record.tool_run_id != run.run_id
        or record.topic_id != run.topic_id
        or record.claim_id != run.claim_id
    ):
        raise ValueError("monitor snapshot topic and claim must match the exact tool run")

    expected_id = monitor_snapshot_id(record)
    if record.snapshot_id and record.snapshot_id != expected_id:
        raise ValueError("monitor snapshot_id does not match its deterministic identity")
    repository = RecordRepository(ws, actor=actor)
    prepared = replace(record, snapshot_id=expected_id)
    with repository.lock_record("monitor_snapshots", expected_id):
        existing = repository.read(f"monitor_snapshot:{expected_id}")
        if existing.status == "found" and isinstance(existing.record, MonitorSnapshotRecord):
            replay = _prepare_replay(prepared, existing.record)
            if asdict(replay) != asdict(existing.record):
                raise MonitorSnapshotConflict(
                    "deterministic monitor snapshot already exists with different content"
                )
            return repository.write(
                "monitor_snapshots",
                replay,
                body=_render_body(replay),
            )
        if existing.status != "not_found":
            raise MonitorSnapshotConflict(
                f"deterministic monitor snapshot is not readable: {existing.status}"
            )

        history = list_monitor_history(ws, run_pin)
        if history.status == "malformed":
            raise ValueError("monitor history is malformed: " + "; ".join(history.errors))
        expected_sequence = len(history.records) + 1
        if prepared.sequence != expected_sequence:
            raise ValueError(f"monitor snapshot next sequence must be {expected_sequence}")
        prepared = _link_previous(prepared, history)
        return repository.write(
            "monitor_snapshots",
            prepared,
            body=_render_body(prepared),
        )


def list_monitor_history(
    ws: WorkspacePaths,
    tool_run_ref: PinnedRecordRef | Mapping[str, Any],
) -> MonitorHistory:
    """Read ordered immutable observations for one exact tool-run version."""

    run_pin = _coerce_pin(tool_run_ref)
    run = get_record_version(ws, run_pin).record
    if not isinstance(run, ToolRunRecord):
        raise ValueError("tool_run_ref must pin a tool run")
    report = _repository(ws).list("monitor_snapshots")
    errors = [
        f"{issue.path}: {issue.error_type}: {issue.message}"
        for issue in report.malformed
    ]
    candidates = [
        item
        for item in report.records
        if isinstance(item, MonitorSnapshotRecord)
        and item.tool_run_id == run.run_id
        and item.tool_run_ref == run_pin.record_ref
        and item.tool_run_hash == run_pin.content_hash
        and item.tool_run_revision == run_pin.revision
    ]
    candidates.sort(key=lambda item: (item.sequence, _timestamp(item.captured_at), item.snapshot_id))
    refs: list[PinnedRecordRef] = []
    warnings: list[str] = []
    previous: MonitorSnapshotRecord | None = None
    previous_ref: PinnedRecordRef | None = None
    for index, item in enumerate(candidates, start=1):
        item_errors = _history_item_errors(item, run, expected_sequence=index)
        errors.extend(f"monitor_snapshot:{item.snapshot_id}: {message}" for message in item_errors)
        try:
            item_ref = pin_current_record(ws, f"monitor_snapshot:{item.snapshot_id}")
        except Exception as exc:  # noqa: BLE001 - history is a fail-closed read model.
            errors.append(f"monitor_snapshot:{item.snapshot_id}: cannot pin current record: {exc}")
            continue
        if item_ref.revision != 1:
            errors.append(f"monitor_snapshot:{item.snapshot_id}: snapshot was revised in place")
        if previous is not None and previous_ref is not None:
            if _timestamp(item.captured_at) <= _timestamp(previous.captured_at):
                errors.append(
                    f"monitor_snapshot:{item.snapshot_id}: captured_at is not later than sequence {previous.sequence}"
                )
            if item.previous_snapshot_ref:
                if (
                    item.previous_snapshot_ref != previous_ref.record_ref
                    or item.previous_snapshot_hash != previous_ref.content_hash
                    or item.previous_snapshot_revision != previous_ref.revision
                ):
                    errors.append(
                        f"monitor_snapshot:{item.snapshot_id}: previous snapshot pin is incorrect"
                    )
            else:
                warnings.append(
                    f"monitor_snapshot:{item.snapshot_id}: legacy snapshot lacks an exact previous link"
                )
        refs.append(item_ref)
        previous = item
        previous_ref = item_ref
    status = "malformed" if errors else ("complete" if candidates else "empty")
    return MonitorHistory(
        tool_run_ref=run_pin,
        status=status,
        snapshot_refs=tuple(refs),
        records=tuple(candidates),
        latest_snapshot_ref=refs[-1] if refs and not errors else None,
        checked_count=report.checked_count,
        errors=tuple(dict.fromkeys(errors)),
        compatibility_warnings=tuple(dict.fromkeys(warnings)),
    )


def monitor_history_payload(history: MonitorHistory) -> dict[str, Any]:
    return {
        "ok": history.status != "malformed",
        "kind": "monitor_history",
        "status": history.status,
        "tool_run_ref": asdict(history.tool_run_ref),
        "snapshot_refs": [asdict(item) for item in history.snapshot_refs],
        "snapshots": [asdict(item) for item in history.records],
        "latest_snapshot_ref": (
            asdict(history.latest_snapshot_ref) if history.latest_snapshot_ref else None
        ),
        "checked_count": history.checked_count,
        "errors": list(history.errors),
        "compatibility_warnings": list(history.compatibility_warnings),
        "truth_source": "typed_monitor_snapshot_records",
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _prepare_replay(
    candidate: MonitorSnapshotRecord,
    existing: MonitorSnapshotRecord,
) -> MonitorSnapshotRecord:
    for name in (
        "previous_snapshot_ref",
        "previous_snapshot_hash",
        "previous_snapshot_revision",
    ):
        supplied = getattr(candidate, name)
        stored = getattr(existing, name)
        if supplied not in ("", 0) and supplied != stored:
            raise MonitorSnapshotConflict("replayed monitor snapshot has a different previous link")
    return replace(
        candidate,
        previous_snapshot_ref=existing.previous_snapshot_ref,
        previous_snapshot_hash=existing.previous_snapshot_hash,
        previous_snapshot_revision=existing.previous_snapshot_revision,
    )


def _link_previous(
    record: MonitorSnapshotRecord,
    history: MonitorHistory,
) -> MonitorSnapshotRecord:
    if not history.records:
        if any(
            (
                record.previous_snapshot_ref,
                record.previous_snapshot_hash,
                record.previous_snapshot_revision,
            )
        ):
            raise ValueError("first monitor snapshot cannot declare a previous snapshot")
        return record
    previous = history.records[-1]
    previous_ref = history.snapshot_refs[-1]
    if _timestamp(record.captured_at) <= _timestamp(previous.captured_at):
        raise ValueError("monitor captured_at must be later than the previous snapshot")
    supplied = (
        record.previous_snapshot_ref,
        record.previous_snapshot_hash,
        record.previous_snapshot_revision,
    )
    expected = (
        previous_ref.record_ref,
        previous_ref.content_hash,
        previous_ref.revision,
    )
    if any(supplied) and supplied != expected:
        raise ValueError("monitor previous snapshot pin does not match latest history")
    return replace(
        record,
        previous_snapshot_ref=previous_ref.record_ref,
        previous_snapshot_hash=previous_ref.content_hash,
        previous_snapshot_revision=previous_ref.revision,
    )


def _validate_snapshot_shape(record: MonitorSnapshotRecord) -> None:
    for name in (
        "topic_id",
        "claim_id",
        "tool_run_id",
        "captured_at",
        "collector_id",
        "collector_version",
        "tool_run_ref",
        "tool_run_hash",
    ):
        if not str(getattr(record, name) or "").strip():
            raise ValueError(f"monitor snapshot {name} must be non-empty")
    if record.sequence < 1:
        raise ValueError("monitor snapshot sequence must be positive")
    if not record.immutable:
        raise ValueError("monitor snapshot must be immutable")
    if record.can_update_claim_trust or record.claim_trust_mutation != "none":
        raise ValueError("monitor snapshot cannot update claim trust")
    if not isinstance(record.scheduler_state, Mapping):
        raise ValueError("monitor scheduler_state must be a mapping")
    _timestamp_required(record.captured_at)


def _history_item_errors(
    record: MonitorSnapshotRecord,
    run: ToolRunRecord,
    *,
    expected_sequence: int,
) -> list[str]:
    errors: list[str] = []
    try:
        _validate_snapshot_shape(record)
    except ValueError as exc:
        errors.append(str(exc))
    if record.sequence != expected_sequence:
        errors.append(f"sequence is {record.sequence}, expected {expected_sequence}")
    if record.topic_id != run.topic_id or record.claim_id != run.claim_id:
        errors.append("topic or claim does not match exact tool run")
    return errors


def _run_pin(record: MonitorSnapshotRecord) -> PinnedRecordRef:
    return PinnedRecordRef(
        record_ref=record.tool_run_ref,
        content_hash=record.tool_run_hash,
        revision=record.tool_run_revision,
    )


def _coerce_pin(value: PinnedRecordRef | Mapping[str, Any]) -> PinnedRecordRef:
    if isinstance(value, PinnedRecordRef):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("tool_run_ref must be an exact pinned ref")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )


def _timestamp_required(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("monitor captured_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("monitor captured_at must include a timezone")
    return parsed.astimezone(UTC)


def _timestamp(value: str) -> datetime:
    try:
        return _timestamp_required(value)
    except ValueError:
        return datetime.min.replace(tzinfo=UTC)


def _repository(ws: WorkspacePaths) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="system",
            actor_id="monitor-history-projection",
            host="local",
        ),
    )


def _render_body(record: MonitorSnapshotRecord) -> str:
    state = record.scheduler_state.get("state") or record.scheduler_state.get("status") or "unknown"
    return (
        "# Immutable Monitor Snapshot\n\n"
        f"Tool run: `{record.tool_run_ref}`\n\n"
        f"Sequence: `{record.sequence}`\n\n"
        f"Scheduler state: `{state}`\n\n"
        "Process observation only; this record cannot create scientific evidence or claim trust.\n"
    )
