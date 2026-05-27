"""Workspace-level replay packet for resuming long-running AITP work."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from brain.v5.evidence import required_output_coverage
from brain.v5.flow import resolve_flow_profile
from brain.v5.markdown import write_md
from brain.v5.memory_index import MemoryEntrySummary, scan_memory_entry_summaries
from brain.v5.models import ClaimRecord, CodeStateRecord, EvidenceRecord, SessionBinding, SourceReconstructionReviewResultRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.risk import action_budget_for_level, assess_claim_risk
from brain.v5.replay_backlog_summary import build_workspace_backlog_summary, workspace_replay_body
from brain.v5.source_reconstruction import audit_source_reconstruction_batch
from brain.v5.store import list_records


@dataclass
class WorkspaceReplayPacket:
    replay_dir: str
    files: dict[str, str]
    entry_count: int
    attention_count: int
    workspace_backlog_summary: dict[str, Any] = field(default_factory=dict)
    entries: list[dict[str, Any]] = field(default_factory=list)
    source_records: dict[str, list[str]] = field(default_factory=dict)
    kind: str = "workspace_replay_packet"
    derived_from: str = "kernel_state"
    truth_source: bool = False
    orientation_only: bool = True
    adapter_rule: str = "read_for_orientation_then_call_kernel_before_trust_updates"
    can_update_kernel_state: bool = False
    can_update_claim_trust: bool = False


def write_workspace_replay_packet(
    ws: WorkspacePaths,
    *,
    migration_dir: str | None = None,
) -> WorkspaceReplayPacket:
    """Write an orientation-only packet for resuming active sessions."""

    replay_dir = ws.root / "surfaces" / "workspace_replay"
    replay_path = replay_dir / "replay_packet.md"
    sessions = list_records(ws.root / "runtime" / "sessions", SessionBinding)
    claims = {claim.claim_id: claim for claim in list_records(ws.registry_dir("claims"), ClaimRecord)}
    evidence = _group_by_claim(list_records(ws.registry_dir("evidence"), EvidenceRecord))
    code_states = list_records(ws.registry_dir("code_states"), CodeStateRecord)
    source_reviews = _group_source_reviews_by_claim(
        list_records(ws.registry_dir("source_reconstruction_reviews"), SourceReconstructionReviewResultRecord),
        review_dir=ws.registry_dir("source_reconstruction_reviews"),
    )
    active_claim_ids = [session.active_claim for session in sessions if session.active_claim]
    memory_entries = scan_memory_entry_summaries(ws, claim_ids=active_claim_ids, active_only=True)
    source_audits = audit_source_reconstruction_batch(ws, active_claim_ids)
    entries = [
        _entry_for_session(session, claims, memory_entries, evidence, code_states, source_audits, source_reviews)
        for session in sessions
    ]
    attention = [entry for entry in entries if entry["attention_reasons"]]
    workspace_backlog_summary = build_workspace_backlog_summary(ws, entries, migration_dir=migration_dir)
    source_records = {
        "sessions": [entry["session_id"] for entry in entries],
        "topics": _unique([entry["topic_id"] for entry in entries if entry["topic_id"]]),
        "claims": [entry["claim_id"] for entry in entries if entry["claim_id"]],
        "memory_entries": _unique([mid for entry in entries for mid in entry["memory_entry_ids"]]),
        "validation_results": _unique([vid for entry in entries for vid in entry["validation_result_ids"]]),
        "source_reconstruction_reviews": _unique([
            rid for entry in entries for rid in entry["source_reconstruction_review_result_ids"]
        ]),
    }
    write_md(
        replay_path,
        _frontmatter(source_records, workspace_backlog_summary),
        workspace_replay_body(entries, workspace_backlog_summary),
    )
    return WorkspaceReplayPacket(
        replay_dir=str(replay_dir),
        files={"replay_packet": str(replay_path)},
        entry_count=len(entries),
        attention_count=len(attention),
        workspace_backlog_summary=workspace_backlog_summary,
        entries=entries,
        source_records=source_records,
    )


def _entry_for_session(
    session: SessionBinding,
    claims: dict[str, ClaimRecord],
    memory_entries: list[MemoryEntrySummary],
    evidence_by_claim: dict[str, list[EvidenceRecord]],
    code_states: list[CodeStateRecord],
    source_audits: dict[str, dict],
    source_reviews_by_claim: dict[str, list[SourceReconstructionReviewResultRecord]],
) -> dict[str, Any]:
    claim = claims.get(session.active_claim)
    if claim is None:
        return {
            "session_id": session.session_id,
            "topic_id": session.topic_id,
            "claim_id": session.active_claim,
            "claim_statement": "",
            "confidence_state": "",
            "risk_level": "",
            "missing_outputs": [],
            "satisfied_outputs": [],
            "next_actions": [],
            "source_reconstruction_complete": False,
            "source_reconstruction_review_status": "missing_claim_record",
            "source_reconstruction_review_result_ids": [],
            "missing_source_components": ["claim_record"],
            "memory_entry_ids": [],
            "validation_result_ids": [],
            "attention_reasons": ["missing_claim_record"],
        }
    risk = assess_claim_risk(claim, code_states=_linked_code_states(code_states, claim.claim_id))
    flow = resolve_flow_profile(claim, assessment=risk)
    action_budget = risk.action_budget if risk and risk.action_budget else action_budget_for_level("guided")
    evidence_coverage = required_output_coverage(
        evidence_by_claim.get(claim.claim_id, []),
        required_outputs=action_budget.required_outputs,
    )
    source_audit = source_audits[claim.claim_id]
    source_reviews = source_reviews_by_claim.get(claim.claim_id, [])
    latest_source_review = source_reviews[-1] if source_reviews else None
    source_review_status = latest_source_review.status if latest_source_review else "pending"
    claim_memory = [entry for entry in memory_entries if entry.source_claim_id == claim.claim_id]
    missing_outputs = evidence_coverage.missing_outputs
    missing_source = source_audit["missing_components"]
    reasons = []
    if claim.confidence_state == "hypothesis":
        reasons.append("claim_still_hypothesis")
    if missing_outputs:
        reasons.append("missing_evidence_outputs")
    if missing_source:
        reasons.append("missing_source_reconstruction")
    if source_review_status != "passed":
        reasons.append("source_reconstruction_review_pending")
    return {
        "session_id": session.session_id,
        "topic_id": session.topic_id,
        "claim_id": claim.claim_id,
        "claim_statement": claim.statement,
        "confidence_state": claim.confidence_state,
        "risk_level": risk.level,
        "missing_outputs": list(missing_outputs),
        "satisfied_outputs": list(evidence_coverage.satisfied_outputs),
        "next_actions": _next_actions(flow.profile, missing_outputs, missing_source, source_review_status),
        "source_reconstruction_complete": source_audit["complete"],
        "source_reconstruction_review_status": source_review_status,
        "source_reconstruction_review_result_ids": [review.result_id for review in source_reviews],
        "missing_source_components": list(missing_source),
        "memory_entry_ids": [entry.entry_id for entry in claim_memory],
        "validation_result_ids": _unique([vid for entry in claim_memory for vid in entry.validation_result_ids]),
        "attention_reasons": reasons,
    }


def _frontmatter(source_records: dict[str, list[str]], workspace_backlog_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "derived_workspace_replay",
        "derived_from": "kernel_state",
        "truth_source": False,
        "orientation_only": True,
        "adapter_rule": "read_for_orientation_then_call_kernel_before_trust_updates",
        "source_records": source_records,
        "workspace_backlog_summary": workspace_backlog_summary,
    }


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _group_by_claim(records: list[EvidenceRecord]) -> dict[str, list[EvidenceRecord]]:
    grouped: dict[str, list[EvidenceRecord]] = {}
    for record in records:
        grouped.setdefault(record.claim_id, []).append(record)
    return grouped


def _group_source_reviews_by_claim(
    records: list[SourceReconstructionReviewResultRecord],
    *,
    review_dir: Path,
) -> dict[str, list[SourceReconstructionReviewResultRecord]]:
    grouped: dict[str, list[SourceReconstructionReviewResultRecord]] = {}
    for record in records:
        grouped.setdefault(record.claim_id, []).append(record)
    for reviews in grouped.values():
        reviews.sort(key=lambda review: _source_review_sort_key(review, review_dir))
    return grouped


def _source_review_sort_key(
    review: SourceReconstructionReviewResultRecord,
    review_dir: Path,
) -> tuple[str, str]:
    return (review.created_at or _source_review_file_mtime(review, review_dir), review.result_id)


def _source_review_file_mtime(
    review: SourceReconstructionReviewResultRecord,
    review_dir: Path,
) -> str:
    path = review_dir / f"{review.result_id}.md"
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _linked_code_states(code_states: list[CodeStateRecord], claim_id: str) -> list[CodeStateRecord]:
    return [state for state in code_states if _record_links_to_claim(state.linked_records, claim_id)]


def _record_links_to_claim(linked_records: dict, claim_id: str) -> bool:
    for value in linked_records.values():
        if value == claim_id:
            return True
        if isinstance(value, list) and claim_id in value:
            return True
    return False


def _next_actions(
    profile: str,
    missing_outputs: list[str],
    missing_source: list[str],
    source_review_status: str = "pending",
) -> list[str]:
    actions: list[str] = []
    if missing_outputs:
        actions.append("collect_required_evidence_or_provenance")
    if missing_source:
        actions.append("complete_source_reconstruction")
    if source_review_status != "passed":
        actions.append("record_source_reconstruction_review_result")
    if profile == "adversarial":
        actions.append("design_falsification_or_counterargument")
    elif profile == "rigorous":
        actions.append("run_or_record_minimal_validation")
    elif not actions:
        actions.append("refresh_execution_brief_before_acting")
    return _unique(actions)
