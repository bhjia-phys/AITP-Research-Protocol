"""Prioritized worklist for legacy semantic review backlog."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.legacy_semantic_review_manifest import build_legacy_semantic_review_manifest
from brain.v5.legacy_semantic_worklist_commands import followup_review_commands, review_action_commands
from brain.v5.models import HumanCheckpointRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records


def build_legacy_semantic_review_worklist(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a read-only prioritized queue for remaining legacy semantic reviews."""

    if manifest is None:
        manifest = build_legacy_semantic_review_manifest(ws, migration_dir=migration_dir)
    checkpoints_by_claim = _group_open_human_checkpoints(
        list_records(ws.registry_dir("checkpoints"), HumanCheckpointRecord)
    )
    candidates = [
        _work_item(
            item,
            workspace=manifest["workspace"],
            migration_dir=manifest["migration_dir"],
            open_human_checkpoints=checkpoints_by_claim.get(str(item.get("active_claim_id") or ""), []),
        )
        for item in manifest["items"]
        if item["review_status"] in {"pending", "needs_revision", "inconclusive"}
    ]
    items = sorted(candidates, key=lambda item: (-item["priority_score"], item["topic"]))
    open_checkpoints = _open_human_checkpoint_summary(items)
    return {
        "kind": "legacy_semantic_review_worklist",
        "run_id": manifest["run_id"],
        "migration_dir": manifest["migration_dir"],
        "workspace": manifest["workspace"],
        "work_item_count": len(items),
        "open_human_checkpoint_count": len(open_checkpoints),
        "open_human_checkpoints": open_checkpoints,
        "status_counts": _status_counts(items),
        "pass_readiness_counts": _pass_readiness_counts(items),
        "pass_blocker_counts": _pass_blocker_counts(items),
        "blocking_class_counts": _blocking_class_counts(items),
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


def _work_item(
    item: dict[str, Any],
    *,
    workspace: str,
    migration_dir: str,
    open_human_checkpoints: list[HumanCheckpointRecord],
) -> dict[str, Any]:
    repair_count = int(item.get("repair_candidate_count") or 0)
    missing = list(item.get("missing_source_components") or _missing_source_components_from_reasons(item))
    followup_actions = list(item.get("followup_review_actions", []))
    focus = _review_focus(
        item,
        repair_count=repair_count,
        missing_components=missing,
        followup_review_actions=followup_actions,
    )
    priority_score = _priority_score(item, repair_count=repair_count, missing_components=missing)
    latest = item.get("latest_semantic_review") if isinstance(item.get("latest_semantic_review"), dict) else {}
    satisfied_actions = list(item.get("satisfied_review_actions", []))
    source_review_refs = [
        str(ref) for ref in item.get("source_reconstruction_review_refs", []) if str(ref)
    ]
    open_checkpoints = _open_checkpoint_payloads(item, open_human_checkpoints)
    open_checkpoint_refs = [
        f"human-checkpoint:{checkpoint['checkpoint_id']}" for checkpoint in open_checkpoints
    ]
    command_item = {**item, "open_human_checkpoints": open_checkpoints}
    pass_readiness = _pass_readiness(
        item,
        latest_review=latest,
        missing_components=missing,
        followup_review_actions=followup_actions,
        open_human_checkpoint_refs=open_checkpoint_refs,
    )
    blocking_classes = _blocking_classes(pass_readiness, review_focus=focus)
    commands = review_action_commands(
        command_item,
        latest_review=latest,
        workspace=workspace,
        migration_dir=migration_dir,
    )
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
        "source_reconstruction_review_refs": source_review_refs,
        "current_recovery_focus": dict(item.get("current_recovery_focus") or {}),
        "open_human_checkpoint_refs": open_checkpoint_refs,
        "satisfied_review_actions": satisfied_actions,
        "followup_review_actions": followup_actions,
        "pass_readiness": pass_readiness,
        "blocking_classes": blocking_classes,
        "review_action_commands": commands,
        "followup_review_commands": followup_review_commands(
            item,
            latest_review=latest,
            satisfied_review_actions=satisfied_actions,
            followup_review_actions=followup_actions,
            workspace=workspace,
            migration_dir=migration_dir,
        ),
        "repair_candidate_count": repair_count,
        "repair_candidates": list(item.get("repair_candidates", [])),
        "packet_cli": item["packet_cli"],
        "result_cli_template": item["result_cli_template"],
        "can_update_claim_trust": False,
    }


