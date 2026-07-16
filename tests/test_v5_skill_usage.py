from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="skill-usage-test", host="pytest")


def _installed_skill(tmp_path, monkeypatch):
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.skill_install_transactions import apply_skill_install_plan
    from tests.test_v5_project_skill_install import _checkpoint, _plan, _proposal

    ws, proposal_ref, _artifact_ref, preview = _proposal(tmp_path, semantic_version="0.1.0")
    plan, plan_ref = _plan(ws, proposal_ref)
    checkpoint = _checkpoint(ws, plan_ref, monkeypatch)
    application = apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())
    receipt_ref = application.receipt_ref
    proposal = __import__(
        "brain.v5.pinned_record_refs", fromlist=["get_record_version"]
    ).get_record_version(ws, proposal_ref).record
    run_ref = __import__(
        "brain.v5.skill_install_planning", fromlist=["coerce_pin"]
    ).coerce_pin(proposal.execution_refs[0])
    validation_refs = tuple(
        __import__("brain.v5.skill_install_planning", fromlist=["coerce_pin"]).coerce_pin(item)
        for item in proposal.validation_refs[:1]
    )
    return ws, proposal_ref, receipt_ref, run_ref, validation_refs, preview


def _usage_record(ws, receipt_ref, run_ref, validation_refs, preview, **changes):
    from brain.v5.models import SkillUsageRecord
    from brain.v5.pinned_record_refs import get_record_version

    receipt = get_record_version(ws, receipt_ref).record
    values = {
        "usage_id": "librpa-chi0-use-1",
        "skill_id": preview.skill_id,
        "skill_name": preview.name,
        "semantic_version": preview.semantic_version,
        "package_hash": preview.package_hash,
        "install_receipt_ref": asdict(receipt_ref),
        "proposal_ref": dict(receipt.proposal_ref),
        "package_artifact_ref": dict(receipt.package_artifact_ref),
        "session_id": "session-librpa-1",
        "topic_id": "librpa",
        "focus_ref": "tool_recipe:librpa-chi0",
        "consuming_tool_run_ref": asdict(run_ref),
        "selected_selectors": {"software": ["librpa"], "task": ["chi0"]},
        "parameters": {"n_omega": 16},
        "outcome": "success",
        "validation_refs": [asdict(item) for item in validation_refs],
        "failure_refs": [],
        "created_at": datetime.now(UTC).isoformat(),
    }
    values.update(changes)
    return SkillUsageRecord(**values)


def test_records_exact_skill_use_and_backlinks_consuming_run(tmp_path, monkeypatch):
    from brain.v5.models import SkillUsageRecord, ToolRunRecord
    from brain.v5.pinned_record_refs import get_record_version, pin_current_record
    from brain.v5.skill_usage import record_skill_usage

    ws, _proposal_ref, receipt_ref, run_ref, validation_refs, preview = _installed_skill(
        tmp_path, monkeypatch
    )
    record = _usage_record(ws, receipt_ref, run_ref, validation_refs, preview)

    write = record_skill_usage(ws, record, actor=_actor())
    stored = get_record_version(
        ws,
        pin_current_record(ws, write.record_ref),
    ).record
    linked_run = get_record_version(
        ws,
        pin_current_record(ws, run_ref.record_ref),
    ).record

    assert isinstance(stored, SkillUsageRecord)
    assert stored.install_receipt_ref == asdict(receipt_ref)
    assert stored.consuming_tool_run_ref == asdict(run_ref)
    assert stored.can_update_claim_trust is False
    assert isinstance(linked_run, ToolRunRecord)
    assert write.record_ref in linked_run.skill_usage_refs


def test_usage_rejects_package_drift_and_unvalidated_success(tmp_path, monkeypatch):
    from brain.v5.skill_usage import record_skill_usage

    ws, _proposal_ref, receipt_ref, run_ref, validation_refs, preview = _installed_skill(
        tmp_path, monkeypatch
    )

    with pytest.raises(ValueError, match="package identity"):
        record_skill_usage(
            ws,
            _usage_record(
                ws,
                receipt_ref,
                run_ref,
                validation_refs,
                preview,
                package_hash="f" * 64,
            ),
            actor=_actor(),
        )
    with pytest.raises(ValueError, match="validated success"):
        record_skill_usage(
            ws,
            _usage_record(
                ws,
                receipt_ref,
                run_ref,
                (),
                preview,
                usage_id="librpa-chi0-use-unvalidated",
            ),
            actor=_actor(),
        )


