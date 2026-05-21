"""Legacy L3 process-note migration helpers."""

from __future__ import annotations

from pathlib import Path

from brain.v5.evidence import record_evidence
from brain.v5.markdown import read_md
from brain.v5.paths import WorkspacePaths
from brain.v5.sensemaking import record_sensemaking_report


_L3_PROCESS_DIRS = (
    "ideate",
    "plan",
    "derive",
    "trace-derivation",
    "gap-audit",
    "diagnose",
    "integrate",
    "distill",
    "runs",
)


def migrate_legacy_l3_process_notes(
    ws: WorkspacePaths,
    root: Path,
    *,
    topic_id: str,
    claim_id: str,
) -> tuple[list[str], list[str]]:
    evidence_ids: list[str] = []
    report_ids: list[str] = []
    for path, display_path, activity in legacy_l3_process_candidates(root):
        fm, body = read_md(path)
        summary = str(
            fm.get("summary")
            or _first_paragraph(body)
            or f"Legacy L3 {activity} process note: {display_path}"
        )
        evidence = record_evidence(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            evidence_type=f"legacy_l3_{activity.replace('-', '_')}_process_note",
            status="legacy_seed",
            summary=summary,
            supports_outputs=["evidence_or_provenance"],
            source_refs=[f"legacy_l3_process:{path.as_posix()}"],
        )
        report = record_sensemaking_report(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            title=f"Legacy L3 {activity} process note: {path.stem}",
            summary=summary,
            evidence_refs=[evidence.evidence_id],
            next_actions=["review_legacy_l3_process_note"],
        )
        evidence_ids.append(evidence.evidence_id)
        report_ids.append(report.report_id)
    return evidence_ids, report_ids


def legacy_l3_process_candidates(root: Path) -> list[tuple[Path, str, str]]:
    candidates: list[tuple[Path, str, str]] = []
    seen: set[str] = set()
    for activity in _L3_PROCESS_DIRS:
        activity_root = root / "L3" / activity
        for path in sorted(activity_root.rglob("*.md")):
            if path.name.lower() in {"index.md", "readme.md"}:
                continue
            resolved = str(path.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            candidates.append((path, path.relative_to(root).as_posix(), activity))
    return candidates


def legacy_l3_process_audit_candidates(root: Path) -> list[tuple[str, str]]:
    return [
        (display_path, f"l3/{activity} process note candidate")
        for _path, display_path, activity in legacy_l3_process_candidates(root)
    ]


def _first_paragraph(body: str) -> str:
    lines = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped and lines:
            break
        if stripped and not stripped.startswith("#"):
            lines.append(stripped)
    return " ".join(lines)
