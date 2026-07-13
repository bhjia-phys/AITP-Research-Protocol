"""Trust-neutral canonical records for the M1 research-session lifecycle."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionFocusSetRecord:
    focus_set_id: str
    session_id: str
    primary_topic_id: str
    focus_kind: str
    focus_ref: str
    supporting_refs: list[str] = field(default_factory=list)
    excluded_refs: list[str] = field(default_factory=list)
    objective_refs: list[str] = field(default_factory=list)
    program_id: str = ""
    scope_status: str = "active"
    source_refs: list[str] = field(default_factory=list)
    created_at: str = ""
    claim_trust_transfer: str = "forbidden"
    can_update_active_claim: bool = False
    can_update_claim_trust: bool = False
    kind: str = "session_focus_set"

    def __post_init__(self) -> None:
        _require_forbidden(self.claim_trust_transfer, "claim_trust_transfer")
        _require_false(self.can_update_active_claim, "can_update_active_claim")
        _require_false(self.can_update_claim_trust, "can_update_claim_trust")


@dataclass
class ResearchProgramRecord:
    program_id: str
    title: str
    primary_topic_ids: list[str]
    supporting_topic_ids: list[str] = field(default_factory=list)
    scientific_boundary: str = ""
    inclusion_rules: list[str] = field(default_factory=list)
    exclusion_rules: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    review_status: str = "pending_review"
    checkpoint_id: str = ""
    created_at: str = ""
    claim_trust_transfer: str = "forbidden"
    can_update_claim_trust: bool = False
    kind: str = "research_program"

    def __post_init__(self) -> None:
        _require_forbidden(self.claim_trust_transfer, "claim_trust_transfer")
        _require_false(self.can_update_claim_trust, "can_update_claim_trust")


@dataclass
class CrossTopicRelationRecord:
    relation_id: str
    source_topic_id: str
    target_topic_id: str
    source_ref: str
    target_ref: str
    relation_kind: str
    transfer_rationale: str
    applicability_boundary: str
    revalidation_requirements: list[str]
    source_refs: list[str] = field(default_factory=list)
    status: str = "pending_review"
    checkpoint_id: str = ""
    created_at: str = ""
    claim_trust_transfer: str = "forbidden"
    can_update_claim_trust: bool = False
    kind: str = "cross_topic_relation"

    def __post_init__(self) -> None:
        _require_forbidden(self.claim_trust_transfer, "claim_trust_transfer")
        _require_false(self.can_update_claim_trust, "can_update_claim_trust")


@dataclass
class CloseoutBoundaryItem:
    text: str
    boundary_class: str
    source_refs: list[str]
    scope: str = ""
    conditions: list[str] = field(default_factory=list)
    requires_exact_expansion: bool = True
    can_update_claim_trust: bool = False

    def __post_init__(self) -> None:
        _require_false(self.can_update_claim_trust, "can_update_claim_trust")


@dataclass
class SessionCloseoutRecord:
    closeout_id: str
    session_id: str
    topic_id: str
    milestone_id: str
    focus_set_ref: str = ""
    objective_refs: list[str] = field(default_factory=list)
    completed_work: list[str] = field(default_factory=list)
    can_say: list[CloseoutBoundaryItem] = field(default_factory=list)
    cannot_say: list[CloseoutBoundaryItem] = field(default_factory=list)
    open_gaps: list[CloseoutBoundaryItem] = field(default_factory=list)
    failed_routes: list[CloseoutBoundaryItem] = field(default_factory=list)
    unverified_notes: list[CloseoutBoundaryItem] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    source_record_refs: list[str] = field(default_factory=list)
    pending_candidate_batch_refs: list[str] = field(default_factory=list)
    reusable_workflow_candidate_refs: list[str] = field(default_factory=list)
    index_generation: int = 0
    base_index_generation: int = 0
    delta_generation: int = 0
    canonical_watermark: str = ""
    retrieval_scope_token: str = ""
    family_state_tokens: dict[str, str] = field(default_factory=dict)
    family_content_watermarks: dict[str, str] = field(default_factory=dict)
    dirty_families: list[str] = field(default_factory=list)
    checked_families: list[str] = field(default_factory=list)
    read_errors: list[str] = field(default_factory=list)
    coverage_content_verified: bool = False
    coverage_exhaustive: bool = False
    operator: str = ""
    created_at: str = ""
    can_update_claim_trust: bool = False
    kind: str = "session_closeout"

    def __post_init__(self) -> None:
        _require_false(self.can_update_claim_trust, "can_update_claim_trust")
        for field_name in (
            "can_say",
            "cannot_say",
            "open_gaps",
            "failed_routes",
            "unverified_notes",
        ):
            setattr(
                self,
                field_name,
                _boundary_items(getattr(self, field_name), field_name=field_name),
            )


@dataclass
class RecallAuditRecord:
    audit_id: str
    session_id: str
    topic_id: str
    query_text: str
    normalized_intent: str
    scope_refs: list[str]
    lanes: list[dict[str, Any]] = field(default_factory=list)
    index_generation: int = 0
    base_index_generation: int = 0
    delta_generation: int = 0
    canonical_watermark: str = ""
    retrieval_scope_token: str = ""
    family_state_tokens: dict[str, str] = field(default_factory=dict)
    family_content_watermarks: dict[str, str] = field(default_factory=dict)
    dirty_families: list[str] = field(default_factory=list)
    checked_families: list[str] = field(default_factory=list)
    unchecked_families: list[str] = field(default_factory=list)
    records_read: int = 0
    top_refs: list[str] = field(default_factory=list)
    excluded_candidates: list[str] = field(default_factory=list)
    read_errors: list[str] = field(default_factory=list)
    truncated: bool = False
    stale: bool = False
    content_verified: bool = False
    exhaustive: bool = False
    can_claim_no_result: bool = False
    created_at: str = ""
    can_update_claim_trust: bool = False
    kind: str = "recall_audit"

    def __post_init__(self) -> None:
        _require_false(self.can_update_claim_trust, "can_update_claim_trust")


@dataclass
class RecordingCandidateBatchRecord:
    batch_id: str
    session_id: str
    topic_id: str
    milestone_id: str
    candidates: list[dict[str, Any]]
    dedup_keys: list[str]
    source_event_refs: list[str] = field(default_factory=list)
    missing_prerequisites: list[str] = field(default_factory=list)
    status: str = "pending_review"
    expires_at: str = ""
    supersedes: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    created_at: str = ""
    can_update_claim_trust: bool = False
    kind: str = "recording_candidate_batch"

    def __post_init__(self) -> None:
        _require_false(self.can_update_claim_trust, "can_update_claim_trust")


def _boundary_items(value: object, *, field_name: str) -> list[CloseoutBoundaryItem]:
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be a list")
    items: list[CloseoutBoundaryItem] = []
    for item in value:
        if isinstance(item, CloseoutBoundaryItem):
            items.append(item)
        elif isinstance(item, Mapping):
            items.append(CloseoutBoundaryItem(**dict(item)))
        else:
            raise TypeError(f"{field_name} items must be CloseoutBoundaryItem mappings")
    return items


def _require_forbidden(value: object, field_name: str) -> None:
    if value != "forbidden":
        raise ValueError(f"{field_name} must be forbidden")


def _require_false(value: object, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must be false")
