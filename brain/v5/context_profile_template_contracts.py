"""Contracts for context profile report and closeout template catalogs."""

from __future__ import annotations

from typing import Any

from brain.v5.context_profile_templates import FORBIDDEN_USES
from brain.v5.context_profiles import builtin_context_profiles
from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_bool_value,
    _require_list,
    _require_mapping,
    _require_nonempty_str,
)


def validate_context_profile_template_catalog(
    payload: dict[str, Any],
    *,
    path: str = "context_profile_template_catalog",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result

    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != "context_profile_template_catalog":
        result.add(f"{path}.kind", "must be 'context_profile_template_catalog'")
    for key in ("catalog_version", "read_surface_effect", "truth_source"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("read_surface_effect") != "context_profile_template_catalog_only":
        result.add(f"{path}.read_surface_effect", "must be 'context_profile_template_catalog_only'")

    for key in (
        "requested_profile_ids",
        "unknown_profile_ids",
        "profile_ids",
        "templates",
        "report_template_profiles",
        "closeout_template_profiles",
    ):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_count(payload, "profile_ids", "profile_count", path, result)
    _require_count(payload, "templates", "template_count", path, result)
    _validate_catalog_profile_ids(payload, path, result)
    _validate_template_policy(payload.get("template_policy"), f"{path}.template_policy", result)

    if isinstance(payload.get("templates"), list):
        for index, template in enumerate(payload["templates"]):
            _validate_template(template, f"{path}.templates[{index}]", result)

    _require_top_level_flags(payload, path, result)
    return result


def require_valid_context_profile_template_catalog(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_context_profile_template_catalog(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_catalog_profile_ids(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    known_profile_ids = set(builtin_context_profiles())
    profile_ids = payload.get("profile_ids") if isinstance(payload.get("profile_ids"), list) else []
    unknown_ids = payload.get("unknown_profile_ids") if isinstance(payload.get("unknown_profile_ids"), list) else []
    templates = payload.get("templates") if isinstance(payload.get("templates"), list) else []

    for profile_id in profile_ids:
        if profile_id not in known_profile_ids:
            result.add(f"{path}.profile_ids", f"unknown profile id: {profile_id!r}")
    for profile_id in unknown_ids:
        if profile_id in known_profile_ids:
            result.add(f"{path}.unknown_profile_ids", f"known profile id listed as unknown: {profile_id!r}")
    template_profile_ids = [template.get("profile_id") for template in templates if isinstance(template, dict)]
    if profile_ids != template_profile_ids:
        result.add(f"{path}.profile_ids", "must match template profile order")


def _validate_template(template: Any, path: str, result: ContractResult) -> None:
    _require_mapping(template, path, result)
    if not isinstance(template, dict):
        return
    if template.get("kind") != "context_profile_template":
        result.add(f"{path}.kind", "must be 'context_profile_template'")
    for key in (
        "template_id",
        "profile_id",
        "task_type",
        "template_family",
        "template_role",
        "output_shape",
        "purpose",
        "truth_source",
    ):
        _require_nonempty_str(template, key, path, result)
    for key in (
        "required_sections",
        "can_say",
        "cannot_say_yet",
        "must_verify_before_trust_or_promotion",
        "reusable_experience_patterns",
        "read_only_surfaces_to_expand",
        "recommended_next_entrypoints",
        "forbidden_uses",
    ):
        _require_list(template.get(key), f"{path}.{key}", result)
        if key != "reusable_experience_patterns" and isinstance(template.get(key), list) and not template[key]:
            result.add(f"{path}.{key}", "must not be empty")
    _require_count(template, "required_sections", "section_count", path, result)
    if template.get("profile_id") not in builtin_context_profiles():
        result.add(f"{path}.profile_id", "must name a built-in context profile")
    if template.get("output_shape") not in {"report_template", "continuation_report_template", "closeout_template"}:
        result.add(f"{path}.output_shape", "must be a known template shape")
    _validate_required_sections(template.get("required_sections"), f"{path}.required_sections", result)
    _validate_report_or_closeout_template(template.get("report_template"), f"{path}.report_template", result)
    _validate_report_or_closeout_template(template.get("closeout_template"), f"{path}.closeout_template", result)
    _validate_template_policy(template.get("template_policy"), f"{path}.template_policy", result)
    _validate_trust_boundary(template.get("trust_boundary"), f"{path}.trust_boundary", result)
    _require_forbidden_uses(template.get("forbidden_uses"), f"{path}.forbidden_uses", result)
    _require_template_flags(template, path, result)


def _validate_required_sections(value: Any, path: str, result: ContractResult) -> None:
    if not isinstance(value, list):
        return
    for index, section in enumerate(value):
        item_path = f"{path}[{index}]"
        _require_mapping(section, item_path, result)
        if not isinstance(section, dict):
            continue
        for key in ("section_id", "heading", "purpose", "source_policy"):
            _require_nonempty_str(section, key, item_path, result)
        _require_bool_value(section.get("required"), True, f"{item_path}.required", result)
        _require_bool_value(section.get("summary_inputs_trusted"), False, f"{item_path}.summary_inputs_trusted", result)
        _require_bool_value(section.get("orientation_only"), True, f"{item_path}.orientation_only", result)
        _require_bool_value(section.get("source_support_result"), False, f"{item_path}.source_support_result", result)
        if section.get("claim_trust_mutation") != "none":
            result.add(f"{item_path}.claim_trust_mutation", "must be 'none'")


def _validate_report_or_closeout_template(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    for key in ("template_kind", "title_template"):
        _require_nonempty_str(value, key, path, result)
    _require_list(value.get("section_order"), f"{path}.section_order", result)
    _require_list(value.get("section_prompts"), f"{path}.section_prompts", result)
    _require_bool_value(value.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(value.get("orientation_only"), True, f"{path}.orientation_only", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")


def _validate_template_policy(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    _require_list(value.get("host_may_use_for"), f"{path}.host_may_use_for", result)
    _require_list(value.get("forbidden_uses"), f"{path}.forbidden_uses", result)
    _require_bool_value(
        value.get("requires_runtime_context_pack_before_final_answer"),
        True,
        f"{path}.requires_runtime_context_pack_before_final_answer",
        result,
    )
    _require_bool_value(
        value.get("requires_explicit_next_entrypoint"),
        True,
        f"{path}.requires_explicit_next_entrypoint",
        result,
    )
    for key in ("records_validation_result", "source_support_result", "summary_inputs_trusted", "can_update_claim_trust"):
        _require_bool_value(value.get(key), False, f"{path}.{key}", result)
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
    _require_forbidden_uses(value.get("forbidden_uses"), f"{path}.forbidden_uses", result)


def _validate_trust_boundary(value: Any, path: str, result: ContractResult) -> None:
    _require_mapping(value, path, result)
    if not isinstance(value, dict):
        return
    _require_bool_value(value.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(
        value.get("requires_typed_followup_for_claim_support"),
        True,
        f"{path}.requires_typed_followup_for_claim_support",
        result,
    )
    if not isinstance(value.get("requires_exact_source_anchors_for_literature_support"), bool):
        result.add(f"{path}.requires_exact_source_anchors_for_literature_support", "must be a boolean")
    if value.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")


def _require_top_level_flags(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    for key in (
        "summary_inputs_trusted",
        "can_update_kernel_state",
        "can_update_claim_trust",
        "records_validation_result",
        "source_support_result",
        "evidence_created",
        "validation_created",
        "write_executed",
    ):
        _require_bool_value(payload.get(key), False, f"{path}.{key}", result)
    for key in ("read_only", "requires_explicit_next_action", "orientation_only", "trust_update_forbidden"):
        _require_bool_value(payload.get(key), True, f"{path}.{key}", result)
    if payload.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")


def _require_template_flags(template: dict[str, Any], path: str, result: ContractResult) -> None:
    for key in (
        "summary_inputs_trusted",
        "can_update_kernel_state",
        "can_update_claim_trust",
        "records_validation_result",
        "source_support_result",
        "evidence_created",
        "validation_created",
        "write_executed",
    ):
        _require_bool_value(template.get(key), False, f"{path}.{key}", result)
    for key in ("read_only", "requires_explicit_next_action", "orientation_only", "trust_update_forbidden"):
        _require_bool_value(template.get(key), True, f"{path}.{key}", result)
    if template.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")


def _require_forbidden_uses(value: Any, path: str, result: ContractResult) -> None:
    uses = value if isinstance(value, list) else []
    for forbidden in FORBIDDEN_USES:
        if forbidden not in uses:
            result.add(path, f"must include {forbidden!r}")


def _require_count(payload: dict[str, Any], list_key: str, count_key: str, path: str, result: ContractResult) -> None:
    values = payload.get(list_key)
    if isinstance(values, list) and payload.get(count_key) != len(values):
        result.add(f"{path}.{count_key}", f"must equal {list_key} length")
