"""Canonical research-run process records for host runtimes."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.markdown import write_md
from brain.v5.models import ResearchRunEventRecord, ResearchRunRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_valid_records, read_record, write_record

RUN_STATUSES = {"active", "paused", "stopped", "complete", "blocked"}
RUN_PHASES = {
    "planning",
    "context_refresh",
    "action_selection",
    "source_review",
    "validation",
    "answer_drafting",
    "awaiting_approval",
    "blocked",
    "complete",
}
TERMINAL_ANSWER_STATES = {
    "",
    "answered_with_validated_support",
    "answered_with_conditional_support",
    "blocked_needs_human",
    "negative_or_inconclusive",
    "draft_only",
}
EVENT_TYPES = {
    "run_started",
    "context_refreshed",
    "action_selected",
    "action_started",
    "action_completed",
    "operator_checkpoint",
    "status_changed",
    "answer_drafted",
    "answer_finalized",
    "blocked",
    "run_stopped",
}
EVENT_STATUSES = {"recorded", "blocked", "failed", "superseded"}


def start_research_run(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    objective: str,
    research_question: str,
    operator: str,
    title: str = "",
    claim_id: str = "",
    session_id: str = "",
    hypothesis: str = "",
    phase: str = "planning",
    metadata: dict[str, Any] | None = None,
) -> ResearchRunRecord:
    """Create the canonical top-level research-run ledger record."""

    _require_nonempty(topic_id, "topic_id")
    _require_nonempty(objective, "objective")
    _require_nonempty(research_question, "research_question")
    _require_nonempty(operator, "operator")
    _validate_phase(phase)
    now = _now()
    run_id = prefixed_id(
        "research-run",
        f"{topic_id}:{claim_id}:{session_id}:{objective}:{research_question}:{now}",
        max_slug=80,
    )
    record = ResearchRunRecord(
        run_id=run_id,
        topic_id=topic_id,
        title=title,
        objective=objective,
        research_question=research_question,
        hypothesis=hypothesis,
        operator=operator,
        status="active",
        phase=phase,
        claim_id=claim_id,
        session_id=session_id,
        operator_trail=[_operator_trail_item(operator, "run_started", now)],
        metadata={**(metadata or {}), "created_at": now, "updated_at": now},
    )
    _write_run(ws, record)
    event = record_research_run_event(
        ws,
        run_id=run_id,
        topic_id=topic_id,
        operator=operator,
        event_type="run_started",
        summary=f"Research run started: {objective}",
        phase=phase,
        claim_id=claim_id,
        session_id=session_id,
        payload={
            "objective": objective,
            "research_question": research_question,
            "hypothesis": hypothesis,
            "title": title,
        },
    )
    record.event_ids = [event.event_id]
    _write_run(ws, record)
    return record


def update_research_run(
    ws: WorkspacePaths,
    *,
    run_id: str,
    topic_id: str,
    operator: str,
    status: str | None = None,
    phase: str | None = None,
    terminal_answer_state: str | None = None,
    stop_reason: str = "",
    aitp_slice_refs: list[str] | None = None,
    action_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    validation_refs: list[str] | None = None,
    source_refs: list[str] | None = None,
    answer_packet_ref: str | None = None,
    event_type: str = "status_changed",
    event_summary: str = "",
    payload: dict[str, Any] | None = None,
) -> ResearchRunRecord:
    """Update a canonical research run and append a process event."""

    _require_nonempty(operator, "operator")
    record = read_record(_run_record_path(ws, run_id), ResearchRunRecord)
    if record.topic_id != topic_id:
        raise ValueError(f"research run {run_id} belongs to topic {record.topic_id}, not {topic_id}")
    if status is not None:
        _validate_status(status)
        record.status = status
    if phase is not None:
        _validate_phase(phase)
        record.phase = phase
    if terminal_answer_state is not None:
        _validate_terminal_answer_state(terminal_answer_state)
        record.terminal_answer_state = terminal_answer_state
    if stop_reason:
        record.stop_reason = stop_reason
    if aitp_slice_refs is not None:
        record.aitp_slice_refs = aitp_slice_refs
    if action_refs is not None:
        record.action_refs = action_refs
    if evidence_refs is not None:
        record.evidence_refs = evidence_refs
    if validation_refs is not None:
        record.validation_refs = validation_refs
    if source_refs is not None:
        record.source_refs = source_refs
    if answer_packet_ref is not None:
        record.answer_packet_ref = answer_packet_ref
    now = _now()
    metadata = dict(record.metadata)
    metadata["updated_at"] = now
    record.metadata = metadata
    record.operator_trail = [*record.operator_trail, _operator_trail_item(operator, event_type, now)]
    event = record_research_run_event(
        ws,
        run_id=run_id,
        topic_id=topic_id,
        operator=operator,
        event_type=event_type,
        summary=event_summary or _default_update_summary(record),
        status="recorded" if record.status != "blocked" else "blocked",
        phase=record.phase,
        claim_id=record.claim_id,
        session_id=record.session_id,
        source_refs=source_refs,
        evidence_refs=evidence_refs,
        validation_refs=validation_refs,
        payload=payload or {
            "run_status": record.status,
            "phase": record.phase,
            "terminal_answer_state": record.terminal_answer_state,
            "stop_reason": record.stop_reason,
        },
    )
    record.event_ids = [*record.event_ids, event.event_id]
    _write_run(ws, record)
    return record


def record_research_run_event(
    ws: WorkspacePaths,
    *,
    run_id: str,
    topic_id: str,
    operator: str,
    event_type: str,
    summary: str,
    status: str = "recorded",
    phase: str = "",
    claim_id: str = "",
    session_id: str = "",
    action_id: str = "",
    action_ref: str = "",
    source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    validation_refs: list[str] | None = None,
    artifact_refs: list[str] | None = None,
    payload: dict[str, Any] | None = None,
) -> ResearchRunEventRecord:
    """Append one operator/action/status event to the canonical run timeline."""

    _require_nonempty(run_id, "run_id")
    _require_nonempty(topic_id, "topic_id")
    _require_nonempty(operator, "operator")
    _require_nonempty(summary, "summary")
    _validate_event_type(event_type)
    _validate_event_status(status)
    if phase:
        _validate_phase(phase)
    run_record = read_record(_run_record_path(ws, run_id), ResearchRunRecord)
    if run_record.topic_id != topic_id:
        raise ValueError(f"research run {run_id} belongs to topic {run_record.topic_id}, not {topic_id}")
    event_id = prefixed_id("research-run-event", f"{run_id}:{event_type}:{operator}:{summary}:{_now()}", max_slug=96)
    record = ResearchRunEventRecord(
        event_id=event_id,
        run_id=run_id,
        topic_id=topic_id,
        operator=operator,
        event_type=event_type,
        summary=summary,
        status=status,
        phase=phase,
        claim_id=claim_id,
        session_id=session_id,
        action_id=action_id,
        action_ref=action_ref,
        source_refs=source_refs or [],
        evidence_refs=evidence_refs or [],
        validation_refs=validation_refs or [],
        artifact_refs=artifact_refs or [],
        payload=payload or {},
    )
    write_record(_event_record_path(ws, event_id), record, body=_event_body(record))
    _append_topic_timeline(ws, record)
    return record


def research_run_payload(record: ResearchRunRecord) -> dict[str, Any]:
    return {"ok": True, **asdict(record)}


def research_run_event_payload(record: ResearchRunEventRecord) -> dict[str, Any]:
    return {"ok": True, **asdict(record)}


def list_research_runs_for_topic(ws: WorkspacePaths, topic_id: str) -> list[ResearchRunRecord]:
    return [
        record
        for record in list_valid_records(ws.registry_dir("research_runs"), ResearchRunRecord)
        if record.topic_id == topic_id
    ]


def list_research_run_events_for_topic(ws: WorkspacePaths, topic_id: str) -> list[ResearchRunEventRecord]:
    return [
        record
        for record in list_valid_records(ws.registry_dir("research_run_events"), ResearchRunEventRecord)
        if record.topic_id == topic_id
    ]


def _write_run(ws: WorkspacePaths, record: ResearchRunRecord) -> None:
    write_record(_run_record_path(ws, record.run_id), record, body=_run_body(record))
    runtime_dir = _runtime_dir(ws, record.topic_id)
    write_md(runtime_dir / f"{record.run_id}.md", asdict(record), _run_body(record))
    (runtime_dir / f"{record.run_id}.json").write_text(
        json.dumps(asdict(record), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _append_topic_timeline(ws: WorkspacePaths, record: ResearchRunEventRecord) -> None:
    runtime_dir = _runtime_dir(ws, record.topic_id)
    with (runtime_dir / "research_run_events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), ensure_ascii=False, sort_keys=True) + "\n")


def _run_record_path(ws: WorkspacePaths, run_id: str) -> Path:
    return ws.registry_dir("research_runs") / f"{run_id}.md"


def _event_record_path(ws: WorkspacePaths, event_id: str) -> Path:
    return ws.registry_dir("research_run_events") / f"{event_id}.md"


def _runtime_dir(ws: WorkspacePaths, topic_id: str) -> Path:
    runtime_dir = ws.topic_dir(topic_id) / "runtime" / "research_runs"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    return runtime_dir


def _operator_trail_item(operator: str, event_type: str, timestamp: str) -> dict[str, str]:
    return {"operator": operator, "event_type": event_type, "timestamp": timestamp}


def _run_body(record: ResearchRunRecord) -> str:
    actions = "\n".join(f"- {item}" for item in record.action_refs) or "- None"
    sources = "\n".join(f"- {item}" for item in record.source_refs) or "- None"
    events = "\n".join(f"- {item}" for item in record.event_ids) or "- None"
    return (
        f"# Research Run: {record.title or record.objective}\n\n"
        f"Objective: {record.objective}\n\n"
        f"Research question: {record.research_question}\n\n"
        f"Status: `{record.status}` / phase `{record.phase}`\n\n"
        f"Operator: `{record.operator}`\n\n"
        f"Terminal answer state: `{record.terminal_answer_state or 'none'}`\n\n"
        f"Action refs:\n{actions}\n\n"
        f"Source refs:\n{sources}\n\n"
        f"Event ids:\n{events}\n\n"
        "This is a canonical process ledger record. It does not validate evidence or update claim trust.\n"
    )


def _event_body(record: ResearchRunEventRecord) -> str:
    return (
        f"# Research Run Event: {record.event_type}\n\n"
        f"Run: `{record.run_id}`\n\n"
        f"Operator: `{record.operator}`\n\n"
        f"Status: `{record.status}`\n\n"
        f"Summary: {record.summary}\n\n"
        "This event records process provenance only. It is not evidence, validation, or trust promotion.\n"
    )


def _default_update_summary(record: ResearchRunRecord) -> str:
    return f"Research run status={record.status}, phase={record.phase}"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _require_nonempty(value: str, name: str) -> None:
    if not str(value or "").strip():
        raise ValueError(f"{name} is required")


def _validate_status(status: str) -> None:
    if status not in RUN_STATUSES:
        raise ValueError(f"status must be one of {sorted(RUN_STATUSES)}")


def _validate_phase(phase: str) -> None:
    if phase not in RUN_PHASES:
        raise ValueError(f"phase must be one of {sorted(RUN_PHASES)}")


def _validate_terminal_answer_state(state: str) -> None:
    if state not in TERMINAL_ANSWER_STATES:
        raise ValueError(f"terminal_answer_state must be one of {sorted(TERMINAL_ANSWER_STATES)}")


def _validate_event_type(event_type: str) -> None:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"event_type must be one of {sorted(EVENT_TYPES)}")


def _validate_event_status(status: str) -> None:
    if status not in EVENT_STATUSES:
        raise ValueError(f"event status must be one of {sorted(EVENT_STATUSES)}")
