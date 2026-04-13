from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .source_intelligence import (
    build_source_intelligence,
    detect_contradiction_candidates,
    detect_notation_candidates,
    detect_notation_tension_candidates,
    derive_canonical_source_id,
    extract_neighbor_terms,
    extract_reference_ids,
)


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


def _empty_l1_concept_graph() -> dict[str, Any]:
    return {
        "nodes": [],
        "edges": [],
        "hyperedges": [],
        "communities": [],
        "god_nodes": [],
    }


def empty_l1_source_intake() -> dict[str, Any]:
    return {
        "source_count": 0,
        "assumption_rows": [],
        "regime_rows": [],
        "reading_depth_rows": [],
        "method_specificity_rows": [],
        "notation_rows": [],
        "contradiction_candidates": [],
        "notation_tension_candidates": [],
        "concept_graph": _empty_l1_concept_graph(),
    }


def source_intelligence_paths(runtime_root: Path) -> dict[str, Path]:
    return {
        "json": runtime_root / "source_intelligence.json",
        "note": runtime_root / "source_intelligence.md",
    }


def render_source_intelligence_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Source intelligence",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Summary: {payload.get('summary') or '(missing)'}",
        f"- Canonical source ids: `{', '.join(payload.get('canonical_source_ids') or []) or '(none)'}`",
        f"- Citation edge count: `{len(payload.get('citation_edges') or [])}`",
        f"- Neighbor signal count: `{payload.get('neighbor_signal_count') or 0}`",
        f"- Cross-topic match count: `{payload.get('cross_topic_match_count') or 0}`",
        "",
        "## Source fidelity",
        "",
        f"- Strongest tier: `{((payload.get('fidelity_summary') or {}).get('strongest_tier') or 'unknown')}`",
        f"- Weakest tier: `{((payload.get('fidelity_summary') or {}).get('weakest_tier') or 'unknown')}`",
        f"- Counts by tier: `{', '.join(f'{key}={value}' for key, value in ((payload.get('fidelity_summary') or {}).get('counts_by_tier') or {}).items()) or '(none)'}`",
        "",
        "## Citation edges",
        "",
    ]
    for row in payload.get("citation_edges") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` -> `{row.get('target_ref') or '(missing)'}` "
                f"({row.get('relation') or 'cites'})"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Source neighbors", ""])
    for row in payload.get("source_neighbors") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` ~ `{row.get('neighbor_source_id') or '(missing)'}` "
                f"via `{row.get('relation_kind') or '(missing)'}`"
            )
        else:
            lines.append(f"- {row}")
    return "\n".join(lines) + "\n"


def _normalize_l1_intake_rows(rows: Any, *, required_field: str) -> list[dict[str, str]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or "").strip()
        payload_value = str(row.get(required_field) or "").strip()
        if not source_id or not payload_value:
            continue
        key = (source_id.lower(), payload_value.lower())
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "source_id": source_id,
                "source_title": str(row.get("source_title") or "").strip(),
                "source_type": str(row.get("source_type") or "").strip(),
                required_field: payload_value,
                "reading_depth": str(row.get("reading_depth") or "").strip() or "skim",
                "evidence_excerpt": str(row.get("evidence_excerpt") or "").strip(),
            }
        )
    return normalized


def _normalize_reading_depth_rows(rows: Any) -> list[dict[str, str]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or "").strip()
        reading_depth = str(row.get("reading_depth") or "").strip()
        basis = str(row.get("basis") or "").strip()
        if not source_id or not reading_depth:
            continue
        key = (source_id.lower(), reading_depth.lower(), basis.lower())
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "source_id": source_id,
                "source_title": str(row.get("source_title") or "").strip(),
                "source_type": str(row.get("source_type") or "").strip(),
                "reading_depth": reading_depth,
                "basis": basis or "summary_only",
            }
        )
    return normalized


