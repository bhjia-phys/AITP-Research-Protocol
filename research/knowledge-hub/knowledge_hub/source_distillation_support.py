from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Any

from .l1_source_intake_support import evidence_sentence_ids_for_text
from .source_intelligence import detect_assumptions, detect_regimes, infer_method_specificity, infer_reading_depth_label

_FORMAL_SOURCE_TYPES = {"paper", "thesis", "article", "local_note", "book", "lecture", "derivation"}
_NUMERICAL_SOURCE_TYPES = {"benchmark", "code", "implementation", "numerical", "experiment"}
_TITLE_NOVELTY_KEYWORDS = ("novel", "new", "first", "closure", "variational", "derivation")
_SUMMARY_NOVELTY_KEYWORDS = (
    "novel",
    "new contribution",
    "we show",
    "we prove",
    "we derive",
    "closure",
    "variational",
)
_PROGRESSIVE_RUNTIME_MODES = {"discussion", "explore", "verify", "promote"}
_DEEPXIV_HEAD_SECTION_LIMIT = 3
_DEEPXIV_VERIFY_RELEVANT_SECTION_LIMIT = 3
_DEEPXIV_RELEVANT_SECTION_KEYWORDS = (
    "assumption",
    "conclusion",
    "definition",
    "derivation",
    "discussion",
    "equation",
    "method",
    "model",
    "notation",
    "proof",
    "regime",
    "result",
    "setup",
    "theorem",
)


def _empty_l1_source_intake() -> dict[str, Any]:
    return {
        "source_count": 0,
        "assumption_rows": [],
        "regime_rows": [],
        "reading_depth_rows": [],
        "method_specificity_rows": [],
        "concept_graph": {
            "nodes": [],
            "edges": [],
            "hyperedges": [],
            "communities": [],
            "god_nodes": [],
        },
    }


def _empty_distillation() -> dict[str, Any]:
    return {
        "distilled_initial_idea": "",
        "distilled_novelty_target": "",
        "distilled_first_validation_route": "",
        "distilled_lane": "",
        "distilled_l1_source_intake": _empty_l1_source_intake(),
    }


def _strip_comment_lines(text: str) -> str:
    lines = [line for line in text.splitlines() if not line.strip().startswith("%")]
    return "\n".join(lines).strip()


def _snapshot_path(*, kernel_root: Path, topic_slug: str, source_id: str) -> Path:
    return (
        kernel_root
        / "source-layer"
        / "topics"
        / topic_slug
        / "sources"
        / source_id.replace(":", "-")
        / "snapshot.md"
    )


def _load_snapshot_text(*, kernel_root: Path, topic_slug: str, source_id: str) -> str:
    snapshot_path = _snapshot_path(kernel_root=kernel_root, topic_slug=topic_slug, source_id=source_id)
    if not snapshot_path.exists():
        return ""
    return snapshot_path.read_text(encoding="utf-8")


def _extract_preview_from_snapshot(snapshot_text: str) -> str:
    if not snapshot_text:
        return ""
    preview_match = re.search(
        r"## Preview\s*\n(.*?)(?=\n##|\Z)",
        snapshot_text,
        re.DOTALL,
    )
    if not preview_match:
        return ""
    return _strip_comment_lines(preview_match.group(1).strip())


def _extract_preview_from_original_file(absolute_path: str) -> str:
    if not absolute_path:
        return ""
    original_path = Path(absolute_path)
    if not original_path.exists() or original_path.suffix.lower() not in {".tex", ".md", ".txt"}:
        return ""
    try:
        original_text = original_path.read_text(encoding="utf-8")
    except Exception:
        return ""

    if original_path.suffix.lower() != ".tex":
        return original_text[:500].strip()

    section_match = re.search(
        r"\\(?:section|chapter|subsection)\*?\{[^}]+\}[^}]*",
        original_text,
        re.IGNORECASE | re.DOTALL,
    )
    if section_match:
        start_pos = section_match.start()
        return original_text[start_pos:start_pos + 500].strip()

    content_lines = [line for line in original_text.splitlines() if not line.strip().startswith("%")]
    return "\n".join(content_lines[:30])[:500].strip()


def _resolve_preview_content(*, snapshot_text: str, summary: str, absolute_path: str) -> str:
    preview_content = _extract_preview_from_snapshot(snapshot_text)
    if not preview_content:
        preview_content = _extract_preview_from_original_file(absolute_path)
    if not preview_content and summary:
        preview_content = _strip_comment_lines(summary)[:300].strip()
    return preview_content


