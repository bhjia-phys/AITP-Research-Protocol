"""Canonical trust-neutral records for inspectable formal derivations."""

from __future__ import annotations

from dataclasses import dataclass, field


_CHAIN_STATUSES = {"draft", "in_progress", "blocked", "structurally_closed"}
_STEP_STATUSES = {"draft", "established", "blocked"}
_REVIEW_DECISIONS = {"passed", "needs_revision", "inconclusive", "rejected"}


@dataclass
class DerivationChainRecord:
    chain_id: str
    topic_id: str
    claim_id: str
    title: str
    target: str
    assumptions: list[str]
    conventions: list[str]
    framework: str
    regime: str
    ordered_step_refs: list[dict] = field(default_factory=list)
    imported_chain_bindings: list[dict] = field(default_factory=list)
    open_gaps: list[str] = field(default_factory=list)
    check_refs: list[dict] = field(default_factory=list)
    source_refs: list[dict] = field(default_factory=list)
    status: str = "draft"
    program_id: str = ""
    migration_provenance: dict = field(default_factory=dict)
    can_update_claim_trust: bool = False
    kind: str = "derivation_chain"

    def __post_init__(self) -> None:
        _require_nonempty(self.chain_id, "chain_id")
        _require_scope(self.topic_id, self.claim_id)
        for value, name in (
            (self.title, "title"),
            (self.target, "target"),
            (self.framework, "framework"),
            (self.regime, "regime"),
        ):
            _require_nonempty(value, name)
        if not self.assumptions or not self.conventions:
            raise ValueError("derivation chain requires assumptions and conventions")
        if self.status not in _CHAIN_STATUSES:
            raise ValueError(f"unsupported derivation chain status: {self.status}")
        _require_false(self.can_update_claim_trust)


@dataclass
class DerivationStepRecord:
    step_id: str
    chain_id: str
    topic_id: str
    claim_id: str
    sequence: int
    input_expression: str
    output_expression: str
    justification_type: str
    dependency_step_refs: list[dict] = field(default_factory=list)
    invoked_knowledge_refs: list[dict] = field(default_factory=list)
    source_anchor_refs: list[dict] = field(default_factory=list)
    local_check_refs: list[dict] = field(default_factory=list)
    unresolved_conditions: list[str] = field(default_factory=list)
    status: str = "draft"
    program_id: str = ""
    migration_provenance: dict = field(default_factory=dict)
    can_update_claim_trust: bool = False
    kind: str = "derivation_step"

    def __post_init__(self) -> None:
        _require_nonempty(self.step_id, "step_id")
        _require_nonempty(self.chain_id, "chain_id")
        _require_scope(self.topic_id, self.claim_id)
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence < 1:
            raise ValueError("derivation step sequence must be a positive integer")
        for value, name in (
            (self.input_expression, "input_expression"),
            (self.output_expression, "output_expression"),
            (self.justification_type, "justification_type"),
        ):
            _require_nonempty(value, name)
        if self.status not in _STEP_STATUSES:
            raise ValueError(f"unsupported derivation step status: {self.status}")
        _require_false(self.can_update_claim_trust)


@dataclass
class DerivationReviewRecord:
    review_id: str
    topic_id: str
    claim_id: str
    chain_ref: dict
    step_refs: list[dict]
    source_anchor_refs: list[dict]
    validation_check_refs: list[dict]
    tool_run_check_refs: list[dict]
    checkpoint_ref: dict
    reviewer_role: str
    decision: str
    reviewed_scope: list[str]
    summary: str
    program_id: str = ""
    supersedes_review_ref: dict = field(default_factory=dict)
    created_at: str = ""
    can_update_claim_trust: bool = False
    kind: str = "derivation_review"

    def __post_init__(self) -> None:
        _require_nonempty(self.review_id, "review_id")
        _require_scope(self.topic_id, self.claim_id)
        _require_nonempty(self.reviewer_role, "reviewer_role")
        _require_nonempty(self.summary, "summary")
        if self.decision not in _REVIEW_DECISIONS:
            raise ValueError(f"unsupported derivation review decision: {self.decision}")
        if not self.reviewed_scope:
            raise ValueError("derivation review requires explicit reviewed_scope")
        _require_false(self.can_update_claim_trust)


def _require_scope(topic_id: str, claim_id: str) -> None:
    _require_nonempty(topic_id, "topic_id")
    _require_nonempty(claim_id, "claim_id")


def _require_nonempty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"derivation {field_name} must be non-empty")


def _require_false(value: bool) -> None:
    if value is not False:
        raise ValueError("derivation records cannot update claim trust")
