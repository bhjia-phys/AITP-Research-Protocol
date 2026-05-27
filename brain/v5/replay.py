"""Workspace-level replay packet for resuming long-running AITP work."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from brain.v5.evidence import required_output_coverage
from brain.v5.flow import resolve_flow_profile
from brain.v5.legacy_human_checkpoint_packet import build_legacy_human_checkpoint_packet
from brain.v5.legacy_semantic_review_manifest import build_legacy_semantic_review_manifest
from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
from brain.v5.legacy_source_reconstruction import build_legacy_source_reconstruction_manifest
from brain.v5.markdown import write_md
from brain.v5.memory_index import MemoryEntrySummary, scan_memory_entry_summaries
from brain.v5.models import ClaimRecord, CodeStateRecord, EvidenceRecord, SessionBinding, SourceReconstructionReviewResultRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.risk import action_budget_for_level, assess_claim_risk
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
    workspace_backlog_summary = _workspace_backlog_summary(
        entries,
        legacy_semantic_review=_legacy_semantic_review_summary(ws, migration_dir),
        legacy_source_reconstruction=_legacy_source_reconstruction_summary(ws, migration_dir),
        legacy_human_checkpoints=_legacy_human_checkpoint_summary(ws, migration_dir),
    )
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
        _body(entries, workspace_backlog_summary),
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


def _body(entries: list[dict[str, Any]], workspace_backlog_summary: dict[str, Any]) -> str:
    lines = [
        "# Workspace Replay Packet",
        "",
        "This file is regenerated from typed AITP kernel records. Use it for orientation only.",
        "",
        "## Cross-Topic Backlog",
        "",
        f"- Active sessions: {workspace_backlog_summary['active_session_count']}",
        f"- Active topics: {workspace_backlog_summary['active_topic_count']}",
        f"- Active claims: {workspace_backlog_summary['active_claim_count']}",
        f"- Attention items: {workspace_backlog_summary['attention_count']}",
        f"- Source reconstruction incomplete: {workspace_backlog_summary['source_reconstruction']['incomplete_claim_count']}",
        f"- Source review pending: {workspace_backlog_summary['source_reconstruction']['review_status_counts'].get('pending', 0)}",
        "",
    ]
    for item in workspace_backlog_summary["source_reconstruction"]["top_incomplete_claims"]:
        lines.append(
            f"- `{item['claim_id']}` in `{item['topic_id']}`: missing "
            f"{', '.join(item['missing_components']) or 'none'}; review via `{item['review_packet_cli']}`"
        )
    if workspace_backlog_summary["source_reconstruction"]["top_incomplete_claims"]:
        lines.append("")
    legacy = workspace_backlog_summary.get("legacy_semantic_review")
    if isinstance(legacy, dict):
        lines.extend([
            "## Legacy Semantic Review Backlog",
            "",
            f"- Migration dir: `{legacy['migration_dir']}`",
            f"- Review items: {legacy['review_item_count']}",
            f"- Review progress: `{legacy['review_progress']}`",
            f"- Open human checkpoints: {legacy.get('open_human_checkpoint_count', 0)}",
            f"- semantic lossless proven: {legacy['semantic_lossless_proven']}",
            "",
        ])
        for checkpoint in legacy.get("open_human_checkpoints", []):
            lines.append(
                f"- Open checkpoint `{checkpoint['checkpoint_id']}` for `{checkpoint['topic']}`: "
                f"{checkpoint['action']}; decide via `{checkpoint['decision_cli']}`"
            )
        if legacy.get("open_human_checkpoints"):
            lines.append("")
        for item in legacy["top_backlog_items"]:
            lines.append(
                f"- `{item['topic']}`: {item['review_status']} priority {item['review_priority']}; "
                f"review via `{item['packet_cli']}`"
            )
        lines.append("")
    legacy_source = workspace_backlog_summary.get("legacy_source_reconstruction")
    if isinstance(legacy_source, dict):
        lines.extend([
            "## Legacy Source Reconstruction Backlog",
            "",
            f"- Migration dir: `{legacy_source['migration_dir']}`",
            f"- Source reconstruction items: {legacy_source['work_item_count']}",
            f"- Repair status: `{legacy_source['repair_status_counts']}`",
            f"- Proposed repairs: {legacy_source['proposed_repair_count']}",
            "",
        ])
        for item in legacy_source["top_backlog_items"]:
            lines.append(
                f"- `{item['topic']}`: {item['repair_status']}; missing "
                f"{', '.join(item['missing_components']) or 'none'}; review via `{item['review_packet_cli']}`"
            )
        lines.append("")
    legacy_checkpoints = workspace_backlog_summary.get("legacy_human_checkpoints")
    if isinstance(legacy_checkpoints, dict):
        lines.extend([
            "## Legacy Human Checkpoints",
            "",
            f"- Migration dir: `{legacy_checkpoints['migration_dir']}`",
            (
                "- Checkpoint decisions: "
                f"{legacy_checkpoints['open_decision_count']} open, "
                f"{legacy_checkpoints['pending_request_count']} pending request"
            ),
            f"- Next actions: {legacy_checkpoints['next_action_count']}",
            "",
        ])
        for item in legacy_checkpoints["top_checkpoint_items"]:
            lines.append(
                f"- `{item['topic']}`: {item['action']} via `{item['cli']}`"
            )
        lines.append("")
    if not entries:
        lines.append("- No active session bindings are recorded.")
        return "\n".join(lines) + "\n"
    for entry in entries:
        lines.append(f"## `{entry['session_id']}`")
        lines.append("")
        lines.append(f"- Topic: `{entry['topic_id']}`")
        lines.append(f"- Claim: `{entry['claim_id']}`")
        lines.append(f"- Confidence: `{entry['confidence_state']}`")
        lines.append(f"- Risk: `{entry['risk_level']}`")
        lines.append(f"- Missing evidence outputs: {', '.join(entry['missing_outputs']) or 'none'}")
        lines.append(f"- Missing source components: {', '.join(entry['missing_source_components']) or 'none'}")
        lines.append(f"- Source review: `{entry['source_reconstruction_review_status']}`")
        lines.append(f"- Attention: {', '.join(entry['attention_reasons']) or 'none'}")
        lines.append(f"- Next actions: {', '.join(entry['next_actions']) or 'none'}")
        lines.append("")
    return "\n".join(lines)


def _workspace_backlog_summary(
    entries: list[dict[str, Any]],
    *,
    legacy_semantic_review: dict[str, Any] | None = None,
    legacy_source_reconstruction: dict[str, Any] | None = None,
    legacy_human_checkpoints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    complete_entries = [entry for entry in entries if entry["claim_id"] and entry["source_reconstruction_complete"]]
    incomplete_entries = [
        entry for entry in entries if entry["claim_id"] and not entry["source_reconstruction_complete"]
    ]
    attention_entries = _prioritized_attention_entries([entry for entry in entries if entry["attention_reasons"]])
    summary = {
        "active_session_count": len(entries),
        "active_topic_count": len(_unique([entry["topic_id"] for entry in entries if entry["topic_id"]])),
        "active_claim_count": len(_unique([entry["claim_id"] for entry in entries if entry["claim_id"]])),
        "attention_count": len(attention_entries),
        "source_reconstruction": {
            "surface": "source_reconstruction_manifest",
            "complete_claim_count": len(complete_entries),
            "incomplete_claim_count": len(incomplete_entries),
            "review_status_counts": _review_status_counts(entries),
            "missing_component_counts": _missing_component_counts(incomplete_entries),
            "top_incomplete_claims": [_source_backlog_item(entry) for entry in incomplete_entries[:5]],
        },
        "resume_attention": {
            "attention_count": len(attention_entries),
            "top_items": [_attention_item(entry) for entry in attention_entries[:5]],
        },
        "truth_source": "kernel_state",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    if legacy_semantic_review is not None:
        summary["legacy_semantic_review"] = legacy_semantic_review
    if legacy_source_reconstruction is not None:
        summary["legacy_source_reconstruction"] = legacy_source_reconstruction
    if legacy_human_checkpoints is not None:
        summary["legacy_human_checkpoints"] = legacy_human_checkpoints
    return summary


def _legacy_semantic_review_summary(ws: WorkspacePaths, migration_dir: str | None) -> dict[str, Any] | None:
    if not migration_dir:
        return None
    manifest = build_legacy_semantic_review_manifest(ws, migration_dir=migration_dir)
    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=migration_dir)
    backlog = [
        item
        for item in manifest["items"]
        if item["review_status"] in {"pending", "needs_revision", "inconclusive"}
    ]
    return {
        "surface": "legacy_semantic_review_manifest",
        "migration_dir": manifest["migration_dir"],
        "review_item_count": manifest["review_item_count"],
        "review_progress": dict(manifest["review_progress"]),
        "semantic_lossless_proven": bool(manifest["semantic_lossless_proven"]),
        "open_human_checkpoint_count": int(worklist.get("open_human_checkpoint_count") or 0),
        "open_human_checkpoints": list(worklist.get("open_human_checkpoints") or []),
        "top_backlog_items": [_legacy_backlog_item(item) for item in backlog[:5]],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _legacy_source_reconstruction_summary(ws: WorkspacePaths, migration_dir: str | None) -> dict[str, Any] | None:
    if not migration_dir:
        return None
    manifest = build_legacy_source_reconstruction_manifest(ws, migration_dir=migration_dir)
    return {
        "surface": "legacy_source_reconstruction_manifest",
        "migration_dir": manifest["migration_dir"],
        "work_item_count": manifest["work_item_count"],
        "repair_status_counts": dict(manifest["repair_status_counts"]),
        "proposed_repair_count": int(manifest["proposed_repair_count"]),
        "top_backlog_items": [_legacy_source_backlog_item(item) for item in manifest["items"][:5]],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _legacy_human_checkpoint_summary(ws: WorkspacePaths, migration_dir: str | None) -> dict[str, Any] | None:
    if not migration_dir:
        return None
    packet = build_legacy_human_checkpoint_packet(ws, migration_dir=migration_dir)
    return {
        "surface": "legacy_human_checkpoint_packet",
        "migration_dir": packet["migration_dir"],
        "checkpoint_item_count": int(packet["checkpoint_item_count"]),
        "open_decision_count": int(packet["open_decision_count"]),
        "pending_request_count": int(packet["pending_request_count"]),
        "next_action_count": len(packet.get("next_actions") or []),
        "top_checkpoint_items": [
            _legacy_human_checkpoint_item(item)
            for item in packet.get("checkpoint_items", [])[:5]
        ],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _legacy_human_checkpoint_item(item: dict[str, Any]) -> dict[str, Any]:
    command = item.get("command") if isinstance(item.get("command"), dict) else {}
    return {
        "topic": str(item.get("topic") or ""),
        "active_claim_id": str(item.get("active_claim_id") or ""),
        "latest_review_id": str(item.get("latest_review_id") or ""),
        "review_status": str(item.get("review_status") or ""),
        "action": str(item.get("action") or ""),
        "mode": str(item.get("mode") or ""),
        "checkpoint_id": str(item.get("checkpoint_id") or ""),
        "reason": str(item.get("reason") or ""),
        "options": list(item.get("options") or []),
        "cli": str(command.get("cli") or ""),
        "mcp": str(command.get("mcp") or ""),
        "can_update_claim_trust": False,
    }


def _legacy_source_backlog_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "topic": str(item.get("topic") or ""),
        "active_claim_id": str(item.get("active_claim_id") or ""),
        "latest_review_id": str(item.get("latest_review_id") or ""),
        "repair_status": str(item.get("repair_status") or ""),
        "missing_components": list(item.get("missing_components") or []),
        "required_actions": list(item.get("required_actions") or []),
        "review_packet_cli": str(item.get("review_packet_cli") or ""),
        "can_update_claim_trust": False,
    }


def _legacy_backlog_item(item: dict[str, Any]) -> dict[str, Any]:
    latest = item.get("latest_semantic_review") if isinstance(item.get("latest_semantic_review"), dict) else {}
    return {
        "topic": item["topic"],
        "active_claim_id": item["active_claim_id"],
        "review_status": item["review_status"],
        "review_priority": item["review_priority"],
        "latest_review_id": str(latest.get("review_id") or ""),
        "packet_cli": item["packet_cli"],
        "can_update_claim_trust": False,
    }


def _source_backlog_item(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": entry["session_id"],
        "topic_id": entry["topic_id"],
        "claim_id": entry["claim_id"],
        "review_status": entry["source_reconstruction_review_status"],
        "missing_components": list(entry["missing_source_components"]),
        "next_actions": list(entry["next_actions"]),
        "review_packet_cli": f"aitp-v5 source reconstruction-review --claim {entry['claim_id']}",
        "can_update_claim_trust": False,
    }


def _attention_item(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": entry["session_id"],
        "topic_id": entry["topic_id"],
        "claim_id": entry["claim_id"],
        "attention_reasons": list(entry["attention_reasons"]),
        "next_actions": list(entry["next_actions"]),
    }


def _prioritized_attention_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(entries, key=_attention_priority)


def _attention_priority(entry: dict[str, Any]) -> tuple[int, int, str, str]:
    reasons = set(entry["attention_reasons"])
    severity = 0
    if "missing_claim_record" in reasons:
        severity -= 100
    if "missing_source_reconstruction" in reasons:
        severity -= 50
    if "source_reconstruction_review_pending" in reasons:
        severity -= 25
    if "missing_evidence_outputs" in reasons:
        severity -= 10
    return (severity, -len(reasons), entry["topic_id"], entry["session_id"])


def _review_status_counts(entries: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        if not entry["claim_id"]:
            continue
        status = entry["source_reconstruction_review_status"] or "pending"
        counts[status] = counts.get(status, 0) + 1
    return counts


def _missing_component_counts(entries: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        for component in entry["missing_source_components"]:
            counts[component] = counts.get(component, 0) + 1
    return counts


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
