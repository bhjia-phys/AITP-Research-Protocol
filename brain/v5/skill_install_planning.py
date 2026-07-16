"""Pure package, target, version, and checkpoint planning for Skill deployment."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from brain.v5.models import SkillInstallPlanRecord, SkillProposalRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
from brain.v5.project_skill_contracts import require_valid_skill_install_plan
from brain.v5.project_skill_packages import package_manifest_hash
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.skill_package_artifacts import resolve_skill_package_artifact
from brain.v5.skill_install_plan_derivations import (
    checkpoint_action_for,
    diff_projection_for,
    plan_id_for,
    plan_identity_for,
    sha256_json,
    validation_policy_for,
)
from brain.v5.skill_validation_execution import (
    validate_staged_skill_package,
)


SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
EMPTY_TREE_HASH = hashlib.sha256(b"[]").hexdigest()
EFFECT_POLICY = "project_skill_deployment_only_no_claim_trust"
REPLAY_POLICY = "exact_idempotent"


def build_skill_install_plan(
    ws: WorkspacePaths,
    proposal_ref: PinnedRecordRef | Mapping[str, Any],
    target_root: str | Path,
    hosts: Sequence[str],
    *,
    actor: RecordActor,
) -> SkillInstallPlanRecord:
    proposal_pin, proposal, artifact_pin, artifact, files, manifest = proposal_package(
        ws, proposal_ref
    )
    root, target = target_paths(target_root, proposal.name)
    before_hash, existing_manifest = snapshot_target(target)
    operation = _install_operation(
        proposal, before_hash=before_hash, existing_manifest=existing_manifest
    )
    return _record_plan(
        ws,
        actor=actor,
        operation=operation,
        proposal_pin=proposal_pin,
        proposal=proposal,
        artifact_pin=artifact_pin,
        artifact=artifact,
        files=files,
        manifest=manifest,
        root=root,
        target=target,
        hosts=hosts,
        before_hash=before_hash,
        existing_manifest=existing_manifest,
    )


def build_skill_rollback_plan(
    ws: WorkspacePaths,
    proposal_ref: PinnedRecordRef | Mapping[str, Any],
    target_root: str | Path,
    hosts: Sequence[str],
    *,
    expected_current_package_hash: str,
    actor: RecordActor,
) -> SkillInstallPlanRecord:
    proposal_pin, proposal, artifact_pin, artifact, files, manifest = proposal_package(
        ws, proposal_ref
    )
    root, target = target_paths(target_root, proposal.name)
    before_hash, existing_manifest = snapshot_target(target)
    if not existing_manifest:
        raise ValueError("Skill rollback requires an existing managed AITP Skill")
    if existing_manifest.get("package_hash") != expected_current_package_hash:
        raise ValueError("Skill rollback current package hash does not match")
    if existing_manifest.get("skill_id") != proposal.skill_id:
        raise ValueError("Skill rollback cannot replace a different Skill id")
    current_version = semver(str(existing_manifest.get("semantic_version") or ""))
    if semver(proposal.semantic_version) >= current_version:
        raise ValueError("Skill rollback target version must be older than the current version")
    return _record_plan(
        ws,
        actor=actor,
        operation="rollback",
        proposal_pin=proposal_pin,
        proposal=proposal,
        artifact_pin=artifact_pin,
        artifact=artifact,
        files=files,
        manifest=manifest,
        root=root,
        target=target,
        hosts=hosts,
        before_hash=before_hash,
        existing_manifest=existing_manifest,
    )


def skill_install_checkpoint_request(
    ws: WorkspacePaths,
    plan_ref: PinnedRecordRef | Mapping[str, Any],
) -> dict[str, Any]:
    pin, plan = load_plan(ws, plan_ref)
    subjects = [coerce_pin(plan.proposal_ref), coerce_pin(plan.package_artifact_ref)]
    if plan.patch_proposal_ref:
        subjects.append(coerce_pin(plan.patch_proposal_ref))
    return {
        "action": plan.checkpoint_action,
        "action_payload": dict(plan.action_payload),
        "intent_ref": pin,
        "subject_refs": subjects,
        "target_scope_refs": target_scopes(plan, pin),
        "effect_policy": EFFECT_POLICY,
        "replay_policy": REPLAY_POLICY,
    }


def _record_plan(
    ws: WorkspacePaths,
    *,
    actor: RecordActor,
    operation: str,
    proposal_pin: PinnedRecordRef,
    proposal: SkillProposalRecord,
    artifact_pin: PinnedRecordRef,
    artifact: Any,
    files: Mapping[str, bytes],
    manifest: Mapping[str, Any],
    root: Path,
    target: Path,
    hosts: Sequence[str],
    before_hash: str,
    existing_manifest: Mapping[str, Any],
    patch_pin: PinnedRecordRef | None = None,
    old_package_hash: str = "",
    new_package_hash: str = "",
) -> SkillInstallPlanRecord:
    del manifest
    normalized_hosts = sorted({str(host).strip() for host in hosts if str(host).strip()})
    if not normalized_hosts:
        raise ValueError("Skill install plan hosts must not be empty")
    after_hash = files_tree_hash(files)
    policy, validation_policy = validation_policy_for(proposal.validation_commands)
    if not policy.requires_m2_execution:
        validate_staged_skill_package(files, proposal.validation_commands)
    validation_policy_hash = sha256_json(validation_policy)
    checkpoint_action = checkpoint_action_for(operation, is_patch=patch_pin is not None)
    existing_skill_id = str(existing_manifest.get("skill_id") or "")
    existing_semantic_version = str(existing_manifest.get("semantic_version") or "")
    existing_package_hash = str(existing_manifest.get("package_hash") or "")
    diff_projection = diff_projection_for(
        operation=operation,
        skill_id=proposal.skill_id,
        semantic_version=proposal.semantic_version,
        package_hash=proposal.package_hash,
        tree_hash=artifact.tree_hash,
        target_root=str(root),
        target_path=str(target),
        hosts=normalized_hosts,
        before_hash=before_hash,
        after_hash=after_hash,
        existing_skill_id=existing_skill_id,
        existing_semantic_version=existing_semantic_version,
        existing_package_hash=existing_package_hash,
        validation_policy_hash=validation_policy_hash,
        patch_proposal_ref=asdict(patch_pin) if patch_pin is not None else None,
        old_package_hash=old_package_hash,
        new_package_hash=new_package_hash,
    )
    identity = plan_identity_for(diff_projection, proposal_pin, artifact_pin)
    diff_hash = identity["diff_hash"]
    plan_id = plan_id_for(identity)
    action_payload = {
        "plan_id": plan_id,
        "operation": operation,
        "skill_id": proposal.skill_id,
        "semantic_version": proposal.semantic_version,
        "package_hash": proposal.package_hash,
        "tree_hash": artifact.tree_hash,
        "diff_hash": diff_hash,
        "target_root": str(root),
        "target_path": str(target),
        "hosts": normalized_hosts,
        "expected_before_hash": before_hash,
        "expected_after_hash": after_hash,
        "existing_skill_id": existing_skill_id,
        "existing_semantic_version": existing_semantic_version,
        "existing_package_hash": existing_package_hash,
        "validation_policy": validation_policy,
        "validation_policy_hash": validation_policy_hash,
    }
    if patch_pin is not None:
        action_payload.update(
            {
                "patch_proposal_ref": asdict(patch_pin),
                "old_package_hash": old_package_hash,
                "new_package_hash": new_package_hash,
            }
        )
    record = SkillInstallPlanRecord(
        plan_id=plan_id,
        operation=operation,
        checkpoint_action=checkpoint_action,
        skill_id=proposal.skill_id,
        name=proposal.name,
        semantic_version=proposal.semantic_version,
        package_hash=proposal.package_hash,
        tree_hash=artifact.tree_hash,
        proposal_ref=asdict(proposal_pin),
        package_artifact_ref=asdict(artifact_pin),
        target_root=str(root),
        target_path=str(target),
        hosts=normalized_hosts,
        expected_before_hash=before_hash,
        expected_after_hash=after_hash,
        diff_hash=diff_hash,
        existing_skill_id=existing_skill_id,
        existing_semantic_version=existing_semantic_version,
        existing_package_hash=existing_package_hash,
        validation_commands=[dict(command) for command in proposal.validation_commands],
        validation_policy=validation_policy,
        validation_policy_hash=validation_policy_hash,
        action_payload=action_payload,
        patch_proposal_ref=asdict(patch_pin) if patch_pin is not None else {},
        old_package_hash=old_package_hash,
        new_package_hash=new_package_hash,
    )
    require_valid_skill_install_plan(record)
    RecordRepository(ws, actor=actor).write(
        "skill_install_plans",
        record,
        body="# Skill Install Plan\n\nImmutable reviewed project-local deployment intent.\n",
    )
    return record


def proposal_package(ws: WorkspacePaths, proposal_ref):
    proposal_pin = coerce_pin(proposal_ref)
    proposal = get_record_version(ws, proposal_pin).record
    if not isinstance(proposal, SkillProposalRecord):
        raise ValueError("Skill install proposal ref must pin a SkillProposalRecord")
    artifact_pin = coerce_pin(proposal.package_artifact_ref)
    artifact, files, manifest = resolve_skill_package_artifact(ws, artifact_pin)
    expected = (proposal.skill_id, proposal.semantic_version, proposal.package_hash, proposal.tree_hash)
    actual = (artifact.skill_id, artifact.semantic_version, artifact.package_hash, artifact.tree_hash)
    if expected != actual:
        raise ValueError("Skill proposal and package artifact identity do not match")
    if proposal.file_hashes != [
        {key: row[key] for key in ("path", "mode", "length", "sha256")}
        for row in artifact.files
    ]:
        raise ValueError("Skill proposal file hashes do not match the package artifact")
    return proposal_pin, proposal, artifact_pin, artifact, files, manifest


def load_plan(ws: WorkspacePaths, value):
    pin = coerce_pin(value)
    record = get_record_version(ws, pin).record
    if not isinstance(record, SkillInstallPlanRecord):
        raise ValueError("plan_ref must pin a SkillInstallPlanRecord")
    if record.plan_id != pin.record_ref.partition(":")[2]:
        raise ValueError("Skill install plan identity is invalid")
    if record.action_payload != checkpoint_request_payload(record):
        raise ValueError("Skill install plan action payload is invalid")
    require_valid_skill_install_plan(record)
    from brain.v5.skill_install_plan_validation import validate_loaded_skill_install_plan

    validate_loaded_skill_install_plan(ws, pin, record)
    return pin, record


def checkpoint_request_payload(plan: SkillInstallPlanRecord) -> dict[str, Any]:
    payload = {
        "plan_id": plan.plan_id,
        "operation": plan.operation,
        "skill_id": plan.skill_id,
        "semantic_version": plan.semantic_version,
        "package_hash": plan.package_hash,
        "tree_hash": plan.tree_hash,
        "diff_hash": plan.diff_hash,
        "target_root": plan.target_root,
        "target_path": plan.target_path,
        "hosts": list(plan.hosts),
        "expected_before_hash": plan.expected_before_hash,
        "expected_after_hash": plan.expected_after_hash,
        "existing_skill_id": plan.existing_skill_id,
        "existing_semantic_version": plan.existing_semantic_version,
        "existing_package_hash": plan.existing_package_hash,
        "validation_policy": dict(plan.validation_policy),
        "validation_policy_hash": plan.validation_policy_hash,
    }
    if plan.patch_proposal_ref:
        payload.update(
            {
                "patch_proposal_ref": dict(plan.patch_proposal_ref),
                "old_package_hash": plan.old_package_hash,
                "new_package_hash": plan.new_package_hash,
            }
        )
    return payload


def _install_operation(proposal, *, before_hash, existing_manifest):
    if before_hash == EMPTY_TREE_HASH:
        return "install"
    if not existing_manifest:
        raise ValueError("Skill target exists but is not a managed AITP package")
    if existing_manifest.get("skill_id") != proposal.skill_id:
        raise ValueError("Skill target belongs to a different or external Skill")
    existing_hash = str(existing_manifest.get("package_hash") or "")
    existing_version = str(existing_manifest.get("semantic_version") or "")
    if existing_hash == proposal.package_hash and existing_version == proposal.semantic_version:
        return "reinstall"
    current, proposed = semver(existing_version), semver(proposal.semantic_version)
    if proposed == current:
        raise ValueError("same Skill id and version already bind different package bytes")
    if proposed < current:
        raise ValueError("Skill downgrade requires an explicit rollback plan")
    return "upgrade"


def target_paths(target_root: str | Path, name: str) -> tuple[Path, Path]:
    raw_root = Path(target_root).expanduser()
    raw_root = raw_root if raw_root.is_absolute() else raw_root.absolute()
    home_root = Path.home().expanduser()
    home_root = home_root if home_root.is_absolute() else home_root.absolute()
    if raw_root.resolve(strict=False) == home_root.resolve(strict=False):
        raise ValueError("user-global Skill target roots are forbidden")
    _reject_link_components(raw_root)
    root = raw_root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Skill target root must be an existing project directory")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError("generated Skill name is not path-safe")
    if link_like(root):
        raise ValueError("Skill target root cannot be a link or junction")
    target = root / ".agents" / "skills" / "aitp-generated" / name
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("Skill target escapes the explicit project root") from exc
    current = root
    for part in target.relative_to(root).parts:
        current = current / part
        if current.exists() and link_like(current):
            raise ValueError("Skill target path cannot contain a link or junction")
    return root, target


def snapshot_target(target: Path) -> tuple[str, dict[str, Any]]:
    if not target.exists():
        return EMPTY_TREE_HASH, {}
    if link_like(target) or not target.is_dir():
        raise ValueError("Skill target must be a normal directory")
    files: dict[str, bytes] = {}
    for path in sorted(target.rglob("*"), key=lambda item: item.as_posix().encode("utf-8")):
        if link_like(path):
            raise ValueError("Skill target cannot contain links or junctions")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError("Skill target contains an unsupported filesystem entry")
        files[path.relative_to(target).as_posix()] = path.read_bytes()
    manifest: dict[str, Any] = {}
    if "manifest.json" in files:
        try:
            decoded = json.loads(files["manifest.json"].decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("existing Skill manifest is invalid") from exc
        if not isinstance(decoded, dict):
            raise ValueError("existing Skill manifest must be an object")
        if decoded.get("namespace") != "aitp-generated":
            raise ValueError("existing Skill target is not managed by AITP")
        manifest = decoded
        _require_managed_target_integrity(files, manifest)
    return files_tree_hash(files), manifest


def _require_managed_target_integrity(files, manifest):
    package_hash = str(manifest.get("package_hash") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", package_hash):
        raise ValueError("existing managed Skill package hash is invalid")
    if package_manifest_hash(dict(manifest)) != package_hash:
        raise ValueError("existing managed Skill manifest hash is invalid")
    rows = manifest.get("included_files")
    if not isinstance(rows, list):
        raise ValueError("existing managed Skill manifest file list is invalid")
    expected_paths = {"manifest.json"}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("existing managed Skill manifest file row is invalid")
        path, content = str(row.get("path") or ""), files.get(str(row.get("path") or ""))
        if content is None:
            raise ValueError("existing managed Skill file is missing")
        if row.get("mode") != "0644":
            raise ValueError("existing managed Skill file mode is invalid")
        if row.get("length") != len(content) or row.get("sha256") != hashlib.sha256(content).hexdigest():
            raise ValueError("existing managed Skill file does not match its manifest")
        expected_paths.add(path)
    if set(files) != expected_paths:
        raise ValueError("existing managed Skill contains undeclared files")


def files_tree_hash(files: Mapping[str, bytes]) -> str:
    rows = [
        {"path": path, "length": len(content), "sha256": hashlib.sha256(content).hexdigest()}
        for path, content in sorted(files.items(), key=lambda item: item[0].encode("utf-8"))
    ]
    return sha256_json(rows)


def target_scopes(plan, plan_pin):
    scopes = [
        plan_pin.record_ref,
        f"project-root:{plan.target_root}",
        f"project-skill-path:{plan.target_path}",
    ]
    if plan.patch_proposal_ref:
        scopes.append(coerce_pin(plan.patch_proposal_ref).record_ref)
    return scopes


def coerce_pin(value):
    if isinstance(value, PinnedRecordRef):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("pinned ref must be a mapping or PinnedRecordRef")
    return PinnedRecordRef(
        str(value.get("record_ref") or ""),
        str(value.get("content_hash") or ""),
        value.get("revision"),
    )


def semver(value):
    match = SEMVER.fullmatch(value)
    if not match:
        raise ValueError("Skill semantic version must be canonical MAJOR.MINOR.PATCH")
    return tuple(int(part) for part in match.groups())


def link_like(path):
    is_junction = getattr(path, "is_junction", None)
    return path.is_symlink() or bool(is_junction and is_junction())


def _reject_link_components(path: Path) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        if current.exists() and link_like(current):
            raise ValueError("Skill target root cannot contain a link or junction")
