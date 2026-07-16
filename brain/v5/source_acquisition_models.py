"""Canonical process records for controlled source-byte acquisition."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Mapping

from brain.v5.ids import prefixed_id


@dataclass(frozen=True)
class SourceAcquisitionDecisionRecord:
    decision_id: str
    topic_id: str
    canonical_uri: str
    dedup_key: str
    action: str
    policy_basis: str
    access_disposition: str
    storage_permission: str
    connector_id: str
    collector_id: str
    decided_at: str
    claim_id: str = ""
    expires_at: str = ""
    can_update_claim_trust: bool = False
    kind: str = "source_acquisition_decision"


@dataclass(frozen=True)
class SourceAcquisitionReceiptRecord:
    receipt_id: str
    topic_id: str
    decision_ref: dict[str, Any]
    canonical_uri: str
    dedup_key: str
    status: str
    connector_id: str
    collector_id: str
    acquired_at: str
    claim_id: str = ""
    byte_sha256: str = ""
    hash_algorithm: str = ""
    byte_length: int = 0
    stored_uri: str = ""
    errors: list[str] | None = None
    can_update_claim_trust: bool = False
    kind: str = "source_acquisition_receipt"

    def __post_init__(self) -> None:
        if self.errors is None:
            object.__setattr__(self, "errors", [])


def source_acquisition_decision_id(**bound: Any) -> str:
    """Return the stable decision identity from its immutable policy binding."""

    return prefixed_id(
        "source-acquisition-decision",
        _canonical_json(bound),
        max_slug=72,
    )


def source_acquisition_receipt_id(**bound: Any) -> str:
    """Return the stable receipt identity from its immutable acquisition binding."""

    return prefixed_id(
        "source-acquisition-receipt",
        _canonical_json(bound),
        max_slug=72,
    )


def decision_bound_content(record: SourceAcquisitionDecisionRecord) -> dict[str, Any]:
    return {
        "topic_id": record.topic_id,
        "claim_id": record.claim_id,
        "canonical_uri": record.canonical_uri,
        "dedup_key": record.dedup_key,
        "action": record.action,
        "policy_basis": record.policy_basis,
        "access_disposition": record.access_disposition,
        "storage_permission": record.storage_permission,
        "connector_id": record.connector_id,
        "collector_id": record.collector_id,
        "decided_at": record.decided_at,
        "expires_at": record.expires_at,
    }


def receipt_bound_content(record: SourceAcquisitionReceiptRecord) -> dict[str, Any]:
    return {
        "topic_id": record.topic_id,
        "claim_id": record.claim_id,
        "decision_ref": record.decision_ref,
        "canonical_uri": record.canonical_uri,
        "dedup_key": record.dedup_key,
        "status": record.status,
        "byte_sha256": record.byte_sha256,
        "hash_algorithm": record.hash_algorithm,
        "byte_length": record.byte_length,
        "stored_uri": record.stored_uri,
        "connector_id": record.connector_id,
        "collector_id": record.collector_id,
        "acquired_at": record.acquired_at,
        "errors": record.errors or [],
    }


def expected_decision_id(record: SourceAcquisitionDecisionRecord) -> str:
    return source_acquisition_decision_id(**decision_bound_content(record))


def expected_receipt_id(record: SourceAcquisitionReceiptRecord) -> str:
    return source_acquisition_receipt_id(**receipt_bound_content(record))


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        _json_compatible(value),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def _json_compatible(value: Any) -> Any:
    if is_dataclass(value):
        return _json_compatible(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"source acquisition identity contains {type(value).__name__}")
