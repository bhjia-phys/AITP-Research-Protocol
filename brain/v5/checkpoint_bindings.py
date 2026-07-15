"""Exact action, intent, subject, request, and decision checkpoint bindings."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, Mapping, Sequence

from brain.v5.checkpoints import decide_human_checkpoint
from brain.v5.human_approval import checkpoint_can_authorize_trust
from brain.v5.models import HumanCheckpointRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import (
    PinnedRecordRef,
    PinnedRecordVersion,
    get_record_version,
    pin_current_record,
)
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository


@dataclass(frozen=True)
class CheckpointSubjectBinding:
    intent: PinnedRecordRef
    subjects: tuple[PinnedRecordRef, ...]
    action: str
    action_payload_hash: str
    request_hash: str
    target_scope_refs: tuple[str, ...]
    effect_policy: str
    replay_policy: str


@dataclass(frozen=True)
class BoundCheckpointRequest:
    record: HumanCheckpointRecord
    request_ref: PinnedRecordRef
    binding: CheckpointSubjectBinding
    write_status: str


@dataclass(frozen=True)
class BoundCheckpointDecision:
    record: HumanCheckpointRecord
    request_ref: PinnedRecordRef
    decision_ref: PinnedRecordRef
    binding: CheckpointSubjectBinding


def hash_action_payload(payload: Mapping[str, Any]) -> str:
    """Hash one JSON-compatible action payload without persisting its contents."""

    if not isinstance(payload, Mapping):
        raise TypeError("action_payload must be a mapping")
    return _sha256_json(dict(payload))


def request_bound_checkpoint(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    reason: str,
    requested_by: str,
    action: str,
    action_payload: Mapping[str, Any],
    intent_ref: PinnedRecordRef | Mapping[str, Any],
    subject_refs: Sequence[PinnedRecordRef | Mapping[str, Any]],
    options: Sequence[str],
    expires_at: str,
    replay_policy: str,
    target_scope_refs: Sequence[str],
    effect_policy: str,
    actor: RecordActor,
    now: datetime | None = None,
) -> BoundCheckpointRequest:
    """Write an idempotent open checkpoint bound to exact canonical versions."""

    required = {
        "topic_id": topic_id,
        "claim_id": claim_id,
        "reason": reason,
        "requested_by": requested_by,
        "action": action,
        "effect_policy": effect_policy,
        "replay_policy": replay_policy,
    }
    for field_name, value in required.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
    normalized_options = tuple(_nonempty_strings(options, "options"))
    if not normalized_options:
        raise ValueError("options must not be empty")
    normalized_scopes = tuple(sorted(set(_nonempty_strings(target_scope_refs, "target_scope_refs"))))
    if not normalized_scopes:
        raise ValueError("target_scope_refs must not be empty")
    expiration = _parse_timestamp(expires_at, "expires_at")
    current_time = _utc(now)
    if expiration <= current_time:
        raise ValueError("expires_at must be in the future")

    intent = _coerce_pin(intent_ref)
    subjects = tuple(sorted({_coerce_pin(item) for item in subject_refs}))
    if not subjects:
        raise ValueError("subject_refs must not be empty")
    _resolve_all(ws, (intent, *subjects))
    payload_hash = hash_action_payload(action_payload)
    request_identity = {
        "topic_id": topic_id.strip(),
        "claim_id": claim_id.strip(),
        "reason": reason.strip(),
        "requested_by": requested_by.strip(),
        "action": action.strip(),
        "action_payload_hash": payload_hash,
        "intent": asdict(intent),
        "subjects": [asdict(item) for item in subjects],
        "options": list(normalized_options),
        "expires_at": expiration.isoformat(),
        "replay_policy": replay_policy.strip(),
        "target_scope_refs": list(normalized_scopes),
        "effect_policy": effect_policy.strip(),
    }
    request_hash = _sha256_json(request_identity)
    binding = CheckpointSubjectBinding(
        intent=intent,
        subjects=subjects,
        action=action.strip(),
        action_payload_hash=payload_hash,
        request_hash=request_hash,
        target_scope_refs=normalized_scopes,
        effect_policy=effect_policy.strip(),
        replay_policy=replay_policy.strip(),
    )
    checkpoint_id = f"checkpoint-bound-{request_hash}"
    record = HumanCheckpointRecord(
        checkpoint_id=checkpoint_id,
        topic_id=topic_id.strip(),
        claim_id=claim_id.strip(),
        reason=reason.strip(),
        requested_by=requested_by.strip(),
        options=list(normalized_options),
        intent_ref=intent.record_ref,
        intent_hash=intent.content_hash,
        intent_revision=intent.revision,
        action=binding.action,
        subject_refs=[asdict(item) for item in subjects],
        request_hash=request_hash,
        payload_hash=payload_hash,
        expires_at=expiration.isoformat(),
        replay_policy=binding.replay_policy,
        target_scope_refs=list(normalized_scopes),
        effect_policy=binding.effect_policy,
    )
    write = RecordRepository(ws, actor=actor).write(
        "checkpoints",
        record,
        body=(
            f"# Bound Human Checkpoint: {checkpoint_id}\n\n"
            f"**Reason:** {record.reason}\n\n"
            f"**Action:** {record.action}\n"
        ),
    )
    return BoundCheckpointRequest(
        record=record,
        request_ref=PinnedRecordRef(
            record_ref=write.record_ref,
            content_hash=write.content_hash,
            revision=write.revision,
        ),
        binding=binding,
        write_status=write.status,
    )


def decide_bound_checkpoint(
    ws: WorkspacePaths,
    *,
    request_ref: PinnedRecordRef | Mapping[str, Any],
    expected: CheckpointSubjectBinding,
    decision: str,
    rationale: str,
    decided_by: str,
    approval_receipt: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> BoundCheckpointDecision:
    """Revise one exact open request into a host-attested bound decision."""

    request_pin = _coerce_pin(request_ref)
    request_version = validate_checkpoint_binding(
        ws,
        request_pin,
        expected,
        now=now,
    )
    if request_version.record.status != "open":
        raise ValueError("bound checkpoint request is not open")
    current = pin_current_record(ws, request_pin.record_ref)
    if current != request_pin:
        raise ValueError("bound checkpoint request is not the current exact revision")
    checkpoint_id = request_pin.record_ref.partition(":")[2]
    decided = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint_id,
        decision=decision,
        rationale=rationale,
        decided_by=decided_by,
        approval_receipt=approval_receipt,
    )
    decision_pin = pin_current_record(ws, request_pin.record_ref)
    decision_version = validate_checkpoint_binding(
        ws,
        decision_pin,
        expected,
        now=now,
        require_decided=True,
    )
    predecessor = f"{request_pin.record_ref}@sha256:{request_pin.content_hash}"
    supersedes = decision_version.frontmatter.get("supersedes") or []
    if decision_pin.revision != request_pin.revision + 1 or predecessor not in supersedes:
        raise ValueError("bound checkpoint decision does not supersede the pinned request")
    return BoundCheckpointDecision(
        record=decided,
        request_ref=request_pin,
        decision_ref=decision_pin,
        binding=expected,
    )


def validate_checkpoint_binding(
    ws: WorkspacePaths,
    checkpoint_ref: PinnedRecordRef | Mapping[str, Any],
    expected: CheckpointSubjectBinding,
    *,
    now: datetime | None = None,
    require_decided: bool = False,
) -> PinnedRecordVersion:
    """Fail closed unless one exact checkpoint version matches the full binding."""

    pinned = _coerce_pin(checkpoint_ref)
    version = get_record_version(ws, pinned)
    record = version.record
    if not isinstance(record, HumanCheckpointRecord) or not _is_v2_bound(record):
        raise ValueError("checkpoint is not a v2 bound checkpoint")
    if record.action != expected.action:
        raise ValueError("checkpoint action does not match expected binding")
    if record.payload_hash != expected.action_payload_hash:
        raise ValueError("checkpoint payload hash does not match expected binding")
    if record.request_hash != expected.request_hash:
        raise ValueError("checkpoint request hash does not match expected binding")
    actual_intent = PinnedRecordRef(
        record_ref=record.intent_ref,
        content_hash=record.intent_hash,
        revision=record.intent_revision,
    )
    if actual_intent != expected.intent:
        raise ValueError("checkpoint intent does not match expected binding")
    actual_subjects = tuple(sorted(_coerce_pin(item) for item in record.subject_refs))
    if actual_subjects != tuple(sorted(expected.subjects)):
        raise ValueError("checkpoint subjects do not match expected binding")
    if tuple(sorted(record.target_scope_refs)) != tuple(sorted(expected.target_scope_refs)):
        raise ValueError("checkpoint target scopes do not match expected binding")
    if record.effect_policy != expected.effect_policy:
        raise ValueError("checkpoint effect policy does not match expected binding")
    if record.replay_policy != expected.replay_policy:
        raise ValueError("checkpoint replay policy does not match expected binding")
    if _parse_timestamp(record.expires_at, "expires_at") <= _utc(now):
        raise ValueError("bound checkpoint has expired")
    _resolve_all(ws, (actual_intent, *actual_subjects))
    if require_decided:
        if record.status != "decided" or record.decision != "approve":
            raise ValueError("bound checkpoint is not an approved decision")
        if not checkpoint_can_authorize_trust(record):
            raise ValueError("bound checkpoint decision lacks host-verified approval")
    return version


def _is_v2_bound(record: HumanCheckpointRecord) -> bool:
    return bool(
        record.intent_ref
        and record.intent_hash
        and record.intent_revision > 0
        and record.action
        and record.subject_refs
        and record.request_hash
        and record.payload_hash
        and record.expires_at
        and record.replay_policy
        and record.effect_policy
    )


def _resolve_all(ws: WorkspacePaths, refs: Sequence[PinnedRecordRef]) -> None:
    for pinned in refs:
        get_record_version(ws, pinned)


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


def _nonempty_strings(values: Sequence[str], field_name: str) -> list[str]:
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must contain non-empty strings")
        normalized.append(value.strip())
    return normalized


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
