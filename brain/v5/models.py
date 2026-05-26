"""Data records used by the AITP v5 kernel."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ContextRecord:
    context_id: str
    title: str
    kind: str = "context"
    status: str = "active"


@dataclass
class TopicRecord:
    topic_id: str
    context_id: str
    title: str
    kind: str = "topic"
    status: str = "active"


@dataclass
class SessionBinding:
    session_id: str
    topic_id: str
    context_id: str
    runtime: str = "unknown"
    interaction_profile: str = "collaborator"
    interaction_steering: str = ""
    active_cycle: str = ""
    active_claim: str = ""
    active_route: str = ""
    write_scope: list[str] = field(default_factory=list)
    lock_level: str = "none"
    kind: str = "session_binding"


@dataclass
class ClaimRecord:
    claim_id: str
    topic_id: str
    statement: str
    evidence_profile: str
    confidence_state: str
    active_uncertainty: str
    recipe_id: str = ""
    scope: str = ""
    non_claims: str = ""
    strongest_failure_mode: str = ""
    kind: str = "claim"


@dataclass
class TrustUpdateRequest:
    request_id: str
    action: str
    session_id: str
    topic_id: str
    claim_id: str
    requested_state: str = ""
    source_kind: str = ""
    source_ref: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    code_state_ids: list[str] = field(default_factory=list)
    rationale: str = ""
    preflight_token: str = ""
    kind: str = "trust_update_request"


@dataclass
class TrustUpdateRecord:
    update_id: str
    request_id: str
    action: str
    session_id: str
    topic_id: str
    claim_id: str
    previous_state: str
    new_state: str
    applied: bool
    preflight_allowed: bool
    requested_state: str = ""
    source_kind: str = ""
    source_ref: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    code_state_ids: list[str] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)
    policy_reason_ids: list[str] = field(default_factory=list)
    preflight_token: str = ""
    status: str = "blocked"
    rationale: str = ""
    kind: str = "trust_update"

    @property
    def record_id(self) -> str:
        return self.update_id


@dataclass
class FlowDecision:
    profile: str
    reason: str
    escalation_triggers: list[str] = field(default_factory=list)
    risk_level: str = ""
    risk_score: int = 0
    action_budget: dict = field(default_factory=dict)


@dataclass
class QuestionRecord:
    question_id: str
    scene: str
    target_claim: str
    question: str
    why_this_question: str
    expected_answer_shape: str
    possible_next_actions: list[str] = field(default_factory=list)
    target_objects: list[str] = field(default_factory=list)
    target_relations: list[str] = field(default_factory=list)
    target_uncertainty: str = ""
    intent_id: str = ""
    intent_type: str = ""
    expansion_boundary: str = ""
    escalation_if_unanswered: str = ""
    kind: str = "dynamic_question"


@dataclass
class CodeWorkspaceRecord:
    workspace_id: str
    topic_id: str
    session_id: str
    repo_id: str
    worktree_path: str
    branch_name: str
    base_commit: str
    purpose: str
    upstream_tracking_branch: str = ""
    write_scope: list[str] = field(default_factory=list)
    active_claim: str = ""
    active_attempt: str = ""
    status: str = "active"
    cleanup_plan: str = ""
    kind: str = "code_workspace"


@dataclass
class CodeStateRecord:
    code_state_id: str
    repo_id: str
    upstream_remote: str
    upstream_branch: str
    upstream_commit: str
    local_branch: str
    worktree_path: str
    dirty: bool
    patch_id: str = ""
    diff_hash: str = ""
    build_config: dict = field(default_factory=dict)
    runtime_environment: dict = field(default_factory=dict)
    linked_records: dict = field(default_factory=dict)
    known_divergence: str = ""
    kind: str = "code_state"


@dataclass
class ToolRecipeRecord:
    recipe_id: str
    tool_family: str
    tool_name: str
    purpose: str
    required_inputs: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    kind: str = "tool_recipe"


@dataclass
class ToolRunRecord:
    run_id: str
    recipe_id: str
    tool_family: str
    tool_name: str
    topic_id: str
    claim_id: str
    inputs: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    environment: dict = field(default_factory=dict)
    evidence_status: str = "unreviewed"
    code_state_ids: list[str] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    kind: str = "tool_run"


@dataclass
class ArtifactRecord:
    artifact_id: str
    topic_id: str
    claim_id: str
    artifact_type: str
    uri: str
    summary: str
    size_bytes: int = 0
    metadata: dict = field(default_factory=dict)
    kind: str = "artifact"


@dataclass
class ReferenceLocationRecord:
    location_id: str
    topic_id: str
    connector_id: str
    location_type: str
    uri: str
    label: str
    claim_id: str = ""
    source_ref: str = ""
    external_id: str = ""
    status: str = "located"
    summary: str = ""
    metadata: dict = field(default_factory=dict)
    linked_records: dict = field(default_factory=dict)
    orientation_only: bool = True
    kind: str = "reference_location"


@dataclass
class EvidenceRecord:
    evidence_id: str
    topic_id: str
    claim_id: str
    evidence_type: str
    status: str
    summary: str
    supports_outputs: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    tool_run_ids: list[str] = field(default_factory=list)
    validation_result_ids: list[str] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    kind: str = "evidence"


@dataclass
class BenchmarkRecord:
    benchmark_id: str
    topic_id: str
    claim_id: str
    observable: str
    reference_value: str
    tolerance: str
    source_ref: str
    kind: str = "benchmark"


@dataclass
class PhysicsObjectRecord:
    object_id: str
    topic_id: str
    object_type: str
    name: str
    definition: str
    notation: str = ""
    assumptions: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    linked_records: dict = field(default_factory=dict)
    status: str = "active"
    kind: str = "physics_object"


@dataclass
class ObjectRelationRecord:
    relation_id: str
    topic_id: str
    relation_type: str
    subject_id: str
    object_id: str
    statement: str
    claim_id: str = ""
    assumptions: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    status: str = "hypothesis"
    kind: str = "object_relation"


@dataclass
class SensemakingReportRecord:
    report_id: str
    topic_id: str
    claim_id: str
    title: str
    summary: str
    object_ids: list[str] = field(default_factory=list)
    relation_ids: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    validation_status: str = "not_validation"
    kind: str = "sensemaking_report"


@dataclass
class ValidationContractRecord:
    contract_id: str
    topic_id: str
    claim_id: str
    required_checks: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    required_evidence_outputs: list[str] = field(default_factory=list)
    tool_recipe_ids: list[str] = field(default_factory=list)
    executor_ids: list[str] = field(default_factory=list)
    validator_role: str = "adversarial_reviewer"
    status: str = "open"
    kind: str = "validation_contract"


@dataclass
class ValidationResultRecord:
    result_id: str
    topic_id: str
    claim_id: str
    contract_id: str
    tool_run_id: str
    status: str
    checked_outputs: list[str] = field(default_factory=list)
    missing_outputs: list[str] = field(default_factory=list)
    covered_failure_modes: list[str] = field(default_factory=list)
    failure_modes_observed: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    summary: str = ""
    kind: str = "validation_result"


@dataclass
class HumanCheckpointRecord:
    checkpoint_id: str
    topic_id: str
    claim_id: str
    reason: str
    requested_by: str
    options: list[str] = field(default_factory=list)
    status: str = "open"
    decision: str = ""
    rationale: str = ""
    decided_by: str = ""
    kind: str = "human_checkpoint"


@dataclass
class FailureModeReviewResultRecord:
    result_id: str
    topic_id: str
    claim_id: str
    checkpoint_id: str
    status: str
    reviewed_failure_modes: list[str] = field(default_factory=list)
    basis_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    validation_result_ids: list[str] = field(default_factory=list)
    tool_run_ids: list[str] = field(default_factory=list)
    reference_location_ids: list[str] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    reviewer_role: str = "adversarial_reviewer"
    summary: str = ""
    summary_inputs_trusted: bool = False
    can_update_claim_trust: bool = False
    kind: str = "failure_mode_review_result"


@dataclass
class SourceReconstructionReviewResultRecord:
    result_id: str
    topic_id: str
    claim_id: str
    status: str
    reviewed_components: list[str] = field(default_factory=list)
    basis_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    validation_result_ids: list[str] = field(default_factory=list)
    reference_location_ids: list[str] = field(default_factory=list)
    object_ids: list[str] = field(default_factory=list)
    relation_ids: list[str] = field(default_factory=list)
    remaining_actions: list[str] = field(default_factory=list)
    reviewer_role: str = "human_or_adversarial_reviewer"
    summary: str = ""
    created_at: str = ""
    summary_inputs_trusted: bool = False
    can_update_claim_trust: bool = False
    kind: str = "source_reconstruction_review_result"


@dataclass
class LegacySemanticReviewResultRecord:
    review_id: str
    migration_run_id: str
    migration_dir: str
    topic: str
    status: str
    summary: str
    active_claim_id: str = ""
    reviewer_role: str = "human_or_adversarial_reviewer"
    reviewed_legacy_refs: list[str] = field(default_factory=list)
    reviewed_typed_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    validation_result_ids: list[str] = field(default_factory=list)
    remaining_actions: list[str] = field(default_factory=list)
    checkpoint_id: str = ""
    created_at: str = ""
    summary_inputs_trusted: bool = False
    can_update_claim_trust: bool = False
    kind: str = "legacy_semantic_review_result"


@dataclass
class LegacySemanticRepairRecord:
    repair_id: str
    migration_run_id: str
    migration_dir: str
    topic: str
    active_claim_id: str
    review_id: str
    repair_type: str
    previous_value: str
    new_value: str
    basis_refs: list[str] = field(default_factory=list)
    applied: bool = False
    required_actions: list[str] = field(default_factory=list)
    summary_inputs_trusted: bool = False
    can_update_claim_trust: bool = False
    kind: str = "legacy_semantic_repair"

    @property
    def record_id(self) -> str:
        return self.repair_id


@dataclass
class PromotionPacketRecord:
    packet_id: str
    topic_id: str
    claim_id: str
    proposed_memory_kind: str = "scoped_claim"
    scope: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    validation_result_ids: list[str] = field(default_factory=list)
    non_claims: list[str] = field(default_factory=list)
    known_failure_modes: list[str] = field(default_factory=list)
    failure_mode_review_checkpoint_id: str = ""
    failure_mode_review_result_id: str = ""
    status: str = "pending_human_checkpoint"
    human_checkpoint_id: str = ""
    kind: str = "promotion_packet"

    @property
    def record_id(self) -> str:
        return self.packet_id


@dataclass
class MemoryEntryRecord:
    entry_id: str
    topic_id: str
    source_claim_id: str
    source_topic_id: str = ""
    statement: str = ""
    memory_kind: str = "scoped_claim"
    scope: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    validation_result_ids: list[str] = field(default_factory=list)
    non_claims: list[str] = field(default_factory=list)
    known_failure_modes: list[str] = field(default_factory=list)
    source_packet_id: str = ""
    human_checkpoint_id: str = ""
    failure_mode_review_checkpoint_id: str = ""
    failure_mode_review_result_id: str = ""
    status: str = "active"
    kind: str = "memory_entry"

    @property
    def record_id(self) -> str:
        return self.entry_id
