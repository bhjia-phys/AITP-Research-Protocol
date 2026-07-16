"""Deep public contract for v2 evidence basis provenance."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from brain.v5.contracts import ContractError, ContractResult
from brain.v5.evidence_basis_policy import evidence_basis_audit_hash
from brain.v5.pinned_record_refs import PinnedRecordRef
from brain.v5.record_contracts import validate_evidence_record


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_V2_FIELDS = {
    "support_basis_refs",
    "trace_context_refs",
    "basis_audit",
    "basis_policy_status",
    "basis_payload_hash",
    "basis_policy_version",
    "can_update_claim_trust",
}


def require_valid_evidence_record_v2(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_evidence_record(payload)
    if isinstance(payload, dict) and _V2_FIELDS.intersection(payload):
        _validate_v2_fields(payload, result)
    if not result.ok:
        raise ContractError(result)
    return payload


def evidence_surface_validators() -> dict[str, Any]:
    return {"evidence_record": require_valid_evidence_record_v2}


def _validate_v2_fields(payload: dict[str, Any], result: ContractResult) -> None:
    path = "evidence_record"
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")

    status = payload.get("basis_policy_status")
    if status not in {"admissible", "legacy_unchecked"}:
        result.add(
            f"{path}.basis_policy_status",
            "must be admissible or legacy_unchecked",
        )

    support = _validate_pin_list(payload.get("support_basis_refs"), "support_basis_refs", result)
    _validate_pin_list(payload.get("trace_context_refs"), "trace_context_refs", result)
    audit = payload.get("basis_audit")
    if not isinstance(audit, Mapping):
        result.add(f"{path}.basis_audit", "must be a mapping")
        audit = {}

    if status != "admissible":
        return
    if not support:
        result.add(f"{path}.support_basis_refs", "must contain exact support pins")
    payload_hash = str(payload.get("basis_payload_hash") or "")
    if not _SHA256.fullmatch(payload_hash):
        result.add(f"{path}.basis_payload_hash", "must be a lowercase SHA-256 digest")
    if payload.get("basis_policy_version") != "evidence_basis_v1":
        result.add(f"{path}.basis_policy_version", "must be evidence_basis_v1")
    if audit.get("admissible") is not True:
        result.add(f"{path}.basis_audit.admissible", "must be true")
    if audit.get("payload_hash") != payload_hash:
        result.add(f"{path}.basis_payload_hash", "must match basis_audit.payload_hash")
    if audit.get("policy_version") != payload.get("basis_policy_version"):
        result.add(
            f"{path}.basis_audit.policy_version",
            "must match basis_policy_version",
        )
    if audit.get("can_update_claim_trust") is not False:
        result.add(f"{path}.basis_audit.can_update_claim_trust", "must be false")
    audit_hash = str(audit.get("audit_hash") or "")
    if not _SHA256.fullmatch(audit_hash):
        result.add(f"{path}.basis_audit.audit_hash", "must be a lowercase SHA-256 digest")
    else:
        try:
            recomputed_audit_hash = evidence_basis_audit_hash(audit)
        except (TypeError, ValueError):
            recomputed_audit_hash = ""
        if recomputed_audit_hash != audit_hash:
            result.add(f"{path}.basis_audit.audit_hash", "must bind the complete basis audit")


def _validate_pin_list(value: Any, field: str, result: ContractResult) -> list[dict[str, Any]]:
    path = f"evidence_record.{field}"
    if not isinstance(value, list):
        result.add(path, "must be a list")
        return []
    valid: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            result.add(f"{path}[{index}]", "must be an exact pin mapping")
            continue
        try:
            PinnedRecordRef(
                record_ref=str(item.get("record_ref") or ""),
                content_hash=str(item.get("content_hash") or ""),
                revision=item.get("revision"),
            )
        except (TypeError, ValueError) as exc:
            result.add(f"{path}[{index}]", str(exc))
            continue
        valid.append(dict(item))
    return valid
