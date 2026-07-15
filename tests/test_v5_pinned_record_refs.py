from __future__ import annotations

from dataclasses import asdict

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="pinned-ref-test", host="pytest")


def test_hash_qualified_read_resolves_current_and_archived_revisions(tmp_path):
    from brain.v5.models import ArtifactRecord
    from brain.v5.pinned_record_refs import (
        PinnedRecordMismatchError,
        get_record_version,
        pin_current_record,
    )
    from brain.v5.record_repository import RecordRepository, WritePolicy
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    repository = RecordRepository(ws, actor=_actor())
    first = ArtifactRecord(
        artifact_id="artifact-versioned",
        topic_id="topic",
        claim_id="claim",
        artifact_type="result",
        uri="file:///result.dat",
        summary="first revision",
    )
    first_write = repository.write("artifacts", first, body="# First\n")
    first_pin = pin_current_record(ws, first_write.record_ref)

    second = ArtifactRecord(
        artifact_id=first.artifact_id,
        topic_id=first.topic_id,
        claim_id=first.claim_id,
        artifact_type=first.artifact_type,
        uri=first.uri,
        summary="second revision",
    )
    second_write = repository.write(
        "artifacts",
        second,
        body="# Second\n",
        policy=WritePolicy(mode="revision", expected_hash=first_pin.content_hash),
    )
    second_pin = pin_current_record(ws, second_write.record_ref)

    archived = get_record_version(ws, first_pin)
    current = get_record_version(ws, second_pin)

    assert archived.version_source == "archive"
    assert archived.pinned_ref == first_pin
    assert archived.record.summary == "first revision"
    assert current.version_source == "current"
    assert current.pinned_ref == second_pin
    assert current.record.summary == "second revision"
    assert first_pin.revision == 1
    assert second_pin.revision == 2

    with pytest.raises(PinnedRecordMismatchError, match="content hash"):
        get_record_version(
            ws,
            {
                "record_ref": second_pin.record_ref,
                "content_hash": "f" * 64,
                "revision": second_pin.revision,
            },
        )
    with pytest.raises(PinnedRecordMismatchError, match="revision"):
        get_record_version(
            ws,
            {
                "record_ref": second_pin.record_ref,
                "content_hash": second_pin.content_hash,
                "revision": 99,
            },
        )


def test_archived_exact_pin_survives_later_malformed_current_record(tmp_path):
    from dataclasses import replace
    from pathlib import Path

    from brain.v5.models import ArtifactRecord
    from brain.v5.pinned_record_refs import (
        get_record_version,
        pin_current_record,
        pin_record_hash,
    )
    from brain.v5.record_repository import RecordRepository, WritePolicy
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    repository = RecordRepository(ws, actor=_actor())
    first = ArtifactRecord(
        artifact_id="artifact-archive-survives",
        topic_id="topic",
        claim_id="claim",
        artifact_type="result",
        uri="file:///result.dat",
        summary="frozen revision",
    )
    first_write = repository.write("artifacts", first, body="# Frozen\n")
    first_pin = pin_current_record(ws, first_write.record_ref)
    second_write = repository.write(
        "artifacts",
        replace(first, summary="later current revision"),
        body="# Current\n",
        policy=WritePolicy(mode="revision", expected_hash=first_pin.content_hash),
    )
    Path(second_write.path).write_text(
        "---\nrecord_content_hash: broken\n---\n",
        encoding="utf-8",
    )

    recovered = get_record_version(ws, first_pin)
    recovered_without_revision = pin_record_hash(
        ws,
        first_pin.record_ref,
        first_pin.content_hash,
    )

    assert recovered.version_source == "archive"
    assert recovered.record.summary == "frozen revision"
    assert recovered_without_revision == first_pin


def test_frozen_dependency_manifest_is_recursive_deterministic_and_cycle_safe(tmp_path):
    from brain.v5.models import (
        ArtifactBlobReceiptRecord,
        ArtifactRecord,
        ToolRecipeRecord,
        ToolRunRecord,
    )
    from brain.v5.pinned_record_refs import (
        build_frozen_dependency_manifest,
        pin_current_record,
    )
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    repository = RecordRepository(ws, actor=_actor())
    blob = ArtifactBlobReceiptRecord(
        receipt_id="artifact-blob-sha256-" + "a" * 64,
        storage_kind="local_sha256",
        hash_algorithm="sha256",
        byte_sha256="a" * 64,
        byte_length=4,
        blob_key="blobs/sha256/aa/" + "a" * 64,
    )
    blob_write = repository.write("artifact_blob_receipts", blob)
    recipe = ToolRecipeRecord(
        recipe_id="recipe-frozen",
        tool_family="python",
        tool_name="check.py",
        purpose="Check frozen closure",
    )
    recipe_write = repository.write("tool_recipes", recipe)
    artifact = ArtifactRecord(
        artifact_id="artifact-frozen",
        topic_id="topic",
        claim_id="claim",
        artifact_type="result",
        uri="aitp-blob://" + "a" * 64,
        summary="Frozen bytes",
        content_hash="a" * 64,
        hash_algorithm="sha256",
        storage_mode="local_sha256",
        artifact_blob_receipt_ref=blob_write.record_ref,
        artifact_blob_receipt_hash=blob_write.content_hash,
        provenance_refs=["tool_run:run-frozen"],
    )
    artifact_write = repository.write("artifacts", artifact)
    run = ToolRunRecord(
        run_id="run-frozen",
        recipe_id=recipe.recipe_id,
        tool_family="python",
        tool_name="check.py",
        topic_id="topic",
        claim_id="claim",
        recipe_ref=recipe_write.record_ref,
        artifact_refs=[artifact_write.record_ref],
        recorded_maturity="reproducible_candidate",
    )
    run_write = repository.write("tool_runs", run)
    root = pin_current_record(ws, run_write.record_ref)

    first = build_frozen_dependency_manifest(ws, [root])
    second = build_frozen_dependency_manifest(ws, [root])

    assert first == second
    assert first.closure_hash
    assert [asdict(item) for item in first.roots] == [asdict(root)]
    assert {item.record_ref for item in first.nodes} == {
        blob_write.record_ref,
        artifact_write.record_ref,
        recipe_write.record_ref,
        run_write.record_ref,
    }
    assert {
        (edge.owner_ref, edge.field_name, edge.target_ref)
        for edge in first.edges
    } == {
        (run_write.record_ref, "artifact_refs", artifact_write.record_ref),
        (run_write.record_ref, "recipe_ref", recipe_write.record_ref),
        (artifact_write.record_ref, "artifact_blob_receipt_ref", blob_write.record_ref),
        (artifact_write.record_ref, "provenance_refs", run_write.record_ref),
    }


def test_dependency_fields_are_owned_by_the_family_registry():
    from brain.v5.record_family_registry import record_family_specs

    specs = record_family_specs()

    assert specs["tool_runs"].dependency_fields == (
        "artifact_refs",
        "code_state_ref",
        "environment_ref",
        "input_manifest[].artifact_ref",
        "monitor_snapshot_refs",
        "output_manifest[].artifact_ref",
        "recipe_ref",
        "skill_usage_refs",
        "validation_result_refs",
    )
    assert specs["artifacts"].dependency_fields == (
        "artifact_blob_receipt_ref",
        "provenance_refs",
    )
    assert specs["code_patch_manifests"].dependency_fields == (
        "entries[].blob_receipt_ref",
        "entries[].index_blob_receipt_ref",
        "source_refs[].record_ref",
    )
    assert specs["tool_recipes"].dependency_fields == (
        "script_refs",
        "validation_contract_refs",
    )
