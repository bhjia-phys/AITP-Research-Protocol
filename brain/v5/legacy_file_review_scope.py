"""File-level review scope derived from workspace migration ledgers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from brain.v5.paths import WorkspacePaths


FILE_DECISION_FIELDS = (
    "decision_ref",
    "source_family",
    "source_store_label",
    "source_store_path",
    "source_path",
    "topic_id",
    "session_id",
    "registry_family",
    "source_category",
    "target_surface",
    "recommended_decision",
    "review_status",
    "blocks_old_store_retirement",
    "safe_to_auto_import",
    "sha256",
    "size_bytes",
    "decision_reason",
)


def build_workspace_file_review_scope_index(
    ws: WorkspacePaths,
    *,
    ledger_path: str | Path | None = None,
) -> dict[str, Any]:
    """Return per-topic file decision scopes for semantic migration review."""

    path = Path(ledger_path) if ledger_path else latest_workspace_file_migration_ledger(ws)
    if path is None or not path.exists():
        return {
            "ledger_path": "",
            "ledger_status": "ledger_unavailable",
            "topics": {},
        }
    payload = _read_json(path)
    decisions = payload.get("file_decisions")
    if not isinstance(decisions, list):
        return {
            "ledger_path": str(path),
            "ledger_status": "invalid_ledger",
            "topics": {},
        }
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in decisions:
        if not isinstance(item, dict):
            continue
        topic = _decision_topic(item)
        if not topic:
            continue
        grouped.setdefault(topic, []).append(_compact_decision(item))
    return {
        "ledger_path": str(path),
        "ledger_status": "ready",
        "topics": {
            topic: _scope_from_decisions(topic, items, ledger_path=str(path))
            for topic, items in sorted(grouped.items())
        },
    }


def file_review_scope_for_topic(scope_index: dict[str, Any], topic: str) -> dict[str, Any]:
    """Return a typed, empty-safe scope for one topic."""

    status = str(scope_index.get("ledger_status") or "ledger_unavailable")
    ledger_path = str(scope_index.get("ledger_path") or "")
    topics = scope_index.get("topics") if isinstance(scope_index.get("topics"), dict) else {}
    scope = topics.get(topic)
    if isinstance(scope, dict):
        return scope
    return {
        "kind": "legacy_file_review_scope",
        "topic": topic,
        "ledger_path": ledger_path,
        "ledger_status": status,
        "scope_status": "empty" if status == "ready" else status,
        "file_decision_count": 0,
        "blocking_file_count": 0,
        "review_status_counts": {},
        "decision_counts": {},
        "source_family_counts": {},
        "all_file_decision_refs": [],
        "required_review_refs": [],
        "file_decisions": [],
        "truth_source": "workspace_file_migration_ledger",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def latest_workspace_file_migration_ledger(ws: WorkspacePaths) -> Path | None:
    candidates = [
        path
        for path in (ws.root / "migrations").glob("*/workspace_file_migration_ledger.json")
        if path.is_file()
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime_ns)


def _scope_from_decisions(topic: str, decisions: list[dict[str, Any]], *, ledger_path: str) -> dict[str, Any]:
    blocking = [item for item in decisions if item.get("blocks_old_store_retirement") is True]
    return {
        "kind": "legacy_file_review_scope",
        "topic": topic,
        "ledger_path": ledger_path,
        "ledger_status": "ready",
        "scope_status": "ready",
        "file_decision_count": len(decisions),
        "blocking_file_count": len(blocking),
        "review_status_counts": _counts(decisions, "review_status"),
        "decision_counts": _counts(decisions, "recommended_decision"),
        "source_family_counts": _counts(decisions, "source_family"),
        "all_file_decision_refs": _refs(decisions),
        "required_review_refs": _refs(blocking),
        "file_decisions": decisions,
        "truth_source": "workspace_file_migration_ledger",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _compact_decision(item: dict[str, Any]) -> dict[str, Any]:
    result = {field: item.get(field) for field in FILE_DECISION_FIELDS if field in item}
    result["decision_ref"] = str(result.get("decision_ref") or "")
    result["source_path"] = str(result.get("source_path") or "")
    result["review_status"] = str(result.get("review_status") or "")
    result["recommended_decision"] = str(result.get("recommended_decision") or "")
    result["blocks_old_store_retirement"] = bool(result.get("blocks_old_store_retirement") is True)
    result["safe_to_auto_import"] = bool(result.get("safe_to_auto_import") is True)
    result["size_bytes"] = int(result.get("size_bytes") or 0)
    return result


def _decision_topic(item: dict[str, Any]) -> str:
    topic = str(item.get("topic_id") or "").strip()
    if topic:
        return topic
    source_path = str(item.get("source_path") or "").replace("\\", "/").strip("/")
    if "/" in source_path:
        return source_path.split("/", 1)[0]
    return ""


def _refs(decisions: list[dict[str, Any]]) -> list[str]:
    return [
        str(item.get("decision_ref") or "")
        for item in decisions
        if str(item.get("decision_ref") or "")
    ]


def _counts(decisions: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in decisions:
        value = str(item.get(key) or "")
        if value:
            counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}
