"""Derived human-facing summary files for AITP v5 sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from brain.v5.brief import build_execution_brief
from brain.v5.evidence import list_evidence_for_claim
from brain.v5.markdown import read_md, write_md
from brain.v5.models import ToolRunRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records
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

    return {
        "kind": "summary_orientation",
        "session_id": session_id,
        "summary_dir": str(summary_dir),
        "files": files,
        "truth_source": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
    }


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


def _summary_body(
    *,
    role: str,
    brief: dict[str, Any],
    claim_statement: str,
    evidence_records: list,
    tool_runs: list[ToolRunRecord],
) -> str:
    if role == "task_plan":
        return _task_plan_body(brief, claim_statement)
    if role == "findings":
        return _findings_body(brief, claim_statement, evidence_records)
    if role == "progress":
        return _progress_body(brief, claim_statement, evidence_records, tool_runs)
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


def _findings_body(brief: dict[str, Any], claim_statement: str, evidence_records: list) -> str:
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
    return "\n".join(lines) + "\n"


def _progress_body(
    brief: dict[str, Any],
    claim_statement: str,
    evidence_records: list,
    tool_runs: list[ToolRunRecord],
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
    return "\n".join(lines) + "\n"


def _tool_runs_for_claim(ws: WorkspacePaths, claim_id: str) -> list[ToolRunRecord]:
    return [
        run
        for run in list_records(ws.registry_dir("tool_runs"), ToolRunRecord)
        if run.claim_id == claim_id
    ]
