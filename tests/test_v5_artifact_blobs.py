from __future__ import annotations

from pathlib import Path

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="artifact-blob-test", host="pytest")


def test_local_artifact_bytes_are_content_addressed_idempotent_and_path_independent(
    tmp_path,
):
    from brain.v5.artifact_blobs import capture_artifact_bytes, resolve_artifact_bytes
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "workspace")
    first_source = tmp_path / "first" / "result.bin"
    first_source.parent.mkdir(parents=True)
    first_source.write_bytes(b"AITP reproducible bytes\x00\x01")
    second_source = tmp_path / "elsewhere" / "renamed.bin"
    second_source.parent.mkdir(parents=True)
    second_source.write_bytes(first_source.read_bytes())

    first = capture_artifact_bytes(ws, first_source, actor=_actor())
    first_source.unlink()
    replay = capture_artifact_bytes(ws, second_source, actor=_actor())

    assert replay.pinned_ref == first.pinned_ref
    assert replay.record == first.record
    assert replay.write_status == "unchanged"
    assert Path(first.blob_path).read_bytes() == b"AITP reproducible bytes\x00\x01"
    assert resolve_artifact_bytes(ws, first.pinned_ref) == b"AITP reproducible bytes\x00\x01"
    assert first.record.receipt_id == "artifact-blob-sha256-" + first.record.byte_sha256
    assert first.record.byte_length == len(b"AITP reproducible bytes\x00\x01")
    assert first.record.blob_key.startswith("blobs/sha256/")

    canonical = ws.registry_dir("artifact_blob_receipts") / f"{first.record.receipt_id}.md"
    text = canonical.read_text(encoding="utf-8")
    assert str(second_source) not in text
    assert str(first_source) not in text
    assert "captured_at" not in text


def test_in_memory_artifact_bytes_use_the_same_content_addressed_receipt(tmp_path):
    from brain.v5.artifact_blobs import (
        capture_artifact_content,
        resolve_artifact_bytes,
    )
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    capture = capture_artifact_content(
        ws,
        b"git index bytes\x00\xff",
        actor=_actor(),
    )

    assert resolve_artifact_bytes(ws, capture.pinned_ref) == b"git index bytes\x00\xff"
    assert capture.record.byte_length == len(b"git index bytes\x00\xff")


@pytest.mark.parametrize("failure", ["missing", "corrupt"])
def test_local_artifact_resolution_fails_closed_on_missing_or_corrupt_bytes(
    tmp_path,
    failure,
):
    from brain.v5.artifact_blobs import (
        ArtifactBlobIntegrityError,
        capture_artifact_bytes,
        resolve_artifact_bytes,
    )
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "workspace")
    source = tmp_path / "result.dat"
    source.write_bytes(b"validated bytes")
    capture = capture_artifact_bytes(ws, source, actor=_actor())
    blob_path = Path(capture.blob_path)
    if failure == "missing":
        blob_path.unlink()
    else:
        blob_path.write_bytes(b"corrupt bytes")

    with pytest.raises(ArtifactBlobIntegrityError, match=failure):
        resolve_artifact_bytes(ws, capture.pinned_ref)


def test_external_receipt_requires_immutable_identity_and_verified_availability(tmp_path):
    from brain.v5.artifact_blobs import record_external_artifact_receipt
    from brain.v5.models import ValidationResultRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    object_key = "s3://bucket/results/qsgw.json?versionId=version-42"
    validation_write = RecordRepository(ws, actor=_actor()).write(
        "validation_results",
        ValidationResultRecord(
            result_id="validation-external-object-version-42",
            topic_id="librpa",
            claim_id="claim-librpa",
            contract_id="external-object-availability-v1",
            tool_run_id="run-external-object-check",
            status="passed",
            executor_id="s3-head-object-verifier",
            executor_version="1.0.0",
            executor_hash="b" * 64,
            checked_artifact_hashes={object_key: "a" * 64},
        ),
    )
    verification_ref = pin_current_record(ws, validation_write.record_ref)
    receipt = record_external_artifact_receipt(
        ws,
        provider="s3",
        object_id="bucket/results/qsgw.json",
        object_version="version-42",
        byte_sha256="a" * 64,
        byte_length=2048,
        retention_policy="object-lock-governance-2030-01-01",
        access_policy="project-readonly",
        availability_verification_ref=verification_ref,
        actor=_actor(),
    )
    replay = record_external_artifact_receipt(
        ws,
        provider="s3",
        object_id="bucket/results/qsgw.json",
        object_version="version-42",
        byte_sha256="a" * 64,
        byte_length=2048,
        retention_policy="object-lock-governance-2030-01-01",
        access_policy="project-readonly",
        availability_verification_ref=verification_ref,
        actor=_actor(),
    )

    assert replay.pinned_ref == receipt.pinned_ref
    assert receipt.record.storage_kind == "external_immutable"
    assert receipt.record.availability_verified is True

    with pytest.raises(ValueError, match="object_version"):
        record_external_artifact_receipt(
            ws,
            provider="s3",
            object_id="bucket/results/qsgw.json",
            object_version="",
            byte_sha256="a" * 64,
            byte_length=2048,
            retention_policy="object-lock-governance-2030-01-01",
            access_policy="project-readonly",
            availability_verification_ref=verification_ref,
            actor=_actor(),
        )
    with pytest.raises(ValueError, match="verification"):
        record_external_artifact_receipt(
            ws,
            provider="s3",
            object_id="bucket/results/qsgw.json",
            object_version="version-42",
            byte_sha256="a" * 64,
            byte_length=2048,
            retention_policy="object-lock-governance-2030-01-01",
            access_policy="project-readonly",
            availability_verification_ref={
                "record_ref": verification_ref.record_ref,
                "content_hash": "f" * 64,
                "revision": verification_ref.revision,
            },
            actor=_actor(),
        )
