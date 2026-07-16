"""Exact patch-to-install-plan adapter for reviewed Skill upgrades."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from brain.v5.models import SkillPatchProposalRecord, SkillProposalRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
from brain.v5.record_envelope import RecordActor
from brain.v5.skill_install_planning import (
    _install_operation,
    _record_plan,
    coerce_pin,
    proposal_package,
    snapshot_target,
    target_paths,
)
from brain.v5.skill_usage import validate_skill_patch_proposal


def build_skill_patch_install_plan(
    ws: WorkspacePaths,
    patch_proposal_ref: PinnedRecordRef | Mapping[str, Any],
    target_root: str | Path,
    hosts: Sequence[str],
    *,
    actor: RecordActor,
):
    patch_pin = coerce_pin(patch_proposal_ref)
    patch = get_record_version(ws, patch_pin).record
    if not isinstance(patch, SkillPatchProposalRecord):
        raise ValueError("patch_proposal_ref must pin a SkillPatchProposalRecord")
    validate_skill_patch_proposal(ws, patch)
    new_pin = coerce_pin(patch.new_package_proposal_ref)
    proposal_pin, proposal, artifact_pin, artifact, files, manifest = proposal_package(
        ws, new_pin
    )
    if proposal_pin != new_pin:
        raise ValueError("Skill patch new package proposal changed")
    old_pin = coerce_pin(patch.old_package_proposal_ref)
    old_proposal = get_record_version(ws, old_pin).record
    if not isinstance(old_proposal, SkillProposalRecord):
        raise ValueError("Skill patch old package proposal is invalid")
    expected_patch = (
        patch.skill_id,
        patch.current_version,
        patch.proposed_version,
        patch.old_package_hash,
        patch.new_package_hash,
    )
    actual_patch = (
        proposal.skill_id,
        old_proposal.semantic_version,
        proposal.semantic_version,
        old_proposal.package_hash,
        proposal.package_hash,
    )
    if expected_patch != actual_patch or proposal.name != patch.skill_name:
        raise ValueError("Skill patch package identities disagree")
    root, target = target_paths(target_root, proposal.name)
    before_hash, existing_manifest = snapshot_target(target)
    if (
        not existing_manifest
        or existing_manifest.get("skill_id") != patch.skill_id
        or existing_manifest.get("semantic_version") != patch.current_version
        or existing_manifest.get("package_hash") != patch.old_package_hash
    ):
        raise ValueError("Skill patch target does not match its exact old package")
    if _install_operation(
        proposal,
        before_hash=before_hash,
        existing_manifest=existing_manifest,
    ) != "upgrade":
        raise ValueError("Skill patch must be a monotonic package upgrade")
    return _record_plan(
        ws,
        actor=actor,
        operation="upgrade",
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
        patch_pin=patch_pin,
        old_package_hash=patch.old_package_hash,
        new_package_hash=patch.new_package_hash,
    )
