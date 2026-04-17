from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize_key(value: Any) -> str:
    return _normalize_text(value).lower()


def _slugify(value: str) -> str:
    normalized = "".join(ch if ch.isalnum() else "-" for ch in str(value or "").strip().lower())
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized.strip("-") or "item"


def _sorted_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in sorted(_normalize_text(item) for item in values if _normalize_text(item)):
        lowered = value.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        ordered.append(value)
    return ordered


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _frontmatter(*, page_type: str, topic_slug: str, updated_at: str, updated_by: str, extra: dict[str, Any] | None = None) -> str:
    lines = [
        "---",
        f"page_type: {page_type}",
        f"topic_slug: {topic_slug}",
        "authority_level: non_authoritative_compiled_l1",
        f"updated_at: {updated_at}",
        f"updated_by: {updated_by}",
    ]
    for key, value in (extra or {}).items():
        if isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {str(value)}")
    lines.append("---")
    return "\n".join(lines)


def _wiki_link(path_without_md: str, label: str | None = None) -> str:
    target = str(path_without_md).replace("\\", "/").removesuffix(".md")
    if label and label != target.rsplit("/", 1)[-1]:
        return f"[[{target}|{label}]]"
    return f"[[{target}]]"


def _graph_export_root(kernel_root: Path, topic_slug: str) -> Path:
    return kernel_root / "topics" / topic_slug / "L1" / "vault" / "wiki" / "concept-graph"


def _source_locator_text(row: dict[str, Any]) -> str:
    provenance = row.get("provenance") or {}
    if not isinstance(provenance, dict):
        provenance = {}
    locator = row.get("locator") or {}
    if not isinstance(locator, dict):
        locator = {}
    for candidate in (
        provenance.get("abs_url"),
        provenance.get("absolute_path"),
        provenance.get("source_url"),
        locator.get("local_path"),
        locator.get("concept_graph_path"),
    ):
        value = _normalize_text(candidate)
        if value:
            return value
    return ""


def _source_row_lookup(source_rows: list[dict[str, Any]] | None) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for row in source_rows or []:
        if not isinstance(row, dict):
            continue
        source_id = _normalize_text(row.get("source_id"))
        if not source_id:
            continue
        lookup[source_id] = {
            "source_title": _normalize_text(row.get("title")) or source_id,
            "source_type": _normalize_text(row.get("source_type")),
            "summary": _normalize_text(row.get("summary")),
            "locator_text": _source_locator_text(row),
        }
    return lookup


def _community_labels_by_node(concept_graph: dict[str, Any]) -> dict[tuple[str, str], list[str]]:
    mapping: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in concept_graph.get("communities") or []:
        if not isinstance(row, dict):
            continue
        source_id = _normalize_text(row.get("source_id"))
        label = _normalize_text(row.get("label"))
        if not source_id or not label:
            continue
        for node_id in row.get("node_ids") or []:
            normalized_node_id = _normalize_text(node_id)
            if normalized_node_id:
                mapping[(source_id, normalized_node_id)].add(label)
    return {key: sorted(values) for key, values in mapping.items()}


