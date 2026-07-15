"""Compatibility-safe v2 lifecycle records and knowledge projections."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LifecycleEventRecord:
    event_id: str
    event_type: str
    subject_record_id: str
    subject_kind: str
    lifecycle_status: str
    reason: str
    operator: str
    timestamp: str
    from_topic: str = ""
    to_topic: str = ""
    replacement_ref: str = ""
    supersedes_event: str = ""
    subject_ref: dict = field(default_factory=dict)
    replacement_ref_pin: dict = field(default_factory=dict)
    lifecycle_action: str = ""
    supersedes_event_ref: dict = field(default_factory=dict)
    effect_policy: str = "record_visibility_only"
    can_update_claim_trust: bool = False
    kind: str = "lifecycle_event"

    def __post_init__(self) -> None:
        if self.can_update_claim_trust:
            raise ValueError("lifecycle events cannot update claim trust")


@dataclass(frozen=True)
class KnowledgeLifecycleProjection:
    subject_ref: str
    subject_content_hash: str
    effective_status: str
    active: bool
    active_event_ref: str = ""
    replacement_ref: str = ""
    replacement_content_hash: str = ""
    blocking_reasons: tuple[str, ...] = ()
    can_update_claim_trust: bool = False
