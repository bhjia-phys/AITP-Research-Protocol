"""Read-only paper-learning route compiler for literature work."""

from __future__ import annotations

from typing import Any

from brain.v5.record_refs import lookup_record_refs
from brain.v5.workspace import get_session_binding


_DEFAULT_FOCUS_SECTIONS = (
    "source_identity",
    "exact_locations",
    "core_definitions",
    "notation_conventions",
    "equation_anchors",
    "claim_scope",
    "caveats",
    "open_gaps",
    "not_supported",
)
_DEFAULT_COMPARISON_DIMENSIONS = (
    "research_question",
    "objects_and_definitions",
    "notation_and_conventions",
    "method_assumptions",
    "evidence_basis",
    "scope_and_limitations",
    "open_gaps",
)


def build_literature_reading_route(
    ws,
    *,
    session_id: str,
    reading_question: str,
    source_refs: list[str],
    route_type: str = "auto",
    focus_terms: list[str] | None = None,
    optional_claim_id: str = "",
    rationale: str = "",
) -> dict[str, Any]:
    """Compile a source-grounded reading route without reading or writing records."""

    session = get_session_binding(ws, session_id)
    claim_id = optional_claim_id or session.active_claim
    normalized_refs = _nonempty_unique(source_refs)
    if not normalized_refs:
        raise ValueError("source_refs is required")
    normalized_focus_terms = _nonempty_unique(focus_terms or [])
    selected_route_type = _route_type(route_type, normalized_refs)
    profile_id = _profile_id(selected_route_type)
    ref_lookup = lookup_record_refs(ws, normalized_refs)
    source_requirements = [_source_requirement(ref) for ref in normalized_refs]
    route_steps = _route_steps(selected_route_type, normalized_refs)
    extraction_templates = _extraction_templates(
        selected_route_type,
        profile_id=profile_id,
        source_refs=normalized_refs,
    )
    return {
        "ok": True,
        "kind": "literature_reading_route",
        "session_id": session_id,
        "topic_id": session.topic_id,
        "claim_id": claim_id,
        "reading_question": reading_question,
        "rationale": rationale,
        "route_type": selected_route_type,
        "context_profile_id": profile_id,
        "source_refs": normalized_refs,
        "source_ref_count": len(normalized_refs),
        "focus_terms": normalized_focus_terms,
        "focus_term_count": len(normalized_focus_terms),
        "source_requirements": source_requirements,
        "source_requirement_count": len(source_requirements),
        "route_steps": route_steps,
        "route_step_count": len(route_steps),
        "comparison_dimensions": _comparison_dimensions(selected_route_type),
        "extraction_report_templates": extraction_templates,
        "extraction_report_template_count": len(extraction_templates),
        "record_ref_lookup": ref_lookup,
        "recommended_next_entrypoints": _recommended_next_entrypoints(selected_route_type),
        "route_policy": {
            "source": "session_binding_agent_supplied_sources_and_reading_question",
            "host_may_use_for": [
                "paper_learning_route_selection",
                "exact_source_anchor_planning",
                "source_extraction_report_planning",
                "paired_or_multi_paper_comparison_planning",
                "source_reconstruction_before_synthesis",
            ],
            "requires_exact_reference_locations_before_synthesis": True,
            "requires_explicit_next_entrypoint": True,
            "allowed_next_entrypoints": [
                "register_source_asset",
                "record_reference_location",
                "build_literature_source_extraction_candidates",
                "build_literature_comparison_draft",
                "build_literature_source_review_handoff",
                "record_sensemaking_report",
                "create_validation_contract",
                "preflight_trust_update",
            ],
            "forbidden_uses": [
                "paper_summary_as_evidence",
                "literature_synthesis_record",
                "evidence_support",
                "source_support_result",
                "validation_result",
                "write_execution",
                "final_gate_satisfaction",
                "claim_trust_update",
                "trust_apply",
            ],
        },
        "allowed_next_tool_calls": [
            _allowed_tool_call("source.extract_candidates"),
            _allowed_tool_call("source.review_context"),
            _allowed_tool_call("source.compare_literature"),
        ],
        "read_surface_effect": "literature_reading_route_only",
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
        "truth_source": "session_binding_agent_supplied_sources_and_reading_question",
    }


def _route_type(route_type: str, source_refs: list[str]) -> str:
    normalized = str(route_type or "auto").lower().replace("-", "_")
    aliases = {
        "single": "single_paper",
        "single_paper": "single_paper",
        "paper": "single_paper",
        "paired": "paired_paper",
        "paired_paper": "paired_paper",
        "two_paper": "paired_paper",
        "multi": "multi_paper",
        "multi_paper": "multi_paper",
        "many_paper": "multi_paper",
    }
    if normalized in aliases:
        return aliases[normalized]
    if len(source_refs) == 1:
        return "single_paper"
    if len(source_refs) == 2:
        return "paired_paper"
    return "multi_paper"


