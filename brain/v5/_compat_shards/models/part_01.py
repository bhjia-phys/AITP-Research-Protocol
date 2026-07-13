# Compatibility shard 1 for models.
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
class ActiveClaimRebindAuditRecord:
    audit_id: str
    session_id: str
    topic_id: str
    old_claim_id: str
    new_claim_id: str
    reason: str
    user_confirmation: str
    timestamp: str
    operator: str = "human"
    status: str = "applied"
    detection_warning_code: str = "active_claim_focus_drift_detected"
    candidate_snapshot: dict = field(default_factory=dict)
    source_records: dict = field(default_factory=dict)
    summary_inputs_trusted: bool = False
    orientation_only: bool = False
    can_update_kernel_state: bool = True
    can_update_claim_trust: bool = False
    trust_update_allowed: bool = False
    kind: str = "active_claim_rebind_audit"

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
    lifecycle_status: str = "active"
    rehome_event_id: str = ""
    rehome_target_topic: str = ""
    replaced_by: str = ""
    kind: str = "claim"

@dataclass
class ClaimStatusRecord:
    status_id: str
    topic_id: str
    claim_id: str
    maturity_level: str
    claim_status: str
    scope: str
    risk: str
    next_action: str
    assumptions: list[str] = field(default_factory=list)
    open_gaps: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    human_gate_required: bool = True
    can_update_claim_trust: bool = False
    kind: str = "claim_status"

@dataclass
class ProofObligationRecord:
    obligation_id: str
    topic_id: str
    claim_id: str
    statement: str
    obligation_type: str
    status: str
    maturity_level: str
    next_action: str
    required_evidence: list[str] = field(default_factory=list)
    proof_strategy: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    human_gate_required: bool = True
    can_update_claim_trust: bool = False
    kind: str = "proof_obligation"

@dataclass
class AuthorityRecord:
    authority_id: str
    topic_id: str
    authority_type: str
    authority_statement: str
    work_package: str = ""
    claim_id: str = ""
    scope: dict = field(default_factory=dict)
    generator_set: str = ""
    closure_envelope: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    linked_records: dict = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
    status: str = "research_authority_not_trust_promotion"
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    can_update_claim_trust: bool = False
    kind: str = "authority"

@dataclass
class QuietCheckpointBatchRecord:
    checkpoint_id: str
    topic_id: str
    session_id: str
    claim_id: str
    run_id: str
    summary: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    generated_artifacts: list[dict] = field(default_factory=list)
    validation_commands: list[str] = field(default_factory=list)
    durable_observations: list[str] = field(default_factory=list)
    claim_boundary: dict = field(default_factory=dict)
    next_blockers: list[str] = field(default_factory=list)
    planned_typed_writes: list[dict] = field(default_factory=list)
    written_refs: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    record_completeness_audit: dict = field(default_factory=dict)
    status: str = "recorded_without_trust_promotion"
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    can_update_kernel_state: bool = True
    can_update_claim_trust: bool = False
    kind: str = "quiet_checkpoint_batch"

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
    scientific_run_id: str = ""
    supersedes_run_id: str = ""
    lane: str = "diagnostic"
    kind: str = "tool_run"

    @property
    def supersedes(self) -> str:
        """Compatibility alias for the hash-protected forward attempt edge."""

        return self.supersedes_run_id

    @property
    def superseded_by(self) -> str:
        """Read-only compatibility hint; reverse edges are derived by readers."""

        return ""

@dataclass
class MonitorSnapshotRecord:
    snapshot_id: str
    topic_id: str
    claim_id: str
    tool_run_id: str
    run_dir: str
    job_id: str
    scheduler_state: dict = field(default_factory=dict)
    elapsed: str = ""
    output_file_sizes: dict = field(default_factory=dict)
    latest_log_markers: list[str] = field(default_factory=list)
    memory_status: dict = field(default_factory=dict)
    failure_markers: list[str] = field(default_factory=list)
    interpretation_boundary: str = ""
    claim_trust_mutation: str = "none"
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    can_update_claim_trust: bool = False
    kind: str = "monitor_snapshot"

@dataclass
class SkillPatchProposalRecord:
    proposal_id: str
    skill_name: str
    current_version: str
    proposed_version: str
    patch_summary: str
    patch_body: str
    topic_ids: list[str] = field(default_factory=list)
    supporting_records: list[str] = field(default_factory=list)
    applicability: list[str] = field(default_factory=list)
    preconditions: list[str] = field(default_factory=list)
    validation_refs: list[str] = field(default_factory=list)
    execution_refs: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    installation_target: str = "project"
    review_checkpoint_id: str = ""
    approved_content_hash: str = ""
    trust_level: str = "open"
    review_status: str = "draft"
    application_status: str = "not_applied"
    requires_human_review: bool = True
    can_update_claim_trust: bool = False
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    kind: str = "skill_patch_proposal"

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
class SourceAssetRecord:
    asset_id: str
    topic_id: str
    asset_type: str
    uri: str
    title: str
    claim_id: str = ""
    label: str = ""
    content_hash: str = ""
    hash_algorithm: str = ""
    version_anchor: dict = field(default_factory=dict)
    acquired_at: str = ""
    source_kind: str = "manual"
    summary: str = ""
    source_refs: list[str] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)
    code_state_ids: list[str] = field(default_factory=list)
    reference_location_ids: list[str] = field(default_factory=list)
    derived_from: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    linked_records: dict = field(default_factory=dict)
    orientation_only: bool = True
    can_update_claim_trust: bool = False
    kind: str = "source_asset"

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
    lifecycle_status: str = "active"
    rehome_event_id: str = ""
    rehome_target_topic: str = ""
    replaced_by: str = ""
    kind: str = "evidence"

@dataclass
class LifecycleEventRecord:
    event_id: str
    event_type: str          # "rehome" | "supersede"
    subject_record_id: str
    subject_kind: str        # "claim" | "evidence" | "tool_run" | "session"
    lifecycle_status: str    # records use active/misrouted/voided/superseded/duplicate; events may use "rehomed"
    reason: str
    operator: str
    timestamp: str
    from_topic: str = ""
    to_topic: str = ""
    replacement_ref: str = ""
    supersedes_event: str = ""
    kind: str = "lifecycle_event"

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
