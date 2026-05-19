"""Knowledge connector declarations for theory learning and literature work."""

from __future__ import annotations

from dataclasses import dataclass, field

from brain.v5.models import ClaimRecord


@dataclass(frozen=True)
class KnowledgeConnectorRecord:
    connector_id: str
    connector_kind: str
    display_name: str
    purpose: str
    skill_ref: str
    backend_role: str = "external_backend"
    is_required: bool = False
    supported_activities: tuple[str, ...] = ()
    expected_retrieval_targets: tuple[str, ...] = ()
    location_ref_targets: tuple[str, ...] = ()
    protocol_hooks: tuple[str, ...] = ()
    required_kernel_followup_records: tuple[str, ...] = ()
    truth_policy: dict = field(default_factory=dict)
    recommended_when: str = ""
    kind: str = "knowledge_connector"


def builtin_knowledge_connectors() -> dict[str, KnowledgeConnectorRecord]:
    """Return built-in knowledge connectors available to the AITP harness."""

    return {
        "ima": KnowledgeConnectorRecord(
            connector_id="ima",
            connector_kind="notes_and_knowledge_base",
            display_name="IMA",
            purpose="Example backend for placing/searching literature and recording external note locations.",
            skill_ref="ima-skill",
            backend_role="example_external_backend",
            is_required=False,
            supported_activities=(
                "literature_learning",
                "theory_discussion",
                "source_note_lookup",
                "knowledge_capture",
            ),
            expected_retrieval_targets=(
                "existing_notes",
                "knowledge_base_items",
                "prior_reading_summaries",
                "source_backed_claim_context",
            ),
            location_ref_targets=(
                "external_note_uri",
                "external_paper_uri",
                "knowledge_base_item_uri",
            ),
            protocol_hooks=(
                "retrieve_before_answering",
                "cite_retrieved_context_as_orientation",
                "record_source_backed_evidence_in_kernel",
                "capture_nontrivial_learning",
            ),
            required_kernel_followup_records=(
                "source_refs",
                "note_location_refs",
                "evidence_records",
                "claim_updates_when_trust_changes",
            ),
            truth_policy={
                "retrieved_notes_are_truth_source": False,
                "source_backed_evidence_required": True,
                "capture_is_process_memory": True,
                "summary_inputs_trusted": False,
            },
            recommended_when="before_theory_literature_discussion",
        )
    }


def describe_knowledge_connectors() -> dict:
    """Describe safe knowledge connectors without reading generated summaries."""

    connectors = [_connector_payload(connector) for connector in builtin_knowledge_connectors().values()]
    return {
        "ok": True,
        "kind": "knowledge_connector_catalog",
        "truth_source": "builtin_connector_registry",
        "summary_inputs_trusted": False,
        "connector_count": len(connectors),
        "connectors": connectors,
    }


def suggest_knowledge_connectors_for_claim(claim: ClaimRecord) -> list[dict]:
    """Suggest knowledge connectors for theory/literature-heavy work."""

    if not _needs_theory_literature_memory(claim):
        return []
    return [_connector_payload(builtin_knowledge_connectors()["ima"])]


def _connector_payload(connector: KnowledgeConnectorRecord) -> dict:
    return {
        "kind": connector.kind,
        "connector_id": connector.connector_id,
        "connector_kind": connector.connector_kind,
        "display_name": connector.display_name,
        "purpose": connector.purpose,
        "skill_ref": connector.skill_ref,
        "backend_role": connector.backend_role,
        "is_required": connector.is_required,
        "supported_activities": list(connector.supported_activities),
        "expected_retrieval_targets": list(connector.expected_retrieval_targets),
        "location_ref_targets": list(connector.location_ref_targets),
        "protocol_hooks": list(connector.protocol_hooks),
        "required_kernel_followup_records": list(connector.required_kernel_followup_records),
        "truth_policy": dict(connector.truth_policy),
        "recommended_when": connector.recommended_when,
    }


def _needs_theory_literature_memory(claim: ClaimRecord) -> bool:
    text = " ".join(
        [
            claim.topic_id,
            claim.statement,
            claim.evidence_profile,
            claim.active_uncertainty,
            claim.scope,
            claim.strongest_failure_mode,
        ]
    ).lower()
    if claim.evidence_profile == "literature_synthesis":
        return True
    return any(
        term in text
        for term in (
            "literature",
            "paper",
            "arxiv",
            "reading",
            "learn",
            "notes",
            "source",
            "review",
            "文献",
            "笔记",
            "学习",
            "综述",
        )
    )