def _profile_id(route_type: str) -> str:
    return {
        "single_paper": "paper_learning",
        "paired_paper": "paired_paper_learning",
        "multi_paper": "multi_paper_learning_route",
    }[route_type]


def _source_requirement(source_ref: str) -> dict[str, Any]:
    return {
        "source_ref": source_ref,
        "required_before_synthesis": [
            "source_asset_record",
            "reference_location_record",
            "source_reconstruction_review",
        ],
        "exact_anchor_required": True,
        "acceptable_anchor_types": ["page", "section", "equation", "figure", "table", "note_block"],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "creates_record_now": False,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }


def _route_steps(route_type: str, source_refs: list[str]) -> list[dict[str, Any]]:
    steps = [
        _step("source_identity", "Confirm canonical source_asset identity for every source."),
        _step("exact_anchor", "Record exact reference locations before quoting or synthesizing."),
        _step("source_extraction_report", "Plan per-source concept, notation, equation, relation, and gap extraction."),
        _step("source_reconstruction_review", "Review whether the source stack is reconstructable before claim-sensitive use."),
    ]
    if route_type in {"paired_paper", "multi_paper"}:
        steps.append(
            _step(
                "comparison_matrix",
                "Compare sources dimension-by-dimension only after each source has exact anchors.",
            )
        )
    steps.append(_step("synthesis_boundary", "List what the source set can and cannot support before any evidence write."))
    return [
        {
            **step,
            "source_refs": list(source_refs),
            "requires_exact_reference_locations": True,
        }
        for step in steps
    ]


def _step(step_id: str, purpose: str) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "purpose": purpose,
        "status": "planned",
        "creates_record_now": False,
        "records_validation_result": False,
        "source_support_result": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "claim_trust_mutation": "none",
    }


def _comparison_dimensions(route_type: str) -> list[dict[str, Any]]:
    if route_type == "single_paper":
        return []
    return [
        {
            "dimension": dimension,
            "status": "draft_placeholder",
            "requires_source_review": True,
            "creates_record_now": False,
            "source_support_result": False,
            "summary_inputs_trusted": False,
            "claim_trust_mutation": "none",
        }
        for dimension in _DEFAULT_COMPARISON_DIMENSIONS
    ]


def _extraction_templates(
    route_type: str,
    *,
    profile_id: str,
    source_refs: list[str],
) -> list[dict[str, Any]]:
    templates = [
        {
            "template_id": f"{profile_id}:source:{index + 1}",
            "template_type": "per_source_extraction_report",
            "source_ref": source_ref,
            "required_sections": list(_DEFAULT_FOCUS_SECTIONS),
            "records_created_by_template": False,
            "requires_exact_reference_locations": True,
            "summary_inputs_trusted": False,
            "orientation_only": True,
            "claim_trust_mutation": "none",
        }
        for index, source_ref in enumerate(source_refs)
    ]
    if route_type in {"paired_paper", "multi_paper"}:
        templates.append(
            {
                "template_id": f"{profile_id}:source-set-comparison",
                "template_type": "source_set_comparison_report",
                "source_ref": "source_set",
                "required_sections": [
                    "comparison_question",
                    "source_by_source_anchor_table",
                    "agreements",
                    "disagreements",
                    "convention_conflicts",
                    "scope_conflicts",
                    "missing_evidence",
                    "open_directions",
                    "not_supported",
                ],
                "records_created_by_template": False,
                "requires_exact_reference_locations": True,
                "summary_inputs_trusted": False,
                "orientation_only": True,
                "claim_trust_mutation": "none",
            }
        )
    return templates


def _recommended_next_entrypoints(route_type: str) -> list[dict[str, str]]:
    entries = [
        ("register_source_asset", "source_asset_record", "record canonical source identity before reading output"),
        ("record_reference_location", "reference_location_record", "record exact anchors for definitions, equations, caveats, and results"),
        ("build_literature_source_extraction_candidates", "literature_source_extraction_candidates", "plan source-backed extraction candidates before synthesis"),
        ("build_literature_source_review_handoff", "literature_source_review_handoff", "review source stack coverage before trust-sensitive work"),
        ("record_sensemaking_report", "sensemaking_report_record", "store reading synthesis as orientation only when useful"),
        ("create_validation_contract", "validation_contract_record", "turn source-derived checks into explicit validation requirements"),
        ("preflight_trust_update", "trust_update_preflight", "trust changes require explicit preflight and checkpoints"),
    ]
    if route_type in {"paired_paper", "multi_paper"}:
        entries.insert(
            3,
            (
                "build_literature_comparison_draft",
                "literature_comparison_draft",
                "build a comparison matrix after per-source anchors exist",
            ),
        )
    return [{"entrypoint": name, "surface": surface, "reason": reason} for name, surface, reason in entries]


def _allowed_tool_call(action_id: str) -> dict[str, Any]:
    return {
        "action": "plan_primitive_tools",
        "action_id": action_id,
        "requires_explicit_next_action": True,
        "records_validation_result": False,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }


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
