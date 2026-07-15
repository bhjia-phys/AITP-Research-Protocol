"""Reviewed target-side applicability decisions for cross-topic execution use."""

from __future__ import annotations

import hashlib
import json
from contextlib import nullcontext
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from typing import Any, Mapping

from brain.v5.checkpoint_bindings import CheckpointSubjectBinding, hash_action_payload
from brain.v5.checkpoint_transactions import apply_bound_checkpoint_action
from brain.v5.lifecycle_models import CrossTopicRelationRecord
from brain.v5.models import (
    ScopeRevalidationDecisionRecord,
    ValidationResultRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository


@dataclass(frozen=True)
class ScopeRevalidationRequest:
    bridge: PinnedRecordRef
    source_refs: tuple[PinnedRecordRef, ...]
    source_scope_refs: tuple[str, ...]
    target_topic_id: str
    target_claim_id: str
    target_program_id: str
    target_scope_refs: tuple[str, ...]
    allowed_operations: tuple[str, ...]
    applicability_conditions: tuple[str, ...]
    validation_refs: tuple[PinnedRecordRef, ...]
    evidence_refs: tuple[PinnedRecordRef, ...]
    decision: str
    expires_at: str
    supersedes_decision: PinnedRecordRef | None = None

    def action_payload(self) -> dict[str, Any]:
        return {
            "bridge": asdict(self.bridge),
            "source_refs": [asdict(item) for item in sorted(self.source_refs)],
            "source_scope_refs": sorted(self.source_scope_refs),
            "target_topic_id": self.target_topic_id,
            "target_claim_id": self.target_claim_id,
            "target_program_id": self.target_program_id,
            "target_scope_refs": sorted(self.target_scope_refs),
            "allowed_operations": sorted(self.allowed_operations),
            "applicability_conditions": list(self.applicability_conditions),
            "validation_refs": [asdict(item) for item in sorted(self.validation_refs)],
            "evidence_refs": [asdict(item) for item in sorted(self.evidence_refs)],
            "decision": self.decision,
            "expires_at": _parse_timestamp(self.expires_at, "expires_at").isoformat(),
            "supersedes_decision": (
                asdict(self.supersedes_decision) if self.supersedes_decision else None
            ),
        }


@dataclass(frozen=True)
class ScopeRevalidationCapture:
    record: ScopeRevalidationDecisionRecord
    pinned_ref: PinnedRecordRef
    application_receipt_ref: PinnedRecordRef
    write_status: str


def record_scope_revalidation(
    ws: WorkspacePaths,
    request: ScopeRevalidationRequest,
    *,
    binding: CheckpointSubjectBinding,
    checkpoint_request_ref: PinnedRecordRef | Mapping[str, Any],
    checkpoint_decision_ref: PinnedRecordRef | Mapping[str, Any],
    actor: RecordActor,
    now: datetime | None = None,
) -> ScopeRevalidationCapture:
    """Persist one exact reviewed decision without transferring claim trust."""

    current_time = _utc(now)
    expiration = _parse_timestamp(request.expires_at, "expires_at")
    if expiration <= current_time:
        raise ValueError("scope revalidation request has expired")
    _validate_request_shape(request)
    bridge_version = get_record_version(ws, request.bridge)
    bridge = bridge_version.record
    if not isinstance(bridge, CrossTopicRelationRecord):
        raise ValueError("bridge must reference a cross-topic relation")
    if bridge.status not in {"reviewed", "approved"}:
        raise ValueError("cross-topic bridge is not reviewed")
    if bridge.target_topic_id != request.target_topic_id:
        raise ValueError("bridge target topic does not match revalidation target")

    for source_ref in request.source_refs:
        source_version = get_record_version(ws, source_ref)
        source_topic = _record_topic(source_version.record)
        if source_topic and source_topic != bridge.source_topic_id:
            raise ValueError("scope revalidation source belongs to the wrong topic")
    for validation_ref in request.validation_refs:
        version = get_record_version(ws, validation_ref)
        validation = version.record
        if not isinstance(validation, ValidationResultRecord) or validation.status != "passed":
            raise ValueError("approved scope revalidation requires passed validation results")
        if validation.topic_id != request.target_topic_id:
            raise ValueError("scope revalidation validation belongs to the wrong target topic")
        if not validation.executor_id or not validation.executor_version or not validation.executor_hash:
            raise ValueError("scope revalidation validation must pin its executor")
    for evidence_ref in request.evidence_refs:
        get_record_version(ws, evidence_ref)

    supersedes = request.supersedes_decision
    if supersedes is not None:
        previous = get_record_version(ws, supersedes).record
        if not isinstance(previous, ScopeRevalidationDecisionRecord):
            raise ValueError("supersedes_decision must pin a scope revalidation decision")
        if previous.bridge_ref != request.bridge.record_ref:
            raise ValueError("superseded decision uses a different bridge")
        if previous.topic_id != request.target_topic_id:
            raise ValueError("superseded decision uses a different target topic")
        if previous.claim_id != request.target_claim_id or previous.program_id != request.target_program_id:
            raise ValueError("superseded decision uses a different target scope")
        if {_coerce_pin(item) for item in previous.source_refs} != set(request.source_refs):
            raise ValueError("superseded decision uses different source refs")
        if set(previous.source_scope_refs) != set(request.source_scope_refs):
            raise ValueError("superseded decision uses different source scopes")
        if set(previous.target_scope_refs) != set(request.target_scope_refs):
            raise ValueError("superseded decision uses different target scopes")

    request_pin = _coerce_pin(checkpoint_request_ref)
    decision_pin = _coerce_pin(checkpoint_decision_ref)
    if binding.action != "approve_scope_revalidation":
        raise ValueError("scope revalidation checkpoint action does not match")
    if binding.effect_policy != "scope_revalidation_only":
        raise ValueError("scope revalidation checkpoint effect policy does not match")
    expected_payload_hash = hash_action_payload(request.action_payload())
    if binding.action_payload_hash != expected_payload_hash:
        raise ValueError("scope revalidation checkpoint payload does not match")
    expected_subjects = {request.bridge, *request.source_refs}
    if set(binding.subjects) != expected_subjects:
        raise ValueError("scope revalidation checkpoint subjects do not match")
    if set(binding.target_scope_refs) != set(request.target_scope_refs):
        raise ValueError("scope revalidation checkpoint target scopes do not match")

    identity = {
        **request.action_payload(),
        "checkpoint": asdict(decision_pin),
    }
    identity_hash = _sha256_json(identity)
    record = ScopeRevalidationDecisionRecord(
        decision_id=f"scope-revalidation-{identity_hash}",
        bridge_ref=request.bridge.record_ref,
        bridge_hash=request.bridge.content_hash,
        bridge_revision=request.bridge.revision,
        decision=request.decision,
        topic_id=request.target_topic_id,
        claim_id=request.target_claim_id,
        program_id=request.target_program_id,
        source_scope_refs=sorted(set(request.source_scope_refs)),
        target_scope_refs=sorted(set(request.target_scope_refs)),
        allowed_operations=sorted(set(request.allowed_operations)),
        source_refs=[asdict(item) for item in sorted(request.source_refs)],
        applicability_conditions=list(request.applicability_conditions),
        validation_refs=[asdict(item) for item in sorted(request.validation_refs)],
        evidence_refs=[asdict(item) for item in sorted(request.evidence_refs)],
        checkpoint_refs=[asdict(decision_pin)],
        expires_at=expiration.isoformat(),
        supersedes_decision_ref=supersedes.record_ref if supersedes else "",
        supersedes_decision_hash=supersedes.content_hash if supersedes else "",
        supersedes_decision_revision=supersedes.revision if supersedes else 0,
    )
    repository = RecordRepository(ws, actor=actor)
    write_status = "unchanged"

    def write_result(_application_id: str) -> PinnedRecordRef:
        nonlocal write_status
        write = repository.write(
            "scope_revalidation_decisions",
            record,
            body=(
                f"# Scope Revalidation: {record.decision_id}\n\n"
                f"Target topic: `{record.topic_id}`\n\n"
                f"Decision: `{record.decision}`\n"
            ),
        )
        write_status = write.status
        return PinnedRecordRef(
            record_ref=write.record_ref,
            content_hash=write.content_hash,
            revision=write.revision,
        )

    def resolve_result(_application_id: str) -> PinnedRecordRef | None:
        record_ref = f"scope_revalidation_decision:{record.decision_id}"
        if repository.read(record_ref).status != "found":
            return None
        from brain.v5.pinned_record_refs import pin_current_record

        return pin_current_record(ws, record_ref)

    def validate_result(_application_id: str, result: PinnedRecordRef) -> None:
        expected = f"scope_revalidation_decision:{record.decision_id}"
        if result.record_ref != expected:
            raise ValueError("scope revalidation result does not belong to application")
        stored = get_record_version(ws, result).record
        if not isinstance(stored, ScopeRevalidationDecisionRecord) or stored != record:
            raise ValueError("scope revalidation result content does not match application")

    lock = (
        repository.lock_record("scope_revalidation_decisions", previous.decision_id)
        if supersedes is not None
        else nullcontext()
    )
    with lock:
        if supersedes is not None:
            _ensure_available_successor(repository, supersedes, record.decision_id)
        application = apply_bound_checkpoint_action(
            ws,
            binding=binding,
            request_ref=request_pin,
            decision_ref=decision_pin,
            action_payload=request.action_payload(),
            result_writer=write_result,
            result_resolver=resolve_result,
            result_validator=validate_result,
            actor=actor,
            now=current_time,
        )
    if application.result_ref is None:
        raise RuntimeError("scope revalidation application produced no decision")
    stored = get_record_version(ws, application.result_ref).record
    if not isinstance(stored, ScopeRevalidationDecisionRecord):
        raise RuntimeError("scope revalidation result is not a scope decision")
    return ScopeRevalidationCapture(
        record=stored,
        pinned_ref=application.result_ref,
        application_receipt_ref=application.receipt_ref,
        write_status=write_status,
    )


def _ensure_available_successor(
    repository: RecordRepository,
    prior: PinnedRecordRef,
    proposed_id: str,
) -> None:
    report = repository.list("scope_revalidation_decisions")
    if report.malformed:
        raise ValueError("scope revalidation decisions are not exhaustively readable")
    for candidate in report.records:
        if not isinstance(candidate, ScopeRevalidationDecisionRecord):
            raise ValueError("scope revalidation family contains an unexpected record")
        if (
            candidate.supersedes_decision_ref == prior.record_ref
            and candidate.supersedes_decision_hash == prior.content_hash
            and candidate.supersedes_decision_revision == prior.revision
            and candidate.decision_id != proposed_id
        ):
            raise ValueError("scope revalidation decision already has a successor")


def _validate_request_shape(request: ScopeRevalidationRequest) -> None:
    if request.decision not in {"approved", "rejected"}:
        raise ValueError("scope revalidation decision must be approved or rejected")
    for field_name, value in (
        ("target_topic_id", request.target_topic_id),
        ("target_claim_id", request.target_claim_id),
    ):
        if not str(value).strip():
            raise ValueError(f"{field_name} must be non-empty")
    if not request.source_refs:
        raise ValueError("scope revalidation source_refs must not be empty")
    if f"topic:{request.target_topic_id}" not in request.target_scope_refs:
        raise ValueError("target_scope_refs must include the target topic")
    if request.target_claim_id and f"claim:{request.target_claim_id}" not in request.target_scope_refs:
        raise ValueError("target_scope_refs must include the target claim")
    if request.decision == "approved":
        if not request.allowed_operations:
            raise ValueError("approved scope revalidation requires allowed operations")
        if not request.applicability_conditions:
            raise ValueError("approved scope revalidation requires applicability conditions")
        if not request.validation_refs:
            raise ValueError("approved scope revalidation requires validation refs")


def _record_topic(record: Any) -> str:
    if is_dataclass(record):
        return str(asdict(record).get("topic_id") or "")
    if isinstance(record, Mapping):
        return str(record.get("topic_id") or "")
    return ""


def _coerce_pin(value: PinnedRecordRef | Mapping[str, Any]) -> PinnedRecordRef:
    if isinstance(value, PinnedRecordRef):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("scope revalidation refs must be exact pinned refs")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )


def _parse_timestamp(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return parsed.astimezone(UTC)


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
