from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .source_intelligence import derive_canonical_source_id, extract_reference_ids


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _slugify(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(text or "").lower())).strip("-") or "source"


def _source_layer_root(kernel_root: Path) -> Path:
    return kernel_root / "topics"


def _compiled_root(kernel_root: Path) -> Path:
    return kernel_root / "canonical" / "compiled"


def _citation_traversal_root(kernel_root: Path) -> Path:
    return _compiled_root(kernel_root) / "citation_traversals"


def _source_family_root(kernel_root: Path) -> Path:
    return _compiled_root(kernel_root) / "source_families"


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


def _reference_alias_for(canonical_source_id: str) -> str | None:
    canonical_source_id = str(canonical_source_id or "").strip()
    if canonical_source_id.startswith("source_identity:doi:"):
        return f"doi:{canonical_source_id.split(':', 2)[-1]}"
    if canonical_source_id.startswith("source_identity:arxiv:"):
        return f"arxiv:{canonical_source_id.split(':', 2)[-1]}"
    return None


def _catalog_entry_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("canonical_source_id") or ""): row
        for row in (payload.get("sources") or [])
        if str(row.get("canonical_source_id") or "").strip()
    }


def _enrich_source_row(row: dict[str, Any], *, topic_slug: str) -> dict[str, Any]:
    title = str(row.get("title") or "").strip()
    summary = str(row.get("summary") or "").strip()
    source_type = str(row.get("source_type") or "").strip()
    provenance = row.get("provenance") if isinstance(row.get("provenance"), dict) else {}
    locator = row.get("locator") if isinstance(row.get("locator"), dict) else {}
    canonical_source_id = str(row.get("canonical_source_id") or "").strip() or derive_canonical_source_id(
        source_type=source_type,
        title=title,
        summary=summary,
        provenance=provenance,
        locator=locator,
    )
    references = _dedupe_strings(
        [str(item) for item in (row.get("references") or []) if str(item).strip()]
        or extract_reference_ids(text=f"{title} {summary}", provenance=provenance)
    )
    return {
        **row,
        "topic_slug": topic_slug,
        "canonical_source_id": canonical_source_id,
        "references": references,
        "source_id": str(row.get("source_id") or "").strip() or f"source:{_slugify(title)}",
        "source_type": source_type or "unknown",
        "title": title or canonical_source_id,
        "summary": summary or "(missing)",
    }


