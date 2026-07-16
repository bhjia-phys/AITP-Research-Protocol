from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import shutil

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="skill-package-artifact-test", host="pytest")


def _ready_candidate(tmp_path):
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.skill_readiness import assess_skill_readiness, record_skill_readiness_report
    from tests.test_v5_skill_readiness import _candidate

    ws, candidate_ref, candidate = _candidate(tmp_path)
    report = assess_skill_readiness(ws, candidate_ref)
    write = record_skill_readiness_report(ws, report, actor=_actor())
    readiness_ref = PinnedRecordRef(write.record_ref, write.content_hash, write.revision)
    return ws, candidate_ref, readiness_ref, candidate


def test_package_artifact_binds_canonical_tree_rows_and_local_blob_receipts(tmp_path):
    from brain.v5.models import SkillPackageArtifactRecord
    from brain.v5.project_skill_packages import build_skill_package_preview
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_package_artifacts import record_skill_package_artifact

    ws, _candidate_ref, readiness_ref, _candidate = _ready_candidate(tmp_path)
    preview = build_skill_package_preview(ws, readiness_ref)
    write = record_skill_package_artifact(ws, preview, actor=_actor())
    artifact = RecordRepository(ws, actor=_actor()).read(write.record_ref).record

    assert isinstance(artifact, SkillPackageArtifactRecord)
    assert artifact.package_hash == preview.package_hash
    assert artifact.tree_hash == _tree_hash(artifact.files)
    assert [row["path"] for row in artifact.files] == sorted(
        (row["path"] for row in artifact.files),
        key=lambda value: value.encode("utf-8"),
    )
    assert {row["mode"] for row in artifact.files} == {"0644"}
    for row in artifact.files:
        assert row["length"] == len(preview.files[row["path"]])
        assert row["sha256"] == hashlib.sha256(preview.files[row["path"]]).hexdigest()
        assert row["blob_receipt_ref"].startswith("artifact_blob_receipt:")
        assert len(row["blob_receipt_content_hash"]) == 64
    assert artifact.renderer_blob_ref.startswith("artifact_blob_receipt:")
    assert artifact.can_update_claim_trust is False

    from brain.v5.project_skill_contracts import validate_skill_package_artifact

    unsorted = asdict(artifact)
    unsorted["files"] = list(reversed(unsorted["files"]))
    result = validate_skill_package_artifact(unsorted)
    assert result.ok is False
    assert any("UTF-8 path order" in issue.message for issue in result.issues)

    malformed = asdict(artifact)
    malformed["candidate_ref"]["content_hash"] = "not-a-hash"
    malformed["files"][0]["blob_receipt_revision"] = 0
    malformed_result = validate_skill_package_artifact(malformed)
    assert malformed_result.ok is False
    assert any("candidate_ref.content_hash" in issue.path for issue in malformed_result.issues)
    assert any("blob_receipt_revision" in issue.path for issue in malformed_result.issues)


def test_preview_rebuild_uses_exact_blobs_after_derived_files_are_deleted(tmp_path):
    from brain.v5.project_skill_packages import build_skill_package_preview
    from brain.v5.skill_package_artifacts import (
        rebuild_skill_package_preview,
        record_skill_package_artifact,
    )

    ws, _candidate_ref, readiness_ref, _candidate = _ready_candidate(tmp_path)
    preview = build_skill_package_preview(ws, readiness_ref)
    write = record_skill_package_artifact(ws, preview, actor=_actor())
    shutil.rmtree(preview.preview_dir)

    rebuilt = rebuild_skill_package_preview(ws, write.record_ref, write.content_hash, write.revision)

    assert rebuilt.package_hash == preview.package_hash
    assert rebuilt.files == preview.files
    assert Path(rebuilt.preview_dir, "SKILL.md").read_bytes() == preview.files["SKILL.md"]
    assert Path(rebuilt.preview_dir, "manifest.json").read_bytes() == preview.files["manifest.json"]


def test_preview_rebuild_removes_stale_derived_files(tmp_path):
    from brain.v5.project_skill_packages import build_skill_package_preview
    from brain.v5.skill_package_artifacts import (
        rebuild_skill_package_preview,
        record_skill_package_artifact,
    )

    ws, _candidate_ref, readiness_ref, _candidate = _ready_candidate(tmp_path)
    preview = build_skill_package_preview(ws, readiness_ref)
    write = record_skill_package_artifact(ws, preview, actor=_actor())
    stale = Path(preview.preview_dir, "stale.txt")
    stale.write_text("not part of the package", encoding="utf-8")

    rebuild_skill_package_preview(ws, write.record_ref, write.content_hash, write.revision)

    assert not stale.exists()


def test_preview_rebuild_rejects_manifest_and_artifact_identity_mismatch(tmp_path):
    from brain.v5.models import SkillPackageArtifactRecord
    from brain.v5.project_skill_packages import (
        build_skill_package_preview,
        package_artifact_id,
    )
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_package_artifacts import (
        rebuild_skill_package_preview,
        record_skill_package_artifact,
    )

    ws, _candidate_ref, readiness_ref, _candidate = _ready_candidate(tmp_path)
    preview = build_skill_package_preview(ws, readiness_ref)
    write = record_skill_package_artifact(ws, preview, actor=_actor())
    repository = RecordRepository(ws, actor=_actor())
    artifact = repository.read(write.record_ref).record
    assert isinstance(artifact, SkillPackageArtifactRecord)
    forged_skill_id = "aitp-generated/forged-identity"
    forged = replace(
        artifact,
        artifact_id=package_artifact_id(forged_skill_id, artifact.semantic_version),
        skill_id=forged_skill_id,
    )
    forged_write = repository.write("skill_package_artifacts", forged)

    with pytest.raises(ValueError, match="manifest.*identity"):
        rebuild_skill_package_preview(
            ws,
            forged_write.record_ref,
            forged_write.content_hash,
            forged_write.revision,
        )


