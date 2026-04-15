from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .topic_truth_root_support import compatibility_projection_path


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize_key(value: Any) -> str:
    return _normalize_text(value).lower()


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


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def graph_analysis_paths(runtime_root: Path) -> dict[str, Path]:
    return {
        "json": runtime_root / "graph_analysis.json",
        "note": runtime_root / "graph_analysis.md",
        "history": runtime_root / "graph_analysis_history.jsonl",
    }


def _empty_graph_snapshot() -> dict[str, Any]:
    return {
        "nodes": [],
        "edges": [],
        "hyperedges": [],
        "communities": [],
        "god_nodes": [],
    }


def _zero_graph_diff() -> dict[str, Any]:
    return {
        "added": {
            "node_count": 0,
            "node_labels": [],
            "edge_count": 0,
            "edge_relations": [],
            "god_node_count": 0,
            "god_node_labels": [],
        },
        "removed": {
            "node_count": 0,
            "node_labels": [],
            "edge_count": 0,
            "edge_relations": [],
            "god_node_count": 0,
            "god_node_labels": [],
        },
    }


def empty_graph_analysis(*, topic_slug: str) -> dict[str, Any]:
    return {
        "topic_slug": topic_slug,
        "summary": {
            "connection_count": 0,
            "question_count": 0,
            "history_length": 0,
        },
        "connections": [],
        "questions": [],
        "diff": _zero_graph_diff(),
        "graph_snapshot": _empty_graph_snapshot(),
        "updated_at": None,
        "updated_by": "",
        "path": f"topics/{topic_slug}/runtime/graph_analysis.json",
        "note_path": f"topics/{topic_slug}/runtime/graph_analysis.md",
        "history_path": f"topics/{topic_slug}/runtime/graph_analysis_history.jsonl",
    }


def _has_graph_content(concept_graph: dict[str, Any]) -> bool:
    return any(
        len(concept_graph.get(key) or [])
        for key in ("nodes", "edges", "hyperedges", "communities", "god_nodes")
    )


