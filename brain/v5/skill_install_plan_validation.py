"""Source and derived-field verification for immutable Skill install plans."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.models import SkillPatchProposalRecord
from brain.v5.pinned_record_refs import get_record_version
from brain.v5.skill_install_plan_derivations import (
    checkpoint_action_for,
    diff_projection_for,
    plan_id_for,
    plan_identity_for,
    sha256_json,
    validation_policy_for,
)


def validate_loaded_skill_install_plan(ws, pin, plan) -> None:
    from brain.v5.skill_install_planning import (
        checkpoint_request_payload,
        coerce_pin,
        files_tree_hash,
        proposal_package,
        snapshot_target,
        target_paths,
    )

    proposal_pin, proposal, artifact_pin, artifact, files, _manifest = proposal_package(
        ws,
        plan.proposal_ref,
    )
    if proposal_pin != coerce_pin(plan.proposal_ref):
        raise ValueError("Skill install plan proposal pin is invalid")
    if artifact_pin != coerce_pin(plan.package_artifact_ref):
        raise ValueError("Skill install plan package artifact pin is invalid")
    expected_source = (
        proposal.skill_id,
        proposal.name,
        proposal.semantic_version,
        proposal.package_hash,
        artifact.tree_hash,
        [dict(command) for command in proposal.validation_commands],
    )
    actual_source = (
        plan.skill_id,
        plan.name,
        plan.semantic_version,
        plan.package_hash,
        plan.tree_hash,
        plan.validation_commands,
    )
    if actual_source != expected_source:
        raise ValueError("Skill install plan identity disagrees with its pinned proposal")
    patch_pin = None
    if plan.patch_proposal_ref:
        patch_pin = coerce_pin(plan.patch_proposal_ref)
        patch = get_record_version(ws, patch_pin).record
        if not isinstance(patch, SkillPatchProposalRecord):
            raise ValueError("Skill install patch ref is invalid")
        from brain.v5.skill_usage import validate_skill_patch_proposal

        validate_skill_patch_proposal(ws, patch)
        if (
            patch.new_package_proposal_ref != asdict(proposal_pin)
            or patch.skill_id != proposal.skill_id
            or patch.proposed_version != proposal.semantic_version
            or patch.new_package_hash != proposal.package_hash
            or plan.old_package_hash != patch.old_package_hash
            or plan.new_package_hash != patch.new_package_hash
        ):
            raise ValueError("Skill install patch identity disagrees with its pinned proposal")

    root, target = target_paths(plan.target_root, plan.name)
    if str(root) != plan.target_root or str(target) != plan.target_path:
        raise ValueError("Skill install plan target derivation is invalid")
    current_hash, current_manifest = snapshot_target(target)
    if current_hash == plan.expected_before_hash:
        validate_plan_before_image(plan, proposal, current_hash, current_manifest)
    after_hash = files_tree_hash(files)
    if plan.expected_after_hash != after_hash:
        raise ValueError("Skill install plan after-image hash is invalid")
    _policy, validation_policy = validation_policy_for(plan.validation_commands)
    validation_policy_hash = sha256_json(validation_policy)
    if (
        plan.validation_policy != validation_policy
        or plan.validation_policy_hash != validation_policy_hash
    ):
        raise ValueError("Skill install plan validation policy derivation is invalid")

    projection = diff_projection_for(
        operation=plan.operation,
        skill_id=proposal.skill_id,
        semantic_version=proposal.semantic_version,
        package_hash=proposal.package_hash,
        tree_hash=artifact.tree_hash,
        target_root=str(root),
        target_path=str(target),
        hosts=plan.hosts,
        before_hash=plan.expected_before_hash,
        after_hash=after_hash,
        existing_skill_id=plan.existing_skill_id,
        existing_semantic_version=plan.existing_semantic_version,
        existing_package_hash=plan.existing_package_hash,
        validation_policy_hash=validation_policy_hash,
        patch_proposal_ref=asdict(patch_pin) if patch_pin is not None else None,
        old_package_hash=plan.old_package_hash,
        new_package_hash=plan.new_package_hash,
    )
    identity = plan_identity_for(projection, proposal_pin, artifact_pin)
    if plan.diff_hash != identity["diff_hash"] or plan.plan_id != plan_id_for(identity):
        raise ValueError("Skill install plan derived identity is invalid")
    if plan.plan_id != pin.record_ref.partition(":")[2]:
        raise ValueError("Skill install plan record identity is invalid")
    if plan.checkpoint_action != checkpoint_action_for(
        plan.operation,
        is_patch=patch_pin is not None,
    ):
        raise ValueError("Skill install plan checkpoint action is invalid")
    if plan.action_payload != checkpoint_request_payload(plan):
        raise ValueError("Skill install plan action payload is invalid")
    if plan.proposal_ref != asdict(proposal_pin) or plan.package_artifact_ref != asdict(
        artifact_pin
    ):
        raise ValueError("Skill install plan source refs are not exact")


def validate_plan_before_image(plan, proposal, before_hash, existing_manifest) -> None:
    from brain.v5.skill_install_planning import _install_operation, semver

    expected_existing = (
        str(existing_manifest.get("skill_id") or ""),
        str(existing_manifest.get("semantic_version") or ""),
        str(existing_manifest.get("package_hash") or ""),
    )
    actual_existing = (
        plan.existing_skill_id,
        plan.existing_semantic_version,
        plan.existing_package_hash,
    )
    if actual_existing != expected_existing:
        raise ValueError("Skill install plan existing before-image metadata is invalid")
    if plan.operation == "rollback":
        if not existing_manifest or expected_existing[0] != proposal.skill_id:
            raise ValueError("Skill rollback before-image is not the same managed Skill")
        if semver(proposal.semantic_version) >= semver(expected_existing[1]):
            raise ValueError("Skill rollback operation does not target an older version")
        expected_operation = "rollback"
    else:
        expected_operation = _install_operation(
            proposal,
            before_hash=before_hash,
            existing_manifest=existing_manifest,
        )
    if plan.operation != expected_operation:
        raise ValueError("Skill install plan operation disagrees with its before-image")
