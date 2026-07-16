from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="skill-applicability-test", host="pytest")


def _proposal_with_selectors(tmp_path, monkeypatch):
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.project_skill_packages import (
        build_skill_package_preview,
        record_skill_proposal,
    )
    from brain.v5.skill_distillation_records import (
        build_skill_distillation_candidate,
        record_skill_distillation_candidate,
    )
    from brain.v5.skill_package_artifacts import record_skill_package_artifact
    from brain.v5.skill_readiness import assess_skill_readiness, record_skill_readiness_report
    from tests.test_v5_skill_distillation_records import _request

    ws, request = _request(tmp_path)
    request = replace(
        request,
        applicability_selectors={
            "domain": ["condensed-matter"],
            "task": ["chi0"],
            "software": ["librpa"],
            "repository": ["librpa"],
            "code_path": ["src/chi0.cpp"],
            "symbol": ["compute_chi0"],
            "physics_object": ["independent-particle-polarizability"],
            "formula": ["chi0-spectral-sum"],
            "parameter": ["n_omega"],
            "environment": ["slurm"],
            "cluster": ["dongfang"],
            "focus_kind": ["software-workflow"],
            "focus_ref": ["tool_recipe:librpa-chi0"],
            "topic": ["librpa"],
            "program": ["gw-methods"],
            "required_inputs": ["structure", "k-grid"],
            "required_records": ["code_state:librpa-main", "tool_recipe:librpa-chi0"],
            "exclusions": ["spin-orbit"],
        },
    )
    report = build_skill_distillation_candidate(ws, request)
    candidate_write = record_skill_distillation_candidate(ws, report, actor=_actor())
    candidate_ref = PinnedRecordRef(
        candidate_write.record_ref,
        candidate_write.content_hash,
        candidate_write.revision,
    )
    readiness = assess_skill_readiness(ws, candidate_ref)
    readiness_write = record_skill_readiness_report(ws, readiness, actor=_actor())
    readiness_ref = PinnedRecordRef(
        readiness_write.record_ref,
        readiness_write.content_hash,
        readiness_write.revision,
    )
    preview = build_skill_package_preview(ws, readiness_ref, semantic_version="1.2.3")
    record_skill_package_artifact(ws, preview, actor=_actor())
    proposal_write = record_skill_proposal(ws, preview, actor=_actor())
    proposal_ref = PinnedRecordRef(
        proposal_write.record_ref,
        proposal_write.content_hash,
        proposal_write.revision,
    )
    from brain.v5.skill_install_transactions import apply_skill_install_plan
    from tests.test_v5_project_skill_install import _checkpoint, _plan

    _plan_record, plan_ref = _plan(ws, proposal_ref)
    checkpoint = _checkpoint(ws, plan_ref, monkeypatch)
    application = apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())
    return ws, proposal_ref, application.receipt_ref, preview


def _matching_request(**changes):
    from brain.v5.skill_applicability import SkillApplicabilityRequest

    values = {
        "domains": ("condensed-matter",),
        "tasks": ("chi0",),
        "software": ("librpa",),
        "repositories": ("librpa",),
        "code_paths": ("src/chi0.cpp",),
        "symbols": ("compute_chi0",),
        "physics_objects": ("independent-particle-polarizability",),
        "formulas": ("chi0-spectral-sum",),
        "parameters": ("n_omega",),
        "environments": ("slurm",),
        "clusters": ("dongfang",),
        "focus_kinds": ("software-workflow",),
        "focus_refs": ("tool_recipe:librpa-chi0",),
        "topic_ids": ("librpa",),
        "program_ids": ("gw-methods",),
        "input_kinds": ("structure", "k-grid", "frequency-grid"),
        "available_record_refs": (
            "code_state:librpa-main",
            "tool_recipe:librpa-chi0",
        ),
    }
    values.update(changes)
    return SkillApplicabilityRequest(**values)


def test_matches_every_selector_with_level_reasons_and_no_claim_trust_shortcut(
    tmp_path, monkeypatch
):
    from brain.v5.skill_applicability import match_applicable_skills

    ws, proposal_ref, receipt_ref, preview = _proposal_with_selectors(tmp_path, monkeypatch)
    result = match_applicable_skills(ws, _matching_request())

    assert result.orientation_only is True
    assert result.can_update_claim_trust is False
    assert len(result.matches) == 1
    match = result.matches[0]
    assert match.skill_id == preview.skill_id
    assert match.semantic_version == "1.2.3"
    assert match.proposal_ref == vars(proposal_ref)
    assert match.install_receipt_ref == vars(receipt_ref)
    assert match.confidence == 1.0
    assert set(match.selector_reasons) == {
        "domain",
        "task",
        "software",
        "repository",
        "code_path",
        "symbol",
        "physics_object",
        "formula",
        "parameter",
        "environment",
        "cluster",
        "focus_kind",
        "focus_ref",
        "topic",
        "program",
        "required_inputs",
        "required_records",
        "exclusions",
    }
    assert all(reason.matched for reason in match.selector_reasons.values())
    assert "claim" not in " ".join(reason.reason for reason in match.selector_reasons.values()).lower()