def _normalize_method_specificity_rows(rows: Any) -> list[dict[str, str]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or "").strip()
        method_family = str(row.get("method_family") or "").strip()
        specificity_tier = str(row.get("specificity_tier") or "").strip()
        if not source_id or not method_family or not specificity_tier:
            continue
        key = (source_id.lower(), method_family.lower(), specificity_tier.lower())
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "source_id": source_id,
                "source_title": str(row.get("source_title") or "").strip(),
                "source_type": str(row.get("source_type") or "").strip(),
                "method_family": method_family,
                "specificity_tier": specificity_tier,
                "reading_depth": str(row.get("reading_depth") or "").strip() or "skim",
                "evidence_excerpt": str(row.get("evidence_excerpt") or "").strip(),
            }
        )
    return normalized


def _normalize_notation_rows(rows: Any) -> list[dict[str, str]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or "").strip()
        symbol = str(row.get("symbol") or "").strip()
        meaning = str(row.get("meaning") or "").strip()
        if not source_id or not symbol or not meaning:
            continue
        key = (source_id.lower(), symbol.lower(), meaning.lower())
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "source_id": source_id,
                "source_title": str(row.get("source_title") or "").strip(),
                "source_type": str(row.get("source_type") or "").strip(),
                "symbol": symbol,
                "meaning": meaning,
                "reading_depth": str(row.get("reading_depth") or "").strip() or "skim",
                "evidence_excerpt": str(row.get("evidence_excerpt") or "").strip(),
            }
        )
    return normalized


def _normalize_contradiction_candidates(rows: Any) -> list[dict[str, str]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or "").strip()
        against_source_id = str(row.get("against_source_id") or "").strip()
        detail = str(row.get("detail") or "").strip()
        if not source_id or not against_source_id or not detail:
            continue
        comparison_basis = str(row.get("comparison_basis") or "").strip() or "assumption_rows"
        source_basis_type = str(row.get("source_basis_type") or "").strip() or "assumption"
        source_basis_summary = str(row.get("source_basis_summary") or "").strip() or detail
        against_basis_type = str(row.get("against_basis_type") or "").strip() or "assumption"
        against_basis_summary = str(row.get("against_basis_summary") or "").strip() or detail
        if comparison_basis == "regime_rows":
            source_basis_type = "regime"
            against_basis_type = "regime"
        elif comparison_basis == "assumption_rows":
            source_basis_type = "assumption"
            against_basis_type = "assumption"
        key = (
            source_id.lower(),
            against_source_id.lower(),
            detail.lower(),
            source_basis_summary.lower(),
            against_basis_summary.lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "kind": str(row.get("kind") or "").strip() or "assumption_conflict",
                "source_id": source_id,
                "source_title": str(row.get("source_title") or "").strip(),
                "source_type": str(row.get("source_type") or "").strip(),
                "reading_depth": str(row.get("reading_depth") or "").strip() or "skim",
                "against_source_id": against_source_id,
                "against_source_title": str(row.get("against_source_title") or "").strip(),
                "against_source_type": str(row.get("against_source_type") or "").strip(),
                "against_reading_depth": str(row.get("against_reading_depth") or "").strip() or "skim",
                "detail": detail,
                "comparison_basis": comparison_basis,
                "source_basis_type": source_basis_type,
                "source_basis_summary": source_basis_summary,
                "source_evidence_excerpt": str(row.get("source_evidence_excerpt") or "").strip() or source_basis_summary,
                "against_basis_type": against_basis_type,
                "against_basis_summary": against_basis_summary,
                "against_evidence_excerpt": str(row.get("against_evidence_excerpt") or "").strip()
                or against_basis_summary,
            }
        )
    return normalized


