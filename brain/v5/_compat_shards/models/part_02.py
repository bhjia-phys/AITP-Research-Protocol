# Compatibility shard 2 for models.
from __future__ import annotations

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
class ExploratoryRecord:
    record_id: str
    topic_id: str
    claim_id: str
    session_id: str
    exploration_type: str
    title: str
    focal_question: str
    summary: str
    original_question: str = ""
    local_question: str = ""
    status: str = "open"
    object_ids: list[str] = field(default_factory=list)
    relation_ids: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    parent_record_ids: list[str] = field(default_factory=list)
    derived_record_ids: list[str] = field(default_factory=list)
    reasoning_moves: list[str] = field(default_factory=list)
    backtrace_targets: list[str] = field(default_factory=list)
    candidate_paths: list[str] = field(default_factory=list)
    relation_path_questions: list[str] = field(default_factory=list)
    definition_boundary_questions: list[str] = field(default_factory=list)
    derivation_backtrace_questions: list[str] = field(default_factory=list)
    source_dependency_questions: list[str] = field(default_factory=list)
    original_question_guard: list[str] = field(default_factory=list)
    unresolved_points: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    human_steering: str = ""
    metadata: dict = field(default_factory=dict)
    orientation_only: bool = True
    can_update_claim_trust: bool = False
    kind: str = "exploratory_record"

@dataclass
class ResearchRouteRecord:
    route_id: str
    topic_id: str
    title: str
    route_type: str
    status: str
    rationale: str
    claim_id: str = ""
    session_id: str = ""
    current_question: str = ""
    next_action: str = ""
    failure_modes: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    parent_route_ids: list[str] = field(default_factory=list)
    checkpoint_ids: list[str] = field(default_factory=list)
    exploratory_record_ids: list[str] = field(default_factory=list)
    object_ids: list[str] = field(default_factory=list)
    relation_ids: list[str] = field(default_factory=list)
    decision_rationale: str = ""
    pivot_reason: str = ""
    metadata: dict = field(default_factory=dict)
    orientation_only: bool = True
    can_update_claim_trust: bool = False
    kind: str = "research_route"

@dataclass
class ResearchRunRecord:
    run_id: str
    topic_id: str
    objective: str
    research_question: str
    operator: str
    status: str
    phase: str
    title: str = ""
    claim_id: str = ""
    session_id: str = ""
    hypothesis: str = ""
    terminal_answer_state: str = ""
    stop_reason: str = ""
    aitp_slice_refs: list[str] = field(default_factory=list)
    action_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    validation_refs: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    event_ids: list[str] = field(default_factory=list)
    operator_trail: list[dict] = field(default_factory=list)
    answer_packet_ref: str = ""
    metadata: dict = field(default_factory=dict)
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    can_update_kernel_state: bool = True
    can_update_claim_trust: bool = False
    kind: str = "research_run"

@dataclass
class ResearchRunEventRecord:
    event_id: str
    run_id: str
    topic_id: str
    operator: str
    event_type: str
    summary: str
    status: str = "recorded"
    phase: str = ""
    claim_id: str = ""
    session_id: str = ""
    action_id: str = ""
    action_ref: str = ""
    source_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    validation_refs: list[str] = field(default_factory=list)
    artifact_refs: list[str] = field(default_factory=list)
    payload: dict = field(default_factory=dict)
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    can_update_kernel_state: bool = True
    can_update_claim_trust: bool = False
    kind: str = "research_run_event"

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
    decision_verified: bool = False
    decision_verification: str = ""
    decision_receipt_hash: str = ""
    decision_receipt_nonce: str = ""
    can_authorize_trust: bool = False
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
class LegacyL2SeedGroupReviewResultRecord:
    review_id: str
    group_id: str
    status: str
    decision: str
    summary: str
    topic_id: str = ""
    target_topic_id: str = ""
    source_claim_id: str = ""
    memory_role: str = ""
    source_family: str = ""
    source_object_id: str = ""
    reviewer_role: str = "human_or_adversarial_reviewer"
    reviewed_seed_entry_ids: list[str] = field(default_factory=list)
    reviewed_seed_refs: list[str] = field(default_factory=list)
    reviewed_typed_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    validation_result_ids: list[str] = field(default_factory=list)
    remaining_actions: list[str] = field(default_factory=list)
    checkpoint_id: str = ""
    created_at: str = ""
    summary_inputs_trusted: bool = False
    can_update_claim_trust: bool = False
    kind: str = "legacy_l2_seed_group_review_result"

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

@dataclass
class LaneContractRecord:
    """A typed lane contract for a compute topic.

    Promotes the cockpit's lane discipline (forbidden/preferred remote roots,
    final allowlist, final-evidence rules, default lane) from a generated JSON
    surface into an auditable, rehome-able typed record. It constrains how
    downstream plotting/reporting treats rows and which roots may feed final
    evidence, but it cannot update claim trust.
    """

    contract_id: str
    topic_id: str
    campaign: str = ""
    claim_id: str = ""
    forbidden_roots: list[str] = field(default_factory=list)
    preferred_clean_roots: list[str] = field(default_factory=list)
    final_allowlist: list[str] = field(default_factory=list)
    final_rules: list[str] = field(default_factory=list)
    default_lane: str = "diagnostic"
    trust_update_forbidden: bool = False
    notes: list[str] = field(default_factory=list)
    lifecycle_status: str = "active"
    metadata: dict = field(default_factory=dict)
    kind: str = "lane_contract"

    @property
    def record_id(self) -> str:
        return self.contract_id
