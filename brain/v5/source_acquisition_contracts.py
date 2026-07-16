"""Independent validators for typed source-acquisition process records."""

from __future__ import annotations

import re
from datetime import datetime

from brain.v5.source_acquisition_models import (
    SourceAcquisitionDecisionRecord,
    SourceAcquisitionReceiptRecord,
    expected_decision_id,
    expected_receipt_id,
)


_ACTIONS = {"allow", "deny", "review"}
_STATUSES = {"succeeded", "failed", "denied"}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def validate_source_acquisition_decision_record(
    record: SourceAcquisitionDecisionRecord,
) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(record, SourceAcquisitionDecisionRecord):
        return ("record must be a SourceAcquisitionDecisionRecord",)
    for field in (
        "decision_id",
        "topic_id",
        "canonical_uri",
        "dedup_key",
        "policy_basis",
        "access_disposition",
        "storage_permission",
        "connector_id",
        "collector_id",
        "decided_at",
    ):
        _require_text(record, field, errors)
    if not isinstance(record.action, str) or record.action not in _ACTIONS:
        errors.append("action must be allow, deny, or review")
    _require_timestamp(record.decided_at, "decided_at", errors)
    if record.expires_at != "":
        _require_timestamp(record.expires_at, "expires_at", errors)
        if (
            _is_timestamp(record.decided_at)
            and _is_timestamp(record.expires_at)
            and _timestamp(record.expires_at) <= _timestamp(record.decided_at)
        ):
            errors.append("expires_at must be later than decided_at")
    if record.can_update_claim_trust is not False:
        errors.append("can_update_claim_trust must be false")
    if record.kind != "source_acquisition_decision":
        errors.append("kind must be source_acquisition_decision")
    if record.decision_id:
        try:
            if record.decision_id != expected_decision_id(record):
                errors.append("decision_id must match immutable bound content")
        except (TypeError, ValueError):
            errors.append("decision_id bound content must be JSON-compatible")
    return tuple(errors)


def validate_source_acquisition_receipt_record(
    record: SourceAcquisitionReceiptRecord,
) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(record, SourceAcquisitionReceiptRecord):
        return ("record must be a SourceAcquisitionReceiptRecord",)
    for field in (
        "receipt_id",
        "topic_id",
        "canonical_uri",
        "dedup_key",
        "connector_id",
        "collector_id",
        "acquired_at",
    ):
        _require_text(record, field, errors)
    _validate_pin(record.decision_ref, errors)
    if not isinstance(record.status, str) or record.status not in _STATUSES:
        errors.append("status must be succeeded, failed, or denied")
    _require_timestamp(record.acquired_at, "acquired_at", errors)
    if not isinstance(record.errors, list) or any(
        not isinstance(error, str) or not error.strip() for error in record.errors or []
    ):
        errors.append("errors must be a list of non-empty strings")
    if record.status == "succeeded":
        if not _SHA256.fullmatch(record.byte_sha256):
            errors.append("byte_sha256 must be a lowercase SHA-256 digest for succeeded receipts")
        if record.hash_algorithm != "sha256":
            errors.append("hash_algorithm must be sha256 for succeeded receipts")
        if isinstance(record.byte_length, bool) or not isinstance(record.byte_length, int) or record.byte_length <= 0:
            errors.append("byte_length must be positive for succeeded receipts")
        if not isinstance(record.stored_uri, str) or not record.stored_uri.strip():
            errors.append("stored_uri must be non-empty for succeeded receipts")
        if record.errors:
            errors.append("errors must be empty for succeeded receipts")
    elif record.byte_sha256 or record.hash_algorithm or record.byte_length or record.stored_uri:
        errors.append("failed or denied receipts cannot claim acquired bytes")
    elif not record.errors:
        errors.append("failed or denied receipts require explicit errors")
    if record.can_update_claim_trust is not False:
        errors.append("can_update_claim_trust must be false")
    if record.kind != "source_acquisition_receipt":
        errors.append("kind must be source_acquisition_receipt")
    if record.receipt_id:
        try:
            if record.receipt_id != expected_receipt_id(record):
                errors.append("receipt_id must match immutable bound content")
        except (TypeError, ValueError):
            errors.append("receipt_id bound content must be JSON-compatible")
    return tuple(errors)


def _require_text(record: object, field: str, errors: list[str]) -> None:
    if not isinstance(getattr(record, field), str) or not getattr(record, field).strip():
        errors.append(f"{field} must be non-empty")


def _validate_pin(value: object, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("decision_ref must be an exact pin mapping")
        return
    if not isinstance(value.get("record_ref"), str) or not value["record_ref"].strip():
        errors.append("decision_ref.record_ref must be non-empty")
    if not isinstance(value.get("content_hash"), str) or not _SHA256.fullmatch(value["content_hash"]):
        errors.append("decision_ref.content_hash must be a lowercase SHA-256 digest")
    revision = value.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        errors.append("decision_ref.revision must be a positive integer")


def _require_timestamp(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be an ISO-8601 timestamp with timezone")
        return
    try:
        parsed = _timestamp(value)
    except ValueError:
        errors.append(f"{field} must be an ISO-8601 timestamp with timezone")
        return
    if parsed.tzinfo is None:
        errors.append(f"{field} must be an ISO-8601 timestamp with timezone")


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _is_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        return _timestamp(value).tzinfo is not None
    except (TypeError, ValueError):
        return False
