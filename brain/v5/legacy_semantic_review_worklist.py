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
        _work_item(item, workspace=manifest["workspace"], migration_dir=manifest["migration_dir"])
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


def _work_item(item: dict[str, Any], *, workspace: str, migration_dir: str) -> dict[str, Any]:
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
    pass_readiness = _pass_readiness(
        item,
        latest_review=latest,
        missing_components=missing,
        followup_review_actions=followup_actions,
    )
    review_action_commands = _review_action_commands(
        item,
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
        "satisfied_review_actions": satisfied_actions,
        "followup_review_actions": followup_actions,
        "pass_readiness": pass_readiness,
        "review_action_commands": review_action_commands,
        "followup_review_commands": _followup_review_commands(
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


def _pass_readiness(
    item: dict[str, Any],
    *,
    latest_review: dict[str, Any],
    missing_components: list[str],
    followup_review_actions: list[str],
) -> dict[str, Any]:
    remaining_actions = [str(action) for action in latest_review.get("remaining_actions", []) if str(action)]
    reviewed_legacy_refs = [
        str(ref) for ref in latest_review.get("reviewed_legacy_refs", []) if str(ref)
    ]
    needs_archive_sampling = "archive_only_records_require_sampling" in set(item.get("review_reasons", []))
    archive_sampled = (not needs_archive_sampling) or any(
        ref.startswith("legacy_archive:") for ref in reviewed_legacy_refs
    )
    requirements = {
        "active_claim_present": bool(str(item.get("active_claim_id") or "")),
        "active_claim_statement_present": bool(item.get("active_claim_statement_present")),
        "source_reconstruction_complete": not missing_components
        and item.get("source_reconstruction", {}).get("status") == "complete",
        "latest_review_recorded": bool(latest_review),
        "latest_review_not_needs_revision": item.get("review_status") != "needs_revision",
        "no_remaining_review_actions": not remaining_actions,
        "no_followup_review_actions": not followup_review_actions,
        "archive_sampled_when_needed": archive_sampled,
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
    if not requirements["archive_sampled_when_needed"]:
        blockers.append("archive_reference_sampling_required")
    return {
        "status": "candidate" if not blockers else "blocked",
        "pass_candidate": not blockers,
        "latest_review_id": str(latest_review.get("review_id") or ""),
        "requirements": requirements,
        "blockers": _unique(blockers),
        "remaining_actions": remaining_actions,
        "followup_review_actions": list(followup_review_actions),
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _review_action_commands(
    item: dict[str, Any],
    *,
    latest_review: dict[str, Any],
    workspace: str,
    migration_dir: str,
) -> list[dict[str, Any]]:
    if not latest_review:
        return []
    return [
        command
        for action in latest_review.get("remaining_actions", [])
        for command in [
            _review_action_command(
                str(action),
                item,
                latest_review=latest_review,
                workspace=workspace,
                migration_dir=migration_dir,
            )
        ]
        if command is not None
    ]


def _review_action_command(
    action: str,
    item: dict[str, Any],
    *,
    latest_review: dict[str, Any],
    workspace: str,
    migration_dir: str,
) -> dict[str, Any] | None:
    action = action.strip()
    if not action:
        return None
    review_id = str(latest_review.get("review_id") or "")
    if action == "migrate_legacy_l2_graph_entries_into_typed_l2_records":
        return _command(
            action,
            review_id=review_id,
            cli=f"aitp-v5 --base {workspace} legacy l2-graph-manifest",
            mcp="aitp_v5_build_legacy_l2_graph_manifest",
            surface="legacy_l2_graph_manifest",
        )
    if action in {
        "review_legacy_l2_memory_entry_candidates",
        "review_legacy_l2_graph_nodes_for_physics_objects",
        "review_legacy_l2_graph_edges_for_object_relations",
        "review_legacy_l2_steps_for_sensemaking_reports",
        "review_legacy_l2_towers_for_memory_entries",
    }:
        return _command(
            action,
            review_id=review_id,
            cli=f"aitp-v5 --base {workspace} legacy l2-typed-migration-packet",
            mcp="aitp_v5_build_legacy_l2_typed_migration_packet",
            surface="legacy_l2_typed_migration_packet",
        )
    if action == "record_reviewed_typed_l2_records_or_keep_orientation_only":
        return _command(
            action,
            review_id=review_id,
            cli=(
                f"aitp-v5 --base {workspace} legacy semantic-review-result "
                f"--migration-dir {migration_dir} --topic {item['topic']} "
                "--status <inconclusive|passed> --legacy-ref <reviewed-l2-ref> "
                "--typed-ref <reviewed-typed-l2-record-or-packet-ref> "
                "--summary <reviewed typed L2 migration basis and remaining gaps>"
            ),
            mcp="aitp_v5_record_legacy_semantic_review_result",
            surface="legacy_semantic_review_result_record",
            effect="typed_review_record_write",
            can_update_kernel_state=True,
        )
    if action == "rebuild_l2_obsidian_view_from_typed_graph":
        return _command(
            action,
            review_id=review_id,
            cli=f"aitp-v5 --base {workspace} legacy l2-obsidian-view",
            mcp="aitp_v5_write_legacy_l2_obsidian_view",
            surface="legacy_l2_obsidian_view_bundle",
        )
    if action == "complete_source_reconstruction":
        return _command(
            action,
            review_id=review_id,
            cli=f"aitp-v5 --base {workspace} source reconstruction-review --claim {item['active_claim_id']}",
            mcp="aitp_v5_build_source_reconstruction_review_packet",
            surface="source_reconstruction_review_packet",
        )
    if action == "record_source_reconstruction_review_result":
        return _command(
            action,
            review_id=review_id,
            cli=(
                f"aitp-v5 --base {workspace} source reconstruction-review-result "
                f"--claim {item['active_claim_id']} --status <passed|needs_revision|inconclusive> "
                f"{_source_review_component_args(item)} "
                f"{_source_review_basis_args(item)} "
                "--summary <source reconstruction review basis>"
            ),
            mcp="aitp_v5_record_source_reconstruction_review_result",
            surface="source_reconstruction_review_result_record",
            effect="typed_review_record_write",
            can_update_kernel_state=True,
        )
    if action == "classify_noncanonical_seed_before_promotion":
        return _command(
            action,
            review_id=review_id,
            cli=(
                f"aitp-v5 --base {workspace} legacy semantic-review-result "
                f"--migration-dir {migration_dir} --topic {item['topic']} "
                "--status <passed|inconclusive> --legacy-ref <reviewed-noncanonical-ref> "
                "--summary <classify noncanonical seed and remaining promotion boundary>"
            ),
            mcp="aitp_v5_record_legacy_semantic_review_result",
            surface="legacy_semantic_review_result_record",
            effect="typed_review_record_write",
            can_update_kernel_state=True,
        )
    if action == "decide_human_checkpoint_before_promotion":
        return _command(
            action,
            review_id=review_id,
            cli=(
                f"aitp-v5 --base {workspace} checkpoint request "
                f"--topic {item['topic']} --claim {item['active_claim_id']} "
                "--reason <legacy semantic review promotion decision> --requested-by legacy_semantic_review "
                "--option approve_semantic_review --option keep_backlog_blocking"
            ),
            mcp="aitp_v5_request_human_checkpoint",
            surface="human_checkpoint_record",
        )
    normalized = " ".join(action.lower().replace("_", " ").split())
    if _requests_physics_object_backfill(normalized):
        return _command(
            action,
            review_id=review_id,
            cli=(
                f"aitp-v5 --base {workspace} object record --topic {item['topic']} "
                "--type <object_type> --name <name> --definition <source-grounded-definition> "
                "--source-ref <legacy-or-typed-source-ref>"
            ),
            mcp="aitp_v5_record_physics_object",
            surface="physics_object_record",
            effect="typed_record_write",
            can_update_kernel_state=True,
        )
    if _requests_scope_or_assumption_backfill(normalized):
        return _command(
            action,
            review_id=review_id,
            cli=(
                f"aitp-v5 --base {workspace} object record --topic {item['topic']} "
                "--type <object_type> --name <scoped-object-or-regime> "
                "--definition <source-grounded-definition> --assumption <assumption-or-scope-limit> "
                "--source-ref <legacy-or-typed-source-ref>"
            ),
            mcp="aitp_v5_record_physics_object",
            surface="physics_object_record",
            effect="typed_record_write",
            can_update_kernel_state=True,
        )
    if _requests_object_relation_backfill(normalized):
        return _command(
            action,
            review_id=review_id,
            cli=(
                f"aitp-v5 --base {workspace} relation record --topic {item['topic']} "
                "--type <relation_type> --subject <object-id> --object <object-id> "
                f"--statement <source-grounded-relation> --claim {item['active_claim_id']} "
                "--source-ref <legacy-or-typed-source-ref>"
            ),
            mcp="aitp_v5_record_object_relation",
            surface="object_relation_record",
            effect="typed_record_write",
            can_update_kernel_state=True,
        )
    if _requests_failure_condition_backfill(normalized):
        return _command(
            action,
            review_id=review_id,
            cli=(
                f"aitp-v5 --base {workspace} validation contract create --topic {item['topic']} "
                f"--claim {item['active_claim_id']} --required-check <check> "
                "--failure-mode <failure-mode> --required-output source_reconstruction"
            ),
            mcp="aitp_v5_create_validation_contract",
            surface="validation_contract_record",
            effect="typed_record_write",
            can_update_kernel_state=True,
        )
    if "source reconstruction" in normalized or "reconstruction path" in normalized:
        return _command(
            action,
            review_id=review_id,
            cli=f"aitp-v5 --base {workspace} source reconstruction-review --claim {item['active_claim_id']}",
            mcp="aitp_v5_build_source_reconstruction_review_packet",
            surface="source_reconstruction_review_packet",
        )
    return None


def _requests_physics_object_backfill(normalized_action: str) -> bool:
    return (
        "physics object" in normalized_action
        or "object definitions" in normalized_action
        or "definition" in normalized_action
    ) and "relation" not in normalized_action


def _requests_scope_or_assumption_backfill(normalized_action: str) -> bool:
    return "scope" in normalized_action or "assumption" in normalized_action


def _requests_object_relation_backfill(normalized_action: str) -> bool:
    return (
        "object relation" in normalized_action
        or "relation" in normalized_action
        or "dependency graph" in normalized_action
        or "workflow" in normalized_action
    )


def _requests_failure_condition_backfill(normalized_action: str) -> bool:
    return (
        "failure condition" in normalized_action
        or "failure mode" in normalized_action
        or "validation contract" in normalized_action
    )


def _source_review_component_args(item: dict[str, Any]) -> str:
    components = list(item.get("missing_source_components") or _missing_source_components_from_reasons(item))
    if not components:
        return "--reviewed-component <component>"
    return " ".join(f"--reviewed-component {component}" for component in components)


def _source_review_basis_args(item: dict[str, Any]) -> str:
    source = item.get("source_reconstruction")
    refs = []
    if isinstance(source, dict):
        refs = [str(ref) for ref in source.get("source_refs", []) if str(ref)]
    refs = _unique(refs)[:5]
    if not refs:
        return "--basis-ref <source-or-typed-ref>"
    return " ".join(f"--basis-ref {ref}" for ref in refs)


def _command(
    action: str,
    *,
    review_id: str,
    cli: str,
    mcp: str,
    surface: str,
    effect: str = "orientation_only",
    can_update_kernel_state: bool = False,
) -> dict[str, Any]:
    return {
        "action": action,
        "latest_review_id": review_id,
        "cli": cli,
        "mcp": mcp,
        "surface": surface,
        "effect": effect,
        "can_update_kernel_state": can_update_kernel_state,
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
    if "archive_only_records_require_sampling" in set(item.get("review_reasons", [])):
        focus.append("sample_archive_reference_readback")
    if item["review_status"] == "pending":
        focus.append("perform_initial_semantic_review")
    if item["review_status"] == "inconclusive":
        focus.append("resolve_inconclusive_semantic_review")
    focus.append("record_next_legacy_semantic_review_result")
    return _unique(focus)


def _followup_review_commands(
    item: dict[str, Any],
    *,
    latest_review: dict[str, Any],
    satisfied_review_actions: list[str],
    followup_review_actions: list[str],
    workspace: str,
    migration_dir: str,
) -> list[dict[str, Any]]:
    if not followup_review_actions:
        return []
    legacy_refs = [str(ref) for ref in latest_review.get("reviewed_legacy_refs", []) if str(ref)]
    typed_refs = [str(ref) for ref in latest_review.get("reviewed_typed_refs", []) if str(ref)]
    typed_refs.extend(str(ref) for ref in item.get("source_reconstruction_review_refs", []) if str(ref))
    return [
        {
            "action": action,
            "latest_review_id": str(latest_review.get("review_id") or ""),
            "satisfied_review_actions": list(satisfied_review_actions),
            "result_cli": _followup_result_cli(
                item,
                workspace=workspace,
                migration_dir=migration_dir,
                legacy_refs=legacy_refs,
                typed_refs=typed_refs,
            ),
            "result_mcp": "aitp_v5_record_legacy_semantic_review_result",
            "can_update_claim_trust": False,
        }
        for action in followup_review_actions
    ]


def _followup_result_cli(
    item: dict[str, Any],
    *,
    workspace: str,
    migration_dir: str,
    legacy_refs: list[str],
    typed_refs: list[str],
) -> str:
    refs = " ".join([*(f"--typed-ref {ref}" for ref in typed_refs), *(f"--legacy-ref {ref}" for ref in legacy_refs)])
    if refs:
        refs = f" {refs}"
    return (
        f"aitp-v5 --base {workspace} legacy semantic-review-result "
        f"--migration-dir {migration_dir} --topic {item['topic']} "
        "--status <passed|inconclusive>"
        f"{refs} "
        "--summary <reviewed satisfied actions; explain any remaining semantic gaps>"
    )


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
