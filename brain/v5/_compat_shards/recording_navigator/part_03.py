# Compatibility shard 3 for recording_navigator.
from __future__ import annotations

def _lightweight_provenance_gaps(counts: dict[str, int]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    if int(counts.get("reference_location", 0) or 0) == 0:
        gaps.append(
            {
                "gap_type": "missing_reference_location",
                "summary": "No reference location is recorded for the current topic/claim focus.",
                "recommended_entrypoints": ["aitp_v5_record_reference_location"],
            }
        )
    if int(counts.get("source_asset", 0) or 0) == 0:
        gaps.append(
            {
                "gap_type": "missing_source_asset",
                "summary": "No source asset is recorded for the current topic/claim focus.",
                "recommended_entrypoints": ["aitp_v5_register_source_asset"],
            }
        )
    if int(counts.get("evidence", 0) or 0) == 0:
        gaps.append(
            {
                "gap_type": "missing_evidence",
                "summary": "No evidence record is linked to the current topic/claim focus.",
                "recommended_entrypoints": ["aitp_v5_record_evidence"],
            }
        )
    if int(counts.get("validation_contract", 0) or 0) == 0:
        gaps.append(
            {
                "gap_type": "missing_validation_contract",
                "summary": "No validation contract is recorded for the current topic/claim focus.",
                "recommended_entrypoints": ["aitp_v5_create_validation_contract"],
            }
        )
    return gaps

def _lightweight_recommended_moments(counts: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {
            "moment": gap["gap_type"],
            "why": gap["summary"],
            "recommended_entrypoints": gap["recommended_entrypoints"],
        }
        for gap in _lightweight_provenance_gaps(counts)
    ]

def _lightweight_open_obligation_hints(relation_map: dict[str, Any]) -> list[dict[str, Any]]:
    source_records = relation_map.get("source_records") if isinstance(relation_map, dict) else {}
    obligation_ids = source_records.get("proof_obligations", []) if isinstance(source_records, dict) else []
    blockers = relation_map.get("current_blockers", []) if isinstance(relation_map, dict) else []
    out: list[dict[str, Any]] = []
    for obligation_id in obligation_ids:
        out.append({"obligation_id": str(obligation_id), "status": "open_or_relevant"})
    for blocker in blockers:
        text = str(blocker)
        if text and text not in {item.get("obligation_id") for item in out}:
            out.append({"summary": text, "status": "open_or_relevant"})
    return out

def _slot_summary(slot: str, graph: dict[str, Any]) -> dict[str, Any]:
    expansion = _SLOT_EXPANSIONS[slot]
    counts = dict(graph.get("record_counts") or {})
    count_key = expansion["record_kind"]
    if count_key == "trust_update_preflight":
        current_count = 0
    else:
        current_count = int(counts.get(count_key, 0) or 0)
    return {
        "slot": slot,
        "record_kind": expansion["record_kind"],
        "current_count": current_count,
        "recommended_write_tool": expansion["recommended_write_tool"],
        "expand_with": "aitp_v5_expand_recording_slot",
        "read_only_at_this_layer": True,
        "can_update_claim_trust": False,
        "when_to_use": expansion["when_to_use"],
    }

def _recommended_slots_from_graph(graph: dict[str, Any]) -> list[str]:
    counts = dict(graph.get("record_counts") or {})
    gaps = list(graph.get("provenance_gaps") or [])
    moments = list(graph.get("recommended_moments") or [])
    slots: list[str] = []
    for gap in gaps:
        for entrypoint in gap.get("recommended_entrypoints", []) if isinstance(gap, dict) else []:
            slots.extend(_slots_for_entrypoint(str(entrypoint)))
    for moment in moments:
        if isinstance(moment, dict):
            for entrypoint in moment.get("recommended_entrypoints", []):
                slots.extend(_slots_for_entrypoint(str(entrypoint)))
    if int(counts.get("reference_location", 0) or 0) == 0:
        slots.append("reference_location")
    if int(counts.get("source_asset", 0) or 0) == 0:
        slots.append("source_asset")
    if int(counts.get("evidence", 0) or 0) == 0:
        slots.append("evidence")
    if int(counts.get("proof_obligation", 0) or 0) == 0:
        slots.append("proof_obligation")
    return _unique_slots(slots)

def _slots_for_entrypoint(entrypoint: str) -> list[str]:
    table = {
        "aitp_v5_record_reference_location": ["reference_location"],
        "aitp_v5_register_source_asset": ["source_asset"],
        "aitp_v5_capture_source_asset_auto": ["source_asset"],
        "aitp_v5_record_tool_run": ["tool_run"],
        "aitp_v5_capture_tool_run_auto": ["tool_run"],
        "aitp_v5_record_evidence": ["evidence"],
        "aitp_v5_record_code_state": ["code_state"],
        "aitp_v5_capture_code_state_auto": ["code_state"],
        "aitp_v5_attach_artifact": ["artifact"],
        "aitp_v5_record_physics_object": ["physics_object"],
        "aitp_v5_record_object_relation": ["object_relation"],
        "aitp_v5_record_research_route": ["research_route"],
        "aitp_v5_start_research_run": ["research_run"],
        "aitp_v5_record_research_run_event": ["research_run_event"],
        "aitp_v5_create_proof_obligation": ["proof_obligation"],
        "aitp_v5_record_source_reconstruction_review_result": ["source_reconstruction_review"],
        "aitp_v5_create_validation_contract": ["validation_contract"],
        "aitp_v5_record_validation_result": ["validation_result"],
        "aitp_v5_request_human_checkpoint": ["human_checkpoint"],
        "aitp_v5_record_sensemaking_report": ["sensemaking_report"],
        "aitp_v5_preflight_trust_update": ["trust_preflight"],
    }
    return table.get(entrypoint, [])

def _fill_known_field_hints(fields: list[str], focus: dict[str, Any]) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    for field in fields:
        value = ""
        if field in {"topic_id", "topic"}:
            value = focus.get("topic_id", "")
        elif field in {"claim_id", "claim"}:
            value = focus.get("claim_id", "")
        elif field in {"session_id", "session"}:
            value = focus.get("session_id", "")
        hints.append(
            {
                "name": field,
                "known_value": value,
                "source": "current_position" if value else "agent_or_human_must_supply",
            }
        )
    return hints

def _unknown_slot_expansion(session_id: str, slot: str) -> dict[str, Any]:
    return {
        "ok": False,
        "kind": "recording_slot_expansion",
        "slot": str(slot or ""),
        "session_id": str(session_id or ""),
        "requested_session_id": str(session_id or ""),
        "topic_id": "",
        "claim_id": "",
        "recommended_write_tool": "",
        "cli_template": "",
        "record_kind": "",
        "required_fields": [],
        "optional_fields": [],
        "recommended_links": [],
        "graph_edges_created": [],
        "when_to_use": "",
        "candidate_context": {},
        "recording_sequence": [],
        "trust_effect": {
            "writes_kernel_state": False,
            "can_update_claim_trust": False,
            "claim_trust_mutation": "none",
            "trust_preflight_required_for_trust_change": False,
        },
        "warnings": [f"unknown slot; supported slots are: {', '.join(_FIRST_LEVEL_SLOT_ORDER)}"],
        "verify_with": "aitp_v5_verify_recording_effect",
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }

def _slot_warnings(slot: str) -> list[str]:
    warnings = [
        "slot expansion is read-only guidance; it does not write a record",
        "verify with aitp_v5_verify_recording_effect after the typed write/preflight tool returns",
    ]
    if slot in {"reference_location", "source_asset", "sensemaking_report", "research_route", "research_run", "research_run_event"}:
        warnings.append("this record is orientation/process context and is not claim evidence by itself")
    if slot == "trust_preflight":
        warnings.append("preflight cannot apply trust; trust application remains excluded from host bridge targets")
    if slot == "evidence":
        warnings.append("evidence records should point to source/tool/validation/artifact provenance where available")
    if slot == "source_reconstruction_review":
        warnings.append("source reconstruction review records audit reconstructability and do not promote claim trust")
    if slot == "validation_result":
        warnings.append("validation results should be tied to an explicit validation contract and tool run")
    return warnings

def _verification_failures(
    expected_refs: list[str],
    missing_refs: list[str],
    before_node_ids: list[str],
    new_node_ids: list[str],
    found_refs: list[str],
) -> list[str]:
    failures: list[str] = []
    if expected_refs and missing_refs:
        failures.append("some expected refs were not found in the typed store")
    if before_node_ids and not new_node_ids and not found_refs:
        failures.append("no new graph nodes were observed and no expected refs were confirmed")
    return failures
