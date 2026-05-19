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
    kind: str = "trust_update_request"


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
