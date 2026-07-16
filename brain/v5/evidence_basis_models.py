"""Compatibility-defaulted EvidenceRecord with basis-policy provenance."""

from __future__ import annotations

from dataclasses import dataclass, field


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
    support_basis_refs: list[dict] = field(default_factory=list)
    trace_context_refs: list[dict] = field(default_factory=list)
    basis_audit: dict = field(default_factory=dict)
    basis_policy_status: str = "legacy_unchecked"
    basis_payload_hash: str = ""
    basis_policy_version: str = ""
    can_update_claim_trust: bool = False
    kind: str = "evidence"

    def __post_init__(self) -> None:
        if self.can_update_claim_trust:
            raise ValueError("evidence records cannot directly update claim trust")
