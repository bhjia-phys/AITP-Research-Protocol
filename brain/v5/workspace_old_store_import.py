"""Controlled import of typed records from noncanonical workspace stores."""

from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from brain.v5.markdown import write_text_atomic
from brain.v5.paths import WorkspacePaths
from brain.v5.workspace_migration_discovery import latest_workspace_old_store_manifest
from brain.v5.workspace_old_store_manifest import build_workspace_old_store_manifest


_IMPORTABLE_CATEGORIES = {"memory_entry", "registry_record", "runtime_session", "topic_shell"}


def build_workspace_old_store_import_plan(
    ws: WorkspacePaths,
    *,
    workspace_root: str | Path | None = None,
    old_store_manifest_path: str | Path | None = None,
    topics: list[str] | None = None,
) -> dict[str, Any]:
    """Plan a conservative copy of old-store typed files into the canonical store."""

    manifest_path = Path(old_store_manifest_path) if old_store_manifest_path else latest_workspace_old_store_manifest(ws)
    manifest = _load_json(manifest_path) if manifest_path else build_workspace_old_store_manifest(
        ws,
        workspace_root=workspace_root,
    )
    selected_topics = [topic for topic in (topics or []) if topic]
    selected = set(selected_topics)
    actions: list[dict[str, Any]] = []
    for store in manifest.get("stores", []):
        if not isinstance(store, dict):
            continue
        source_store = Path(str(store.get("path") or ""))
        for item in store.get("files", []):
            if not isinstance(item, dict):
                continue
            topic_id = str(item.get("topic_id") or "")
            if selected and topic_id not in selected:
                continue
            actions.append(_file_import_action(ws, source_store=source_store, store=store, item=item))

    status_counts = Counter(str(item["status"]) for item in actions)
    importable = [item for item in actions if item["importable"]]
    return {
        "kind": "aitp_workspace_old_store_import_result",
        "mode": "plan",
        "apply_policy": "copy_would_import_only_never_overwrite_conflicts",
        "workspace_root": str(manifest.get("workspace_root") or ""),
        "canonical_topics_root": str(ws.base),
        "canonical_store": str(ws.root),
        "old_store_manifest_source": str(manifest_path or "generated_workspace_old_store_manifest"),
        "topics": selected_topics,
        "summary": {
            "action_count": len(actions),
            "importable_count": len(importable),
            "would_import_count": status_counts.get("would_import", 0),
            "imported_count": 0,
            "already_present_count": status_counts.get("already_present_same_hash", 0),
            "conflict_count": status_counts.get("conflict_existing_different_hash", 0),
            "archive_only_count": status_counts.get("archive_only", 0),
            "requires_semantic_l2_reassignment_count": status_counts.get("requires_semantic_l2_reassignment", 0),
            "status_counts": dict(sorted(status_counts.items())),
            "selected_topic_count": len(selected_topics),
            "safe_to_apply": status_counts.get("conflict_existing_different_hash", 0) == 0,
        },
        "actions": actions,
        "truth_source": "old_store_manifest_and_canonical_file_hashes",
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def apply_workspace_old_store_import_plan(payload: dict[str, Any]) -> dict[str, Any]:
    """Apply a previously built old-store import plan without overwriting conflicts."""

    actions: list[dict[str, Any]] = []
    for action in payload.get("actions", []):
        if not isinstance(action, dict):
            continue
        updated = dict(action)
        if action.get("status") == "would_import" and action.get("importable"):
            source = Path(str(action.get("source_abs_path") or ""))
            target = Path(str(action.get("target_abs_path") or ""))
            if target.exists():
                updated["status"] = "already_present_same_hash" if _sha256(target) == action.get("sha256") else "conflict_existing_different_hash"
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                updated["status"] = "imported"
        actions.append(updated)
    status_counts = Counter(str(item["status"]) for item in actions)
    importable = [item for item in actions if item.get("importable")]
    result = {
        **payload,
        "mode": "apply",
        "summary": {
            **(payload.get("summary") if isinstance(payload.get("summary"), dict) else {}),
            "action_count": len(actions),
            "importable_count": len(importable),
            "would_import_count": status_counts.get("would_import", 0),
            "imported_count": status_counts.get("imported", 0),
            "already_present_count": status_counts.get("already_present_same_hash", 0),
            "conflict_count": status_counts.get("conflict_existing_different_hash", 0),
            "archive_only_count": status_counts.get("archive_only", 0),
            "requires_semantic_l2_reassignment_count": status_counts.get("requires_semantic_l2_reassignment", 0),
            "status_counts": dict(sorted(status_counts.items())),
            "safe_to_apply": status_counts.get("conflict_existing_different_hash", 0) == 0,
        },
        "actions": actions,
    }
    return result


def render_workspace_old_store_import_markdown(payload: dict[str, Any], *, max_rows: int = 160) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# AITP Old Store Import Result",
        "",
        "This is a controlled copy/import surface for root-local typed files. It does not update claim trust.",
        "",
        f"- Mode: `{payload.get('mode', '')}`",
        f"- Canonical topics root: `{payload.get('canonical_topics_root', '')}`",
        f"- Actions: `{summary.get('action_count', 0)}`",
        f"- Importable: `{summary.get('importable_count', 0)}`",
        f"- Imported: `{summary.get('imported_count', 0)}`",
        f"- Would import: `{summary.get('would_import_count', 0)}`",
        f"- Conflicts: `{summary.get('conflict_count', 0)}`",
        f"- Requires semantic L2 reassignment: `{summary.get('requires_semantic_l2_reassignment_count', 0)}`",
        f"- Safe to apply: `{str(summary.get('safe_to_apply', False)).lower()}`",
        f"- Apply policy: `{payload.get('apply_policy', 'copy_would_import_only_never_overwrite_conflicts')}`",
        "",
        "## Status Counts",
        "",
    ]
    for key, value in (summary.get("status_counts") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Actions",
            "",
            "| Topic | Status | Category | Source | Target |",
            "|---|---|---|---|---|",
        ]
    )
    for action in payload.get("actions", [])[:max_rows]:
        if not isinstance(action, dict):
            continue
        lines.append(
            "| {topic} | {status} | {category} | `{source}` | `{target}` |".format(
                topic=_cell(action.get("topic_id", "")),
                status=_cell(action.get("status", "")),
                category=_cell(action.get("source_category", "")),
                source=_cell(action.get("source_path", "")),
                target=_cell(action.get("target_rel_path", "")),
            )
        )
    if int(summary.get("action_count") or 0) > max_rows:
        lines.extend(["", f"Showing first `{max_rows}` rows. Use the JSON result for the complete action list."])
    lines.extend(["", "Archive-only rows remain accounted by manifest/hash and are not imported as typed truth.", ""])
    return "\n".join(lines)


