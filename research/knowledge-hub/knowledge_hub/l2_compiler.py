from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


IGNORED_CANONICAL_DIRS = {"backends", "examples", "compiled", "staging", "__pycache__"}
REUSE_FAMILY_ORDER = (
    ("workflows", "workflow"),
    ("methods", "method"),
    ("warnings", "warning_note"),
    ("validation_patterns", "validation_pattern"),
    ("bridges", "bridge"),
    ("topic_skill_projections", "topic_skill_projection"),
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
