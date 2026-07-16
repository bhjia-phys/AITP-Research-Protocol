"""Capability rows and deep contracts for the reviewed M4 Skill lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from brain.v5.contracts import ContractError, ContractResult


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


@dataclass(frozen=True)
class SkillOperationSpec:
    operation: str
    mcp_name: str
    state_effect: str
    required_result_fields: tuple[str, ...]
    truth_source: str
    authorization_guard: str


_OPERATIONS = {
    "skill_distill_candidate": (
        "kernel_write",
        (
            "eligible",
            "candidate_id",
            "candidate_hash",
            "candidate_ref",
            "rejection_reasons",
            "missing_requirements",
            "write_executed",
        ),
        "typed_records",
        "candidate_only_no_install_no_claim_trust",
    ),
    "skill_assess_readiness": (
        "kernel_write",
        (
            "status",
            "candidate_ref",
            "readiness_ref",
            "blockers",
            "ready_for_package_preview",
            "write_executed",
        ),
        "typed_records_and_reviewed_exception_checkpoint",
        "readiness_report_only_no_install_no_claim_trust",
    ),
    "skill_build_package_preview": (
        "runtime_write",
        (
            "kind",
            "skill_id",
            "name",
            "semantic_version",
            "package_hash",
            "candidate_ref",
            "readiness_ref",
            "files",
            "preview_dir",
            "can_install_skill",
            "write_executed",
        ),
        "typed_records_and_deterministic_renderer",
        "derived_preview_only_no_install_no_claim_trust",
    ),
    "skill_record_package_proposal": (
        "kernel_write",
        (
            "skill_id",
            "name",
            "semantic_version",
            "package_hash",
            "tree_hash",
            "package_artifact_ref",
            "proposal_ref",
            "write_executed",
        ),
        "typed_records_and_content_addressed_package_blobs",
        "draft_proposal_only_no_install_no_claim_trust",
    ),
    "skill_plan_deployment": (
        "kernel_write",
        (
            "plan_ref",
            "operation",
            "checkpoint_action",
            "action_payload",
            "target_path",
            "package_hash",
            "patch_proposal_ref",
            "write_executed",
        ),
        "typed_records_and_current_project_skill_tree",
        "immutable_plan_only_exact_review_required",
    ),
    "skill_apply_deployment": (
        "kernel_write",
        (
            "install_receipt_ref",
            "checkpoint_application_ref",
            "operation",
            "skill_id",
            "semantic_version",
            "package_hash",
            "status",
            "replayed",
            "write_executed",
        ),
        "typed_records_project_tree_and_host_attestation",
        "host_attested_exact_skill_deployment_checkpoint",
    ),
    "skill_match_applicable": (
        "read_only",
        (
            "matches",
            "rejected",
            "checked_count",
            "orientation_only",
            "can_update_claim_trust",
            "write_executed",
        ),
        "typed_records_and_current_project_skill_tree",
        "read_only_orientation",
    ),
    "skill_record_usage": (
        "kernel_write",
        (
            "usage_ref",
            "consuming_tool_run_ref",
            "consuming_baseline_ref",
            "outcome",
            "package_hash",
            "write_executed",
        ),
        "typed_records_and_exact_installed_package_receipt",
        "exact_use_provenance_only_no_claim_trust",
    ),
    "skill_propose_patch": (
        "kernel_write",
        (
            "patch_proposal_ref",
            "current_version",
            "proposed_version",
            "old_package_hash",
            "new_package_hash",
            "diff_hash",
            "source_usage_refs",
            "review_status",
            "application_status",
            "write_executed",
        ),
        "typed_skill_usage_and_content_addressed_packages",
        "draft_patch_only_exact_review_required",
    ),
    "skill_build_validation_request": (
        "read_only",
        (
            "command_digest",
            "commands",
            "requires_m2_execution",
            "risk_class",
            "network_policy",
            "writable_roots",
            "timeout_seconds",
            "can_execute",
            "write_executed",
        ),
        "declared_package_validation_commands",
        "m2_high_risk_execution_required_for_external_commands",
    ),
}


def skill_operation_specs() -> dict[str, SkillOperationSpec]:
    return {
        operation: SkillOperationSpec(
            operation=operation,
            mcp_name=f"aitp_v5_{operation}",
            state_effect=state_effect,
            required_result_fields=required,
            truth_source=truth_source,
            authorization_guard=guard,
        )
        for operation, (state_effect, required, truth_source, guard) in _OPERATIONS.items()
    }


def skill_capability_rows() -> tuple[tuple[str, str, str, str, str, str], ...]:
    return tuple(
        (
            spec.operation,
            spec.mcp_name,
            f"aitp-v5 skill {spec.operation} --payload-file <args>",
            "skill_operation_result",
            spec.state_effect,
            "full",
        )
        for spec in skill_operation_specs().values()
    )


def skill_surface_names() -> tuple[str, ...]:
    return ("skill_operation_result",)


def skill_surface_purposes() -> dict[str, str]:
    return {
        "skill_operation_result": (
            "full-only reviewed Skill distillation, packaging, deployment, use, and patch result"
        )
    }


def skill_surface_validators():
    return {"skill_operation_result": require_valid_skill_operation_result}


def validate_skill_operation_result(
    payload: dict[str, Any],
    *,
    path: str = "skill_operation_result",
) -> ContractResult:
    result = ContractResult()
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return result
    if payload.get("kind") != "skill_operation_result":
        result.add(f"{path}.kind", "must be 'skill_operation_result'")
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    operation = payload.get("operation")
    spec = skill_operation_specs().get(operation)
    if spec is None:
        result.add(f"{path}.operation", "must name a registered Skill operation")
        return result
    if payload.get("state_effect") != spec.state_effect:
        result.add(f"{path}.state_effect", f"must be {spec.state_effect!r}")
    if payload.get("truth_source") != spec.truth_source:
        result.add(f"{path}.truth_source", f"must be {spec.truth_source!r}")
    if payload.get("authorization_guard") != spec.authorization_guard:
        result.add(
            f"{path}.authorization_guard",
            f"must be {spec.authorization_guard!r}",
        )
    kernel_write = spec.state_effect == "kernel_write"
    runtime_write = spec.state_effect == "runtime_write"
    expected_flags = {
        "writes_records": kernel_write,
        "writes_derived_state": runtime_write,
        "can_update_kernel_state": kernel_write,
        "orientation_only": not kernel_write,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "can_write_evidence": False,
        "can_install_skill": operation == "skill_apply_deployment",
        "can_execute_commands": False,
    }
    for field, expected in expected_flags.items():
        if payload.get(field) is not expected:
            result.add(f"{path}.{field}", f"must be {expected!r}")
    value = payload.get("result")
    if not isinstance(value, dict):
        result.add(f"{path}.result", "must be a mapping")
        return result
    for field in spec.required_result_fields:
        if field not in value:
            result.add(f"{path}.result.{field}", "is required")
    if not isinstance(value.get("write_executed"), bool):
        result.add(f"{path}.result.write_executed", "must be a boolean")
    _reject_nested_authority(value, result, f"{path}.result")
    _validate_operation_result(operation, value, result, f"{path}.result")
    return result


def _validate_operation_result(
    operation: str,
    value: dict[str, Any],
    result: ContractResult,
    path: str,
) -> None:
    if operation == "skill_distill_candidate":
        eligible = value.get("eligible")
        if not isinstance(eligible, bool):
            result.add(f"{path}.eligible", "must be a boolean")
        if eligible:
            _validate_pin(value.get("candidate_ref"), result, f"{path}.candidate_ref")
            if not _digest(value.get("candidate_hash")):
                result.add(f"{path}.candidate_hash", "must be lowercase sha256")
            if value.get("write_executed") is not True:
                result.add(f"{path}.write_executed", "eligible candidates must be written")
        elif value.get("candidate_ref") != {} or value.get("write_executed") is not False:
            result.add(path, "ineligible candidates must not carry a pin or execute a write")
    elif operation == "skill_assess_readiness":
        _validate_pin(value.get("candidate_ref"), result, f"{path}.candidate_ref")
        _validate_pin(value.get("readiness_ref"), result, f"{path}.readiness_ref")
    elif operation == "skill_build_package_preview":
        _validate_package_identity(value, result, path)
        _validate_pin(value.get("candidate_ref"), result, f"{path}.candidate_ref")
        _validate_pin(value.get("readiness_ref"), result, f"{path}.readiness_ref")
        if value.get("can_install_skill") is not False:
            result.add(f"{path}.can_install_skill", "preview cannot install a Skill")
    elif operation == "skill_record_package_proposal":
        _validate_package_identity(value, result, path)
        _validate_pin(value.get("package_artifact_ref"), result, f"{path}.package_artifact_ref")
        _validate_pin(value.get("proposal_ref"), result, f"{path}.proposal_ref")
        if not _digest(value.get("tree_hash")):
            result.add(f"{path}.tree_hash", "must be lowercase sha256")
    elif operation == "skill_plan_deployment":
        _validate_pin(value.get("plan_ref"), result, f"{path}.plan_ref")
        if not _digest(value.get("package_hash")):
            result.add(f"{path}.package_hash", "must be lowercase sha256")
        patch_ref = value.get("patch_proposal_ref")
        if patch_ref:
            _validate_pin(patch_ref, result, f"{path}.patch_proposal_ref")
    elif operation == "skill_apply_deployment":
        _validate_pin(value.get("install_receipt_ref"), result, f"{path}.install_receipt_ref")
        _validate_pin(
            value.get("checkpoint_application_ref"),
            result,
            f"{path}.checkpoint_application_ref",
        )
        _validate_package_identity(value, result, path, require_name=False)
        if value.get("status") != "completed":
            result.add(f"{path}.status", "must be completed")
    elif operation == "skill_match_applicable":
        for field in ("matches", "rejected"):
            items = value.get(field)
            if not isinstance(items, list):
                result.add(f"{path}.{field}", "must be a list")
                continue
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    result.add(f"{path}.{field}[{index}]", "must be a mapping")
                    continue
                _validate_package_identity(item, result, f"{path}.{field}[{index}]")
                _validate_pin(
                    item.get("proposal_ref"),
                    result,
                    f"{path}.{field}[{index}].proposal_ref",
                )
                _validate_pin(
                    item.get("install_receipt_ref"),
                    result,
                    f"{path}.{field}[{index}].install_receipt_ref",
                )
    elif operation == "skill_record_usage":
        _validate_pin(value.get("usage_ref"), result, f"{path}.usage_ref")
        _validate_pin(
            value.get("consuming_tool_run_ref"),
            result,
            f"{path}.consuming_tool_run_ref",
        )
        baseline = value.get("consuming_baseline_ref")
        if baseline:
            _validate_pin(baseline, result, f"{path}.consuming_baseline_ref")
        if not _digest(value.get("package_hash")):
            result.add(f"{path}.package_hash", "must be lowercase sha256")
    elif operation == "skill_propose_patch":
        _validate_pin(value.get("patch_proposal_ref"), result, f"{path}.patch_proposal_ref")
        for field in ("old_package_hash", "new_package_hash", "diff_hash"):
            if not _digest(value.get(field)):
                result.add(f"{path}.{field}", "must be lowercase sha256")
        for field in ("current_version", "proposed_version"):
            if not _semver(value.get(field)):
                result.add(f"{path}.{field}", "must be semantic version x.y.z")
        _validate_pin_list(value.get("source_usage_refs"), result, f"{path}.source_usage_refs")
    elif operation == "skill_build_validation_request":
        if not _digest(value.get("command_digest")):
            result.add(f"{path}.command_digest", "must be lowercase sha256")
        if value.get("can_execute") is not False:
            result.add(f"{path}.can_execute", "validation request cannot execute")


def _validate_package_identity(
    value: dict[str, Any],
    result: ContractResult,
    path: str,
    *,
    require_name: bool = True,
) -> None:
    if not isinstance(value.get("skill_id"), str) or not value.get("skill_id"):
        result.add(f"{path}.skill_id", "must be non-empty")
    if require_name and (not isinstance(value.get("name"), str) or not value.get("name")):
        result.add(f"{path}.name", "must be non-empty")
    if not _semver(value.get("semantic_version")):
        result.add(f"{path}.semantic_version", "must be semantic version x.y.z")
    if not _digest(value.get("package_hash")):
        result.add(f"{path}.package_hash", "must be lowercase sha256")


def _reject_nested_authority(value: Any, result: ContractResult, path: str) -> None:
    if isinstance(value, dict):
        forbidden = {
            "can_update_claim_trust": True,
            "can_write_evidence": True,
            "can_install_skill": True,
            "can_execute": True,
        }
        for field, forbidden_value in forbidden.items():
            if value.get(field) is forbidden_value:
                result.add(f"{path}.{field}", "must never grant this authority")
        for key, item in value.items():
            _reject_nested_authority(item, result, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_nested_authority(item, result, f"{path}[{index}]")


def _validate_pin(value: Any, result: ContractResult, path: str) -> None:
    if not isinstance(value, dict):
        result.add(path, "must be an exact pin mapping")
        return
    if not _typed_ref(value.get("record_ref")):
        result.add(f"{path}.record_ref", "must be a typed record ref")
    if not _digest(value.get("content_hash")):
        result.add(f"{path}.content_hash", "must be lowercase sha256")
    revision = value.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        result.add(f"{path}.revision", "must be a positive integer")


def _validate_pin_list(value: Any, result: ContractResult, path: str) -> None:
    if not isinstance(value, list):
        result.add(path, "must be a list")
        return
    for index, item in enumerate(value):
        _validate_pin(item, result, f"{path}[{index}]")


def _typed_ref(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    kind, separator, record_id = value.partition(":")
    return bool(separator and kind.strip() and record_id.strip())


def _digest(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256.fullmatch(value))


def _semver(value: Any) -> bool:
    return isinstance(value, str) and bool(_SEMVER.fullmatch(value))


def require_valid_skill_operation_result(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_skill_operation_result(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


__all__ = [
    "SkillOperationSpec",
    "require_valid_skill_operation_result",
    "skill_capability_rows",
    "skill_operation_specs",
    "skill_surface_names",
    "skill_surface_purposes",
    "skill_surface_validators",
    "validate_skill_operation_result",
]
