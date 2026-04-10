from __future__ import annotations

import re
from pathlib import Path
from typing import Any

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


def _empty_distillation() -> dict[str, str]:
    return {
        "distilled_initial_idea": "",
        "distilled_novelty_target": "",
        "distilled_first_validation_route": "",
        "distilled_lane": "",
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
) -> dict[str, str]:
    if not source_rows:
        return _empty_distillation()

    previews, claims, titles, source_types = _collect_source_material(
        kernel_root=kernel_root,
        source_rows=source_rows,
        topic_slug=topic_slug,
    )
    lane, first_validation_route = _distill_lane_and_route(source_types=source_types, titles=titles)
    return {
        "distilled_initial_idea": _distill_initial_idea(previews=previews, titles=titles),
        "distilled_novelty_target": _distill_novelty_target(claims),
        "distilled_first_validation_route": first_validation_route,
        "distilled_lane": lane,
    }
