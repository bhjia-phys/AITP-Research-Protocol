"""Read-only literature/source review handoff packet for host runtimes."""

from __future__ import annotations

from typing import Any

from brain.v5.literature_intake import suggest_literature_intake
from brain.v5.record_refs import lookup_record_refs
from brain.v5.source_reconstruction import build_source_reconstruction_review_packet
from brain.v5.source_stack_coverage import build_source_stack_coverage_manifest


def build_literature_source_review_handoff(
    ws,
    *,
    session_id: str,
    uri: str,
    label: str,
    external_id: str = "",
    short_summary: str = "",
    detected_relevance: str = "",
    optional_claim_id: str = "",
    scoped_output: str = "",
    reviewed_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Compose existing read-only source/literature surfaces for host review."""

    suggestion = suggest_literature_intake(
        ws,
        session_id=session_id,
        uri=uri,
        label=label,
        external_id=external_id,
        short_summary=short_summary,
        detected_relevance=detected_relevance,
        optional_claim_id=optional_claim_id,
        scoped_output=scoped_output,
    )
    claim_id = str(suggestion.get("active_claim") or "")
    refs = [str(ref).strip() for ref in (reviewed_refs or []) if str(ref).strip()]
    ref_lookup = lookup_record_refs(ws, refs)
    coverage = build_source_stack_coverage_manifest(ws)
    coverage_item = _coverage_item_for_claim(coverage, claim_id)
    review_packet = build_source_reconstruction_review_packet(ws, claim_id=claim_id) if claim_id else {}
    return {
        "ok": True,
        "kind": "literature_source_review_handoff",
        "session_id": session_id,
        "topic_id": str(suggestion.get("topic_id") or ""),
        "claim_id": claim_id,
        "literature_intake_suggestion": suggestion,
        "record_ref_lookup": ref_lookup,
        "source_stack_coverage_item": coverage_item,
        "source_reconstruction_review_packet": review_packet,
        "recommended_next_entrypoints": _recommended_next_entrypoints(
            suggestion=suggestion,
            ref_lookup=ref_lookup,
            coverage_item=coverage_item,
            has_review_packet=bool(review_packet),
        ),
        "handoff_policy": {
            "source": "composed_read_only_aitp_surfaces",
            "host_may_use_for": [
                "literature_orientation",
                "source_context_review",
                "record_ref_existence_check",
                "source_stack_gap_review",
                "next_action_selection",
            ],
            "requires_explicit_next_entrypoint": True,
            "allowed_next_entrypoints": [
                "record_reference_location",
                "register_source_asset",
                "record_evidence",
                "create_validation_contract",
                "record_validation_result",
                "record_source_reconstruction_review_result",
                "preflight_trust_update",
            ],
            "forbidden_uses": [
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
            "action_id": "source.review_context",
            "requires_explicit_next_action": True,
            "records_validation_result": False,
            "source_support_result": False,
            "claim_trust_mutation": "none",
        },
        "read_surface_effect": "handoff_context_only",
        "read_only": True,
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
        "truth_source": "composed_typed_records_and_agent_supplied_literature_metadata",
    }


def _coverage_item_for_claim(coverage: dict[str, Any], claim_id: str) -> dict[str, Any]:
    if not claim_id:
        return {}
    for item in coverage.get("items") or []:
        if isinstance(item, dict) and item.get("claim_id") == claim_id:
            return item
    return {}


def _recommended_next_entrypoints(
    *,
    suggestion: dict[str, Any],
    ref_lookup: dict[str, Any],
    coverage_item: dict[str, Any],
    has_review_packet: bool,
) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    reference_candidate = suggestion.get("reference_candidate")
    if isinstance(reference_candidate, dict):
        entries.append(
            {
                "entrypoint": "record_reference_location",
                "surface": "reference_location_record",
                "reason": "record the literature location before using it as source context",
            }
        )
    for item in ref_lookup.get("refs") or []:
        if not isinstance(item, dict):
            continue
        entrypoint = str(item.get("suggested_next_entrypoint") or "")
        surface = str(item.get("suggested_next_surface") or "")
        reason = str(item.get("suggested_next_reason") or "")
        if entrypoint:
            entries.append({"entrypoint": entrypoint, "surface": surface, "reason": reason})
    if coverage_item and coverage_item.get("coverage_status") != "complete":
        entries.append(
            {
                "entrypoint": "record_evidence",
                "surface": "evidence_record",
                "reason": "source-stack coverage still has evidence or reconstruction gaps",
            }
        )
    if has_review_packet:
        entries.append(
            {
                "entrypoint": "record_source_reconstruction_review_result",
                "surface": "source_reconstruction_review_result_record",
                "reason": "review source reconstruction gaps before trust-sensitive use",
            }
        )
    return _unique_entrypoints(entries)


def _unique_entrypoints(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []
    for entry in entries:
        key = (entry.get("entrypoint", ""), entry.get("surface", ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return unique
