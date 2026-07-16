"""Render host-neutral, content-addressed Skill previews and proposals."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.markdown import write_text_atomic
from brain.v5.models import (
    SkillDistillationCandidateRecord,
    SkillPackageArtifactRecord,
    SkillProposalRecord,
    SkillReadinessReportRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.project_skill_contracts import (
    canonical_package_path,
    require_valid_skill_package_preview,
    require_valid_skill_proposal,
)
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WriteResult
from brain.v5.skill_models import SkillPackagePreview
from brain.v5.skill_readiness import assess_skill_readiness


GENERATOR_VERSION = "aitp-v5-skill-package-v1"


def build_skill_package_preview(
    ws: WorkspacePaths,
    readiness_ref: PinnedRecordRef | dict,
    *,
    semantic_version: str = "0.1.0",
    revalidate_readiness: bool = True,
) -> SkillPackagePreview:
    readiness_pin = _coerce_pin(readiness_ref)
    readiness_version = get_record_version(ws, readiness_pin)
    readiness = readiness_version.record
    if not isinstance(readiness, SkillReadinessReportRecord):
        raise ValueError("readiness_ref must pin a Skill readiness report")
    if readiness.status != "ready" or not readiness.ready_for_package_preview:
        raise ValueError("Skill package preview requires a ready report")
    if revalidate_readiness:
        current = assess_skill_readiness(
            ws,
            readiness.candidate_ref,
            expert_exception_ref=readiness.expert_exception_ref or None,
        )
        if asdict(current) != asdict(readiness):
            raise ValueError("Skill readiness report no longer matches current state")
    candidate_pin = _coerce_pin(readiness.candidate_ref)
    candidate = get_record_version(ws, candidate_pin).record
    if not isinstance(candidate, SkillDistillationCandidateRecord):
        raise ValueError("readiness candidate ref is not a Skill distillation candidate")
    name = _slug(candidate.title)
    _require_semver(semantic_version)
    skill_id = f"aitp-generated/{name}"
    requirements = [canonical_package_path(value) for value in candidate.package_requirements]
    if "SKILL.md" not in requirements or "manifest.json" not in requirements:
        raise ValueError("package requirements must include SKILL.md and manifest.json")
    fixture_paths = [value for value in requirements if value not in {"SKILL.md", "manifest.json"}]
    if any(not value.startswith(("tests/", "fixtures/")) for value in fixture_paths):
        raise ValueError("package requirement has no deterministic renderer")

    rendered = {"SKILL.md": _render_skill(candidate).encode("utf-8")}
    for path in fixture_paths:
        rendered[path] = _render_fixture(candidate, path)
    file_rows = [
        {
            "path": path,
            "mode": "0644",
            "length": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        for path, content in sorted(rendered.items())
    ]
    artifact_ref = f"skill_package_artifact:{package_artifact_id(skill_id, semantic_version)}"
    manifest = {
        "schema_version": "v1",
        "catalog_state": "preview",
        "skill_id": skill_id,
        "namespace": "aitp-generated",
        "name": name,
        "semantic_version": semantic_version,
        "candidate_ref": asdict(candidate_pin),
        "readiness_ref": asdict(readiness_pin),
        "source_topic_ids": list(candidate.source_topic_ids),
        "recipe_refs": list(candidate.recipe_refs),
        "source_program_refs": list(candidate.source_program_refs),
        "execution_refs": list(candidate.execution_refs),
        "validation_refs": list(candidate.validation_refs),
        "artifact_refs": list(candidate.artifact_refs),
        "code_state_refs": list(candidate.code_state_refs),
        "environment_refs": list(candidate.environment_refs),
        "source_refs": list(candidate.source_refs),
        "failure_basis": {
            "candidate_ref": asdict(candidate_pin),
            "known_failures": list(candidate.known_failures),
            "none_known_boundary": candidate.failure_boundary,
        },
        "applicability_selectors": dict(candidate.applicability_selectors),
        "transfer_boundary": candidate.transfer_boundary,
        "entrypoint": "SKILL.md",
        "included_files": file_rows,
        "validation_commands": _validation_commands(fixture_paths),
        "external_dependencies": [],
        "license_access_notes": [
            "Project-local generated procedural memory.",
            "Source and software access remain governed by the pinned AITP records.",
        ],
        "renderer": {
            "renderer_id": "aitp-v5-project-skill-renderer",
            "generator_version": GENERATOR_VERSION,
            "source_sha256": _renderer_source_hash(),
        },
        "artifact_identity": {
            "package_artifact_ref": artifact_ref,
            "tree_hash_owner": "canonical_skill_package_artifact_record",
        },
        "generated_at": readiness.created_at,
        "can_install_skill": False,
        "can_update_claim_trust": False,
        "can_write_evidence": False,
    }
    package_hash = package_manifest_hash(manifest)
    manifest["package_hash"] = package_hash
    rendered["manifest.json"] = (
        json.dumps(manifest, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    _reject_conflicting_package_version(ws, artifact_ref, package_hash)
    preview_dir = package_preview_dir(ws, skill_id, semantic_version)
    _write_preview(preview_dir, rendered)
    preview = SkillPackagePreview(
        skill_id=skill_id,
        namespace="aitp-generated",
        name=name,
        semantic_version=semantic_version,
        package_hash=package_hash,
        candidate_ref=asdict(candidate_pin),
        readiness_ref=asdict(readiness_pin),
        files=dict(rendered),
        manifest=manifest,
        preview_dir=str(preview_dir),
        generator_version=GENERATOR_VERSION,
    )
    require_valid_skill_package_preview(preview.contract_payload())
    return preview


def record_skill_proposal(
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
        raise ValueError("Skill proposal preview does not match current readiness")
    artifact_ref = f"skill_package_artifact:{package_artifact_id(preview.skill_id, preview.semantic_version)}"
    artifact_pin = pin_current_record(ws, artifact_ref)
    artifact = get_record_version(ws, artifact_pin).record
    if not isinstance(artifact, SkillPackageArtifactRecord):
        raise ValueError("Skill proposal requires a package artifact")
    from brain.v5.skill_package_artifacts import require_artifact_matches_preview

    require_artifact_matches_preview(ws, artifact, preview)
    candidate = get_record_version(ws, preview.candidate_ref).record
    if not isinstance(candidate, SkillDistillationCandidateRecord):
        raise ValueError("Skill proposal candidate pin is invalid")
    proposal = SkillProposalRecord(
        proposal_id=package_proposal_id(preview.skill_id, preview.semantic_version),
        skill_id=preview.skill_id,
        namespace=preview.namespace,
        name=preview.name,
        semantic_version=preview.semantic_version,
        package_hash=preview.package_hash,
        tree_hash=artifact.tree_hash,
        candidate_ref=dict(preview.candidate_ref),
        readiness_ref=dict(preview.readiness_ref),
        package_artifact_ref=asdict(artifact_pin),
        source_topic_ids=list(candidate.source_topic_ids),
        recipe_refs=list(candidate.recipe_refs),
        source_program_refs=list(candidate.source_program_refs),
        execution_refs=list(candidate.execution_refs),
        validation_refs=list(candidate.validation_refs),
        artifact_refs=list(candidate.artifact_refs),
        code_state_refs=list(candidate.code_state_refs),
        environment_refs=list(candidate.environment_refs),
        source_refs=list(candidate.source_refs),
        failure_basis=dict(preview.manifest["failure_basis"]),
        applicability_selectors=dict(candidate.applicability_selectors),
        manifest=dict(preview.manifest),
        file_hashes=[
            {key: row[key] for key in ("path", "mode", "length", "sha256")}
            for row in artifact.files
        ],
        validation_commands=list(preview.manifest["validation_commands"]),
    )
    require_valid_skill_proposal(proposal)
    return RecordRepository(ws, actor=actor).write(
        "skill_proposals",
        proposal,
        body=(
            f"# Skill Proposal: {proposal.skill_id} {proposal.semantic_version}\n\n"
            "Review is required before any project-local installation.\n"
        ),
    )


def package_artifact_id(skill_id: str, semantic_version: str) -> str:
    return prefixed_id("skill-package-artifact", f"{skill_id}:{semantic_version}", max_slug=72)


def package_proposal_id(skill_id: str, semantic_version: str) -> str:
    return prefixed_id("skill-proposal", f"{skill_id}:{semantic_version}", max_slug=72)


def package_preview_dir(ws: WorkspacePaths, skill_id: str, semantic_version: str) -> Path:
    namespace, name = skill_id.split("/", 1)
    return ws.root / "tools" / "skills" / "catalog" / namespace / name / semantic_version / "preview"


def _render_skill(candidate: SkillDistillationCandidateRecord) -> str:
    procedure = "\n".join(
        f"{index}. {step['action']}" for index, step in enumerate(candidate.ordered_steps, start=1)
    )
    parameters = "\n".join(
        f"- `{name}`: {json.dumps(spec, ensure_ascii=True, sort_keys=True)}"
        for name, spec in sorted(candidate.parameter_contract.items())
    )
    failures = "\n".join(
        f"- {item['failure']}: detect with {item['detection']}; recover via "
        + "; ".join(item["recovery"])
        for item in candidate.known_failures
    ) or f"- None known: {candidate.failure_boundary}"
    expansion_refs = [
        *(item["record_ref"] for item in candidate.recipe_refs),
        *(item["record_ref"] for item in candidate.execution_refs),
        *(item["record_ref"] for item in candidate.validation_refs),
        *(item["record_ref"] for item in candidate.artifact_refs),
        *(item["record_ref"] for item in candidate.code_state_refs),
        *(item["record_ref"] for item in candidate.environment_refs),
        *(item["record_ref"] for item in candidate.source_program_refs),
        *(item["record_ref"] for item in candidate.source_refs),
    ]
    return (
        "---\n"
        f"name: {_slug(candidate.title)}\n"
        f"description: Use for {candidate.workflow_kind} only within the declared selectors.\n"
        "---\n\n"
        f"# {candidate.title}\n\n"
        "## When To Use\n\n"
        f"Use only for `{candidate.workflow_kind}` within the declared selectors.\n\n"
        "## Applicability\n\n"
        f"- Selectors: `{json.dumps(candidate.applicability_selectors, ensure_ascii=True, sort_keys=True)}`\n"
        f"- Transfer boundary: {candidate.transfer_boundary}\n\n"
        "## Non-Applicability\n\n"
        f"- Stop outside this transfer boundary: {candidate.transfer_boundary}\n\n"
        "## Prerequisites\n\n" + _bullets(candidate.prerequisites) + "\n\n"
        "## Procedure\n\n" + procedure + "\n\n"
        "## Parameters\n\n" + parameters + "\n\n"
        "## Stop Rules\n\n" + _bullets(candidate.stop_rules) + "\n\n"
        "## Failure Recovery\n\n" + failures + "\n\n"
        "## Validation\n\n" + _bullets(item["record_ref"] for item in candidate.validation_refs) + "\n\n"
        "## AITP Expansion Refs\n\n" + _bullets(expansion_refs) + "\n\n"
        "This Skill is procedural memory and cannot update scientific claim trust.\n"
    )


def _render_fixture(candidate: SkillDistillationCandidateRecord, path: str) -> bytes:
    payload = {
        "schema_version": "v1",
        "fixture_path": path,
        "validator_id": "aitp-pinned-validation-replay",
        "execution_refs": candidate.execution_refs,
        "validation_refs": candidate.validation_refs,
        "expected_status": "passed",
        "network": "forbidden",
        "writes": [],
        "can_update_claim_trust": False,
    }
    return (json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _validation_commands(paths: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "kind": "aitp_builtin_declarative",
            "validator_id": "aitp-pinned-validation-replay",
            "fixture": path,
            "network": "forbidden",
            "writes": [],
            "timeout_seconds": 30,
        }
        for path in paths
    ]


def _write_preview(root: Path, files: dict[str, bytes]) -> None:
    if _link_like(root):
        raise ValueError("Skill package preview root cannot be a link or junction")
    if root.exists():
        if not root.is_dir():
            raise ValueError("Skill package preview root must be a directory")
        for path in root.rglob("*"):
            if _link_like(path):
                raise ValueError("Skill package preview cannot contain links or junctions")
        shutil.rmtree(root)
    for path, content in files.items():
        target = root.joinpath(*canonical_package_path(path).split("/"))
        write_text_atomic(target, content.decode("utf-8"))


def _renderer_source_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def package_manifest_hash(manifest: dict[str, Any]) -> str:
    projection = dict(manifest)
    projection.pop("package_hash", None)
    return _sha256_json(projection)


def _reject_conflicting_package_version(
    ws: WorkspacePaths,
    artifact_ref: str,
    package_hash: str,
) -> None:
    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="project-skill-package-preview",
            host="aitp-v5",
        ),
    )
    existing = repository.read(artifact_ref)
    if existing.status == "not_found":
        return
    if existing.status != "found" or not isinstance(existing.record, SkillPackageArtifactRecord):
        raise ValueError("existing Skill package artifact is unreadable")
    if existing.record.package_hash != package_hash:
        raise ValueError("same Skill id and version already bind a different package hash")


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _link_like(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", None)
    return path.is_symlink() or bool(is_junction and is_junction())


def _coerce_pin(value: PinnedRecordRef | dict) -> PinnedRecordRef:
    if isinstance(value, PinnedRecordRef):
        return value
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )


def _require_semver(value: str) -> None:
    if not re.fullmatch(
        r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)",
        value,
    ):
        raise ValueError("semantic_version must be canonical MAJOR.MINOR.PATCH")


def _slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not result:
        raise ValueError("Skill name is empty after normalization")
    return result[:80].rstrip("-")


def _bullets(values) -> str:
    return "\n".join(f"- {value}" for value in values) or "- None"


__all__ = [
    "GENERATOR_VERSION", "build_skill_package_preview", "package_artifact_id",
    "package_manifest_hash", "package_preview_dir", "record_skill_proposal",
]