def test_usage_backlinks_execution_baseline_without_changing_claim_trust(tmp_path, monkeypatch):
    from brain.v5.models import ExecutionBaselineRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_usage import record_skill_usage

    ws, _proposal_ref, receipt_ref, run_ref, validation_refs, preview = _installed_skill(
        tmp_path, monkeypatch
    )
    baseline = ExecutionBaselineRecord(
        baseline_id="librpa-chi0-baseline",
        topic_id="librpa",
        claim_id="chi0-workflow",
        run_ref=run_ref.record_ref,
        run_hash=run_ref.content_hash,
        run_revision=run_ref.revision,
        frozen_dependencies={},
    )
    baseline_write = RecordRepository(ws, actor=_actor()).write("execution_baselines", baseline)
    baseline_ref = pin_current_record(ws, baseline_write.record_ref)
    usage = _usage_record(
        ws,
        receipt_ref,
        run_ref,
        validation_refs,
        preview,
        usage_id="librpa-chi0-use-with-baseline",
        consuming_baseline_ref=asdict(baseline_ref),
    )

    write = record_skill_usage(ws, usage, actor=_actor())
    linked = RecordRepository(ws, actor=_actor()).read(baseline_write.record_ref).record

    assert linked.skill_usage_refs == [write.record_ref]
    assert RecordRepository(ws, actor=_actor()).list("trust_updates").records == ()


def test_patch_proposal_is_exact_evidence_backed_and_does_not_apply(tmp_path, monkeypatch):
    from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
    from brain.v5.project_skill_packages import build_skill_package_preview, record_skill_proposal
    from brain.v5.skill_package_artifacts import record_skill_package_artifact
    from brain.v5.skill_usage import build_skill_patch_proposal, record_skill_usage

    ws, proposal_ref, receipt_ref, run_ref, validation_refs, preview = _installed_skill(
        tmp_path, monkeypatch
    )
    usage_write = record_skill_usage(
        ws,
        _usage_record(ws, receipt_ref, run_ref, validation_refs, preview),
        actor=_actor(),
    )
    usage_ref = PinnedRecordRef(
        usage_write.record_ref,
        usage_write.content_hash,
        usage_write.revision,
    )
    old_proposal = get_record_version(ws, proposal_ref).record
    updated_preview = build_skill_package_preview(
        ws,
        old_proposal.readiness_ref,
        semantic_version="0.1.1",
    )
    record_skill_package_artifact(ws, updated_preview, actor=_actor())
    updated_write = record_skill_proposal(ws, updated_preview, actor=_actor())
    updated_ref = PinnedRecordRef(
        updated_write.record_ref,
        updated_write.content_hash,
        updated_write.revision,
    )

    patch = build_skill_patch_proposal(
        ws,
        [usage_ref],
        proposed_package_ref=updated_ref,
        patch_summary="Clarify the validated chi0 invocation and keep the stop rule.",
        patch_diff=[{"op": "clarify_step", "path": "procedure/submit"}],
        actor=_actor(),
    )

    assert patch.current_version == "0.1.0"
    assert patch.proposed_version == "0.1.1"
    assert patch.old_package_hash == preview.package_hash
    assert patch.new_package_hash == updated_preview.package_hash
    assert patch.source_usage_refs == [asdict(usage_ref)]
    assert patch.validation_refs == [asdict(validation_refs[0])]
    assert patch.review_status == "draft"
    assert patch.application_status == "not_applied"
    assert patch.requires_human_review is True
    assert not (ws.base / ".agents" / "skills" / "aitp-generated" / preview.name / "PATCHED").exists()
    assert get_record_version(ws, pin_current_record(ws, f"skill_patch_proposal:{patch.proposal_id}")).record == patch


def test_validated_failure_can_propose_a_boundary_patch(tmp_path, monkeypatch):
    from brain.v5.models import ValidationResultRecord
    from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
    from brain.v5.project_skill_packages import build_skill_package_preview, record_skill_proposal
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_package_artifacts import record_skill_package_artifact
    from brain.v5.skill_usage import build_skill_patch_proposal, record_skill_usage

    ws, proposal_ref, receipt_ref, run_ref, _validation_refs, preview = _installed_skill(
        tmp_path, monkeypatch
    )
    failed = ValidationResultRecord(
        result_id="librpa-validation-walltime-failure",
        topic_id="librpa",
        claim_id="",
        contract_id="chi0-contract",
        tool_run_id=run_ref.record_ref.partition(":")[2],
        status="failed",
        failure_modes_observed=["walltime before final chi0 block"],
        tool_run_ref=run_ref.record_ref,
        tool_run_hash=run_ref.content_hash,
        tool_run_revision=run_ref.revision,
    )
    failed_write = RecordRepository(ws, actor=_actor()).write("validation_results", failed)
    failed_ref = PinnedRecordRef(
        failed_write.record_ref,
        failed_write.content_hash,
        failed_write.revision,
    )
    usage_write = record_skill_usage(
        ws,
        _usage_record(
            ws,
            receipt_ref,
            run_ref,
            (failed_ref,),
            preview,
            usage_id="librpa-chi0-walltime-failure",
            outcome="failure",
            failure_refs=[asdict(failed_ref)],
        ),
        actor=_actor(),
    )
    usage_ref = PinnedRecordRef(
        usage_write.record_ref,
        usage_write.content_hash,
        usage_write.revision,
    )
    old_proposal = get_record_version(ws, proposal_ref).record
    updated_preview = build_skill_package_preview(
        ws, old_proposal.readiness_ref, semantic_version="0.1.1"
    )
    record_skill_package_artifact(ws, updated_preview, actor=_actor())
    updated_write = record_skill_proposal(ws, updated_preview, actor=_actor())
    updated_ref = PinnedRecordRef(
        updated_write.record_ref,
        updated_write.content_hash,
        updated_write.revision,
    )

    patch = build_skill_patch_proposal(
        ws,
        [usage_ref],
        proposed_package_ref=updated_ref,
        patch_summary="Add a walltime stop rule from a validated failed use.",
        patch_diff=[{"op": "add_stop_rule", "failure": "walltime"}],
        actor=_actor(),
    )

    assert patch.failure_refs == [asdict(failed_ref)]
    assert patch.validation_refs == [asdict(failed_ref)]


