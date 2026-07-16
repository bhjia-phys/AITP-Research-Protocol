from __future__ import annotations

from dataclasses import replace

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="skill-distillation-test", host="pytest")


def _pin(write):
    from brain.v5.pinned_record_refs import PinnedRecordRef

    return PinnedRecordRef(write.record_ref, write.content_hash, write.revision)


def _graph_fixture(tmp_path, *, duplicate_retry: bool = False):
    from brain.v5.models import (
        ArtifactRecord,
        CodeStateRecord,
        ExecutionEnvironmentRecord,
        ToolRecipeRecord,
        ToolRunRecord,
        ValidationResultRecord,
    )
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa", context_id="condensed-matter", title="LibRPA")
    repository = RecordRepository(ws, actor=_actor())
    recipe = repository.write(
        "tool_recipes",
        ToolRecipeRecord(
            recipe_id="librpa-chi0-hpc-v2",
            tool_family="hpc",
            tool_name="librpa",
            purpose="Run and validate a pinned LibRPA chi0 calculation.",
            required_inputs=["structure", "k grid", "frequency grid"],
            expected_outputs=["chi0 blocks", "timing summary"],
            command_template=["srun", "librpa", "--input", "{input}"],
            parameter_roles={"n_omega": "frequency resolution"},
            environment_requirements=["pinned executable hash", "scheduler allocation"],
            failure_modes=["walltime before final chi0 block"],
            stop_rules=["stop when any required chi0 block is absent"],
            invariants=["same reciprocal-grid convention"],
            applicability_boundary="LibRPA chi0 runs with the pinned input schema.",
        ),
    )
    code = repository.write(
        "code_states",
        CodeStateRecord(
            code_state_id="librpa-code-a1",
            repo_id="librpa",
            upstream_remote="origin",
            upstream_branch="main",
            upstream_commit="a" * 40,
            local_branch="chi0-validation",
            worktree_path="/project/librpa",
            dirty=False,
        ),
    )
    environment = repository.write(
        "execution_environments",
        ExecutionEnvironmentRecord(
            environment_id="cluster-a-env",
            host="cluster-a",
            operating_system="linux",
            architecture="x86_64",
            modules=["gcc/13", "openmpi/5"],
            executable_hashes={"librpa": "b" * 64},
        ),
    )
    artifacts = []
    runs = []
    validations = []
    for index in (1, 2):
        artifact_id = "chi0-output-1" if duplicate_retry else f"chi0-output-{index}"
        if index == 1 or not duplicate_retry:
            artifact = repository.write(
                "artifacts",
                ArtifactRecord(
                    artifact_id=artifact_id,
                    topic_id="librpa",
                    claim_id="",
                    artifact_type="hpc_output_manifest",
                    uri=f"file:///runs/{artifact_id}.json",
                    summary="Pinned LibRPA output manifest.",
                    content_hash=str(index) * 64,
                    hash_algorithm="sha256",
                ),
            )
            artifacts.append(artifact)
        else:
            artifact = artifacts[0]
        run = repository.write(
            "tool_runs",
            ToolRunRecord(
                run_id=f"librpa-run-{index}",
                recipe_id="librpa-chi0-hpc-v2",
                tool_family="hpc",
                tool_name="librpa",
                topic_id="librpa",
                claim_id="",
                scientific_run_id=("librpa-scientific-1" if duplicate_retry else f"librpa-scientific-{index}"),
                lane="final",
                artifact_ids=[artifact_id],
                code_state_ids=["librpa-code-a1"],
                recipe_ref=recipe.record_ref,
                recipe_hash=recipe.content_hash,
                recipe_revision=recipe.revision,
                code_state_ref=code.record_ref,
                code_state_hash=code.content_hash,
                code_state_revision=code.revision,
                environment_ref=environment.record_ref,
                environment_hash=environment.content_hash,
                environment_revision=environment.revision,
                recorded_maturity="reproducible_candidate",
            ),
        )
        validation = repository.write(
            "validation_results",
            ValidationResultRecord(
                result_id=f"librpa-validation-{index}",
                topic_id="librpa",
                claim_id="",
                contract_id="chi0-contract",
                tool_run_id=f"librpa-run-{index}",
                status="passed",
                checked_outputs=["chi0 blocks", "timing summary"],
                artifact_ids=[artifact_id],
                tool_run_ref=run.record_ref,
                tool_run_hash=run.content_hash,
                tool_run_revision=run.revision,
            ),
        )
        runs.append(run)
        validations.append(validation)
    return ws, recipe, code, environment, artifacts, runs, validations


def _request(tmp_path, *, duplicate_retry: bool = False):
    from brain.v5.skill_models import SkillDistillationRequest

    ws, recipe, code, environment, artifacts, runs, validations = _graph_fixture(
        tmp_path,
        duplicate_retry=duplicate_retry,
    )
    request = SkillDistillationRequest(
        title="Validated LibRPA chi0 HPC workflow",
        summary="Submit, monitor, stop, and validate a pinned LibRPA chi0 run.",
        workflow_kind="hpc_software_workflow",
        input_kinds=("tool_recipe", "tool_run", "validation_result"),
        source_topic_ids=("librpa",),
        ordered_steps=(
            {"step_id": "prepare", "action": "Freeze input, code, and environment refs."},
            {"step_id": "submit", "action": "Submit the declared scheduler command."},
            {"step_id": "validate", "action": "Check every required chi0 block."},
        ),
        parameter_contract={
            "n_omega": {"role": "frequency resolution", "type": "integer", "required": True}
        },
        inputs=("structure", "k grid", "frequency grid"),
        outputs=("chi0 blocks", "timing summary"),
        prerequisites=("pinned executable hash", "scheduler allocation"),
        stop_rules=("stop when any required chi0 block is absent",),
        known_failures=(
            {
                "failure": "walltime before final chi0 block",
                "detection": "scheduler timeout and incomplete output manifest",
                "recovery": ["increase bounded walltime", "resume from a pinned checkpoint"],
            },
        ),
        applicability_selectors={
            "software": ["librpa"],
            "task": ["chi0"],
            "environment": ["slurm"],
        },
        transfer_boundary="Revalidate for changed input schema, code hash, or reciprocal-grid convention.",
        package_requirements=("SKILL.md", "manifest.json", "tests/chi0-smoke.json"),
        recipe_refs=(_pin(recipe),),
        execution_refs=tuple(_pin(item) for item in runs),
        validation_refs=tuple(_pin(item) for item in validations),
        artifact_refs=tuple(_pin(item) for item in artifacts),
        code_state_refs=(_pin(code),),
        environment_refs=(_pin(environment),),
    )
    return ws, request


