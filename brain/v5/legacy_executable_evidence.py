"""Read-only packet for executable evidence blockers in legacy semantic review."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.legacy_semantic_review import build_legacy_semantic_review_packet
from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
from brain.v5.paths import WorkspacePaths

_EXECUTABLE_SURFACES = {"validation_result_record", "tool_run_record"}


def build_legacy_executable_evidence_packet(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
    topic: str = "",
) -> dict[str, Any]:
    """Group validation/tool-run actions that block legacy semantic review pass."""

    topic_filter = topic.strip()
    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=migration_dir)
    evidence_items = [
        evidence_item
        for item in worklist["items"]
        if (not topic_filter or item["topic"] == topic_filter)
        and "executable_evidence_required" in set(item.get("blocking_classes", []))
        for evidence_item in [_evidence_item(ws, item, migration_dir=worklist["migration_dir"])]
        if evidence_item is not None
    ]
    return {
        "kind": "legacy_executable_evidence_packet",
        "run_id": worklist["run_id"],
        "migration_dir": worklist["migration_dir"],
        "workspace": worklist["workspace"],
        "topic_filter": topic_filter,
        "evidence_item_count": len(evidence_items),
        "executable_action_count": sum(len(item["executable_actions"]) for item in evidence_items),
        "evidence_items": evidence_items,
        "next_actions": [
            f"executable_evidence:{item['topic']}:{action}"
            for item in evidence_items
            for action in item["executable_actions"]
        ],
        "semantic_lossless_proven": False,
        "truth_source": "legacy_semantic_review_worklist_validation_and_tool_run_commands",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _evidence_item(ws: WorkspacePaths, item: dict[str, Any], *, migration_dir: str) -> dict[str, Any] | None:
    commands = [
        dict(command)
        for command in item.get("review_action_commands", [])
        if _is_executable_command(command)
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
    validation_commands = [
        command for command in commands if command.get("surface") == "validation_result_record"
    ]
    tool_run_commands = [
        command for command in commands if command.get("surface") == "tool_run_record"
    ]
    return {
        "topic": str(item["topic"]),
        "active_claim_id": str(item.get("active_claim_id") or ""),
        "latest_review_id": str(item.get("latest_review_id") or latest_review.get("review_id") or ""),
        "review_status": str(item.get("review_status") or ""),
        "executable_actions": [str(command["action"]) for command in commands],
        "validation_commands": validation_commands,
        "tool_run_commands": tool_run_commands,
        "reviewed_legacy_refs": _clean_refs(latest_review.get("reviewed_legacy_refs", [])),
        "reviewed_typed_refs": _clean_refs(latest_review.get("reviewed_typed_refs", [])),
        "evidence_refs": _clean_refs(latest_review.get("evidence_refs", [])),
        "followup_result_cli": (
            f"aitp-v5 --base {ws.base} legacy semantic-review-result "
            f"--migration-dir {migration_dir} --topic {item['topic']} "
            "--status <inconclusive|passed> "
            "--typed-ref <validation-or-tool-run-ref> --evidence-ref <evidence-ref> "
            "--summary <executable evidence review basis and remaining semantic gaps>"
        ),
        "can_update_claim_trust": False,
    }


def _is_executable_command(command: Any) -> bool:
    return (
        isinstance(command, dict)
        and command.get("surface") in _EXECUTABLE_SURFACES
        and command.get("effect") == "typed_record_write"
        and isinstance(command.get("action"), str)
        and bool(command["action"])
    )


def _clean_refs(values: Any) -> list[str]:
    return [str(value).strip() for value in values or [] if str(value).strip()]
