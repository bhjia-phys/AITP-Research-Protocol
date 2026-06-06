"""Research route records for nonlinear theory-process state."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.models import ResearchRouteRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import read_record, write_record


ROUTE_TYPES = {
    "derivation",
    "source_backtrace",
    "relation_path",
    "code_validation",
    "benchmark_validation",
    "literature_route",
    "steering_route",
    "other",
}

ROUTE_STATUSES = {"live", "blocked", "abandoned", "superseded", "selected"}


def record_research_route(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    title: str,
    route_type: str,
    status: str,
    rationale: str,
    claim_id: str = "",
    session_id: str = "",
    current_question: str = "",
    next_action: str = "",
    failure_modes: list[str] | None = None,
    source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    parent_route_ids: list[str] | None = None,
    checkpoint_ids: list[str] | None = None,
    exploratory_record_ids: list[str] | None = None,
    object_ids: list[str] | None = None,
    relation_ids: list[str] | None = None,
    decision_rationale: str = "",
    pivot_reason: str = "",
    metadata: dict[str, Any] | None = None,
) -> ResearchRouteRecord:
    """Record an orientation-only route, failed route, branch, or pivot."""

    _require_route_type(route_type)
    _require_route_status(status)
    if not topic_id:
        raise ValueError("topic_id is required")
    if not title:
        raise ValueError("title is required")
    if not rationale:
        raise ValueError("rationale is required")

    route_id = prefixed_id(
        "route",
        f"{topic_id}:{claim_id}:{session_id}:{route_type}:{title}",
        max_slug=72,
    )
    record = ResearchRouteRecord(
        route_id=route_id,
        topic_id=topic_id,
        claim_id=claim_id,
        session_id=session_id,
        title=title,
        route_type=route_type,
        status=status,
        rationale=rationale,
        current_question=current_question,
        next_action=next_action,
        failure_modes=failure_modes or [],
        source_refs=source_refs or [],
        evidence_refs=evidence_refs or [],
        artifact_ids=artifact_ids or [],
        parent_route_ids=parent_route_ids or [],
        checkpoint_ids=checkpoint_ids or [],
        exploratory_record_ids=exploratory_record_ids or [],
        object_ids=object_ids or [],
        relation_ids=relation_ids or [],
        decision_rationale=decision_rationale,
        pivot_reason=pivot_reason,
        metadata=metadata or {},
        orientation_only=True,
        can_update_claim_trust=False,
    )
    _write_route(ws, record)
    return record


def update_research_route_status(
    ws: WorkspacePaths,
    route_id: str,
    *,
    status: str,
    decision_rationale: str = "",
    pivot_reason: str = "",
    next_action: str = "",
    failure_modes: list[str] | None = None,
    checkpoint_ids: list[str] | None = None,
) -> ResearchRouteRecord:
    """Update route process status without changing claim trust."""

    _require_route_status(status)
    record = read_record(ws.registry_dir("routes") / f"{route_id}.md", ResearchRouteRecord)
    record.status = status
    if decision_rationale:
        record.decision_rationale = decision_rationale
    if pivot_reason:
        record.pivot_reason = pivot_reason
    if next_action:
        record.next_action = next_action
    if failure_modes is not None:
        record.failure_modes = failure_modes
    if checkpoint_ids is not None:
        record.checkpoint_ids = checkpoint_ids
    _write_route(ws, record)
    return record


def research_route_payload(record: ResearchRouteRecord) -> dict[str, Any]:
    return {"ok": True, **asdict(record)}


def _write_route(ws: WorkspacePaths, record: ResearchRouteRecord) -> None:
    body = _body(record)
    write_record(ws.registry_dir("routes") / f"{record.route_id}.md", record, body=body)
    topic_route_dir = ws.topic_dir(record.topic_id) / "routes" / "decisions"
    write_record(topic_route_dir / f"{record.route_id}.md", record, body=body)


def _body(record: ResearchRouteRecord) -> str:
    failure_modes = "\n".join(f"- {item}" for item in record.failure_modes) or "- None"
    parents = "\n".join(f"- {item}" for item in record.parent_route_ids) or "- None"
    checkpoints = "\n".join(f"- {item}" for item in record.checkpoint_ids) or "- None"
    return (
        f"# Research Route: {record.title}\n\n"
        f"Type: `{record.route_type}`\n\n"
        f"Status: `{record.status}`\n\n"
        f"Current question: {record.current_question}\n\n"
        f"Rationale: {record.rationale}\n\n"
        f"Decision rationale: {record.decision_rationale}\n\n"
        f"Pivot reason: {record.pivot_reason}\n\n"
        f"Failure modes:\n{failure_modes}\n\n"
        f"Parent routes:\n{parents}\n\n"
        f"Checkpoints:\n{checkpoints}\n\n"
        f"Next action: {record.next_action}\n\n"
        "This record is orientation-only route/process state. It is not evidence or validation.\n"
    )


def _require_route_type(route_type: str) -> None:
    if route_type not in ROUTE_TYPES:
        allowed = ", ".join(sorted(ROUTE_TYPES))
        raise ValueError(f"route_type must be one of: {allowed}")


def _require_route_status(status: str) -> None:
    if status not in ROUTE_STATUSES:
        allowed = ", ".join(sorted(ROUTE_STATUSES))
        raise ValueError(f"status must be one of: {allowed}")
