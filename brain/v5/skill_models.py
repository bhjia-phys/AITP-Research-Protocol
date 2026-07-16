"""Typed records and request/report models for reviewed procedural Skills."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SkillDistillationRequest:
    title: str
    summary: str
    workflow_kind: str
    input_kinds: tuple[str, ...]
    source_topic_ids: tuple[str, ...]
    ordered_steps: tuple[dict[str, Any], ...]
    parameter_contract: dict[str, Any]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    prerequisites: tuple[str, ...]
    stop_rules: tuple[str, ...]
    known_failures: tuple[dict[str, Any], ...]
    applicability_selectors: dict[str, Any]
    transfer_boundary: str
    package_requirements: tuple[str, ...]
    recipe_refs: tuple[Any, ...]
    execution_refs: tuple[Any, ...]
    validation_refs: tuple[Any, ...]
    artifact_refs: tuple[Any, ...]
    code_state_refs: tuple[Any, ...]
    environment_refs: tuple[Any, ...]
    source_program_refs: tuple[Any, ...] = ()
    source_refs: tuple[Any, ...] = ()
    failure_boundary: str = ""


@dataclass
class SkillDistillationCandidateRecord:
    candidate_id: str
    title: str
    summary: str
    workflow_kind: str
    workflow_signature: str
    input_kinds: list[str]
    source_topic_ids: list[str]
    source_program_refs: list[dict]
    ordered_steps: list[dict]
    parameter_contract: dict
    inputs: list[str]
    outputs: list[str]
    prerequisites: list[str]
    stop_rules: list[str]
    known_failures: list[dict]
    recipe_refs: list[dict]
    execution_refs: list[dict]
    validation_refs: list[dict]
    artifact_refs: list[dict]
    code_state_refs: list[dict]
    environment_refs: list[dict]
    source_refs: list[dict]
    independent_execution_keys: list[str]
    applicability_selectors: dict
    transfer_boundary: str
    package_requirements: list[str]
    failure_boundary: str = ""
    status: str = "draft"
    created_at: str = ""
    requires_human_review: bool = True
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    can_update_claim_trust: bool = False
    kind: str = "skill_distillation_candidate"

    def __post_init__(self) -> None:
        if self.status not in {"draft", "reviewed", "rejected", "superseded"}:
            raise ValueError("skill distillation candidate status is invalid")
        if not self.requires_human_review:
            raise ValueError("skill distillation candidates require human review")
        if self.summary_inputs_trusted or not self.orientation_only:
            raise ValueError("skill distillation candidates are orientation-only")
        if self.can_update_claim_trust:
            raise ValueError("skill distillation candidates cannot update claim trust")


@dataclass
class SkillReadinessReportRecord:
    report_id: str
    candidate_ref: dict
    candidate_id: str
    candidate_signature: str
    status: str
    readiness_basis: str
    independent_use_count: int
    checked_execution_refs: list[dict]
    validation_fixture_refs: list[str]
    failure_coverage: dict
    overlap: dict
    blockers: list[str]
    required_actions: list[str]
    expert_exception_ref: dict = field(default_factory=dict)
    created_at: str = ""
    ready_for_package_preview: bool = False
    can_install_skill: bool = False
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    can_update_claim_trust: bool = False
    kind: str = "skill_readiness_report"

    def __post_init__(self) -> None:
        if self.status not in {"ready", "blocked"}:
            raise ValueError("skill readiness status must be ready or blocked")
        if self.ready_for_package_preview != (self.status == "ready"):
            raise ValueError("package preview readiness must match report status")
        if self.can_install_skill:
            raise ValueError("readiness reports cannot install Skills")
        if self.summary_inputs_trusted or not self.orientation_only:
            raise ValueError("skill readiness reports are orientation-only")
        if self.can_update_claim_trust:
            raise ValueError("skill readiness reports cannot update claim trust")


@dataclass(frozen=True)
class SkillPackagePreview:
    skill_id: str
    namespace: str
    name: str
    semantic_version: str
    package_hash: str
    candidate_ref: dict
    readiness_ref: dict
    files: dict[str, bytes]
    manifest: dict
    preview_dir: str
    generator_version: str
    can_install_skill: bool = False
    can_update_claim_trust: bool = False

    def contract_payload(self) -> dict:
        import hashlib

        return {
            "kind": "skill_package_preview",
            "skill_id": self.skill_id,
            "namespace": self.namespace,
            "name": self.name,
            "semantic_version": self.semantic_version,
            "package_hash": self.package_hash,
            "candidate_ref": dict(self.candidate_ref),
            "readiness_ref": dict(self.readiness_ref),
            "files": [
                {
                    "path": path,
                    "mode": "0644",
                    "length": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
                for path, content in sorted(self.files.items())
            ],
            "manifest": dict(self.manifest),
            "preview_dir": self.preview_dir,
            "generator_version": self.generator_version,
            "can_install_skill": self.can_install_skill,
            "can_update_claim_trust": self.can_update_claim_trust,
        }


@dataclass(frozen=True)
class SkillPackageArtifactRecord:
    artifact_id: str
    skill_id: str
    semantic_version: str
    package_hash: str
    tree_hash: str
    candidate_ref: dict
    readiness_ref: dict
    files: list[dict]
    renderer_blob_ref: str
    renderer_blob_hash: str
    renderer_blob_revision: int
    generator_version: str
    template_refs: list[dict] = field(default_factory=list)
    immutable: bool = True
    can_install_skill: bool = False
    can_update_claim_trust: bool = False
    kind: str = "skill_package_artifact"

    def __post_init__(self) -> None:
        if not self.immutable:
            raise ValueError("skill package artifacts are immutable")
        if self.can_install_skill or self.can_update_claim_trust:
            raise ValueError("skill package artifacts have no install or trust authority")


@dataclass(frozen=True)
class SkillProposalRecord:
    proposal_id: str
    skill_id: str
    namespace: str
    name: str
    semantic_version: str
    package_hash: str
    tree_hash: str
    candidate_ref: dict
    readiness_ref: dict
    package_artifact_ref: dict
    source_topic_ids: list[str]
    recipe_refs: list[dict]
    source_program_refs: list[dict]
    execution_refs: list[dict]
    validation_refs: list[dict]
    artifact_refs: list[dict]
    code_state_refs: list[dict]
    environment_refs: list[dict]
    source_refs: list[dict]
    failure_basis: dict
    applicability_selectors: dict
    manifest: dict
    file_hashes: list[dict]
    validation_commands: list[dict]
    review_status: str = "draft"
    application_status: str = "not_applied"
    requires_human_review: bool = True
    can_install_skill: bool = False
    can_update_claim_trust: bool = False
    kind: str = "skill_proposal"

    def __post_init__(self) -> None:
        if self.review_status != "draft":
            raise ValueError("skill proposals must remain draft")
        if self.application_status != "not_applied":
            raise ValueError("skill proposals must remain not_applied")
        if not self.requires_human_review or self.can_install_skill:
            raise ValueError("skill proposals require review and cannot install directly")
        if self.can_update_claim_trust:
            raise ValueError("skill proposals cannot update claim trust")


@dataclass(frozen=True)
class CandidateBuildReport:
    eligible: bool
    candidate: SkillDistillationCandidateRecord | None
    rejection_reasons: tuple[str, ...] = ()
    missing_requirements: tuple[str, ...] = ()
    independent_execution_count: int = 0
    checked_record_refs: tuple[str, ...] = ()
    can_update_claim_trust: bool = False

    def __post_init__(self) -> None:
        if self.can_update_claim_trust:
            raise ValueError("candidate build reports cannot update claim trust")
        if self.eligible != (self.candidate is not None):
            raise ValueError("eligible reports must contain exactly one candidate")
