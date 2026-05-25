"""Read-only manifest for legacy global L2 graph migration planning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.markdown import read_md
from brain.v5.paths import WorkspacePaths


def build_legacy_l2_graph_manifest(
    ws: WorkspacePaths,
    *,
    legacy_l2_dir: str | Path = "",
) -> dict[str, Any]:
    """Scan legacy L2 files without promoting them into typed memory."""

    l2_dir = Path(legacy_l2_dir) if legacy_l2_dir else ws.base / "research" / "aitp-topics" / "L2"
    if not l2_dir.exists():
        return _empty_manifest(l2_dir, status="missing_legacy_l2_dir")
    entries = _scan_entries(l2_dir / "entries")
    graph_counts = _graph_counts(l2_dir / "graph")
    has_graph = any(graph_counts.values())
    counts = {
        "entries": len(entries),
        **graph_counts,
        "index_files": len(_obsidian_view_targets(l2_dir)),
    }
    return {
        "kind": "legacy_l2_graph_manifest",
        "legacy_l2_dir": str(l2_dir),
        "legacy_shape": "global_l2_graph",
        "typed_migration_status": (
            "needs_typed_l2_migration" if entries or has_graph else "no_legacy_l2_records_found"
        ),
        "counts": counts,
        "entries_by_role": _counts_by(entries, "role"),
        "entries_by_status": _counts_by(entries, "status"),
        "entry_samples": entries[:10],
        "obsidian_view_targets": _obsidian_view_targets(l2_dir),
        "next_actions": _next_actions(entries=entries, has_graph=has_graph),
        "truth_source": "legacy_l2_filesystem",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _empty_manifest(l2_dir: Path, *, status: str) -> dict[str, Any]:
    return {
        "kind": "legacy_l2_graph_manifest",
        "legacy_l2_dir": str(l2_dir),
        "legacy_shape": "missing",
        "typed_migration_status": status,
        "counts": {
            "entries": 0,
            "graph_nodes": 0,
            "graph_edges": 0,
            "graph_steps": 0,
            "graph_towers": 0,
            "index_files": 0,
        },
        "entries_by_role": {},
        "entries_by_status": {},
        "entry_samples": [],
        "obsidian_view_targets": [],
        "next_actions": ["locate_legacy_l2_directory"],
        "truth_source": "legacy_l2_filesystem",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _scan_entries(entries_dir: Path) -> list[dict[str, str]]:
    if not entries_dir.exists():
        return []
    entries: list[dict[str, str]] = []
    for path in sorted(entries_dir.glob("*.md")):
        if path.stem.upper().startswith("INDEX"):
            continue
        frontmatter, _body = read_md(path)
        entry_id = _text(frontmatter.get("entry_id")) or path.stem
        entries.append({
            "entry_id": entry_id,
            "role": _text(frontmatter.get("role")) or "unknown",
            "status": _text(frontmatter.get("status")) or "unknown",
            "lane": _lane_text(frontmatter.get("lane")),
            "path": str(path),
        })
    return entries


def _graph_counts(graph_dir: Path) -> dict[str, int]:
    return {
        "graph_nodes": _md_count(graph_dir / "nodes"),
        "graph_edges": _md_count(graph_dir / "edges"),
        "graph_steps": _md_count(graph_dir / "steps"),
        "graph_towers": _md_count(graph_dir / "towers"),
    }


def _md_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(list(path.glob("*.md")))


def _obsidian_view_targets(l2_dir: Path) -> list[str]:
    candidates = [
        "index.md",
        "entries/INDEX.md",
        "entries/INDEX_status.md",
        "entries/INDEX_pitfalls.md",
        "entries/INDEX_reverse.md",
        "graph/index.html",
    ]
    return [rel for rel in candidates if (l2_dir / rel).exists()]


def _next_actions(*, entries: list[dict[str, str]], has_graph: bool) -> list[str]:
    actions: list[str] = []
    if entries:
        actions.append("migrate_legacy_l2_entries_into_memory_records")
    if has_graph:
        actions.append("migrate_legacy_l2_graph_edges_into_object_relations")
    if entries or has_graph:
        actions.extend([
            "rebuild_l2_obsidian_view_from_typed_graph",
            "keep_legacy_l2_orientation_only_until_typed_migration",
        ])
    if not actions:
        actions.append("locate_legacy_l2_directory")
    return actions


def _counts_by(entries: list[dict[str, str]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        value = entry.get(field) or "unknown"
        counts[value] = counts.get(value, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def _text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _lane_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(_text(item) for item in value if _text(item))
    return _text(value)
