"""QSGW AC command hints for legacy semantic review worklists."""

from __future__ import annotations

from typing import Any


def qsgw_review_action_command(
    action: str,
    item: dict[str, Any],
    *,
    latest_review: dict[str, Any],
    review_id: str,
    workspace: str,
    migration_dir: str,
) -> dict[str, Any] | None:
    if action == "verify_runtime_logs_for_recomputed_head_wing_each_qsgw_iteration":
        return _runtime_log_marker_audit_command(
            action,
            item,
            review_id=review_id,
            workspace=workspace,
            migration_dir=migration_dir,
        )
    code_readbacks = {
        "readback_librpa_task_qsgw_ac_call_site_and_truncation_fallback_logic_from_actual_code_or_preserved_originals": "qsgw_ac_callsite_readback",
        "readback_librpa_analycont_thiele_pade_division_or_pole_instability_points_from_actual_code_or_preserved_originals": "qsgw_ac_pade_readback",
        "resolve_n_params_anacon_input_parsing_before_molecular_sensitivity_sweep": "qsgw_ac_parameter_parse_readback",
    }
    if action in code_readbacks:
        return _code_readback_command(
            action,
            item,
            review_id=review_id,
            workspace=workspace,
            tool_name=code_readbacks[action],
        )
    if action == "provide_or_patch_n_params_anacon_parameter_injection_before_n_params_sensitivity_sweep":
        return _parameter_injection_code_state_command(
            action,
            review_id=review_id,
            workspace=workspace,
        )
    validation_actions = {
        "compare_nfreq_and_n_params_anacon_sensitivity_on_molecular_regression_cases": (
            "molecular-sensitivity-tool-run-id",
            "nfreq/n_params_anacon molecular regression comparison",
        ),
        "compare_pade_mitigation_against_full_frequency_or_contour_deformation_reference": (
            "pade-mitigation-comparison-tool-run-id",
            "Pade mitigation against full-frequency or contour-deformation reference",
        ),
    }
    if action in validation_actions:
        tool_run_placeholder, summary = validation_actions[action]
        return _validation_result_command(
            action,
            item,
            latest_review=latest_review,
            review_id=review_id,
            workspace=workspace,
            tool_run_placeholder=tool_run_placeholder,
            summary=summary,
            statuses="<partial|passed|failed|inconclusive>",
        )
    return None


def _runtime_log_marker_audit_command(
    action: str,
    item: dict[str, Any],
    *,
    review_id: str,
    workspace: str,
    migration_dir: str,
) -> dict[str, Any]:
    return _command(
        action,
        review_id=review_id,
        cli=(
            f"aitp-v5 --base {workspace} legacy runtime-log-marker-audit "
            f"--migration-dir {migration_dir} --topic {item['topic']} "
            "--marker \"Recomputed head-wing\" --expected-min-count <qsgw-iteration-count> "
            "--raw-log-file <raw-runtime-log>"
        ),
        mcp="aitp_v5_build_legacy_runtime_log_marker_audit",
        surface="legacy_runtime_log_marker_audit",
    )


def _code_readback_command(
    action: str,
    item: dict[str, Any],
    *,
    review_id: str,
    workspace: str,
    tool_name: str,
) -> dict[str, Any]:
    return _command(
        action,
        review_id=review_id,
        cli=(
            f"aitp-v5 --base {workspace} tool run record "
            f"--recipe <code-trace-recipe-id> --family code_trace --name {tool_name} "
            f"--topic {item['topic']} --claim {item['active_claim_id']} "
            "--outputs-json <code-readback-json> --source-ref <LibRPA-code-ref>"
        ),
        mcp="aitp_v5_record_tool_run",
        surface="tool_run_record",
        effect="typed_record_write",
        can_update_kernel_state=True,
    )


def _parameter_injection_code_state_command(
    action: str,
    *,
    review_id: str,
    workspace: str,
) -> dict[str, Any]:
    return _command(
        action,
        review_id=review_id,
        cli=(
            f"aitp-v5 --base {workspace} code state record "
            "--repo-id <LibRPA-repo-id> --upstream-remote <remote> --upstream-branch <branch> "
            "--upstream-commit <commit> --local-branch <branch> --worktree-path <LibRPA-worktree-path> "
            "--linked-records-json <parameter-injection-validation-links> "
            "--known-divergence <n_params_anacon parameter injection path or nfreq-only sweep decision>"
        ),
        mcp="aitp_v5_record_code_state",
        surface="code_state_record",
        effect="typed_record_write",
        can_update_kernel_state=True,
    )


def _validation_result_command(
    action: str,
    item: dict[str, Any],
    *,
    latest_review: dict[str, Any],
    review_id: str,
    workspace: str,
    tool_run_placeholder: str,
    summary: str,
    statuses: str,
) -> dict[str, Any]:
    return _command(
        action,
        review_id=review_id,
        cli=(
            f"aitp-v5 --base {workspace} validation result record "
            f"--topic {item['topic']} --claim {item['active_claim_id']} "
            f"--contract {_validation_contract_id(latest_review)} "
            f"--tool-run <{tool_run_placeholder}> --status {statuses} "
            f"--checked-output validation_result --summary <{summary}>"
        ),
        mcp="aitp_v5_record_validation_result",
        surface="validation_result_record",
        effect="typed_record_write",
        can_update_kernel_state=True,
    )


def _validation_contract_id(latest_review: dict[str, Any]) -> str:
    for ref in latest_review.get("reviewed_typed_refs", []):
        text = str(ref)
        if text.startswith("validation-contract"):
            return text.removeprefix("validation-contract:")
    return "<validation-contract-id>"


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