def test_complete_procedure_builds_and_records_a_trust_neutral_candidate(tmp_path):
    from brain.v5.models import SkillDistillationCandidateRecord
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_distillation_records import (
        build_skill_distillation_candidate,
        record_skill_distillation_candidate,
    )

    ws, request = _request(tmp_path)
    report = build_skill_distillation_candidate(ws, request)

    assert report.eligible is True
    assert report.rejection_reasons == ()
    assert report.missing_requirements == ()
    assert report.independent_execution_count == 2
    assert report.candidate is not None
    assert report.candidate.execution_refs == [vars(item) for item in request.execution_refs]
    assert report.candidate.can_update_claim_trust is False

    written = record_skill_distillation_candidate(ws, report, actor=_actor())
    stored = RecordRepository(ws, actor=_actor()).read(written.record_ref).record

    assert isinstance(stored, SkillDistillationCandidateRecord)
    assert stored.candidate_id == report.candidate.candidate_id
    assert stored.status == "draft"
    assert stored.ordered_steps[2]["step_id"] == "validate"
    assert stored.known_failures[0]["recovery"]
    assert stored.can_update_claim_trust is False
    assert RecordRepository(ws, actor=_actor()).list("evidence").records == ()
    assert RecordRepository(ws, actor=_actor()).list("trust_updates").records == ()


def test_retries_preserve_each_run_but_collapse_independence(tmp_path):
    from brain.v5.skill_distillation_records import build_skill_distillation_candidate

    ws, request = _request(tmp_path, duplicate_retry=True)
    report = build_skill_distillation_candidate(ws, request)

    assert report.eligible is True
    assert report.independent_execution_count == 1
    assert len(report.candidate.execution_refs) == 2
    assert len(report.candidate.independent_execution_keys) == 1


def test_candidate_requires_run_topics_and_artifacts_to_match_declared_pins(tmp_path):
    from brain.v5.skill_distillation_records import build_skill_distillation_candidate

    ws, request = _request(tmp_path)
    wrong_topic = build_skill_distillation_candidate(
        ws,
        replace(request, source_topic_ids=("other-topic",)),
    )
    missing_artifact = build_skill_distillation_candidate(
        ws,
        replace(request, artifact_refs=request.artifact_refs[:1]),
    )

    assert wrong_topic.eligible is False
    assert "execution_topics_declared" in wrong_topic.missing_requirements
    assert missing_artifact.eligible is False
    assert "execution_artifacts_pinned" in missing_artifact.missing_requirements


def test_candidate_requires_each_validation_to_bind_a_selected_run(tmp_path):
    from brain.v5.models import ValidationResultRecord
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_distillation_records import build_skill_distillation_candidate

    ws, request = _request(tmp_path)
    unrelated = RecordRepository(ws, actor=_actor()).write(
        "validation_results",
        ValidationResultRecord(
            result_id="unrelated-validation",
            topic_id="librpa",
            claim_id="",
            contract_id="chi0-contract",
            tool_run_id="unselected-run",
            status="passed",
        ),
    )
    report = build_skill_distillation_candidate(
        ws,
        replace(request, validation_refs=(*request.validation_refs, _pin(unrelated))),
    )

    assert report.eligible is False
    assert "validation_refs_bound_to_executions" in report.missing_requirements


@pytest.mark.parametrize(
    ("input_kinds", "reason"),
    [
        (("definition", "formula", "derivation"), "semantic_content_routes_to_m3"),
        (("literature_summary",), "source_summary_routes_to_m3"),
        (("interpretation", "insight"), "insight_content_routes_to_m3"),
    ],
)
def test_semantic_or_source_summary_inputs_never_form_skill_candidates(
    tmp_path,
    input_kinds,
    reason,
):
    from brain.v5.skill_distillation_records import build_skill_distillation_candidate

    ws, request = _request(tmp_path)
    report = build_skill_distillation_candidate(
        ws,
        replace(request, input_kinds=input_kinds),
    )

    assert report.eligible is False
    assert reason in report.rejection_reasons
    assert report.candidate is None
    assert list(ws.registry_dir("skill_distillation_candidates").glob("*.md")) == []


def test_candidate_contract_forbids_claim_trust_authority(tmp_path):
    from brain.v5.skill_distillation_contracts import validate_skill_distillation_candidate
    from brain.v5.skill_distillation_records import build_skill_distillation_candidate

    ws, request = _request(tmp_path)
    candidate = build_skill_distillation_candidate(ws, request).candidate
    payload = vars(candidate) | {"can_update_claim_trust": True}

    result = validate_skill_distillation_candidate(payload)

    assert result.ok is False
    assert any(issue.path.endswith("can_update_claim_trust") for issue in result.issues)