def build_source_catalog(kernel_root: Path) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    topics_root = _source_layer_root(kernel_root)
    source_rows: list[dict[str, Any]] = []
    topic_index: list[dict[str, Any]] = []
    topic_slugs: list[str] = []
    for source_index_path in sorted(topics_root.glob("*/L0/source_index.jsonl")):
        topic_slug = source_index_path.parent.parent.name
        topic_slugs.append(topic_slug)
        rows = [_enrich_source_row(row, topic_slug=topic_slug) for row in read_jsonl(source_index_path)]
        source_rows.extend(rows)
        topic_index.append(
            {
                "topic_slug": topic_slug,
                "source_count": len(rows),
                "canonical_source_ids": _dedupe_strings([str(row.get("canonical_source_id") or "") for row in rows]),
            }
        )

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in source_rows:
        grouped.setdefault(str(row["canonical_source_id"]), []).append(row)

    alias_to_canonical: dict[str, str] = {}
    for canonical_source_id in grouped:
        alias = _reference_alias_for(canonical_source_id)
        if alias:
            alias_to_canonical[alias] = canonical_source_id

    sources: list[dict[str, Any]] = []
    linked_reference_edge_count = 0
    for canonical_source_id, rows in grouped.items():
        topic_slugs_for_source = _dedupe_strings([str(row.get("topic_slug") or "") for row in rows])
        references = _dedupe_strings([ref for row in rows for ref in (row.get("references") or [])])
        linked_canonical_source_ids = [
            alias_to_canonical[ref]
            for ref in references
            if ref in alias_to_canonical and alias_to_canonical[ref] != canonical_source_id
        ]
        linked_canonical_source_ids = _dedupe_strings(linked_canonical_source_ids)
        linked_reference_edge_count += len(linked_canonical_source_ids)
        source_types = _dedupe_strings([str(row.get("source_type") or "") for row in rows])
        titles = _dedupe_strings([str(row.get("title") or "") for row in rows])
        entry = {
            "canonical_source_id": canonical_source_id,
            "representative_title": titles[0] if titles else canonical_source_id,
            "source_types": source_types,
            "topic_count": len(topic_slugs_for_source),
            "occurrence_count": len(rows),
            "topic_slugs": topic_slugs_for_source,
            "source_ids": _dedupe_strings([str(row.get("source_id") or "") for row in rows]),
            "titles": titles,
            "references": references,
            "linked_canonical_source_ids": linked_canonical_source_ids,
        }
        sources.append(entry)

    sources.sort(key=lambda row: (-int(row["topic_count"]), -int(row["occurrence_count"]), str(row["canonical_source_id"])))
    source_type_families: list[dict[str, Any]] = []
    grouped_by_type: dict[str, list[dict[str, Any]]] = {}
    for entry in sources:
        for source_type in entry["source_types"] or ["unknown"]:
            grouped_by_type.setdefault(source_type, []).append(entry)
    for source_type, rows in sorted(grouped_by_type.items(), key=lambda item: (-len(item[1]), item[0])):
        source_type_families.append(
            {
                "source_type": source_type,
                "canonical_source_count": len(rows),
                "multi_topic_source_count": sum(1 for row in rows if int(row["topic_count"]) > 1),
            }
        )

    return {
        "kind": "aitp_source_catalog",
        "compiler_version": 1,
        "generated_at": now_iso(),
        "source_contract_path": "L0_SOURCE_LAYER.md",
        "summary": {
            "total_topics": len(topic_slugs),
            "total_source_rows": len(source_rows),
            "unique_canonical_source_count": len(sources),
            "multi_topic_source_count": sum(1 for row in sources if int(row["topic_count"]) > 1),
            "linked_reference_edge_count": linked_reference_edge_count,
            "empty_source_store": len(source_rows) == 0,
        },
        "sources": sources,
        "source_type_families": source_type_families,
        "topic_index": sorted(topic_index, key=lambda row: (str(row["topic_slug"]), -int(row["source_count"]))),
    }


def build_source_citation_traversal(kernel_root: Path, *, canonical_source_id: str) -> dict[str, Any]:
    catalog = build_source_catalog(kernel_root)
    by_id = _catalog_entry_by_id(catalog)
    seed = by_id.get(canonical_source_id)
    if seed is None:
        raise ValueError(f"Unknown canonical_source_id: {canonical_source_id}")

    outgoing_links = [
        {
            "target_canonical_source_id": target_id,
            "target_title": str(target_entry.get("representative_title") or target_id),
            "target_topic_count": int(target_entry.get("topic_count") or 0),
            "target_topic_slugs": list(target_entry.get("topic_slugs") or []),
            "target_source_types": list(target_entry.get("source_types") or []),
        }
        for target_id in seed.get("linked_canonical_source_ids") or []
        if (target_entry := by_id.get(str(target_id)))
    ]
    incoming_links = [
        {
            "source_canonical_source_id": source_id,
            "source_title": str(source_entry.get("representative_title") or source_id),
            "source_topic_count": int(source_entry.get("topic_count") or 0),
            "source_topic_slugs": list(source_entry.get("topic_slugs") or []),
            "source_source_types": list(source_entry.get("source_types") or []),
        }
        for source_id, source_entry in sorted(by_id.items())
        if canonical_source_id in (source_entry.get("linked_canonical_source_ids") or [])
    ]
    related_topics = _dedupe_strings(
        list(seed.get("topic_slugs") or [])
        + [topic for row in outgoing_links for topic in (row.get("target_topic_slugs") or [])]
        + [topic for row in incoming_links for topic in (row.get("source_topic_slugs") or [])]
    )
    return {
        "kind": "aitp_source_citation_traversal",
        "compiler_version": 1,
        "generated_at": now_iso(),
        "source_contract_path": "L0_SOURCE_LAYER.md",
        "seed": {
            "canonical_source_id": canonical_source_id,
            "representative_title": str(seed.get("representative_title") or canonical_source_id),
            "source_types": list(seed.get("source_types") or []),
            "topic_count": int(seed.get("topic_count") or 0),
            "occurrence_count": int(seed.get("occurrence_count") or 0),
            "topic_slugs": list(seed.get("topic_slugs") or []),
            "references": list(seed.get("references") or []),
        },
        "summary": {
            "topic_count": int(seed.get("topic_count") or 0),
            "occurrence_count": int(seed.get("occurrence_count") or 0),
            "outgoing_link_count": len(outgoing_links),
            "incoming_link_count": len(incoming_links),
            "related_topic_count": len(related_topics),
        },
        "outgoing_links": outgoing_links,
        "incoming_links": incoming_links,
        "related_topics": related_topics,
    }


