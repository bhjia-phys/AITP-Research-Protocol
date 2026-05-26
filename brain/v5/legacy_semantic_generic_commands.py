"""Generic command hints for source-readback, boundary, and validation actions."""

from __future__ import annotations

from typing import Any


def generic_review_action_command(
    action: str,
    item: dict[str, Any],
    *,
    latest_review: dict[str, Any],
    review_id: str,
    workspace: str,
) -> dict[str, Any] | None:
    normalized = _normalize(action)
    if _requests_source_readback(normalized):
        return _source_readback_command(
            action,
            item,
            review_id=review_id,
            workspace=workspace,
            tool_name=_tool_name(action),
        )
    if _requests_source_search(normalized):
        return _source_search_command(
            action,
            item,
            review_id=review_id,
            workspace=workspace,
            tool_name=_tool_name(action),
        )
    if normalized.startswith(("design or import ", "implement or import ")):
        return _implementation_boundary_command(
            action,
            item,
            review_id=review_id,
            workspace=workspace,
            tool_name=_tool_name(action),
        )
    if _requests_validation_result(normalized):
        return _validation_result_command(
            action,
            item,
            latest_review=latest_review,
            review_id=review_id,
            workspace=workspace,
            summary=normalized,
        )
    if normalized.startswith("choose "):
        return _choice_checkpoint_command(
            action,
            item,
            review_id=review_id,
            workspace=workspace,
            reason=normalized,
        )
    if normalized.startswith("separate "):
        return _scope_partition_command(
            action,
            item,
            review_id=review_id,
            workspace=workspace,
            name=_tool_name(action),
        )
    if _requests_scope_or_model_definition(normalized):
        return _scope_or_model_definition_command(
            action,
            item,
            review_id=review_id,
            workspace=workspace,
            name=_tool_name(action),
        )
    if _requests_sensemaking_report(normalized):
        return _sensemaking_report_command(
            action,
            item,
            review_id=review_id,
            workspace=workspace,
            title=normalized,
        )
    return None


def _source_readback_command(
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
            f"--recipe <source-readback-recipe-id> --family source_readback --name {tool_name} "
            f"--topic {item['topic']} --claim {item['active_claim_id']} "
            "--outputs-json <source-readback-json> --source-ref <source-or-code-ref>"
        ),
        mcp="aitp_v5_record_tool_run",
        surface="tool_run_record",
        effect="typed_record_write",
        can_update_kernel_state=True,
    )


def _source_search_command(
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
            f"--recipe <source-search-recipe-id> --family source_search --name {tool_name} "
            f"--topic {item['topic']} --claim {item['active_claim_id']} "
            "--outputs-json <source-search-json> --source-ref <source-or-query-ref>"
        ),
        mcp="aitp_v5_record_tool_run",
        surface="tool_run_record",
        effect="typed_record_write",
        can_update_kernel_state=True,
    )


def _implementation_boundary_command(
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
            f"--recipe <implementation-boundary-recipe-id> --family implementation_boundary --name {tool_name} "
            f"--topic {item['topic']} --claim {item['active_claim_id']} "
            "--outputs-json <implementation-boundary-json> --source-ref <source-or-code-ref>"
        ),
        mcp="aitp_v5_record_tool_run",
        surface="tool_run_record",
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
    summary: str,
) -> dict[str, Any]:
    return _command(
        action,
        review_id=review_id,
        cli=(
            f"aitp-v5 --base {workspace} validation result record "
            f"--topic {item['topic']} --claim {item['active_claim_id']} "
            f"--contract {_validation_contract_id(latest_review)} "
            "--tool-run <validation-tool-run-id> --status <partial|passed|failed|inconclusive> "
            f"--checked-output validation_result --summary <{summary}>"
        ),
        mcp="aitp_v5_record_validation_result",
        surface="validation_result_record",
        effect="typed_record_write",
        can_update_kernel_state=True,
    )


