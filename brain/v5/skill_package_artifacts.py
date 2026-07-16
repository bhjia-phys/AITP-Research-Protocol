"""Persist and reconstruct exact Skill package byte trees."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any

from brain.v5.artifact_blobs import capture_artifact_content, resolve_artifact_bytes
from brain.v5.models import SkillPackageArtifactRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
from brain.v5.project_skill_contracts import (
    canonical_package_path,
    require_valid_skill_package_artifact,
)
from brain.v5.project_skill_packages import (
    _write_preview,
    build_skill_package_preview,
    package_artifact_id,
    package_manifest_hash,
    package_preview_dir,
)
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WriteResult
from brain.v5.skill_models import SkillPackagePreview


def record_skill_package_artifact(
    ws: WorkspacePaths,
    preview: SkillPackagePreview,
    *,
    actor: RecordActor,
) -> WriteResult:
    expected = build_skill_package_preview(
        ws,
        preview.readiness_ref,
        semantic_version=preview.semantic_version,
    )
    if expected.files != preview.files or expected.package_hash != preview.package_hash:
        raise ValueError("Skill package artifact preview does not match current readiness")
    rows = []
    for path, content in sorted(preview.files.items(), key=lambda item: item[0].encode("utf-8")):
        canonical_package_path(path)
        capture = capture_artifact_content(ws, content, actor=actor)
        rows.append(
            {
                "path": path,
                "mode": "0644",
                "length": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "blob_receipt_ref": capture.pinned_ref.record_ref,
                "blob_receipt_content_hash": capture.pinned_ref.content_hash,
                "blob_receipt_revision": capture.pinned_ref.revision,
            }
        )
    renderer = capture_artifact_content(
        ws,
        Path(__file__).with_name("project_skill_packages.py").read_bytes(),
        actor=actor,
    )
    artifact = SkillPackageArtifactRecord(
        artifact_id=package_artifact_id(preview.skill_id, preview.semantic_version),
        skill_id=preview.skill_id,
        semantic_version=preview.semantic_version,
        package_hash=preview.package_hash,
        tree_hash=package_tree_hash(rows),
        candidate_ref=dict(preview.candidate_ref),
        readiness_ref=dict(preview.readiness_ref),
        files=rows,
        renderer_blob_ref=renderer.pinned_ref.record_ref,
        renderer_blob_hash=renderer.pinned_ref.content_hash,
        renderer_blob_revision=renderer.pinned_ref.revision,
        generator_version=preview.generator_version,
    )
    require_artifact_matches_preview(ws, artifact, preview)
    return RecordRepository(ws, actor=actor).write(
        "skill_package_artifacts",
        artifact,
        body="# Skill Package Artifact\n\nImmutable package file tree and local blob receipts.\n",
    )


def rebuild_skill_package_preview(
    ws: WorkspacePaths,
    record_ref: str,
    content_hash: str,
    revision: int,
) -> SkillPackagePreview:
    pin = PinnedRecordRef(record_ref, content_hash, revision)
    artifact = get_record_version(ws, pin).record
    if not isinstance(artifact, SkillPackageArtifactRecord):
        raise ValueError("artifact ref must pin a Skill package artifact")
    files, manifest = _resolve_validated_artifact(ws, artifact)
    root = package_preview_dir(ws, artifact.skill_id, artifact.semantic_version)
    _write_preview(root, files)
    namespace, name = artifact.skill_id.split("/", 1)
    return SkillPackagePreview(
        skill_id=artifact.skill_id,
        namespace=namespace,
        name=name,
        semantic_version=artifact.semantic_version,
        package_hash=artifact.package_hash,
        candidate_ref=dict(artifact.candidate_ref),
        readiness_ref=dict(artifact.readiness_ref),
        files=files,
        manifest=manifest,
        preview_dir=str(root),
        generator_version=artifact.generator_version,
    )


def resolve_skill_package_artifact(
    ws: WorkspacePaths,
    artifact_ref: PinnedRecordRef | dict[str, Any],
) -> tuple[SkillPackageArtifactRecord, dict[str, bytes], dict[str, Any]]:
    """Resolve and fully verify one immutable package artifact and its bytes."""

    pin = artifact_ref if isinstance(artifact_ref, PinnedRecordRef) else PinnedRecordRef(
        str(artifact_ref.get("record_ref") or ""),
        str(artifact_ref.get("content_hash") or ""),
        artifact_ref.get("revision"),
    )
    artifact = get_record_version(ws, pin).record
    if not isinstance(artifact, SkillPackageArtifactRecord):
        raise ValueError("artifact ref must pin a Skill package artifact")
    files, manifest = _resolve_validated_artifact(ws, artifact)
    return artifact, files, manifest


def package_tree_hash(rows: list[dict[str, Any]]) -> str:
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


def require_artifact_matches_preview(
    ws: WorkspacePaths,
    artifact: SkillPackageArtifactRecord,
    preview: SkillPackagePreview,
) -> SkillPackageArtifactRecord:
    files, _manifest = _resolve_validated_artifact(ws, artifact)
    expected_identity = (
        preview.skill_id,
        preview.semantic_version,
        preview.package_hash,
        preview.candidate_ref,
        preview.readiness_ref,
        preview.generator_version,
    )
    actual_identity = (
        artifact.skill_id,
        artifact.semantic_version,
        artifact.package_hash,
        artifact.candidate_ref,
        artifact.readiness_ref,
        artifact.generator_version,
    )
    if actual_identity != expected_identity:
        raise ValueError("Skill package artifact identity does not match preview")
    if set(files) != set(preview.files):
        raise ValueError("Skill package artifact file tree does not match preview")
    for path, content in preview.files.items():
        if files[path] != content:
            raise ValueError("Skill package artifact bytes do not match preview")
    return artifact


def _resolve_validated_artifact(
    ws: WorkspacePaths,
    artifact: SkillPackageArtifactRecord,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    require_valid_skill_package_artifact(artifact)
    if artifact.artifact_id != package_artifact_id(artifact.skill_id, artifact.semantic_version):
        raise ValueError("Skill package artifact identity is invalid")
    if package_tree_hash(artifact.files) != artifact.tree_hash:
        raise ValueError("Skill package artifact tree hash is invalid")
    files: dict[str, bytes] = {}
    for row in artifact.files:
        if row["mode"] != "0644":
            raise ValueError("generated Skill package files must use mode 0644")
        receipt = PinnedRecordRef(
            row["blob_receipt_ref"],
            row["blob_receipt_content_hash"],
            row["blob_receipt_revision"],
        )
        content = resolve_artifact_bytes(ws, receipt)
        if len(content) != row["length"] or hashlib.sha256(content).hexdigest() != row["sha256"]:
            raise ValueError("Skill package file does not match its artifact row")
        files[row["path"]] = content
    try:
        manifest = json.loads(files["manifest.json"].decode("utf-8"))
    except (KeyError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Skill package artifact manifest is invalid") from exc
    if not isinstance(manifest, dict):
        raise ValueError("Skill package artifact manifest must be an object")
    namespace, name = artifact.skill_id.split("/", 1)
    expected_identity = {
        "skill_id": artifact.skill_id,
        "namespace": namespace,
        "name": name,
        "semantic_version": artifact.semantic_version,
        "package_hash": artifact.package_hash,
        "candidate_ref": artifact.candidate_ref,
        "readiness_ref": artifact.readiness_ref,
    }
    if any(manifest.get(key) != value for key, value in expected_identity.items()):
        raise ValueError("Skill package manifest and artifact identity do not match")
    if package_manifest_hash(manifest) != artifact.package_hash:
        raise ValueError("Skill package manifest package hash is invalid")
    artifact_identity = manifest.get("artifact_identity")
    expected_ref = f"skill_package_artifact:{artifact.artifact_id}"
    if not isinstance(artifact_identity, dict) or artifact_identity.get("package_artifact_ref") != expected_ref:
        raise ValueError("Skill package manifest artifact identity is invalid")
    included_files = [
        {key: row[key] for key in ("path", "mode", "length", "sha256")}
        for row in artifact.files
        if row["path"] != "manifest.json"
    ]
    if manifest.get("included_files") != included_files:
        raise ValueError("Skill package manifest file projection is invalid")
    renderer = manifest.get("renderer")
    if not isinstance(renderer, dict) or renderer.get("generator_version") != artifact.generator_version:
        raise ValueError("Skill package manifest renderer identity is invalid")
    return files, manifest


__all__ = [
    "package_tree_hash",
    "rebuild_skill_package_preview",
    "record_skill_package_artifact",
    "resolve_skill_package_artifact",
    "require_artifact_matches_preview",
]
