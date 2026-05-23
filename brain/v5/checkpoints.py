"""Human checkpoint records for AITP v5."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.contracts import ContractError
from brain.v5.ids import prefixed_id
from brain.v5.models import HumanCheckpointRecord
from brain.v5.record_contracts import require_valid_human_checkpoint_record
from brain.v5.paths import WorkspacePaths
from brain.v5.store import write_record, list_records


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
    write_record(
        ws.registry_dir("checkpoints") / f"{checkpoint_id}.md",
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
) -> HumanCheckpointRecord:
    records = list_records(ws.registry_dir("checkpoints"), HumanCheckpointRecord)
    target = next(r for r in records if r.checkpoint_id == checkpoint_id)
    _require_valid_checkpoint(target)
    if target.status == "decided":
        raise ValueError(f"checkpoint {checkpoint_id} is already decided")
    if decision not in target.options:
        raise ValueError(f"decision {decision!r} must be one of options {target.options}")
    target.status = "decided"
    target.decision = decision
    target.rationale = rationale
    target.decided_by = decided_by
    _require_valid_checkpoint(target)
    write_record(
        ws.registry_dir("checkpoints") / f"{checkpoint_id}.md",
        target,
        body=f"# Human Checkpoint: {checkpoint_id}\n\n"
        f"**Decision:** {decision} by {decided_by}\n\n**Rationale:** {rationale}\n",
    )
    return target


def _require_valid_checkpoint(record: HumanCheckpointRecord) -> None:
    try:
        require_valid_human_checkpoint_record({"ok": True, **asdict(record)})
    except ContractError as exc:
        raise ValueError(str(exc)) from exc
