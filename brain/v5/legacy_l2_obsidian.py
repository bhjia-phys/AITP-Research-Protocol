"""Orientation-only Obsidian views for legacy global L2 graphs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.legacy_l2_graph import build_legacy_l2_graph_manifest
from brain.v5.markdown import read_md, write_md
from brain.v5.paths import WorkspacePaths


def write_legacy_l2_obsidian_view(
    ws: WorkspacePaths,
    *,
    legacy_l2_dir: str | Path = "",
    output_dir: str = "",
) -> dict[str, Any]:
    """Write derived Markdown views over a legacy L2 graph without promoting it."""

    l2_dir = Path(legacy_l2_dir) if legacy_l2_dir else ws.base / "research" / "aitp-topics" / "L2"
    view_dir = Path(output_dir) if output_dir else ws.root / "surfaces" / "legacy_l2_obsidian"
    entries = _scan_entries(l2_dir / "entries")
    manifest = build_legacy_l2_graph_manifest(ws, legacy_l2_dir=l2_dir)
    overview_path = view_dir / "Legacy L2 Overview.md"
    entries_path = view_dir / "Legacy L2 Entries.md"
    write_md(
        overview_path,
        _frontmatter("legacy_l2_overview", str(l2_dir)),
        _overview_body(l2_dir, manifest, entries),
    )
    write_md(
        entries_path,
        _frontmatter("legacy_l2_entries_index", str(l2_dir / "entries")),
        _entries_body(entries),
    )
    return {
        "ok": True,
        "kind": "legacy_l2_obsidian_view_bundle",
        "view_dir": str(view_dir),
        "legacy_l2_dir": str(l2_dir),
        "files": {
            "overview": str(overview_path),
            "entries_index": str(entries_path),
        },
        "legacy_entry_count": len(entries),
        "memory_entry_count": 0,
        "entries_by_role": _counts_by(entries, "role"),
        "entries_by_status": _counts_by(entries, "status"),
        "graph_counts": {
            key: manifest["counts"][key]
            for key in ("graph_nodes", "graph_edges", "graph_steps", "graph_towers")
        },
        "source_records": {
            "legacy_entries": [entry["entry_id"] for entry in entries],
            "memory_entries": [],
        },
        "next_actions": list(manifest["next_actions"]),
        "derived_from": "legacy_l2_filesystem",
        "truth_source": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _frontmatter(role: str, source_id: str) -> dict[str, Any]:
    return {
        "kind": "derived_obsidian_view",
        "view_role": role,
        "source_id": source_id,
        "derived_from": "legacy_l2_filesystem",
        "truth_source": False,
        "orientation_only": True,
        "adapter_rule": "read_for_orientation_then_migrate_into_typed_l2_before_trust_updates",
    }


def _overview_body(l2_dir: Path, manifest: dict[str, Any], entries: list[dict[str, str]]) -> str:
    counts = manifest["counts"]
    lines = [
        "# Legacy L2 Overview",
        "",
        "This is an orientation-only view of the legacy global L2 graph. It is not typed AITP memory.",
        "",
        f"- Legacy L2 dir: `{l2_dir}`",
        f"- Legacy entries: {len(entries)}",
        f"- Graph nodes: {counts['graph_nodes']}",
        f"- Graph edges: {counts['graph_edges']}",
        f"- Graph steps: {counts['graph_steps']}",
        f"- Graph towers: {counts['graph_towers']}",
        "",
        "## Next Actions",
        "",
    ]
    lines.extend(f"- `{action}`" for action in manifest["next_actions"])
    lines.extend([
        "",
        "## Trust Boundary",
        "",
        "Use this view for browsing and triage only. Promote reusable knowledge through typed L2 memory records before trust updates.",
    ])
    return "\n".join(lines) + "\n"


def _entries_body(entries: list[dict[str, str]]) -> str:
    lines = [
        "# Legacy L2 Entries",
        "",
        "This index is orientation-only; legacy entries remain source material until typed migration.",
        "",
        "| Entry | Role | Status | Lane | Source |",
        "|---|---|---|---|---|",
    ]
    if not entries:
        lines.append("| None |  |  |  |  |")
        return "\n".join(lines) + "\n"
    for entry in entries:
        lines.append(
            f"| `{entry['entry_id']}` | {entry['role']} | {entry['status']} | "
            f"{entry['lane']} | `{entry['path']}` |"
        )
    return "\n".join(lines) + "\n"


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
