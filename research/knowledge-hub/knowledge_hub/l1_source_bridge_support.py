from __future__ import annotations

from pathlib import Path
from typing import Any


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _frontmatter(**fields: str) -> str:
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def _kernel_relative_status(path_value: str, *, kernel_root: Path) -> str:
    normalized = str(path_value or "").strip()
    if not normalized:
        return "missing"
    candidate = Path(normalized)
    if not candidate.is_absolute():
        candidate = kernel_root / candidate
    return "available" if candidate.exists() else "expected_but_missing"


def _append_anchor(
    entry: dict[str, Any],
    *,
    anchor_kind: str,
    summary: str,
    reading_depth: str = "",
    evidence_excerpt: str = "",
    evidence_sentence_ids: list[str] | None = None,
    paired_source_id: str = "",
    basis_summary: str = "",
    comparison_basis: str = "",
    direction: str = "",
) -> None:
    normalized_summary = str(summary or "").strip()
    normalized_excerpt = str(evidence_excerpt or "").strip()
    normalized_basis_summary = str(basis_summary or "").strip()
    normalized_paired_source_id = str(paired_source_id or "").strip()
    normalized_sentence_ids = _dedupe_strings([str(item) for item in (evidence_sentence_ids or [])])
    dedupe_key = (
        str(anchor_kind or "").strip().lower(),
        normalized_summary.lower(),
        normalized_excerpt.lower(),
        normalized_paired_source_id.lower(),
        "|".join(normalized_sentence_ids).lower(),
        normalized_basis_summary.lower(),
        str(direction or "").strip().lower(),
    )
    seen_keys = entry.setdefault("_anchor_seen_keys", set())
    if dedupe_key in seen_keys:
        return
    seen_keys.add(dedupe_key)

    anchors = entry.setdefault("anchors", [])
    anchor_counts = entry.setdefault("anchor_counts", {})
    anchors.append(
        {
            "anchor_kind": str(anchor_kind or "").strip() or "anchor",
            "summary": normalized_summary,
            "reading_depth": str(reading_depth or "").strip(),
            "evidence_excerpt": normalized_excerpt,
            "evidence_sentence_ids": normalized_sentence_ids,
            "paired_source_id": normalized_paired_source_id,
            "basis_summary": normalized_basis_summary,
            "comparison_basis": str(comparison_basis or "").strip(),
            "direction": str(direction or "").strip(),
        }
    )
    anchor_counts[str(anchor_kind or "").strip() or "anchor"] = int(
        anchor_counts.get(str(anchor_kind or "").strip() or "anchor") or 0
    ) + 1


