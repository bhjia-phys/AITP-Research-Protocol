"""Read-only discovery of review candidates for optional M1 sidecars."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordReadReport, RecordRepository


def audit_lifecycle_migration_candidates(ws: WorkspacePaths) -> dict[str, Any]:
    """Inventory existing scope state without creating programs or focus sets.

    Shared contexts and session anchors are routing evidence only. The result is
    deliberately not a canonical-record payload because scientific boundaries,
    primary/supporting roles, and cross-topic applicability require human review.
    """

    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="migration",
            actor_id="lifecycle-migration-audit",
            host="aitp-v5",
        ),
    )
    reports = {
        family: repository.list(family)
        for family in (
            "topics",
            "sessions",
            "session_focus_sets",
            "research_programs",
        )
    }
    topics = _records_by_id(reports["topics"], "topic_id")
    sessions = _records_by_id(reports["sessions"], "session_id")
    focuses = tuple(_payload(record) for record in reports["session_focus_sets"].records)
    programs = tuple(_payload(record) for record in reports["research_programs"].records)
    read_errors = _read_errors(reports)

    active_focus_sessions = {
        str(focus.get("session_id") or "")
        for focus in focuses
        if focus.get("scope_status") == "active"
    }
    sessions_without_focus = sorted(set(sessions) - active_focus_sessions)
    focus_candidates, focus_blockers = _focus_candidates(
        repository,
        sessions,
        sessions_without_focus,
    )
    program_candidates = _program_candidates(topics, sessions, programs)

    return {
        "kind": "lifecycle_migration_candidate_audit",
        "inventory": {
            "topic_count": len(topics),
            "session_count": len(sessions),
            "focus_set_count": len(focuses),
            "program_count": len(programs),
        },
        "read_errors": read_errors,
        "existing_sessions_without_focus": sessions_without_focus,
        "focus_candidates": focus_candidates,
        "focus_candidate_blockers": focus_blockers,
        "program_candidates": program_candidates,
        "candidate_semantics": "routing_hints_only",
        "existing_sessions_remain_valid_without_focus_sidecars": True,
        "write_executed": False,
        "human_review_required": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "claim_trust_transfer": "forbidden",
        "truth_source": "typed_canonical_records",
    }


def _records_by_id(report: RecordReadReport, id_field: str) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for record in report.records:
        payload = _payload(record)
        record_id = str(payload.get(id_field) or "").strip()
        if record_id:
            records[record_id] = payload
    return dict(sorted(records.items()))


def _payload(record: Any) -> dict[str, Any]:
    if is_dataclass(record):
        return asdict(record)
    if isinstance(record, Mapping):
        return dict(record)
    return {}


def _read_errors(reports: Mapping[str, RecordReadReport]) -> list[dict[str, str]]:
    return [
        {
            "family": family,
            "path": issue.path,
            "error_type": issue.error_type,
            "message": issue.message,
        }
        for family, report in reports.items()
        for issue in report.malformed
    ]


def _focus_candidates(
    repository: RecordRepository,
    sessions: Mapping[str, Mapping[str, Any]],
    session_ids: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    candidates: list[dict[str, Any]] = []
    blockers: list[dict[str, str]] = []
    for session_id in session_ids:
        session = sessions[session_id]
        topic_id = str(session.get("topic_id") or "").strip()
        anchor = _session_anchor(session)
        if not topic_id or anchor is None:
            blockers.append(
                {
                    "session_id": session_id,
                    "reason": "no_readable_session_topic_or_durable_focus_anchor",
                }
            )
            continue
        focus_kind, focus_ref, basis = anchor
        result = repository.read(focus_ref)
        payload = _payload(result.record)
        if result.status != "found" or payload.get("topic_id") != topic_id:
            blockers.append(
                {
                    "session_id": session_id,
                    "reason": "session_focus_anchor_is_missing_unreadable_or_cross_topic",
                }
            )
            continue
        candidates.append(
            {
                "session_id": session_id,
                "primary_topic_id": topic_id,
                "focus_kind": focus_kind,
                "focus_ref": focus_ref,
                "basis": basis,
                "human_review_required": True,
                "canonical_payload_ready": False,
            }
        )
    return candidates, blockers


def _session_anchor(session: Mapping[str, Any]) -> tuple[str, str, str] | None:
    claim_id = str(session.get("active_claim") or "").strip()
    if claim_id:
        return "claim", f"claim:{claim_id}", "existing_session_active_claim"
    route_id = str(session.get("active_route") or "").strip()
    if route_id:
        return "route", f"research_route:{route_id}", "existing_session_active_route"
    return None


def _program_candidates(
    topics: Mapping[str, Mapping[str, Any]],
    sessions: Mapping[str, Mapping[str, Any]],
    programs: tuple[dict[str, Any], ...],
) -> list[dict[str, Any]]:
    by_context: dict[str, list[str]] = {}
    for topic_id, topic in topics.items():
        context_id = str(topic.get("context_id") or "").strip()
        if context_id:
            by_context.setdefault(context_id, []).append(topic_id)

    existing_topic_sets = {
        frozenset(
            str(topic_id)
            for topic_id in (
                list(program.get("primary_topic_ids") or ())
                + list(program.get("supporting_topic_ids") or ())
            )
            if str(topic_id)
        )
        for program in programs
    }
    candidates: list[dict[str, Any]] = []
    for context_id, raw_topic_ids in sorted(by_context.items()):
        topic_ids = sorted(set(raw_topic_ids))
        if len(topic_ids) < 2 or frozenset(topic_ids) in existing_topic_sets:
            continue
        session_ids = sorted(
            session_id
            for session_id, session in sessions.items()
            if str(session.get("context_id") or "") == context_id
        )
        candidates.append(
            {
                "context_id": context_id,
                "topic_ids": topic_ids,
                "session_ids": session_ids,
                "basis": "shared_context_routing_hint_only",
                "scientific_boundary_inferred": False,
                "human_review_required": True,
                "canonical_payload_ready": False,
            }
        )
    return candidates
