"""Derived human-facing summary files for AITP v5 sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from brain.v5.brief import build_execution_brief
from brain.v5.contracts import require_valid_summary_orientation
from brain.v5.evidence import list_evidence_for_claim
from brain.v5.markdown import read_md, write_md
from brain.v5.models import ClaimRecord, MemoryEntryRecord, SessionBinding, ToolRunRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records, list_valid_records
from brain.v5.workspace import get_claim


_SUMMARY_ROLES = ("task_plan", "findings", "progress")


@dataclass
class SessionSummaryBundle:
    session_id: str
    topic_id: str
    active_claim: str
    summary_dir: str
    files: dict[str, str]
    kind: str = "session_summary_bundle"
    derived_from: str = "kernel_state"
    truth_source: bool = False
    orientation_only: bool = True
    adapter_rule: str = "read_for_orientation_then_call_kernel_before_trust_updates"
    source_records: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class WorkspaceSummaryBundle:
    summary_dir: str
    files: dict[str, str]
    session_count: int
    active_claim_count: int
    memory_entry_count: int
    kind: str = "workspace_summary_bundle"
    derived_from: str = "kernel_state"
    truth_source: bool = False
    orientation_only: bool = True
    adapter_rule: str = "read_for_orientation_then_call_kernel_before_trust_updates"
    source_records: dict[str, list[str]] = field(default_factory=dict)


def write_session_summary(ws: WorkspacePaths, session_id: str) -> SessionSummaryBundle:
    """Write derived task/findings/progress views for one session.

    These files are a friendly working shell for humans and agents. They are
    always regenerated from typed records and never become a truth source.
    """

    brief = build_execution_brief(ws, session_id)
    session = brief["session"]
    active_claim = session.get("active_claim", "")
    topic_id = session["topic_id"]
    summary_dir = ws.root / "surfaces" / "session_summaries" / session_id

    claim = get_claim(ws, active_claim) if active_claim else None
    evidence_records = list_evidence_for_claim(ws, active_claim) if active_claim else []
    tool_runs = _tool_runs_for_claim(ws, active_claim) if active_claim else []
    memory_entries = brief.get("known_context", {}).get("memory_entries", [])
    files = {
        "task_plan": summary_dir / "task_plan.md",
        "findings": summary_dir / "findings.md",
        "progress": summary_dir / "progress.md",
    }

    source_records = {
        "sessions": [session_id],
        "claims": [active_claim] if active_claim else [],
        "evidence": [record.evidence_id for record in evidence_records],
        "tool_runs": [record.run_id for record in tool_runs],
        "memory_entries": [entry["entry_id"] for entry in memory_entries],
        "validation_results": _validation_result_ids_from_memory_entries(memory_entries),
    }

    for role, path in files.items():
        write_md(
            path,
            _summary_frontmatter(
                role=role,
                session_id=session_id,
                topic_id=topic_id,
                active_claim=active_claim,
                source_records=source_records,
            ),
            _summary_body(
                role=role,
                brief=brief,
                claim_statement=claim.statement if claim else "",
                evidence_records=evidence_records,
                tool_runs=tool_runs,
                memory_entries=memory_entries,
            ),
        )

    return SessionSummaryBundle(
        session_id=session_id,
        topic_id=topic_id,
        active_claim=active_claim,
        summary_dir=str(summary_dir),
        files={role: str(path) for role, path in files.items()},
        source_records=source_records,
    )


def write_workspace_summary(ws: WorkspacePaths) -> WorkspaceSummaryBundle:
    """Write an orientation-only summary across active workspace sessions."""

    summary_dir = ws.root / "surfaces" / "workspace_summary"
    overview_path = summary_dir / "overview.md"
    sessions = list_records(ws.root / "runtime" / "sessions", SessionBinding)
    claims_by_id = {
        claim.claim_id: claim
        for claim in list_records(ws.registry_dir("claims"), ClaimRecord)
    }
    active_claim_ids = _unique([session.active_claim for session in sessions if session.active_claim])
    active_claims = [
        claims_by_id[claim_id]
        for claim_id in active_claim_ids
        if claim_id in claims_by_id
    ]
    memory_entries = [
        entry
        for entry in list_records(ws.root / "memory" / "l2" / "entries", MemoryEntryRecord)
        if entry.status == "active" and entry.source_claim_id in active_claim_ids
    ]
    source_records = {
        "sessions": [session.session_id for session in sessions],
        "topics": _unique([session.topic_id for session in sessions if session.topic_id]),
        "claims": [claim.claim_id for claim in active_claims],
        "memory_entries": [entry.entry_id for entry in memory_entries],
        "validation_results": _validation_result_ids_from_memory_records(memory_entries),
    }
    write_md(
        overview_path,
        _workspace_summary_frontmatter(source_records=source_records),
        _workspace_overview_body(
            sessions=sessions,
            claims_by_id=claims_by_id,
            active_claims=active_claims,
            memory_entries=memory_entries,
        ),
    )
    return WorkspaceSummaryBundle(
        summary_dir=str(summary_dir),
        files={"overview": str(overview_path)},
        session_count=len(sessions),
        active_claim_count=len(active_claims),
        memory_entry_count=len(memory_entries),
        source_records=source_records,
    )


def read_summary_orientation(ws: WorkspacePaths, session_id: str) -> dict[str, Any]:
    """Read generated summaries as orientation only.

    Even if a user or model edits a summary frontmatter to claim truth-source
    status, the returned payload keeps the kernel contract explicit.
    """

    summary_dir = ws.root / "surfaces" / "session_summaries" / session_id
    files: dict[str, dict[str, Any]] = {}
    for role in _SUMMARY_ROLES:
        path = summary_dir / f"{role}.md"
        fm, body = read_md(path)
        files[role] = {
            "path": str(path),
            "frontmatter": fm,
            "body": body,
            "truth_source": False,
            "orientation_only": True,
        }

    payload = {
        "kind": "summary_orientation",
        "session_id": session_id,
        "summary_dir": str(summary_dir),
        "files": files,
        "truth_source": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
    }
    return require_valid_summary_orientation(payload)


def _summary_frontmatter(
    *,
    role: str,
    session_id: str,
    topic_id: str,
    active_claim: str,
    source_records: dict[str, list[str]],
) -> dict[str, Any]:
    return {
        "kind": "derived_summary",
        "summary_role": role,
        "session_id": session_id,
        "topic_id": topic_id,
        "active_claim": active_claim,
        "derived_from": "kernel_state",
        "truth_source": False,
        "orientation_only": True,
        "adapter_rule": "read_for_orientation_then_call_kernel_before_trust_updates",
        "source_records": source_records,
    }


def _workspace_summary_frontmatter(*, source_records: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "kind": "derived_workspace_summary",
        "summary_role": "workspace_overview",
        "derived_from": "kernel_state",
        "truth_source": False,
        "orientation_only": True,
        "adapter_rule": "read_for_orientation_then_call_kernel_before_trust_updates",
        "source_records": source_records,
    }


def _workspace_overview_body(
    *,
    sessions: list[SessionBinding],
    claims_by_id: dict[str, ClaimRecord],
    active_claims: list[ClaimRecord],
    memory_entries: list[MemoryEntryRecord],
) -> str:
    lines = [
        "# Workspace Summary",
        "",
        "This file is regenerated from typed AITP kernel records. Use it for orientation only.",
        "",
        "## Active Sessions",
        "",
    ]
    if sessions:
        for session in sessions:
            lines.append(
                f"- `{session.session_id}` topic `{session.topic_id}` claim `{session.active_claim or 'none'}`"
            )
    else:
        lines.append("- No active session bindings are recorded.")

    lines.extend(["", "## Active Claims", ""])
    if active_claims:
        for claim in active_claims:
            lines.append(f"- `{claim.claim_id}` [{claim.confidence_state}/{claim.evidence_profile}] {claim.statement}")
    else:
        lines.append("- No active claims are bound to recorded sessions.")

    lines.extend(["", "## Promoted Memory", ""])
    if memory_entries:
        for entry in memory_entries:
            claim = claims_by_id.get(entry.source_claim_id)
            statement = claim.statement if claim else entry.statement
            lines.append(f"- `{entry.entry_id}` for claim `{entry.source_claim_id}`")
            lines.append(f"  Statement: {statement}")
            lines.append(f"  Evidence refs: {', '.join(entry.evidence_refs) or 'none'}")
            lines.append(f"  Validation results: {', '.join(entry.validation_result_ids) or 'none'}")
    else:
        lines.append("- No active promoted memory entries are linked to active session claims.")
    return "\n".join(lines) + "\n"


def _summary_body(
    *,
    role: str,
    brief: dict[str, Any],
    claim_statement: str,
    evidence_records: list,
    tool_runs: list[ToolRunRecord],
    memory_entries: list[dict[str, Any]],
) -> str:
    if role == "task_plan":
        return _task_plan_body(brief, claim_statement)
    if role == "findings":
        return _findings_body(brief, claim_statement, evidence_records, memory_entries)
    if role == "progress":
        return _progress_body(brief, claim_statement, evidence_records, tool_runs, memory_entries)
    raise ValueError(f"unknown summary role: {role}")


def _task_plan_body(brief: dict[str, Any], claim_statement: str) -> str:
    focus = brief["current_focus"]
    next_actions = brief["next_action_candidates"]
    questions = brief["mandatory_reflection"]
    forbidden = brief["forbidden_now"]
    lines = [
        "# Task Plan",
        "",
        "This file is regenerated from typed AITP kernel records. Use it for orientation only.",
        "",
        "## Current Focus",
        "",
        f"- Topic: `{brief['session']['topic_id']}`",
        f"- Active claim: `{focus['active_claim']}`",
        f"- Claim statement: {claim_statement}",
        f"- Confidence: `{focus['confidence_state']}`",
        f"- Main uncertainty: {focus['main_uncertainty']}",
        f"- Flow profile: `{brief['flow_profile']['profile']}`",
        "",
        "## Next Actions",
        "",
    ]
    if next_actions:
        for item in next_actions:
            lines.append(f"- `{item['action']}`: {item['why']}")
    else:
        lines.append("- No active next action was generated by the kernel.")

    lines.extend(["", "## Mandatory Reflection", ""])
    if questions:
        for question in questions:
            lines.append(f"- {question['question']}")
    else:
        lines.append("- No mandatory question is currently required.")

    lines.extend(["", "## Forbidden Now", ""])
    lines.extend(f"- `{item}`" for item in forbidden)
    return "\n".join(lines) + "\n"


def _findings_body(
    brief: dict[str, Any],
    claim_statement: str,
    evidence_records: list,
    memory_entries: list[dict[str, Any]],
) -> str:
    focus = brief["current_focus"]
    coverage = brief["evidence_coverage"]
    lines = [
        "# Findings",
        "",
        "This file summarizes typed claims and evidence. Edits here do not change the kernel ledger.",
        "",
        "## Active Claim",
        "",
        f"- Claim id: `{focus['active_claim']}`",
        f"- Statement: {claim_statement}",
        f"- Evidence profile: `{focus['evidence_profile']}`",
        f"- Confidence: `{focus['confidence_state']}`",
        f"- Uncertainty: {focus['main_uncertainty']}",
        "",
        "## Evidence Coverage",
        "",
        f"- Satisfied outputs: {', '.join(coverage['satisfied_outputs']) or 'none'}",
        f"- Missing outputs: {', '.join(coverage['missing_outputs']) or 'none'}",
        "",
        "## Evidence Records",
        "",
    ]
    if evidence_records:
        for record in evidence_records:
            lines.extend(
                [
                    f"- `{record.evidence_id}` [{record.status}/{record.evidence_type}]",
                    f"  Summary: {record.summary}",
                    f"  Supports: {', '.join(record.supports_outputs) or 'none'}",
                ]
            )
    else:
        lines.append("- No evidence records are linked to this claim.")
    lines.extend(["", "## L2 Memory Links", ""])
    _append_memory_entry_lines(lines, memory_entries)
    return "\n".join(lines) + "\n"


def _progress_body(
    brief: dict[str, Any],
    claim_statement: str,
    evidence_records: list,
    tool_runs: list[ToolRunRecord],
    memory_entries: list[dict[str, Any]],
) -> str:
    session = brief["session"]
    lines = [
        "# Progress",
        "",
        "This file is a derived session log view. Trust-changing updates must go through the kernel.",
        "",
        "## Session",
        "",
        f"- Session id: `{session['session_id']}`",
        f"- Runtime: `{session['runtime']}`",
        f"- Active route: `{session['active_route']}`",
        f"- Active cycle: `{session['active_cycle']}`",
        f"- Active claim statement: {claim_statement}",
        "",
        "## Evidence Recorded",
        "",
    ]
    if evidence_records:
        for record in evidence_records:
            lines.append(f"- `{record.evidence_id}`: {record.summary}")
    else:
        lines.append("- No evidence has been recorded yet.")

    lines.extend(["", "## Tool Runs", ""])
    if tool_runs:
        for run in tool_runs:
            outputs = ", ".join(f"{key}={value}" for key, value in run.outputs.items()) or "no outputs"
            lines.append(f"- `{run.run_id}` via `{run.tool_family}:{run.tool_name}` ({run.evidence_status}); {outputs}")
    else:
        lines.append("- No tool runs are linked to this claim.")
    lines.extend(["", "## Promoted Memory", ""])
    _append_memory_entry_lines(lines, memory_entries)
    return "\n".join(lines) + "\n"


def _append_memory_entry_lines(lines: list[str], memory_entries: list[dict[str, Any]]) -> None:
    if not memory_entries:
        lines.append("- No active L2 memory entries are linked to this claim.")
        return
    for entry in memory_entries:
        validation_ids = entry.get("validation_result_ids") or []
        lines.append(f"- `{entry['entry_id']}` [{entry['memory_kind']}] scope: {entry['scope']}")
        lines.append(f"  Evidence refs: {', '.join(entry.get('evidence_refs', [])) or 'none'}")
        lines.append(f"  Validation results: {', '.join(validation_ids) or 'none'}")


def _validation_result_ids_from_memory_entries(memory_entries: list[dict[str, Any]]) -> list[str]:
    seen = set()
    result: list[str] = []
    for entry in memory_entries:
        for result_id in entry.get("validation_result_ids") or []:
            if result_id and result_id not in seen:
                seen.add(result_id)
                result.append(result_id)
    return result


def _validation_result_ids_from_memory_records(memory_entries: list[MemoryEntryRecord]) -> list[str]:
    return _unique(
        result_id
        for entry in memory_entries
        for result_id in entry.validation_result_ids
        if result_id
    )


def _unique(values) -> list[str]:
    seen = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _tool_runs_for_claim(ws: WorkspacePaths, claim_id: str) -> list[ToolRunRecord]:
    return [
        run
        for run in list_valid_records(ws.registry_dir("tool_runs"), ToolRunRecord)
        if run.claim_id == claim_id
    ]