def materialize_obsidian_concept_graph_export(
    *,
    kernel_root: Path,
    topic_slug: str,
    source_rows: list[dict[str, Any]] | None = None,
    l1_source_intake: dict[str, Any],
    updated_by: str,
    relativize: Callable[[Path], str],
) -> dict[str, Any]:
    updated_at = _now_iso()
    concept_graph = (l1_source_intake or {}).get("concept_graph") or {}
    source_lookup = _source_row_lookup(source_rows)
    export_root = _graph_export_root(kernel_root, topic_slug)
    manifest_path = export_root / "manifest.json"
    index_path = export_root / "index.md"

    community_lookup = _community_labels_by_node(concept_graph)
    merged_nodes: dict[tuple[str, str], dict[str, Any]] = {}
    note_ref_by_source_node: dict[tuple[str, str], str] = {}

    for row in concept_graph.get("nodes") or []:
        if not isinstance(row, dict):
            continue
        source_id = _normalize_text(row.get("source_id"))
        source_title = _normalize_text(row.get("source_title")) or source_id
        source_type = _normalize_text(row.get("source_type"))
        node_id = _normalize_text(row.get("node_id"))
        label = _normalize_text(row.get("label"))
        node_type = _normalize_text(row.get("node_type"))
        if not source_id or not node_id or not label or not node_type:
            continue
        key = (_normalize_key(label), _normalize_key(node_type))
        entry = merged_nodes.setdefault(
            key,
            {
                "label": label,
                "node_type": node_type,
                "source_ids": set(),
                "source_types": set(),
                "source_anchor_map": {},
                "occurrences": [],
                "community_labels": set(),
            },
        )
        entry["source_ids"].add(source_id)
        if source_type:
            entry["source_types"].add(source_type)
        source_row = source_lookup.get(source_id) or {}
        entry["source_anchor_map"][source_id] = {
            "source_title": _normalize_text(source_row.get("source_title")) or source_title,
            "source_type": _normalize_text(source_row.get("source_type")) or source_type,
            "summary": _normalize_text(source_row.get("summary")),
            "locator_text": _normalize_text(source_row.get("locator_text")),
        }
        entry["occurrences"].append((source_id, node_id))
        for community_label in community_lookup.get((source_id, node_id), []):
            entry["community_labels"].add(community_label)

    community_folder_labels: dict[str, str] = {}
    used_note_slugs: dict[str, set[str]] = defaultdict(set)
    merged_note_entries: list[dict[str, Any]] = []
    sorted_nodes = sorted(
        merged_nodes.values(),
        key=lambda row: (
            sorted(row["community_labels"])[0] if row["community_labels"] else "zzzz-unclustered",
            row["label"].lower(),
            row["node_type"].lower(),
        ),
    )
    for entry in sorted_nodes:
        community_labels = _sorted_unique(list(entry["community_labels"])) or ["Unclustered"]
        community_label = community_labels[0]
        folder_slug = _slugify(community_label)
        for label in community_labels:
            community_folder_labels.setdefault(_slugify(label), label)
        used_note_slugs[folder_slug].add("index")
        note_slug = _slugify(entry["label"])
        if note_slug in used_note_slugs[folder_slug]:
            note_slug = f"{note_slug}-{_slugify(entry['node_type'])}"
        suffix = 2
        while note_slug in used_note_slugs[folder_slug]:
            note_slug = f"{_slugify(entry['label'])}-{_slugify(entry['node_type'])}-{suffix}"
            suffix += 1
        used_note_slugs[folder_slug].add(note_slug)
        note_ref = f"concept-graph/{folder_slug}/{note_slug}"
        merged_note_entry = {
            "label": entry["label"],
            "node_type": entry["node_type"],
            "community_label": community_label,
            "folder_slug": folder_slug,
            "note_slug": note_slug,
            "note_ref": note_ref,
            "note_path": export_root / folder_slug / f"{note_slug}.md",
            "source_ids": _sorted_unique(list(entry["source_ids"])),
            "source_types": _sorted_unique(list(entry["source_types"])),
            "source_anchors": [
                {
                    "source_id": source_id,
                    "source_title": _normalize_text((entry["source_anchor_map"].get(source_id) or {}).get("source_title")) or source_id,
                    "source_type": _normalize_text((entry["source_anchor_map"].get(source_id) or {}).get("source_type")),
                    "summary": _normalize_text((entry["source_anchor_map"].get(source_id) or {}).get("summary")),
                    "locator_text": _normalize_text((entry["source_anchor_map"].get(source_id) or {}).get("locator_text")),
                }
                for source_id in _sorted_unique(list(entry["source_ids"]))
            ],
            "community_labels": community_labels,
            "outgoing_edges": [],
            "incoming_edges": [],
            "hyperedge_contexts": [],
        }
        for occurrence in entry["occurrences"]:
            note_ref_by_source_node[occurrence] = note_ref
        merged_note_entries.append(merged_note_entry)

    note_entry_by_ref = {entry["note_ref"]: entry for entry in merged_note_entries}

    seen_outgoing: set[tuple[str, str, str]] = set()
    seen_incoming: set[tuple[str, str, str]] = set()
    for row in concept_graph.get("edges") or []:
        if not isinstance(row, dict):
            continue
        source_id = _normalize_text(row.get("source_id"))
        relation = _normalize_text(row.get("relation"))
        from_id = _normalize_text(row.get("from_id"))
        to_id = _normalize_text(row.get("to_id"))
        if not source_id or not relation or not from_id or not to_id:
            continue
        from_ref = note_ref_by_source_node.get((source_id, from_id))
        to_ref = note_ref_by_source_node.get((source_id, to_id))
        if not from_ref or not to_ref or from_ref == to_ref:
            continue
        outgoing_key = (from_ref, relation.lower(), to_ref)
        incoming_key = (to_ref, relation.lower(), from_ref)
        if outgoing_key not in seen_outgoing:
            seen_outgoing.add(outgoing_key)
            note_entry_by_ref[from_ref]["outgoing_edges"].append(
                {
                    "relation": relation,
                    "target_ref": to_ref,
                    "target_label": note_entry_by_ref[to_ref]["label"],
                }
            )
        if incoming_key not in seen_incoming:
            seen_incoming.add(incoming_key)
            note_entry_by_ref[to_ref]["incoming_edges"].append(
                {
                    "relation": relation,
                    "source_ref": from_ref,
                    "source_label": note_entry_by_ref[from_ref]["label"],
                }
            )

    seen_hyperedges: set[tuple[str, str, tuple[str, ...]]] = set()
    for row in concept_graph.get("hyperedges") or []:
        if not isinstance(row, dict):
            continue
        source_id = _normalize_text(row.get("source_id"))
        relation = _normalize_text(row.get("relation"))
        node_ids = [_normalize_text(node_id) for node_id in (row.get("node_ids") or [])]
        note_refs = _sorted_unique(
            [
                note_ref_by_source_node.get((source_id, node_id), "")
                for node_id in node_ids
                if _normalize_text(node_id)
            ]
        )
        note_refs = [note_ref for note_ref in note_refs if note_ref]
        if not source_id or not relation or len(note_refs) < 2:
            continue
        sorted_note_refs = tuple(sorted(note_refs))
        for note_ref in note_refs:
            peer_refs = tuple(ref for ref in sorted_note_refs if ref != note_ref)
            if not peer_refs:
                continue
            key = (note_ref, relation.lower(), peer_refs)
            if key in seen_hyperedges:
                continue
            seen_hyperedges.add(key)
            note_entry_by_ref[note_ref]["hyperedge_contexts"].append(
                {
                    "relation": relation,
                    "peer_refs": list(peer_refs),
                }
            )

    community_notes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in merged_note_entries:
        for label in entry["community_labels"] or [entry["community_label"]]:
            community_notes[_slugify(label)].append(entry)

    index_lines = [
        _frontmatter(
            page_type="concept_graph_index",
            topic_slug=topic_slug,
            updated_at=updated_at,
            updated_by=updated_by,
            extra={
                "node_note_count": len(merged_note_entries),
                "community_folder_count": len(community_notes),
            },
        ),
        "",
        "# Concept Graph",
        "",
        "## Summary",
        "",
        f"- Node notes: `{len(merged_note_entries)}`",
        f"- Community folders: `{len(community_notes)}`",
        "",
        "## Communities",
        "",
    ]
    community_payloads: list[dict[str, Any]] = []
    community_page_paths: list[str] = []
    for folder_slug in sorted(community_notes):
        label = community_folder_labels.get(folder_slug, folder_slug)
        entries = sorted(community_notes[folder_slug], key=lambda row: (row["label"].lower(), row["node_type"].lower()))
        community_index_path = export_root / folder_slug / "index.md"
        community_page_paths.append(relativize(community_index_path))
        index_lines.append(f"### {label}")
        index_lines.append("")
        index_lines.append(f"- Overview: {_wiki_link(f'concept-graph/{folder_slug}/index', label)}")
        note_paths: list[str] = []
        for entry in entries:
            index_lines.append(
                f"- {_wiki_link(entry['note_ref'], entry['label'])} `{entry['node_type']}`"
            )
            note_paths.append(relativize(entry["note_path"]))
        index_lines.append("")
        community_lines = [
            _frontmatter(
                page_type="concept_graph_community",
                topic_slug=topic_slug,
                updated_at=updated_at,
                updated_by=updated_by,
                extra={
                    "community_label": label,
                    "note_count": len(entries),
                },
            ),
            "",
            f"# {_wiki_link('concept-graph/index', 'Concept Graph')} / {label}",
            "",
            "## Summary",
            "",
            f"- Node notes: `{len(entries)}`",
            "",
            "## Nodes",
            "",
        ]
        for entry in entries:
            community_lines.append(
                f"- {_wiki_link(entry['note_ref'], entry['label'])} `{entry['node_type']}`"
            )
        _write_text(community_index_path, "\n".join(community_lines).rstrip() + "\n")
        community_payloads.append(
            {
                "label": label,
                "folder_path": relativize(export_root / folder_slug),
                "index_path": relativize(community_index_path),
                "note_count": len(entries),
                "note_paths": note_paths,
            }
        )
    _write_text(index_path, "\n".join(index_lines).rstrip() + "\n")

    total_edge_link_count = 0
    total_hyperedge_context_count = 0
    for entry in merged_note_entries:
        total_edge_link_count += len(entry["outgoing_edges"]) + len(entry["incoming_edges"])
        total_hyperedge_context_count += len(entry["hyperedge_contexts"])
        lines = [
            _frontmatter(
                page_type="concept_graph_node",
                topic_slug=topic_slug,
                updated_at=updated_at,
                updated_by=updated_by,
                extra={
                    "node_label": entry["label"],
                    "node_type": entry["node_type"],
                    "community_label": entry["community_label"],
                    "source_count": len(entry["source_ids"]),
                },
            ),
            "",
            f"# {_wiki_link('concept-graph/index', 'Concept Graph')} / {entry['label']}",
            "",
            "## Summary",
            "",
            f"- Node type: `{entry['node_type']}`",
            f"- Primary community: `{entry['community_label']}`",
            f"- Communities: `{', '.join(entry['community_labels'])}`",
            f"- Source count: `{len(entry['source_ids'])}`",
            f"- Source types: `{', '.join(entry['source_types']) or '(none)'}`",
            "",
            "## Source anchors",
            "",
        ]
        for source_anchor in entry["source_anchors"]:
            source_type = str(source_anchor.get("source_type") or "").strip()
            type_suffix = f" [{source_type}]" if source_type else ""
            lines.append(
                f"- `{source_anchor['source_id']}`{type_suffix} {source_anchor['source_title']}"
            )
            if str(source_anchor.get("summary") or "").strip():
                lines.append(f"  - Summary: {source_anchor['summary']}")
            if str(source_anchor.get("locator_text") or "").strip():
                lines.append(f"  - Locator: `{source_anchor['locator_text']}`")
        lines.extend(["", "## Outgoing relations", ""])
        if entry["outgoing_edges"]:
            for edge in sorted(entry["outgoing_edges"], key=lambda row: (row["relation"].lower(), row["target_label"].lower())):
                lines.append(
                    f"- This node `{edge['relation']}` {_wiki_link(edge['target_ref'], edge['target_label'])}"
                )
        else:
            lines.append("- (none)")
        lines.extend(["", "## Incoming relations", ""])
        if entry["incoming_edges"]:
            for edge in sorted(entry["incoming_edges"], key=lambda row: (row["relation"].lower(), row["source_label"].lower())):
                lines.append(
                    f"- {_wiki_link(edge['source_ref'], edge['source_label'])} `{edge['relation']}` this node"
                )
        else:
            lines.append("- (none)")
        lines.extend(["", "## Hyperedge context", ""])
        if entry["hyperedge_contexts"]:
            for context in sorted(entry["hyperedge_contexts"], key=lambda row: (row["relation"].lower(), ",".join(row["peer_refs"]))):
                peer_links = ", ".join(
                    _wiki_link(peer_ref, note_entry_by_ref[peer_ref]["label"])
                    for peer_ref in context["peer_refs"]
                )
                lines.append(f"- This node participates in `{context['relation']}` with {peer_links}")
        else:
            lines.append("- (none)")
        _write_text(entry["note_path"], "\n".join(lines).rstrip() + "\n")

    payload = {
        "kind": "obsidian_concept_graph_export",
        "export_version": 1,
        "topic_slug": topic_slug,
        "status": "materialized",
        "root_path": relativize(export_root),
        "index_path": relativize(index_path),
        "summary": {
            "page_count": len(merged_note_entries) + 1 + len(community_payloads),
            "node_note_count": len(merged_note_entries),
            "community_folder_count": len(community_payloads),
            "community_page_count": len(community_payloads),
            "edge_link_count": total_edge_link_count,
            "hyperedge_context_count": total_hyperedge_context_count,
        },
        "communities": community_payloads,
        "note_paths": [relativize(entry["note_path"]) for entry in merged_note_entries],
        "community_page_paths": community_page_paths,
        "updated_at": updated_at,
        "updated_by": updated_by,
    }
    _write_json(manifest_path, payload)
    return {
        "payload": payload,
        "root_path": str(export_root),
        "manifest_path": str(manifest_path),
        "index_path": str(index_path),
        "note_paths": [str(entry["note_path"]) for entry in merged_note_entries],
    }
