"""Repository-backed recording and exact validation for source acquisition."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.source_acquisition_contracts import (
    validate_source_acquisition_decision_record,
    validate_source_acquisition_receipt_record,
)
from brain.v5.source_acquisition_models import (
    SourceAcquisitionDecisionRecord,
    SourceAcquisitionReceiptRecord,
    source_acquisition_decision_id,
    source_acquisition_receipt_id,
)


class SourceAcquisitionResolutionError(RuntimeError):
    """Raised when a source-asset application cannot prove acquisition authority."""


@dataclass(frozen=True)
class SourceAcquisitionDecisionCapture:
    record: SourceAcquisitionDecisionRecord
    pinned_ref: PinnedRecordRef
    write_status: str


@dataclass(frozen=True)
class SourceAcquisitionReceiptCapture:
    record: SourceAcquisitionReceiptRecord
    pinned_ref: PinnedRecordRef
    write_status: str


@dataclass(frozen=True)
class SourceAcquisitionResolution:
    decision: SourceAcquisitionDecisionRecord
    decision_ref: PinnedRecordRef
    receipt: SourceAcquisitionReceiptRecord
    receipt_ref: PinnedRecordRef


def record_source_acquisition_decision(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    canonical_uri: str,
    dedup_key: str,
    action: str,
    policy_basis: str,
    access_disposition: str,
    storage_permission: str,
    connector_id: str,
    collector_id: str,
    decided_at: str,
    actor: RecordActor,
    claim_id: str = "",
    expires_at: str = "",
) -> SourceAcquisitionDecisionCapture:
    """Record one append-only source access and storage decision."""

    fields = {
        "topic_id": topic_id,
        "claim_id": claim_id,
        "canonical_uri": canonical_uri,
        "dedup_key": dedup_key,
        "action": action,
        "policy_basis": policy_basis,
        "access_disposition": access_disposition,
        "storage_permission": storage_permission,
        "connector_id": connector_id,
        "collector_id": collector_id,
        "decided_at": decided_at,
        "expires_at": expires_at,
    }
    record = SourceAcquisitionDecisionRecord(
        decision_id=source_acquisition_decision_id(**fields),
        **fields,
    )
    _raise_contract_errors(validate_source_acquisition_decision_record(record))
    if _parse_timestamp(record.decided_at) > _utc_now():
        raise ValueError("decided_at cannot be in the future")
    write = RecordRepository(ws, actor=actor).write(
        "source_acquisition_decisions",
        record,
        body="# Source Acquisition Decision\n\nAccess and storage authority.\n",
    )
    return SourceAcquisitionDecisionCapture(
        record=record,
        pinned_ref=_pin_from_write(write),
        write_status=write.status,
    )


def record_source_acquisition_receipt(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    decision_ref: PinnedRecordRef | Mapping[str, Any],
    canonical_uri: str,
    dedup_key: str,
    status: str,
    connector_id: str,
    collector_id: str,
    acquired_at: str,
    errors: list[str],
    actor: RecordActor,
    claim_id: str = "",
    byte_sha256: str = "",
    hash_algorithm: str = "",
    byte_length: int = 0,
    stored_uri: str = "",
) -> SourceAcquisitionReceiptCapture:
    """Record an exact acquisition outcome only against a valid decision pin."""

    decision_pin = _coerce_pin(decision_ref)
    decision = _resolve_decision(ws, decision_pin, error_type=ValueError)
    fields = {
        "topic_id": topic_id,
        "claim_id": claim_id,
        "decision_ref": asdict(decision_pin),
        "canonical_uri": canonical_uri,
        "dedup_key": dedup_key,
        "status": status,
        "byte_sha256": byte_sha256,
        "hash_algorithm": hash_algorithm,
        "byte_length": byte_length,
        "stored_uri": stored_uri,
        "connector_id": connector_id,
        "collector_id": collector_id,
        "acquired_at": acquired_at,
        "errors": list(errors),
    }
    record = SourceAcquisitionReceiptRecord(
        receipt_id=source_acquisition_receipt_id(**fields),
        **fields,
    )
    _raise_contract_errors(validate_source_acquisition_receipt_record(record))
    _validate_receipt_binding(
        decision,
        record,
        at=record.acquired_at,
        require_allow=record.status == "succeeded",
    )
    now = _utc_now()
    if _parse_timestamp(record.acquired_at) > now:
        raise ValueError("acquired_at cannot be in the future")
    _validate_decision_current(decision, now=now)
    write = RecordRepository(ws, actor=actor).write(
        "source_acquisition_receipts",
        record,
        body="# Source Acquisition Receipt\n\nExact acquisition outcome.\n",
    )
    return SourceAcquisitionReceiptCapture(
        record=record,
        pinned_ref=_pin_from_write(write),
        write_status=write.status,
    )


def resolve_source_acquisition_for_source_asset(
    ws: WorkspacePaths,
    receipt_ref: PinnedRecordRef | Mapping[str, Any],
) -> SourceAcquisitionResolution:
    """Fail closed unless a successful receipt retains currently valid authority."""

    try:
        receipt_pin = _coerce_pin(receipt_ref)
        receipt_version = get_record_version(ws, receipt_pin)
    except Exception as exc:  # noqa: BLE001 - exact source authority must fail closed.
        raise SourceAcquisitionResolutionError("receipt pin is not resolvable") from exc
    if not isinstance(receipt_version.record, SourceAcquisitionReceiptRecord):
        raise SourceAcquisitionResolutionError("receipt pin has the wrong record type")
    receipt = receipt_version.record
    errors = validate_source_acquisition_receipt_record(receipt)
    if errors:
        raise SourceAcquisitionResolutionError(f"receipt record is invalid: {'; '.join(errors)}")
    if receipt.status != "succeeded":
        raise SourceAcquisitionResolutionError("receipt status must be succeeded")
    try:
        decision_pin = _coerce_pin(receipt.decision_ref)
        decision = _resolve_decision(ws, decision_pin, error_type=SourceAcquisitionResolutionError)
        _validate_receipt_binding(
            decision,
            receipt,
            at=receipt.acquired_at,
            require_allow=True,
        )
        now = _utc_now()
        if _parse_timestamp(receipt.acquired_at) > now:
            raise SourceAcquisitionResolutionError("receipt acquired_at is in the future")
        _validate_decision_current(decision, now=now)
    except SourceAcquisitionResolutionError:
        raise
    except Exception as exc:  # noqa: BLE001 - preserve the trust boundary for callers.
        raise SourceAcquisitionResolutionError(f"decision authority is invalid: {exc}") from exc
    return SourceAcquisitionResolution(
        decision=decision,
        decision_ref=decision_pin,
        receipt=receipt,
        receipt_ref=receipt_pin,
    )


def _resolve_decision(
    ws: WorkspacePaths,
    pin: PinnedRecordRef,
    *,
    error_type: type[Exception],
) -> SourceAcquisitionDecisionRecord:
    try:
        version = get_record_version(ws, pin)
    except Exception as exc:  # noqa: BLE001 - callers receive an authority-specific failure.
        raise error_type("decision_ref is not an exact resolvable decision") from exc
    if not isinstance(version.record, SourceAcquisitionDecisionRecord):
        raise error_type("decision_ref has the wrong record type")
    errors = validate_source_acquisition_decision_record(version.record)
    if errors:
        raise error_type(f"decision record is invalid: {'; '.join(errors)}")
    return version.record


def _validate_receipt_binding(
    decision: SourceAcquisitionDecisionRecord,
    receipt: SourceAcquisitionReceiptRecord,
    *,
    at: str,
    require_allow: bool,
) -> None:
    for field in ("topic_id", "claim_id", "canonical_uri", "dedup_key", "connector_id", "collector_id"):
        if getattr(decision, field) != getattr(receipt, field):
            raise ValueError(f"decision and receipt {field} must match")
    instant = _parse_timestamp(at)
    if instant < _parse_timestamp(decision.decided_at):
        raise ValueError("receipt acquired_at cannot precede decided_at")
    if decision.expires_at and instant >= _parse_timestamp(decision.expires_at):
        raise ValueError("decision is expired")
    if require_allow and decision.action != "allow":
        raise ValueError("successful receipt requires an allow decision")
    if receipt.status == "denied" and decision.action not in {"deny", "review"}:
        raise ValueError("denied receipt requires a deny or review decision")


def _coerce_pin(value: PinnedRecordRef | Mapping[str, Any]) -> PinnedRecordRef:
    if isinstance(value, PinnedRecordRef):
        return value
    if not isinstance(value, Mapping):
        raise ValueError("decision_ref must be an exact pin mapping")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )


def _pin_from_write(write: Any) -> PinnedRecordRef:
    return PinnedRecordRef(
        record_ref=write.record_ref,
        content_hash=write.content_hash,
        revision=write.revision,
    )


def _raise_contract_errors(errors: tuple[str, ...]) -> None:
    if errors:
        raise ValueError("; ".join(errors))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_decision_current(
    decision: SourceAcquisitionDecisionRecord,
    *,
    now: datetime,
) -> None:
    decided_at = _parse_timestamp(decision.decided_at)
    if decided_at > now:
        raise ValueError("decision decided_at is in the future")
    if decision.expires_at and now >= _parse_timestamp(decision.expires_at):
        raise ValueError("decision is expired at the current time")


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed
