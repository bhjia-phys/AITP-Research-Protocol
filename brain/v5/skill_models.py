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
