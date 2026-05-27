"""Legacy migration backlog summaries for workspace replay packets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from brain.v5.legacy_semantic_review_manifest import build_legacy_semantic_review_manifest
from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
from brain.v5.models import HumanCheckpointRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records

_EXECUTABLE_SURFACES = {"validation_result_record", "tool_run_record"}
_NEEDS_REVISION_BASIS_ACTIONS = [
    "record_needs_revision_review_with_specific_repair_basis",
    "keep_semantic_review_blocking_until_typed_review_basis_exists",
]


@dataclass
class LegacyBacklogContext:
    ws: WorkspacePaths
    migration_dir: str | None
    semantic_review_manifest: dict[str, Any] | None = None
    semantic_review_worklist: dict[str, Any] | None = None
    checkpoints_by_id: dict[str, HumanCheckpointRecord] | None = None

    def manifest(self) -> dict[str, Any] | None:
        if not self.migration_dir:
            return None
        if self.semantic_review_manifest is None:
            self.semantic_review_manifest = build_legacy_semantic_review_manifest(
                self.ws,
                migration_dir=self.migration_dir,
            )
        return self.semantic_review_manifest

    def worklist(self) -> dict[str, Any] | None:
        if not self.migration_dir:
            return None
        if self.semantic_review_worklist is None:
            self.semantic_review_worklist = build_legacy_semantic_review_worklist(
                self.ws,
                migration_dir=self.migration_dir,
                manifest=self.manifest(),
            )
        return self.semantic_review_worklist

    def checkpoints(self) -> dict[str, HumanCheckpointRecord]:
        if self.checkpoints_by_id is None:
            self.checkpoints_by_id = {
                checkpoint.checkpoint_id: checkpoint
                for checkpoint in list_records(self.ws.registry_dir("checkpoints"), HumanCheckpointRecord)
            }
        return self.checkpoints_by_id


def legacy_semantic_review_summary(context: LegacyBacklogContext) -> dict[str, Any] | None:
    manifest = context.manifest()
    worklist = context.worklist()
    if manifest is None or worklist is None:
        return None
    backlog = [item for item in manifest["items"] if item["review_status"] in {"pending", "needs_revision", "inconclusive"}]
    return {
        "surface": "legacy_semantic_review_manifest",
        "migration_dir": manifest["migration_dir"],
        "review_item_count": manifest["review_item_count"],
        "review_progress": dict(manifest["review_progress"]),
        "semantic_lossless_proven": bool(manifest["semantic_lossless_proven"]),
        "open_human_checkpoint_count": int(worklist.get("open_human_checkpoint_count") or 0),
        "open_human_checkpoints": list(worklist.get("open_human_checkpoints") or []),
        "top_backlog_items": [_legacy_backlog_item(item) for item in backlog[:5]],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def legacy_executable_evidence_summary(context: LegacyBacklogContext) -> dict[str, Any] | None:
    worklist = context.worklist()
    if worklist is None:
        return None
    evidence_items = [
        evidence_item
        for item in worklist["items"]
        if "executable_evidence_required" in set(item.get("blocking_classes", []))
        for evidence_item in [_legacy_executable_evidence_worklist_item(context.ws, item, migration_dir=worklist["migration_dir"])]
        if evidence_item is not None
    ]
    return {
        "surface": "legacy_executable_evidence_packet",
        "migration_dir": worklist["migration_dir"],
        "evidence_item_count": len(evidence_items),
        "executable_action_count": sum(len(item["executable_actions"]) for item in evidence_items),
        "top_evidence_items": [_legacy_executable_evidence_item(item) for item in evidence_items[:5]],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def legacy_human_checkpoint_summary(context: LegacyBacklogContext) -> dict[str, Any] | None:
    worklist = context.worklist()
    if worklist is None:
        return None
    checkpoint_items = [
        checkpoint_item
        for item in worklist["items"]
        for command in item.get("review_action_commands", [])
        for checkpoint_item in [_legacy_human_checkpoint_worklist_item(item, command, checkpoints=context.checkpoints())]
        if checkpoint_item is not None
    ]
    return {
        "surface": "legacy_human_checkpoint_packet",
        "migration_dir": worklist["migration_dir"],
        "checkpoint_item_count": len(checkpoint_items),
        "open_decision_count": sum(1 for item in checkpoint_items if item["mode"] == "decide_open_checkpoint"),
        "pending_request_count": sum(1 for item in checkpoint_items if item["mode"] == "request_checkpoint"),
        "next_action_count": len(checkpoint_items),
        "top_checkpoint_items": [_legacy_human_checkpoint_item(item) for item in checkpoint_items[:5]],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def legacy_needs_revision_basis_summary(context: LegacyBacklogContext) -> dict[str, Any] | None:
    worklist = context.worklist()
    if worklist is None:
        return None
    items = [
        _needs_revision_basis_item(context.ws, worklist, item)
        for item in worklist["items"]
        if item.get("review_status") == "inconclusive"
    ]
    return {
        "surface": "legacy_semantic_needs_revision_basis_queue",
        "migration_dir": worklist["migration_dir"],
        "basis_item_count": len(items),
        "status_counts": _status_counts(items),
        "required_action_counts": _required_action_counts(items),
        "top_basis_items": [_legacy_needs_revision_basis_item(item) for item in items[:5]],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _legacy_backlog_item(item: dict[str, Any]) -> dict[str, Any]:
    latest = item.get("latest_semantic_review") if isinstance(item.get("latest_semantic_review"), dict) else {}
    return {
        "topic": item["topic"],
        "active_claim_id": item["active_claim_id"],
        "review_status": item["review_status"],
        "review_priority": item["review_priority"],
        "latest_review_id": str(latest.get("review_id") or ""),
        "packet_cli": item["packet_cli"],
        "can_update_claim_trust": False,
    }


def _needs_revision_basis_item(
    ws: WorkspacePaths,
    worklist: dict[str, Any],
    item: dict[str, Any],
) -> dict[str, Any]:
    topic = str(item.get("topic") or "")
    return {
        "topic": topic,
        "active_claim_id": str(item.get("active_claim_id") or ""),
        "latest_review_id": str(item.get("latest_review_id") or ""),
        "review_status": str(item.get("review_status") or ""),
        "required_actions": list(_NEEDS_REVISION_BASIS_ACTIONS),
        "needs_revision_result_cli": (
            f"aitp-v5 --base {ws.base} legacy semantic-review-result "
            f"--migration-dir {worklist['migration_dir']} --topic {topic} "
            "--status needs_revision "
            "--legacy-ref <reviewed-legacy-ref> --typed-ref <reviewed-typed-basis-ref> "
            "--summary <specific repair basis and remaining semantic gaps>"
        ),
        "repair_plan_cli": (
            f"aitp-v5 --base {ws.base} legacy semantic-repair-plan "
            f"--migration-dir {worklist['migration_dir']} --topic {topic}"
        ),
        "can_update_claim_trust": False,
    }


def _legacy_needs_revision_basis_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "topic": str(item.get("topic") or ""),
        "active_claim_id": str(item.get("active_claim_id") or ""),
        "latest_review_id": str(item.get("latest_review_id") or ""),
        "review_status": str(item.get("review_status") or ""),
        "required_actions": list(item.get("required_actions") or []),
        "needs_revision_result_cli": str(item.get("needs_revision_result_cli") or ""),
        "repair_plan_cli": str(item.get("repair_plan_cli") or ""),
        "can_update_claim_trust": False,
    }


def _legacy_executable_evidence_worklist_item(
    ws: WorkspacePaths,
    item: dict[str, Any],
    *,
    migration_dir: str,
) -> dict[str, Any] | None:
    commands = [
        dict(command)
        for command in item.get("review_action_commands", [])
        if _is_executable_command(command)
    ]
    if not commands:
        return None
    validation_commands = [
        command for command in commands if command.get("surface") == "validation_result_record"
    ]
    tool_run_commands = [
        command for command in commands if command.get("surface") == "tool_run_record"
    ]
    return {
        "topic": str(item.get("topic") or ""),
        "active_claim_id": str(item.get("active_claim_id") or ""),
        "latest_review_id": str(item.get("latest_review_id") or ""),
        "review_status": str(item.get("review_status") or ""),
        "executable_actions": [str(command["action"]) for command in commands],
        "validation_commands": validation_commands,
        "tool_run_commands": tool_run_commands,
        "followup_result_cli": (
            f"aitp-v5 --base {ws.base} legacy semantic-review-result "
            f"--migration-dir {migration_dir} --topic {item['topic']} "
            "--status <inconclusive|passed> "
            "--typed-ref <validation-or-tool-run-ref> --evidence-ref <evidence-ref> "
            "--summary <executable evidence review basis and remaining semantic gaps>"
        ),
        "can_update_claim_trust": False,
    }


def _legacy_executable_evidence_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "topic": str(item.get("topic") or ""),
        "active_claim_id": str(item.get("active_claim_id") or ""),
        "latest_review_id": str(item.get("latest_review_id") or ""),
        "review_status": str(item.get("review_status") or ""),
        "executable_actions": list(item.get("executable_actions") or []),
        "validation_command_count": len(item.get("validation_commands") or []),
        "tool_run_command_count": len(item.get("tool_run_commands") or []),
        "followup_result_cli": str(item.get("followup_result_cli") or ""),
        "can_update_claim_trust": False,
    }


def _legacy_human_checkpoint_worklist_item(
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


def _legacy_human_checkpoint_item(item: dict[str, Any]) -> dict[str, Any]:
    command = item.get("command") if isinstance(item.get("command"), dict) else {}
    return {
        "topic": str(item.get("topic") or ""),
        "active_claim_id": str(item.get("active_claim_id") or ""),
        "latest_review_id": str(item.get("latest_review_id") or ""),
        "review_status": str(item.get("review_status") or ""),
        "action": str(item.get("action") or ""),
        "mode": str(item.get("mode") or ""),
        "checkpoint_id": str(item.get("checkpoint_id") or ""),
        "reason": str(item.get("reason") or ""),
        "options": list(item.get("options") or []),
        "cli": str(command.get("cli") or ""),
        "mcp": str(command.get("mcp") or ""),
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


def _status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("review_status") or "")
        if status:
            counts[status] = counts.get(status, 0) + 1
    return counts


def _required_action_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for action in item.get("required_actions", []):
            action = str(action)
            if action:
                counts[action] = counts.get(action, 0) + 1
    return counts
