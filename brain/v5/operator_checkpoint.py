"""Topic-local vNext operator checkpoint surfaces."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.markdown import write_md
from brain.v5.paths import WorkspacePaths

_CHECKPOINT_KINDS = {
    "scope_ambiguity",
    "novelty_direction_choice",
    "benchmark_validation_route_choice",
    "resource_risk_limit_choice",
    "contradiction_adjudication_choice",
    "promotion_approval",
    "stop_continue_branch_redirect_decision",
}
_STATUSES = {"requested", "answered", "superseded", "cancelled"}


@dataclass
class OperatorCheckpointRecord:
    checkpoint_id: str
    topic_id: str
    checkpoint_kind: str
    question: str
    options: list[str] = field(default_factory=list)
    requested_by: str = ""
    claim_id: str = ""
    human_checkpoint_id: str = ""
    source_refs: list[str] = field(default_factory=list)
    status: str = "requested"
    selected_option: str = ""
    rationale: str = ""
    answered_by: str = ""
    summary_inputs_trusted: bool = False
    can_update_claim_trust: bool = False
    kind: str = "operator_checkpoint"


def request_operator_checkpoint(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    checkpoint_kind: str,
    question: str,
    options: list[str] | None = None,
    requested_by: str,
    claim_id: str = "",
    human_checkpoint_id: str = "",
    source_refs: list[str] | None = None,
) -> OperatorCheckpointRecord:
    """Write the current durable operator question for a topic."""

    _validate_kind(checkpoint_kind)
    if not options:
        raise ValueError("operator checkpoint options must not be empty")
    record = OperatorCheckpointRecord(
        checkpoint_id=prefixed_id("operator-checkpoint", f"{topic_id}:{checkpoint_kind}:{question}", max_slug=72),
        topic_id=topic_id,
        checkpoint_kind=checkpoint_kind,
        question=question,
        options=options or [],
        requested_by=requested_by,
        claim_id=claim_id,
        human_checkpoint_id=human_checkpoint_id,
        source_refs=source_refs or [],
    )
    _write_active(ws, record)
    _append_ledger(ws, record)
    return record


def answer_operator_checkpoint(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    checkpoint_id: str,
    selected_option: str = "",
    rationale: str,
    answered_by: str,
    status: str = "answered",
) -> OperatorCheckpointRecord:
    """Answer, cancel, or supersede the current operator checkpoint."""

    if status not in {"answered", "superseded", "cancelled"}:
        raise ValueError("operator checkpoint answer status must be answered, superseded, or cancelled")
    record = _load_active_record(ws, topic_id)
    if record.checkpoint_id != checkpoint_id:
        raise ValueError(f"active checkpoint is {record.checkpoint_id}, not {checkpoint_id}")
    if status == "answered":
        if selected_option not in record.options:
            raise ValueError(f"selected_option {selected_option!r} must be one of {record.options}")
    record.status = status
    record.selected_option = selected_option
    record.rationale = rationale
    record.answered_by = answered_by
    _write_active(ws, record)
    _append_ledger(ws, record)
    return record


def load_operator_checkpoint(ws: WorkspacePaths, topic_id: str) -> dict[str, Any]:
    """Return brief-facing operator checkpoint state for the current topic."""

    path = _runtime_dir(ws, topic_id) / "operator_checkpoint.active.json"
    if not path.exists():
        return {"present": False, "active": False, "summary_inputs_trusted": False, "can_update_claim_trust": False}
    data = json.loads(path.read_text(encoding="utf-8"))
    status = str(data.get("status") or "")
    active = status == "requested"
    return {
        "present": True,
        "active": active,
        "checkpoint_id": str(data.get("checkpoint_id") or ""),
        "topic_id": topic_id,
        "claim_id": str(data.get("claim_id") or ""),
        "human_checkpoint_id": str(data.get("human_checkpoint_id") or ""),
        "checkpoint_kind": str(data.get("checkpoint_kind") or ""),
        "question": str(data.get("question") or ""),
        "options": list(data.get("options") or []),
        "requested_by": str(data.get("requested_by") or ""),
        "status": status,
        "selected_option": str(data.get("selected_option") or ""),
        "rationale": str(data.get("rationale") or ""),
        "answered_by": str(data.get("answered_by") or ""),
        "required_next_action": "answer_operator_checkpoint" if active else "",
        "artifact_paths": {
            "markdown": str(_runtime_dir(ws, topic_id) / "operator_checkpoint.active.md"),
            "json": str(path),
            "ledger": str(_runtime_dir(ws, topic_id) / "operator_checkpoints.jsonl"),
        },
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _load_active_record(ws: WorkspacePaths, topic_id: str) -> OperatorCheckpointRecord:
    path = _runtime_dir(ws, topic_id) / "operator_checkpoint.active.json"
    if not path.exists():
        raise ValueError(f"no active operator checkpoint for topic {topic_id}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return OperatorCheckpointRecord(
        checkpoint_id=str(data.get("checkpoint_id") or ""),
        topic_id=str(data.get("topic_id") or topic_id),
        checkpoint_kind=str(data.get("checkpoint_kind") or ""),
        question=str(data.get("question") or ""),
        options=list(data.get("options") or []),
        requested_by=str(data.get("requested_by") or ""),
        claim_id=str(data.get("claim_id") or ""),
        human_checkpoint_id=str(data.get("human_checkpoint_id") or ""),
        source_refs=list(data.get("source_refs") or []),
        status=str(data.get("status") or ""),
        selected_option=str(data.get("selected_option") or ""),
        rationale=str(data.get("rationale") or ""),
        answered_by=str(data.get("answered_by") or ""),
    )


def _validate_kind(checkpoint_kind: str) -> None:
    if checkpoint_kind not in _CHECKPOINT_KINDS:
        raise ValueError(f"operator checkpoint kind must be one of {sorted(_CHECKPOINT_KINDS)}")


def _write_active(ws: WorkspacePaths, record: OperatorCheckpointRecord) -> None:
    runtime_dir = _runtime_dir(ws, record.topic_id)
    payload = asdict(record)
    _write_json(runtime_dir / "operator_checkpoint.active.json", payload)
    write_md(runtime_dir / "operator_checkpoint.active.md", payload, _body(record))


def _append_ledger(ws: WorkspacePaths, record: OperatorCheckpointRecord) -> None:
    path = _runtime_dir(ws, record.topic_id) / "operator_checkpoints.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), ensure_ascii=False, sort_keys=True) + "\n")


def _runtime_dir(ws: WorkspacePaths, topic_id: str) -> Path:
    runtime_dir = ws.topic_dir(topic_id) / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    return runtime_dir


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _body(record: OperatorCheckpointRecord) -> str:
    options = "\n".join(f"- {option}" for option in record.options)
    return (
        "# Operator Checkpoint\n\n"
        f"Question: {record.question}\n\n"
        f"Kind: {record.checkpoint_kind}\n\n"
        f"Status: {record.status}\n\n"
        f"Options:\n{options}\n\n"
        f"Selected option: {record.selected_option}\n\n"
        f"Rationale: {record.rationale}\n"
    )
