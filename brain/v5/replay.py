"""Workspace-level replay packet for resuming long-running AITP work."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from brain.v5.brief import build_execution_brief
from brain.v5.markdown import write_md
from brain.v5.models import ClaimRecord, MemoryEntryRecord, SessionBinding
from brain.v5.paths import WorkspacePaths
from brain.v5.source_reconstruction import audit_source_reconstruction
from brain.v5.store import list_records


@dataclass
class WorkspaceReplayPacket:
    replay_dir: str
    files: dict[str, str]
    entry_count: int
    attention_count: int
    entries: list[dict[str, Any]] = field(default_factory=list)
    source_records: dict[str, list[str]] = field(default_factory=dict)
    kind: str = "workspace_replay_packet"
    derived_from: str = "kernel_state"
    truth_source: bool = False
    orientation_only: bool = True
    adapter_rule: str = "read_for_orientation_then_call_kernel_before_trust_updates"
    can_update_kernel_state: bool = False
    can_update_claim_trust: bool = False


def write_workspace_replay_packet(ws: WorkspacePaths) -> WorkspaceReplayPacket:
    """Write an orientation-only packet for resuming active sessions."""

    replay_dir = ws.root / "surfaces" / "workspace_replay"
    replay_path = replay_dir / "replay_packet.md"
    sessions = list_records(ws.root / "runtime" / "sessions", SessionBinding)
    claims = {claim.claim_id: claim for claim in list_records(ws.registry_dir("claims"), ClaimRecord)}
    memory_entries = [
        entry
        for entry in list_records(ws.root / "memory" / "l2" / "entries", MemoryEntryRecord)
        if entry.status == "active"
    ]
    entries = [_entry_for_session(ws, session, claims, memory_entries) for session in sessions]
    attention = [entry for entry in entries if entry["attention_reasons"]]
    source_records = {
        "sessions": [entry["session_id"] for entry in entries],
        "topics": _unique([entry["topic_id"] for entry in entries if entry["topic_id"]]),
        "claims": [entry["claim_id"] for entry in entries if entry["claim_id"]],
        "memory_entries": _unique([mid for entry in entries for mid in entry["memory_entry_ids"]]),
        "validation_results": _unique([vid for entry in entries for vid in entry["validation_result_ids"]]),
    }
    write_md(
        replay_path,
        _frontmatter(source_records),
        _body(entries),
    )
    return WorkspaceReplayPacket(
        replay_dir=str(replay_dir),
        files={"replay_packet": str(replay_path)},
        entry_count=len(entries),
        attention_count=len(attention),
        entries=entries,
        source_records=source_records,
    )


def _entry_for_session(
    ws: WorkspacePaths,
    session: SessionBinding,
    claims: dict[str, ClaimRecord],
    memory_entries: list[MemoryEntryRecord],
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
            "missing_source_components": ["claim_record"],
            "memory_entry_ids": [],
            "validation_result_ids": [],
            "attention_reasons": ["missing_claim_record"],
        }
    brief = build_execution_brief(ws, session.session_id)
    source_audit = audit_source_reconstruction(ws, claim_id=claim.claim_id)
    claim_memory = [entry for entry in memory_entries if entry.source_claim_id == claim.claim_id]
    missing_outputs = brief.get("evidence_coverage", {}).get("missing_outputs", [])
    missing_source = source_audit["missing_components"]
    reasons = []
    if claim.confidence_state == "hypothesis":
        reasons.append("claim_still_hypothesis")
    if missing_outputs:
        reasons.append("missing_evidence_outputs")
    if missing_source:
        reasons.append("missing_source_reconstruction")
    return {
        "session_id": session.session_id,
        "topic_id": session.topic_id,
        "claim_id": claim.claim_id,
        "claim_statement": claim.statement,
        "confidence_state": claim.confidence_state,
        "risk_level": brief.get("risk_assessment", {}).get("level", ""),
        "missing_outputs": list(missing_outputs),
        "satisfied_outputs": list(brief.get("evidence_coverage", {}).get("satisfied_outputs", [])),
        "next_actions": [item.get("action", "") for item in brief.get("next_action_candidates", [])],
        "source_reconstruction_complete": source_audit["complete"],
        "missing_source_components": list(missing_source),
        "memory_entry_ids": [entry.entry_id for entry in claim_memory],
        "validation_result_ids": _unique([vid for entry in claim_memory for vid in entry.validation_result_ids]),
        "attention_reasons": reasons,
    }


def _frontmatter(source_records: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "kind": "derived_workspace_replay",
        "derived_from": "kernel_state",
        "truth_source": False,
        "orientation_only": True,
        "adapter_rule": "read_for_orientation_then_call_kernel_before_trust_updates",
        "source_records": source_records,
    }


def _body(entries: list[dict[str, Any]]) -> str:
    lines = [
        "# Workspace Replay Packet",
        "",
        "This file is regenerated from typed AITP kernel records. Use it for orientation only.",
        "",
    ]
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
        lines.append(f"- Attention: {', '.join(entry['attention_reasons']) or 'none'}")
        lines.append(f"- Next actions: {', '.join(entry['next_actions']) or 'none'}")
        lines.append("")
    return "\n".join(lines)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
