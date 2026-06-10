"""MCP wrappers for canonical research-run process records."""

from __future__ import annotations

from pathlib import Path

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.research_runs import (
    record_research_run_event,
    research_run_event_payload,
    research_run_payload,
    start_research_run,
    update_research_run,
)
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(Path(base))


def aitp_v5_start_research_run(
    base: str,
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
    metadata: dict | None = None,
) -> dict:
    record = start_research_run(
        _ws(base),
        topic_id=topic_id,
        objective=objective,
        research_question=research_question,
        operator=operator,
        title=title,
        claim_id=claim_id,
        session_id=session_id,
        hypothesis=hypothesis,
        phase=phase,
        metadata=metadata,
    )
    return require_valid_public_surface("research_run_record", research_run_payload(record))


def aitp_v5_update_research_run(
    base: str,
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
    payload: dict | None = None,
) -> dict:
    record = update_research_run(
        _ws(base),
        run_id=run_id,
        topic_id=topic_id,
        operator=operator,
        status=status,
        phase=phase,
        terminal_answer_state=terminal_answer_state,
        stop_reason=stop_reason,
        aitp_slice_refs=aitp_slice_refs,
        action_refs=action_refs,
        evidence_refs=evidence_refs,
        validation_refs=validation_refs,
        source_refs=source_refs,
        answer_packet_ref=answer_packet_ref,
        event_type=event_type,
        event_summary=event_summary,
        payload=payload,
    )
    return require_valid_public_surface("research_run_record", research_run_payload(record))


def aitp_v5_record_research_run_event(
    base: str,
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
    payload: dict | None = None,
) -> dict:
    record = record_research_run_event(
        _ws(base),
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
        source_refs=source_refs,
        evidence_refs=evidence_refs,
        validation_refs=validation_refs,
        artifact_refs=artifact_refs,
        payload=payload,
    )
    return require_valid_public_surface("research_run_event_record", research_run_event_payload(record))
