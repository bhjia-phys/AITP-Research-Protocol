"""Read-only admissibility audit for evidence support and trace context."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from typing import Any, Mapping

from brain.v5.models import (
    EvidenceRecord,
    ReferenceLocationRecord,
    ToolRunRecord,
    ValidationResultRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.evidence_support_policy import (
    evidence_support_record_ids,
    support_record_policy_errors,
)


_ADMISSIBLE_SUPPORT_KINDS = frozenset(
    {"source_asset", "reference_location", "tool_run", "validation_result", "artifact"}
)


@dataclass(frozen=True)
class EvidenceBasisRefAudit:
    role: str
    record_ref: str
    content_hash: str
    revision: int
    record_kind: str
    classification: str
    topic_id: str
    errors: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceBasisAudit:
    admissible: bool
    support_basis_refs: tuple[PinnedRecordRef, ...]
    trace_context_refs: tuple[PinnedRecordRef, ...]
    checked_refs: tuple[str, ...]
    ref_audits: tuple[EvidenceBasisRefAudit, ...]
    errors: tuple[str, ...]
    payload_hash: str
    audit_hash: str
    policy_version: str = "evidence_basis_v1"
    can_update_claim_trust: bool = False


@dataclass(frozen=True)
class EvidencePromotionPolicyBlock:
    policy_id: str
    message: str
    required_action: str


def promotion_evidence_policy_blocks(
    *,
    evidence_refs: list[str],
    evidence_records: list[EvidenceRecord],
    validation_results: list[ValidationResultRecord],
    risk_level: str,
) -> tuple[EvidencePromotionPolicyBlock, ...]:
    """Return trust-neutral blocks for evidence used in claim promotion."""

    blocks: list[EvidencePromotionPolicyBlock] = []
    resolved = {record.evidence_id for record in evidence_records}
    if evidence_refs and not set(evidence_refs) <= resolved:
        blocks.append(
            EvidencePromotionPolicyBlock(
                policy_id="inadmissible_evidence_basis",
                message="L2 promotion requires every evidence ref to have a current admissible basis audit",
                required_action="record_or_review_evidence_basis",
            )
        )

    tool_run_ids = {
        run_id for evidence in evidence_records for run_id in evidence_support_record_ids(evidence, "tool_run")
    }
    if not tool_run_ids:
        return tuple(blocks)
    passed_tool_runs = {
        result.tool_run_id
        for result in validation_results
        if result.status == "passed"
        and not result.missing_outputs
        and not result.failure_modes_observed
    }
    high_risk = risk_level in {"rigorous", "adversarial"}
    if not passed_tool_runs:
        blocks.append(
            EvidencePromotionPolicyBlock(
                policy_id=(
                    "high_risk_promotion_requires_validation_result"
                    if high_risk
                    else "tool_evidence_requires_validation_result"
                ),
                message="tool-derived evidence requires matching passed validation-result refs before L2 promotion",
                required_action="attach_passed_validation_result",
            )
        )
    elif not tool_run_ids.issubset(passed_tool_runs):
        blocks.append(
            EvidencePromotionPolicyBlock(
                policy_id=(
                    "high_risk_promotion_validation_result_mismatch"
                    if high_risk
                    else "tool_evidence_validation_result_mismatch"
                ),
                message="provided validation results do not pass every tool-derived evidence run in the promotion packet",
                required_action="attach_matching_validation_result",
            )
        )
    return tuple(blocks)


def trust_update_evidence_policy_blocks(
    *,
    evidence_refs: list[str],
    evidence_records: list[EvidenceRecord],
    validation_results: list[ValidationResultRecord],
    requested_state: str,
) -> tuple[EvidencePromotionPolicyBlock, ...]:
    """Reject cited evidence that cannot justify a direct confidence update."""

    if not evidence_refs:
        if requested_state in {"locally_checked", "validated", "human_accepted"}:
            return (
                EvidencePromotionPolicyBlock(
                    policy_id="checked_confidence_requires_evidence",
                    message="checked confidence requires exact admissible evidence",
                    required_action="record_supporting_evidence",
                ),
            )
        return ()
    wanted = {
        ref.split(":", 1)[1] if ref.startswith("evidence:") else ref
        for ref in evidence_refs
    }
    resolved = {record.evidence_id for record in evidence_records}
    if wanted != resolved:
        return (
            EvidencePromotionPolicyBlock(
                policy_id="claim_confidence_requires_admissible_evidence",
                message="every cited confidence-update evidence record must have an admissible exact basis",
                required_action="record_or_review_evidence_basis",
            ),
        )
    if requested_state not in {"locally_checked", "validated", "human_accepted"}:
        return ()
    required_result_ids = {
        result_id
        for evidence in evidence_records
        for result_id in evidence_support_record_ids(evidence, "validation_result")
    }
    passed_result_ids = {
        result.result_id
        for result in validation_results
        if result.status == "passed"
        and not result.missing_outputs
        and not result.failure_modes_observed
    }
    if required_result_ids and required_result_ids <= passed_result_ids:
        return ()
    return (
        EvidencePromotionPolicyBlock(
            policy_id="checked_confidence_requires_validation_result",
            message="checked confidence requires a pinned passed validation result",
            required_action="record_validation_result",
        ),
    )


def audit_evidence_basis(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    support_basis_refs: tuple[PinnedRecordRef, ...],
    trace_context_refs: tuple[PinnedRecordRef, ...],
    evidence_payload: Mapping[str, Any],
    require_current: bool = True,
) -> EvidenceBasisAudit:
    """Validate exact evidence dependencies without writing or changing trust."""

    errors: list[str] = []
    checked: list[str] = []
    ref_audits: list[EvidenceBasisRefAudit] = []
    support_records: list[tuple[PinnedRecordRef, Any]] = []
    if not support_basis_refs:
        errors.append("support_basis_refs_required")
    for lane, pins in (
        ("support", support_basis_refs),
        ("trace", trace_context_refs),
    ):
        for pin in pins:
            checked.append(pin.record_ref)
            kind = pin.record_ref.split(":", 1)[0]
            try:
                if require_current and pin_current_record(ws, pin.record_ref) != pin:
                    raise ValueError("stale pin")
                record = get_record_version(ws, pin).record
            except (ValueError, RuntimeError) as exc:
                error = f"unresolved_{lane}_ref:{pin.record_ref}:{exc}"
                errors.append(error)
                ref_audits.append(
                    EvidenceBasisRefAudit(
                        role=lane,
                        record_ref=pin.record_ref,
                        content_hash=pin.content_hash,
                        revision=pin.revision,
                        record_kind=kind,
                        classification="unresolved",
                        topic_id="",
                        errors=(error,),
                    )
                )
                continue
            ref_errors: list[str] = []
            record_topic = str(getattr(record, "topic_id", "") or "")
            if topic_id and record_topic and record_topic != topic_id:
                error = f"{lane}_scope_mismatch:{pin.record_ref}"
                errors.append(error)
                ref_errors.append(error)
            if lane == "support":
                support_records.append((pin, record))
                if kind not in _ADMISSIBLE_SUPPORT_KINDS:
                    error = f"inadmissible_support_kind:{kind}"
                    errors.append(error)
                    ref_errors.append(error)
            ref_audits.append(
                EvidenceBasisRefAudit(
                    role=lane,
                    record_ref=pin.record_ref,
                    content_hash=pin.content_hash,
                    revision=pin.revision,
                    record_kind=kind,
                    classification=(
                        f"{kind}_support"
                        if lane == "support" and kind in _ADMISSIBLE_SUPPORT_KINDS
                        else "inadmissible_support"
                        if lane == "support"
                        else f"{kind}_trace"
                    ),
                    topic_id=record_topic,
                    errors=tuple(ref_errors),
                )
            )

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
    located_asset_refs = {location.source_ref for location in locations}
    for asset_ref in sorted(asset_refs - located_asset_refs):
        error = f"exact_source_location_pin_missing:{asset_ref}"
        errors.append(error)
        ref_audits = _append_ref_error(ref_audits, asset_ref, error)
    for location in locations:
        if location.source_ref not in asset_refs:
            error = f"source_location_asset_pin_missing:{location.source_ref}"
            errors.append(error)
            location_ref = next(
                pin.record_ref
                for pin, record in support_records
                if record is location
            )
            ref_audits = _append_ref_error(ref_audits, location_ref, error)

    semantic_errors = support_record_policy_errors(
        support_records,
        claim_id=str(evidence_payload.get("claim_id") or ""),
    )
    for record_ref, record_errors in semantic_errors.items():
        for error in record_errors:
            errors.append(error)
            ref_audits = _append_ref_error(ref_audits, record_ref, error)

    payload_hash = _payload_hash(
        evidence_payload,
        support_basis_refs=support_basis_refs,
        trace_context_refs=trace_context_refs,
    )
    audit = EvidenceBasisAudit(
        admissible=not errors,
        support_basis_refs=support_basis_refs,
        trace_context_refs=trace_context_refs,
        checked_refs=tuple(checked),
        ref_audits=tuple(ref_audits),
        errors=tuple(dict.fromkeys(errors)),
        payload_hash=payload_hash,
        audit_hash="",
    )
    return replace(audit, audit_hash=evidence_basis_audit_hash(asdict(audit)))


def persisted_evidence_basis_is_admissible(
    ws: WorkspacePaths,
    evidence: Any,
) -> bool:
    """Re-audit a persisted v2 evidence record and verify its payload binding."""

    if getattr(evidence, "basis_policy_status", "") != "admissible":
        return False
    try:
        support = tuple(_coerce_pin(value) for value in evidence.support_basis_refs)
        trace = tuple(_coerce_pin(value) for value in evidence.trace_context_refs)
        audit = audit_evidence_basis(
            ws,
            topic_id=evidence.topic_id,
            support_basis_refs=support,
            trace_context_refs=trace,
            evidence_payload=evidence_policy_payload(evidence),
            require_current=False,
        )
    except (TypeError, ValueError, RuntimeError):
        return False
    stored_audit = evidence.basis_audit if isinstance(evidence.basis_audit, Mapping) else {}
    try:
        stored_audit_hash = evidence_basis_audit_hash(stored_audit)
    except (TypeError, ValueError):
        return False
    return bool(
        audit.admissible
        and evidence.basis_policy_version == audit.policy_version
        and evidence.basis_payload_hash == audit.payload_hash
        and stored_audit.get("admissible") is True
        and stored_audit.get("payload_hash") == audit.payload_hash
        and stored_audit.get("audit_hash") == audit.audit_hash
        and stored_audit_hash == audit.audit_hash
    )


def persisted_evidence_basis_is_trust_admissible(
    ws: WorkspacePaths,
    evidence: Any,
) -> bool:
    """Require grounded exact pins plus passed validation for tool-run support."""

    if not persisted_evidence_basis_is_admissible(ws, evidence):
        return False
    try:
        support = tuple(_coerce_pin(value) for value in evidence.support_basis_refs)
        records = [get_record_version(ws, pin).record for pin in support]
    except (TypeError, ValueError, RuntimeError):
        return False
    tool_runs = {
        record.run_id: record for record in records if isinstance(record, ToolRunRecord)
    }
    validation_results = [
        record for record in records if isinstance(record, ValidationResultRecord)
    ]
    return bool(
        all(
            any(_passed_validation_for_run(result, run_id) for result in validation_results)
            for run_id in tool_runs
        )
        and all(result.tool_run_id in tool_runs for result in validation_results)
    )


def evidence_policy_payload(evidence: Any) -> dict[str, Any]:
    return {
        "topic_id": evidence.topic_id,
        "claim_id": evidence.claim_id,
        "evidence_type": evidence.evidence_type,
        "status": evidence.status,
        "summary": evidence.summary,
        "supports_outputs": list(evidence.supports_outputs),
        "source_refs": list(evidence.source_refs),
        "tool_run_ids": list(evidence.tool_run_ids),
        "validation_result_ids": list(evidence.validation_result_ids),
        "artifact_ids": list(evidence.artifact_ids),
    }


def evidence_basis_audit_hash(audit: Mapping[str, Any]) -> str:
    """Hash every persisted audit field except the hash itself."""

    material = {str(key): value for key, value in audit.items() if key != "audit_hash"}
    encoded = json.dumps(
        material,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _append_ref_error(
    ref_audits: list[EvidenceBasisRefAudit],
    record_ref: str,
    error: str,
) -> list[EvidenceBasisRefAudit]:
    return [
        replace(item, errors=(*item.errors, error)) if item.record_ref == record_ref else item
        for item in ref_audits
    ]


def _coerce_pin(value: Any) -> PinnedRecordRef:
    if not isinstance(value, Mapping):
        raise TypeError("persisted evidence basis ref must be an exact pin")
    revision = value.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int):
        raise TypeError("persisted evidence basis revision must be an integer")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=revision,
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


def _passed_validation_for_run(result: ValidationResultRecord, run_id: str) -> bool:
    return bool(
        result.tool_run_id == run_id
        and result.status == "passed"
        and not result.missing_outputs
        and not result.failure_modes_observed
    )
