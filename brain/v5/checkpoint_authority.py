"""Cryptographic authority verification for exact human-checkpoint revisions."""

from __future__ import annotations

from dataclasses import fields
from datetime import datetime
from typing import Any

from brain.v5.human_approval import (
    checkpoint_can_authorize_trust,
    verify_human_approval_receipt,
)
from brain.v5.models import HumanCheckpointRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import (
    PinnedRecordRef,
    PinnedRecordVersion,
    get_record_version,
)


_DECISION_FIELDS = frozenset(
    {
        "status",
        "decision",
        "rationale",
        "decided_by",
        "decision_verified",
        "decision_verification",
        "decision_receipt_hash",
        "decision_receipt_nonce",
        "can_authorize_trust",
    }
)


def require_verified_checkpoint_authority(
    ws: WorkspacePaths,
    decision_version: PinnedRecordVersion,
) -> PinnedRecordVersion:
    """Reverify one signed decision and its exact open-request predecessor."""

    decision = decision_version.record
    if not isinstance(decision, HumanCheckpointRecord):
        raise ValueError("checkpoint decision is not a human checkpoint")
    if not checkpoint_can_authorize_trust(decision):
        raise ValueError("checkpoint decision lacks host-verified approval metadata")
    request_version = _resolve_request_predecessor(ws, decision_version)
    request = request_version.record
    if not isinstance(request, HumanCheckpointRecord) or request.status != "open":
        raise ValueError("checkpoint decision predecessor is not an open request")
    _require_exact_decision_transition(request, decision)
    _require_decision_writer(decision_version.frontmatter)
    decision_time = _decision_time(decision_version.frontmatter)
    try:
        verification = verify_human_approval_receipt(
            ws,
            checkpoint_id=decision.checkpoint_id,
            checkpoint_content_hash=request_version.pinned_ref.content_hash,
            decision=decision.decision,
            rationale=decision.rationale,
            decided_by=decision.decided_by,
            now=decision_time,
        )
    except ValueError as exc:
        raise ValueError(
            f"checkpoint decision lacks host-verified approval: {exc}"
        ) from exc
    if (
        verification.decision_verified is not decision.decision_verified
        or verification.method != decision.decision_verification
        or verification.receipt_hash != decision.decision_receipt_hash
        or verification.nonce != decision.decision_receipt_nonce
        or verification.can_authorize_trust is not decision.can_authorize_trust
    ):
        raise ValueError("checkpoint decision receipt does not match persisted metadata")
    return request_version


def _resolve_request_predecessor(
    ws: WorkspacePaths,
    decision_version: PinnedRecordVersion,
) -> PinnedRecordVersion:
    decision_ref = decision_version.pinned_ref
    if decision_ref.revision < 2:
        raise ValueError("checkpoint decision has no request predecessor revision")
    supersedes = decision_version.frontmatter.get("supersedes") or []
    if not isinstance(supersedes, list) or not supersedes:
        raise ValueError("checkpoint decision does not declare a request predecessor")
    prefix = f"{decision_ref.record_ref}@sha256:"
    immediate = str(supersedes[0])
    if not immediate.startswith(prefix):
        raise ValueError("checkpoint decision immediate predecessor is malformed")
    request_ref = PinnedRecordRef(
        record_ref=decision_ref.record_ref,
        content_hash=immediate[len(prefix) :],
        revision=decision_ref.revision - 1,
    )
    return get_record_version(ws, request_ref)


def _require_exact_decision_transition(
    request: HumanCheckpointRecord,
    decision: HumanCheckpointRecord,
) -> None:
    for field in fields(HumanCheckpointRecord):
        if field.name in _DECISION_FIELDS:
            continue
        if getattr(request, field.name) != getattr(decision, field.name):
            raise ValueError(
                f"checkpoint decision changed immutable request field: {field.name}"
            )
    if any(
        (
            request.decision,
            request.rationale,
            request.decided_by,
            request.decision_verification,
            request.decision_receipt_hash,
            request.decision_receipt_nonce,
        )
    ) or request.decision_verified or request.can_authorize_trust:
        raise ValueError("checkpoint request predecessor already contains decision authority")


def _require_decision_writer(frontmatter: dict[str, Any]) -> None:
    actor = frontmatter.get("created_by") or {}
    if actor != {
        "actor_type": "tool",
        "actor_id": "decide_human_checkpoint",
        "host": "aitp",
    }:
        raise ValueError("checkpoint decision was not written by the decision tool")


def _decision_time(frontmatter: dict[str, Any]) -> datetime:
    value = str(frontmatter.get("created_at") or "")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("checkpoint decision created_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("checkpoint decision created_at must include a timezone")
    return parsed