def _normalize_excerpt(text: str, *, max_chars: int = 220) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized[:max_chars]


def _excerpt_for_signal(*, text: str, needle: str) -> str:
    normalized = _normalize_excerpt(text, max_chars=400)
    if not normalized:
        return ""
    lowered = normalized.lower()
    lowered_needle = str(needle or "").strip().lower()
    if not lowered_needle:
        return normalized[:220]
    match_index = lowered.find(lowered_needle)
    if match_index < 0:
        return normalized[:220]
    start = max(0, match_index - 60)
    end = min(len(normalized), match_index + len(lowered_needle) + 100)
    return normalized[start:end].strip()


def _dedupe_rows(rows: list[dict[str, Any]], *, key_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for row in rows:
        key = tuple(str(row.get(field) or "").strip().lower() for field in key_fields)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _normalize_runtime_mode(runtime_mode: str | None) -> str:
    normalized = str(runtime_mode or "").strip().lower()
    if normalized in _PROGRESSIVE_RUNTIME_MODES:
        return normalized
    return "discussion"


def _dedupe_text_parts(parts: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for part in parts:
        normalized = re.sub(r"\s+", " ", str(part or "")).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)
    return deduped


def _normalize_deepxiv_sections(provenance: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, value in enumerate(provenance.get("deepxiv_sections") or []):
        if not isinstance(value, dict):
            continue
        name = str(value.get("name") or value.get("section") or "").strip()
        tldr = str(value.get("tldr") or "").strip()
        if not name or not tldr:
            continue
        rows.append(
            {
                "name": name,
                "idx": int(value.get("idx", idx)),
                "tldr": tldr,
                "token_count": int(value.get("token_count") or max(len(tldr.split()), 1)),
            }
        )
    return sorted(rows, key=lambda row: (int(row.get("idx", 0)), str(row.get("name") or "").lower()))


def _section_is_verify_relevant(section: dict[str, Any]) -> bool:
    haystack = " ".join(
        [
            str(section.get("name") or "").strip().lower(),
            str(section.get("tldr") or "").strip().lower(),
        ]
    )
    return any(keyword in haystack for keyword in _DEEPXIV_RELEVANT_SECTION_KEYWORDS)


def _format_deepxiv_section(section: dict[str, Any]) -> str:
    name = str(section.get("name") or "").strip()
    tldr = str(section.get("tldr") or "").strip()
    if name and tldr:
        return f"[{name}] {tldr}"
    return tldr or name


def _select_progressive_sections(
    sections: list[dict[str, Any]],
    *,
    runtime_mode: str,
) -> list[dict[str, Any]]:
    normalized_mode = _normalize_runtime_mode(runtime_mode)
    if normalized_mode == "discussion":
        return []
    if normalized_mode == "promote":
        return list(sections)

    selected = list(sections[:_DEEPXIV_HEAD_SECTION_LIMIT])
    if normalized_mode == "explore":
        return selected

    seen_keys = {
        (str(section.get("name") or "").strip().lower(), int(section.get("idx", 0)))
        for section in selected
    }
    for section in sections:
        key = (str(section.get("name") or "").strip().lower(), int(section.get("idx", 0)))
        if key in seen_keys:
            continue
        if not _section_is_verify_relevant(section):
            continue
        selected.append(section)
        seen_keys.add(key)
        extra_count = max(0, len(selected) - _DEEPXIV_HEAD_SECTION_LIMIT)
        if extra_count >= _DEEPXIV_VERIFY_RELEVANT_SECTION_LIMIT:
            break
    return selected


def _resolve_progressive_reading_content(
    *,
    runtime_mode: str,
    provenance: dict[str, Any],
    snapshot_text: str,
    summary: str,
    absolute_path: str,
) -> tuple[str, str]:
    normalized_mode = _normalize_runtime_mode(runtime_mode)
    deepxiv_tldr = str(provenance.get("deepxiv_tldr") or "").strip()
    sections = _normalize_deepxiv_sections(provenance)
    if not deepxiv_tldr and not sections:
        preview_content = _resolve_preview_content(
            snapshot_text=snapshot_text,
            summary=summary,
            absolute_path=absolute_path,
        )
        analysis_text = "\n".join(
            _dedupe_text_parts(
                [
                    preview_content,
                    _strip_comment_lines(summary),
                ]
            )
        )
        return preview_content, analysis_text

    selected_sections = _select_progressive_sections(sections, runtime_mode=normalized_mode)
    selected_section_lines = [_format_deepxiv_section(section) for section in selected_sections]
    preview_content = "\n".join(_dedupe_text_parts([deepxiv_tldr, *selected_section_lines]))

    analysis_parts = [deepxiv_tldr, *selected_section_lines]
    if normalized_mode == "promote":
        analysis_parts.extend(
            [
                _resolve_preview_content(
                    snapshot_text=snapshot_text,
                    summary=summary,
                    absolute_path=absolute_path,
                ),
                _strip_comment_lines(summary),
            ]
        )
    analysis_text = "\n".join(_dedupe_text_parts(analysis_parts))
    return preview_content or analysis_text, analysis_text or preview_content


def _load_concept_graph_text(*, kernel_root: Path, locator: dict[str, Any]) -> dict[str, Any] | None:
    concept_graph_path = str(locator.get("concept_graph_path") or "").strip()
    if not concept_graph_path:
        return None
    path = kernel_root / concept_graph_path
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _build_l1_concept_graph(
    *,
    kernel_root: Path,
    source_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = _empty_l1_source_intake()["concept_graph"]
    node_seen: set[tuple[str, str]] = set()
    edge_seen: set[tuple[str, str]] = set()
    hyperedge_seen: set[tuple[str, str]] = set()
    community_seen: set[tuple[str, str]] = set()
    god_node_seen: set[tuple[str, str]] = set()

    for row in source_rows:
        source_id = str(row.get("source_id") or "").strip()
        source_title = str(row.get("title") or "").strip()
        source_type = str(row.get("source_type") or "").strip()
        locator = row.get("locator") or {}
        if not isinstance(locator, dict):
            locator = {}
        graph = _load_concept_graph_text(kernel_root=kernel_root, locator=locator)
        if not isinstance(graph, dict):
            continue

        labels_by_id = {
            str(item.get("node_id") or "").strip(): str(item.get("label") or "").strip()
            for item in (graph.get("nodes") or [])
            if isinstance(item, dict)
        }
        for item in graph.get("nodes") or []:
            if not isinstance(item, dict):
                continue
            node_id = str(item.get("node_id") or "").strip()
            label = str(item.get("label") or "").strip()
            node_type = str(item.get("node_type") or "").strip()
            if not node_id or not label or not node_type:
                continue
            key = (source_id.lower(), node_id.lower())
            if key in node_seen:
                continue
            node_seen.add(key)
            payload["nodes"].append(
                {
                    "source_id": source_id,
                    "source_title": source_title,
                    "source_type": source_type,
                    "node_id": node_id,
                    "label": label,
                    "node_type": node_type,
                    "confidence_tier": str(item.get("confidence_tier") or "EXTRACTED"),
                    "confidence_score": float(item.get("confidence_score") or 0.0),
                }
            )
        for item in graph.get("edges") or []:
            if not isinstance(item, dict):
                continue
            edge_id = str(item.get("edge_id") or "").strip()
            relation = str(item.get("relation") or "").strip()
            from_id = str(item.get("from_id") or "").strip()
            to_id = str(item.get("to_id") or "").strip()
            if not edge_id or not relation or not from_id or not to_id:
                continue
            key = (source_id.lower(), edge_id.lower())
            if key in edge_seen:
                continue
            edge_seen.add(key)
            payload["edges"].append(
                {
                    "source_id": source_id,
                    "edge_id": edge_id,
                    "from_id": from_id,
                    "relation": relation,
                    "to_id": to_id,
                }
            )
        for item in graph.get("hyperedges") or []:
            if not isinstance(item, dict):
                continue
            hyperedge_id = str(item.get("hyperedge_id") or "").strip()
            relation = str(item.get("relation") or "").strip()
            node_ids = [str(value).strip() for value in (item.get("node_ids") or []) if str(value).strip()]
            if not hyperedge_id or not relation or len(node_ids) < 2:
                continue
            key = (source_id.lower(), hyperedge_id.lower())
            if key in hyperedge_seen:
                continue
            hyperedge_seen.add(key)
            payload["hyperedges"].append(
                {
                    "source_id": source_id,
                    "hyperedge_id": hyperedge_id,
                    "relation": relation,
                    "node_ids": node_ids,
                }
            )
        for item in graph.get("communities") or []:
            if not isinstance(item, dict):
                continue
            community_id = str(item.get("community_id") or "").strip()
            label = str(item.get("label") or "").strip()
            node_ids = [str(value).strip() for value in (item.get("node_ids") or []) if str(value).strip()]
            if not community_id or not label or not node_ids:
                continue
            key = (source_id.lower(), community_id.lower())
            if key in community_seen:
                continue
            community_seen.add(key)
            payload["communities"].append(
                {
                    "source_id": source_id,
                    "community_id": community_id,
                    "label": label,
                    "node_ids": node_ids,
                }
            )
        for node_id in graph.get("god_nodes") or []:
            normalized = str(node_id or "").strip()
            if not normalized:
                continue
            key = (source_id.lower(), normalized.lower())
            if key in god_node_seen:
                continue
            god_node_seen.add(key)
            payload["god_nodes"].append(
                {
                    "source_id": source_id,
                    "node_id": normalized,
                    "label": labels_by_id.get(normalized) or normalized,
                }
            )

    return payload


def _reading_depth_signal(
    *,
    source_type: str,
    provenance: dict[str, Any],
    locator: dict[str, Any],
    snapshot_text: str,
    absolute_path: str,
    runtime_mode: str | None = None,
) -> tuple[str, str]:
    deepxiv_tldr = str(provenance.get("deepxiv_tldr") or "").strip()
    deepxiv_sections = _normalize_deepxiv_sections(provenance)
    if deepxiv_tldr or deepxiv_sections:
        normalized_mode = _normalize_runtime_mode(runtime_mode)
        if normalized_mode == "discussion":
            return "abstract_only", "deepxiv_brief"
        if normalized_mode == "explore":
            return "skim", "deepxiv_head"
        if normalized_mode == "verify":
            return "skim", "deepxiv_sections"
        return "full_read", "deepxiv_full"

    inferred = infer_reading_depth_label(
        source_type=source_type,
        provenance=provenance,
        locator=locator,
    )
    original_path = Path(absolute_path) if absolute_path else None
    if snapshot_text.strip():
        return "full_read", "snapshot_preview"
    if original_path and original_path.exists() and original_path.suffix.lower() in {".tex", ".md", ".txt"}:
        return "full_read", "local_source_text"
    if inferred == "full_read":
        return "full_read", "extracted_source_bundle"
    if inferred == "abstract_only":
        return "abstract_only", "metadata_link"
    return "skim", "summary_only"


def _build_l1_source_intake(
    *,
    kernel_root: Path,
    source_rows: list[dict[str, Any]],
    topic_slug: str,
    runtime_mode: str,
) -> dict[str, Any]:
    if not source_rows:
        return _empty_l1_source_intake()

    assumption_rows: list[dict[str, str]] = []
    regime_rows: list[dict[str, str]] = []
    reading_depth_rows: list[dict[str, str]] = []
    method_specificity_rows: list[dict[str, str]] = []
    counted_sources: set[str] = set()

    for row in source_rows:
        source_id = str(row.get("source_id") or "").strip()
        source_type = str(row.get("source_type") or "").strip()
        title = str(row.get("title") or "").strip()
        summary = str(row.get("summary") or "").strip()
        provenance = row.get("provenance") or {}
        locator = row.get("locator") or {}
        if not isinstance(provenance, dict):
            provenance = {}
        if not isinstance(locator, dict):
            locator = {}
        absolute_path = str(provenance.get("absolute_path") or "").strip()
        snapshot_text = _load_snapshot_text(kernel_root=kernel_root, topic_slug=topic_slug, source_id=source_id)
        preview_content, analysis_text = _resolve_progressive_reading_content(
            runtime_mode=runtime_mode,
            provenance=provenance,
            snapshot_text=snapshot_text,
            summary=summary,
            absolute_path=absolute_path,
        )
        reading_depth, basis = _reading_depth_signal(
            source_type=source_type,
            provenance=provenance,
            locator=locator,
            snapshot_text=snapshot_text,
            absolute_path=absolute_path,
            runtime_mode=runtime_mode,
        )
        source_key = source_id or title
        if source_key:
            counted_sources.add(source_key)
            reading_depth_rows.append(
                {
                    "source_id": source_id,
                    "source_title": title,
                    "source_type": source_type,
                    "reading_depth": reading_depth,
                    "basis": basis,
                }
            )
            method_family, specificity_tier, specificity_needle = infer_method_specificity(
                text=analysis_text,
                source_type=source_type,
            )
            method_specificity_rows.append(
                {
                    "source_id": source_id,
                    "source_title": title,
                    "source_type": source_type,
                    "method_family": method_family,
                    "specificity_tier": specificity_tier,
                    "reading_depth": reading_depth,
                    "evidence_excerpt": _excerpt_for_signal(
                        text=analysis_text,
                        needle=specificity_needle or title or summary,
                    ),
                    "evidence_sentence_ids": evidence_sentence_ids_for_text(
                        text=analysis_text,
                        needle=specificity_needle or title or summary,
                    ),
                }
            )
        if not analysis_text:
            continue
        for assumption in detect_assumptions(text=analysis_text):
            assumption_rows.append(
                {
                    "source_id": source_id,
                    "source_title": title,
                    "source_type": source_type,
                    "assumption": assumption,
                    "reading_depth": reading_depth,
                    "evidence_excerpt": _excerpt_for_signal(text=analysis_text, needle=assumption),
                    "evidence_sentence_ids": evidence_sentence_ids_for_text(text=analysis_text, needle=assumption),
                }
            )
        for regime in detect_regimes(text=analysis_text):
            regime_rows.append(
                {
                    "source_id": source_id,
                    "source_title": title,
                    "source_type": source_type,
                    "regime": regime,
                    "reading_depth": reading_depth,
                    "evidence_excerpt": _excerpt_for_signal(text=analysis_text, needle=regime),
                    "evidence_sentence_ids": evidence_sentence_ids_for_text(text=analysis_text, needle=regime),
                }
            )

    return {
        "source_count": len(counted_sources),
        "assumption_rows": _dedupe_rows(assumption_rows, key_fields=("source_id", "assumption")),
        "regime_rows": _dedupe_rows(regime_rows, key_fields=("source_id", "regime")),
        "reading_depth_rows": _dedupe_rows(
            reading_depth_rows,
            key_fields=("source_id", "reading_depth", "basis"),
        ),
        "method_specificity_rows": _dedupe_rows(
            method_specificity_rows,
            key_fields=("source_id", "method_family", "specificity_tier"),
        ),
        "concept_graph": _build_l1_concept_graph(
            kernel_root=kernel_root,
            source_rows=source_rows,
        ),
    }


def _claims_from_snapshot(*, snapshot_text: str, source_id: str) -> list[dict[str, Any]]:
    if not snapshot_text:
        return []
    claims: list[dict[str, Any]] = []
    rev_matches = re.findall(r"%\s*\[REV\]\s*\[([^\]]+)\]", snapshot_text)
    for match in rev_matches:
        tag = match.strip()
        lower_tag = tag.lower()
        if any(
            keyword in lower_tag
            for keyword in ("novel", "new", "change", "add", "improve", "extend", "mainline", "introduce")
        ):
            claims.append(
                {
                    "source_id": source_id,
                    "claim": tag,
                    "priority": 1 if "novel" in lower_tag else 2,
                }
            )
    return claims


def _claims_from_title(*, title: str, source_id: str) -> list[dict[str, Any]]:
    if not title:
        return []
    title_lower = title.lower()
    if not any(keyword in title_lower for keyword in _TITLE_NOVELTY_KEYWORDS):
        return []
    return [
        {
            "source_id": source_id,
            "claim": f"Title indicates: {title}",
            "priority": 3,
        }
    ]


def _claims_from_summary(*, summary: str, source_id: str) -> list[dict[str, Any]]:
    if not summary:
        return []
    summary_lower = summary.lower()
    sentences = re.split(r"[.!?]", summary)
    claims: list[dict[str, Any]] = []
    for keyword in _SUMMARY_NOVELTY_KEYWORDS:
        if keyword not in summary_lower:
            continue
        for sentence in sentences:
            if keyword in sentence.lower():
                claims.append(
                    {
                        "source_id": source_id,
                        "claim": sentence.strip()[:100],
                        "priority": 2,
                    }
                )
                break
    return claims


def _collect_source_material(
    *,
    kernel_root: Path,
    source_rows: list[dict[str, Any]],
    topic_slug: str,
    runtime_mode: str,
) -> tuple[list[dict[str, str]], list[dict[str, Any]], list[str], set[str]]:
    previews: list[dict[str, str]] = []
    claims: list[dict[str, Any]] = []
    titles: list[str] = []
    source_types: set[str] = set()

    for row in source_rows:
        source_id = str(row.get("source_id") or "")
        source_type = str(row.get("source_type") or "")
        title = str(row.get("title") or "")
        summary = str(row.get("summary") or "")
        provenance = row.get("provenance") or {}
        absolute_path = str(provenance.get("absolute_path") or "") if isinstance(provenance, dict) else ""
        snapshot_text = _load_snapshot_text(kernel_root=kernel_root, topic_slug=topic_slug, source_id=source_id)
        preview_content, _analysis_text = _resolve_progressive_reading_content(
            runtime_mode=runtime_mode,
            provenance=provenance if isinstance(provenance, dict) else {},
            snapshot_text=snapshot_text,
            summary=summary,
            absolute_path=absolute_path,
        )

        if title:
            titles.append(title)
        if source_type:
            source_types.add(source_type.lower())
        if preview_content:
            previews.append(
                {
                    "source_id": source_id,
                    "source_type": source_type,
                    "title": title,
                    "preview": preview_content,
                }
            )

        claims.extend(_claims_from_snapshot(snapshot_text=snapshot_text, source_id=source_id))
        claims.extend(_claims_from_title(title=title, source_id=source_id))
        claims.extend(_claims_from_summary(summary=summary, source_id=source_id))

    return previews, claims, titles, source_types


def _distill_initial_idea(*, previews: list[dict[str, str]], titles: list[str]) -> str:
    preview_parts: list[str] = []
    for preview_row in previews[:3]:
        preview_text = preview_row.get("preview", "")
        title = preview_row.get("title", "")
        first_para = preview_text.split("\n\n")[0] if preview_text else ""
        if first_para and len(first_para) > 20:
            preview_parts.append(f"[{title}] {first_para[:200]}")
    if preview_parts:
        return " ".join(preview_parts)
    if titles:
        return f"Research topic: {', '.join(titles[:3])}"
    return ""


def _distill_novelty_target(claims: list[dict[str, Any]]) -> str:
    if not claims:
        return ""
    sorted_claims = sorted(claims, key=lambda row: row.get("priority", 3))
    return str(sorted_claims[0].get("claim") or "")


def _distill_lane_and_route(*, source_types: set[str], titles: list[str]) -> tuple[str, str]:
    if any(source_type in source_types for source_type in _FORMAL_SOURCE_TYPES):
        if "thesis" in source_types:
            return (
                "formal_theory",
                f"Extract the core thesis claim from {', '.join(titles[:2])}, "
                "then identify the key definitions and first bounded proof obligation.",
            )
        return (
            "formal_theory",
            "Derive the first bounded question from the source material, "
            "then identify the key definitions and proof obligations.",
        )
    if any(source_type in source_types for source_type in _NUMERICAL_SOURCE_TYPES):
        return (
            "numerical",
            "Reproduce the baseline benchmark before trusting new results. "
            "then validate the observable definitions and normalization.",
        )
    return (
        "exploratory",
        "Define the scope boundaries and first validation artifact.",
    )


def distill_from_sources(
    *,
    kernel_root: Path,
    source_rows: list[dict[str, Any]],
    topic_slug: str,
    runtime_mode: str | None = None,
) -> dict[str, Any]:
    if not source_rows:
        return _empty_distillation()

    normalized_runtime_mode = _normalize_runtime_mode(runtime_mode)
    previews, claims, titles, source_types = _collect_source_material(
        kernel_root=kernel_root,
        source_rows=source_rows,
        topic_slug=topic_slug,
        runtime_mode=normalized_runtime_mode,
    )
    lane, first_validation_route = _distill_lane_and_route(source_types=source_types, titles=titles)
    l1_source_intake = _build_l1_source_intake(
        kernel_root=kernel_root,
        source_rows=source_rows,
        topic_slug=topic_slug,
        runtime_mode=normalized_runtime_mode,
    )
    return {
        "distilled_initial_idea": _distill_initial_idea(previews=previews, titles=titles),
        "distilled_novelty_target": _distill_novelty_target(claims),
        "distilled_first_validation_route": first_validation_route,
        "distilled_lane": lane,
        "distilled_l1_source_intake": l1_source_intake,
    }
