"""Deterministic projections shared by Skill install planning and verification."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from typing import Any, Mapping, Sequence

from brain.v5.ids import prefixed_id
from brain.v5.skill_validation_execution import classify_skill_validation_policy


def validation_policy_for(commands: Sequence[Mapping[str, Any]]):
    policy = classify_skill_validation_policy(commands)
    payload = {
        "command_digest": policy.command_digest,
        "executor": (
            "aitp_builtin_declarative_parser"
            if not policy.requires_m2_execution
            else "m2_bound_execution"
        ),
        "requires_m2_execution": policy.requires_m2_execution,
        "network": policy.network_policy,
        "writable_roots": list(policy.writable_roots),
        "timeout_seconds": policy.timeout_seconds,
        "environment_allowlist": list(policy.environment_allowlist),
        "can_execute": False,
        "can_update_claim_trust": False,
    }
    return policy, payload


def checkpoint_action_for(operation: str, *, is_patch: bool = False) -> str:
    if is_patch:
        if operation != "upgrade":
            raise ValueError("Skill patch plans must be monotonic upgrades")
        return "apply_aitp_skill_patch"
    if operation == "rollback":
        return "rollback_aitp_skill"
    if operation in {"reinstall", "upgrade", "overwrite"}:
        return "overwrite_aitp_skill"
    if operation == "install":
        return "install_aitp_skill"
    raise ValueError("Skill install plan operation is invalid")


def diff_projection_for(
    *,
    operation: str,
    skill_id: str,
    semantic_version: str,
    package_hash: str,
    tree_hash: str,
    target_root: str,
    target_path: str,
    hosts: Sequence[str],
    before_hash: str,
    after_hash: str,
    existing_skill_id: str,
    existing_semantic_version: str,
    existing_package_hash: str,
    validation_policy_hash: str,
    patch_proposal_ref: Mapping[str, Any] | None = None,
    old_package_hash: str = "",
    new_package_hash: str = "",
) -> dict[str, Any]:
    projection = {
        "operation": operation,
        "skill_id": skill_id,
        "semantic_version": semantic_version,
        "package_hash": package_hash,
        "tree_hash": tree_hash,
        "target_root": target_root,
        "target_path": target_path,
        "hosts": list(hosts),
        "before_hash": before_hash,
        "after_hash": after_hash,
        "existing_skill_id": existing_skill_id,
        "existing_semantic_version": existing_semantic_version,
        "existing_package_hash": existing_package_hash,
        "validation_policy_hash": validation_policy_hash,
    }
    if patch_proposal_ref:
        projection.update(
            {
                "patch_proposal_ref": dict(patch_proposal_ref),
                "old_package_hash": old_package_hash,
                "new_package_hash": new_package_hash,
            }
        )
    return projection


def plan_identity_for(diff_projection, proposal_pin, artifact_pin) -> dict[str, Any]:
    return {
        **diff_projection,
        "diff_hash": sha256_json(diff_projection),
        "proposal_ref": asdict(proposal_pin),
        "package_artifact_ref": asdict(artifact_pin),
    }


def plan_id_for(identity: Mapping[str, Any]) -> str:
    return prefixed_id("skill-install-plan", sha256_json(identity), max_slug=64)


def sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