def _normalize_notation_tension_candidates(rows: Any) -> list[dict[str, str]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or "").strip()
        against_source_id = str(row.get("against_source_id") or "").strip()
        meaning = str(row.get("meaning") or "").strip()
        incoming_symbol = str(row.get("incoming_symbol") or "").strip()
        existing_symbol = str(row.get("existing_symbol") or "").strip()
        if not source_id or not against_source_id or not meaning or not incoming_symbol or not existing_symbol:
            continue
        key = (source_id.lower(), against_source_id.lower(), meaning.lower(), incoming_symbol.lower())
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "source_id": source_id,
                "source_title": str(row.get("source_title") or "").strip(),
                "source_type": str(row.get("source_type") or "").strip(),
                "reading_depth": str(row.get("reading_depth") or "").strip() or "skim",
                "against_source_id": against_source_id,
                "against_source_title": str(row.get("against_source_title") or "").strip(),
                "against_source_type": str(row.get("against_source_type") or "").strip(),
                "against_reading_depth": str(row.get("against_reading_depth") or "").strip() or "skim",
                "meaning": meaning,
                "existing_symbol": existing_symbol,
                "incoming_symbol": incoming_symbol,
            }
        )
    return normalized


def _normalize_concept_graph_nodes(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or "").strip()
        node_id = str(row.get("node_id") or "").strip()
        label = str(row.get("label") or "").strip()
        node_type = str(row.get("node_type") or "").strip()
        if not source_id or not node_id or not label or not node_type:
            continue
        key = (source_id.lower(), node_id.lower())
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "source_id": source_id,
                "source_title": str(row.get("source_title") or "").strip(),
                "source_type": str(row.get("source_type") or "").strip(),
                "node_id": node_id,
                "label": label,
                "node_type": node_type,
                "confidence_tier": str(row.get("confidence_tier") or "EXTRACTED").strip(),
                "confidence_score": float(row.get("confidence_score") or 0.0),
            }
        )
    return normalized


def _normalize_concept_graph_edges(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or "").strip()
        edge_id = str(row.get("edge_id") or "").strip()
        relation = str(row.get("relation") or "").strip()
        from_id = str(row.get("from_id") or "").strip()
        to_id = str(row.get("to_id") or "").strip()
        if not source_id or not edge_id or not relation or not from_id or not to_id:
            continue
        key = (source_id.lower(), edge_id.lower())
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "source_id": source_id,
                "edge_id": edge_id,
                "from_id": from_id,
                "relation": relation,
                "to_id": to_id,
            }
        )
    return normalized


def _normalize_concept_graph_hyperedges(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or "").strip()
        hyperedge_id = str(row.get("hyperedge_id") or "").strip()
        relation = str(row.get("relation") or "").strip()
        node_ids = _dedupe_strings([str(item).strip() for item in (row.get("node_ids") or []) if str(item).strip()])
        if not source_id or not hyperedge_id or not relation or len(node_ids) < 2:
            continue
        key = (source_id.lower(), hyperedge_id.lower())
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "source_id": source_id,
                "hyperedge_id": hyperedge_id,
                "relation": relation,
                "node_ids": node_ids,
            }
        )
    return normalized


def _normalize_concept_graph_communities(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or "").strip()
        community_id = str(row.get("community_id") or "").strip()
        label = str(row.get("label") or "").strip()
        node_ids = _dedupe_strings([str(item).strip() for item in (row.get("node_ids") or []) if str(item).strip()])
        if not source_id or not community_id or not label or not node_ids:
            continue
        key = (source_id.lower(), community_id.lower())
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "source_id": source_id,
                "community_id": community_id,
                "label": label,
                "node_ids": node_ids,
            }
        )
    return normalized


def _normalize_concept_graph_god_nodes(rows: Any) -> list[dict[str, str]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or "").strip()
        node_id = str(row.get("node_id") or "").strip()
        label = str(row.get("label") or "").strip()
        if not source_id or not node_id or not label:
            continue
        key = (source_id.lower(), node_id.lower())
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "source_id": source_id,
                "node_id": node_id,
                "label": label,
            }
        )
    return normalized


