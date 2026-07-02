"""Read-only literature source extraction planning surface."""

from __future__ import annotations

from typing import Any

from brain.v5.record_refs import lookup_record_refs
from brain.v5.workspace import get_session_binding


_DEFAULT_EXTRACTION_MODES = ("concept", "notation", "equation_anchor", "relation", "open_gap")

_MODE_SPECS: dict[str, dict[str, Any]] = {
    "concept": {
        "candidate_kind": "physics_object",
        "target_record": "physics_object_record",
        "purpose": "extract a named physical object, concept, operator, field, regime, or definition",
        "required_fields": ["object_type", "name", "definition", "source_refs"],
        "review_questions": [
            "Which exact source location defines this object?",
            "Which assumptions or regimes are attached to the definition?",
            "Does the notation collide with another source or local note?",
        ],
    },
    "notation": {
        "candidate_kind": "physics_object",
        "target_record": "physics_object_record",
        "purpose": "extract notation, normalization, sign, scheme, or convention as a source-backed object",
        "required_fields": ["object_type", "name", "notation", "definition", "source_refs"],
        "review_questions": [
            "Is the convention local to one paper or shared across the source set?",
            "Does changing this convention alter the current claim scope?",
            "Which equations or sections anchor the convention?",
        ],
    },
    "equation_anchor": {
        "candidate_kind": "reference_location",
        "target_record": "reference_location_record",
        "purpose": "locate a page, section, equation, figure, table, or local-note anchor",
        "required_fields": ["connector_id", "location_type", "uri", "label", "source_ref"],
        "review_questions": [
            "Is the anchor exact enough for another agent to reopen it?",
            "Does the anchor identify an equation, definition, result, or caveat?",
            "Does it need a source_asset record before claim-scoped use?",
        ],
    },
    "relation": {
        "candidate_kind": "object_relation",
        "target_record": "object_relation_record",
        "purpose": "extract a relation between definitions, assumptions, limits, equations, or claims",
        "required_fields": ["relation_type", "subject_id", "object_id", "statement", "source_refs"],
        "review_questions": [
            "Are both relation endpoints already typed physics objects?",
            "Is the relation asserted by the source or inferred by the agent?",
            "Which failure modes would break this relation?",
        ],
    },
    "open_gap": {
        "candidate_kind": "proof_obligation",
        "target_record": "proof_obligation_record",
        "purpose": "extract an unresolved derivation, source dependency, assumption, or validation gap",
        "required_fields": ["statement", "obligation_type", "status", "next_action", "source_refs"],
        "review_questions": [
            "Is the gap a missing source, a derivation gap, or a validation requirement?",
            "Can the current claim be scoped without closing this gap?",
            "Which evidence, validation, or checkpoint would close it?",
        ],
    },
}


