"""Read-only manifests for noncanonical AITP workspace stores."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from brain.v5.markdown import read_md, write_text_atomic
from brain.v5.paths import WorkspacePaths


NONCANONICAL_STORE_LABELS = ("workspace_root_store", "workspace_root_nested_store")


def build_workspace_old_store_manifest(
    ws: WorkspacePaths,
    *,
    workspace_root: str | Path | None = None,
) -> dict[str, Any]:
    """Return a file-level manifest for noncanonical root-local stores."""

    root = Path(workspace_root).resolve() if workspace_root else _infer_workspace_root(ws.base)
    stores = [
        _store_manifest("workspace_root_store", root / ".aitp"),
        _store_manifest("workspace_root_nested_store", root / ".aitp" / ".aitp"),
    ]
    topic_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    total_files = 0
    total_bytes = 0
    for store in stores:
        total_files += int(store["file_count"])
        total_bytes += int(store["total_bytes"])
        category_counts.update(store["category_counts"])
        topic_counts.update(store["topic_file_counts"])

    return {
        "kind": "aitp_workspace_old_store_manifest",
        "workspace_root": str(root),
        "canonical_topics_root": str(ws.base.resolve()),
        "canonical_store": str(ws.root.resolve()),
        "stores": stores,
        "summary": {
            "store_count": len(stores),
            "existing_store_count": sum(1 for store in stores if store["exists"]),
            "file_count": total_files,
            "total_bytes": total_bytes,
            "category_counts": dict(sorted(category_counts.items())),
            "topic_file_counts": dict(sorted(topic_counts.items())),
            "old_store_retirement_safe": False,
            "old_store_retirement_requires_manifest_archive": total_files > 0,
        },
        "retirement_rule": (
            "Do not delete root-local .aitp stores until this manifest, the workspace migration plan, "
            "and per-topic import/archive decisions are preserved under the canonical migrations directory."
        ),
        "truth_source": "filesystem_manifest",
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def render_workspace_old_store_manifest_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# AITP Old Store Manifest",
        "",
        "This is a read-only file manifest for noncanonical workspace stores.",
        "",
        f"- Workspace root: `{payload.get('workspace_root', '')}`",
        f"- Canonical topics root: `{payload.get('canonical_topics_root', '')}`",
        f"- Manifested files: `{summary.get('file_count', 0)}`",
        f"- Old store retirement safe now: `{str(summary.get('old_store_retirement_safe', False)).lower()}`",
        "",
        "## Stores",
        "",
        "| Store | Exists | Files | Bytes | Registry Records | L2 Memory Entries | Topic Shell Files | Sessions | Path |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for store in payload.get("stores", []):
        if not isinstance(store, dict):
            continue
        categories = store.get("category_counts") if isinstance(store.get("category_counts"), dict) else {}
        lines.append(
            "| {label} | {exists} | {files} | {bytes} | {registry} | {memory} | {topics} | {sessions} | `{path}` |".format(
                label=store.get("label", ""),
                exists=str(store.get("exists", False)).lower(),
                files=store.get("file_count", 0),
                bytes=store.get("total_bytes", 0),
                registry=categories.get("registry_record", 0),
                memory=categories.get("memory_entry", 0),
                topics=categories.get("topic_shell", 0),
                sessions=categories.get("runtime_session", 0),
                path=store.get("path", ""),
            )
        )
    lines.extend(
        [
            "",
            "## Topic File Counts",
            "",
            "| Topic | Files |",
            "|---|---:|",
        ]
    )
    for topic, count in (summary.get("topic_file_counts") or {}).items():
        lines.append(f"| {topic} | {count} |")
    lines.extend(
        [
            "",
            "## Rule",
            "",
            f"- {payload.get('retirement_rule', '')}",
            "",
        ]
    )
    return "\n".join(lines)


def write_workspace_old_store_manifest_report(payload: dict[str, Any], path: str | Path) -> Path:
    report_path = Path(path)
    write_text_atomic(report_path, render_workspace_old_store_manifest_markdown(payload))
    return report_path


def _store_manifest(label: str, path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    files: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    topic_file_counts: Counter[str] = Counter()
    if resolved.exists():
        for item in sorted((p for p in resolved.rglob("*") if p.is_file()), key=lambda p: p.as_posix()):
            if label == "workspace_root_store" and _is_under_nested_store(resolved, item):
                continue
            entry = _file_entry(resolved, item)
            files.append(entry)
            category_counts[entry["category"]] += 1
            topic_id = entry.get("topic_id")
            if topic_id:
                topic_file_counts[str(topic_id)] += 1
    return {
        "label": label,
        "path": str(resolved),
        "exists": resolved.exists(),
        "file_count": len(files),
        "total_bytes": sum(int(item["size_bytes"]) for item in files),
        "category_counts": dict(sorted(category_counts.items())),
        "topic_file_counts": dict(sorted(topic_file_counts.items())),
        "files": files,
    }


def _file_entry(store: Path, path: Path) -> dict[str, Any]:
    rel = path.relative_to(store).as_posix()
    frontmatter: dict[str, Any] = {}
    if path.suffix.lower() == ".md":
        try:
            frontmatter, _body = read_md(path)
        except UnicodeDecodeError:
            frontmatter = {}
    category, family, topic_hint = _classify_path(rel)
    topic_id = str(frontmatter.get("topic_id") or frontmatter.get("source_topic_id") or topic_hint or "")
    return {
        "path": rel,
        "category": category,
        "registry_family": family,
        "topic_id": topic_id,
        "session_id": _session_id(rel),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
        "summary_inputs_trusted": False,
    }


def _classify_path(rel: str) -> tuple[str, str, str]:
    parts = rel.split("/")
    if len(parts) >= 3 and parts[0] == "registry":
        return "registry_record", parts[1], ""
    if len(parts) >= 2 and parts[0] == "topics":
        return "topic_shell", "", parts[1]
    if len(parts) >= 3 and parts[0] == "runtime" and parts[1] == "sessions":
        return "runtime_session", "", ""
    if len(parts) >= 3 and parts[0] == "memory" and parts[1] == "l2" and parts[2] == "entries":
        return "memory_entry", "memory_entries", ""
    if parts and parts[0] == "surfaces":
        return "derived_surface", "", ""
    if parts and parts[0] == "migrations":
        return "migration_artifact", "", ""
    if parts and parts[0] == "runtime":
        return "runtime_artifact", "", ""
    return "store_metadata", "", ""


def _session_id(rel: str) -> str:
    parts = rel.split("/")
    if len(parts) >= 3 and parts[0] == "runtime" and parts[1] == "sessions":
        return Path(parts[-1]).stem
    return ""


def _is_under_nested_store(store: Path, path: Path) -> bool:
    try:
        rel = path.relative_to(store).as_posix()
    except ValueError:
        return False
    return rel.startswith(".aitp/")


def _infer_workspace_root(base: Path) -> Path:
    resolved = base.resolve()
    if resolved.name == "aitp-topics" and resolved.parent.name == "research":
        return resolved.parent.parent
    return resolved


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
