"""JSON coercion and dispatch for the full reviewed M4 Skill lifecycle."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from brain.v5.models import (
    SkillPackageArtifactRecord,
    SkillProposalRecord,
    SkillUsageRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.project_skill_packages import build_skill_package_preview, record_skill_proposal
from brain.v5.record_envelope import RecordActor
from brain.v5.skill_applicability import SkillApplicabilityRequest, match_applicable_skills
from brain.v5.skill_distillation_records import (
    build_skill_distillation_candidate,
    record_skill_distillation_candidate,
)
from brain.v5.skill_install_planning import build_skill_install_plan, build_skill_rollback_plan
from brain.v5.skill_install_transactions import apply_skill_install_plan
from brain.v5.skill_models import SkillDistillationRequest
from brain.v5.skill_package_artifacts import record_skill_package_artifact
from brain.v5.skill_patch_install_planning import build_skill_patch_install_plan
from brain.v5.skill_readiness import assess_skill_readiness, record_skill_readiness_report
from brain.v5.skill_surface_contracts import (
    require_valid_skill_operation_result,
    skill_operation_specs,
)
from brain.v5.skill_usage import build_skill_patch_proposal, record_skill_usage
from brain.v5.skill_validation_execution import classify_skill_validation_policy


_ACTOR = RecordActor(actor_type="tool", actor_id="skill-facade", host="aitp-v5")


def decode_skill_payload(payload_json: str) -> dict[str, Any]:
    try:
        payload = json.loads(payload_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Skill facade payload_json must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("Skill facade payload must be a JSON object")
    return payload


def invoke_skill_operation(
    ws: WorkspacePaths,
    operation: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if operation not in skill_operation_specs():
        raise ValueError(f"unsupported Skill operation: {operation}")
    if operation == "skill_distill_candidate":
        value = _distill(ws, payload)
    elif operation == "skill_assess_readiness":
        value = _assess_readiness(ws, payload)
    elif operation == "skill_build_package_preview":
        value = _build_preview(ws, payload)
    elif operation == "skill_record_package_proposal":
        value = _record_package_proposal(ws, payload)
    elif operation == "skill_plan_deployment":
        value = _plan_deployment(ws, payload)
    elif operation == "skill_apply_deployment":
        value = _apply_deployment(ws, payload)
    elif operation == "skill_match_applicable":
        value = {
            **asdict(match_applicable_skills(ws, _applicability_request(payload.get("request")))),
            "write_executed": False,
        }
    elif operation == "skill_record_usage":
        value = _record_usage(ws, payload)
    elif operation == "skill_propose_patch":
        value = _propose_patch(ws, payload)
    elif operation == "skill_build_validation_request":
        commands = _mapping_list(payload.get("commands", []), "commands")
        value = {
            **asdict(classify_skill_validation_policy(commands)),
            "write_executed": False,
        }
    else:  # pragma: no cover - registry and dispatch are audited together.
        raise ValueError(f"unsupported Skill operation: {operation}")
    return _skill_result(operation, value)


def _distill(ws: WorkspacePaths, payload: Mapping[str, Any]) -> dict[str, Any]:
    report = build_skill_distillation_candidate(
        ws,
        _distillation_request(payload.get("request")),
    )
    base = {
        "eligible": report.eligible,
        "candidate_id": report.candidate.candidate_id if report.candidate else "",
        "candidate_hash": "",
        "candidate_ref": {},
        "rejection_reasons": list(report.rejection_reasons),
        "missing_requirements": list(report.missing_requirements),
        "independent_execution_count": report.independent_execution_count,
        "checked_record_refs": list(report.checked_record_refs),
        "can_update_claim_trust": False,
        "write_executed": False,
    }
    if not report.eligible:
        return base
    written = record_skill_distillation_candidate(ws, report, actor=_ACTOR)
    pin = _write_pin(written)
    return {
        **base,
        "candidate_hash": pin["content_hash"],
        "candidate_ref": pin,
        "write_executed": True,
    }


def _assess_readiness(ws: WorkspacePaths, payload: Mapping[str, Any]) -> dict[str, Any]:
    candidate_ref = _pin(payload.get("candidate_ref"), "candidate_ref")
    exception = payload.get("expert_exception_ref")
    report = assess_skill_readiness(
        ws,
        candidate_ref,
        expert_exception_ref=(
            _pin(exception, "expert_exception_ref") if exception else None
        ),
    )
    written = record_skill_readiness_report(ws, report, actor=_ACTOR)
    return {
        "status": report.status,
        "candidate_ref": asdict(candidate_ref),
        "readiness_ref": _write_pin(written),
        "blockers": list(report.blockers),
        "required_actions": list(report.required_actions),
        "ready_for_package_preview": report.ready_for_package_preview,
        "can_install_skill": False,
        "can_update_claim_trust": False,
        "write_executed": True,
    }


def _build_preview(ws: WorkspacePaths, payload: Mapping[str, Any]) -> dict[str, Any]:
    preview = build_skill_package_preview(
        ws,
        _pin(payload.get("readiness_ref"), "readiness_ref"),
        semantic_version=str(payload.get("semantic_version") or "0.1.0"),
    )
    return {**preview.contract_payload(), "write_executed": True}


def _record_package_proposal(
    ws: WorkspacePaths,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    preview = build_skill_package_preview(
        ws,
        _pin(payload.get("readiness_ref"), "readiness_ref"),
        semantic_version=str(payload.get("semantic_version") or "0.1.0"),
    )
    artifact_write = record_skill_package_artifact(ws, preview, actor=_ACTOR)
    proposal_write = record_skill_proposal(ws, preview, actor=_ACTOR)
    artifact_ref = _write_pin(artifact_write)
    proposal_ref = _write_pin(proposal_write)
    artifact = get_record_version(ws, PinnedRecordRef(**artifact_ref)).record
    proposal = get_record_version(ws, PinnedRecordRef(**proposal_ref)).record
    if not isinstance(artifact, SkillPackageArtifactRecord) or not isinstance(
        proposal, SkillProposalRecord
    ):
        raise RuntimeError("Skill package writes did not resolve to their typed records")
    return {
        "skill_id": proposal.skill_id,
        "name": proposal.name,
        "semantic_version": proposal.semantic_version,
        "package_hash": proposal.package_hash,
        "tree_hash": artifact.tree_hash,
        "package_artifact_ref": artifact_ref,
        "proposal_ref": proposal_ref,
        "preview_dir": preview.preview_dir,
        "review_status": proposal.review_status,
        "application_status": proposal.application_status,
        "can_install_skill": False,
        "can_update_claim_trust": False,
        "write_executed": True,
    }


def _plan_deployment(ws: WorkspacePaths, payload: Mapping[str, Any]) -> dict[str, Any]:
    mode = str(payload.get("mode") or "install")
    target_root = str(payload.get("target_root") or "")
    hosts = _strings(payload.get("hosts"), "hosts")
    if mode == "install":
        plan = build_skill_install_plan(
            ws,
            _pin(payload.get("proposal_ref"), "proposal_ref"),
            target_root,
            hosts,
            actor=_ACTOR,
        )
    elif mode == "rollback":
        plan = build_skill_rollback_plan(
            ws,
            _pin(payload.get("proposal_ref"), "proposal_ref"),
            target_root,
            hosts,
            expected_current_package_hash=str(
                payload.get("expected_current_package_hash") or ""
            ),
            actor=_ACTOR,
        )
    elif mode == "patch":
        plan = build_skill_patch_install_plan(
            ws,
            _pin(payload.get("patch_proposal_ref"), "patch_proposal_ref"),
            target_root,
            hosts,
            actor=_ACTOR,
        )
    else:
        raise ValueError("Skill deployment mode must be install, rollback, or patch")
    plan_ref = pin_current_record(ws, f"skill_install_plan:{plan.plan_id}")
    return {
        "plan_ref": asdict(plan_ref),
        "operation": plan.operation,
        "checkpoint_action": plan.checkpoint_action,
        "action_payload": dict(plan.action_payload),
        "target_path": plan.target_path,
        "package_hash": plan.package_hash,
        "patch_proposal_ref": dict(plan.patch_proposal_ref),
        "can_install_skill": False,
        "can_update_claim_trust": False,
        "write_executed": True,
    }


def _apply_deployment(ws: WorkspacePaths, payload: Mapping[str, Any]) -> dict[str, Any]:
    checkpoint = _mapping(payload.get("checkpoint"), "checkpoint")
    application = apply_skill_install_plan(
        ws,
        _pin(payload.get("plan_ref"), "plan_ref"),
        checkpoint,
        actor=_ACTOR,
    )
    receipt = application.record
    return {
        "install_receipt_ref": asdict(application.receipt_ref),
        "checkpoint_application_ref": asdict(application.checkpoint_application_ref),
        "operation": receipt.operation,
        "skill_id": receipt.skill_id,
        "semantic_version": receipt.semantic_version,
        "package_hash": receipt.package_hash,
        "status": receipt.status,
        "replayed": application.replayed,
        "can_update_claim_trust": False,
        "write_executed": not application.replayed,
    }


def _record_usage(ws: WorkspacePaths, payload: Mapping[str, Any]) -> dict[str, Any]:
    usage = _usage_record(payload.get("usage"))
    written = record_skill_usage(ws, usage, actor=_ACTOR)
    return {
        "usage_ref": _write_pin(written),
        "consuming_tool_run_ref": dict(usage.consuming_tool_run_ref),
        "consuming_baseline_ref": dict(usage.consuming_baseline_ref),
        "outcome": usage.outcome,
        "package_hash": usage.package_hash,
        "can_update_claim_trust": False,
        "write_executed": True,
    }


def _propose_patch(ws: WorkspacePaths, payload: Mapping[str, Any]) -> dict[str, Any]:
    patch = build_skill_patch_proposal(
        ws,
        _pins(payload.get("usage_refs"), "usage_refs"),
        proposed_package_ref=_pin(
            payload.get("proposed_package_ref"), "proposed_package_ref"
        ),
        patch_summary=str(payload.get("patch_summary") or ""),
        patch_diff=_mapping_list(payload.get("patch_diff"), "patch_diff"),
        actor=_ACTOR,
    )
    patch_ref = pin_current_record(ws, f"skill_patch_proposal:{patch.proposal_id}")
    return {
        "patch_proposal_ref": asdict(patch_ref),
        "current_version": patch.current_version,
        "proposed_version": patch.proposed_version,
        "old_package_hash": patch.old_package_hash,
        "new_package_hash": patch.new_package_hash,
        "diff_hash": patch.diff_hash,
        "source_usage_refs": list(patch.source_usage_refs),
        "review_status": patch.review_status,
        "application_status": patch.application_status,
        "can_install_skill": False,
        "can_update_claim_trust": False,
        "write_executed": True,
    }


def _skill_result(operation: str, value: Any) -> dict[str, Any]:
    spec = skill_operation_specs()[operation]
    kernel_write = spec.state_effect == "kernel_write"
    runtime_write = spec.state_effect == "runtime_write"
    payload = {
        "ok": True,
        "kind": "skill_operation_result",
        "operation": operation,
        "state_effect": spec.state_effect,
        "writes_records": kernel_write,
        "writes_derived_state": runtime_write,
        "result": _jsonable(value),
        "truth_source": spec.truth_source,
        "authorization_guard": spec.authorization_guard,
        "summary_inputs_trusted": False,
        "orientation_only": not kernel_write,
        "can_update_kernel_state": kernel_write,
        "can_update_claim_trust": False,
        "can_write_evidence": False,
        "can_install_skill": operation == "skill_apply_deployment",
        "can_execute_commands": False,
    }
    return require_valid_skill_operation_result(payload)


def _distillation_request(value: Any) -> SkillDistillationRequest:
    data = _mapping(value, "request")
    return SkillDistillationRequest(
        title=str(data.get("title") or ""),
        summary=str(data.get("summary") or ""),
        workflow_kind=str(data.get("workflow_kind") or ""),
        input_kinds=_strings(data.get("input_kinds"), "input_kinds"),
        source_topic_ids=_strings(data.get("source_topic_ids"), "source_topic_ids"),
        ordered_steps=tuple(_mapping_list(data.get("ordered_steps"), "ordered_steps")),
        parameter_contract=_mapping(data.get("parameter_contract"), "parameter_contract"),
        inputs=_strings(data.get("inputs"), "inputs", allow_empty=True),
        outputs=_strings(data.get("outputs"), "outputs", allow_empty=True),
        prerequisites=_strings(data.get("prerequisites"), "prerequisites", allow_empty=True),
        stop_rules=_strings(data.get("stop_rules"), "stop_rules", allow_empty=True),
        known_failures=tuple(_mapping_list(data.get("known_failures"), "known_failures")),
        applicability_selectors=_mapping(
            data.get("applicability_selectors"), "applicability_selectors"
        ),
        transfer_boundary=str(data.get("transfer_boundary") or ""),
        package_requirements=_strings(
            data.get("package_requirements"), "package_requirements", allow_empty=True
        ),
        recipe_refs=_pins(data.get("recipe_refs"), "recipe_refs"),
        execution_refs=_pins(data.get("execution_refs"), "execution_refs"),
        validation_refs=_pins(data.get("validation_refs"), "validation_refs"),
        artifact_refs=_pins(data.get("artifact_refs"), "artifact_refs"),
        code_state_refs=_pins(data.get("code_state_refs"), "code_state_refs"),
        environment_refs=_pins(data.get("environment_refs"), "environment_refs"),
        source_program_refs=_pins(
            data.get("source_program_refs", []), "source_program_refs"
        ),
        source_refs=_pins(data.get("source_refs", []), "source_refs"),
        failure_boundary=str(data.get("failure_boundary") or ""),
    )


def _applicability_request(value: Any) -> SkillApplicabilityRequest:
    data = _mapping(value, "request")
    string_fields = (
        "domains",
        "tasks",
        "software",
        "repositories",
        "code_paths",
        "symbols",
        "physics_objects",
        "formulas",
        "parameters",
        "environments",
        "clusters",
        "focus_kinds",
        "focus_refs",
        "topic_ids",
        "program_ids",
        "input_kinds",
        "available_record_refs",
    )
    values = {
        field: _strings(data.get(field, []), field, allow_empty=True)
        for field in string_fields
    }
    return SkillApplicabilityRequest(
        **values,
        override_refs=_pins(data.get("override_refs", []), "override_refs"),
    )


def _usage_record(value: Any) -> SkillUsageRecord:
    data = _mapping(value, "usage")
    return SkillUsageRecord(
        usage_id=str(data.get("usage_id") or ""),
        skill_id=str(data.get("skill_id") or ""),
        skill_name=str(data.get("skill_name") or ""),
        semantic_version=str(data.get("semantic_version") or ""),
        package_hash=str(data.get("package_hash") or ""),
        install_receipt_ref=asdict(_pin(data.get("install_receipt_ref"), "install_receipt_ref")),
        proposal_ref=asdict(_pin(data.get("proposal_ref"), "proposal_ref")),
        package_artifact_ref=asdict(
            _pin(data.get("package_artifact_ref"), "package_artifact_ref")
        ),
        session_id=str(data.get("session_id") or ""),
        topic_id=str(data.get("topic_id") or ""),
        focus_ref=str(data.get("focus_ref") or ""),
        consuming_tool_run_ref=asdict(
            _pin(data.get("consuming_tool_run_ref"), "consuming_tool_run_ref")
        ),
        selected_selectors=_mapping(
            data.get("selected_selectors"), "selected_selectors"
        ),
        parameters=_mapping(data.get("parameters"), "parameters"),
        outcome=str(data.get("outcome") or ""),
        validation_refs=[asdict(item) for item in _pins(data.get("validation_refs"), "validation_refs")],
        failure_refs=[asdict(item) for item in _pins(data.get("failure_refs"), "failure_refs")],
        consuming_baseline_ref=(
            asdict(_pin(data.get("consuming_baseline_ref"), "consuming_baseline_ref"))
            if data.get("consuming_baseline_ref")
            else {}
        ),
        created_at=str(data.get("created_at") or ""),
    )


def _pin(value: Any, field_name: str) -> PinnedRecordRef:
    data = _mapping(value, field_name)
    return PinnedRecordRef(
        record_ref=str(data.get("record_ref") or ""),
        content_hash=str(data.get("content_hash") or ""),
        revision=data.get("revision"),
    )


def _pins(value: Any, field_name: str) -> tuple[PinnedRecordRef, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a list")
    return tuple(_pin(item, field_name) for item in value)


def _mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _mapping_list(value: Any, field_name: str) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a list")
    return [_mapping(item, field_name) for item in value]


def _strings(
    value: Any,
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field_name} must contain non-empty strings")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(value)


def _write_pin(write: Any) -> dict[str, Any]:
    return {
        "record_ref": write.record_ref,
        "content_hash": write.content_hash,
        "revision": write.revision,
    }


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_jsonable(item) for item in value]
    if isinstance(value, bytes):
        raise TypeError("Skill facade does not inline package bytes")
    return value


__all__ = ["decode_skill_payload", "invoke_skill_operation"]
