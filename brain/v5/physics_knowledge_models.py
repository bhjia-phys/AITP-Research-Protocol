"""Compatibility-defaulted records for grounded physics knowledge and insight."""

from __future__ import annotations

from dataclasses import dataclass, field


INSIGHT_KINDS = frozenset(
    {
        "interpretation",
        "analogy",
        "conjecture",
        "failed_route_lesson",
        "counterexample_direction",
        "conceptual_bridge",
        "open_research_direction",
    }
)


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
    scope_kind: str = "topic"
    scope_ref: str = ""
    knowledge_role: str = "identity"
    canonical_name: str = ""
    aliases: list[str] = field(default_factory=list)
    review_status: str = "legacy_unreviewed"
    lifecycle_status: str = "active"
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
    subject_ref: str = ""
    object_ref: str = ""
    direction: str = "directed"
    conditions: list[str] = field(default_factory=list)
    framework: str = ""
    regime: str = ""
    conventions: list[str] = field(default_factory=list)
    contradiction_refs: list[str] = field(default_factory=list)
    review_status: str = "legacy_unreviewed"
    lifecycle_status: str = "active"
    claim_trust_transfer: str = "forbidden"
    kind: str = "object_relation"

    def __post_init__(self) -> None:
        if self.claim_trust_transfer != "forbidden":
            raise ValueError("object relations forbid claim trust transfer")


@dataclass
class PhysicsAssertionRecord:
    assertion_id: str
    object_ref: str
    topic_id: str
    predicate: str
    value: str
    expression: str = ""
    program_id: str = ""
    claim_id: str = ""
    framework: str = ""
    regime: str = ""
    conventions: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    non_claims: list[str] = field(default_factory=list)
    source_asset_refs: list[str] = field(default_factory=list)
    source_location_refs: list[str] = field(default_factory=list)
    contradiction_refs: list[str] = field(default_factory=list)
    supersedes_assertion_ref: str = ""
    review_decision_ref: dict = field(default_factory=dict)
    review_status: str = "unreviewed"
    lifecycle_status: str = "active"
    can_update_claim_trust: bool = False
    kind: str = "physics_assertion"

    def __post_init__(self) -> None:
        if self.can_update_claim_trust:
            raise ValueError("physics assertions cannot update claim trust")


@dataclass
class InsightRecord:
    insight_id: str
    insight_kind: str
    statement: str
    topic_id: str
    program_id: str = ""
    grounding_refs: list[str] = field(default_factory=list)
    inferred_from_refs: list[str] = field(default_factory=list)
    framework: str = ""
    regime: str = ""
    speculation_level: str = "exploratory"
    counterevidence_refs: list[str] = field(default_factory=list)
    falsifiers: list[str] = field(default_factory=list)
    proof_obligation_refs: list[str] = field(default_factory=list)
    review_status: str = "unreviewed"
    checkpoint_id: str = ""
    review_decision_ref: dict = field(default_factory=dict)
    lifecycle_status: str = "active"
    source_refs: list[str] = field(default_factory=list)
    created_at: str = ""
    evidence_role: str = "forbidden"
    can_update_claim_trust: bool = False
    kind: str = "insight"

    def __post_init__(self) -> None:
        if self.insight_kind not in INSIGHT_KINDS:
            raise ValueError("insight_kind is not an allowed speculative insight kind")
        if self.evidence_role != "forbidden" or self.can_update_claim_trust:
            raise ValueError("insight is non-evidence and cannot update claim trust")


@dataclass
class KnowledgeReviewDecisionRecord:
    decision_id: str
    candidate_id: str
    candidate_hash: str
    candidate_lane: str
    topic_id: str
    decision: str
    rationale: str
    reviewer: str
    checkpoint_ref: dict
    candidate_payload: dict = field(default_factory=dict)
    source_refs: list[dict] = field(default_factory=list)
    lifecycle_status: str = "active"
    supersedes_decision_ref: dict = field(default_factory=dict)
    can_update_claim_trust: bool = False
    kind: str = "knowledge_review_decision"

    def __post_init__(self) -> None:
        if self.decision not in {"approve", "reject", "revise"}:
            raise ValueError("knowledge review decision must be approve, reject, or revise")
        if self.can_update_claim_trust:
            raise ValueError("knowledge review decisions cannot update claim trust")
