from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


def empty_l1_source_intake() -> dict[str, Any]:
    return {
        "source_count": 0,
        "assumption_rows": [],
        "regime_rows": [],
        "reading_depth_rows": [],
        "method_specificity_rows": [],
    }


def empty_source_intelligence(*, topic_slug: str) -> dict[str, Any]:
    return {
        "topic_slug": topic_slug,
        "summary": "No source-intelligence signals are currently recorded for this topic.",
        "canonical_source_ids": [],
        "cross_topic_match_count": 0,
        "fidelity_rows": [],
        "fidelity_summary": {
            "source_count": 0,
            "counts_by_tier": {},
            "strongest_tier": "unknown",
            "weakest_tier": "unknown",
        },
        "citation_edges": [],
        "source_neighbors": [],
        "neighbor_signal_count": 0,
        "path": f"runtime/topics/{topic_slug}/source_intelligence.json",
        "note_path": f"runtime/topics/{topic_slug}/source_intelligence.md",
    }


def append_l1_source_intake_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    l1_source_intake = payload.get("l1_source_intake") or {}
    lines.extend(
        [
            "",
            "## L1 source intake",
            "",
            f"- Source count: `{l1_source_intake.get('source_count') or 0}`",
            "",
            "## Source-backed assumptions",
            "",
        ]
    )
    for row in l1_source_intake.get("assumption_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` [{row.get('reading_depth') or 'skim'}]: "
                f"{row.get('assumption') or '(missing)'}"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Source-backed regimes", ""])
    for row in l1_source_intake.get("regime_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` [{row.get('reading_depth') or 'skim'}]: "
                f"{row.get('regime') or '(missing)'}"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Reading depth", ""])
    for row in l1_source_intake.get("reading_depth_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` => `{row.get('reading_depth') or 'skim'}` "
                f"(basis: `{row.get('basis') or 'summary_only'}`)"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Method specificity", ""])
    for row in l1_source_intake.get("method_specificity_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` [{row.get('reading_depth') or 'skim'}]: "
                f"`{row.get('method_family') or '(missing)'}` / `{row.get('specificity_tier') or '(missing)'}`"
            )
        else:
            lines.append(f"- {row}")


def append_source_intelligence_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    lines.extend(
        [
            "",
            "## Source intelligence",
            "",
            f"- JSON path: `{payload.get('path') or '(missing)'}`",
            f"- Note path: `{payload.get('note_path') or '(missing)'}`",
            f"- Canonical source ids: `{', '.join(payload.get('canonical_source_ids') or []) or '(none)'}`",
            f"- Citation edge count: `{len(payload.get('citation_edges') or [])}`",
            f"- Neighbor signal count: `{payload.get('neighbor_signal_count') or 0}`",
            f"- Cross-topic matches: `{payload.get('cross_topic_match_count') or 0}`",
            "",
            payload.get("summary") or "(missing)",
        ]
    )
    fidelity_summary = payload.get("fidelity_summary") or {}
    lines.extend(
        [
            "",
            "## Source fidelity",
            "",
            f"- Strongest tier: `{fidelity_summary.get('strongest_tier') or 'unknown'}`",
            f"- Weakest tier: `{fidelity_summary.get('weakest_tier') or 'unknown'}`",
            f"- Counts by tier: `{', '.join(f'{key}={value}' for key, value in (fidelity_summary.get('counts_by_tier') or {}).items()) or '(none)'}`",
        ]
    )
    if payload.get("source_neighbors"):
        lines.extend(["", "### Neighbor highlights", ""])
        for row in (payload.get("source_neighbors") or [])[:6]:
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` ~ `{row.get('neighbor_source_id') or '(missing)'}` "
                f"via `{row.get('relation_kind') or '(missing)'}`"
            )


def normalized_source_intelligence(
    *,
    topic_slug: str,
    shell_surfaces: dict[str, Any],
    relativize: Callable[[Path], str],
) -> dict[str, Any]:
    payload = dict(shell_surfaces.get("source_intelligence") or empty_source_intelligence(topic_slug=topic_slug))
    if shell_surfaces.get("source_intelligence_path"):
        payload["path"] = relativize(Path(shell_surfaces["source_intelligence_path"]))
    if shell_surfaces.get("source_intelligence_note_path"):
        payload["note_path"] = relativize(Path(shell_surfaces["source_intelligence_note_path"]))
    return payload


def build_active_research_contract_payload(
    *,
    research_contract: dict[str, Any],
    validation_contract: dict[str, Any],
    shell_surfaces: dict[str, Any],
    relativize: Callable[[Path], str],
) -> dict[str, Any]:
    return {
        "question_id": str(research_contract.get("question_id") or ""),
        "title": str(research_contract.get("title") or ""),
        "status": str(research_contract.get("status") or ""),
        "template_mode": str(research_contract.get("template_mode") or ""),
        "research_mode": str(research_contract.get("research_mode") or ""),
        "validation_mode": str(validation_contract.get("validation_mode") or ""),
        "target_layers": [str(item) for item in (research_contract.get("target_layers") or []) if str(item).strip()],
        "question": str(research_contract.get("question") or ""),
        "l1_source_intake": research_contract.get("l1_source_intake") or empty_l1_source_intake(),
        "path": relativize(Path(shell_surfaces["research_question_contract_path"])),
        "note_path": relativize(Path(shell_surfaces["research_question_contract_note_path"])),
    }
