# Compatibility shard 2 for lightweight_record_router.
from __future__ import annotations

def _artifact_plan(
    *,
    topic_id: str,
    target_claim_id: str,
    event_summary: str,
    touched_entry: dict[str, str],
) -> dict[str, Any]:
    value = touched_entry["value"]
    if touched_entry["kind"] == "canonical_ref":
        kind, rid = _split_ref(value)  # type: ignore[assignment]
        return {
            "record_type": "artifact",
            "target_claim_id": target_claim_id,
            "summary": _compress(event_summary),
            "required_fields": {
                "topic_id": topic_id,
                "claim_id": target_claim_id,
                "artifact_type": _infer_artifact_type(rid),
                "uri": rid,
                "summary": _compress(event_summary),
            },
            "optional_fields": {
                "metadata": {
                    "status": "orientation_only_not_claim_trust",
                    "event_summary": event_summary,
                    "source": "lightweight_record_router",
                }
            },
            "verification_refs": [value],  # already canonical
            "recommended_mcp_tool": "aitp_v5_attach_artifact_auto",
            "execute_now": False,
        }
    # path entry -> plan a new artifact
    return {
        "record_type": "artifact",
        "target_claim_id": target_claim_id,
        "summary": _compress(event_summary),
        "required_fields": {
            "topic_id": topic_id,
            "claim_id": target_claim_id,
            "path": value,
            "artifact_type": _infer_artifact_type(value),
            "summary": _compress(event_summary),
        },
        "optional_fields": {
            "metadata": {
                "status": "orientation_only_not_claim_trust",
                "event_summary": event_summary,
                "router_reason": "durable_artifact_located",
            }
        },
        "verification_refs": ["artifact:<to-be-created>"],
        "recommended_mcp_tool": "aitp_v5_attach_artifact_auto",
        "execute_now": False,
    }

def _sensemaking_plan(
    *,
    topic_id: str,
    target_claim_id: str,
    event_summary: str,
    is_runtime_failure: bool,
    is_boundary: bool,
    extra_verification_refs: list[str] | None = None,
) -> dict[str, Any]:
    if is_runtime_failure:
        title = "Runtime/environment failure boundary (not algorithm failure)"
        summary = (
            f"{event_summary}\n\nThis is a runtime/environment failure, NOT an "
            "algorithm failure. It does not refute any claim."
        )
    elif is_boundary:
        title = "Lane/convention boundary note"
        summary = (
            f"{event_summary}\n\nThis is an orientation-only boundary/convention "
            "note. It is not evidence and does not change claim trust."
        )
    else:
        title = "Orientation-only sensemaking note"
        summary = event_summary
    extras = list(extra_verification_refs or [])
    return {
        "record_type": "sensemaking_report",
        "target_claim_id": target_claim_id,
        "summary": _compress(summary),
        "required_fields": {
            "topic_id": topic_id,
            "claim_id": target_claim_id,
            "title": title,
            "summary": summary,
        },
        "optional_fields": {
            "evidence_refs": [],
            "open_questions": [],
            "next_actions": [],
            "metadata": {"status": "orientation_only_not_claim_trust"},
        },
        "verification_refs": extras + ["sensemaking_report:<to-be-created>"],
        "recommended_mcp_tool": "aitp_v5_record_sensemaking_report",
        "execute_now": False,
    }

def _proof_obligation_plan(
    *,
    topic_id: str,
    target_claim_id: str,
    event_summary: str,
    extra_verification_refs: list[str] | None = None,
) -> dict[str, Any]:
    event_lower = _lower(event_summary)
    if _contains_any(event_lower, _KW_GAP):
        obligation_type = "validation_gap"
    elif _contains_any(event_lower, ["reproduce", "rerun", "复现"]):
        obligation_type = "reproducibility_gap"
    elif _contains_any(event_lower, ["undefined", "未定义"]):
        obligation_type = "undefined_object_gap"
    else:
        obligation_type = "proof_gap"
    extras = list(extra_verification_refs or [])
    return {
        "record_type": "proof_obligation",
        "target_claim_id": target_claim_id,
        "summary": _compress(event_summary),
        "required_fields": {
            "topic_id": topic_id,
            "claim_id": target_claim_id,
            "statement": _compress(event_summary),
            "obligation_type": obligation_type,
            "status": "open",
            "maturity_level": "exploratory",
            "next_action": _compress(event_summary),
        },
        "optional_fields": {
            "required_evidence": [],
            "proof_strategy": [],
            "failure_modes": [],
            "source_refs": [],
            "evidence_refs": [],
            "artifact_ids": [],
            "metadata": {"status": "orientation_only_not_claim_trust"},
        },
        "verification_refs": extras + ["proof_obligation:<to-be-created>"],
        "recommended_mcp_tool": "aitp_v5_create_proof_obligation",
        "execute_now": False,
    }