def build_literature_source_extraction_candidates(
    ws,
    *,
    session_id: str,
    source_refs: list[str],
    focus_terms: list[str] | None = None,
    extraction_modes: list[str] | None = None,
    optional_claim_id: str = "",
    rationale: str = "",
) -> dict[str, Any]:
    """Plan source extraction candidates without reading content or writing records."""

    session = get_session_binding(ws, session_id)
    claim_id = optional_claim_id or session.active_claim
    normalized_refs = _nonempty_unique(source_refs)
    if not normalized_refs:
        raise ValueError("source_refs is required")
    normalized_focus_terms = _nonempty_unique(focus_terms or [])
    normalized_modes = _normalize_modes(extraction_modes)
    ref_lookup = lookup_record_refs(ws, normalized_refs)
    candidate_groups = [
        _candidate_group(
            mode,
            topic_id=session.topic_id,
            claim_id=claim_id,
            source_refs=normalized_refs,
            focus_terms=normalized_focus_terms,
        )
        for mode in normalized_modes
    ]
    return {
        "ok": True,
        "kind": "literature_source_extraction_candidates",
        "session_id": session_id,
        "topic_id": session.topic_id,
        "claim_id": claim_id,
        "rationale": rationale,
        "source_refs": normalized_refs,
        "source_ref_count": len(normalized_refs),
        "focus_terms": normalized_focus_terms,
        "focus_term_count": len(normalized_focus_terms),
        "extraction_modes": normalized_modes,
        "extraction_mode_count": len(normalized_modes),
        "candidate_groups": candidate_groups,
        "candidate_group_count": len(candidate_groups),
        "record_ref_lookup": ref_lookup,
        "draft_record_intent": {
            "kind": "literature_source_extraction_candidate_set",
            "status": "draft_only",
            "requires_explicit_write_surface": True,
            "requires_source_review": True,
            "creates_record_now": False,
            "records_validation_result": False,
            "source_support_result": False,
            "claim_trust_mutation": "none",
            "can_update_claim_trust": False,
        },
        "recommended_next_entrypoints": [
            {
                "entrypoint": "register_source_asset",
                "surface": "source_asset_record",
                "reason": "record canonical source identity before source-backed extraction",
            },
            {
                "entrypoint": "record_reference_location",
                "surface": "reference_location_record",
                "reason": "anchor extracted concepts, equations, or caveats to exact source locations",
            },
            {
                "entrypoint": "record_physics_object",
                "surface": "physics_object_record",
                "reason": "turn source-backed concepts, notation, and conventions into typed objects",
            },
            {
                "entrypoint": "record_object_relation",
                "surface": "object_relation_record",
                "reason": "record source-backed relations after object endpoints are typed",
            },
            {
                "entrypoint": "create_proof_obligation",
                "surface": "proof_obligation_record",
                "reason": "preserve source or derivation gaps before any claim-support decision",
            },
            {
                "entrypoint": "record_sensemaking_report",
                "surface": "sensemaking_report_record",
                "reason": "summarize extraction results as orientation, not claim support",
            },
            {
                "entrypoint": "create_validation_contract",
                "surface": "validation_contract_record",
                "reason": "convert extraction-derived checks into explicit validation requirements",
            },
            {
                "entrypoint": "preflight_trust_update",
                "surface": "trust_update_preflight",
                "reason": "trust changes require explicit AITP preflight and checkpoints",
            },
        ],
        "extraction_policy": {
            "source": "session_binding_agent_supplied_sources_focus_terms_and_modes",
            "host_may_use_for": [
                "source_extraction_planning",
                "concept_and_notation_scaffolding",
                "equation_anchor_planning",
                "object_relation_candidate_planning",
                "proof_obligation_discovery",
            ],
            "requires_explicit_next_entrypoint": True,
            "allowed_next_entrypoints": [
                "register_source_asset",
                "record_reference_location",
                "record_physics_object",
                "record_object_relation",
                "create_proof_obligation",
                "record_sensemaking_report",
                "create_validation_contract",
                "record_validation_result",
                "preflight_trust_update",
            ],
            "forbidden_uses": [
                "extracted_source_fact",
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
            "action_id": "source.extract_candidates",
            "requires_explicit_next_action": True,
            "records_validation_result": False,
            "source_support_result": False,
            "claim_trust_mutation": "none",
        },
        "read_surface_effect": "extraction_candidates_only",
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
        "truth_source": "session_binding_agent_supplied_sources_focus_terms_and_modes",
    }


def _candidate_group(
    mode: str,
    *,
    topic_id: str,
    claim_id: str,
    source_refs: list[str],
    focus_terms: list[str],
) -> dict[str, Any]:
    spec = _MODE_SPECS[mode]
    return {
        "mode": mode,
        "candidate_kind": spec["candidate_kind"],
        "target_record": spec["target_record"],
        "topic_id": topic_id,
        "claim_id": claim_id,
        "source_refs": list(source_refs),
        "focus_terms": list(focus_terms),
        "purpose": spec["purpose"],
        "required_fields": list(spec["required_fields"]),
        "review_questions": list(spec["review_questions"]),
        "status": "candidate_only",
        "requires_source_review": True,
        "creates_record_now": False,
        "records_validation_result": False,
        "source_support_result": False,
        "claim_trust_mutation": "none",
        "summary_inputs_trusted": False,
        "orientation_only": True,
    }


def _normalize_modes(values: list[str] | None) -> list[str]:
    requested = _nonempty_unique(values or list(_DEFAULT_EXTRACTION_MODES))
    modes = [value.lower().replace("-", "_") for value in requested if value.lower().replace("-", "_") in _MODE_SPECS]
    return modes or list(_DEFAULT_EXTRACTION_MODES)


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