def build_source_family_report(kernel_root: Path, *, source_type: str) -> dict[str, Any]:
    normalized_source_type = str(source_type or "").strip()
    if not normalized_source_type:
        raise ValueError("source_type must not be empty")
    catalog = build_source_catalog(kernel_root)
    matching_sources = [
        row
        for row in (catalog.get("sources") or [])
        if normalized_source_type in (row.get("source_types") or [])
    ]
    topic_slugs = _dedupe_strings([topic for row in matching_sources for topic in (row.get("topic_slugs") or [])])
    linked_reference_edge_count = sum(len(row.get("linked_canonical_source_ids") or []) for row in matching_sources)
    return {
        "kind": "aitp_source_family_report",
        "compiler_version": 1,
        "generated_at": now_iso(),
        "source_contract_path": "L0_SOURCE_LAYER.md",
        "source_type": normalized_source_type,
        "summary": {
            "source_type": normalized_source_type,
            "canonical_source_count": len(matching_sources),
            "multi_topic_source_count": sum(1 for row in matching_sources if int(row.get("topic_count") or 0) > 1),
            "topic_count": len(topic_slugs),
            "linked_reference_edge_count": linked_reference_edge_count,
            "empty_family": len(matching_sources) == 0,
        },
        "sources": matching_sources,
        "topic_slugs": topic_slugs,
    }


