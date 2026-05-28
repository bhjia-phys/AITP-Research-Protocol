"""Conservative literature intake suggestions for AITP v5."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.output_stability import load_final_output_profile
from brain.v5.references import record_reference_location
from brain.v5.workspace import get_session_binding

_REFERENCE_CONNECTOR = "literature_search"
_REFERENCE_LOCATION_TYPE = "paper"
_EVIDENCE_STATUSES = ("supports", "contradicts", "mixed", "inconclusive")


def suggest_literature_intake(
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
) -> dict[str, Any]:
    """Return guarded intake actions for a discovered literature item without writing records."""

    session = get_session_binding(ws, session_id)
    claim_id = ""
    if session.active_claim:
        claim_id = optional_claim_id or session.active_claim
    clear_relation = _has_clear_claim_relation(detected_relevance, scoped_output)
    reference = _reference_candidate(
        topic_id=session.topic_id,
        claim_id=claim_id,
        uri=uri,
        label=label,
        external_id=external_id,
        short_summary=short_summary,
        detected_relevance=detected_relevance,
    )
    sensemaking = _sensemaking_candidate(session.topic_id, claim_id, label, short_summary, detected_relevance)
    evidence = _evidence_candidate(session.topic_id, claim_id, reference["location_id"], short_summary, scoped_output)
    next_steps = _guarded_next_steps(claim_id, clear_relation, sensemaking, evidence)
    output_profile = _topic_output_profile(ws, session.topic_id)
    return {
        "ok": True,
        "kind": "literature_intake_suggestion",
        "session_id": session_id,
        "topic_id": session.topic_id,
        "active_claim": claim_id,
        "recommended_action": _recommended_action(claim_id, clear_relation, bool(scoped_output)),
        "reference_candidate": reference,
        "sensemaking_candidate": sensemaking if claim_id and clear_relation else {},
        "evidence_candidate": evidence if claim_id and clear_relation and scoped_output else {},
        "guarded_next_steps": next_steps,
        "mcp_templates": _mcp_templates(reference, sensemaking, evidence, claim_id, clear_relation, scoped_output),
        "cli_templates": _cli_templates(reference, sensemaking, evidence, claim_id, clear_relation, scoped_output),
        "risk_notes": _risk_notes(claim_id, clear_relation, scoped_output),
        "output_profile_context": output_profile,
        "forbidden_without_preflight": [
            "aitp_v5_preflight_trust_update",
            "aitp_v5_create_promotion_packet",
            "aitp_v5_apply_promotion_packet",
        ],
        "trust_update_forbidden": True,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "truth_source": "session_binding_and_agent_supplied_literature_metadata",
    }


def record_literature_candidate(
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
) -> dict[str, Any]:
    """Write only the orientation reference location and return guarded follow-up suggestions."""

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
    ref = suggestion["reference_candidate"]
    location = record_reference_location(
        ws,
        topic_id=ref["topic_id"],
        claim_id=ref["claim_id"],
        connector_id=ref["connector_id"],
        location_type=ref["location_type"],
        uri=ref["uri"],
        label=ref["label"],
        external_id=ref["external_id"],
        status="located",
        summary=ref["summary"],
        metadata=ref["metadata"],
        linked_records=ref["linked_records"],
    )
    return {
        "ok": True,
        "kind": "literature_intake_record_result",
        "session_id": session_id,
        "topic_id": suggestion["topic_id"],
        "active_claim": suggestion["active_claim"],
        "recommended_action": suggestion["recommended_action"],
        "recorded_reference_location": {"ok": True, **asdict(location)},
        "guarded_next_steps": suggestion["guarded_next_steps"],
        "sensemaking_candidate": suggestion["sensemaking_candidate"],
        "evidence_candidate": suggestion["evidence_candidate"],
        "evidence_written": False,
        "sensemaking_written": False,
        "trust_update_forbidden": True,
        "summary_inputs_trusted": False,
        "orientation_only": False,
        "can_update_kernel_state": True,
        "kernel_state_change": "reference_location_record_only",
        "can_update_claim_trust": False,
        "truth_source": "written_reference_location_record",
    }


def _reference_candidate(
    *,
    topic_id: str,
    claim_id: str,
    uri: str,
    label: str,
    external_id: str,
    short_summary: str,
    detected_relevance: str,
) -> dict[str, Any]:
    location_id = prefixed_id(
        "reference-location",
        f"{topic_id}:{claim_id}:{_REFERENCE_CONNECTOR}:{_REFERENCE_LOCATION_TYPE}:{uri}",
        max_slug=64,
    )
    return {
        "location_id": location_id,
        "topic_id": topic_id,
        "claim_id": claim_id,
        "connector_id": _REFERENCE_CONNECTOR,
        "location_type": _REFERENCE_LOCATION_TYPE,
        "uri": uri,
        "label": label,
        "external_id": external_id,
        "status": "candidate",
        "summary": short_summary,
        "metadata": {
            "detected_relevance": detected_relevance,
            "intake_source": "literature_intake_assistant",
        },
        "linked_records": {"claim_id": claim_id} if claim_id else {},
        "orientation_only": True,
    }


def _sensemaking_candidate(
    topic_id: str,
    claim_id: str,
    label: str,
    short_summary: str,
    detected_relevance: str,
) -> dict[str, Any]:
    summary = _sensemaking_summary(short_summary, detected_relevance)
    return {
        "topic_id": topic_id,
        "claim_id": claim_id,
        "title": f"Literature intake: {label}",
        "summary": summary,
        "open_questions": [
            "prior_art_closeness",
            "claim_scope_may_need_shrinking",
            "open_proof_gap",
            "possible_failure_mode",
        ],
        "next_actions": ["decide_whether_to_record_evidence_with_explicit_scope"],
        "validation_status": "not_validation",
    }


def _evidence_candidate(
    topic_id: str,
    claim_id: str,
    reference_location_id: str,
    short_summary: str,
    scoped_output: str,
) -> dict[str, Any]:
    status = _evidence_status(short_summary)
    return {
        "topic_id": topic_id,
        "claim_id": claim_id,
        "evidence_type": "literature_scope_limit" if status == "mixed" else "literature",
        "status": status,
        "summary": short_summary,
        "supports_outputs": [scoped_output] if scoped_output else [],
        "source_refs": [f"reference_location:{reference_location_id}"],
        "reference_location_id": reference_location_id,
        "scope_note": scoped_output,
    }


def _recommended_action(claim_id: str, clear_relation: bool, has_scope: bool) -> str:
    if not claim_id:
        return "record_reference_only"
    if clear_relation and has_scope:
        return "record_reference_plus_evidence_candidate"
    if clear_relation:
        return "record_reference_plus_sensemaking"
    return "record_reference_only"


def _guarded_next_steps(
    claim_id: str,
    clear_relation: bool,
    sensemaking: dict[str, Any],
    evidence: dict[str, Any],
) -> list[dict[str, Any]]:
    if not claim_id or not clear_relation:
        return []
    steps = [{"action": "record_sensemaking_report", "candidate": sensemaking, "required": False}]
    if evidence["supports_outputs"]:
        steps.append({"action": "record_evidence", "candidate": evidence, "required": False})
    return steps


def _mcp_templates(
    reference: dict[str, Any],
    sensemaking: dict[str, Any],
    evidence: dict[str, Any],
    claim_id: str,
    clear_relation: bool,
    scoped_output: str,
) -> dict[str, Any]:
    templates: dict[str, Any] = {
        "record_reference_location": {
            "entrypoint": "aitp_v5_record_reference_location",
            **{key: reference[key] for key in ("topic_id", "claim_id", "connector_id", "location_type", "uri", "label", "external_id")},
            "status": "located",
            "summary": reference["summary"],
            "metadata": reference["metadata"],
            "linked_records": reference["linked_records"],
        }
    }
    if claim_id and clear_relation:
        templates["record_sensemaking_report"] = {
            "entrypoint": "aitp_v5_record_sensemaking_report",
            **sensemaking,
        }
    if claim_id and clear_relation and scoped_output:
        templates["record_evidence"] = {"entrypoint": "aitp_v5_record_evidence", **evidence}
    return templates


def _cli_templates(
    reference: dict[str, Any],
    sensemaking: dict[str, Any],
    evidence: dict[str, Any],
    claim_id: str,
    clear_relation: bool,
    scoped_output: str,
) -> list[str]:
    templates = [
        (
            "aitp-v5 --base <workspace> reference location record "
            f"--topic {reference['topic_id']} --claim {reference['claim_id']} "
            f"--connector {reference['connector_id']} --type {reference['location_type']} "
            f"--uri {reference['uri']} --label <label> --external-id {reference['external_id']}"
        )
    ]
    if claim_id and clear_relation:
        templates.append(
            "aitp-v5 --base <workspace> sensemaking report "
            f"--topic {sensemaking['topic_id']} --claim {claim_id} "
            "--title <literature-intake-title> --summary <prior-art-scope-gap-summary>"
        )
    if claim_id and clear_relation and scoped_output:
        templates.append(
            "aitp-v5 --base <workspace> evidence record "
            f"--topic {evidence['topic_id']} --claim {claim_id} "
            f"--type {evidence['evidence_type']} --status {evidence['status']} "
            "--summary <source-grounded-scope-summary> "
            f"--supports-output {scoped_output} --source-ref reference_location:{evidence['reference_location_id']}"
        )
    return templates


def _risk_notes(claim_id: str, clear_relation: bool, scoped_output: str) -> list[str]:
    notes = [
        "reference_location_is_orientation_only",
        "literature_summary_is_not_validated_evidence",
        "trust_update_requires_preflight_and_human_checkpoint_when_policy_requires",
    ]
    if not claim_id:
        notes.append("bind_active_claim_before_evidence")
    if claim_id and not clear_relation:
        notes.append("claim_relation_unclear_record_reference_only")
    if claim_id and clear_relation and not scoped_output:
        notes.append("evidence_requires_scoped_output")
    if claim_id and clear_relation:
        notes.append("not_a_supports_claim_by_default")
    return notes


def _has_clear_claim_relation(detected_relevance: str, scoped_output: str) -> bool:
    lowered = detected_relevance.lower()
    signals = ("explicit", "claim", "close_prior_art", "close prior art", "scope", "contradict", "support", "mixed")
    return bool(scoped_output) or any(signal in lowered for signal in signals)


def _evidence_status(short_summary: str) -> str:
    lowered = short_summary.lower()
    if any(token in lowered for token in ("close prior art", "scope", "already studied", "remains open")):
        return "mixed"
    if "contradict" in lowered or "refute" in lowered:
        return "contradicts"
    if "support" in lowered:
        return "supports"
    return _EVIDENCE_STATUSES[-1]


def _sensemaking_summary(short_summary: str, detected_relevance: str) -> str:
    lowered = f"{short_summary} {detected_relevance}".lower()
    if "close" in lowered and "level statistics" in lowered and "classification" in lowered:
        return "close prior art; level statistics already studied; algebraic classification remains open"
    return short_summary or detected_relevance or "Literature item may affect claim scope or open proof gaps."


def _topic_output_profile(ws, topic_id: str) -> dict[str, Any]:
    profile = load_final_output_profile(ws, topic_id)
    if not profile or not profile.get("present"):
        return {}
    return {
        "output_version": str(profile.get("output_version") or ""),
        "stable_sections": list(profile.get("stable_sections") or []),
        "lane_boundary_note": "Final lane evidence must use usable_for_final=True sources; diagnostic lane may use assumptions with explicit labels. Literature evidence must not mix lanes.",
    }
