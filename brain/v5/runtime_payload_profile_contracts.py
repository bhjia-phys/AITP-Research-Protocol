"""Contracts for host runtime payload profiles."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_list, _require_mapping
from brain.v5.runtime_payload_profiles import runtime_payload_profiles


def validate_runtime_payload_profiles(
    payload: Any,
    *,
    path: str = "runtime_payload_profiles",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result

    if payload.get("kind") != "runtime_payload_profiles":
        result.add(f"{path}.kind", "must be 'runtime_payload_profiles'")
    if payload.get("catalog_version") != "aitp.v5.runtime_payload_profiles.v1":
        result.add(
            f"{path}.catalog_version",
            "must be 'aitp.v5.runtime_payload_profiles.v1'",
        )
    if payload.get("truth_source") != "runtime_payload_profile_catalog":
        result.add(f"{path}.truth_source", "must be 'runtime_payload_profile_catalog'")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    _require_list(payload.get("profiles"), f"{path}.profiles", result)
    if isinstance(payload.get("profiles"), list):
        _validate_profiles(payload["profiles"], f"{path}.profiles", result)
        profile_index = [profile.get("profile_id") for profile in payload["profiles"] if isinstance(profile, dict)]
        if payload.get("profile_count") != len(payload["profiles"]):
            result.add(f"{path}.profile_count", "must equal len(profiles)")
        if payload.get("profile_index") != profile_index:
            result.add(f"{path}.profile_index", "must list profile ids in catalog order")
    if payload != runtime_payload_profiles():
        result.add(path, "must match runtime_payload_profiles()")
    return result


def require_valid_runtime_payload_profiles(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_runtime_payload_profiles(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_profiles(profiles: list[Any], path: str, result: ContractResult) -> None:
    ids: set[str] = set()
    for index, profile in enumerate(profiles):
        item_path = f"{path}[{index}]"
        _require_mapping(profile, item_path, result)
        if not isinstance(profile, dict):
            continue
        profile_id = profile.get("profile_id")
        if not isinstance(profile_id, str) or not profile_id:
            result.add(f"{item_path}.profile_id", "must be a non-empty string")
        elif profile_id in ids:
            result.add(f"{item_path}.profile_id", "must be unique")
        else:
            ids.add(profile_id)
        for key in (
            "host_event",
            "target_operation",
            "target_entrypoint",
            "target_record_action",
            "target_surface",
            "payload_key_case",
            "strict_boundary",
        ):
            if not isinstance(profile.get(key), str) or not profile.get(key):
                result.add(f"{item_path}.{key}", "must be a non-empty string")
        for key in ("required_host_fields", "optional_host_fields"):
            _require_list(profile.get(key), f"{item_path}.{key}", result)
        for key in ("capture_policy", "payload_template", "result_semantics"):
            _require_mapping(profile.get(key), f"{item_path}.{key}", result)

        if profile_id == "benchmark_adapter_run_to_tool_run":
            _validate_benchmark_adapter_profile(profile, item_path, result)
        if profile_id == "primitive_tool_lifecycle_to_tool_run":
            _validate_primitive_tool_lifecycle_profile(profile, item_path, result)


def _validate_benchmark_adapter_profile(
    profile: dict[str, Any],
    path: str,
    result: ContractResult,
) -> None:
    expected_required = [
        "adapter_id",
        "case_id",
        "action_id",
        "outcome",
        "observation",
        "output",
        "topic_id",
        "claim_id",
    ]
    if profile.get("host_event") != "benchmark_adapter_run":
        result.add(f"{path}.host_event", "must be 'benchmark_adapter_run'")
    if profile.get("target_operation") != "recordToolRun":
        result.add(f"{path}.target_operation", "must be 'recordToolRun'")
    if profile.get("target_entrypoint") != "aitp_v5_record_tool_run":
        result.add(f"{path}.target_entrypoint", "must be 'aitp_v5_record_tool_run'")
    if profile.get("target_surface") != "tool_run_record":
        result.add(f"{path}.target_surface", "must be 'tool_run_record'")
    if profile.get("required_host_fields") != expected_required:
        result.add(f"{path}.required_host_fields", "must name the benchmark adapter run contract")
    _validate_capture_policy(
        profile,
        path,
        result,
        expected_capture_mode="controlled_auto",
        expected_host_trigger="ResearchAction.run_benchmark_adapter",
        expected_tool_call_requirement=False,
    )
    template = profile.get("payload_template")
    if isinstance(template, dict):
        if template.get("tool_family") != "benchmark_adapter":
            result.add(f"{path}.payload_template.tool_family", "must be 'benchmark_adapter'")
        if template.get("evidence_status") != "unreviewed":
            result.add(f"{path}.payload_template.evidence_status", "must be 'unreviewed'")
    semantics = profile.get("result_semantics")
    if isinstance(semantics, dict):
        if semantics.get("records_validation_result") is not False:
            result.add(f"{path}.result_semantics.records_validation_result", "must be false")
        if semantics.get("claim_trust_mutation") != "none":
            result.add(f"{path}.result_semantics.claim_trust_mutation", "must be 'none'")
        if semantics.get("can_update_claim_trust") is not False:
            result.add(f"{path}.result_semantics.can_update_claim_trust", "must be false")


def _validate_primitive_tool_lifecycle_profile(
    profile: dict[str, Any],
    path: str,
    result: ContractResult,
) -> None:
    expected_required = [
        "tool_call_id",
        "tool_name",
        "status",
        "output_summary",
        "topic_id",
        "claim_id",
    ]
    if profile.get("host_event") != "primitive_tool_lifecycle_completed":
        result.add(f"{path}.host_event", "must be 'primitive_tool_lifecycle_completed'")
    if profile.get("target_operation") != "recordToolRun":
        result.add(f"{path}.target_operation", "must be 'recordToolRun'")
    if profile.get("target_entrypoint") != "aitp_v5_record_tool_run":
        result.add(f"{path}.target_entrypoint", "must be 'aitp_v5_record_tool_run'")
    if profile.get("target_surface") != "tool_run_record":
        result.add(f"{path}.target_surface", "must be 'tool_run_record'")
    if profile.get("required_host_fields") != expected_required:
        result.add(f"{path}.required_host_fields", "must name the primitive tool lifecycle contract")
    _validate_capture_policy(
        profile,
        path,
        result,
        expected_capture_mode="explicit_request",
        expected_host_trigger="ResearchAction.capture_primitive_tool_run",
        expected_tool_call_requirement=True,
    )
    template = profile.get("payload_template")
    if isinstance(template, dict):
        if template.get("tool_family") != "primitive_tool":
            result.add(f"{path}.payload_template.tool_family", "must be 'primitive_tool'")
        if template.get("evidence_status") != "unreviewed":
            result.add(f"{path}.payload_template.evidence_status", "must be 'unreviewed'")
    semantics = profile.get("result_semantics")
    if isinstance(semantics, dict):
        if semantics.get("records_validation_result") is not False:
            result.add(f"{path}.result_semantics.records_validation_result", "must be false")
        if semantics.get("claim_trust_mutation") != "none":
            result.add(f"{path}.result_semantics.claim_trust_mutation", "must be 'none'")
        if semantics.get("can_update_claim_trust") is not False:
            result.add(f"{path}.result_semantics.can_update_claim_trust", "must be false")


def _validate_capture_policy(
    profile: dict[str, Any],
    path: str,
    result: ContractResult,
    *,
    expected_capture_mode: str,
    expected_host_trigger: str,
    expected_tool_call_requirement: bool,
) -> None:
    policy = profile.get("capture_policy")
    if not isinstance(policy, dict):
        return
    if policy.get("capture_mode") != expected_capture_mode:
        result.add(f"{path}.capture_policy.capture_mode", f"must be '{expected_capture_mode}'")
    if policy.get("host_trigger") != expected_host_trigger:
        result.add(f"{path}.capture_policy.host_trigger", f"must be '{expected_host_trigger}'")
    if policy.get("requires_configured_bridge") is not True:
        result.add(f"{path}.capture_policy.requires_configured_bridge", "must be true")
    if policy.get("requires_scoped_topic_and_claim") is not True:
        result.add(f"{path}.capture_policy.requires_scoped_topic_and_claim", "must be true")
    if policy.get("requires_tool_call_id") is not expected_tool_call_requirement:
        result.add(
            f"{path}.capture_policy.requires_tool_call_id",
            f"must be {str(expected_tool_call_requirement).lower()}",
        )
    if not isinstance(policy.get("capture_granularity"), str) or not policy.get("capture_granularity"):
        result.add(f"{path}.capture_policy.capture_granularity", "must be a non-empty string")
    if policy.get("missing_scope_behavior") != "skip_with_reason":
        result.add(f"{path}.capture_policy.missing_scope_behavior", "must be 'skip_with_reason'")
    if policy.get("bulk_auto_capture") is not False:
        result.add(f"{path}.capture_policy.bulk_auto_capture", "must be false")
    if policy.get("records_validation_result") is not False:
        result.add(f"{path}.capture_policy.records_validation_result", "must be false")
    if policy.get("claim_trust_mutation") != "none":
        result.add(f"{path}.capture_policy.claim_trust_mutation", "must be 'none'")
    if policy.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.capture_policy.summary_inputs_trusted", "must be false")
    if policy.get("can_update_claim_trust") is not False:
        result.add(f"{path}.capture_policy.can_update_claim_trust", "must be false")