def _open_human_checkpoint_summary(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for item in items:
        for command in item.get("review_action_commands", []):
            if not isinstance(command, dict):
                continue
            checkpoint_id = str(command.get("checkpoint_id") or "")
            if not checkpoint_id:
                continue
            summaries.append(
                {
                    "topic": str(item.get("topic") or ""),
                    "active_claim_id": str(item.get("active_claim_id") or ""),
                    "checkpoint_id": checkpoint_id,
                    "checkpoint_ref": f"human-checkpoint:{checkpoint_id}",
                    "action": str(command.get("action") or ""),
                    "decision_cli": str(command.get("cli") or ""),
                    "decision_mcp": str(command.get("mcp") or ""),
                    "can_update_claim_trust": False,
                }
            )
    return summaries


def _group_open_human_checkpoints(
    records: list[HumanCheckpointRecord],
) -> dict[str, list[HumanCheckpointRecord]]:
    grouped: dict[str, list[HumanCheckpointRecord]] = {}
    for record in records:
        if record.status != "open":
            continue
        grouped.setdefault(record.claim_id, []).append(record)
    for checkpoints in grouped.values():
        checkpoints.sort(key=lambda checkpoint: checkpoint.checkpoint_id)
    return grouped


def _open_checkpoint_payloads(
    item: dict[str, Any],
    checkpoints: list[HumanCheckpointRecord],
) -> list[dict[str, Any]]:
    topic = str(item.get("topic") or "")
    return [
        {
            "checkpoint_id": checkpoint.checkpoint_id,
            "topic_id": checkpoint.topic_id,
            "claim_id": checkpoint.claim_id,
            "reason": checkpoint.reason,
            "requested_by": checkpoint.requested_by,
            "options": list(checkpoint.options),
            "status": checkpoint.status,
        }
        for checkpoint in checkpoints
        if checkpoint.topic_id == topic
    ]


def _pass_readiness(
    item: dict[str, Any],
    *,
    latest_review: dict[str, Any],
    missing_components: list[str],
    followup_review_actions: list[str],
    open_human_checkpoint_refs: list[str],
) -> dict[str, Any]:
    remaining_actions = [str(action) for action in latest_review.get("remaining_actions", []) if str(action)]
    reviewed_legacy_refs = [
        str(ref) for ref in latest_review.get("reviewed_legacy_refs", []) if str(ref)
    ]
    needs_archive_sampling = "archive_only_records_require_sampling" in set(item.get("review_reasons", []))
    archive_sampled = (not needs_archive_sampling) or any(
        ref.startswith("legacy_archive:") for ref in reviewed_legacy_refs
    )
    reviewed_ref_set = set(reviewed_legacy_refs)
    file_scope = item.get("file_review_scope") if isinstance(item.get("file_review_scope"), dict) else {}
    required_file_refs = [
        str(ref) for ref in file_scope.get("required_review_refs", []) if str(ref)
    ]
    missing_file_refs = [ref for ref in required_file_refs if ref not in reviewed_ref_set]
    file_scope_status = str(file_scope.get("scope_status") or "")
    recovery_focus = (
        item.get("current_recovery_focus")
        if isinstance(item.get("current_recovery_focus"), dict)
        else {}
    )
    active_claim_divergence = bool(recovery_focus.get("active_claim_divergence") is True)
    requirements = {
        "active_claim_present": bool(str(item.get("active_claim_id") or "")),
        "active_claim_statement_present": bool(item.get("active_claim_statement_present")),
        "source_reconstruction_complete": not missing_components
        and item.get("source_reconstruction", {}).get("status") == "complete",
        "latest_review_recorded": bool(latest_review),
        "latest_review_not_needs_revision": item.get("review_status") != "needs_revision",
        "no_remaining_review_actions": not remaining_actions,
        "no_followup_review_actions": not followup_review_actions,
        "no_open_human_checkpoints": not open_human_checkpoint_refs,
        "archive_sampled_when_needed": archive_sampled,
        "file_review_scope_available": file_scope_status in {"ready", "empty", "ledger_unavailable"},
        "required_file_review_refs_recorded": not missing_file_refs,
        "no_active_claim_divergence": not active_claim_divergence,
    }
    blockers: list[str] = []
    if not requirements["active_claim_present"]:
        blockers.append("missing_active_claim")
    if not requirements["active_claim_statement_present"]:
        blockers.append("active_claim_statement_empty")
    if not requirements["source_reconstruction_complete"]:
        blockers.append("source_reconstruction_incomplete")
    if not requirements["latest_review_recorded"] or item.get("review_status") == "pending":
        blockers.append("initial_semantic_review_not_recorded")
    if not requirements["latest_review_not_needs_revision"]:
        blockers.append("latest_review_needs_revision")
    if not requirements["no_remaining_review_actions"]:
        blockers.append("latest_review_remaining_actions")
    if not requirements["no_followup_review_actions"]:
        blockers.append("followup_review_actions_pending")
    if not requirements["no_open_human_checkpoints"]:
        blockers.append("open_human_checkpoint_pending")
    if not requirements["archive_sampled_when_needed"]:
        blockers.append("archive_reference_sampling_required")
    if file_scope_status == "invalid_ledger":
        blockers.append("file_review_scope_unavailable")
    if not requirements["required_file_review_refs_recorded"]:
        blockers.append("file_level_review_refs_missing")
    if not requirements["no_active_claim_divergence"]:
        blockers.append("active_claim_divergence_requires_review")
    return {
        "status": "candidate" if not blockers else "blocked",
        "pass_candidate": not blockers,
        "latest_review_id": str(latest_review.get("review_id") or ""),
        "requirements": requirements,
        "blockers": _unique(blockers),
        "remaining_actions": remaining_actions,
        "followup_review_actions": list(followup_review_actions),
        "open_human_checkpoint_refs": list(open_human_checkpoint_refs),
        "required_file_review_ref_count": len(required_file_refs),
        "missing_file_review_ref_count": len(missing_file_refs),
        "missing_file_review_refs_sample": missing_file_refs[:20],
        "can_update_kernel_state": False,
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
    followup_review_actions: list[str],
) -> list[str]:
    focus: list[str] = []
    if repair_count:
        focus.append("apply_or_review_typed_repair_candidates")
    focus.extend(followup_review_actions)
    if missing_components:
        focus.append("complete_source_reconstruction_components")
    file_scope = item.get("file_review_scope") if isinstance(item.get("file_review_scope"), dict) else {}
    if file_scope.get("scope_status") == "invalid_ledger":
        focus.append("locate_file_level_migration_ledger")
    elif file_scope.get("required_review_refs"):
        focus.append("review_file_level_migration_decisions")
    recovery_focus = item.get("current_recovery_focus") if isinstance(item.get("current_recovery_focus"), dict) else {}
    if recovery_focus.get("active_claim_divergence"):
        focus.append("resolve_active_claim_divergence")
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


def _pass_readiness_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"blocked": 0, "candidate": 0}
    for item in items:
        readiness = item.get("pass_readiness")
        status = readiness.get("status") if isinstance(readiness, dict) else ""
        if status in counts:
            counts[status] += 1
    return counts


