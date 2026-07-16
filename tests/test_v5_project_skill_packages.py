from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="project-skill-package-test", host="pytest")


def _preview(tmp_path, *, semantic_version="0.1.0"):
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.project_skill_packages import build_skill_package_preview
    from brain.v5.skill_readiness import assess_skill_readiness, record_skill_readiness_report
    from tests.test_v5_skill_readiness import _candidate

    ws, candidate_ref, candidate = _candidate(tmp_path)
    readiness = assess_skill_readiness(ws, candidate_ref)
    write = record_skill_readiness_report(ws, readiness, actor=_actor())
    readiness_ref = PinnedRecordRef(write.record_ref, write.content_hash, write.revision)
    return (
        ws,
        candidate_ref,
        readiness_ref,
        candidate,
        build_skill_package_preview(
            ws,
            readiness_ref,
            semantic_version=semantic_version,
        ),
    )


def test_host_neutral_preview_is_complete_compact_and_not_installed(tmp_path):
    ws, candidate_ref, readiness_ref, candidate, preview = _preview(tmp_path)

    assert preview.skill_id == "aitp-generated/validated-librpa-chi0-hpc-workflow"
    assert preview.semantic_version == "0.1.0"
    assert set(preview.files) == {"SKILL.md", "manifest.json", "tests/chi0-smoke.json"}
    manifest = json.loads(preview.files["manifest.json"])
    skill_text = preview.files["SKILL.md"].decode("utf-8")
    assert manifest["namespace"] == "aitp-generated"
    assert manifest["candidate_ref"] == vars(candidate_ref)
    assert manifest["readiness_ref"] == vars(readiness_ref)
    assert manifest["package_hash"] == preview.package_hash
    assert manifest["artifact_identity"]["package_artifact_ref"].startswith(
        "skill_package_artifact:"
    )
    assert manifest["artifact_identity"]["tree_hash_owner"] == (
        "canonical_skill_package_artifact_record"
    )
    assert manifest["validation_commands"][0]["kind"] == "aitp_builtin_declarative"
    assert manifest["validation_commands"][0]["network"] == "forbidden"
    assert manifest["validation_commands"][0]["writes"] == []
    assert manifest["source_topic_ids"] == candidate.source_topic_ids
    for field in (
        "recipe_refs",
        "execution_refs",
        "validation_refs",
        "artifact_refs",
        "code_state_refs",
        "environment_refs",
        "source_program_refs",
        "source_refs",
    ):
        assert manifest[field] == getattr(candidate, field)
        for pinned in getattr(candidate, field):
            assert pinned["record_ref"] in skill_text
    assert manifest["failure_basis"]["known_failures"] == candidate.known_failures
    assert "## When To Use" in skill_text
    assert "## Procedure" in skill_text
    assert "## Stop Rules" in skill_text
    assert "## Failure Recovery" in skill_text
    assert "## Applicability" in skill_text
    assert "## Non-Applicability" in skill_text
    assert "## AITP Expansion Refs" in skill_text
    assert candidate.summary not in skill_text
    assert not (ws.base / ".agents" / "skills" / "aitp-generated").exists()
    assert Path(preview.preview_dir, "SKILL.md").is_file()


def test_proposal_pins_exact_package_artifact_and_cannot_install_or_change_trust(tmp_path):
    from brain.v5.models import SkillProposalRecord
    from brain.v5.project_skill_packages import record_skill_proposal
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_package_artifacts import record_skill_package_artifact

    ws, _candidate_ref, _readiness_ref, candidate, preview = _preview(tmp_path)
    artifact_write = record_skill_package_artifact(ws, preview, actor=_actor())
    proposal_write = record_skill_proposal(ws, preview, actor=_actor())
    proposal = RecordRepository(ws, actor=_actor()).read(proposal_write.record_ref).record

    assert isinstance(proposal, SkillProposalRecord)
    assert proposal.package_artifact_ref == {
        "record_ref": artifact_write.record_ref,
        "content_hash": artifact_write.content_hash,
        "revision": artifact_write.revision,
    }
    assert proposal.package_hash == preview.package_hash
    for field in (
        "recipe_refs",
        "execution_refs",
        "validation_refs",
        "artifact_refs",
        "code_state_refs",
        "environment_refs",
        "source_program_refs",
        "source_refs",
    ):
        assert getattr(proposal, field) == getattr(candidate, field)
    assert len(proposal.tree_hash) == 64
    assert proposal.review_status == "draft"
    assert proposal.application_status == "not_applied"
    assert proposal.requires_human_review is True
    assert proposal.can_install_skill is False
    assert proposal.can_update_claim_trust is False
    assert not (ws.base / ".agents" / "skills" / "aitp-generated").exists()
    assert RecordRepository(ws, actor=_actor()).list("evidence").records == ()
    assert RecordRepository(ws, actor=_actor()).list("trust_updates").records == ()

    with pytest.raises(ValueError, match="must remain draft"):
        replace(proposal, review_status="approved")

    from brain.v5.project_skill_contracts import validate_skill_proposal

    invalid = asdict(proposal)
    invalid["package_artifact_ref"]["revision"] = 0
    invalid["validation_commands"][0]["can_install_skill"] = True
    result = validate_skill_proposal(invalid)
    assert result.ok is False
    assert any("package_artifact_ref.revision" in issue.path for issue in result.issues)
    assert any("can_install_skill" in issue.path for issue in result.issues)


def test_nondefault_semantic_version_is_preserved_through_artifact_and_proposal(tmp_path):
    from brain.v5.models import SkillPackageArtifactRecord, SkillProposalRecord
    from brain.v5.project_skill_packages import record_skill_proposal
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_package_artifacts import record_skill_package_artifact

    ws, _candidate_ref, _readiness_ref, _candidate, preview = _preview(
        tmp_path,
        semantic_version="1.2.3",
    )

    artifact_write = record_skill_package_artifact(ws, preview, actor=_actor())
    proposal_write = record_skill_proposal(ws, preview, actor=_actor())
    repository = RecordRepository(ws, actor=_actor())
    artifact = repository.read(artifact_write.record_ref).record
    proposal = repository.read(proposal_write.record_ref).record

    assert isinstance(artifact, SkillPackageArtifactRecord)
    assert isinstance(proposal, SkillProposalRecord)
    assert artifact.semantic_version == "1.2.3"
    assert proposal.semantic_version == "1.2.3"


def test_project_skill_contract_rejects_manifest_or_nested_trust_inflation(tmp_path):
    from brain.v5.project_skill_contracts import validate_skill_package_preview

    _ws, _candidate_ref, _readiness_ref, _candidate, preview = _preview(tmp_path)
    payload = preview.contract_payload()
    payload["manifest"]["can_update_claim_trust"] = True

    result = validate_skill_package_preview(payload)

    assert result.ok is False
    assert any("can_update_claim_trust" in issue.path for issue in result.issues)

    invalid_path = preview.contract_payload()
    invalid_path["files"][0]["path"] = []
    path_result = validate_skill_package_preview(invalid_path)
    assert path_result.ok is False
    assert any("files[0].path" in issue.path for issue in path_result.issues)
