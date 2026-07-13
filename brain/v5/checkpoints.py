"""Human checkpoint records for AITP v5."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.contracts import ContractError
from brain.v5.human_approval import verify_human_approval_receipt
from brain.v5.ids import prefixed_id
from brain.v5.models import HumanCheckpointRecord
from brain.v5.record_contracts import require_valid_human_checkpoint_record
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor, canonical_record_hash
from brain.v5.record_repository import RecordRepository, WritePolicy


def request_human_checkpoint(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    reason: str,
    requested_by: str,
    options: list[str] | None = None,
) -> HumanCheckpointRecord:
    if not options:
        raise ValueError("checkpoint options must not be empty")
    checkpoint_id = prefixed_id(
        "checkpoint",
        f"{topic_id}:{claim_id}:{reason}:{requested_by}",
        max_slug=64,
    )
    record = HumanCheckpointRecord(
        checkpoint_id=checkpoint_id,
        topic_id=topic_id,
        claim_id=claim_id,
        reason=reason,
        requested_by=requested_by,
        options=options or [],
    )
    _require_valid_checkpoint(record)
    _repository(ws, actor_type="tool", actor_id="request_human_checkpoint").write(
        "checkpoints",
        record,
        body=f"# Human Checkpoint: {checkpoint_id}\n\n**Reason:** {reason}\n\n"
        f"**Options:** {', '.join(record.options)}\n",
    )
    return record


def decide_human_checkpoint(
    ws: WorkspacePaths,
    *,
    checkpoint_id: str,
    decision: str,
    rationale: str,
    decided_by: str,
    approval_receipt: dict | None = None,
) -> HumanCheckpointRecord:
    repository = _repository(
        ws,
        actor_type="tool",
        actor_id="decide_human_checkpoint",
    )
    current = repository.read(f"human_checkpoint:{checkpoint_id}")
    if current.status != "found" or current.record is None:
        raise ValueError(f"human checkpoint not found: {checkpoint_id}")
    target = current.record
    _require_valid_checkpoint(target)
    if target.status == "decided":
        raise ValueError(f"checkpoint {checkpoint_id} is already decided")
    if decision not in target.options:
        raise ValueError(f"decision {decision!r} must be one of options {target.options}")
    frontmatter = current.frontmatter or {}
    expected_hash = str(frontmatter.get("record_content_hash") or "")
    if not expected_hash:
        expected_hash = canonical_record_hash(frontmatter, current.body)
    verification = verify_human_approval_receipt(
        ws,
        checkpoint_id=checkpoint_id,
        checkpoint_content_hash=expected_hash,
        decision=decision,
        rationale=rationale,
        decided_by=decided_by,
        approval_receipt=approval_receipt,
    )
    target.status = "decided"
    target.decision = decision
    target.rationale = rationale
    target.decided_by = decided_by
    target.decision_verified = verification.decision_verified
    target.decision_verification = verification.method
    target.decision_receipt_hash = verification.receipt_hash
    target.decision_receipt_nonce = verification.nonce
    target.can_authorize_trust = verification.can_authorize_trust
    _require_valid_checkpoint(target)
    repository.write(
        "checkpoints",
        target,
        body=f"# Human Checkpoint: {checkpoint_id}\n\n"
        f"**Decision:** {decision} by {decided_by}\n\n**Rationale:** {rationale}\n",
        policy=WritePolicy(mode="revision", expected_hash=expected_hash),
    )
    return target


def _require_valid_checkpoint(record: HumanCheckpointRecord) -> None:
    try:
        require_valid_human_checkpoint_record({"ok": True, **asdict(record)})
    except ContractError as exc:
        raise ValueError(str(exc)) from exc


def _repository(
    ws: WorkspacePaths,
    *,
    actor_type: str,
    actor_id: str,
) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(actor_type=actor_type, actor_id=actor_id, host="aitp"),
    )
