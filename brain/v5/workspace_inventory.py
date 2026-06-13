"""Read-only inventory for mixed legacy/v5 AITP workspaces."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from brain.v5.markdown import read_md, write_text_atomic
from brain.v5.paths import WorkspacePaths


LEGACY_STAGE_DIRS = ("L0", "L1", "L2", "L3", "L4", "L5")
REGISTRY_FAMILIES = (
    "claims",
    "claim_statuses",
    "evidence",
    "artifacts",
    "source_assets",
    "reference_locations",
    "tool_runs",
    "code_states",
    "physics_objects",
    "object_relations",
    "proof_obligations",
    "validation_contracts",
    "validation_results",
    "research_runs",
    "research_run_events",
    "sensemaking_reports",
    "checkpoints",
    "promotion_packets",
    "routes",
    "legacy_semantic_reviews",
    "legacy_semantic_repairs",
    "legacy_source_reconstruction_repairs",
)


def build_workspace_inventory(
    ws: WorkspacePaths,
    *,
    workspace_root: str | Path | None = None,
) -> dict[str, Any]:
    """Return a read-only inventory across canonical and local AITP stores."""

    root = Path(workspace_root).resolve() if workspace_root else _infer_workspace_root(ws.base)
    canonical_base = ws.base.resolve()
    store_specs = _store_specs(root, canonical_base)
    stores = [_store_inventory(label, path, canonical=canonical) for label, path, canonical in store_specs]
    legacy_topics = [_legacy_topic_inventory(path) for path in _legacy_topic_dirs(canonical_base)]
    canonical_store = next((store for store in stores if store["label"] == "canonical_topics_store"), None)
    root_store = next((store for store in stores if store["label"] == "workspace_root_store"), None)
    nested_store = next((store for store in stores if store["label"] == "workspace_root_nested_store"), None)

    topic_rows = _topic_migration_rows(
        legacy_topics=legacy_topics,
        canonical_store=canonical_store,
        root_store=root_store,
        nested_store=nested_store,
    )
    duplicate_topics = sorted(
        topic_id for topic_id, count in Counter(row["topic_id"] for row in topic_rows).items() if count > 1
    )
    root_only_topics = sorted(
        set((root_store or {}).get("topic_ids", []))
        - set((canonical_store or {}).get("topic_ids", []))
    )
    nested_only_topics = sorted(
        set((nested_store or {}).get("topic_ids", []))
        - set((canonical_store or {}).get("topic_ids", []))
    )

    return {
        "kind": "aitp_workspace_inventory",
        "workspace_root": str(root),
        "canonical_topics_root": str(canonical_base),
        "canonical_store": str(ws.root.resolve()),
        "stores": stores,
        "legacy_topics": legacy_topics,
        "topic_migration_rows": topic_rows,
        "summary": {
            "store_count": len(stores),
            "existing_store_count": sum(1 for store in stores if store["exists"]),
            "legacy_topic_count": len(legacy_topics),
            "topic_row_count": len(topic_rows),
            "canonical_v5_topic_count": len((canonical_store or {}).get("topic_ids", [])),
            "root_store_topic_count": len((root_store or {}).get("topic_ids", [])),
            "nested_store_topic_count": len((nested_store or {}).get("topic_ids", [])),
            "root_only_topics": root_only_topics,
            "nested_only_topics": nested_only_topics,
            "duplicate_topic_ids": duplicate_topics,
            "manual_semantic_review_required": True,
            "manual_semantic_review_reason": (
                "Inventory proves structural accounting only. Legacy files, root-local "
                "stores, and generated recovery surfaces still need topic-by-topic semantic review."
            ),
        },
        "truth_source": "filesystem_inventory",
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def render_workspace_inventory_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# AITP Workspace Inventory",
        "",
        "This report is read-only structural accounting. It does not prove semantic migration completeness.",
        "",
        f"- Workspace root: `{payload.get('workspace_root', '')}`",
        f"- Canonical topics root: `{payload.get('canonical_topics_root', '')}`",
        f"- Canonical store: `{payload.get('canonical_store', '')}`",
        "",
        "## Summary",
        "",
    ]
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    for key in [
        "existing_store_count",
        "legacy_topic_count",
        "canonical_v5_topic_count",
        "root_store_topic_count",
        "nested_store_topic_count",
        "topic_row_count",
    ]:
        lines.append(f"- {key}: `{summary.get(key, 0)}`")
    lines.extend(
        [
            f"- root_only_topics: `{', '.join(summary.get('root_only_topics') or []) or 'none'}`",
            f"- nested_only_topics: `{', '.join(summary.get('nested_only_topics') or []) or 'none'}`",
            f"- duplicate_topic_ids: `{', '.join(summary.get('duplicate_topic_ids') or []) or 'none'}`",
            "",
            "## Stores",
            "",
            "| Store | Exists | Topics | Registry Records | Sessions | Path |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for store in payload.get("stores", []):
        if not isinstance(store, dict):
            continue
        lines.append(
            "| {label} | {exists} | {topics} | {records} | {sessions} | `{path}` |".format(
                label=store.get("label", ""),
                exists=str(store.get("exists", False)).lower(),
                topics=store.get("topic_count", 0),
                records=store.get("registry_record_count", 0),
                sessions=store.get("session_count", 0),
                path=store.get("path", ""),
            )
        )
    lines.extend(
        [
            "",
            "## Topic Migration Rows",
            "",
            "| Topic | Legacy | Canonical v5 | Root-local v5 | Nested-root v5 | Legacy Files | Registry Records | Required Action |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload.get("topic_migration_rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {topic} | {legacy} | {canonical} | {root_local} | {nested} | {files} | {records} | {action} |".format(
                topic=row.get("topic_id", ""),
                legacy=str(row.get("legacy_present", False)).lower(),
                canonical=str(row.get("canonical_v5_present", False)).lower(),
                root_local=str(row.get("root_store_present", False)).lower(),
                nested=str(row.get("nested_root_store_present", False)).lower(),
                files=row.get("legacy_file_count", 0),
                records=row.get("canonical_registry_record_count", 0),
                action=row.get("required_action", ""),
            )
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Root-local `.aitp/` and nested `.aitp/.aitp/` stores are not the canonical theory-topic store.",
            "- Canonical durable research state belongs under `research/aitp-topics/.aitp/`.",
            "- Every row marked `semantic_review` or `merge_root_store_topic` must be reviewed before removing old surfaces.",
            "",
        ]
    )
    return "\n".join(lines)


def write_workspace_inventory_report(payload: dict[str, Any], path: str | Path) -> Path:
    report_path = Path(path)
    write_text_atomic(report_path, render_workspace_inventory_markdown(payload))
    return report_path


def _infer_workspace_root(base: Path) -> Path:
    base = base.resolve()
    if base.name == "aitp-topics" and base.parent.name == "research":
        return base.parent.parent
    return base


def _store_specs(root: Path, canonical_base: Path) -> list[tuple[str, Path, bool]]:
    specs = [
        ("canonical_topics_store", canonical_base / ".aitp", True),
        ("workspace_root_store", root / ".aitp", False),
        ("workspace_root_nested_store", root / ".aitp" / ".aitp", False),
    ]
    deduped: list[tuple[str, Path, bool]] = []
    seen: set[Path] = set()
    for label, path, canonical in specs:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append((label, resolved, canonical))
    return deduped


def _store_inventory(label: str, path: Path, *, canonical: bool) -> dict[str, Any]:
    exists = path.exists()
    registry_counts = _registry_counts(path)
    topic_ids = _topic_ids(path)
    session_ids = _session_ids(path)
    topic_record_counts = _registry_topic_counts(path)
    return {
        "label": label,
        "path": str(path),
        "canonical": canonical,
        "exists": exists,
        "workspace_md_exists": (path / "workspace.md").exists(),
        "topic_count": len(topic_ids),
        "topic_ids": topic_ids,
        "session_count": len(session_ids),
        "session_ids": session_ids,
        "registry_counts": registry_counts,
        "registry_record_count": sum(registry_counts.values()),
        "registry_topic_record_counts": dict(sorted(topic_record_counts.items())),
    }


def _registry_counts(store: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    registry = store / "registry"
    for family in REGISTRY_FAMILIES:
        directory = registry / family
        out[family] = len(list(directory.glob("*.md"))) if directory.exists() else 0
    extra_families = []
    if registry.exists():
        extra_families = [
            path.name
            for path in registry.iterdir()
            if path.is_dir() and path.name not in REGISTRY_FAMILIES
        ]
    for family in sorted(extra_families):
        out[family] = len(list((registry / family).glob("*.md")))
    return out


def _registry_topic_counts(store: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    registry = store / "registry"
    if not registry.exists():
        return counts
    for path in registry.glob("*/*.md"):
        frontmatter, _body = read_md(path)
        topic_id = str(frontmatter.get("topic_id") or "").strip()
        if topic_id:
            counts[topic_id] += 1
    return counts


def _topic_ids(store: Path) -> list[str]:
    topics_dir = store / "topics"
    if not topics_dir.exists():
        return []
    return sorted(path.name for path in topics_dir.iterdir() if path.is_dir())


def _session_ids(store: Path) -> list[str]:
    sessions_dir = store / "runtime" / "sessions"
    if not sessions_dir.exists():
        return []
    return sorted(path.stem for path in sessions_dir.glob("*.md"))


def _legacy_topic_dirs(canonical_base: Path) -> list[Path]:
    if not canonical_base.exists():
        return []
    ignored = {".aitp"}
    return sorted(
        path
        for path in canonical_base.iterdir()
        if path.is_dir() and path.name not in ignored and _looks_like_legacy_topic(path)
    )


def _looks_like_legacy_topic(path: Path) -> bool:
    return (
        (path / "state.md").exists()
        or any((path / stage).exists() for stage in LEGACY_STAGE_DIRS)
        or (path / "research.md").exists()
    )


def _legacy_topic_inventory(path: Path) -> dict[str, Any]:
    stage_counts = {
        stage: _count_files(path / stage)
        for stage in LEGACY_STAGE_DIRS
        if (path / stage).exists()
    }
    frontmatter, _body = read_md(path / "state.md")
    return {
        "topic_id": path.name,
        "path": str(path),
        "state_exists": (path / "state.md").exists(),
        "research_md_exists": (path / "research.md").exists(),
        "stage_file_counts": stage_counts,
        "legacy_file_count": _count_files(path),
        "state_stage": str(frontmatter.get("stage") or ""),
        "state_lane": str(frontmatter.get("lane") or ""),
        "state_status": str(frontmatter.get("status") or ""),
    }


def _topic_migration_rows(
    *,
    legacy_topics: list[dict[str, Any]],
    canonical_store: dict[str, Any] | None,
    root_store: dict[str, Any] | None,
    nested_store: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    canonical_ids = set((canonical_store or {}).get("topic_ids", []))
    root_ids = set((root_store or {}).get("topic_ids", []))
    nested_ids = set((nested_store or {}).get("topic_ids", []))
    legacy_by_id = {str(item.get("topic_id")): item for item in legacy_topics}
    all_ids = sorted(set(legacy_by_id) | canonical_ids | root_ids | nested_ids)
    canonical_counts = (canonical_store or {}).get("registry_topic_record_counts", {})

    rows: list[dict[str, Any]] = []
    for topic_id in all_ids:
        legacy = legacy_by_id.get(topic_id, {})
        canonical_present = topic_id in canonical_ids
        root_present = topic_id in root_ids
        nested_present = topic_id in nested_ids
        required_action = _required_action(
            legacy_present=bool(legacy),
            canonical_present=canonical_present,
            root_present=root_present,
            nested_present=nested_present,
            canonical_record_count=int(canonical_counts.get(topic_id) or 0),
        )
        rows.append(
            {
                "topic_id": topic_id,
                "legacy_present": bool(legacy),
                "canonical_v5_present": canonical_present,
                "root_store_present": root_present,
                "nested_root_store_present": nested_present,
                "legacy_file_count": int(legacy.get("legacy_file_count") or 0),
                "legacy_stage_file_counts": legacy.get("stage_file_counts") or {},
                "legacy_state_stage": legacy.get("state_stage") or "",
                "legacy_state_lane": legacy.get("state_lane") or "",
                "canonical_registry_record_count": int(canonical_counts.get(topic_id) or 0),
                "required_action": required_action,
                "semantic_review_required": required_action != "structurally_current",
            }
        )
    return rows


def _required_action(
    *,
    legacy_present: bool,
    canonical_present: bool,
    root_present: bool,
    nested_present: bool,
    canonical_record_count: int,
) -> str:
    if (root_present or nested_present) and not canonical_present:
        return "merge_root_store_topic"
    if legacy_present and not canonical_present:
        return "migrate_legacy_topic"
    if canonical_present and canonical_record_count == 0:
        return "semantic_review_empty_registry"
    if legacy_present and canonical_present:
        return "semantic_review_legacy_vs_v5"
    if root_present or nested_present:
        return "semantic_review_duplicate_store"
    return "structurally_current"


def _count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())
