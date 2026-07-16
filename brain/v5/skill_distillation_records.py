"""Build and persist procedural Skill candidates from exact graph records."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import hashlib
import json
from typing import Any, Mapping

from brain.v5.ids import prefixed_id
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import get_record_version
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WriteResult
from brain.v5.skill_distillation_contracts import require_valid_skill_distillation_candidate
from brain.v5.skill_models import (
    CandidateBuildReport,
    SkillDistillationCandidateRecord,
    SkillDistillationRequest,
)


_SEMANTIC_INPUTS = frozenset({"definition", "formula", "derivation"})
_SOURCE_SUMMARY_INPUTS = frozenset({"literature_summary", "source_summary"})
_INSIGHT_INPUTS = frozenset({"interpretation", "insight"})


def build_skill_distillation_candidate(
    ws: WorkspacePaths,
    request: SkillDistillationRequest,
) -> CandidateBuildReport:
    """Compile one complete process candidate without writing canonical state."""

    rejection_reasons = _semantic_rejections(request.input_kinds)
    if rejection_reasons:
        return CandidateBuildReport(
            eligible=False,
            candidate=None,
            rejection_reasons=tuple(rejection_reasons),
        )
    pins = _request_pins(request)
    versions = {
        field: tuple(get_record_version(ws, pin) for pin in values)
        for field, values in pins.items()
    }
    _require_ref_kinds(versions)
    missing = _missing_requirements(request, versions)
    execution_keys = _independent_execution_keys(versions["execution_refs"])
    checked_refs = tuple(
        pin["record_ref"]
        for field in pins
        for pin in pins[field]
    )
    if missing:
        return CandidateBuildReport(
            eligible=False,
            candidate=None,
            missing_requirements=tuple(missing),
            independent_execution_count=len(execution_keys),
            checked_record_refs=checked_refs,
        )
    signature = _workflow_signature(request)
    created_at = max(
        str(version.frontmatter.get("created_at") or "")
        for group in versions.values()
        for version in group
    )
    candidate = SkillDistillationCandidateRecord(
        candidate_id=prefixed_id(
            "skill-candidate",
            f"{request.title}:{signature}",
            max_slug=72,
        ),
        title=request.title.strip(),
        summary=request.summary.strip(),
        workflow_kind=request.workflow_kind.strip(),
        workflow_signature=signature,
        input_kinds=_strings(request.input_kinds),
        source_topic_ids=_strings(request.source_topic_ids),
        source_program_refs=list(pins["source_program_refs"]),
        ordered_steps=[dict(step) for step in request.ordered_steps],
        parameter_contract=dict(request.parameter_contract),
        inputs=_strings(request.inputs),
        outputs=_strings(request.outputs),
        prerequisites=_strings(request.prerequisites),
        stop_rules=_strings(request.stop_rules),
        known_failures=[dict(item) for item in request.known_failures],
        recipe_refs=list(pins["recipe_refs"]),
        execution_refs=list(pins["execution_refs"]),
        validation_refs=list(pins["validation_refs"]),
        artifact_refs=list(pins["artifact_refs"]),
        code_state_refs=list(pins["code_state_refs"]),
        environment_refs=list(pins["environment_refs"]),
        source_refs=list(pins["source_refs"]),
        independent_execution_keys=list(execution_keys),
        applicability_selectors=dict(request.applicability_selectors),
        transfer_boundary=request.transfer_boundary.strip(),
        package_requirements=_strings(request.package_requirements),
        failure_boundary=request.failure_boundary.strip(),
        created_at=created_at,
    )
    require_valid_skill_distillation_candidate(candidate)
    return CandidateBuildReport(
        eligible=True,
        candidate=candidate,
        independent_execution_count=len(execution_keys),
        checked_record_refs=checked_refs,
    )


def record_skill_distillation_candidate(
    ws: WorkspacePaths,
    report: CandidateBuildReport,
    *,
    actor: RecordActor,
) -> WriteResult:
    if not report.eligible or report.candidate is None:
        reasons = (*report.rejection_reasons, *report.missing_requirements)
        raise ValueError("skill distillation candidate is not recordable: " + ", ".join(reasons))
    candidate = require_valid_skill_distillation_candidate(report.candidate)
    body = (
        f"# Skill Distillation Candidate: {candidate.title}\n\n"
        f"{candidate.summary}\n\n"
        "This is a review-required procedural candidate. It cannot install a Skill "
        "or update scientific claim trust.\n"
    )
    return RecordRepository(ws, actor=actor).write(
        "skill_distillation_candidates",
        candidate,
        body=body,
    )


def _semantic_rejections(input_kinds: tuple[str, ...]) -> list[str]:
    kinds = {str(item).strip() for item in input_kinds}
    reasons = []
    if kinds & _SEMANTIC_INPUTS:
        reasons.append("semantic_content_routes_to_m3")
    if kinds & _SOURCE_SUMMARY_INPUTS:
        reasons.append("source_summary_routes_to_m3")
    if kinds & _INSIGHT_INPUTS:
        reasons.append("insight_content_routes_to_m3")
    return reasons


def _request_pins(request: SkillDistillationRequest) -> dict[str, tuple[dict, ...]]:
    return {
        field: tuple(_pin_dict(item) for item in getattr(request, field))
        for field in (
            "recipe_refs",
            "execution_refs",
            "validation_refs",
            "artifact_refs",
            "code_state_refs",
            "environment_refs",
            "source_program_refs",
            "source_refs",
        )
    }


def _pin_dict(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return dict(value)
    raise ValueError("skill distillation provenance refs must be exact record pins")


def _require_ref_kinds(versions: Mapping[str, tuple[Any, ...]]) -> None:
    expected = {
        "recipe_refs": "tool_recipe:",
        "execution_refs": "tool_run:",
        "validation_refs": "validation_result:",
        "artifact_refs": "artifact:",
        "code_state_refs": "code_state:",
        "environment_refs": "execution_environment:",
        "source_program_refs": "research_program:",
        "source_refs": "source_asset:",
    }
    for field, prefix in expected.items():
        for version in versions[field]:
            if not version.pinned_ref.record_ref.startswith(prefix):
                raise ValueError(f"{field} requires {prefix.rstrip(':')} refs")


def _missing_requirements(
    request: SkillDistillationRequest,
    versions: Mapping[str, tuple[Any, ...]],
) -> list[str]:
    missing = []
    required = {
        "title": request.title.strip(),
        "summary": request.summary.strip(),
        "workflow_kind": request.workflow_kind.strip(),
        "source_topics": request.source_topic_ids,
        "ordered_steps": request.ordered_steps,
        "parameter_contract": request.parameter_contract,
        "inputs": request.inputs,
        "outputs": request.outputs,
        "prerequisites": request.prerequisites,
        "stop_rules": request.stop_rules,
        "failure_coverage": request.known_failures or request.failure_boundary.strip(),
        "applicability_selectors": request.applicability_selectors,
        "transfer_boundary": request.transfer_boundary.strip(),
        "package_requirements": request.package_requirements,
        "recipe_refs": versions["recipe_refs"],
        "execution_refs": versions["execution_refs"],
        "validation_refs": versions["validation_refs"],
        "artifact_refs": versions["artifact_refs"],
        "code_state_refs": versions["code_state_refs"],
        "environment_refs": versions["environment_refs"],
    }
    missing.extend(key for key, value in required.items() if not value)
    steps_complete = all(
        isinstance(step, Mapping)
        and str(step.get("step_id") or "").strip()
        and str(step.get("action") or "").strip()
        for step in request.ordered_steps
    )
    if request.ordered_steps and not steps_complete:
        missing.append("complete_ordered_steps")
    failures_complete = all(
        isinstance(item, Mapping)
        and str(item.get("failure") or "").strip()
        and str(item.get("detection") or "").strip()
        and isinstance(item.get("recovery"), list)
        and item["recovery"]
        for item in request.known_failures
    )
    if request.known_failures and not failures_complete:
        missing.append("complete_failure_recovery")
    runs = [version.record for version in versions["execution_refs"]]
    validations = [version.record for version in versions["validation_refs"]]
    run_ids = {run.run_id for run in runs}
    if {run.topic_id for run in runs} - set(request.source_topic_ids):
        missing.append("execution_topics_declared")
    recipe_ids = {version.record.recipe_id for version in versions["recipe_refs"]}
    if {run.recipe_id for run in runs} - recipe_ids:
        missing.append("execution_recipes_pinned")
    artifact_ids = {version.record.artifact_id for version in versions["artifact_refs"]}
    if {item for run in runs for item in run.artifact_ids} - artifact_ids:
        missing.append("execution_artifacts_pinned")
    code_state_ids = {
        version.record.code_state_id for version in versions["code_state_refs"]
    }
    if {item for run in runs for item in run.code_state_ids} - code_state_ids:
        missing.append("execution_code_states_pinned")
    environment_refs = {
        version.pinned_ref.record_ref for version in versions["environment_refs"]
    }
    if {run.environment_ref for run in runs if run.environment_ref} - environment_refs:
        missing.append("execution_environments_pinned")
    source_refs = {version.pinned_ref.record_ref for version in versions["source_refs"]}
    if {item for run in runs for item in run.source_refs} - source_refs:
        missing.append("execution_sources_pinned")
    if any(getattr(run, "lane", "") != "final" for run in runs):
        missing.append("final_execution_only")
    passed_run_ids = {
        validation.tool_run_id
        for validation in validations
        if getattr(validation, "status", "") == "passed"
    }
    if any(run.run_id not in passed_run_ids for run in runs):
        missing.append("passed_validation_for_each_execution")
    if {validation.tool_run_id for validation in validations} - run_ids:
        missing.append("validation_refs_bound_to_executions")
    if any(getattr(validation, "status", "") != "passed" for validation in validations):
        missing.append("passed_validations_only")
    return list(dict.fromkeys(missing))


def _independent_execution_keys(versions: tuple[Any, ...]) -> tuple[str, ...]:
    keys = []
    for version in versions:
        run = version.record
        payload = {
            "topic_id": run.topic_id,
            "scientific_run_id": run.scientific_run_id,
            "artifact_ids": sorted(run.artifact_ids),
            "code_state_ids": sorted(run.code_state_ids),
            "environment_ref": run.environment_ref,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        keys.append(hashlib.sha256(encoded).hexdigest())
    return tuple(dict.fromkeys(keys))


def _workflow_signature(request: SkillDistillationRequest) -> str:
    payload = {
        "workflow_kind": request.workflow_kind.strip(),
        "ordered_steps": list(request.ordered_steps),
        "parameter_contract": request.parameter_contract,
        "inputs": list(request.inputs),
        "outputs": list(request.outputs),
        "prerequisites": list(request.prerequisites),
        "stop_rules": list(request.stop_rules),
        "known_failures": list(request.known_failures),
        "applicability_selectors": request.applicability_selectors,
        "transfer_boundary": request.transfer_boundary.strip(),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _strings(values: tuple[str, ...]) -> list[str]:
    return list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))


__all__ = ["build_skill_distillation_candidate", "record_skill_distillation_candidate"]