def _choice_checkpoint_command(
    action: str,
    item: dict[str, Any],
    *,
    review_id: str,
    workspace: str,
    reason: str,
) -> dict[str, Any]:
    return _command(
        action,
        review_id=review_id,
        cli=(
            f"aitp-v5 --base {workspace} checkpoint request "
            f"--topic {item['topic']} --claim {item['active_claim_id']} "
            f"--reason <{reason}> --requested-by legacy_semantic_review "
            "--option record_choice --option keep_backlog_blocking"
        ),
        mcp="aitp_v5_request_human_checkpoint",
        surface="human_checkpoint_record",
    )


def _scope_partition_command(
    action: str,
    item: dict[str, Any],
    *,
    review_id: str,
    workspace: str,
    name: str,
) -> dict[str, Any]:
    return _command(
        action,
        review_id=review_id,
        cli=(
            f"aitp-v5 --base {workspace} object record "
            f"--topic {item['topic']} --type <scope_boundary_or_claim_partition> "
            f"--name {name} --definition <source-grounded scope partition> "
            "--assumption <separate claim scopes before promotion> --source-ref <legacy-or-typed-source-ref>"
        ),
        mcp="aitp_v5_record_physics_object",
        surface="physics_object_record",
        effect="typed_record_write",
        can_update_kernel_state=True,
    )


def _scope_or_model_definition_command(
    action: str,
    item: dict[str, Any],
    *,
    review_id: str,
    workspace: str,
    name: str,
) -> dict[str, Any]:
    return _command(
        action,
        review_id=review_id,
        cli=(
            f"aitp-v5 --base {workspace} object record "
            f"--topic {item['topic']} --type <scope_or_model_definition> "
            f"--name {name} --definition <source-grounded scope or model definition> "
            "--assumption <reviewed boundary before promotion> --source-ref <legacy-or-typed-source-ref>"
        ),
        mcp="aitp_v5_record_physics_object",
        surface="physics_object_record",
        effect="typed_record_write",
        can_update_kernel_state=True,
    )


def _sensemaking_report_command(
    action: str,
    item: dict[str, Any],
    *,
    review_id: str,
    workspace: str,
    title: str,
) -> dict[str, Any]:
    return _command(
        action,
        review_id=review_id,
        cli=(
            f"aitp-v5 --base {workspace} sensemaking report "
            f"--topic {item['topic']} --claim {item['active_claim_id']} "
            f"--title <{title}> --summary <source-grounded review of {title}> "
            "--next-action <record-legacy-semantic-review-result>"
        ),
        mcp="aitp_v5_record_sensemaking_report",
        surface="sensemaking_report_record",
        effect="typed_record_write",
        can_update_kernel_state=True,
    )


def _validation_contract_id(latest_review: dict[str, Any]) -> str:
    for ref in latest_review.get("reviewed_typed_refs", []):
        text = str(ref)
        if text.startswith("validation-contract"):
            return text.removeprefix("validation-contract:")
    return "<validation-contract-id>"


def _tool_name(action: str) -> str:
    return "_".join(_normalize(action).split())


def _requests_source_readback(normalized_action: str) -> bool:
    return (
        normalized_action.startswith(("readback ", "extract ", "map ", "trace "))
        or " archive readback" in normalized_action
        or normalized_action.endswith(" readback")
    )


def _requests_source_search(normalized_action: str) -> bool:
    return (
        normalized_action.startswith(("perform external source search ", "add "))
        and ("source" in normalized_action or "sources" in normalized_action)
    )


def _requests_validation_result(normalized_action: str) -> bool:
    return normalized_action.startswith(
        (
            "audit ",
            "confirm ",
            "verify ",
            "validate ",
            "compare ",
            "reproduce ",
            "reproduce or audit ",
            "run ",
            "test ",
        )
    )


def _requests_scope_or_model_definition(normalized_action: str) -> bool:
    return normalized_action.startswith(("define ", "specify ", "retain "))


def _requests_sensemaking_report(normalized_action: str) -> bool:
    return (
        normalized_action.startswith(("prove ", "prove or refute ", "construct ", "derive "))
        or (
            normalized_action.startswith("resolve ")
            and "scope limit" not in normalized_action
            and "or record scope" not in normalized_action
        )
    )


def _normalize(action: str) -> str:
    return " ".join(action.strip().lower().replace("_", " ").replace("-", " ").split())


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