def _coerce_graph_snapshot(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return _empty_graph_snapshot()
    return {
        "nodes": list(payload.get("nodes") or []),
        "edges": list(payload.get("edges") or []),
        "hyperedges": list(payload.get("hyperedges") or []),
        "communities": list(payload.get("communities") or []),
        "god_nodes": list(payload.get("god_nodes") or []),
    }


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
    return {
        key: sorted(values)
        for key, values in mapping.items()
    }


def _connection_priority(kind: str) -> int:
    return {
        "shared_foundation_bridge": 0,
        "shared_concept_bridge": 1,
        "shared_community_bridge": 2,
        "shared_hyperedge_pattern_bridge": 3,
    }.get(str(kind or "").strip(), 99)


def _source_ids_key(source_ids: list[str]) -> tuple[str, ...]:
    return tuple(sorted(_normalize_key(source_id) for source_id in source_ids if _normalize_text(source_id)))


def surprising_connections(
    concept_graph: dict[str, Any],
    *,
    max_connections: int = 6,
) -> list[dict[str, Any]]:
    community_lookup = _community_labels_by_node(concept_graph)
    nodes_by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    source_meta_by_id: dict[str, dict[str, str]] = {}
    node_label_by_source_node: dict[tuple[str, str], str] = {}
    node_type_by_source_node: dict[tuple[str, str], str] = {}
    label_display: dict[str, str] = {}
    god_sources_by_label: dict[str, set[str]] = defaultdict(set)

    for row in concept_graph.get("god_nodes") or []:
        if not isinstance(row, dict):
            continue
        normalized_label = _normalize_key(row.get("label") or row.get("node_id"))
        source_id = _normalize_text(row.get("source_id"))
        if normalized_label and source_id:
            god_sources_by_label[normalized_label].add(source_id)

    for row in concept_graph.get("nodes") or []:
        if not isinstance(row, dict):
            continue
        normalized_label = _normalize_key(row.get("label"))
        source_id = _normalize_text(row.get("source_id"))
        source_title = _normalize_text(row.get("source_title"))
        source_type = _normalize_text(row.get("source_type"))
        node_id = _normalize_text(row.get("node_id"))
        node_type = _normalize_text(row.get("node_type"))
        if not normalized_label or not source_id or not node_id:
            continue
        node_label_by_source_node[(source_id, node_id)] = _normalize_text(row.get("label")) or node_id
        if node_type:
            node_type_by_source_node[(source_id, node_id)] = node_type
        label_display.setdefault(normalized_label, _normalize_text(row.get("label")) or node_id)
        source_meta = source_meta_by_id.setdefault(
            source_id,
            {
                "source_title": source_title or source_id,
                "source_type": source_type,
            },
        )
        if source_title and not source_meta.get("source_title"):
            source_meta["source_title"] = source_title
        if source_type and not source_meta.get("source_type"):
            source_meta["source_type"] = source_type
        nodes_by_label[normalized_label].append(
            {
                "source_id": source_id,
                "source_title": source_title or source_id,
                "source_type": source_type,
                "node_id": node_id,
                "community_labels": community_lookup.get((source_id, node_id), []),
            }
        )

    rows: list[dict[str, Any]] = []
    covered_community_keys: set[tuple[str, tuple[str, ...]]] = set()
    for normalized_label, group in nodes_by_label.items():
        unique_sources = _sorted_unique([row["source_id"] for row in group])
        if len(unique_sources) < 2:
            continue
        source_titles_by_id = {
            row["source_id"]: row["source_title"]
            for row in group
            if row["source_id"] and row["source_title"]
        }
        source_types = _sorted_unique([row["source_type"] for row in group])
        community_labels = _sorted_unique(
            [label for row in group for label in row.get("community_labels") or []]
        )
        bridge_label = label_display.get(normalized_label) or normalized_label
        foundation_sources = sorted(god_sources_by_label.get(normalized_label) or set())
        source_titles = _sorted_unique([source_titles_by_id.get(source_id, source_id) for source_id in unique_sources])
        kind = "shared_foundation_bridge" if len(foundation_sources) >= 2 else "shared_concept_bridge"
        detail = (
            f"{bridge_label} appears across {len(unique_sources)} sources: "
            f"{', '.join(source_titles[:3])}."
        )
        if community_labels:
            detail += f" Shared community labels: {', '.join(community_labels[:2])}."
        rows.append(
            {
                "kind": kind,
                "bridge_label": bridge_label,
                "source_ids": unique_sources,
                "source_titles": source_titles,
                "source_types": source_types,
                "community_labels": community_labels,
                "foundation_source_ids": foundation_sources,
                "detail": detail,
            }
        )
        for community_label in community_labels:
            covered_community_keys.add((_normalize_key(community_label), _source_ids_key(unique_sources)))

    community_groups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "bridge_label": "",
            "source_ids": set(),
            "node_labels_by_source": defaultdict(set),
            "community_node_ids_by_source": defaultdict(set),
        }
    )
    for row in concept_graph.get("communities") or []:
        if not isinstance(row, dict):
            continue
        source_id = _normalize_text(row.get("source_id"))
        bridge_label = _normalize_text(row.get("label"))
        node_ids = [_normalize_text(node_id) for node_id in (row.get("node_ids") or [])]
        node_ids = [node_id for node_id in node_ids if node_id]
        normalized_bridge = _normalize_key(bridge_label)
        if not source_id or not bridge_label or not node_ids:
            continue
        group = community_groups[normalized_bridge]
        group["bridge_label"] = group["bridge_label"] or bridge_label
        group["source_ids"].add(source_id)
        for node_id in node_ids:
            group["community_node_ids_by_source"][source_id].add(node_id)
            node_label = _normalize_text(node_label_by_source_node.get((source_id, node_id)))
            if node_label:
                group["node_labels_by_source"][source_id].add(node_label)

    for normalized_bridge, group in community_groups.items():
        unique_sources = _sorted_unique(list(group["source_ids"]))
        if len(unique_sources) < 2:
            continue
        source_key = _source_ids_key(unique_sources)
        if (normalized_bridge, source_key) in covered_community_keys:
            continue
        bridge_label = str(group.get("bridge_label") or normalized_bridge).strip()
        source_titles: list[str] = []
        source_types: list[str] = []
        detail_sources: list[str] = []
        for source_id in unique_sources:
            source_meta = source_meta_by_id.get(source_id) or {}
            source_title = _normalize_text(source_meta.get("source_title")) or source_id
            source_type = _normalize_text(source_meta.get("source_type"))
            node_labels = _sorted_unique(list((group.get("node_labels_by_source") or {}).get(source_id) or []))
            source_titles.append(source_title)
            if source_type:
                source_types.append(source_type)
            if node_labels:
                detail_sources.append(f"{source_title} ({', '.join(node_labels[:2])})")
            else:
                detail_sources.append(source_title)
        rows.append(
            {
                "kind": "shared_community_bridge",
                "bridge_label": bridge_label,
                "source_ids": unique_sources,
                "source_titles": _sorted_unique(source_titles),
                "source_types": _sorted_unique(source_types),
                "community_labels": [bridge_label],
                "foundation_source_ids": [],
                "detail": (
                    f"{bridge_label} recurs as a shared community across {len(unique_sources)} sources: "
                    f"{', '.join(detail_sources[:3])}."
                ),
            }
        )

    hyperedge_pattern_groups: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = defaultdict(
        lambda: {
            "relation": "",
            "node_type_signature": (),
            "source_ids": set(),
            "node_labels_by_source": defaultdict(set),
        }
    )
    for row in concept_graph.get("hyperedges") or []:
        if not isinstance(row, dict):
            continue
        source_id = _normalize_text(row.get("source_id"))
        relation = _normalize_text(row.get("relation"))
        node_ids = [_normalize_text(node_id) for node_id in (row.get("node_ids") or [])]
        node_ids = [node_id for node_id in node_ids if node_id]
        if not source_id or not relation or len(node_ids) < 2:
            continue
        node_type_signature = tuple(
            sorted(
                {
                    node_type_by_source_node.get((source_id, node_id), "")
                    for node_id in node_ids
                    if _normalize_text(node_type_by_source_node.get((source_id, node_id), ""))
                }
            )
        )
        if len(node_type_signature) < 2:
            continue
        group = hyperedge_pattern_groups[(relation.lower(), node_type_signature)]
        group["relation"] = group["relation"] or relation
        group["node_type_signature"] = node_type_signature
        group["source_ids"].add(source_id)
        for node_id in node_ids:
            node_label = _normalize_text(node_label_by_source_node.get((source_id, node_id)))
            if node_label:
                group["node_labels_by_source"][source_id].add(node_label)

    for group in hyperedge_pattern_groups.values():
        unique_sources = _sorted_unique(list(group["source_ids"]))
        if len(unique_sources) < 2:
            continue
        relation = _normalize_text(group.get("relation"))
        node_type_signature = tuple(group.get("node_type_signature") or ())
        bridge_label = f"{relation} pattern ({' + '.join(node_type_signature)})"
        source_titles: list[str] = []
        source_types: list[str] = []
        detail_sources: list[str] = []
        for source_id in unique_sources:
            source_meta = source_meta_by_id.get(source_id) or {}
            source_title = _normalize_text(source_meta.get("source_title")) or source_id
            source_type = _normalize_text(source_meta.get("source_type"))
            node_labels = _sorted_unique(list((group.get("node_labels_by_source") or {}).get(source_id) or []))
            source_titles.append(source_title)
            if source_type:
                source_types.append(source_type)
            if node_labels:
                detail_sources.append(f"{source_title} ({', '.join(node_labels[:3])})")
            else:
                detail_sources.append(source_title)
        rows.append(
            {
                "kind": "shared_hyperedge_pattern_bridge",
                "bridge_label": bridge_label,
                "source_ids": unique_sources,
                "source_titles": _sorted_unique(source_titles),
                "source_types": _sorted_unique(source_types),
                "community_labels": [],
                "foundation_source_ids": [],
                "detail": (
                    f"{bridge_label} recurs across {len(unique_sources)} sources: "
                    f"{', '.join(detail_sources[:3])}."
                ),
                "pattern_relation": relation,
                "pattern_node_types": list(node_type_signature),
            }
        )

    rows.sort(
        key=lambda row: (
            _connection_priority(str(row.get("kind") or "")),
            -len(row.get("source_ids") or []),
            row.get("bridge_label") or "",
        )
    )
    return rows[:max_connections]


def suggest_questions(
    concept_graph: dict[str, Any],
    *,
    max_questions: int = 6,
) -> list[dict[str, Any]]:
    connections = surprising_connections(concept_graph, max_connections=max_questions)
    questions: list[dict[str, Any]] = []
    for index, connection in enumerate(connections, start=1):
        source_titles = list(connection.get("source_titles") or [])
        bridge_label = _normalize_text(connection.get("bridge_label"))
        if not bridge_label or len(source_titles) < 2:
            continue
        community_labels = list(connection.get("community_labels") or [])
        if str(connection.get("kind") or "").strip() == "shared_hyperedge_pattern_bridge":
            question = (
                f"How do {source_titles[0]} and {source_titles[1]} realize the `{bridge_label}` "
                "structural pattern inside the current topic?"
            )
        else:
            question = (
                f"How does {bridge_label} connect {source_titles[0]} and {source_titles[1]} "
                "inside the current topic?"
            )
        if community_labels:
            question += f" Which assumptions or regimes stabilize the shared `{community_labels[0]}` view?"
        questions.append(
            {
                "question_id": f"graph-question:{index:02d}",
                "question_type": "bridge_question",
                "bridge_label": bridge_label,
                "source_ids": list(connection.get("source_ids") or []),
                "source_titles": source_titles,
                "community_labels": community_labels,
                "graph_analysis_kind": str(connection.get("kind") or "").strip(),
                "question": question,
            }
        )
    return questions


def _node_signatures(concept_graph: dict[str, Any]) -> dict[tuple[str, str, str], str]:
    signatures: dict[tuple[str, str, str], str] = {}
    for row in concept_graph.get("nodes") or []:
        if not isinstance(row, dict):
            continue
        source_id = _normalize_text(row.get("source_id"))
        label = _normalize_text(row.get("label"))
        node_type = _normalize_text(row.get("node_type"))
        if source_id and label and node_type:
            signatures[(source_id, label.lower(), node_type.lower())] = label
    return signatures


def _edge_signatures(concept_graph: dict[str, Any]) -> set[tuple[str, str, str, str]]:
    signatures: set[tuple[str, str, str, str]] = set()
    for row in concept_graph.get("edges") or []:
        if not isinstance(row, dict):
            continue
        source_id = _normalize_text(row.get("source_id"))
        relation = _normalize_text(row.get("relation"))
        from_id = _normalize_text(row.get("from_id"))
        to_id = _normalize_text(row.get("to_id"))
        if source_id and relation and from_id and to_id:
            signatures.add((source_id, relation.lower(), from_id.lower(), to_id.lower()))
    return signatures


def _god_node_signatures(concept_graph: dict[str, Any]) -> dict[tuple[str, str], str]:
    signatures: dict[tuple[str, str], str] = {}
    for row in concept_graph.get("god_nodes") or []:
        if not isinstance(row, dict):
            continue
        source_id = _normalize_text(row.get("source_id"))
        label = _normalize_text(row.get("label") or row.get("node_id"))
        if source_id and label:
            signatures[(source_id, label.lower())] = label
    return signatures


def graph_diff(
    previous_graph: dict[str, Any],
    current_graph: dict[str, Any],
) -> dict[str, Any]:
    previous_nodes = _node_signatures(previous_graph)
    current_nodes = _node_signatures(current_graph)
    previous_edges = _edge_signatures(previous_graph)
    current_edges = _edge_signatures(current_graph)
    previous_god_nodes = _god_node_signatures(previous_graph)
    current_god_nodes = _god_node_signatures(current_graph)

    added_node_keys = set(current_nodes) - set(previous_nodes)
    removed_node_keys = set(previous_nodes) - set(current_nodes)
    added_edge_keys = current_edges - previous_edges
    removed_edge_keys = previous_edges - current_edges
    added_god_node_keys = set(current_god_nodes) - set(previous_god_nodes)
    removed_god_node_keys = set(previous_god_nodes) - set(current_god_nodes)

    return {
        "added": {
            "node_count": len(added_node_keys),
            "node_labels": sorted({current_nodes[key] for key in added_node_keys}),
            "edge_count": len(added_edge_keys),
            "edge_relations": sorted({key[1] for key in added_edge_keys}),
            "god_node_count": len(added_god_node_keys),
            "god_node_labels": sorted({current_god_nodes[key] for key in added_god_node_keys}),
        },
        "removed": {
            "node_count": len(removed_node_keys),
            "node_labels": sorted({previous_nodes[key] for key in removed_node_keys}),
            "edge_count": len(removed_edge_keys),
            "edge_relations": sorted({key[1] for key in removed_edge_keys}),
            "god_node_count": len(removed_god_node_keys),
            "god_node_labels": sorted({previous_god_nodes[key] for key in removed_god_node_keys}),
        },
    }


def build_graph_analysis_surface(
    *,
    topic_slug: str,
    l1_source_intake: dict[str, Any],
    previous_payload: dict[str, Any] | None,
    updated_by: str,
) -> dict[str, Any]:
    concept_graph = _coerce_graph_snapshot((l1_source_intake or {}).get("concept_graph") or {})
    previous_snapshot = _coerce_graph_snapshot((previous_payload or {}).get("graph_snapshot") or {})
    previous_summary = (previous_payload or {}).get("summary") or {}
    previous_history_length = int(previous_summary.get("history_length") or 0)
    previous_exists = _has_graph_content(previous_snapshot)
    connections = surprising_connections(concept_graph)
    questions = suggest_questions(concept_graph)
    diff = graph_diff(previous_snapshot, concept_graph) if previous_exists else _zero_graph_diff()
    history_length = (
        previous_history_length + 1
        if previous_history_length
        else 2
        if previous_exists
        else 1
    )
    return {
        "topic_slug": topic_slug,
        "summary": {
            "connection_count": len(connections),
            "question_count": len(questions),
            "history_length": history_length,
        },
        "connections": connections,
        "questions": questions,
        "diff": diff,
        "graph_snapshot": concept_graph,
        "updated_at": now_iso(),
        "updated_by": updated_by,
    }


def render_graph_analysis_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    diff = payload.get("diff") or _zero_graph_diff()
    lines = [
        "# Graph analysis",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- JSON path: `{payload.get('path') or '(missing)'}`",
        f"- Note path: `{payload.get('note_path') or '(missing)'}`",
        f"- History path: `{payload.get('history_path') or '(missing)'}`",
        f"- Updated at: `{payload.get('updated_at') or '(missing)'}`",
        f"- Updated by: `{payload.get('updated_by') or '(missing)'}`",
        "",
        "## Summary",
        "",
        f"- Connection count: `{summary.get('connection_count') or 0}`",
        f"- Question count: `{summary.get('question_count') or 0}`",
        f"- History length: `{summary.get('history_length') or 0}`",
        "",
        "## Surprising connections",
        "",
    ]
    for row in payload.get("connections") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('kind') or '(missing)'}` `{row.get('bridge_label') or '(missing)'}`: "
                f"{row.get('detail') or '(missing)'}"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Question seeds", ""])
    for row in payload.get("questions") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('question_type') or '(missing)'}` `{row.get('bridge_label') or '(missing)'}`: "
                f"{row.get('question') or '(missing)'}"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Graph diff",
            "",
            f"- Added nodes: `{(diff.get('added') or {}).get('node_count') or 0}`",
            f"- Removed nodes: `{(diff.get('removed') or {}).get('node_count') or 0}`",
            f"- Added labels: `{', '.join((diff.get('added') or {}).get('node_labels') or []) or '(none)'}`",
            f"- Removed labels: `{', '.join((diff.get('removed') or {}).get('node_labels') or []) or '(none)'}`",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_graph_analysis_history(
    path: Path,
    *,
    payload: dict[str, Any],
) -> None:
    history_row = {
        "topic_slug": payload.get("topic_slug"),
        "updated_at": payload.get("updated_at"),
        "updated_by": payload.get("updated_by"),
        "summary": payload.get("summary") or {},
        "diff": payload.get("diff") or _zero_graph_diff(),
    }
    rendered = json.dumps(history_row, ensure_ascii=True, separators=(",", ":")) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(rendered)
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        with compatibility_path.open("a", encoding="utf-8") as handle:
            handle.write(rendered)
