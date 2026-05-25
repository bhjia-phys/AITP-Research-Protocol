"""Batch manifest for legacy semantic review packets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.legacy_semantic_review import build_legacy_semantic_review_queue
from brain.v5.paths import WorkspacePaths


def build_legacy_semantic_review_manifest(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
) -> dict[str, Any]:
    """Build a read-only manifest of per-topic semantic review work."""

    queue = build_legacy_semantic_review_queue(ws, migration_dir=migration_dir)
    migration = str(queue["migration_dir"])
    items = [_manifest_item(ws, migration, item) for item in queue["items"]]
    progress = _progress(items)
    return {
        "kind": "legacy_semantic_review_manifest",
        "run_id": queue["run_id"],
        "migration_dir": migration,
        "workspace": queue["workspace"],
        "topic_count": queue["topic_count"],
        "review_item_count": queue["review_item_count"],
        "priority_counts": queue["priority_counts"],
        "review_progress": progress,
        "pending_count": progress["pending"],
        "passed_count": progress["passed"],
        "needs_revision_count": progress["needs_revision"],
        "inconclusive_count": progress["inconclusive"],
        "items": items,
        "next_actions": _next_actions(items),
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "truth_source": "migration_manifests_and_typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _manifest_item(ws: WorkspacePaths, migration_dir: str, item: dict[str, Any]) -> dict[str, Any]:
    topic = item["topic"]
    status = item["semantic_review_status"].removeprefix("reviewed_")
    if status == item["semantic_review_status"]:
        status = "pending"
    packet_cli = (
        f"aitp-v5 --base {ws.base} legacy semantic-review-packet "
        f"--migration-dir {migration_dir} --topic {topic}"
    )
    result_cli = (
        f"aitp-v5 --base {ws.base} legacy semantic-review-result "
        f"--migration-dir {migration_dir} --topic {topic} --status <passed|needs_revision|inconclusive> "
        "--legacy-ref <ref> --summary <summary>"
    )
    return {
        "topic": topic,
        "active_claim_id": item["active_claim_id"],
        "review_status": status,
        "review_priority": item["review_priority"],
        "review_reasons": item["review_reasons"],
        "recommended_actions": item["recommended_actions"],
        "packet_cli": packet_cli,
        "result_cli_template": result_cli,
        "packet_mcp": "aitp_v5_build_legacy_semantic_review_packet",
        "result_mcp": "aitp_v5_record_legacy_semantic_review_result",
        "can_update_claim_trust": False,
    }


def _progress(items: list[dict[str, Any]]) -> dict[str, int]:
    progress = {"passed": 0, "inconclusive": 0, "needs_revision": 0, "pending": 0}
    for item in items:
        progress[item["review_status"]] += 1
    return progress


def _next_actions(items: list[dict[str, Any]]) -> list[str]:
    return [
        f"review_packet:{item['topic']}"
        for item in items
        if item["review_status"] in {"pending", "needs_revision", "inconclusive"}
    ]
