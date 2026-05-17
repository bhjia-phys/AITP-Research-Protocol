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
