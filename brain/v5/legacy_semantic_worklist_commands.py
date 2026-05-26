"""Command hints for legacy semantic review worklist items."""

from __future__ import annotations

from typing import Any

from brain.v5.legacy_semantic_qsgw_commands import qsgw_review_action_command


def review_action_commands(
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


def followup_review_commands(
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
        return _source_reconstruction_command(action, item, review_id=review_id, workspace=workspace)
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
    if action == "trace_compute_Wc_freq_q_accepts_chi_r_substitution_on_actual_LibRPA_code":
        return _command(
            action,
            review_id=review_id,
            cli=(
                f"aitp-v5 --base {workspace} tool run record "
                "--recipe <code-trace-recipe-id> --family code_trace --name trace_compute_Wc_freq_q "
                f"--topic {item['topic']} --claim {item['active_claim_id']} "
                "--outputs-json <trace-result-json> --source-ref <LibRPA-code-ref>"
            ),
            mcp="aitp_v5_record_tool_run",
            surface="tool_run_record",
            effect="typed_record_write",
            can_update_kernel_state=True,
        )
    if action == "validate_static_U_and_J_against_SrVO3_reference":
        return _command(
            action,
            review_id=review_id,
            cli=(
                f"aitp-v5 --base {workspace} validation result record "
                f"--topic {item['topic']} --claim {item['active_claim_id']} "
                f"--contract {_validation_contract_id(latest_review)} "
                "--tool-run <srvo3-validation-tool-run-id> --status <partial|passed|failed> "
                "--checked-output validation_result --summary <SrVO3 U/J benchmark result>"
            ),
            mcp="aitp_v5_record_validation_result",
            surface="validation_result_record",
            effect="typed_record_write",
            can_update_kernel_state=True,
        )
    qsgw_command = qsgw_review_action_command(
        action,
        item,
        latest_review=latest_review,
        review_id=review_id,
        workspace=workspace,
    )
    if qsgw_command is not None:
        return qsgw_command
    return _normalized_action_command(action, item, review_id=review_id, workspace=workspace)


def _normalized_action_command(
    action: str,
    item: dict[str, Any],
    *,
    review_id: str,
    workspace: str,
) -> dict[str, Any] | None:
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
        return _source_reconstruction_command(action, item, review_id=review_id, workspace=workspace)
    return None


def _source_reconstruction_command(
    action: str,
    item: dict[str, Any],
    *,
    review_id: str,
    workspace: str,
) -> dict[str, Any]:
    return _command(
        action,
        review_id=review_id,
        cli=f"aitp-v5 --base {workspace} source reconstruction-review --claim {item['active_claim_id']}",
        mcp="aitp_v5_build_source_reconstruction_review_packet",
        surface="source_reconstruction_review_packet",
    )


def _validation_contract_id(latest_review: dict[str, Any]) -> str:
    for ref in latest_review.get("reviewed_typed_refs", []):
        text = str(ref)
        if text.startswith("validation-contract"):
            return text.removeprefix("validation-contract:")
    return "<validation-contract-id>"


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


def _missing_source_components_from_reasons(item: dict[str, Any]) -> list[str]:
    source = item.get("source_reconstruction")
    if isinstance(source, dict) and isinstance(source.get("missing_components"), list):
        return [str(value) for value in source["missing_components"]]
    return []


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