def write_workspace_old_store_import_result(
    payload: dict[str, Any],
    *,
    json_path: str | Path | None = None,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    result = dict(payload)
    if json_path:
        path = Path(json_path)
        write_text_atomic(path, json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        result["json_path"] = str(path)
    if report_path:
        path = Path(report_path)
        write_text_atomic(path, render_workspace_old_store_import_markdown(payload))
        result["report_path"] = str(path)
    return result


def _file_import_action(
    ws: WorkspacePaths,
    *,
    source_store: Path,
    store: dict[str, Any],
    item: dict[str, Any],
) -> dict[str, Any]:
    source_path = str(item.get("path") or "")
    category = str(item.get("category") or "")
    source = source_store / source_path
    target_rel = _target_rel_path(item)
    target = ws.root / target_rel if target_rel else None
    importable = bool(target_rel) and category in _IMPORTABLE_CATEGORIES
    status = "archive_only"
    reason = "source category is preserved by manifest/hash, not imported into typed canonical state"
    if _requires_semantic_l2_reassignment(store=store, item=item):
        status = "requires_semantic_l2_reassignment"
        reason = (
            "noncanonical L2 memory entries are global/orientation records; "
            "review, reassign, or archive them before writing typed memory"
        )
        importable = False
    if importable and target is not None:
        if target.exists():
            status = "already_present_same_hash" if _sha256(target) == str(item.get("sha256") or "") else "conflict_existing_different_hash"
            reason = "canonical target already exists"
        else:
            status = "would_import"
            reason = "canonical target is absent and source category is importable"
    return {
        "source_store_label": str(store.get("label") or ""),
        "source_store_path": str(store.get("path") or ""),
        "source_path": source_path,
        "source_abs_path": str(source),
        "source_category": category,
        "registry_family": str(item.get("registry_family") or ""),
        "topic_id": str(item.get("topic_id") or ""),
        "session_id": str(item.get("session_id") or ""),
        "sha256": str(item.get("sha256") or ""),
        "size_bytes": int(item.get("size_bytes") or 0),
        "target_rel_path": target_rel,
        "target_abs_path": str(target) if target is not None else "",
        "importable": importable,
        "status": status,
        "reason": reason,
        "requires_semantic_l2_reassignment": status == "requires_semantic_l2_reassignment",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _requires_semantic_l2_reassignment(*, store: dict[str, Any], item: dict[str, Any]) -> bool:
    label = str(store.get("label") or "")
    source_path = str(item.get("path") or "").replace("\\", "/")
    return (
        label in {"workspace_root_store", "workspace_root_nested_store"}
        and str(item.get("category") or "") == "memory_entry"
        and source_path.startswith("memory/l2/entries/")
    )


def _target_rel_path(item: dict[str, Any]) -> str:
    source_path = str(item.get("path") or "")
    category = str(item.get("category") or "")
    family = str(item.get("registry_family") or "")
    name = Path(source_path).name
    if category == "registry_record" and family:
        return f"registry/{family}/{name}"
    if category == "memory_entry":
        return f"memory/l2/entries/{name}"
    if category == "runtime_session":
        return f"runtime/sessions/{name}"
    if category == "topic_shell" and source_path.startswith("topics/"):
        return source_path
    return ""


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
