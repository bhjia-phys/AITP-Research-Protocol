from __future__ import annotations

import re
from pathlib import Path
from typing import Any

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


def _empty_l1_source_intake() -> dict[str, Any]:
    return {
        "source_count": 0,
        "assumption_rows": [],
        "regime_rows": [],
        "reading_depth_rows": [],
        "method_specificity_rows": [],
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


def _reading_depth_signal(
    *,
    source_type: str,
    provenance: dict[str, Any],
    locator: dict[str, Any],
    snapshot_text: str,
    absolute_path: str,
) -> tuple[str, str]:
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
        preview_content = _resolve_preview_content(
            snapshot_text=snapshot_text,
            summary=summary,
            absolute_path=absolute_path,
        )
        analysis_text = "\n".join(part for part in (preview_content, summary) if str(part).strip())
        reading_depth, basis = _reading_depth_signal(
            source_type=source_type,
            provenance=provenance,
            locator=locator,
            snapshot_text=snapshot_text,
            absolute_path=absolute_path,
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
        preview_content = _resolve_preview_content(
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
) -> dict[str, Any]:
    if not source_rows:
        return _empty_distillation()

    previews, claims, titles, source_types = _collect_source_material(
        kernel_root=kernel_root,
        source_rows=source_rows,
        topic_slug=topic_slug,
    )
    lane, first_validation_route = _distill_lane_and_route(source_types=source_types, titles=titles)
    l1_source_intake = _build_l1_source_intake(
        kernel_root=kernel_root,
        source_rows=source_rows,
        topic_slug=topic_slug,
    )
    return {
        "distilled_initial_idea": _distill_initial_idea(previews=previews, titles=titles),
        "distilled_novelty_target": _distill_novelty_target(claims),
        "distilled_first_validation_route": first_validation_route,
        "distilled_lane": lane,
        "distilled_l1_source_intake": l1_source_intake,
    }
