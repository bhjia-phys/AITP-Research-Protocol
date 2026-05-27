"""Run-local L3/L4/L3 iteration continuity surfaces."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from brain.v5.markdown import write_md
from brain.v5.paths import WorkspacePaths

_STATUSES = {"planned", "l4_returned", "synthesized", "blocked"}


@dataclass
class RunIterationRecord:
    topic_id: str
    run_id: str
    iteration_id: str
    plan_summary: str
    deliverables: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)
    stop_rules: list[str] = field(default_factory=list)
    l4_return_summary: str = ""
    l4_artifact_refs: list[str] = field(default_factory=list)
    l3_synthesis_summary: str = ""
    decision: str = ""
    status: str = "planned"
    claim_id: str = ""
    source_refs: list[str] = field(default_factory=list)
    files: dict[str, str] = field(default_factory=dict)
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    can_update_kernel_state: bool = True
    can_update_claim_trust: bool = False
    kind: str = "run_iteration"


def record_run_iteration(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    run_id: str,
    iteration_id: str,
    plan_summary: str,
    deliverables: list[str] | None = None,
    checks: list[str] | None = None,
    stop_rules: list[str] | None = None,
    l4_return_summary: str = "",
    l4_artifact_refs: list[str] | None = None,
    l3_synthesis_summary: str = "",
    decision: str = "",
    status: str = "planned",
    claim_id: str = "",
    source_refs: list[str] | None = None,
) -> RunIterationRecord:
    """Write Markdown-first run iteration records plus thin JSON contracts."""

    if status not in _STATUSES:
        raise ValueError(f"status must be one of {sorted(_STATUSES)}")
    record = RunIterationRecord(
        topic_id=topic_id,
        run_id=run_id,
        iteration_id=iteration_id,
        plan_summary=plan_summary,
        deliverables=deliverables or [],
        checks=checks or [],
        stop_rules=stop_rules or [],
        l4_return_summary=l4_return_summary,
        l4_artifact_refs=l4_artifact_refs or [],
        l3_synthesis_summary=l3_synthesis_summary,
        decision=decision,
        status=status,
        claim_id=claim_id,
        source_refs=source_refs or [],
    )
    files = _write_iteration_files(ws, record)
    record.files = {key: str(value) for key, value in files.items()}
    _write_journal(ws, record)
    return record


def load_run_iterations(ws: WorkspacePaths, topic_id: str, *, limit: int = 5) -> dict[str, Any]:
    """Load recent run iteration continuity summaries for briefs/status views."""

    run_root = ws.topic_dir(topic_id) / "L3" / "runs"
    if not run_root.exists():
        return {"present": False, "items": [], "summary_inputs_trusted": False, "can_update_claim_trust": False}
    items = []
    for path in sorted(run_root.glob("*/iteration_journal.json")):
        try:
            journal = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        iterations = [item for item in journal.get("iterations", []) if isinstance(item, dict)]
        if not iterations:
            continue
        last = iterations[-1]
        items.append({
            "topic_id": str(journal.get("topic_id") or topic_id),
            "run_id": str(journal.get("run_id") or path.parent.name),
            "iteration_count": len(iterations),
            "last_iteration_id": str(last.get("iteration_id") or ""),
            "last_iteration_status": str(last.get("status") or ""),
            "plan_summary": str(last.get("plan_summary") or ""),
            "l4_return_summary": str(last.get("l4_return_summary") or ""),
            "l3_synthesis_summary": str(last.get("l3_synthesis_summary") or ""),
            "decision": str(last.get("decision") or ""),
            "journal_path": str(path),
            "markdown_path": str(path.with_suffix(".md")),
            "orientation_only": True,
        })
    items = items[-limit:]
    return {
        "present": bool(items),
        "items": items,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _write_iteration_files(ws: WorkspacePaths, record: RunIterationRecord) -> dict[str, Path]:
    iteration_dir = _iteration_dir(ws, record)
    iteration_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "plan": iteration_dir / "plan.md",
        "plan_contract": iteration_dir / "plan.contract.json",
        "l4_return": iteration_dir / "l4_return.md",
        "l4_return_contract": iteration_dir / "l4_return.json",
        "l3_synthesis": iteration_dir / "l3_synthesis.md",
        "l3_synthesis_contract": iteration_dir / "l3_synthesis.json",
    }
    write_md(files["plan"], _frontmatter(record, "run_iteration_plan"), _plan_body(record))
    _write_json(files["plan_contract"], _plan_contract(record))
    write_md(files["l4_return"], _frontmatter(record, "run_iteration_l4_return"), _l4_return_body(record))
    _write_json(files["l4_return_contract"], _l4_return_contract(record))
    write_md(files["l3_synthesis"], _frontmatter(record, "run_iteration_l3_synthesis"), _synthesis_body(record))
    _write_json(files["l3_synthesis_contract"], _synthesis_contract(record))
    return files


def _write_journal(ws: WorkspacePaths, record: RunIterationRecord) -> None:
    run_dir = _run_dir(ws, record.topic_id, record.run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    journal_json_path = run_dir / "iteration_journal.json"
    journal_md_path = run_dir / "iteration_journal.md"
    journal = _load_journal(journal_json_path, record)
    entry = _journal_entry(record)
    journal["iterations"] = [
        item for item in journal.get("iterations", [])
        if item.get("iteration_id") != record.iteration_id
    ]
    journal["iterations"].append(entry)
    _write_json(journal_json_path, journal)
    write_md(
        journal_md_path,
        {
            "kind": "run_iteration_journal",
            "topic_id": record.topic_id,
            "run_id": record.run_id,
            "summary_inputs_trusted": False,
            "orientation_only": True,
            "can_update_claim_trust": False,
        },
        _journal_body(journal),
    )


def _load_journal(path: Path, record: RunIterationRecord) -> dict[str, Any]:
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                existing.setdefault("iterations", [])
                return existing
        except json.JSONDecodeError:
            pass
    return {
        "kind": "run_iteration_journal",
        "topic_id": record.topic_id,
        "run_id": record.run_id,
        "human_review_surface": "iteration_journal.md",
        "thin_machine_contract": True,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_claim_trust": False,
        "iterations": [],
    }


def _journal_entry(record: RunIterationRecord) -> dict[str, Any]:
    payload = asdict(record)
    payload["files"] = dict(record.files)
    payload["source_records"] = _source_records(record)
    return payload


def _frontmatter(record: RunIterationRecord, kind: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "topic_id": record.topic_id,
        "run_id": record.run_id,
        "iteration_id": record.iteration_id,
        "claim_id": record.claim_id,
        "status": record.status,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_claim_trust": False,
    }


def _plan_contract(record: RunIterationRecord) -> dict[str, Any]:
    return {
        "kind": "run_iteration_plan_contract",
        "topic_id": record.topic_id,
        "run_id": record.run_id,
        "iteration_id": record.iteration_id,
        "claim_id": record.claim_id,
        "plan_summary": record.plan_summary,
        "deliverables": list(record.deliverables),
        "checks": list(record.checks),
        "stop_rules": list(record.stop_rules),
        "thin_machine_contract": True,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _l4_return_contract(record: RunIterationRecord) -> dict[str, Any]:
    return {
        "kind": "run_iteration_l4_return_contract",
        "topic_id": record.topic_id,
        "run_id": record.run_id,
        "iteration_id": record.iteration_id,
        "l4_return_summary": record.l4_return_summary,
        "artifact_refs": list(record.l4_artifact_refs),
        "source_refs": list(record.source_refs),
        "thin_machine_contract": True,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _synthesis_contract(record: RunIterationRecord) -> dict[str, Any]:
    return {
        "kind": "run_iteration_l3_synthesis_contract",
        "topic_id": record.topic_id,
        "run_id": record.run_id,
        "iteration_id": record.iteration_id,
        "l3_synthesis_summary": record.l3_synthesis_summary,
        "decision": record.decision,
        "status": record.status,
        "thin_machine_contract": True,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _journal_body(journal: dict[str, Any]) -> str:
    lines = [
        "# Iteration Journal",
        "",
        "Markdown is the human review surface. JSON files are thin machine contracts for routing and replay.",
        "",
    ]
    for item in journal.get("iterations", []):
        lines.extend([
            f"## {item.get('iteration_id', '')}",
            "",
            f"Status: {item.get('status', '')}",
            "",
            f"Plan: {item.get('plan_summary', '')}",
            "",
            f"L4 return: {item.get('l4_return_summary', '') or 'Pending'}",
            "",
            f"L3 synthesis: {item.get('l3_synthesis_summary', '') or 'Pending'}",
            "",
            f"Decision: {item.get('decision', '') or 'Pending'}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def _plan_body(record: RunIterationRecord) -> str:
    return _sectioned_body(
        "Iteration Plan",
        record.plan_summary,
        {
            "Deliverables": record.deliverables,
            "Checks": record.checks,
            "Stop Rules": record.stop_rules,
        },
    )


def _l4_return_body(record: RunIterationRecord) -> str:
    return _sectioned_body(
        "L4 Return",
        record.l4_return_summary or "Pending L4 return.",
        {
            "Artifact Refs": record.l4_artifact_refs,
            "Source Refs": record.source_refs,
        },
    )


def _synthesis_body(record: RunIterationRecord) -> str:
    return _sectioned_body(
        "L3 Synthesis",
        record.l3_synthesis_summary or "Pending L3 synthesis.",
        {
            "Decision": [record.decision] if record.decision else [],
            "Trust Boundary": ["This iteration record cannot update claim confidence or promote L2 memory."],
        },
    )


def _sectioned_body(title: str, summary: str, sections: dict[str, list[str]]) -> str:
    lines = [f"# {title}", "", summary, ""]
    for heading, values in sections.items():
        lines.extend([f"## {heading}", ""])
        if values:
            lines.extend(f"- {value}" for value in values)
        else:
            lines.append("- None")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _source_records(record: RunIterationRecord) -> dict[str, list[str]]:
    return {
        "topics": [record.topic_id],
        "claims": [record.claim_id] if record.claim_id else [],
        "source_refs": list(record.source_refs),
    }


def _run_dir(ws: WorkspacePaths, topic_id: str, run_id: str) -> Path:
    return ws.topic_dir(topic_id) / "L3" / "runs" / run_id


def _iteration_dir(ws: WorkspacePaths, record: RunIterationRecord) -> Path:
    return _run_dir(ws, record.topic_id, record.run_id) / "iterations" / record.iteration_id


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