def build_l1_source_anchor_index(
    *,
    kernel_root: Path,
    topic_slug: str,
    raw_sources: list[dict[str, Any]],
    l1_source_intake: dict[str, Any],
    source_intelligence: dict[str, Any],
    updated_at: str,
    updated_by: str,
) -> dict[str, Any]:
    relevance_by_source_id: dict[str, dict[str, Any]] = {}
    for row in source_intelligence.get("relevance_rows") or []:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or "").strip()
        if not source_id:
            continue
        relevance_by_source_id[source_id] = {
            "relevance_tier": str(row.get("relevance_tier") or "").strip(),
            "role_labels": _dedupe_strings([str(item) for item in row.get("role_labels") or []]),
        }

    entries_by_source_id: dict[str, dict[str, Any]] = {}

    def _ensure_entry(source_id: str) -> dict[str, Any]:
        normalized_source_id = str(source_id or "").strip()
        if normalized_source_id in entries_by_source_id:
            return entries_by_source_id[normalized_source_id]

        raw_row = next(
            (
                row
                for row in raw_sources
                if str((row or {}).get("source_id") or "").strip() == normalized_source_id
            ),
            {},
        )
        relevance_row = relevance_by_source_id.get(normalized_source_id) or {}
        source_index_path = str(raw_row.get("source_index_path") or "").strip()
        source_json_path = str(raw_row.get("source_json_path") or "").strip()
        snapshot_path = str(raw_row.get("snapshot_path") or "").strip()
        entry = {
            "source_id": normalized_source_id,
            "source_type": str(raw_row.get("source_type") or "").strip(),
            "title": str(raw_row.get("title") or "").strip(),
            "summary": str(raw_row.get("summary") or "").strip(),
            "canonical_source_id": str(raw_row.get("canonical_source_id") or "").strip(),
            "relevance_tier": str(relevance_row.get("relevance_tier") or "").strip(),
            "role_labels": list(relevance_row.get("role_labels") or []),
            "l0_refs": {
                "source_index_path": source_index_path,
                "source_json_path": source_json_path,
                "source_json_status": _kernel_relative_status(source_json_path, kernel_root=kernel_root),
                "snapshot_path": snapshot_path,
                "snapshot_status": _kernel_relative_status(snapshot_path, kernel_root=kernel_root),
                "absolute_path": str(raw_row.get("absolute_path") or "").strip(),
                "abs_url": str(raw_row.get("abs_url") or "").strip(),
            },
            "anchors": [],
            "anchor_counts": {},
        }
        entries_by_source_id[normalized_source_id] = entry
        return entry

    for row in raw_sources:
        source_id = str((row or {}).get("source_id") or "").strip()
        if source_id:
            _ensure_entry(source_id)

    for row in l1_source_intake.get("assumption_rows") or []:
        if not isinstance(row, dict):
            continue
        _append_anchor(
            _ensure_entry(str(row.get("source_id") or "").strip()),
            anchor_kind="assumption",
            summary=str(row.get("assumption") or "").strip(),
            reading_depth=str(row.get("reading_depth") or "").strip(),
            evidence_excerpt=str(row.get("evidence_excerpt") or "").strip(),
            evidence_sentence_ids=list(row.get("evidence_sentence_ids") or []),
        )
    for row in l1_source_intake.get("regime_rows") or []:
        if not isinstance(row, dict):
            continue
        _append_anchor(
            _ensure_entry(str(row.get("source_id") or "").strip()),
            anchor_kind="regime",
            summary=str(row.get("regime") or "").strip(),
            reading_depth=str(row.get("reading_depth") or "").strip(),
            evidence_excerpt=str(row.get("evidence_excerpt") or "").strip(),
            evidence_sentence_ids=list(row.get("evidence_sentence_ids") or []),
        )
    for row in l1_source_intake.get("method_specificity_rows") or []:
        if not isinstance(row, dict):
            continue
        method_family = str(row.get("method_family") or "").strip()
        specificity_tier = str(row.get("specificity_tier") or "").strip()
        _append_anchor(
            _ensure_entry(str(row.get("source_id") or "").strip()),
            anchor_kind="method_specificity",
            summary=f"{method_family} / {specificity_tier}".strip(" /"),
            reading_depth=str(row.get("reading_depth") or "").strip(),
            evidence_excerpt=str(row.get("evidence_excerpt") or "").strip(),
            evidence_sentence_ids=list(row.get("evidence_sentence_ids") or []),
        )
    for row in l1_source_intake.get("notation_rows") or []:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("symbol") or "").strip()
        meaning = str(row.get("meaning") or "").strip()
        _append_anchor(
            _ensure_entry(str(row.get("source_id") or "").strip()),
            anchor_kind="notation",
            summary=f"{symbol} => {meaning}".strip(" =>"),
            reading_depth=str(row.get("reading_depth") or "").strip(),
            evidence_excerpt=str(row.get("evidence_excerpt") or "").strip(),
            evidence_sentence_ids=list(row.get("evidence_sentence_ids") or []),
        )
    for row in l1_source_intake.get("contradiction_candidates") or []:
        if not isinstance(row, dict):
            continue
        detail = str(row.get("detail") or "").strip()
        comparison_basis = str(row.get("comparison_basis") or "").strip()
        _append_anchor(
            _ensure_entry(str(row.get("source_id") or "").strip()),
            anchor_kind="contradiction",
            summary=detail,
            reading_depth=str(row.get("reading_depth") or "").strip(),
            evidence_excerpt=str(row.get("source_evidence_excerpt") or "").strip(),
            evidence_sentence_ids=list(row.get("source_evidence_sentence_ids") or []),
            paired_source_id=str(row.get("against_source_id") or "").strip(),
            basis_summary=str(row.get("source_basis_summary") or "").strip(),
            comparison_basis=comparison_basis,
            direction="source",
        )
        _append_anchor(
            _ensure_entry(str(row.get("against_source_id") or "").strip()),
            anchor_kind="contradiction",
            summary=detail,
            reading_depth=str(row.get("against_reading_depth") or "").strip(),
            evidence_excerpt=str(row.get("against_evidence_excerpt") or "").strip(),
            evidence_sentence_ids=list(row.get("against_evidence_sentence_ids") or []),
            paired_source_id=str(row.get("source_id") or "").strip(),
            basis_summary=str(row.get("against_basis_summary") or "").strip(),
            comparison_basis=comparison_basis,
            direction="against",
        )

    ordered_sources = sorted(
        entries_by_source_id.values(),
        key=lambda row: (
            str(row.get("source_id") or "").strip().lower(),
            str(row.get("title") or "").strip().lower(),
        ),
    )
    anchor_row_count = 0
    for row in ordered_sources:
        row.pop("_anchor_seen_keys", None)
        row["anchors"] = sorted(
            row.get("anchors") or [],
            key=lambda anchor: (
                str(anchor.get("anchor_kind") or "").strip().lower(),
                str(anchor.get("summary") or "").strip().lower(),
                str(anchor.get("paired_source_id") or "").strip().lower(),
            ),
        )
        row["anchor_count"] = len(row["anchors"])
        anchor_row_count += row["anchor_count"]

    return {
        "kind": "l1_source_anchor_index",
        "index_version": 1,
        "topic_slug": topic_slug,
        "source_count": len(ordered_sources),
        "anchor_row_count": anchor_row_count,
        "sources": ordered_sources,
        "updated_at": updated_at,
        "updated_by": updated_by,
    }


