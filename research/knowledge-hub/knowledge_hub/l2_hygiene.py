from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .l2_compiler import load_canonical_units, read_jsonl, write_json, write_text


GENERIC_TAGS = {"demo", "test", "example", "misc"}
CONTRADICTION_RELATIONS = {"contradicts", "conflicts_with", "incompatible_with", "conflict"}
STALE_DAYS_THRESHOLD = 180
MIN_SUMMARY_CHARS = 24

VALID_EDGE_RELATIONS: frozenset[str] = frozenset({
    "bridged_to",
    "depends_on",
    "derived_from",
    "specializes",
    "supports",
    "uses_method",
    "validated_by",
    "warned_by",
    "contradicts",
    "conflicts_with",
    "incompatible_with",
    "conflict",
    "related_to",
    "generalizes",
    "assumes",
    "proves",
    "illustrates",
})


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _canonical_root(kernel_root: Path) -> Path:
    return kernel_root / "canonical"


def _hygiene_root(kernel_root: Path) -> Path:
    return _canonical_root(kernel_root) / "hygiene"


def _parse_datetime(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _normalize_text(text: str) -> str:
    return " ".join(str(text or "").strip().lower().split())


def _link_counts(units: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, int]:
    counts = {str(unit["unit_id"]): 0 for unit in units}
    for unit in units:
        unit_id = str(unit["unit_id"])
        explicit_refs = {
            str(item).strip()
            for item in (unit.get("dependencies") or []) + (unit.get("related_units") or [])
            if str(item).strip()
        }
        counts[unit_id] += len(explicit_refs)

    for edge in edges:
        source = str(edge.get("source") or edge.get("from") or "").strip()
        target = str(edge.get("target") or edge.get("to") or "").strip()
        if source in counts:
            counts[source] += 1
        if target in counts:
            counts[target] += 1
    return counts


def _stale_summary_candidates(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    now = datetime.now().astimezone()
    findings: list[dict[str, Any]] = []
    for unit in units:
        reasons: list[str] = []
        summary = str(unit.get("summary") or "")
        title = str(unit.get("title") or "")
        updated_at = _parse_datetime(str(unit.get("updated_at") or ""))
        if len(summary.strip()) < MIN_SUMMARY_CHARS:
            reasons.append("summary_too_short")
        if _normalize_text(summary) == _normalize_text(title):
            reasons.append("summary_matches_title")
        if updated_at is not None:
            age_days = (now - updated_at).days
            if age_days >= STALE_DAYS_THRESHOLD:
                reasons.append(f"updated_at_older_than_{STALE_DAYS_THRESHOLD}_days")
        if reasons:
            findings.append(
                {
                    "unit_id": unit["unit_id"],
                    "unit_type": unit["unit_type"],
                    "title": unit["title"],
                    "path": unit["path"],
                    "reasons": reasons,
                }
            )
    return findings


def _has_explicit_link(left: dict[str, Any], right: dict[str, Any], edges: list[dict[str, Any]]) -> bool:
    left_id = str(left["unit_id"])
    right_id = str(right["unit_id"])
    left_refs = {str(item).strip() for item in (left.get("dependencies") or []) + (left.get("related_units") or [])}
    right_refs = {str(item).strip() for item in (right.get("dependencies") or []) + (right.get("related_units") or [])}
    if right_id in left_refs or left_id in right_refs:
        return True
    for edge in edges:
        source = str(edge.get("source") or edge.get("from") or "").strip()
        target = str(edge.get("target") or edge.get("to") or "").strip()
        if {source, target} == {left_id, right_id}:
            return True
    return False


def _shared_non_generic_tags(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    left_tags = {str(tag).strip() for tag in (left.get("tags") or []) if str(tag).strip()}
    right_tags = {str(tag).strip() for tag in (right.get("tags") or []) if str(tag).strip()}
    shared = sorted(tag for tag in (left_tags & right_tags) if tag.lower() not in GENERIC_TAGS)
    return shared


def _missing_bridge_candidates(units: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for index, left in enumerate(units):
        for right in units[index + 1 :]:
            shared_tags = _shared_non_generic_tags(left, right)
            if not shared_tags:
                continue
            if _has_explicit_link(left, right, edges):
                continue
            pair = tuple(sorted((str(left["unit_id"]), str(right["unit_id"]))))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            findings.append(
                {
                    "left_unit_id": left["unit_id"],
                    "right_unit_id": right["unit_id"],
                    "left_title": left["title"],
                    "right_title": right["title"],
                    "shared_tags": shared_tags,
                    "reason": "shared_tag_overlap_without_explicit_bridge",
                }
            )
    return findings


def _contradiction_findings(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for edge in edges:
        relation = str(
            edge.get("relation")
            or edge.get("edge_type")
            or edge.get("kind")
            or edge.get("type")
            or ""
        ).strip()
        if relation not in CONTRADICTION_RELATIONS:
            continue
        findings.append(
            {
                "source_unit_id": str(edge.get("source") or edge.get("from") or "").strip(),
                "target_unit_id": str(edge.get("target") or edge.get("to") or "").strip(),
                "relation": relation,
            }
        )
    return findings


def _connectivity_findings(units: list[dict[str, Any]], edges: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    counts = _link_counts(units, edges)
    orphaned: list[dict[str, Any]] = []
    weak: list[dict[str, Any]] = []
    for unit in units:
        unit_id = str(unit["unit_id"])
        link_count = counts.get(unit_id, 0)
        row = {
            "unit_id": unit["unit_id"],
            "unit_type": unit["unit_type"],
            "title": unit["title"],
            "path": unit["path"],
            "link_count": link_count,
        }
        if link_count == 0:
            orphaned.append(row)
        elif link_count == 1:
            weak.append(row)
    return orphaned, weak


def build_workspace_hygiene_report(kernel_root: Path) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    units = load_canonical_units(kernel_root)
    edges = read_jsonl(_canonical_root(kernel_root) / "edges.jsonl")

    stale_summary_candidates = _stale_summary_candidates(units)
    missing_bridge_candidates = _missing_bridge_candidates(units, edges)
    contradiction_findings = _contradiction_findings(edges)
    orphaned_units, weakly_connected_units = _connectivity_findings(units, edges)

    summary = {
        "total_units": len(units),
        "edge_count": len(edges),
        "empty_canonical_store": len(units) == 0,
        "finding_counts": {
            "stale_summary_candidates": len(stale_summary_candidates),
            "missing_bridge_candidates": len(missing_bridge_candidates),
            "contradiction_findings": len(contradiction_findings),
            "orphaned_units": len(orphaned_units),
            "weakly_connected_units": len(weakly_connected_units),
        },
    }

    total_findings = sum(summary["finding_counts"].values())
    summary["total_findings"] = total_findings
    summary["status"] = "clean" if total_findings == 0 else "needs_review"

    return {
        "kind": "l2_workspace_hygiene_report",
        "report_version": 1,
        "generated_at": now_iso(),
        "source_contract_path": "canonical/L2_COMPILER_PROTOCOL.md",
        "audit_mode": "report_only",
        "summary": summary,
        "stale_summary_candidates": stale_summary_candidates,
        "missing_bridge_candidates": missing_bridge_candidates,
        "contradiction_findings": contradiction_findings,
        "orphaned_units": orphaned_units,
        "weakly_connected_units": weakly_connected_units,
    }


def render_workspace_hygiene_report_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    finding_counts = summary.get("finding_counts") or {}
    lines = [
        "# Workspace Hygiene Report",
        "",
        f"- Generated at: `{payload.get('generated_at') or '(missing)'}`",
        f"- Source contract: `{payload.get('source_contract_path') or '(missing)'}`",
        f"- Audit mode: `{payload.get('audit_mode') or '(missing)'}`",
        f"- Status: `{summary.get('status') or '(missing)'}`",
        f"- Total canonical units: `{summary.get('total_units', 0)}`",
        f"- Edge count: `{summary.get('edge_count', 0)}`",
        f"- Total findings: `{summary.get('total_findings', 0)}`",
        "",
        "## Finding Counts",
        "",
        f"- Stale summary candidates: `{finding_counts.get('stale_summary_candidates', 0)}`",
        f"- Missing bridge candidates: `{finding_counts.get('missing_bridge_candidates', 0)}`",
        f"- Contradiction findings: `{finding_counts.get('contradiction_findings', 0)}`",
        f"- Orphaned units: `{finding_counts.get('orphaned_units', 0)}`",
        f"- Weakly connected units: `{finding_counts.get('weakly_connected_units', 0)}`",
        "",
    ]

    if summary.get("empty_canonical_store"):
        lines.extend(
            [
                "No canonical units were found in the current workspace.",
                "",
            ]
        )

    def add_unit_section(title: str, rows: list[dict[str, Any]], extra_keys: list[str] | None = None) -> None:
        lines.extend([f"## {title}", ""])
        if not rows:
            lines.append("- `(none)`")
            lines.append("")
            return
        for row in rows:
            line = f"- `{row.get('unit_id') or '(missing)'}` {row.get('title') or ''} (`{row.get('path') or '(missing)'}`)"
            lines.append(line)
            for key in extra_keys or []:
                value = row.get(key)
                if isinstance(value, list):
                    display = ", ".join(str(item) for item in value) or "(none)"
                else:
                    display = str(value or "(none)")
                lines.append(f"  - {key}: {display}")
        lines.append("")

    add_unit_section("Stale Summary Candidates", payload.get("stale_summary_candidates") or [], ["reasons"])

    lines.extend(["## Missing Bridge Candidates", ""])
    bridge_rows = payload.get("missing_bridge_candidates") or []
    if not bridge_rows:
        lines.append("- `(none)`")
    else:
        for row in bridge_rows:
            lines.append(
                f"- `{row.get('left_unit_id')}` <-> `{row.get('right_unit_id')}` shared_tags=`{', '.join(row.get('shared_tags') or []) or '(none)'}`"
            )
    lines.append("")

    lines.extend(["## Contradiction Findings", ""])
    contradiction_rows = payload.get("contradiction_findings") or []
    if not contradiction_rows:
        lines.append("- `(none)`")
    else:
        for row in contradiction_rows:
            lines.append(
                f"- `{row.get('source_unit_id')}` -[{row.get('relation') or 'contradiction'}]-> `{row.get('target_unit_id')}`"
            )
    lines.append("")

    add_unit_section("Orphaned Units", payload.get("orphaned_units") or [], ["link_count"])
    add_unit_section("Weakly Connected Units", payload.get("weakly_connected_units") or [], ["link_count"])

    lines.extend(
        [
            "## Hygiene Rule",
            "",
            "This report is audit-only. Findings are candidates for review unless the underlying canonical artifacts already state the issue explicitly.",
            "",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def materialize_workspace_hygiene_report(kernel_root: Path) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    hygiene_root = _hygiene_root(kernel_root)
    payload = build_workspace_hygiene_report(kernel_root)
    json_path = hygiene_root / "workspace_hygiene_report.json"
    md_path = hygiene_root / "workspace_hygiene_report.md"
    write_json(json_path, payload)
    write_text(md_path, render_workspace_hygiene_report_markdown(payload))
    return {
        "payload": payload,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }


def validate_edge_types(kernel_root: Path) -> dict[str, Any]:
    """Validate that all edges use known relation types."""
    edges_path = _canonical_root(kernel_root) / "edges.jsonl"
    if not edges_path.exists():
        return {"valid": True, "total": 0, "unknown": [], "known_types": sorted(VALID_EDGE_RELATIONS)}

    edges = read_jsonl(edges_path)
    unknown: list[dict[str, str]] = []
    for edge in edges:
        relation = str(
            edge.get("relation")
            or edge.get("edge_type")
            or edge.get("kind")
            or edge.get("type")
            or ""
        ).strip()
        if relation and relation not in VALID_EDGE_RELATIONS:
            unknown.append({
                "relation": relation,
                "from": str(edge.get("from") or edge.get("source") or ""),
                "to": str(edge.get("to") or edge.get("target") or ""),
            })

    return {
        "valid": len(unknown) == 0,
        "total": len(edges),
        "unknown_count": len(unknown),
        "unknown": unknown[:20],
        "known_types": sorted(VALID_EDGE_RELATIONS),
    }
