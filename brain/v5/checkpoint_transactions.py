"""Exactly-once application receipts for action-bound human checkpoints."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Mapping

from brain.v5.checkpoint_bindings import (
    CheckpointSubjectBinding,
    hash_action_payload,
    validate_checkpoint_binding,
)
from brain.v5.markdown import write_text_atomic
from brain.v5.models import CheckpointApplicationReceiptRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository


class CheckpointApplicationInterrupted(RuntimeError):
    """Raised by a deterministic test or host failpoint before receipt completion."""


class CheckpointApplicationFailed(RuntimeError):
    """Raised after an immutable failed application receipt has been written."""


class CheckpointReplayRejected(RuntimeError):
    """Raised when a prior failed or non-identical application cannot be replayed."""


@dataclass(frozen=True)
class BoundCheckpointApplication:
    record: CheckpointApplicationReceiptRecord
    receipt_ref: PinnedRecordRef
    result_ref: PinnedRecordRef | None
    write_status: str
    replayed: bool


def apply_bound_checkpoint_action(
    ws: WorkspacePaths,
    *,
    binding: CheckpointSubjectBinding,
    request_ref: PinnedRecordRef | Mapping[str, Any],
    decision_ref: PinnedRecordRef | Mapping[str, Any],
    action_payload: Mapping[str, Any],
    result_writer: Callable[[str], PinnedRecordRef | Mapping[str, Any] | None],
    result_resolver: Callable[[str], PinnedRecordRef | Mapping[str, Any] | None],
    result_validator: Callable[[str, PinnedRecordRef], None],
    actor: RecordActor,
    now: datetime | None = None,
    failpoint: str = "",
) -> BoundCheckpointApplication:
    """Apply one approved exact action and persist its sole consumption fact."""

    if failpoint not in {
        "",
        "before_result_write",
        "after_result_before_journal",
        "after_result_write",
    }:
        raise ValueError("unsupported checkpoint application failpoint")
    if not callable(result_writer):
        raise TypeError("result_writer must be callable")
    if not callable(result_resolver):
        raise TypeError("result_resolver must be callable")
    if not callable(result_validator):
        raise TypeError("result_validator must be callable")
    if binding.replay_policy != "exact_idempotent":
        raise CheckpointReplayRejected("checkpoint replay policy prohibits application")
    if hash_action_payload(action_payload) != binding.action_payload_hash:
        raise ValueError("action payload hash does not match checkpoint binding")

    request_pin = _coerce_pin(request_ref)
    decision_pin = _coerce_pin(decision_ref)
    request_version = validate_checkpoint_binding(
        ws,
        request_pin,
        binding,
        now=now,
    )
    if request_version.record.status != "open":
        raise ValueError("pinned checkpoint request must be the open request revision")
    decision_version = validate_checkpoint_binding(
        ws,
        decision_pin,
        binding,
        now=now,
        require_decided=True,
    )
    if request_pin.record_ref != decision_pin.record_ref:
        raise ValueError("checkpoint request and decision refs do not match")
    predecessor = f"{request_pin.record_ref}@sha256:{request_pin.content_hash}"
    if predecessor not in (decision_version.frontmatter.get("supersedes") or []):
        raise ValueError("checkpoint decision does not supersede the pinned request")

    application_key = {
        "action": binding.action,
        "action_payload_hash": binding.action_payload_hash,
        "intent": asdict(binding.intent),
        "subjects": [asdict(item) for item in sorted(binding.subjects)],
        "request": asdict(request_pin),
        "decision": asdict(decision_pin),
    }
    application_hash = _sha256_json(application_key)
    application_id = f"checkpoint-application-{application_hash}"
    repository = RecordRepository(ws, actor=actor)
    with repository.lock_record("checkpoint_application_receipts", application_id):
        existing = repository.read(f"checkpoint_application_receipt:{application_id}")
        if existing.status == "found" and existing.record is not None:
            return _existing_outcome(
                ws,
                existing.record,
                application_key,
                result_validator,
            )
        if existing.status not in {"not_found"}:
            raise CheckpointReplayRejected(
                f"checkpoint application receipt is not readable: {existing.status}"
            )

        journal_path = _journal_path(ws, application_id)
        journal = _load_or_create_journal(
            journal_path,
            application_id=application_id,
            application_key=application_key,
            started_at=_utc(now).isoformat(),
        )
        result_pin = _journal_result(journal)
        if result_pin is None:
            result_pin = _resolve_result(
                ws,
                result_resolver,
                result_validator,
                application_id,
            )
            if result_pin is None:
                if failpoint == "before_result_write":
                    raise CheckpointApplicationInterrupted(
                        "checkpoint application interrupted before result write"
                    )
                try:
                    raw_result = result_writer(application_id)
                    result_pin = _coerce_optional_pin(raw_result)
                    if result_pin is not None:
                        get_record_version(ws, result_pin)
                        result_validator(application_id, result_pin)
                except Exception as exc:  # noqa: BLE001 - recover deterministic writes first.
                    result_pin = _resolve_result(
                        ws,
                        result_resolver,
                        result_validator,
                        application_id,
                    )
                    if result_pin is None:
                        return _record_failed_application(
                            repository,
                            application_id=application_id,
                            binding=binding,
                            request_pin=request_pin,
                            decision_pin=decision_pin,
                            journal=journal,
                            error=exc,
                        )
            if failpoint == "after_result_before_journal":
                raise CheckpointApplicationInterrupted(
                    "checkpoint application interrupted after result write before journal"
                )
            journal["status"] = "result_written"
            journal["result"] = asdict(result_pin) if result_pin is not None else None
            journal["completed_at"] = _utc(now).isoformat()
            _write_journal(journal_path, journal)
        else:
            get_record_version(ws, result_pin)
            result_validator(application_id, result_pin)

        if failpoint == "after_result_write":
            raise CheckpointApplicationInterrupted(
                "checkpoint application interrupted after result write"
            )
        completed_at = str(journal.get("completed_at") or _utc(now).isoformat())
        record = _receipt_record(
            application_id=application_id,
            binding=binding,
            request_pin=request_pin,
            decision_pin=decision_pin,
            result_pin=result_pin,
            status="applied",
            started_at=str(journal["started_at"]),
            completed_at=completed_at,
            errors=[],
        )
        write = repository.write(
            "checkpoint_application_receipts",
            record,
            body="# Checkpoint Application Receipt\n\nImmutable application outcome.\n",
        )
        receipt_pin = PinnedRecordRef(
            record_ref=write.record_ref,
            content_hash=write.content_hash,
            revision=write.revision,
        )
        return BoundCheckpointApplication(
            record=record,
            receipt_ref=receipt_pin,
            result_ref=result_pin,
            write_status=write.status,
            replayed=False,
        )


def _record_failed_application(
    repository: RecordRepository,
    *,
    application_id: str,
    binding: CheckpointSubjectBinding,
    request_pin: PinnedRecordRef,
    decision_pin: PinnedRecordRef,
    journal: dict[str, Any],
    error: Exception,
) -> BoundCheckpointApplication:
    completed_at = datetime.now(UTC).isoformat()
    errors = [{"error_type": type(error).__name__, "message": str(error)}]
    record = _receipt_record(
        application_id=application_id,
        binding=binding,
        request_pin=request_pin,
        decision_pin=decision_pin,
        result_pin=None,
        status="failed",
        started_at=str(journal["started_at"]),
        completed_at=completed_at,
        errors=errors,
    )
    write = repository.write(
        "checkpoint_application_receipts",
        record,
        body="# Checkpoint Application Receipt\n\nImmutable application outcome.\n",
    )
    receipt_pin = PinnedRecordRef(
        record_ref=write.record_ref,
        content_hash=write.content_hash,
        revision=write.revision,
    )
    raise CheckpointApplicationFailed(str(error))


def _existing_outcome(
    ws: WorkspacePaths,
    record: CheckpointApplicationReceiptRecord,
    application_key: Mapping[str, Any],
    result_validator: Callable[[str, PinnedRecordRef], None],
) -> BoundCheckpointApplication:
    expected_id = f"checkpoint-application-{_sha256_json(application_key)}"
    if record.application_id != expected_id:
        raise CheckpointReplayRejected("checkpoint application identity does not match")
    if record.status == "failed":
        raise CheckpointReplayRejected("failed application requires a new pinned intent")
    if record.status != "applied":
        raise CheckpointReplayRejected("checkpoint application is not terminal")
    result_pin = None
    if record.result_ref:
        result_pin = PinnedRecordRef(
            record_ref=record.result_ref,
            content_hash=record.result_hash,
            revision=record.result_revision,
        )
        get_record_version(ws, result_pin)
        result_validator(record.application_id, result_pin)
    receipt_pin = PinnedRecordRef(
        record_ref=f"checkpoint_application_receipt:{record.application_id}",
        content_hash="0" * 64,
        revision=1,
    )
    from brain.v5.pinned_record_refs import pin_current_record

    receipt_pin = pin_current_record(ws, receipt_pin.record_ref)
    return BoundCheckpointApplication(
        record=record,
        receipt_ref=receipt_pin,
        result_ref=result_pin,
        write_status="unchanged",
        replayed=True,
    )


def _receipt_record(
    *,
    application_id: str,
    binding: CheckpointSubjectBinding,
    request_pin: PinnedRecordRef,
    decision_pin: PinnedRecordRef,
    result_pin: PinnedRecordRef | None,
    status: str,
    started_at: str,
    completed_at: str,
    errors: list[dict],
) -> CheckpointApplicationReceiptRecord:
    return CheckpointApplicationReceiptRecord(
        application_id=application_id,
        intent_ref=binding.intent.record_ref,
        intent_hash=binding.intent.content_hash,
        intent_revision=binding.intent.revision,
        decision_ref=decision_pin.record_ref,
        decision_hash=decision_pin.content_hash,
        decision_revision=decision_pin.revision,
        action=binding.action,
        action_payload_hash=binding.action_payload_hash,
        subject_refs=[asdict(item) for item in sorted(binding.subjects)],
        request_ref=request_pin.record_ref,
        request_hash=request_pin.content_hash,
        request_revision=request_pin.revision,
        result_ref=result_pin.record_ref if result_pin else "",
        result_hash=result_pin.content_hash if result_pin else "",
        result_revision=result_pin.revision if result_pin else 0,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        recorded_at=completed_at,
        errors=errors,
    )


def _journal_path(ws: WorkspacePaths, application_id: str) -> Path:
    return ws.root / "runtime" / "checkpoint_applications" / f"{application_id}.json"


def _load_or_create_journal(
    path: Path,
    *,
    application_id: str,
    application_key: Mapping[str, Any],
    started_at: str,
) -> dict[str, Any]:
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CheckpointReplayRejected("checkpoint application journal is invalid") from exc
        if not isinstance(payload, dict):
            raise CheckpointReplayRejected("checkpoint application journal must be an object")
        if payload.get("application_id") != application_id:
            raise CheckpointReplayRejected("checkpoint application journal id does not match")
        if payload.get("application_key") != application_key:
            raise CheckpointReplayRejected("checkpoint application journal binding does not match")
        return payload
    payload = {
        "version": "v1",
        "application_id": application_id,
        "application_key": dict(application_key),
        "status": "started",
        "started_at": started_at,
        "completed_at": "",
        "result": None,
    }
    _write_journal(path, payload)
    return payload


def _write_journal(path: Path, payload: Mapping[str, Any]) -> None:
    write_text_atomic(
        path,
        json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
    )


def _journal_result(journal: Mapping[str, Any]) -> PinnedRecordRef | None:
    raw = journal.get("result")
    return _coerce_optional_pin(raw)


def _coerce_optional_pin(value: Any) -> PinnedRecordRef | None:
    if value is None:
        return None
    return _coerce_pin(value)


def _resolve_result(
    ws: WorkspacePaths,
    resolver: Callable[[str], PinnedRecordRef | Mapping[str, Any] | None],
    validator: Callable[[str, PinnedRecordRef], None],
    application_id: str,
) -> PinnedRecordRef | None:
    resolved = _coerce_optional_pin(resolver(application_id))
    if resolved is not None:
        get_record_version(ws, resolved)
        validator(application_id, resolved)
    return resolved


def _coerce_pin(value: PinnedRecordRef | Mapping[str, Any]) -> PinnedRecordRef:
    if isinstance(value, PinnedRecordRef):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("pinned ref must be PinnedRecordRef or a mapping")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )


def _utc(value: datetime | None) -> datetime:
    current = value or datetime.now(UTC)
    if current.tzinfo is None:
        raise ValueError("now must include a timezone")
    return current.astimezone(UTC)


def _sha256_json(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