def render_l1_source_bridge_markdown(
    payload: dict[str, Any],
    *,
    topic_slug: str,
    source_anchor_index_path: str,
    updated_at: str,
    updated_by: str,
) -> str:
    lines = [
        _frontmatter(
            page_type="source_bridge",
            topic_slug=topic_slug,
            authority_level="non_authoritative_compiled_l1",
            updated_at=updated_at,
            updated_by=updated_by,
        ),
        "# [[home|Home]] / Source Anchor Bridge",
        "",
        "Sparse L1 understanding should remain thin, but every usable anchor should point back to the exact L0 source surface needed for later verification or route selection.",
        "",
        f"- Source count: `{payload.get('source_count') or 0}`",
        f"- Anchor rows: `{payload.get('anchor_row_count') or 0}`",
        f"- Machine index: `{source_anchor_index_path}`",
        "",
    ]

    sources = payload.get("sources") or []
    if not sources:
        lines.extend(["## Sources", "", "- (none)"])
        return "\n".join(lines).rstrip() + "\n"

    for row in sources:
        l0_refs = row.get("l0_refs") or {}
        lines.extend(
            [
                f"## `{row.get('source_id') or '(missing)'}`",
                "",
                f"- Title: {row.get('title') or '(missing)'}",
                f"- Type: `{row.get('source_type') or '(missing)'}`",
                f"- Relevance tier: `{row.get('relevance_tier') or 'unclassified'}`",
                f"- Role labels: `{', '.join(row.get('role_labels') or []) or '(none)'}`",
                "",
                "### L0 refs",
                "",
                f"- source_index.jsonl: `{l0_refs.get('source_index_path') or '(missing)'}`",
                f"- source.json: `{l0_refs.get('source_json_path') or '(missing)'}` status=`{l0_refs.get('source_json_status') or 'missing'}`",
                f"- snapshot.md: `{l0_refs.get('snapshot_path') or '(missing)'}` status=`{l0_refs.get('snapshot_status') or 'missing'}`",
            ]
        )
        if l0_refs.get("absolute_path"):
            lines.append(f"- absolute_path: `{l0_refs.get('absolute_path')}`")
        if l0_refs.get("abs_url"):
            lines.append(f"- abs_url: `{l0_refs.get('abs_url')}`")
        lines.extend(["", "### L1 anchors", ""])
        anchors = row.get("anchors") or []
        if not anchors:
            lines.append("- (none)")
            lines.append("")
            continue
        for anchor in anchors:
            anchor_line = (
                f"- `{anchor.get('anchor_kind') or 'anchor'}`"
                f" [{anchor.get('reading_depth') or 'n/a'}]: {anchor.get('summary') or '(missing)'}"
            )
            if anchor.get("paired_source_id"):
                anchor_line += f" vs `{anchor.get('paired_source_id')}`"
            lines.append(anchor_line)
            if anchor.get("basis_summary"):
                lines.append(f"  basis: {anchor.get('basis_summary')}")
            if anchor.get("evidence_excerpt"):
                lines.append(f"  evidence: {anchor.get('evidence_excerpt')}")
            if anchor.get("evidence_sentence_ids"):
                lines.append(
                    "  sentence ids=`"
                    + ", ".join(anchor.get("evidence_sentence_ids") or [])
                    + "`"
                )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