def test_patch_builder_rejects_harness_feedback_and_non_usage_refs(tmp_path, monkeypatch):
    from brain.v5.models import SkillPatchProposalRecord
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_usage import build_skill_patch_proposal

    ws, proposal_ref, _receipt_ref, _run_ref, _validation_refs, _preview = _installed_skill(
        tmp_path, monkeypatch
    )
    legacy = SkillPatchProposalRecord(
        proposal_id="legacy-harness-feedback",
        skill_name="legacy-feedback",
        current_version="0.0.0",
        proposed_version="0.0.1",
        patch_summary="Harness friction only.",
        patch_body="This is not Skill evidence.",
    )
    write = RecordRepository(ws, actor=_actor()).write("skill_patch_proposals", legacy)
    legacy_ref = PinnedRecordRef(write.record_ref, write.content_hash, write.revision)

    with pytest.raises(ValueError, match="Harness Feedback.*inadmissible"):
        build_skill_patch_proposal(
            ws,
            [legacy_ref],
            proposed_package_ref=proposal_ref,
            patch_summary="invalid",
            patch_diff=[{"op": "invalid"}],
            actor=_actor(),
        )


def test_patch_upgrade_uses_exact_patch_checkpoint_and_shared_transaction(tmp_path, monkeypatch):
    from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
    from brain.v5.project_skill_packages import build_skill_package_preview, record_skill_proposal
    from brain.v5.skill_install_transactions import (
        apply_skill_install_plan,
        build_skill_patch_install_plan,
    )
    from brain.v5.skill_package_artifacts import record_skill_package_artifact
    from brain.v5.skill_usage import build_skill_patch_proposal, record_skill_usage
    from tests.test_v5_project_skill_install import _checkpoint

    ws, proposal_ref, receipt_ref, run_ref, validation_refs, preview = _installed_skill(
        tmp_path, monkeypatch
    )
    usage_write = record_skill_usage(
        ws,
        _usage_record(ws, receipt_ref, run_ref, validation_refs, preview),
        actor=_actor(),
    )
    usage_ref = PinnedRecordRef(
        usage_write.record_ref,
        usage_write.content_hash,
        usage_write.revision,
    )
    old_proposal = get_record_version(ws, proposal_ref).record
    updated_preview = build_skill_package_preview(
        ws, old_proposal.readiness_ref, semantic_version="0.1.1"
    )
    record_skill_package_artifact(ws, updated_preview, actor=_actor())
    updated_write = record_skill_proposal(ws, updated_preview, actor=_actor())
    updated_ref = PinnedRecordRef(
        updated_write.record_ref,
        updated_write.content_hash,
        updated_write.revision,
    )
    patch = build_skill_patch_proposal(
        ws,
        [usage_ref],
        proposed_package_ref=updated_ref,
        patch_summary="Apply the reviewed 0.1.1 procedural clarification.",
        patch_diff=[{"op": "clarify_step", "path": "procedure/submit"}],
        actor=_actor(),
    )
    patch_ref = pin_current_record(ws, f"skill_patch_proposal:{patch.proposal_id}")
    plan = build_skill_patch_install_plan(
        ws,
        patch_ref,
        target_root=ws.base,
        hosts=["codex"],
        actor=_actor(),
    )
    plan_ref = pin_current_record(ws, f"skill_install_plan:{plan.plan_id}")

    assert plan.checkpoint_action == "apply_aitp_skill_patch"
    assert plan.patch_proposal_ref == asdict(patch_ref)
    assert plan.old_package_hash == preview.package_hash
    assert plan.new_package_hash == updated_preview.package_hash
    checkpoint = _checkpoint(ws, plan_ref, monkeypatch)
    application = apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())
    replay = apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())
    receipt = get_record_version(ws, application.receipt_ref).record

    assert receipt.operation == "upgrade"
    assert receipt.package_hash == updated_preview.package_hash
    assert receipt.patch_proposal_ref == asdict(patch_ref)
    assert replay.replayed is True
    assert replay.receipt_ref == application.receipt_ref

    from brain.v5.skill_applicability import SkillApplicabilityRequest, match_applicable_skills

    applicable = match_applicable_skills(
        ws,
        SkillApplicabilityRequest(
            tasks=("chi0",),
            software=("librpa",),
            environments=("slurm",),
        ),
    )
    assert [item.semantic_version for item in applicable.matches] == ["0.1.1"]
