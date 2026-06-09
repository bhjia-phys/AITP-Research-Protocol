"""Read-only literature comparison draft packet for host runtimes."""

from __future__ import annotations

from typing import Any

from brain.v5.record_refs import lookup_record_refs
from brain.v5.workspace import get_session_binding


_DEFAULT_DIMENSIONS = (
    "research_question",
    "studied_object",
    "method_assumptions",
    "evidence_basis",
    "conclusion_scope",
    "limitations",
    "open_directions",
)


def build_literature_comparison_draft(
    ws,
    *,
    session_id: str,
    comparison_question: str,
    source_refs: list[str],
    dimensions: list[str] | None = None,
    optional_claim_id: str = "",
    rationale: str = "",
) -> dict[str, Any]:
    """Draft a literature comparison packet without writing comparison records."""

    session = get_session_binding(ws, session_id)
    claim_id = optional_claim_id or session.active_claim
    normalized_refs = _nonempty_unique(source_refs)
    normalized_dimensions = _nonempty_unique(dimensions or list(_DEFAULT_DIMENSIONS))
    ref_lookup = lookup_record_refs(ws, normalized_refs)
    return {
        "ok": True,
        "kind": "literature_comparison_draft",
        "session_id": session_id,
        "topic_id": session.topic_id,
        "claim_id": claim_id,
        "comparison_question": comparison_question,
        "rationale": rationale,
        "source_refs": normalized_refs,
        "source_ref_count": len(normalized_refs),
        "comparison_dimensions": _dimension_payloads(normalized_dimensions),
        "comparison_dimension_count": len(normalized_dimensions),
        "record_ref_lookup": ref_lookup,
        "draft_record_intent": {
            "kind": "literature_comparison_record_candidate",
            "target_surface": "future_literature_comparison_record",
            "target_entrypoint": "record_literature_comparison",
            "status": "draft_only",
            "requires_explicit_write_surface": True,
            "requires_source_review": True,
            "requires_evidence_or_reference_records": True,
            "requires_trust_preflight_before_claim_trust": True,
            "creates_record_now": False,
            "records_validation_result": False,
            "source_support_result": False,
            "claim_trust_mutation": "none",
            "can_update_claim_trust": False,
        },
        "suggested_sections": [
            {"section": "agreements", "description": "claim-aligned similarities to check against sources"},
            {"section": "disagreements", "description": "scope, method, or conclusion conflicts to inspect"},
            {"section": "missing_evidence", "description": "outputs, references, or validation still absent"},
            {"section": "open_directions", "description": "research routes or proof obligations suggested by comparison"},
        ],
        "recommended_next_entrypoints": [
            {
                "entrypoint": "record_reference_location",
                "surface": "reference_location_record",
                "reason": "ensure every compared source has a canonical reference location",
            },
            {
                "entrypoint": "record_source_reconstruction_review_result",
                "surface": "source_reconstruction_review_result_record",
                "reason": "review reconstruction status before using comparison in trust-sensitive work",
            },
            {
                "entrypoint": "record_evidence",
                "surface": "evidence_record",
                "reason": "only after source review, record evidence for scoped outputs if warranted",
            },
            {
                "entrypoint": "create_validation_contract",
                "surface": "validation_contract_record",
                "reason": "turn comparison-derived checks into explicit validation requirements when needed",
            },
            {
                "entrypoint": "preflight_trust_update",
                "surface": "trust_update_preflight",
                "reason": "trust changes require explicit AITP preflight and checkpoints",
            },
        ],
        "draft_policy": {
            "source": "session_binding_agent_supplied_sources_and_dimensions",
            "host_may_use_for": [
                "literature_comparison_planning",
                "source_set_review",
                "dimension_selection",
                "agreement_disagreement_scaffolding",
                "open_direction_selection",
            ],
            "requires_explicit_next_entrypoint": True,
            "allowed_next_entrypoints": [
                "record_reference_location",
                "register_source_asset",
                "record_source_reconstruction_review_result",
                "record_evidence",
                "create_validation_contract",
                "record_validation_result",
                "preflight_trust_update",
            ],
            "forbidden_uses": [
                "literature_comparison_record",
                "evidence_support",
                "source_support_result",
                "validation_result",
                "write_execution",
                "final_gate_satisfaction",
                "claim_trust_update",
                "trust_apply",
            ],
        },
        "allowed_next_tool_call": {
            "action": "plan_primitive_tools",
            "action_id": "source.compare_literature",
            "requires_explicit_next_action": True,
            "records_validation_result": False,
            "source_support_result": False,
            "claim_trust_mutation": "none",
        },
        "read_surface_effect": "comparison_draft_only",
        "read_only": True,
        "draft_creates_records": False,
        "requires_explicit_next_action": True,
        "bridge_called": False,
        "executes_write_now": False,
        "mutates_next_payload_now": False,
        "infers_payload_values": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "records_validation_result": False,
        "source_support_result": False,
        "evidence_created": False,
        "validation_created": False,
        "write_executed": False,
        "trust_update_forbidden": True,
        "claim_trust_mutation": "none",
        "truth_source": "session_binding_agent_supplied_sources_and_dimensions",
    }


def _dimension_payloads(dimensions: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "dimension": dimension,
            "status": "draft_placeholder",
            "requires_source_review": True,
            "summary_inputs_trusted": False,
            "creates_record_now": False,
            "records_validation_result": False,
            "source_support_result": False,
            "claim_trust_mutation": "none",
        }
        for dimension in dimensions
    ]


def _nonempty_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result