def test_uninstalled_draft_package_is_not_advertised_as_applicable(tmp_path):
    from brain.v5.skill_applicability import SkillApplicabilityRequest, match_applicable_skills
    from tests.test_v5_project_skill_install import _proposal

    ws, _proposal_ref, _artifact_ref, _preview = _proposal(tmp_path)

    result = match_applicable_skills(
        ws,
        SkillApplicabilityRequest(
            tasks=("chi0",),
            software=("librpa",),
            environments=("slurm",),
        ),
    )

    assert result.checked_count == 0
    assert result.matches == ()
    assert result.rejected == ()


def test_exclusion_and_missing_required_record_fail_closed(tmp_path, monkeypatch):
    from brain.v5.skill_applicability import match_applicable_skills

    ws, _proposal_ref, _receipt_ref, _preview = _proposal_with_selectors(tmp_path, monkeypatch)

    excluded = match_applicable_skills(
        ws,
        _matching_request(software=("librpa", "spin-orbit")),
    )
    missing = match_applicable_skills(
        ws,
        _matching_request(available_record_refs=("code_state:librpa-main",)),
    )

    assert excluded.matches == ()
    assert excluded.rejected[0].selector_reasons["exclusions"].matched is False
    assert missing.matches == ()
    assert missing.rejected[0].selector_reasons["required_records"].matched is False


def test_reviewed_unexpired_scope_override_can_include_a_mismatch(tmp_path, monkeypatch):
    from brain.v5.models import HumanCheckpointRecord, ScopeRevalidationDecisionRecord
    from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_applicability import match_applicable_skills

    ws, proposal_ref, receipt_ref, _preview = _proposal_with_selectors(tmp_path, monkeypatch)
    repository = RecordRepository(ws, actor=_actor())
    proposal = get_record_version(ws, proposal_ref).record
    checkpoint = HumanCheckpointRecord(
        checkpoint_id="skill-applicability-override",
        topic_id="librpa",
        claim_id=receipt_ref.record_ref,
        reason="Review a narrow task-name override for this exact Skill package.",
        requested_by="skill-applicability-test",
        status="decided",
        decision="approve",
        rationale="The target task is an exact local alias for chi0.",
        decided_by="samur",
        decision_verified=True,
        decision_verification="host_receipt_verified",
        decision_receipt_hash="a" * 64,
        action="approve_scope_revalidation",
        effect_policy="scope_revalidation_only",
    )
    checkpoint_write = repository.write("checkpoints", checkpoint)
    checkpoint_ref = PinnedRecordRef(
        checkpoint_write.record_ref,
        checkpoint_write.content_hash,
        checkpoint_write.revision,
    )
    override = ScopeRevalidationDecisionRecord(
        decision_id="skill-applicability-override",
        bridge_ref=receipt_ref.record_ref,
        bridge_hash=receipt_ref.content_hash,
        bridge_revision=receipt_ref.revision,
        decision="approved",
        topic_id="librpa",
        program_id="gw-methods",
        target_scope_refs=["topic:librpa", "task:polarizability"],
        allowed_operations=["use_skill"],
        source_refs=[vars(receipt_ref), vars(proposal_ref)],
        applicability_conditions=["polarizability is the reviewed local alias for chi0"],
        validation_refs=[dict(proposal.validation_refs[0])],
        checkpoint_refs=[vars(checkpoint_ref)],
        expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    )
    override_write = repository.write("scope_revalidation_decisions", override)
    override_ref = PinnedRecordRef(
        override_write.record_ref,
        override_write.content_hash,
        override_write.revision,
    )

    result = match_applicable_skills(
        ws,
        _matching_request(tasks=("polarizability",), override_refs=(override_ref,)),
    )

    assert len(result.matches) == 1
    assert result.matches[0].match_source == "reviewed_override"
    assert result.matches[0].override_ref == vars(override_ref)


def test_expired_or_unreviewed_override_cannot_change_a_derived_mismatch(
    tmp_path, monkeypatch
):
    from brain.v5.skill_applicability import SkillApplicabilityRequest, match_applicable_skills

    ws, _proposal_ref, _receipt_ref, _preview = _proposal_with_selectors(tmp_path, monkeypatch)
    request = _matching_request(tasks=("polarizability",))

    assert match_applicable_skills(ws, request).matches == ()
    with pytest.raises(ValueError, match="pin a ScopeRevalidationDecisionRecord"):
        match_applicable_skills(
            ws,
            SkillApplicabilityRequest(**{**request.__dict__, "override_refs": ("checkpoint:open",)}),
        )
