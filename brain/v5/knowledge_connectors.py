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

    truth_policy = {
        "retrieved_notes_are_truth_source": False,
        "source_backed_evidence_required": True,
        "capture_is_process_memory": True,
        "summary_inputs_trusted": False,
    }
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
                "reference_location_records",
                "evidence_records",
                "claim_updates_when_trust_changes",
            ),
            truth_policy=dict(truth_policy),
            recommended_when="before_theory_literature_discussion",
        ),
        "qft_literature": KnowledgeConnectorRecord(
            connector_id="qft_literature",
            connector_kind="literature_and_notes_corpus",
            display_name="QFT Literature Notes",
            purpose="Quantum field theory paper and note retrieval for concepts, notation, derivation routes, and source reconstruction.",
            skill_ref="qft-literature-skill",
            backend_role="domain_literature_connector",
            is_required=False,
            supported_activities=(
                "literature_learning",
                "notation_lookup",
                "derivation_scaffolding",
                "source_reconstruction",
            ),
            expected_retrieval_targets=(
                "local_pdf_assets",
                "paper_section_notes",
                "equation_anchors",
                "notation_convention_notes",
                "prior_derivation_attempts",
            ),
            location_ref_targets=(
                "pdf_page",
                "paper_section",
                "equation_label",
                "local_note_uri",
            ),
            protocol_hooks=(
                "retrieve_before_derivation_check",
                "record_exact_reference_locations",
                "create_physics_objects_for_notation",
                "promote_only_after_source_reconstruction",
            ),
            required_kernel_followup_records=(
                "source_asset",
                "reference_location_records",
                "physics_object_records",
                "object_relation_records",
                "evidence_records",
                "proof_obligation_records",
            ),
            truth_policy=dict(truth_policy),
            recommended_when="for_qft_literature_learning_or_derivation_checks",
        ),
        "quantum_gravity_literature": KnowledgeConnectorRecord(
            connector_id="quantum_gravity_literature",
            connector_kind="literature_and_notes_corpus",
            display_name="Quantum Gravity Literature Notes",
            purpose="Quantum gravity, holography, de Sitter, black-hole, and wormhole literature retrieval for source-backed theory learning.",
            skill_ref="quantum-gravity-literature-skill",
            backend_role="domain_literature_connector",
            is_required=False,
            supported_activities=(
                "literature_learning",
                "cross_paper_comparison",
                "source_reconstruction",
                "concept_dependency_mapping",
            ),
            expected_retrieval_targets=(
                "local_pdf_assets",
                "paper_pair_reading_notes",
                "concept_dependency_notes",
                "claim_scope_notes",
                "open_gap_notes",
            ),
            location_ref_targets=(
                "pdf_page",
                "paper_section",
                "figure_or_equation_anchor",
                "local_note_uri",
            ),
            protocol_hooks=(
                "retrieve_before_cross_paper_synthesis",
                "record_source_backtrace",
                "separate_speculation_from_evidence",
                "request_human_checkpoint_before_promotion",
            ),
            required_kernel_followup_records=(
                "source_asset",
                "reference_location_records",
                "physics_object_records",
                "object_relation_records",
                "evidence_records",
                "proof_obligation_records",
                "human_checkpoint_records",
            ),
            truth_policy=dict(truth_policy),
            recommended_when="for_quantum_gravity_or_holography_literature_learning",
        ),
        "librpa_research_notes": KnowledgeConnectorRecord(
            connector_id="librpa_research_notes",
            connector_kind="method_notes_and_run_corpus",
            display_name="LibRPA Research Notes",
            purpose="LibRPA/GW notes, run reports, rule cards, and prior failure routes for first-principles method work.",
            skill_ref="oh-my-librpa",
            backend_role="domain_experience_connector",
            is_required=False,
            supported_activities=(
                "run_continuation",
                "debug_route_lookup",
                "workflow_reproduction",
                "benchmark_provenance_review",
            ),
            expected_retrieval_targets=(
                "run_reports",
                "lane_manifests",
                "input_bundle_notes",
                "failure_mode_cards",
                "benchmark_notes",
            ),
            location_ref_targets=(
                "local_report_uri",
                "artifact_path",
                "rule_card_path",
                "run_directory_uri",
            ),
            protocol_hooks=(
                "retrieve_before_hpc_run_interpretation",
                "record_artifact_and_tool_run_refs",
                "keep_diagnostic_lane_separate",
                "promote_only_after_validation_result",
            ),
            required_kernel_followup_records=(
                "code_state",
                "tool_run",
                "artifact",
                "reference_location_records",
                "evidence_records",
                "validation_result_records",
            ),
            truth_policy=dict(truth_policy),
            recommended_when="for_librpa_gw_run_continuation_or_method_debugging",
        ),
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

    connectors = builtin_knowledge_connectors()
    text = _claim_text(claim)
    selected: list[str] = []
    if any(term in text for term in ("qft", "quantum field", "field theory", "renormalization", "path integral")):
        selected.append("qft_literature")
    if any(term in text for term in ("quantum gravity", "holograph", "ads", "de sitter", "black hole", "wormhole")):
        selected.append("quantum_gravity_literature")
    if any(term in text for term in ("librpa", "qsgw", "g0w0", "abacus", "pyatb")):
        selected.append("librpa_research_notes")
    if not selected and _needs_theory_literature_memory(claim):
        selected.append("ima")
    return [_connector_payload(connectors[connector_id]) for connector_id in _dedupe(selected)]


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
    text = _claim_text(claim)
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


def _claim_text(claim: ClaimRecord) -> str:
    return " ".join(
        [
            claim.topic_id,
            claim.statement,
            claim.evidence_profile,
            claim.active_uncertainty,
            claim.scope,
            claim.strongest_failure_mode,
        ]
    ).lower()


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