def _pass_blocker_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        readiness = item.get("pass_readiness")
        blockers = readiness.get("blockers") if isinstance(readiness, dict) else []
        for blocker in blockers or []:
            key = str(blocker)
            if key:
                counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _blocking_class_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for key in item.get("blocking_classes") or []:
            if isinstance(key, str) and key:
                counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _blocking_classes(pass_readiness: dict[str, Any], *, review_focus: list[str]) -> list[str]:
    blockers = {
        str(blocker)
        for blocker in pass_readiness.get("blockers", [])
        if str(blocker)
    }
    action_text = " ".join(
        [
            *[str(action) for action in pass_readiness.get("remaining_actions", [])],
            *[str(action) for action in pass_readiness.get("followup_review_actions", [])],
            *[str(action) for action in review_focus],
        ]
    ).lower()
    classes: list[str] = []

    def add(name: str) -> None:
        if name not in classes:
            classes.append(name)

    if "source_reconstruction_incomplete" in blockers:
        add("source_reconstruction_required")
    if "active_claim_statement_empty" in blockers or "topic_question" in action_text:
        add("claim_statement_backfill_required")
    if "initial_semantic_review_not_recorded" in blockers:
        add("initial_semantic_review_required")
    if "latest_review_needs_revision" in blockers:
        add("semantic_review_revision_required")
    if blockers.intersection({"latest_review_remaining_actions", "followup_review_actions_pending"}):
        add("semantic_review_followup_required")
    if "archive_reference_sampling_required" in blockers:
        add("archive_sampling_required")
    if "open_human_checkpoint_pending" in blockers or "human_checkpoint" in action_text:
        add("human_checkpoint_required")
    if "file_review_scope_unavailable" in blockers or "file_level_review_refs_missing" in blockers:
        add("file_level_semantic_review_required")
    if "active_claim_divergence_requires_review" in blockers:
        add("current_recovery_state_review_required")
    if _mentions_source_metadata_repair(action_text):
        add("source_metadata_repair_required")
    if "executable" in action_text or "benchmark" in action_text:
        add("executable_evidence_required")
    if not classes and pass_readiness.get("status") == "blocked":
        add("unclassified_semantic_blocker")
    return classes


def _mentions_source_metadata_repair(action_text: str) -> bool:
    repair_word = any(
        token in action_text
        for token in ("repair", "resolve", "mismatch", "correct", "canonical")
    )
    metadata_word = any(
        token in action_text
        for token in ("doi", "bibliograph", "citation", "source metadata")
    )
    return repair_word and metadata_word


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