def _normalize_concept_graph(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return _empty_l1_concept_graph()
    return {
        "nodes": _normalize_concept_graph_nodes(payload.get("nodes")),
        "edges": _normalize_concept_graph_edges(payload.get("edges")),
        "hyperedges": _normalize_concept_graph_hyperedges(payload.get("hyperedges")),
        "communities": _normalize_concept_graph_communities(payload.get("communities")),
        "god_nodes": _normalize_concept_graph_god_nodes(payload.get("god_nodes")),
    }


def normalize_l1_source_intake(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return empty_l1_source_intake()
    normalized = {
        "source_count": int(payload.get("source_count") or 0),
        "assumption_rows": _normalize_l1_intake_rows(payload.get("assumption_rows"), required_field="assumption"),
        "regime_rows": _normalize_l1_intake_rows(payload.get("regime_rows"), required_field="regime"),
        "reading_depth_rows": _normalize_reading_depth_rows(payload.get("reading_depth_rows")),
        "method_specificity_rows": _normalize_method_specificity_rows(payload.get("method_specificity_rows")),
        "notation_rows": _normalize_notation_rows(payload.get("notation_rows")),
        "contradiction_candidates": _normalize_contradiction_candidates(payload.get("contradiction_candidates")),
        "notation_tension_candidates": _normalize_notation_tension_candidates(payload.get("notation_tension_candidates")),
        "concept_graph": _normalize_concept_graph(payload.get("concept_graph")),
    }
    if normalized["source_count"] <= 0:
        source_keys = {
            str(row.get("source_id") or "").strip()
            for row in normalized["reading_depth_rows"]
            if str(row.get("source_id") or "").strip()
        }
        normalized["source_count"] = len(source_keys)
    return normalized


def _has_l1_source_intake_content(payload: dict[str, Any]) -> bool:
    return any(
        payload[key]
        for key in (
            "assumption_rows",
            "regime_rows",
            "reading_depth_rows",
            "method_specificity_rows",
            "notation_rows",
            "contradiction_candidates",
            "notation_tension_candidates",
        )
    ) or any(
        len((payload.get("concept_graph") or {}).get(key) or [])
        for key in ("nodes", "edges", "hyperedges", "communities", "god_nodes")
    )


def coalesce_l1_source_intake(existing: Any, default: dict[str, Any]) -> dict[str, Any]:
    normalized_existing = normalize_l1_source_intake(existing)
    normalized_default = normalize_l1_source_intake(default)
    if _has_l1_source_intake_content(normalized_default):
        return normalized_default
    if _has_l1_source_intake_content(normalized_existing):
        return normalized_existing
    return normalized_default


def _summary_excerpt(row: dict[str, Any]) -> str:
    summary = str(row.get("summary") or row.get("summary_text") or "").strip()
    if not summary:
        summary = str(row.get("source_title") or "").strip()
    return re.sub(r"\s+", " ", summary)[:220]


def derive_l1_conflict_intake(source_rows: list[dict[str, Any]], l1_source_intake: dict[str, Any]) -> dict[str, Any]:
    reading_depth_by_source = {
        str(row.get("source_id") or "").strip(): str(row.get("reading_depth") or "").strip() or "skim"
        for row in l1_source_intake.get("reading_depth_rows") or []
        if str(row.get("source_id") or "").strip()
    }
    assumptions_by_source: dict[str, list[str]] = {}
    for row in l1_source_intake.get("assumption_rows") or []:
        source_id = str(row.get("source_id") or "").strip()
        if source_id:
            assumptions_by_source.setdefault(source_id, []).append(str(row.get("assumption") or "").strip())
    regimes_by_source: dict[str, list[str]] = {}
    for row in l1_source_intake.get("regime_rows") or []:
        source_id = str(row.get("source_id") or "").strip()
        if source_id:
            regimes_by_source.setdefault(source_id, []).append(str(row.get("regime") or "").strip())

    notation_rows: list[dict[str, str]] = []
    contradiction_candidates_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    notation_tension_candidates: list[dict[str, str]] = []
    processed_rows: list[dict[str, Any]] = []
    processed_by_source: dict[str, dict[str, Any]] = {}

    for row in source_rows:
        source_id = str(row.get("source_id") or "").strip()
        source_title = str(row.get("title") or "").strip()
        source_type = str(row.get("source_type") or "").strip()
        if not source_id:
            continue
        reading_depth = reading_depth_by_source.get(source_id, "skim")
        text = " ".join(part for part in (str(row.get("summary") or "").strip(), source_title) if part).strip()
        notation_candidates = detect_notation_candidates(text=text)
        excerpt = _summary_excerpt(row)
        for candidate in notation_candidates:
            notation_rows.append(
                {
                    "source_id": source_id,
                    "source_title": source_title,
                    "source_type": source_type,
                    "symbol": str(candidate.get("symbol") or "").strip(),
                    "meaning": str(candidate.get("meaning") or "").strip(),
                    "reading_depth": reading_depth,
                    "evidence_excerpt": excerpt,
                }
            )

        for candidate in detect_contradiction_candidates(
            existing_rows=processed_rows,
            assumptions=assumptions_by_source.get(source_id, []),
            regimes=regimes_by_source.get(source_id, []),
        ):
            against_source_id = str(candidate.get("against_source_id") or "").strip()
            against_row = processed_by_source.get(against_source_id, {})
            contradiction_row = {
                "kind": str(candidate.get("kind") or "").strip() or "assumption_conflict",
                "source_id": source_id,
                "source_title": source_title,
                "source_type": source_type,
                "reading_depth": reading_depth,
                "against_source_id": against_source_id,
                "against_source_title": str(against_row.get("source_title") or "").strip(),
                "against_source_type": str(against_row.get("source_type") or "").strip(),
                "against_reading_depth": str(against_row.get("reading_depth") or "").strip() or "skim",
                "detail": str(candidate.get("detail") or "").strip(),
                "comparison_basis": str(candidate.get("comparison_basis") or "").strip() or "assumption_rows",
                "source_basis_type": str(candidate.get("source_basis_type") or "").strip() or "assumption",
                "source_basis_summary": str(candidate.get("source_basis_summary") or "").strip(),
                "source_evidence_excerpt": excerpt,
                "against_basis_type": str(candidate.get("against_basis_type") or "").strip() or "assumption",
                "against_basis_summary": str(candidate.get("against_basis_summary") or "").strip(),
                "against_evidence_excerpt": _summary_excerpt(against_row),
            }
            contradiction_key = (
                source_id,
                against_source_id,
                str(contradiction_row.get("detail") or "").strip(),
            )
            existing_row = contradiction_candidates_by_key.get(contradiction_key)
            if existing_row is None or (
                contradiction_row["comparison_basis"] == "regime_rows"
                and existing_row.get("comparison_basis") != "regime_rows"
            ):
                contradiction_candidates_by_key[contradiction_key] = contradiction_row

        for tension in detect_notation_tension_candidates(
            existing_rows=processed_rows,
            notation_candidates=notation_candidates,
        ):
            against_source_id = str(tension.get("against_source_id") or "").strip()
            against_row = processed_by_source.get(against_source_id, {})
            notation_tension_candidates.append(
                {
                    "source_id": source_id,
                    "source_title": source_title,
                    "source_type": source_type,
                    "reading_depth": reading_depth,
                    "against_source_id": against_source_id,
                    "against_source_title": str(against_row.get("source_title") or "").strip(),
                    "against_source_type": str(against_row.get("source_type") or "").strip(),
                    "against_reading_depth": str(against_row.get("reading_depth") or "").strip() or "skim",
                    "meaning": str(tension.get("meaning") or "").strip(),
                    "existing_symbol": str(tension.get("existing_symbol") or "").strip(),
                    "incoming_symbol": str(tension.get("incoming_symbol") or "").strip(),
                }
            )

        processed_row = {
            "source_id": source_id,
            "source_title": source_title,
            "source_type": source_type,
            "summary_text": str(row.get("summary") or "").strip(),
            "reading_depth": reading_depth,
            "assumptions": assumptions_by_source.get(source_id, []),
            "regimes": regimes_by_source.get(source_id, []),
            "notation_candidates": notation_candidates,
        }
        processed_rows.append(processed_row)
        processed_by_source[source_id] = processed_row

    return {
        "notation_rows": _normalize_notation_rows(notation_rows),
        "contradiction_candidates": _normalize_contradiction_candidates(
            list(contradiction_candidates_by_key.values())
        ),
        "notation_tension_candidates": _normalize_notation_tension_candidates(notation_tension_candidates),
    }


def _enrich_source_row_for_intelligence(row: dict[str, Any], *, topic_slug: str) -> dict[str, Any]:
    provenance = row.get("provenance") or {}
    locator = row.get("locator") or {}
    if not isinstance(provenance, dict):
        provenance = {}
    if not isinstance(locator, dict):
        locator = {}
    title = str(row.get("title") or "").strip()
    summary = str(row.get("summary") or "").strip()
    source_type = str(row.get("source_type") or "").strip()
    return {
        **row,
        "topic_slug": str(row.get("topic_slug") or "").strip() or topic_slug,
        "canonical_source_id": str(row.get("canonical_source_id") or "").strip()
        or derive_canonical_source_id(
            source_type=source_type,
            title=title,
            summary=summary,
            provenance=provenance,
            locator=locator,
        ),
        "references": _dedupe_strings(list(row.get("references") or []))
        or extract_reference_ids(text=f"{title} {summary}", provenance=provenance),
        "neighbor_terms": extract_neighbor_terms(title=title, summary=summary),
    }


def source_intelligence_payload(*, kernel_root: Path, topic_slug: str, source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    local_rows = [_enrich_source_row_for_intelligence(row, topic_slug=topic_slug) for row in source_rows]
    topics_root = kernel_root / "source-layer" / "topics"
    global_rows: list[dict[str, Any]] = []
    for source_index_path in sorted(topics_root.glob("*/source_index.jsonl")):
        indexed_topic_slug = source_index_path.parent.name
        for row in _read_jsonl(source_index_path):
            global_rows.append(_enrich_source_row_for_intelligence(row, topic_slug=indexed_topic_slug))
    intelligence = build_source_intelligence(
        topic_slug=topic_slug,
        source_rows=local_rows,
        global_rows=global_rows,
    )
    citation_edge_count = len(intelligence.get("citation_edges") or [])
    neighbor_signal_count = int(intelligence.get("neighbor_signal_count") or 0)
    cross_topic_match_count = int(intelligence.get("cross_topic_match_count") or 0)
    return {
        "topic_slug": topic_slug,
        "summary": (
            f"{len(intelligence.get('canonical_source_ids') or [])} canonical source ids, "
            f"{citation_edge_count} citation edges, "
            f"{neighbor_signal_count} neighbor signals, "
            f"{cross_topic_match_count} cross-topic matches. "
            f"Strongest fidelity={((intelligence.get('fidelity_summary') or {}).get('strongest_tier') or 'unknown')}."
        ),
        **intelligence,
    }


def l1_context_lines(l1_source_intake: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if l1_source_intake.get("assumption_rows"):
        assumptions = _dedupe_strings(
            [
                str(row.get("assumption") or "").strip()
                for row in l1_source_intake.get("assumption_rows") or []
                if str(row.get("assumption") or "").strip()
            ]
        )
        if assumptions:
            lines.append(f"Source-backed assumptions: {'; '.join(assumptions[:3])}")
    if l1_source_intake.get("regime_rows"):
        regimes = [str(row.get("regime") or "").strip() for row in l1_source_intake["regime_rows"]]
        regimes = [item for item in regimes if item]
        if regimes:
            lines.append(f"Source-backed regimes: {', '.join(regimes[:4])}")
    if l1_source_intake.get("reading_depth_rows"):
        depth_summary = []
        for row in l1_source_intake["reading_depth_rows"][:4]:
            source_id = str(row.get("source_id") or "").strip()
            reading_depth = str(row.get("reading_depth") or "").strip()
            if source_id and reading_depth:
                depth_summary.append(f"{source_id}={reading_depth}")
        if depth_summary:
            lines.append(f"Recorded reading depth: {', '.join(depth_summary)}")
    if l1_source_intake.get("method_specificity_rows"):
        labels = []
        for row in l1_source_intake["method_specificity_rows"][:4]:
            source_id = str(row.get("source_id") or "").strip()
            method_family = str(row.get("method_family") or "").strip()
            specificity_tier = str(row.get("specificity_tier") or "").strip()
            if source_id and method_family and specificity_tier:
                labels.append(f"{source_id}={method_family}/{specificity_tier}")
        if labels:
            lines.append(f"Source-backed method specificity: {', '.join(labels)}")
    concept_graph = l1_source_intake.get("concept_graph") or {}
    node_count = len(concept_graph.get("nodes") or [])
    edge_count = len(concept_graph.get("edges") or [])
    if node_count or edge_count:
        lines.append(f"Source concept graph: nodes={node_count} edges={edge_count}")
    god_nodes = [str(row.get("label") or "").strip() for row in (concept_graph.get("god_nodes") or []) if str(row.get("label") or "").strip()]
    if god_nodes:
        lines.append(f"Graph foundations: {', '.join(god_nodes[:4])}")
    return lines


def l1_assumption_depth_summary_lines(l1_source_intake: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    source_count = int(l1_source_intake.get("source_count") or 0)
    assumption_count = len(l1_source_intake.get("assumption_rows") or [])
    regime_count = len(l1_source_intake.get("regime_rows") or [])
    depth_count = len(l1_source_intake.get("reading_depth_rows") or [])
    if any((source_count, assumption_count, regime_count, depth_count)):
        lines.append(
            f"Sources=`{source_count}` assumptions=`{assumption_count}` regimes=`{regime_count}` reading-depth rows=`{depth_count}`"
        )
    contradiction_count = len(l1_source_intake.get("contradiction_candidates") or [])
    if contradiction_count:
        lines.append(f"Open contradiction candidates=`{contradiction_count}`")
    notation_tension_count = len(l1_source_intake.get("notation_tension_candidates") or [])
    if notation_tension_count:
        lines.append(f"Open notation-tension candidates=`{notation_tension_count}`")
    concept_graph = l1_source_intake.get("concept_graph") or {}
    if any(len(concept_graph.get(key) or []) for key in ("nodes", "edges", "communities", "god_nodes")):
        lines.append(
            "Concept-graph rows="
            f"`{len(concept_graph.get('nodes') or [])}` nodes / "
            f"`{len(concept_graph.get('edges') or [])}` edges / "
            f"`{len(concept_graph.get('communities') or [])}` communities / "
            f"`{len(concept_graph.get('god_nodes') or [])}` god-nodes"
        )
    return lines


def l1_concept_graph_summary_lines(l1_source_intake: dict[str, Any]) -> list[str]:
    concept_graph = l1_source_intake.get("concept_graph") or {}
    lines: list[str] = []
    node_count = len(concept_graph.get("nodes") or [])
    edge_count = len(concept_graph.get("edges") or [])
    hyperedge_count = len(concept_graph.get("hyperedges") or [])
    community_count = len(concept_graph.get("communities") or [])
    god_nodes = concept_graph.get("god_nodes") or []
    if any((node_count, edge_count, hyperedge_count, community_count, len(god_nodes))):
        lines.append(
            f"nodes=`{node_count}` edges=`{edge_count}` hyperedges=`{hyperedge_count}` communities=`{community_count}` god-nodes=`{len(god_nodes)}`"
        )
    for row in god_nodes[:4]:
        label = str(row.get("label") or "").strip()
        node_id = str(row.get("node_id") or "").strip()
        source_id = str(row.get("source_id") or "").strip()
        if label and node_id:
            lines.append(f"`{source_id or '(unknown source)'}` foundation `{label}` ({node_id})")
    return lines


def l1_reading_depth_limit_lines(l1_source_intake: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    partial_depth_rows = [
        row
        for row in l1_source_intake.get("reading_depth_rows") or []
        if str(row.get("reading_depth") or "").strip() != "full_read"
    ]
    for row in partial_depth_rows[:4]:
        source_id = str(row.get("source_id") or "").strip()
        reading_depth = str(row.get("reading_depth") or "").strip()
        basis = str(row.get("basis") or "").strip() or "summary_only"
        if source_id and reading_depth:
            lines.append(f"`{source_id}` remains `{reading_depth}` (basis=`{basis}`)")
    return lines


def l1_contradiction_summary_lines(l1_source_intake: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for row in l1_source_intake.get("contradiction_candidates") or []:
        detail = str(row.get("detail") or "").strip()
        source_id = str(row.get("source_id") or "").strip()
        against_source_id = str(row.get("against_source_id") or "").strip()
        reading_depth = str(row.get("reading_depth") or "").strip() or "skim"
        against_reading_depth = str(row.get("against_reading_depth") or "").strip() or "skim"
        comparison_basis = str(row.get("comparison_basis") or "").strip() or "assumption_rows"
        source_basis_summary = str(row.get("source_basis_summary") or "").strip()
        against_basis_summary = str(row.get("against_basis_summary") or "").strip()
        if detail and source_id and against_source_id:
            line = (
                f"{detail} (`{source_id}`[{reading_depth}] vs `{against_source_id}`[{against_reading_depth}]) "
                f"basis=`{comparison_basis}`"
            )
            if source_basis_summary or against_basis_summary:
                line += (
                    f"; current=`{source_basis_summary or '(missing)'}`"
                    f"; compared=`{against_basis_summary or '(missing)'}`"
                )
            lines.append(line)
    return lines


def l1_notation_tension_lines(l1_source_intake: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for row in l1_source_intake.get("notation_tension_candidates") or []:
        meaning = str(row.get("meaning") or "").strip()
        existing_symbol = str(row.get("existing_symbol") or "").strip()
        incoming_symbol = str(row.get("incoming_symbol") or "").strip()
        source_id = str(row.get("source_id") or "").strip()
        against_source_id = str(row.get("against_source_id") or "").strip()
        if meaning and existing_symbol and incoming_symbol and source_id and against_source_id:
            lines.append(
                f"`{existing_symbol}` vs `{incoming_symbol}` for `{meaning}` (`{source_id}` vs `{against_source_id}`)"
            )
    return lines


def l1_interpretation_focus_lines(l1_source_intake: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    regimes = [str(row.get("regime") or "").strip() for row in l1_source_intake.get("regime_rows") or []]
    regimes = [item for item in regimes if item]
    if regimes:
        lines.append(f"Keep interpretation bounded to the recorded source regimes: {', '.join(regimes[:4])}.")
    if any(str(row.get("reading_depth") or "").strip() != "full_read" for row in l1_source_intake.get("reading_depth_rows") or []):
        lines.append("Do not over-interpret claims that are currently backed only by abstract-only or skim-level reading depth.")
    return lines


def l1_open_ambiguity_lines(l1_source_intake: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    reading_depth_limits = l1_reading_depth_limit_lines(l1_source_intake)
    if reading_depth_limits:
        lines.append(f"Reading-depth limits still apply for: {', '.join(reading_depth_limits)}")
    low_specificity_rows = [
        row
        for row in l1_source_intake.get("method_specificity_rows") or []
        if str(row.get("specificity_tier") or "").strip() == "low"
    ]
    if low_specificity_rows:
        labels = [
            f"{row['source_id']}={row['method_family']}/{row['specificity_tier']}"
            for row in low_specificity_rows[:4]
            if str(row.get("source_id") or "").strip() and str(row.get("method_family") or "").strip()
        ]
        if labels:
            lines.append(f"Method-specificity limits still apply for: {', '.join(labels)}")
    for item in l1_contradiction_summary_lines(l1_source_intake):
        lines.append(f"Contradiction candidate: {item}")
    for item in l1_notation_tension_lines(l1_source_intake):
        lines.append(f"Notation tension: {item}")
    return lines


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows
