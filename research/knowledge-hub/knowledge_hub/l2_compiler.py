from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .l2_staging import load_staging_entries, materialize_workspace_staging_manifest


IGNORED_CANONICAL_DIRS = {"backends", "examples", "compiled", "staging", "__pycache__"}
REUSE_FAMILY_ORDER = (
    ("workflows", "workflow"),
    ("methods", "method"),
    ("warnings", "warning_note"),
    ("validation_patterns", "validation_pattern"),
    ("bridges", "bridge"),
    ("topic_skill_projections", "topic_skill_projection"),
)
IGNORED_FOCUS_TAG_PREFIXES = (
    "against:",
    "literature-intake",
    "method-family:",
    "reading-depth:",
    "source:",
    "specificity:",
)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


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


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _canonical_root(kernel_root: Path) -> Path:
    return kernel_root / "canonical"


def _compiled_root(kernel_root: Path) -> Path:
    return _canonical_root(kernel_root) / "compiled"


def _derived_navigation_root(kernel_root: Path) -> Path:
    return _compiled_root(kernel_root) / "derived_navigation"


def _knowledge_report_path(kernel_root: Path) -> Path:
    return _compiled_root(kernel_root) / "workspace_knowledge_report.json"


def _knowledge_report_markdown_path(kernel_root: Path) -> Path:
    return _compiled_root(kernel_root) / "workspace_knowledge_report.md"


def _topic_corpus_baseline_path(kernel_root: Path, topic_slug: str, suffix: str) -> Path:
    return _compiled_root(kernel_root) / f"topic_l2_corpus_baseline--{_slugify(topic_slug)}.{suffix}"


def _allowed_unit_types(canonical_root: Path) -> set[str]:
    schema = read_json(canonical_root / "canonical-unit.schema.json") or {}
    enum_values = (((schema.get("properties") or {}).get("unit_type") or {}).get("enum") or [])
    return {str(item).strip() for item in enum_values if str(item).strip()}


def _compact_unit_ref(payload: dict[str, Any], *, path: str) -> dict[str, Any]:
    return {
        "unit_id": str(payload.get("id") or ""),
        "unit_type": str(payload.get("unit_type") or ""),
        "title": str(payload.get("title") or ""),
        "summary": str(payload.get("summary") or ""),
        "path": path,
        "updated_at": str(payload.get("updated_at") or ""),
        "maturity": str(payload.get("maturity") or ""),
        "topic_completion_status": str(payload.get("topic_completion_status") or ""),
        "dependencies": [str(item) for item in (payload.get("dependencies") or []) if str(item).strip()],
        "related_units": [str(item) for item in (payload.get("related_units") or []) if str(item).strip()],
        "tags": [str(item) for item in (payload.get("tags") or []) if str(item).strip()],
        "promotion_route": str(((payload.get("promotion") or {}).get("route")) or ""),
    }


def load_canonical_units(kernel_root: Path) -> list[dict[str, Any]]:
    canonical_root = _canonical_root(kernel_root)
    allowed_unit_types = _allowed_unit_types(canonical_root)
    units_by_id: dict[str, dict[str, Any]] = {}

    for json_path in canonical_root.rglob("*.json"):
        relative_parts = json_path.relative_to(canonical_root).parts
        if not relative_parts:
            continue
        if relative_parts[0] in IGNORED_CANONICAL_DIRS:
            continue
        if json_path.name == "canonical-unit.schema.json":
            continue
        payload = read_json(json_path)
        if not isinstance(payload, dict):
            continue
        unit_id = str(payload.get("id") or "").strip()
        unit_type = str(payload.get("unit_type") or "").strip()
        title = str(payload.get("title") or "").strip()
        summary = str(payload.get("summary") or "").strip()
        if not unit_id or not unit_type or not title or not summary:
            continue
        if allowed_unit_types and unit_type not in allowed_unit_types:
            continue
        units_by_id[unit_id] = _compact_unit_ref(
            payload,
            path=relative_to_root(json_path, kernel_root),
        )

    return sorted(units_by_id.values(), key=lambda item: (item["unit_type"], item["title"], item["unit_id"]))


def _units_by_type(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for unit in units:
        grouped.setdefault(unit["unit_type"], []).append(unit)

    rows: list[dict[str, Any]] = []
    for unit_type in sorted(grouped):
        typed_units = grouped[unit_type]
        rows.append(
            {
                "unit_type": unit_type,
                "count": len(typed_units),
                "units": typed_units,
            }
        )
    return rows


def _consultation_entrypoints(units: list[dict[str, Any]], retrieval_profiles: dict[str, Any]) -> dict[str, Any]:
    profiles = (retrieval_profiles.get("profiles") or {})
    entrypoints: dict[str, Any] = {}
    for profile_name in sorted(profiles):
        profile = profiles[profile_name] or {}
        preferred_types = [str(item) for item in (profile.get("preferred_unit_types") or []) if str(item).strip()]
        matches = [unit for unit in units if unit["unit_type"] in preferred_types]
        max_hits = int(profile.get("max_primary_hits") or len(matches) or 0)
        entrypoints[profile_name] = {
            "preferred_unit_types": preferred_types,
            "available_count": len(matches),
            "units": matches[:max_hits] if max_hits > 0 else matches,
        }
    return entrypoints


def _reuse_family_groups(units: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, Any] = {}
    for family_name, unit_type in REUSE_FAMILY_ORDER:
        matches = [unit for unit in units if unit["unit_type"] == unit_type]
        groups[family_name] = {
            "unit_type": unit_type,
            "count": len(matches),
            "units": matches,
        }
    return groups


def _relation_summary(units: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    edges_by_kind: dict[str, int] = {}
    for edge in edges:
        relation = str(
            edge.get("relation")
            or edge.get("edge_type")
            or edge.get("kind")
            or edge.get("type")
            or "unknown"
        ).strip()
        if not relation:
            relation = "unknown"
        edges_by_kind[relation] = edges_by_kind.get(relation, 0) + 1

    units_with_dependencies = sum(1 for unit in units if unit.get("dependencies"))
    units_with_related_links = sum(1 for unit in units if unit.get("related_units"))
    units_without_links = sum(
        1 for unit in units if not unit.get("dependencies") and not unit.get("related_units")
    )

    return {
        "edge_count": len(edges),
        "edges_by_kind": dict(sorted(edges_by_kind.items())),
        "units_with_dependencies": units_with_dependencies,
        "units_with_related_links": units_with_related_links,
        "units_without_links": units_without_links,
    }


def _edge_endpoints(edge: dict[str, Any]) -> tuple[str, str, str]:
    relation = str(
        edge.get("relation")
        or edge.get("edge_type")
        or edge.get("kind")
        or edge.get("type")
        or "unknown"
    ).strip() or "unknown"
    from_id = str(edge.get("from_id") or edge.get("source") or "").strip()
    to_id = str(edge.get("to_id") or edge.get("target") or "").strip()
    return from_id, relation, to_id


def _slugify(value: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.lower())).strip("-") or "unit"


def _navigation_page_name(unit_id: str, unit_type: str) -> str:
    _, _, suffix = unit_id.partition(":")
    return f"{unit_type}--{_slugify(suffix or unit_id)}.md"


def _wiki_link(target: str, label: str) -> str:
    stem = target[:-3] if target.endswith(".md") else target
    return f"[[{stem}|{label}]]"


def _fingerprint_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


def _consultation_profiles_by_type(retrieval_profiles: dict[str, Any]) -> dict[str, list[str]]:
    profiles = (retrieval_profiles.get("profiles") or {})
    mapping: dict[str, list[str]] = {}
    for profile_name, profile in sorted(profiles.items()):
        for unit_type in [str(item) for item in (profile or {}).get("preferred_unit_types") or [] if str(item).strip()]:
            mapping.setdefault(unit_type, []).append(profile_name)
    return mapping


def build_workspace_graph_report(kernel_root: Path) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    canonical_root = _canonical_root(kernel_root)
    units = load_canonical_units(kernel_root)
    retrieval_profiles = read_json(canonical_root / "retrieval_profiles.json") or {}
    edges = read_jsonl(canonical_root / "edges.jsonl")
    unit_by_id = {unit["unit_id"]: unit for unit in units}
    profiles_by_type = _consultation_profiles_by_type(retrieval_profiles)
    outgoing: dict[str, list[dict[str, Any]]] = {}
    incoming: dict[str, list[dict[str, Any]]] = {}
    relation_clusters: dict[str, list[dict[str, Any]]] = {}

    for edge in edges:
        from_id, relation, to_id = _edge_endpoints(edge)
        if from_id not in unit_by_id or to_id not in unit_by_id:
            continue
        source_unit = unit_by_id[from_id]
        target_unit = unit_by_id[to_id]
        edge_row = {
            "relation": relation,
            "from_id": from_id,
            "from_title": source_unit["title"],
            "from_unit_type": source_unit["unit_type"],
            "to_id": to_id,
            "to_title": target_unit["title"],
            "to_unit_type": target_unit["unit_type"],
            "notes": str(edge.get("notes") or ""),
        }
        outgoing.setdefault(from_id, []).append(edge_row)
        incoming.setdefault(to_id, []).append(edge_row)
        relation_clusters.setdefault(relation, []).append(edge_row)

    unit_navigation: list[dict[str, Any]] = []
    for unit in sorted(units, key=lambda row: (row["unit_type"], row["title"], row["unit_id"])):
        unit_id = unit["unit_id"]
        page_name = _navigation_page_name(unit_id, unit["unit_type"])
        outgoing_rows = sorted(
            outgoing.get(unit_id, []),
            key=lambda row: (row["relation"], row["to_title"], row["to_id"]),
        )
        incoming_rows = sorted(
            incoming.get(unit_id, []),
            key=lambda row: (row["relation"], row["from_title"], row["from_id"]),
        )
        entry = {
            "unit_id": unit_id,
            "unit_type": unit["unit_type"],
            "title": unit["title"],
            "summary": unit["summary"],
            "canonical_path": unit["path"],
            "page_name": page_name,
            "page_path": relative_to_root(_derived_navigation_root(kernel_root) / page_name, kernel_root),
            "consultation_profiles": profiles_by_type.get(unit["unit_type"], []),
            "outgoing_count": len(outgoing_rows),
            "incoming_count": len(incoming_rows),
            "degree": len(outgoing_rows) + len(incoming_rows),
            "outgoing_relations": [
                {
                    **row,
                    "target_page_name": _navigation_page_name(row["to_id"], row["to_unit_type"]),
                }
                for row in outgoing_rows
            ],
            "incoming_relations": [
                {
                    **row,
                    "source_page_name": _navigation_page_name(row["from_id"], row["from_unit_type"]),
                }
                for row in incoming_rows
            ],
        }
        unit_navigation.append(entry)

    hub_units = sorted(
        unit_navigation,
        key=lambda row: (-int(row["degree"]), -int(row["outgoing_count"]), row["unit_type"], row["title"]),
    )
    relation_rows = [
        {
            "relation": relation,
            "count": len(rows),
            "example_edges": sorted(
                rows,
                key=lambda row: (row["from_title"], row["to_title"], row["relation"]),
            )[:8],
        }
        for relation, rows in sorted(relation_clusters.items(), key=lambda item: (-len(item[1]), item[0]))
    ]
    connected_count = sum(1 for row in unit_navigation if int(row["degree"]) > 0)
    isolated_units = [row for row in unit_navigation if int(row["degree"]) == 0]

    return {
        "kind": "l2_workspace_graph_report",
        "compiler_version": 1,
        "generated_at": now_iso(),
        "source_contract_path": "canonical/L2_COMPILER_PROTOCOL.md",
        "summary": {
            "total_units": len(units),
            "edge_count": sum(cluster["count"] for cluster in relation_rows),
            "connected_unit_count": connected_count,
            "isolated_unit_count": len(isolated_units),
            "relation_kinds_present": [cluster["relation"] for cluster in relation_rows],
            "empty_canonical_store": len(units) == 0,
        },
        "consultation_entrypoints": _consultation_entrypoints(units, retrieval_profiles),
        "hub_units": hub_units[:10],
        "isolated_units": [
            {
                "unit_id": row["unit_id"],
                "unit_type": row["unit_type"],
                "title": row["title"],
                "page_name": row["page_name"],
                "page_path": row["page_path"],
            }
            for row in isolated_units
        ],
        "relation_clusters": relation_rows,
        "unit_navigation": unit_navigation,
    }


def build_workspace_memory_map(kernel_root: Path) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    canonical_root = _canonical_root(kernel_root)
    units = load_canonical_units(kernel_root)
    retrieval_profiles = read_json(canonical_root / "retrieval_profiles.json") or {}
    edges = read_jsonl(canonical_root / "edges.jsonl")

    unit_types_present = sorted({unit["unit_type"] for unit in units})
    summary = {
        "total_units": len(units),
        "unit_types_present": unit_types_present,
        "edge_count": len(edges),
        "empty_canonical_store": len(units) == 0,
    }

    return {
        "kind": "l2_workspace_memory_map",
        "compiler_version": 1,
        "generated_at": now_iso(),
        "source_contract_path": "canonical/L2_COMPILER_PROTOCOL.md",
        "inputs": {
            "index_path": "canonical/index.jsonl",
            "edges_path": "canonical/edges.jsonl",
            "retrieval_profiles_path": "canonical/retrieval_profiles.json",
            "scan_mode": "filesystem_fallback_plus_declared_canonical_inputs",
        },
        "summary": summary,
        "units_by_type": _units_by_type(units),
        "consultation_entrypoints": _consultation_entrypoints(units, retrieval_profiles),
        "reuse_families": _reuse_family_groups(units),
        "relation_summary": _relation_summary(units, edges),
    }


def render_workspace_memory_map_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Workspace Memory Map",
        "",
        f"- Generated at: `{payload.get('generated_at') or '(missing)'}`",
        f"- Source contract: `{payload.get('source_contract_path') or '(missing)'}`",
        f"- Total canonical units: `{summary.get('total_units', 0)}`",
        f"- Unit types present: `{', '.join(summary.get('unit_types_present') or []) or '(none)'}`",
        f"- Edge count: `{summary.get('edge_count', 0)}`",
        "",
    ]

    if summary.get("empty_canonical_store"):
        lines.extend(
            [
                "No canonical units were found in the current workspace.",
                "",
                "This compiled map is still valid: it confirms the compiler target exists and that the canonical store is currently empty.",
                "",
            ]
        )

    lines.extend(["## Consultation Entry Points", ""])
    consultation_entrypoints = payload.get("consultation_entrypoints") or {}
    for profile_name in sorted(consultation_entrypoints):
        profile = consultation_entrypoints[profile_name] or {}
        lines.append(f"### `{profile_name}`")
        lines.append(f"- Preferred unit types: `{', '.join(profile.get('preferred_unit_types') or []) or '(none)'}`")
        lines.append(f"- Available count: `{profile.get('available_count', 0)}`")
        units = profile.get("units") or []
        if not units:
            lines.append("- Units: `(none)`")
        else:
            for unit in units:
                lines.append(
                    f"- [`{unit.get('unit_type')}`] `{unit.get('unit_id')}` {unit.get('title')} "
                    f"- {unit.get('summary')} (`{unit.get('path')}`)"
                )
        lines.append("")

    lines.extend(["## Reuse Families", ""])
    reuse_families = payload.get("reuse_families") or {}
    for family_name, _unit_type in REUSE_FAMILY_ORDER:
        family = reuse_families.get(family_name) or {}
        lines.append(f"### `{family_name}`")
        lines.append(f"- Count: `{family.get('count', 0)}`")
        units = family.get("units") or []
        if not units:
            lines.append("- Units: `(none)`")
        else:
            for unit in units:
                lines.append(
                    f"- `{unit.get('unit_id')}` {unit.get('title')} - {unit.get('summary')} (`{unit.get('path')}`)"
                )
        lines.append("")

    relation_summary = payload.get("relation_summary") or {}
    lines.extend(["## Relation Summary", ""])
    lines.append(f"- Units with dependencies: `{relation_summary.get('units_with_dependencies', 0)}`")
    lines.append(f"- Units with related links: `{relation_summary.get('units_with_related_links', 0)}`")
    lines.append(f"- Units without links: `{relation_summary.get('units_without_links', 0)}`")
    edge_kinds = relation_summary.get("edges_by_kind") or {}
    if edge_kinds:
        lines.append("- Edge kinds:")
        for relation, count in edge_kinds.items():
            lines.append(f"  - `{relation}`: `{count}`")
    else:
        lines.append("- Edge kinds: `(none)`")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def materialize_workspace_memory_map(kernel_root: Path) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    compiled_root = _compiled_root(kernel_root)
    payload = build_workspace_memory_map(kernel_root)
    json_path = compiled_root / "workspace_memory_map.json"
    md_path = compiled_root / "workspace_memory_map.md"
    write_json(json_path, payload)
    write_text(md_path, render_workspace_memory_map_markdown(payload))
    return {
        "payload": payload,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }


def render_workspace_graph_report_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Workspace Graph Report",
        "",
        f"- Generated at: `{payload.get('generated_at') or '(missing)'}`",
        f"- Total canonical units: `{summary.get('total_units', 0)}`",
        f"- Edge count: `{summary.get('edge_count', 0)}`",
        f"- Connected units: `{summary.get('connected_unit_count', 0)}`",
        f"- Isolated units: `{summary.get('isolated_unit_count', 0)}`",
        f"- Navigation index: `canonical/compiled/derived_navigation/index.md`",
        "",
    ]

    if summary.get("empty_canonical_store"):
        lines.extend(
            [
                "No canonical graph units were found in the current workspace.",
                "",
            ]
        )

    lines.extend(["## Graph Hubs", ""])
    hub_units = payload.get("hub_units") or []
    if not hub_units:
        lines.append("- Units: `(none)`")
    for unit in hub_units:
        unit_label = str(unit.get("title") or unit.get("unit_id") or "unit")
        unit_link = _wiki_link(f"derived_navigation/{unit.get('page_name')}", unit_label)
        lines.append(
            f"- `{unit.get('unit_id')}` {unit.get('title')} "
            f"(degree=`{unit.get('degree', 0)}`, outgoing=`{unit.get('outgoing_count', 0)}`, incoming=`{unit.get('incoming_count', 0)}`) "
            f"{unit_link}"
        )
    lines.append("")

    lines.extend(["## Relation Clusters", ""])
    relation_clusters = payload.get("relation_clusters") or []
    if not relation_clusters:
        lines.append("- Relation clusters: `(none)`")
    for cluster in relation_clusters:
        lines.append(f"### `{cluster.get('relation')}` (`{cluster.get('count', 0)}`)")
        for row in cluster.get("example_edges") or []:
            lines.append(
                f"- `{row.get('from_id')}` {row.get('from_title')} -> `{row.get('to_id')}` {row.get('to_title')}"
            )
        lines.append("")

    lines.extend(["## Consultation Anchors", ""])
    consultation_entrypoints = payload.get("consultation_entrypoints") or {}
    for profile_name in sorted(consultation_entrypoints):
        entry = consultation_entrypoints[profile_name] or {}
        lines.append(f"### `{profile_name}`")
        lines.append(f"- Available count: `{entry.get('available_count', 0)}`")
        for unit in (entry.get("units") or [])[:6]:
            page_name = _navigation_page_name(str(unit.get("unit_id") or ""), str(unit.get("unit_type") or "unit"))
            lines.append(
                f"- `{unit.get('unit_id')}` {unit.get('title')} "
                f"{_wiki_link(f'derived_navigation/{page_name}', str(unit.get('title') or unit.get('unit_id') or 'unit'))}"
            )
        lines.append("")

    lines.extend(["## Isolated Units", ""])
    isolated_units = payload.get("isolated_units") or []
    if not isolated_units:
        lines.append("- Units: `(none)`")
    for unit in isolated_units:
        unit_label = str(unit.get("title") or unit.get("unit_id") or "unit")
        unit_link = _wiki_link(f"derived_navigation/{unit.get('page_name')}", unit_label)
        lines.append(
            f"- `{unit.get('unit_id')}` {unit.get('title')} "
            f"{unit_link}"
        )
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_workspace_graph_navigation_index_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# L2 Graph Navigation Index",
        "",
        f"- Generated at: `{payload.get('generated_at') or '(missing)'}`",
        f"- Source report: `canonical/compiled/workspace_graph_report.md`",
        "",
        "## Top Hubs",
        "",
    ]
    hub_units = payload.get("hub_units") or []
    if not hub_units:
        lines.append("- Units: `(none)`")
    for unit in hub_units:
        lines.append(
            f"- {_wiki_link(str(unit.get('page_name') or ''), str(unit.get('title') or unit.get('unit_id') or 'unit'))} "
            f"(degree=`{unit.get('degree', 0)}`)"
        )
    lines.append("")

    lines.extend(["## All Units By Type", ""])
    grouped: dict[str, list[dict[str, Any]]] = {}
    for unit in payload.get("unit_navigation") or []:
        grouped.setdefault(str(unit.get("unit_type") or "unknown"), []).append(unit)
    for unit_type in sorted(grouped):
        lines.append(f"### `{unit_type}`")
        for unit in grouped[unit_type]:
            lines.append(
                f"- {_wiki_link(str(unit.get('page_name') or ''), str(unit.get('title') or unit.get('unit_id') or 'unit'))} "
                f"- {unit.get('summary')} (degree=`{unit.get('degree', 0)}`)"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_workspace_graph_navigation_page_markdown(entry: dict[str, Any]) -> str:
    lines = [
        f"# {entry.get('title') or entry.get('unit_id') or 'L2 Unit'}",
        "",
        f"- Unit id: `{entry.get('unit_id') or '(missing)'}`",
        f"- Unit type: `{entry.get('unit_type') or '(missing)'}`",
        f"- Canonical path: `{entry.get('canonical_path') or '(missing)'}`",
        f"- Degree: `{entry.get('degree', 0)}`",
        f"- Consultation profiles: `{', '.join(entry.get('consultation_profiles') or []) or '(none)'}`",
        "",
        "## Summary",
        "",
        str(entry.get("summary") or "(missing)"),
        "",
        "## Outgoing Relations",
        "",
    ]
    outgoing_relations = entry.get("outgoing_relations") or []
    if not outgoing_relations:
        lines.append("- Relations: `(none)`")
    for row in outgoing_relations:
        lines.append(
            f"- `{row.get('relation')}` -> {_wiki_link(str(row.get('target_page_name') or ''), str(row.get('to_title') or row.get('to_id') or 'unit'))}"
        )
    lines.extend(["", "## Incoming Relations", ""])
    incoming_relations = entry.get("incoming_relations") or []
    if not incoming_relations:
        lines.append("- Relations: `(none)`")
    for row in incoming_relations:
        lines.append(
            f"- `{row.get('relation')}` <- {_wiki_link(str(row.get('source_page_name') or ''), str(row.get('from_title') or row.get('from_id') or 'unit'))}"
        )
    lines.extend(["", "## Navigation", "", f"- {_wiki_link('index.md', 'L2 Graph Navigation Index')}"])
    return "\n".join(lines).rstrip() + "\n"


def materialize_workspace_graph_report(kernel_root: Path) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    compiled_root = _compiled_root(kernel_root)
    navigation_root = _derived_navigation_root(kernel_root)
    payload = build_workspace_graph_report(kernel_root)
    json_path = compiled_root / "workspace_graph_report.json"
    markdown_path = compiled_root / "workspace_graph_report.md"
    navigation_index_path = navigation_root / "index.md"
    write_json(json_path, payload)
    write_text(markdown_path, render_workspace_graph_report_markdown(payload))
    write_text(navigation_index_path, render_workspace_graph_navigation_index_markdown(payload))
    for unit in payload.get("unit_navigation") or []:
        write_text(navigation_root / str(unit.get("page_name") or "unit.md"), render_workspace_graph_navigation_page_markdown(unit))
    return {
        "payload": payload,
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
        "navigation_root": str(navigation_root),
        "navigation_index_path": str(navigation_index_path),
        "navigation_page_count": len(payload.get("unit_navigation") or []),
    }


def _canonical_knowledge_row(unit: dict[str, Any]) -> dict[str, Any]:
    base_payload = {
        "title": str(unit.get("title") or ""),
        "summary": str(unit.get("summary") or ""),
        "unit_type": str(unit.get("unit_type") or ""),
        "path": str(unit.get("path") or ""),
        "updated_at": str(unit.get("updated_at") or ""),
        "promotion_route": str(unit.get("promotion_route") or ""),
        "tags": [str(item) for item in (unit.get("tags") or []) if str(item).strip()],
    }
    return {
        "knowledge_id": str(unit.get("unit_id") or ""),
        "title": base_payload["title"],
        "summary": base_payload["summary"],
        "source_surface": "canonical_l2",
        "authority_level": "authoritative_canonical",
        "knowledge_state": "trusted",
        "path": base_payload["path"],
        "updated_at": base_payload["updated_at"],
        "provenance_refs": [base_payload["path"]],
        "tags": base_payload["tags"],
        "change_fingerprint": _fingerprint_payload(base_payload),
    }


def _staging_knowledge_state(entry: dict[str, Any]) -> str:
    entry_kind = str(entry.get("entry_kind") or "").strip().lower()
    status = str(entry.get("status") or "").strip().lower()
    title = str(entry.get("title") or "").strip().lower()
    summary = str(entry.get("summary") or "").strip().lower()
    if status == "dismissed":
        return "dismissed"
    if entry_kind == "negative_result" or any(keyword in f"{title} {summary}" for keyword in ("contradiction", "conflict", "mismatch", "failed")):
        return "contradiction_watch"
    return "provisional"


def _staging_knowledge_row(entry: dict[str, Any]) -> dict[str, Any]:
    state = _staging_knowledge_state(entry)
    base_payload = {
        "title": str(entry.get("title") or ""),
        "summary": str(entry.get("summary") or ""),
        "entry_kind": str(entry.get("entry_kind") or ""),
        "status": str(entry.get("status") or ""),
        "path": str(entry.get("path") or ""),
        "updated_at": str(entry.get("updated_at") or ""),
        "topic_slug": str(entry.get("topic_slug") or ""),
        "source_artifact_paths": [str(item) for item in (entry.get("source_artifact_paths") or []) if str(item).strip()],
    }
    return {
        "knowledge_id": str(entry.get("entry_id") or ""),
        "title": base_payload["title"],
        "summary": base_payload["summary"],
        "source_surface": "staging_l2",
        "authority_level": "non_authoritative_staging",
        "knowledge_state": state,
        "path": base_payload["path"],
        "updated_at": base_payload["updated_at"],
        "topic_slug": base_payload["topic_slug"],
        "provenance_refs": [base_payload["path"], *base_payload["source_artifact_paths"]],
        "tags": [str(item) for item in (entry.get("tags") or []) if str(item).strip()],
        "change_fingerprint": _fingerprint_payload(base_payload),
    }


def _previous_knowledge_rows(kernel_root: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(_knowledge_report_path(kernel_root))
    if not isinstance(payload, dict):
        return {}
    rows = payload.get("knowledge_rows")
    if not isinstance(rows, list):
        return {}
    previous: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        knowledge_id = str(row.get("knowledge_id") or "").strip()
        if knowledge_id:
            previous[knowledge_id] = row
    return previous


def build_workspace_knowledge_report(kernel_root: Path) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    canonical_units = load_canonical_units(kernel_root)
    staging_entries = load_staging_entries(kernel_root)
    previous_rows = _previous_knowledge_rows(kernel_root)

    knowledge_rows = [
        _canonical_knowledge_row(unit)
        for unit in canonical_units
    ] + [
        _staging_knowledge_row(entry)
        for entry in staging_entries
    ]
    knowledge_rows = sorted(
        knowledge_rows,
        key=lambda row: (
            str(row.get("authority_level") or ""),
            str(row.get("knowledge_state") or ""),
            str(row.get("title") or ""),
            str(row.get("knowledge_id") or ""),
        ),
    )

    added_count = 0
    updated_count = 0
    unchanged_count = 0
    for row in knowledge_rows:
        knowledge_id = str(row.get("knowledge_id") or "")
        previous = previous_rows.get(knowledge_id)
        previous_fingerprint = str((previous or {}).get("change_fingerprint") or "")
        if not previous:
            row["change_status"] = "added"
            added_count += 1
        elif previous_fingerprint != str(row.get("change_fingerprint") or ""):
            row["change_status"] = "updated"
            updated_count += 1
        else:
            row["change_status"] = "unchanged"
            unchanged_count += 1

    removed_rows = [
        {
            "knowledge_id": knowledge_id,
            "title": str(row.get("title") or ""),
            "authority_level": str(row.get("authority_level") or ""),
        }
        for knowledge_id, row in sorted(previous_rows.items())
        if knowledge_id not in {str(item.get("knowledge_id") or "") for item in knowledge_rows}
    ]

    contradiction_rows = [
        {
            "knowledge_id": str(row.get("knowledge_id") or ""),
            "title": str(row.get("title") or ""),
            "summary": str(row.get("summary") or ""),
            "authority_level": str(row.get("authority_level") or ""),
            "path": str(row.get("path") or ""),
        }
        for row in knowledge_rows
        if str(row.get("knowledge_state") or "") in {"contradiction_watch", "dismissed"}
    ]
    provisional_rows = [
        {
            "knowledge_id": str(row.get("knowledge_id") or ""),
            "title": str(row.get("title") or ""),
            "summary": str(row.get("summary") or ""),
            "authority_level": str(row.get("authority_level") or ""),
            "path": str(row.get("path") or ""),
        }
        for row in knowledge_rows
        if str(row.get("knowledge_state") or "") == "provisional"
    ]

    return {
        "kind": "l2_workspace_knowledge_report",
        "compiler_version": 1,
        "generated_at": now_iso(),
        "source_contract_path": "canonical/L2_COMPILER_PROTOCOL.md",
        "authority_rule": "This report is compiled and non-authoritative. Canonical L2 remains the source of truth; staging content stays explicitly provisional.",
        "summary": {
            "total_rows": len(knowledge_rows),
            "canonical_row_count": sum(1 for row in knowledge_rows if row["authority_level"] == "authoritative_canonical"),
            "staging_row_count": sum(1 for row in knowledge_rows if row["authority_level"] == "non_authoritative_staging"),
            "provisional_row_count": len(provisional_rows),
            "contradiction_row_count": len(contradiction_rows),
        },
        "change_summary": {
            "previous_report_found": bool(previous_rows),
            "added_count": added_count,
            "updated_count": updated_count,
            "unchanged_count": unchanged_count,
            "removed_count": len(removed_rows),
            "removed_rows": removed_rows,
        },
        "navigation_entrypoints": {
            "workspace_memory_map": "canonical/compiled/workspace_memory_map.md",
            "workspace_graph_report": "canonical/compiled/workspace_graph_report.md",
            "derived_navigation_index": "canonical/compiled/derived_navigation/index.md",
            "workspace_staging_manifest": "canonical/staging/workspace_staging_manifest.md",
        },
        "provisional_rows": provisional_rows,
        "contradiction_rows": contradiction_rows,
        "knowledge_rows": knowledge_rows,
    }


def render_workspace_knowledge_report_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    change_summary = payload.get("change_summary") or {}
    lines = [
        "# Workspace Knowledge Report",
        "",
        f"- Generated at: `{payload.get('generated_at') or '(missing)'}`",
        f"- Source contract: `{payload.get('source_contract_path') or '(missing)'}`",
        f"- Authority rule: {payload.get('authority_rule') or '(missing)' }",
        f"- Total rows: `{summary.get('total_rows', 0)}`",
        f"- Canonical rows: `{summary.get('canonical_row_count', 0)}`",
        f"- Staging rows: `{summary.get('staging_row_count', 0)}`",
        f"- Provisional rows: `{summary.get('provisional_row_count', 0)}`",
        f"- Contradiction rows: `{summary.get('contradiction_row_count', 0)}`",
        "",
        "## Change Summary",
        "",
        f"- Previous report found: `{change_summary.get('previous_report_found', False)}`",
        f"- Added: `{change_summary.get('added_count', 0)}`",
        f"- Updated: `{change_summary.get('updated_count', 0)}`",
        f"- Unchanged: `{change_summary.get('unchanged_count', 0)}`",
        f"- Removed: `{change_summary.get('removed_count', 0)}`",
        "",
        "## Navigation Entry Points",
        "",
    ]
    for key, value in sorted((payload.get("navigation_entrypoints") or {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Provisional Knowledge", ""])
    provisional_rows = payload.get("provisional_rows") or []
    if not provisional_rows:
        lines.append("- `(none)`")
    for row in provisional_rows:
        lines.append(f"- `{row.get('knowledge_id')}` {row.get('title')} (`{row.get('authority_level')}`)")
    lines.extend(["", "## Contradiction Watch", ""])
    contradiction_rows = payload.get("contradiction_rows") or []
    if not contradiction_rows:
        lines.append("- `(none)`")
    for row in contradiction_rows:
        lines.append(f"- `{row.get('knowledge_id')}` {row.get('title')} (`{row.get('authority_level')}`)")
    lines.extend(["", "## Knowledge Rows", ""])
    for row in payload.get("knowledge_rows") or []:
        lines.append(
            f"- `{row.get('knowledge_id')}` {row.get('title')} "
            f"[{row.get('authority_level')}/{row.get('knowledge_state')}/{row.get('change_status')}] "
            f"`{row.get('path')}`"
        )
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def materialize_workspace_knowledge_report(kernel_root: Path) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    compiled_root = _compiled_root(kernel_root)
    memory_map = materialize_workspace_memory_map(kernel_root)
    graph_report = materialize_workspace_graph_report(kernel_root)
    staging_manifest = materialize_workspace_staging_manifest(kernel_root)
    payload = build_workspace_knowledge_report(kernel_root)
    json_path = _knowledge_report_path(kernel_root)
    markdown_path = _knowledge_report_markdown_path(kernel_root)
    write_json(json_path, payload)
    write_text(markdown_path, render_workspace_knowledge_report_markdown(payload))
    return {
        "payload": payload,
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
        "supporting_artifacts": {
            "workspace_memory_map": memory_map["markdown_path"],
            "workspace_graph_report": graph_report["markdown_path"],
            "derived_navigation_index": graph_report["navigation_index_path"],
            "workspace_staging_manifest": staging_manifest["markdown_path"],
        },
    }


def _normalize_path_string(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _topic_source_anchors(kernel_root: Path, topic_slug: str) -> list[dict[str, Any]]:
    source_root = kernel_root / "topics" / topic_slug / "L0" / "sources"
    rows: list[dict[str, Any]] = []
    if not source_root.exists():
        return rows

    for source_json_path in sorted(source_root.rglob("source.json")):
        payload = read_json(source_json_path)
        if not isinstance(payload, dict):
            continue
        source_id = str(payload.get("source_id") or "").strip()
        title = str(payload.get("title") or "").strip()
        if not source_id or not title:
            continue
        source_slug = str(source_json_path.parent.name or "").strip()
        rows.append(
            {
                "source_id": source_id,
                "source_slug": source_slug,
                "title": title,
                "summary": str(payload.get("summary") or "").strip(),
                "source_type": str(payload.get("source_type") or "").strip(),
                "path": relative_to_root(source_json_path, kernel_root),
            }
        )
    return rows


def _topic_source_anchor_maps(source_anchors: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    by_id: dict[str, str] = {}
    by_slug: dict[str, str] = {}
    by_path: dict[str, str] = {}
    by_directory: dict[str, str] = {}

    for row in source_anchors:
        source_id = str(row.get("source_id") or "").strip()
        source_slug = str(row.get("source_slug") or "").strip()
        normalized_path = _normalize_path_string(row.get("path"))
        if source_id:
            by_id[source_id] = source_id
        if source_slug:
            by_slug[source_slug] = source_id
        if normalized_path:
            by_path[normalized_path] = source_id
            by_directory[str(Path(normalized_path).parent).replace("\\", "/")] = source_id

    return {
        "by_id": by_id,
        "by_slug": by_slug,
        "by_path": by_path,
        "by_directory": by_directory,
    }


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _resolve_topic_entry_source_anchors(entry: dict[str, Any], source_maps: dict[str, dict[str, str]]) -> list[str]:
    source_ids: list[str] = []

    def _append(source_id: str) -> None:
        normalized = str(source_id or "").strip()
        if normalized:
            source_ids.append(normalized)

    for raw_path in entry.get("source_artifact_paths") or []:
        normalized_path = _normalize_path_string(raw_path)
        if not normalized_path:
            continue
        resolved = (source_maps.get("by_path") or {}).get(normalized_path)
        if resolved:
            _append(resolved)
            continue
        resolved = (source_maps.get("by_directory") or {}).get(str(Path(normalized_path).parent).replace("\\", "/"))
        if resolved:
            _append(resolved)

    provenance = entry.get("provenance") or {}
    provenance_source_id = str(provenance.get("source_id") or "").strip()
    if provenance_source_id and provenance_source_id in (source_maps.get("by_id") or {}):
        _append(provenance_source_id)
    provenance_source_slug = str(provenance.get("source_slug") or "").strip()
    if provenance_source_slug and provenance_source_slug in (source_maps.get("by_slug") or {}):
        _append((source_maps.get("by_slug") or {})[provenance_source_slug])

    for source_ref in entry.get("source_refs") or []:
        normalized_ref = str(source_ref or "").strip()
        if not normalized_ref:
            continue
        if normalized_ref in (source_maps.get("by_id") or {}):
            _append(normalized_ref)
            continue
        normalized_ref_path = _normalize_path_string(normalized_ref)
        if normalized_ref_path in (source_maps.get("by_path") or {}):
            _append((source_maps.get("by_path") or {})[normalized_ref_path])
            continue
        normalized_directory = str(Path(normalized_ref_path).parent).replace("\\", "/")
        if normalized_directory in (source_maps.get("by_directory") or {}):
            _append((source_maps.get("by_directory") or {})[normalized_directory])

    for tag in entry.get("tags") or []:
        normalized_tag = str(tag or "").strip()
        if normalized_tag.startswith("source:"):
            source_slug = normalized_tag.split(":", 1)[1].strip()
            resolved = (source_maps.get("by_slug") or {}).get(source_slug)
            if resolved:
                _append(resolved)

    return _dedupe_preserve_order(source_ids)


def _topic_focus_tags(entry: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    for raw_tag in entry.get("tags") or []:
        normalized = str(raw_tag or "").strip().lower()
        if not normalized:
            continue
        if any(normalized.startswith(prefix) for prefix in IGNORED_FOCUS_TAG_PREFIXES):
            continue
        tags.append(normalized)
    return _dedupe_preserve_order(tags)


def _topic_entry_nodes(kernel_root: Path, topic_slug: str, source_anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_maps = _topic_source_anchor_maps(source_anchors)
    nodes: list[dict[str, Any]] = []
    for entry in load_staging_entries(kernel_root):
        if str(entry.get("topic_slug") or "").strip() != topic_slug:
            continue
        source_anchor_ids = _resolve_topic_entry_source_anchors(entry, source_maps)
        nodes.append(
            {
                "entry_id": str(entry.get("entry_id") or ""),
                "entry_kind": str(entry.get("entry_kind") or ""),
                "title": str(entry.get("title") or ""),
                "summary": str(entry.get("summary") or ""),
                "status": str(entry.get("status") or ""),
                "path": str(entry.get("path") or ""),
                "source_anchor_ids": source_anchor_ids,
                "source_anchor_count": len(source_anchor_ids),
                "focus_tags": _topic_focus_tags(entry),
                "linked_unit_ids": [str(item).strip() for item in (entry.get("linked_unit_ids") or []) if str(item).strip()],
                "contradicts_unit_ids": [str(item).strip() for item in (entry.get("contradicts_unit_ids") or []) if str(item).strip()],
                "updated_at": str(entry.get("updated_at") or ""),
            }
        )
    return sorted(nodes, key=lambda row: (row["entry_kind"], row["title"], row["entry_id"]))


def _append_topic_edge(
    edges: list[dict[str, Any]],
    seen: set[tuple[str, str, str]],
    *,
    relation: str,
    from_id: str,
    to_id: str,
    symmetric: bool = False,
    notes: str = "",
) -> None:
    normalized_from = str(from_id or "").strip()
    normalized_to = str(to_id or "").strip()
    if not normalized_from or not normalized_to or normalized_from == normalized_to:
        return
    if symmetric:
        normalized_from, normalized_to = sorted([normalized_from, normalized_to])
    key = (relation, normalized_from, normalized_to)
    if key in seen:
        return
    seen.add(key)
    edges.append(
        {
            "relation": relation,
            "from_id": normalized_from,
            "to_id": normalized_to,
            "notes": notes,
        }
    )


def build_topic_l2_corpus_baseline(kernel_root: Path, *, topic_slug: str) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    source_anchors = _topic_source_anchors(kernel_root, topic_slug)
    entry_nodes = _topic_entry_nodes(kernel_root, topic_slug, source_anchors)
    entry_by_id = {row["entry_id"]: row for row in entry_nodes}
    source_by_id = {row["source_id"]: row for row in source_anchors}

    edges: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str]] = set()

    source_to_entries: dict[str, list[str]] = {}
    tag_to_entries: dict[str, list[str]] = {}
    for entry in entry_nodes:
        entry_id = str(entry.get("entry_id") or "")
        for source_id in entry.get("source_anchor_ids") or []:
            if source_id not in source_by_id:
                continue
            source_to_entries.setdefault(source_id, []).append(entry_id)
            _append_topic_edge(
                edges,
                seen_edges,
                relation="supported_by_source",
                from_id=entry_id,
                to_id=source_id,
                notes=f"Source anchor `{source_id}` supports this topic entry.",
            )
        for focus_tag in entry.get("focus_tags") or []:
            tag_to_entries.setdefault(focus_tag, []).append(entry_id)
        for linked_unit_id in entry.get("linked_unit_ids") or []:
            if linked_unit_id in entry_by_id:
                _append_topic_edge(
                    edges,
                    seen_edges,
                    relation="linked_entry",
                    from_id=entry_id,
                    to_id=linked_unit_id,
                    notes="Explicit topic-local staging link.",
                )
        for contradicts_unit_id in entry.get("contradicts_unit_ids") or []:
            if contradicts_unit_id in entry_by_id:
                _append_topic_edge(
                    edges,
                    seen_edges,
                    relation="contradicts_entry",
                    from_id=entry_id,
                    to_id=contradicts_unit_id,
                    notes="Explicit topic-local contradiction link.",
                )

    for source_id, entry_ids in sorted(source_to_entries.items()):
        deduped_entry_ids = _dedupe_preserve_order(entry_ids)
        for index, left_id in enumerate(deduped_entry_ids):
            for right_id in deduped_entry_ids[index + 1 :]:
                _append_topic_edge(
                    edges,
                    seen_edges,
                    relation="shares_source_anchor",
                    from_id=left_id,
                    to_id=right_id,
                    symmetric=True,
                    notes=f"Both entries resolve to source anchor `{source_id}`.",
                )

    for focus_tag, entry_ids in sorted(tag_to_entries.items()):
        deduped_entry_ids = _dedupe_preserve_order(entry_ids)
        if len(deduped_entry_ids) < 2:
            continue
        for index, left_id in enumerate(deduped_entry_ids):
            for right_id in deduped_entry_ids[index + 1 :]:
                _append_topic_edge(
                    edges,
                    seen_edges,
                    relation="shares_focus_tag",
                    from_id=left_id,
                    to_id=right_id,
                    symmetric=True,
                    notes=f"Both entries carry focus tag `{focus_tag}`.",
                )

    degree_by_entry: dict[str, int] = {row["entry_id"]: 0 for row in entry_nodes}
    attached_entries_by_source: dict[str, set[str]] = {row["source_id"]: set() for row in source_anchors}
    relation_clusters: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        relation = str(edge.get("relation") or "unknown")
        relation_clusters.setdefault(relation, []).append(edge)
        from_id = str(edge.get("from_id") or "")
        to_id = str(edge.get("to_id") or "")
        if from_id in degree_by_entry:
            degree_by_entry[from_id] += 1
        if to_id in degree_by_entry:
            degree_by_entry[to_id] += 1
        if relation == "supported_by_source" and to_id in attached_entries_by_source:
            attached_entries_by_source[to_id].add(from_id)

    for row in entry_nodes:
        row["degree"] = int(degree_by_entry.get(row["entry_id"], 0))

    for row in source_anchors:
        attached_entry_ids = sorted(attached_entries_by_source.get(row["source_id"], set()))
        row["attached_entry_ids"] = attached_entry_ids
        row["attached_entry_count"] = len(attached_entry_ids)

    entry_hubs = sorted(
        [
            {
                "entry_id": row["entry_id"],
                "entry_kind": row["entry_kind"],
                "title": row["title"],
                "degree": row["degree"],
                "source_anchor_count": row["source_anchor_count"],
                "focus_tags": row["focus_tags"],
                "path": row["path"],
            }
            for row in entry_nodes
        ],
        key=lambda row: (-int(row["degree"]), -int(row["source_anchor_count"]), row["entry_kind"], row["title"]),
    )
    isolated_entries = [
        {
            "entry_id": row["entry_id"],
            "entry_kind": row["entry_kind"],
            "title": row["title"],
            "path": row["path"],
        }
        for row in entry_nodes
        if int(row.get("degree") or 0) == 0
    ]

    entry_kind_counts: dict[str, int] = {}
    for row in entry_nodes:
        entry_kind = str(row.get("entry_kind") or "unknown")
        entry_kind_counts[entry_kind] = entry_kind_counts.get(entry_kind, 0) + 1

    relation_rows = [
        {
            "relation": relation,
            "count": len(rows),
            "example_edges": rows[:8],
        }
        for relation, rows in sorted(relation_clusters.items(), key=lambda item: (-len(item[1]), item[0]))
    ]

    return {
        "kind": "topic_l2_corpus_baseline",
        "compiler_version": 1,
        "generated_at": now_iso(),
        "source_contract_path": "canonical/L2_COMPILER_PROTOCOL.md",
        "authority_rule": (
            "This baseline is compiled and non-authoritative. Topic-local staging entries remain provisional; "
            "registered source anchors are provenance support, not promoted L2 claims."
        ),
        "topic_slug": topic_slug,
        "summary": {
            "topic_entry_count": len(entry_nodes),
            "entry_kind_counts": dict(sorted(entry_kind_counts.items())),
            "source_anchor_count": len(source_anchors),
            "source_backed_entry_count": sum(1 for row in entry_nodes if int(row.get("source_anchor_count") or 0) > 0),
            "multi_source_entry_count": sum(1 for row in entry_nodes if int(row.get("source_anchor_count") or 0) > 1),
            "derived_edge_count": len(edges),
            "connected_entry_count": sum(1 for row in entry_nodes if int(row.get("degree") or 0) > 0),
            "isolated_entry_count": len(isolated_entries),
            "bridge_note_count": entry_kind_counts.get("bridge_note", 0),
            "warning_note_count": entry_kind_counts.get("warning_note", 0),
        },
        "topic_entries": entry_nodes,
        "source_anchors": sorted(source_anchors, key=lambda row: (-int(row["attached_entry_count"]), row["title"], row["source_id"])),
        "relation_clusters": relation_rows,
        "derived_edges": edges,
        "entry_hubs": entry_hubs[:10],
        "isolated_entries": isolated_entries,
    }


def render_topic_l2_corpus_baseline_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Topic L2 Corpus Baseline",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Generated at: `{payload.get('generated_at') or '(missing)'}`",
        f"- Authority rule: {payload.get('authority_rule') or '(missing)' }",
        f"- Topic entries: `{summary.get('topic_entry_count', 0)}`",
        f"- Source anchors: `{summary.get('source_anchor_count', 0)}`",
        f"- Source-backed entries: `{summary.get('source_backed_entry_count', 0)}`",
        f"- Multi-source entries: `{summary.get('multi_source_entry_count', 0)}`",
        f"- Derived edges: `{summary.get('derived_edge_count', 0)}`",
        f"- Connected entries: `{summary.get('connected_entry_count', 0)}`",
        f"- Isolated entries: `{summary.get('isolated_entry_count', 0)}`",
        f"- Bridge notes: `{summary.get('bridge_note_count', 0)}`",
        f"- Warning notes: `{summary.get('warning_note_count', 0)}`",
        "",
        "## Entry Kinds",
        "",
    ]
    entry_kind_counts = summary.get("entry_kind_counts") or {}
    if entry_kind_counts:
        for entry_kind, count in entry_kind_counts.items():
            lines.append(f"- `{entry_kind}`: `{count}`")
    else:
        lines.append("- `(none)`")

    lines.extend(["", "## Entry Hubs", ""])
    entry_hubs = payload.get("entry_hubs") or []
    if not entry_hubs:
        lines.append("- `(none)`")
    for row in entry_hubs:
        lines.append(
            f"- `{row.get('entry_id')}` {row.get('title')} "
            f"(kind=`{row.get('entry_kind')}`, degree=`{row.get('degree', 0)}`, source_anchors=`{row.get('source_anchor_count', 0)}`)"
        )

    lines.extend(["", "## Relation Clusters", ""])
    relation_clusters = payload.get("relation_clusters") or []
    if not relation_clusters:
        lines.append("- `(none)`")
    for cluster in relation_clusters:
        lines.append(f"### `{cluster.get('relation')}` (`{cluster.get('count', 0)}`)")
        for edge in cluster.get("example_edges") or []:
            lines.append(f"- `{edge.get('from_id')}` -> `{edge.get('to_id')}`")
        lines.append("")

    lines.extend(["## Source Anchors", ""])
    source_anchors = payload.get("source_anchors") or []
    if not source_anchors:
        lines.append("- `(none)`")
    for row in source_anchors:
        lines.append(
            f"- `{row.get('source_id')}` {row.get('title')} "
            f"(attached_entries=`{row.get('attached_entry_count', 0)}`) `{row.get('path')}`"
        )

    lines.extend(["", "## Isolated Entries", ""])
    isolated_entries = payload.get("isolated_entries") or []
    if not isolated_entries:
        lines.append("- `(none)`")
    for row in isolated_entries:
        lines.append(
            f"- `{row.get('entry_id')}` {row.get('title')} "
            f"(kind=`{row.get('entry_kind')}`) `{row.get('path')}`"
        )
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def materialize_topic_l2_corpus_baseline(kernel_root: Path, *, topic_slug: str) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    payload = build_topic_l2_corpus_baseline(kernel_root, topic_slug=topic_slug)
    json_path = _topic_corpus_baseline_path(kernel_root, topic_slug, "json")
    markdown_path = _topic_corpus_baseline_path(kernel_root, topic_slug, "md")
    write_json(json_path, payload)
    write_text(markdown_path, render_topic_l2_corpus_baseline_markdown(payload))
    return {
        "payload": payload,
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
    }
