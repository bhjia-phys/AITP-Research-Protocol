"""Read-only packet for legacy semantic review human checkpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
from brain.v5.models import HumanCheckpointRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records


def build_legacy_human_checkpoint_packet(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
    topic: str = "",
) -> dict[str, Any]:
    """Group open decisions and pending checkpoint requests from the worklist."""

    topic_filter = topic.strip()
    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=migration_dir)
    checkpoints = {
        checkpoint.checkpoint_id: checkpoint
        for checkpoint in list_records(ws.registry_dir("checkpoints"), HumanCheckpointRecord)
    }
    checkpoint_items = [
        checkpoint_item
        for item in worklist["items"]
        if not topic_filter or item["topic"] == topic_filter
        for command in item.get("review_action_commands", [])
        for checkpoint_item in [_checkpoint_item(item, command, checkpoints=checkpoints)]
        if checkpoint_item is not None
    ]
    return {
        "kind": "legacy_human_checkpoint_packet",
        "run_id": worklist["run_id"],
        "migration_dir": worklist["migration_dir"],
        "workspace": worklist["workspace"],
        "topic_filter": topic_filter,
        "checkpoint_item_count": len(checkpoint_items),
        "open_decision_count": sum(1 for item in checkpoint_items if item["mode"] == "decide_open_checkpoint"),
        "pending_request_count": sum(1 for item in checkpoint_items if item["mode"] == "request_checkpoint"),
        "checkpoint_items": checkpoint_items,
        "next_actions": [
            (
                f"human_checkpoint:{item['topic']}:decide:{item['checkpoint_id']}"
                if item["mode"] == "decide_open_checkpoint"
                else f"human_checkpoint:{item['topic']}:request:{item['action']}"
            )
            for item in checkpoint_items
        ],
        "semantic_lossless_proven": False,
        "truth_source": "legacy_semantic_review_worklist_human_checkpoint_commands",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _checkpoint_item(
    item: dict[str, Any],
    command: Any,
    *,
    checkpoints: dict[str, HumanCheckpointRecord],
) -> dict[str, Any] | None:
    if not _is_human_checkpoint_command(command):
        return None
    checkpoint_id = str(command.get("checkpoint_id") or "")
    mode = "decide_open_checkpoint" if command.get("mcp") == "aitp_v5_decide_human_checkpoint" else "request_checkpoint"
    checkpoint_record = checkpoints.get(checkpoint_id)
    open_checkpoint = _open_checkpoint(item, checkpoint_id=checkpoint_id)
    return {
        "topic": str(item.get("topic") or ""),
        "active_claim_id": str(item.get("active_claim_id") or ""),
        "latest_review_id": str(command.get("latest_review_id") or item.get("latest_review_id") or ""),
        "review_status": str(item.get("review_status") or ""),
        "action": str(command.get("action") or ""),
        "mode": mode,
        "checkpoint_id": checkpoint_id,
        "reason": _checkpoint_reason(checkpoint_record, open_checkpoint, command),
        "options": _checkpoint_options(checkpoint_record, open_checkpoint, command),
        "command": dict(command),
        "can_update_claim_trust": False,
    }


def _is_human_checkpoint_command(command: Any) -> bool:
    return (
        isinstance(command, dict)
        and command.get("surface") == "human_checkpoint_record"
        and command.get("mcp") in {"aitp_v5_request_human_checkpoint", "aitp_v5_decide_human_checkpoint"}
        and command.get("effect") == "typed_record_write"
        and isinstance(command.get("action"), str)
        and bool(command["action"])
    )


def _open_checkpoint(item: dict[str, Any], *, checkpoint_id: str) -> dict[str, Any]:
    for checkpoint in item.get("open_human_checkpoints", []) or []:
        if isinstance(checkpoint, dict) and checkpoint.get("checkpoint_id") == checkpoint_id:
            return checkpoint
    return {}


def _reason_from_cli(command: dict[str, Any]) -> str:
    cli = str(command.get("cli") or "")
    marker = "--reason <"
    if marker not in cli:
        return ""
    tail = cli.split(marker, 1)[1]
    return tail.split(">", 1)[0]


def _options_from_cli(command: dict[str, Any]) -> list[str]:
    cli = str(command.get("cli") or "")
    if "--decision <" in cli:
        tail = cli.split("--decision <", 1)[1]
        return [option for option in tail.split(">", 1)[0].split("|") if option]
    return [
        part.split()[0]
        for part in cli.split("--option ")[1:]
        if part.split()
    ]


def _checkpoint_reason(
    checkpoint: HumanCheckpointRecord | None,
    open_checkpoint: dict[str, Any],
    command: dict[str, Any],
) -> str:
    if checkpoint is not None:
        return checkpoint.reason
    return str(open_checkpoint.get("reason") or _reason_from_cli(command))


def _checkpoint_options(
    checkpoint: HumanCheckpointRecord | None,
    open_checkpoint: dict[str, Any],
    command: dict[str, Any],
) -> list[str]:
    if checkpoint is not None:
        return list(checkpoint.options)
    return list(open_checkpoint.get("options") or _options_from_cli(command))
