"""Read-only admissibility audit for evidence support and trace context."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from brain.v5.models import ReferenceLocationRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record


_SOURCE_SUPPORT_KINDS = frozenset({"source_asset", "reference_location"})


@dataclass(frozen=True)
class EvidenceBasisAudit:
    admissible: bool
    support_basis_refs: tuple[PinnedRecordRef, ...]
    trace_context_refs: tuple[PinnedRecordRef, ...]
    checked_refs: tuple[str, ...]
    errors: tuple[str, ...]
    payload_hash: str
    policy_version: str = "evidence_basis_v1"
    can_update_claim_trust: bool = False


def audit_evidence_basis(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    support_basis_refs: tuple[PinnedRecordRef, ...],
    trace_context_refs: tuple[PinnedRecordRef, ...],
    evidence_payload: Mapping[str, Any],
) -> EvidenceBasisAudit:
    """Validate exact evidence dependencies without writing or changing trust."""

    errors: list[str] = []
    checked: list[str] = []
    support_records: list[tuple[PinnedRecordRef, Any]] = []
    if not support_basis_refs:
        errors.append("support_basis_refs_required")
    for lane, pins in (
        ("support", support_basis_refs),
        ("trace", trace_context_refs),
    ):
        for pin in pins:
            checked.append(pin.record_ref)
            try:
                if pin_current_record(ws, pin.record_ref) != pin:
                    raise ValueError("stale pin")
                record = get_record_version(ws, pin).record
            except (ValueError, RuntimeError) as exc:
                errors.append(f"unresolved_{lane}_ref:{pin.record_ref}:{exc}")
                continue
            record_topic = str(getattr(record, "topic_id", "") or "")
            if topic_id and record_topic and record_topic != topic_id:
                errors.append(f"{lane}_scope_mismatch:{pin.record_ref}")
            if lane == "support":
                support_records.append((pin, record))
                kind = pin.record_ref.split(":", 1)[0]
                if kind not in _SOURCE_SUPPORT_KINDS:
                    errors.append(f"inadmissible_support_kind:{kind}")

    asset_refs = {
        pin.record_ref
        for pin, _record in support_records
        if pin.record_ref.startswith("source_asset:")
    }
    locations = [
        record
        for pin, record in support_records
        if pin.record_ref.startswith("reference_location:")
        and isinstance(record, ReferenceLocationRecord)
    ]
    if asset_refs and not locations:
        errors.append("exact_source_location_pin_missing")
    for location in locations:
        if location.source_ref not in asset_refs:
            errors.append(f"source_location_asset_pin_missing:{location.source_ref}")

    payload_hash = _payload_hash(
        evidence_payload,
        support_basis_refs=support_basis_refs,
        trace_context_refs=trace_context_refs,
    )
    return EvidenceBasisAudit(
        admissible=not errors,
        support_basis_refs=support_basis_refs,
        trace_context_refs=trace_context_refs,
        checked_refs=tuple(checked),
        errors=tuple(dict.fromkeys(errors)),
        payload_hash=payload_hash,
    )


def _payload_hash(
    payload: Mapping[str, Any],
    *,
    support_basis_refs: tuple[PinnedRecordRef, ...],
    trace_context_refs: tuple[PinnedRecordRef, ...],
) -> str:
    encoded = json.dumps(
        {
            "evidence_payload": dict(payload),
            "support_basis_refs": [asdict(pin) for pin in support_basis_refs],
            "trace_context_refs": [asdict(pin) for pin in trace_context_refs],
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
