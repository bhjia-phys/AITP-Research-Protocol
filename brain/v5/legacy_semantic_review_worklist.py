"""Prioritized worklist for legacy semantic review backlog."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.legacy_semantic_review_manifest import build_legacy_semantic_review_manifest
from brain.v5.paths import WorkspacePaths


def build_legacy_semantic_review_worklist(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
) -> dict[str, Any]:
    """Build a read-only prioritized queue for remaining legacy semantic reviews."""

    manifest = build_legacy_semantic_review_manifest(ws, migration_dir=migration_dir)
    candidates = [
        _work_item(item)
        for item in manifest["items"]
        if item["review_status"] in {"pending", "needs_revision", "inconclusive"}
    ]
    items = sorted(candidates, key=lambda item: (-item["priority_score"], item["topic"]))
    return {
        "kind": "legacy_semantic_review_worklist",
        "run_id": manifest["run_id"],
        "migration_dir": manifest["migration_dir"],
        "workspace": manifest["workspace"],
        "work_item_count": len(items),
        "status_counts": _status_counts(items),
        "items": items,
        "next_actions": [f"worklist_item:{item['topic']}" for item in items],
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "truth_source": "legacy_semantic_review_manifest",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _work_item(item: dict[str, Any]) -> dict[str, Any]:
    repair_count = int(item.get("repair_candidate_count") or 0)
    missing = list(item.get("missing_source_components") or _missing_source_components_from_reasons(item))
    focus = _review_focus(item, repair_count=repair_count, missing_components=missing)
    priority_score = _priority_score(item, repair_count=repair_count, missing_components=missing)
    latest = item.get("latest_semantic_review") if isinstance(item.get("latest_semantic_review"), dict) else {}
    return {
        "topic": item["topic"],
        "active_claim_id": item["active_claim_id"],
        "review_status": item["review_status"],
        "review_priority": item["review_priority"],
        "priority_score": priority_score,
        "priority_reasons": _priority_reasons(item, repair_count=repair_count, missing_components=missing),
        "latest_review_id": str(latest.get("review_id") or ""),
        "review_focus": focus,
        "missing_source_components": missing,
        "repair_candidate_count": repair_count,
        "repair_candidates": list(item.get("repair_candidates", [])),
        "packet_cli": item["packet_cli"],
        "result_cli_template": item["result_cli_template"],
        "can_update_claim_trust": False,
    }


def _priority_score(
    item: dict[str, Any],
    *,
    repair_count: int,
    missing_components: list[str],
) -> int:
    score = {
        "needs_revision": 300,
        "inconclusive": 200,
        "pending": 100,
    }.get(str(item.get("review_status")), 0)
    score += {"critical": 80, "high": 50, "medium": 20, "low": 0}.get(str(item.get("review_priority")), 0)
    score += repair_count * 40
    score += len(missing_components) * 5
    if "archive_only_records_require_sampling" in set(item.get("review_reasons", [])):
        score += 10
    return score


def _priority_reasons(
    item: dict[str, Any],
    *,
    repair_count: int,
    missing_components: list[str],
) -> list[str]:
    reasons = [f"review_status:{item['review_status']}", f"review_priority:{item['review_priority']}"]
    if repair_count:
        reasons.append(f"repair_candidates:{repair_count}")
    if missing_components:
        reasons.append(f"missing_source_components:{len(missing_components)}")
    reasons.extend(str(reason) for reason in item.get("review_reasons", []))
    return _unique(reasons)


def _review_focus(
    item: dict[str, Any],
    *,
    repair_count: int,
    missing_components: list[str],
) -> list[str]:
    focus: list[str] = []
    if repair_count:
        focus.append("apply_or_review_typed_repair_candidates")
    if missing_components:
        focus.append("complete_source_reconstruction_components")
    if "archive_only_records_require_sampling" in set(item.get("review_reasons", [])):
        focus.append("sample_archive_reference_readback")
    if item["review_status"] == "pending":
        focus.append("perform_initial_semantic_review")
    if item["review_status"] == "inconclusive":
        focus.append("resolve_inconclusive_semantic_review")
    focus.append("record_next_legacy_semantic_review_result")
    return _unique(focus)


def _missing_source_components_from_reasons(item: dict[str, Any]) -> list[str]:
    source = item.get("source_reconstruction")
    if isinstance(source, dict) and isinstance(source.get("missing_components"), list):
        return [str(value) for value in source["missing_components"]]
    return []


def _status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"needs_revision": 0, "inconclusive": 0, "pending": 0}
    for item in items:
        status = item["review_status"]
        if status in counts:
            counts[status] += 1
    return counts


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
