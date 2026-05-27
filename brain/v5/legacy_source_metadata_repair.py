"""Read-only packet for legacy source metadata repair work."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.legacy_semantic_review import build_legacy_semantic_review_packet
from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
from brain.v5.paths import WorkspacePaths


def build_legacy_source_metadata_repair_packet(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
    topic: str = "",
) -> dict[str, Any]:
    """Group DOI/citation metadata repair actions from the semantic-review worklist."""

    topic_filter = topic.strip()
    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=migration_dir)
    repair_items = [
        repair_item
        for item in worklist["items"]
        if (not topic_filter or item["topic"] == topic_filter)
        for repair_item in [_repair_item(ws, item, migration_dir=worklist["migration_dir"])]
        if repair_item is not None
    ]
    return {
        "kind": "legacy_source_metadata_repair_packet",
        "run_id": worklist["run_id"],
        "migration_dir": worklist["migration_dir"],
        "workspace": worklist["workspace"],
        "topic_filter": topic_filter,
        "repair_item_count": len(repair_items),
        "repair_items": repair_items,
        "next_actions": [
            f"source_metadata_repair:{item['topic']}:{action}"
            for item in repair_items
            for action in item["source_metadata_actions"]
        ],
        "semantic_lossless_proven": False,
        "truth_source": "legacy_semantic_review_worklist_remaining_actions",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _repair_item(ws: WorkspacePaths, item: dict[str, Any], *, migration_dir: str) -> dict[str, Any] | None:
    commands = [
        dict(command)
        for command in item.get("review_action_commands", [])
        if _is_reference_location_command(command)
    ]
    if not commands:
        return None
    semantic_packet = build_legacy_semantic_review_packet(
        ws,
        migration_dir=migration_dir,
        topic=str(item["topic"]),
    )
    latest_review = (
        semantic_packet.get("latest_semantic_review")
        if isinstance(semantic_packet.get("latest_semantic_review"), dict)
        else {}
    )
    return {
        "topic": str(item["topic"]),
        "active_claim_id": str(item.get("active_claim_id") or ""),
        "latest_review_id": str(item.get("latest_review_id") or latest_review.get("review_id") or ""),
        "review_status": str(item.get("review_status") or ""),
        "source_metadata_actions": [str(command["action"]) for command in commands],
        "reviewed_legacy_refs": _clean_refs(latest_review.get("reviewed_legacy_refs", [])),
        "reviewed_typed_refs": _clean_refs(latest_review.get("reviewed_typed_refs", [])),
        "reference_location_commands": commands,
        "followup_result_cli": (
            f"aitp-v5 --base {ws.base} legacy semantic-review-result "
            f"--migration-dir {migration_dir} --topic {item['topic']} "
            "--status <inconclusive|passed> "
            "--legacy-ref <reviewed-source-metadata-ref> --typed-ref <reference-location-id> "
            "--summary <source metadata repair review basis and remaining semantic gaps>"
        ),
        "can_update_claim_trust": False,
    }


def _is_reference_location_command(command: Any) -> bool:
    return (
        isinstance(command, dict)
        and command.get("surface") == "reference_location_record"
        and command.get("mcp") == "aitp_v5_record_reference_location"
        and isinstance(command.get("action"), str)
        and bool(command["action"])
    )


def _clean_refs(values: Any) -> list[str]:
    return [str(value).strip() for value in values or [] if str(value).strip()]
