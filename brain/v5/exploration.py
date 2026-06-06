"""Exploratory theory-process records for AITP v5."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.models import ExploratoryRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import write_record


EXPLORATION_TYPES = {
    "source_asset",
    "question_decomposition",
    "relation_path_brainstorm",
    "backtrace_step",
    "steering_checkpoint",
}

EXPLORATION_STATUSES = {"open", "active", "resolved", "deferred", "superseded"}


def record_exploratory_record(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str = "",
    session_id: str = "",
    exploration_type: str,
    title: str,
    focal_question: str,
    summary: str,
    original_question: str = "",
    local_question: str = "",
    status: str = "open",
    object_ids: list[str] | None = None,
    relation_ids: list[str] | None = None,
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    parent_record_ids: list[str] | None = None,
    derived_record_ids: list[str] | None = None,
    reasoning_moves: list[str] | None = None,
    backtrace_targets: list[str] | None = None,
    candidate_paths: list[str] | None = None,
    relation_path_questions: list[str] | None = None,
    definition_boundary_questions: list[str] | None = None,
    derivation_backtrace_questions: list[str] | None = None,
    source_dependency_questions: list[str] | None = None,
    original_question_guard: list[str] | None = None,
    unresolved_points: list[str] | None = None,
    next_actions: list[str] | None = None,
    human_steering: str = "",
    metadata: dict[str, Any] | None = None,
) -> ExploratoryRecord:
    """Record an orientation-only exploratory step in the typed process graph."""

    if exploration_type not in EXPLORATION_TYPES:
        allowed = ", ".join(sorted(EXPLORATION_TYPES))
        raise ValueError(f"exploration_type must be one of: {allowed}")
    if status not in EXPLORATION_STATUSES:
        allowed = ", ".join(sorted(EXPLORATION_STATUSES))
        raise ValueError(f"status must be one of: {allowed}")
    record_id = prefixed_id(
        "exploratory",
        f"{topic_id}:{claim_id}:{session_id}:{exploration_type}:{title}:{focal_question}",
        max_slug=72,
    )
    record = ExploratoryRecord(
        record_id=record_id,
        topic_id=topic_id,
        claim_id=claim_id,
        session_id=session_id,
        exploration_type=exploration_type,
        title=title,
        focal_question=focal_question,
        summary=summary,
        original_question=original_question,
        local_question=local_question,
        status=status,
        object_ids=object_ids or [],
        relation_ids=relation_ids or [],
        source_refs=source_refs or [],
        artifact_ids=artifact_ids or [],
        parent_record_ids=parent_record_ids or [],
        derived_record_ids=derived_record_ids or [],
        reasoning_moves=reasoning_moves or [],
        backtrace_targets=backtrace_targets or [],
        candidate_paths=candidate_paths or [],
        relation_path_questions=relation_path_questions or [],
        definition_boundary_questions=definition_boundary_questions or [],
        derivation_backtrace_questions=derivation_backtrace_questions or [],
        source_dependency_questions=source_dependency_questions or [],
        original_question_guard=original_question_guard or [],
        unresolved_points=unresolved_points or [],
        next_actions=next_actions or [],
        human_steering=human_steering,
        metadata=metadata or {},
    )
    write_record(
        ws.registry_dir("exploratory_records") / f"{record_id}.md",
        record,
        body=_body(record),
    )
    return record


def exploratory_record_payload(record: ExploratoryRecord) -> dict[str, Any]:
    return {"ok": True, **asdict(record)}


def _body(record: ExploratoryRecord) -> str:
    moves = "\n".join(f"- {item}" for item in record.reasoning_moves) or "- None"
    backtrace_targets = "\n".join(f"- {item}" for item in record.backtrace_targets) or "- None"
    candidates = "\n".join(f"- {item}" for item in record.candidate_paths) or "- None"
    relation_questions = "\n".join(f"- {item}" for item in record.relation_path_questions) or "- None"
    definition_questions = "\n".join(f"- {item}" for item in record.definition_boundary_questions) or "- None"
    derivation_questions = "\n".join(f"- {item}" for item in record.derivation_backtrace_questions) or "- None"
    source_questions = "\n".join(f"- {item}" for item in record.source_dependency_questions) or "- None"
    original_guard = "\n".join(f"- {item}" for item in record.original_question_guard) or "- None"
    unresolved = "\n".join(f"- {item}" for item in record.unresolved_points) or "- None"
    next_actions = "\n".join(f"- {item}" for item in record.next_actions) or "- None"
    return (
        f"# Exploratory Record: {record.title}\n\n"
        f"Type: `{record.exploration_type}`\n\n"
        f"Focal question: {record.focal_question}\n\n"
        f"Original question: {record.original_question}\n\n"
        f"Local question: {record.local_question}\n\n"
        f"Summary: {record.summary}\n\n"
        f"Reasoning moves:\n{moves}\n\n"
        f"Backtrace targets:\n{backtrace_targets}\n\n"
        f"Candidate paths:\n{candidates}\n\n"
        f"Relation path questions:\n{relation_questions}\n\n"
        f"Definition boundary questions:\n{definition_questions}\n\n"
        f"Derivation backtrace questions:\n{derivation_questions}\n\n"
        f"Source dependency questions:\n{source_questions}\n\n"
        f"Original question guard:\n{original_guard}\n\n"
        f"Unresolved points:\n{unresolved}\n\n"
        f"Next actions:\n{next_actions}\n"
    )
