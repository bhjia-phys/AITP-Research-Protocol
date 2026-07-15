"""Read-only detection of validated procedural workflows suitable for skill review."""

from __future__ import annotations

from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.skill_candidates import propose_procedural_skill


def build_procedural_skill_candidates(
    ws: WorkspacePaths,
    *,
    topic_id: str,
) -> dict[str, Any]:
    repository = _repository(ws, "build_procedural_skill_candidates")
    recipes = {record.recipe_id: record for record in _records(repository, "tool_recipes")}
    runs = [record for record in _records(repository, "tool_runs") if record.topic_id == topic_id]
    validations = _records(repository, "validation_results")
    validation_by_run: dict[str, list[Any]] = {}
    for validation in validations:
        validation_by_run.setdefault(validation.tool_run_id, []).append(validation)

    candidates = []
    for recipe_id in sorted({run.recipe_id for run in runs}):
        recipe = recipes.get(recipe_id)
        recipe_runs = [run for run in runs if run.recipe_id == recipe_id]
        final_runs = [run for run in recipe_runs if run.lane == "final"]
        validated_runs = [
            run
            for run in final_runs
            if any(
                validation.status == "passed"
                for validation in validation_by_run.get(run.run_id, [])
            )
        ]
        supporting_validations = [
            validation
            for run in validated_runs
            for validation in validation_by_run.get(run.run_id, [])
            if validation.status == "passed"
        ]
        artifact_ids = _unique(
            artifact_id for run in validated_runs for artifact_id in run.artifact_ids
        )
        code_state_ids = _unique(
            code_state_id for run in validated_runs for code_state_id in run.code_state_ids
        )
        source_refs = _unique(
            source_ref for run in validated_runs for source_ref in run.source_refs
        )
        missing = []
        if recipe is None:
            missing.append("tool_recipe")
        if not final_runs:
            missing.append("final_tool_run")
        if not validated_runs:
            missing.append("passed_validation_for_final_run")
        if not artifact_ids:
            missing.append("artifact_provenance")
        if not (code_state_ids or source_refs):
            missing.append("code_or_source_provenance")
        if recipe is not None and not recipe.invariants:
            missing.append("applicability_or_failure_boundaries")

        candidate_id = prefixed_id(
            "skill-distillation",
            f"{topic_id}:{recipe_id}:{':'.join(run.run_id for run in validated_runs)}",
            max_slug=72,
        )
        candidates.append(
            {
                "candidate_id": candidate_id,
                "candidate_kind": "procedural_skill_candidate",
                "topic_id": topic_id,
                "recipe_id": recipe_id,
                "run_count": len(recipe_runs),
                "validated_final_run_count": len(validated_runs),
                "maturity": (
                    "repeated_validated_workflow"
                    if len(validated_runs) >= 2
                    else "single_validated_workflow"
                    if validated_runs
                    else "incomplete_workflow"
                ),
                "eligible_for_proposal": not missing,
                "missing_requirements": missing,
                "applicability": [recipe.purpose] if recipe is not None else [],
                "preconditions": (
                    _unique([*recipe.required_inputs, *recipe.invariants])
                    if recipe is not None
                    else []
                ),
                "supporting_records": [
                    *(f"tool_recipe:{recipe_id}",),
                    *(f"tool_run:{run.run_id}" for run in validated_runs),
                    *(
                        f"validation_result:{validation.result_id}"
                        for validation in supporting_validations
                    ),
                ],
                "execution_refs": [f"tool_run:{run.run_id}" for run in validated_runs],
                "validation_refs": [
                    f"validation_result:{validation.result_id}"
                    for validation in supporting_validations
                ],
                "source_refs": source_refs,
                "artifact_ids": artifact_ids,
                "code_state_ids": code_state_ids,
                "requires_human_review": True,
                "can_install_skill": False,
                "can_update_claim_trust": False,
            }
        )
    return {
        "ok": True,
        "kind": "procedural_skill_distillation_candidates",
        "topic_id": topic_id,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "excluded_record_kinds": [
            "physics_object",
            "object_relation",
            "physics_assertion",
            "insight",
            "derivation_chain",
            "derivation_step",
            "derivation_review",
            "exploratory_record",
            "sensemaking_report",
        ],
        "trigger_policy": [
            "evaluate at explicit closeout, validation completion, or user request",
            "do not evaluate after ordinary tool noise",
            "record missing requirements instead of drafting an incomplete skill",
        ],
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def propose_detected_procedural_skill(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    candidate_id: str,
    skill_name: str,
    current_version: str = "0.0.0",
    proposed_version: str = "0.1.0",
):
    report = build_procedural_skill_candidates(ws, topic_id=topic_id)
    candidate = next(
        (item for item in report["candidates"] if item["candidate_id"] == candidate_id),
        None,
    )
    if candidate is None:
        raise ValueError(f"procedural skill candidate not found: {candidate_id}")
    if not candidate["eligible_for_proposal"]:
        raise ValueError(
            "procedural skill candidate is incomplete: "
            + ", ".join(candidate["missing_requirements"])
        )
    recipe_id = candidate["recipe_id"]
    recipe = next(
        record
        for record in _records(_repository(ws, "propose_detected_procedural_skill"), "tool_recipes")
        if record.recipe_id == recipe_id
    )
    patch_body = (
        f"Use recipe `{recipe.recipe_id}` for {recipe.purpose.rstrip('.')} only when all "
        "recorded inputs and invariants hold. Preserve exact execution, source/code, artifact, "
        "and validation refs; stop and revalidate when any boundary changes."
    )
    return propose_procedural_skill(
        ws,
        skill_name=skill_name,
        current_version=current_version,
        proposed_version=proposed_version,
        patch_summary=f"Add the validated {recipe.recipe_id} workflow.",
        patch_body=patch_body,
        topic_ids=[topic_id],
        supporting_records=candidate["supporting_records"],
        applicability=candidate["applicability"],
        preconditions=candidate["preconditions"],
        validation_refs=candidate["validation_refs"],
        execution_refs=candidate["execution_refs"],
        source_refs=candidate["source_refs"],
        artifact_ids=candidate["artifact_ids"],
        installation_target="project",
    )


def _records(repository: RecordRepository, family: str) -> list[Any]:
    report = repository.list(family)
    if report.malformed:
        raise ValueError(f"cannot distill skills while {family} contains malformed records")
    return list(report.records)


def _repository(ws: WorkspacePaths, actor_id: str) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id=actor_id, host="aitp-v5"),
    )


def _unique(values) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