def _evidence_plan(
    *,
    topic_id: str,
    target_claim_id: str,
    event_summary: str,
    verified_refs: list[str],
    negative: bool,
    extra_verification_refs: list[str] | None = None,
) -> dict[str, Any]:
    tool_run_ids: list[str] = []
    validation_result_ids: list[str] = []
    for ref in verified_refs:
        kind, rid = _split_ref(ref)  # type: ignore[assignment]
        if kind == "tool_run":
            tool_run_ids.append(rid)
        elif kind == "validation_result":
            validation_result_ids.append(rid)
    if negative:
        evidence_type = "negative_result"
        status = "inconclusive"
    else:
        evidence_type = "tool_run" if tool_run_ids and not validation_result_ids else "validation_result"
        status = "supports"
    extras = list(extra_verification_refs or [])
    return {
        "record_type": "evidence",
        "target_claim_id": target_claim_id,
        "summary": _compress(event_summary),
        "required_fields": {
            "topic_id": topic_id,
            "claim_id": target_claim_id,
            "evidence_type": evidence_type,
            "status": status,
            "summary": _compress(event_summary),
        },
        "optional_fields": {
            "supports_outputs": [],
            "source_refs": [],
            "tool_run_ids": tool_run_ids,
            "validation_result_ids": validation_result_ids,
            "artifact_ids": [],
            "metadata": {
                "status": "orientation_only_not_claim_trust unless verified evidence is explicit"
            },
        },
        # spec §4: preserve canonical input refs (tool_run:run-abc + existing artifact refs)
        # plus the to-be-created evidence ref
        "verification_refs": list(verified_refs) + extras + ["evidence:<to-be-created>"],
        "recommended_mcp_tool": "aitp_v5_record_evidence",
        "execute_now": False,
    }

def _trust_preflight_plan(
    *,
    topic_id: str,
    target_claim_id: str,
    current_session_id: str,
    event_summary: str,
    extra_verification_refs: list[str] | None = None,
) -> dict[str, Any]:
    extras = list(extra_verification_refs or [])
    return {
        "record_type": "trust_preflight",
        "target_claim_id": target_claim_id,
        "summary": _compress(event_summary),
        "required_fields": {
            "action": "set_confidence",
            "session_id": current_session_id,
            "topic_id": topic_id,
            "claim_id": target_claim_id,
            "requested_state": "",
        },
        "optional_fields": {
            "source_kind": "typed_records",
            "source_ref": "",
            "evidence_refs": [],
            "code_state_ids": [],
            "rationale": "requested by event_summary; preflight only, not an approval",
        },
        "verification_refs": extras + ["trust_update_preflight:<to-be-created>"],
        "recommended_mcp_tool": "aitp_v5_preflight_trust_update",
        "execute_now": False,
    }

def _compress(text: str, limit: int = 240) -> str:
    text = (text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text[:limit] + ("…" if len(text) > limit else "")

def _no_write_payload(
    *,
    topic_id: str,
    current_session_id: str,
    active_claim_id: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "ok": True,
        "kind": "lightweight_record_write_plan",
        "decision": DECISION_NO_WRITE,
        "topic_id": topic_id,
        "current_session_id": current_session_id,
        "active_claim_id": active_claim_id,
        "target_claim": {
            "target_claim_id": "",
            "reason_for_target_claim": "no target claim needed for no_write",
            "confidence": "low",
        },
        "write_reasons": [],
        "no_write_reason": reason,
        "selected_record_types": [],
        "typed_write_plan": [],
        "trust_boundary": dict(_TRUST_BOUNDARY),
        "final_human_readable_summary": (
            "No durable research event detected; nothing recorded, no claim changed."
        ),
        **_TOP_LEVEL_TRUTH,
    }
