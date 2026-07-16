from __future__ import annotations

from dataclasses import asdict, replace
from datetime import UTC, datetime

import pytest


def _pin_payload(write):
    return {
        "record_ref": write.record_ref,
        "content_hash": write.content_hash,
        "revision": write.revision,
    }


def test_librpa_skill_lifecycle_requires_review_and_records_exact_later_use(
    tmp_path,
    monkeypatch,
):
    from brain.v5.models import SkillUsageRecord, ToolRunRecord, ValidationResultRecord
    from brain.v5.paths import WorkspacePaths
    from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_facade import invoke_skill_operation
    from tests.test_v5_project_skill_install import _checkpoint
    from tests.test_v5_skill_distillation_records import _request

    actor = RecordActor(actor_type="tool", actor_id="gate4-e2e", host="pytest")
    ws, request = _request(tmp_path)
    ws = WorkspacePaths(tmp_path)

    distilled = invoke_skill_operation(
        ws,
        "skill_distill_candidate",
        {"request": asdict(request)},
    )
    assert distilled["result"]["eligible"] is True
    candidate_ref = distilled["result"]["candidate_ref"]

    readiness = invoke_skill_operation(
        ws,
        "skill_assess_readiness",
        {"candidate_ref": candidate_ref},
    )
    assert readiness["result"]["status"] == "ready"
    readiness_ref = readiness["result"]["readiness_ref"]

    preview = invoke_skill_operation(
        ws,
        "skill_build_package_preview",
        {"readiness_ref": readiness_ref, "semantic_version": "0.1.0"},
    )
    assert preview["result"]["can_install_skill"] is False

    proposed = invoke_skill_operation(
        ws,
        "skill_record_package_proposal",
        {"readiness_ref": readiness_ref, "semantic_version": "0.1.0"},
    )
    proposal_ref = proposed["result"]["proposal_ref"]
    assert proposed["result"]["write_executed"] is True

    planned = invoke_skill_operation(
        ws,
        "skill_plan_deployment",
        {
            "mode": "install",
            "proposal_ref": proposal_ref,
            "target_root": str(tmp_path),
            "hosts": ["codex"],
        },
    )
    plan_ref = planned["result"]["plan_ref"]
    target_path = planned["result"]["target_path"]
    assert planned["result"]["checkpoint_action"] == "install_aitp_skill"

    with pytest.raises(ValueError):
        invoke_skill_operation(
            ws,
            "skill_apply_deployment",
            {
                "plan_ref": plan_ref,
                "checkpoint": {
                    "request_ref": plan_ref,
                    "decision_ref": plan_ref,
                },
            },
        )
    assert not __import__("pathlib").Path(target_path).exists()

    checkpoint = _checkpoint(ws, PinnedRecordRef(**plan_ref), monkeypatch)
    applied = invoke_skill_operation(
        ws,
        "skill_apply_deployment",
        {
            "plan_ref": plan_ref,
            "checkpoint": {
                key: asdict(value) for key, value in checkpoint.items()
            },
        },
    )
    receipt_ref = applied["result"]["install_receipt_ref"]
    assert applied["result"]["status"] == "completed"

    matched = invoke_skill_operation(
        ws,
        "skill_match_applicable",
        {
            "request": {
                "software": ["librpa"],
                "tasks": ["chi0"],
                "environments": ["slurm"],
                "topic_ids": ["librpa"],
            }
        },
    )
    assert [item["semantic_version"] for item in matched["result"]["matches"]] == [
        "0.1.0"
    ]

    repository = RecordRepository(ws, actor=actor)
    source_run = get_record_version(ws, request.execution_refs[0]).record
    later_run = replace(
        source_run,
        run_id="librpa-run-after-skill-install",
        scientific_run_id="librpa-scientific-after-skill-install",
        skill_usage_refs=[],
    )
    run_write = repository.write("tool_runs", later_run)
    source_validation = get_record_version(ws, request.validation_refs[0]).record
    later_validation = replace(
        source_validation,
        result_id="librpa-validation-after-skill-install",
        tool_run_id=later_run.run_id,
        tool_run_ref=run_write.record_ref,
        tool_run_hash=run_write.content_hash,
        tool_run_revision=run_write.revision,
    )
    validation_write = repository.write("validation_results", later_validation)
    receipt = get_record_version(ws, PinnedRecordRef(**receipt_ref)).record
    usage = SkillUsageRecord(
        usage_id="librpa-skill-use-after-install",
        skill_id=proposed["result"]["skill_id"],
        skill_name=proposed["result"]["name"],
        semantic_version=proposed["result"]["semantic_version"],
        package_hash=proposed["result"]["package_hash"],
        install_receipt_ref=receipt_ref,
        proposal_ref=dict(receipt.proposal_ref),
        package_artifact_ref=dict(receipt.package_artifact_ref),
        session_id="session-librpa-e2e",
        topic_id="librpa",
        focus_ref="tool_recipe:librpa-chi0-hpc-v2",
        consuming_tool_run_ref=_pin_payload(run_write),
        selected_selectors={
            "software": ["librpa"],
            "task": ["chi0"],
            "environment": ["slurm"],
        },
        parameters={"n_omega": 16},
        outcome="success",
        validation_refs=[_pin_payload(validation_write)],
        failure_refs=[],
        created_at=datetime.now(UTC).isoformat(),
    )
    used = invoke_skill_operation(
        ws,
        "skill_record_usage",
        {"usage": asdict(usage)},
    )

    assert used["result"]["write_executed"] is True
    assert used["result"]["consuming_tool_run_ref"] == _pin_payload(run_write)
    linked_run = repository.read(run_write.record_ref).record
    assert isinstance(linked_run, ToolRunRecord)
    assert used["result"]["usage_ref"]["record_ref"] in linked_run.skill_usage_refs
    assert repository.list("trust_updates").records == ()


@pytest.mark.parametrize(
    "input_kinds",
    [
        ["definition", "formula", "derivation"],
        ["literature_summary"],
        ["interpretation", "insight"],
    ],
)
def test_conceptual_content_never_enters_skill_lifecycle(tmp_path, input_kinds):
    from brain.v5.skill_facade import invoke_skill_operation
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    result = invoke_skill_operation(
        ws,
        "skill_distill_candidate",
        {
            "request": {
                "title": "A conceptual statement",
                "summary": "This belongs in physics knowledge or Insight.",
                "workflow_kind": "conceptual",
                "input_kinds": input_kinds,
                "source_topic_ids": ["qg"],
                "ordered_steps": [],
                "parameter_contract": {},
                "inputs": [],
                "outputs": [],
                "prerequisites": [],
                "stop_rules": [],
                "known_failures": [],
                "applicability_selectors": {},
                "transfer_boundary": "",
                "package_requirements": [],
                "recipe_refs": [],
                "execution_refs": [],
                "validation_refs": [],
                "artifact_refs": [],
                "code_state_refs": [],
                "environment_refs": [],
                "source_program_refs": [],
                "source_refs": [],
            }
        },
    )

    assert result["result"]["eligible"] is False
    assert result["result"]["write_executed"] is False
    for family in (
        "skill_distillation_candidates",
        "skill_readiness_reports",
        "skill_package_artifacts",
        "skill_proposals",
        "skill_install_plans",
        "skill_install_receipts",
    ):
        assert list(ws.registry_dir(family).glob("*.md")) == []