def test_proposal_rejects_artifact_that_does_not_bind_the_exact_preview_tree(tmp_path):
    from brain.v5.artifact_blobs import capture_artifact_content
    from brain.v5.models import SkillPackageArtifactRecord
    from brain.v5.project_skill_packages import (
        build_skill_package_preview,
        package_artifact_id,
        record_skill_proposal,
    )
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_package_artifacts import package_tree_hash

    ws, _candidate_ref, readiness_ref, _candidate = _ready_candidate(tmp_path)
    preview = build_skill_package_preview(ws, readiness_ref)
    renderer = capture_artifact_content(ws, b"forged renderer", actor=_actor())
    forged = SkillPackageArtifactRecord(
        artifact_id=package_artifact_id(preview.skill_id, preview.semantic_version),
        skill_id=preview.skill_id,
        semantic_version=preview.semantic_version,
        package_hash=preview.package_hash,
        tree_hash=package_tree_hash([]),
        candidate_ref=dict(preview.candidate_ref),
        readiness_ref=dict(preview.readiness_ref),
        files=[],
        renderer_blob_ref=renderer.pinned_ref.record_ref,
        renderer_blob_hash=renderer.pinned_ref.content_hash,
        renderer_blob_revision=renderer.pinned_ref.revision,
        generator_version=preview.generator_version,
    )
    RecordRepository(ws, actor=_actor()).write("skill_package_artifacts", forged)

    with pytest.raises(ValueError):
        record_skill_proposal(ws, preview, actor=_actor())


def test_preview_rejects_existing_same_version_with_different_package_hash(tmp_path):
    from brain.v5.artifact_blobs import capture_artifact_content
    from brain.v5.models import SkillPackageArtifactRecord
    from brain.v5.project_skill_packages import build_skill_package_preview, package_artifact_id
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_package_artifacts import package_tree_hash

    ws, _candidate_ref, readiness_ref, _candidate = _ready_candidate(tmp_path)
    preview = build_skill_package_preview(ws, readiness_ref)
    renderer = capture_artifact_content(ws, b"older renderer", actor=_actor())
    existing = SkillPackageArtifactRecord(
        artifact_id=package_artifact_id(preview.skill_id, preview.semantic_version),
        skill_id=preview.skill_id,
        semantic_version=preview.semantic_version,
        package_hash="0" * 64,
        tree_hash=package_tree_hash([]),
        candidate_ref=dict(preview.candidate_ref),
        readiness_ref=dict(preview.readiness_ref),
        files=[],
        renderer_blob_ref=renderer.pinned_ref.record_ref,
        renderer_blob_hash=renderer.pinned_ref.content_hash,
        renderer_blob_revision=renderer.pinned_ref.revision,
        generator_version=preview.generator_version,
    )
    RecordRepository(ws, actor=_actor()).write("skill_package_artifacts", existing)

    with pytest.raises(ValueError, match="same Skill id and version"):
        build_skill_package_preview(ws, readiness_ref)


@pytest.mark.parametrize(
    "malicious_path",
    ["../escape.py", "/absolute.py", "C:/drive.py", "tests/../escape.py", "tests\\escape.py"],
)
def test_package_preview_rejects_noncanonical_or_escaping_paths(tmp_path, malicious_path):
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.project_skill_packages import build_skill_package_preview
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_distillation_records import (
        build_skill_distillation_candidate,
        record_skill_distillation_candidate,
    )
    from brain.v5.skill_readiness import assess_skill_readiness, record_skill_readiness_report
    from tests.test_v5_skill_distillation_records import _request

    ws, request = _request(tmp_path)
    request = replace(
        request,
        package_requirements=("SKILL.md", "manifest.json", malicious_path),
    )
    candidate_report = build_skill_distillation_candidate(ws, request)
    candidate_write = record_skill_distillation_candidate(ws, candidate_report, actor=_actor())
    candidate_ref = PinnedRecordRef(
        candidate_write.record_ref,
        candidate_write.content_hash,
        candidate_write.revision,
    )
    readiness = assess_skill_readiness(ws, candidate_ref)
    readiness = replace(
        readiness,
        status="ready",
        blockers=[],
        required_actions=[],
        validation_fixture_refs=[malicious_path],
        ready_for_package_preview=True,
    )
    readiness_write = RecordRepository(ws, actor=_actor()).write(
        "skill_readiness_reports",
        readiness,
    )
    readiness_ref = PinnedRecordRef(
        readiness_write.record_ref,
        readiness_write.content_hash,
        readiness_write.revision,
    )

    with pytest.raises(ValueError, match="package path"):
        build_skill_package_preview(ws, readiness_ref, revalidate_readiness=False)


def _tree_hash(rows):
    projection = [
        {
            "path": row["path"],
            "mode": row["mode"],
            "length": row["length"],
            "sha256": row["sha256"],
            "blob_receipt_content_hash": row["blob_receipt_content_hash"],
        }
        for row in sorted(rows, key=lambda item: item["path"].encode("utf-8"))
    ]
    encoded = json.dumps(
        projection,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