def render_source_catalog_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Source Catalog",
        "",
        f"- Generated at: `{payload.get('generated_at') or '(missing)'}`",
        f"- Source contract: `{payload.get('source_contract_path') or '(missing)'}`",
        f"- Total topics: `{summary.get('total_topics', 0)}`",
        f"- Total source rows: `{summary.get('total_source_rows', 0)}`",
        f"- Unique canonical sources: `{summary.get('unique_canonical_source_count', 0)}`",
        f"- Cross-topic reused sources: `{summary.get('multi_topic_source_count', 0)}`",
        f"- Linked reference edges: `{summary.get('linked_reference_edge_count', 0)}`",
        "",
    ]
    if summary.get("empty_source_store"):
        lines.extend(
            [
                "No source-layer topic indexes were found in the current workspace.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(["## Cross-Topic Reused Sources", ""])
    reused_rows = [row for row in payload.get("sources") or [] if int(row.get("topic_count") or 0) > 1]
    if not reused_rows:
        lines.append("- Sources: `(none)`")
    for row in reused_rows:
        lines.append(
            f"- `{row.get('canonical_source_id')}` {row.get('representative_title')} "
            f"(topics=`{', '.join(row.get('topic_slugs') or [])}`, occurrences=`{row.get('occurrence_count', 0)}`)"
        )
    lines.append("")

    lines.extend(["## Reference-Linked Sources", ""])
    linked_rows = [row for row in payload.get("sources") or [] if row.get("linked_canonical_source_ids")]
    if not linked_rows:
        lines.append("- Sources: `(none)`")
    for row in linked_rows:
        lines.append(
            f"- `{row.get('canonical_source_id')}` -> `{', '.join(row.get('linked_canonical_source_ids') or [])}`"
        )
    lines.append("")

    lines.extend(["## Source Type Families", ""])
    for row in payload.get("source_type_families") or []:
        lines.append(
            f"- `{row.get('source_type')}` canonical_count=`{row.get('canonical_source_count', 0)}` "
            f"multi_topic=`{row.get('multi_topic_source_count', 0)}`"
        )
    lines.append("")

    lines.extend(["## Topic Index", ""])
    for row in payload.get("topic_index") or []:
        lines.append(
            f"- `{row.get('topic_slug')}` source_count=`{row.get('source_count', 0)}` "
            f"canonical_sources=`{', '.join(row.get('canonical_source_ids') or []) or '(none)'}`"
        )
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def materialize_source_catalog(kernel_root: Path) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    compiled_root = _compiled_root(kernel_root)
    payload = build_source_catalog(kernel_root)
    json_path = compiled_root / "source_catalog.json"
    markdown_path = compiled_root / "source_catalog.md"
    write_json(json_path, payload)
    write_text(markdown_path, render_source_catalog_markdown(payload))
    return {
        "payload": payload,
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
    }


def render_source_citation_traversal_markdown(payload: dict[str, Any]) -> str:
    seed = payload.get("seed") or {}
    summary = payload.get("summary") or {}
    lines = [
        "# Source Citation Traversal",
        "",
        f"- Canonical source id: `{seed.get('canonical_source_id') or '(missing)'}`",
        f"- Representative title: {seed.get('representative_title') or '(missing)'}",
        f"- Topic count: `{summary.get('topic_count', 0)}`",
        f"- Occurrence count: `{summary.get('occurrence_count', 0)}`",
        f"- Outgoing citation links: `{summary.get('outgoing_link_count', 0)}`",
        f"- Incoming citation links: `{summary.get('incoming_link_count', 0)}`",
        "",
        "## Topic Occurrences",
        "",
    ]
    for topic_slug in seed.get("topic_slugs") or ["(none)"]:
        lines.append(f"- `{topic_slug}`")
    lines.extend(["", "## Outgoing Citation Links", ""])
    outgoing_links = payload.get("outgoing_links") or []
    if not outgoing_links:
        lines.append("- Links: `(none)`")
    for row in outgoing_links:
        lines.append(
            f"- `{row.get('target_canonical_source_id')}` {row.get('target_title')} "
            f"(topics=`{', '.join(row.get('target_topic_slugs') or []) or '(none)'}`)"
        )
    lines.extend(["", "## Incoming Citation Links", ""])
    incoming_links = payload.get("incoming_links") or []
    if not incoming_links:
        lines.append("- Links: `(none)`")
    for row in incoming_links:
        lines.append(
            f"- `{row.get('source_canonical_source_id')}` {row.get('source_title')} "
            f"(topics=`{', '.join(row.get('source_topic_slugs') or []) or '(none)'}`)"
        )
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_source_family_report_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Source Family Report",
        "",
        f"- Source type: `{payload.get('source_type') or '(missing)'}`",
        f"- Canonical source count: `{summary.get('canonical_source_count', 0)}`",
        f"- Multi-topic source count: `{summary.get('multi_topic_source_count', 0)}`",
        f"- Topic count: `{summary.get('topic_count', 0)}`",
        f"- Linked reference edges: `{summary.get('linked_reference_edge_count', 0)}`",
        "",
        "## Most Reused Sources",
        "",
    ]
    sources = payload.get("sources") or []
    if not sources:
        lines.append("- Sources: `(none)`")
    for row in sources:
        lines.append(
            f"- `{row.get('canonical_source_id')}` {row.get('representative_title')} "
            f"(topics=`{', '.join(row.get('topic_slugs') or [])}`, occurrences=`{row.get('occurrence_count', 0)}`)"
        )
    lines.extend(["", "## Topic Spread", ""])
    for topic_slug in payload.get("topic_slugs") or ["(none)"]:
        lines.append(f"- `{topic_slug}`")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def materialize_source_citation_traversal(kernel_root: Path, *, canonical_source_id: str) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    payload = build_source_citation_traversal(kernel_root, canonical_source_id=canonical_source_id)
    basename = _slugify(canonical_source_id)
    json_path = _citation_traversal_root(kernel_root) / f"{basename}.json"
    markdown_path = _citation_traversal_root(kernel_root) / f"{basename}.md"
    write_json(json_path, payload)
    write_text(markdown_path, render_source_citation_traversal_markdown(payload))
    return {
        "payload": payload,
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
    }


def materialize_source_family_report(kernel_root: Path, *, source_type: str) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    payload = build_source_family_report(kernel_root, source_type=source_type)
    basename = _slugify(source_type)
    json_path = _source_family_root(kernel_root) / f"{basename}.json"
    markdown_path = _source_family_root(kernel_root) / f"{basename}.md"
    write_json(json_path, payload)
    write_text(markdown_path, render_source_family_report_markdown(payload))
    return {
        "payload": payload,
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
    }
