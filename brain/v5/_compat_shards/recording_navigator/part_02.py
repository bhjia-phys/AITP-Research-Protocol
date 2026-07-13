# Compatibility shard 2 for recording_navigator.
from __future__ import annotations

def build_recording_navigation_state(
    ws: WorkspacePaths,
    session_id: str,
    *,
    claim_id: str = "",
    limit: int = 40,
) -> dict[str, Any]:
    """Return the shallow navigation state for a session/claim before choosing a slot."""

    focus = _lightweight_focus(ws, session_id, claim_id=claim_id)
    relation_map = _safe_relation_map(ws, session_id)
    relation_conclusion = relation_map.get("current_conclusion", {}) if isinstance(relation_map, dict) else {}
    focus_reconciliation = (
        relation_map.get("active_claim_focus_reconciliation", {})
        if isinstance(relation_map, dict)
        else detect_active_claim_focus_drift(ws, session_id)
    )
    drift_detected = bool(
        (relation_map or {}).get("not_authoritative_for_current_goal_if_rebind_needed")
        if isinstance(relation_map, dict)
        else focus_reconciliation.get("not_authoritative_for_current_goal_if_rebind_needed")
    )
    warnings = ["active_claim_focus_drift_detected"] if drift_detected else []
    focus["can_say"] = relation_conclusion.get("can_say", []) if isinstance(relation_conclusion, dict) else []
    focus["cannot_say"] = relation_conclusion.get("cannot_say", []) if isinstance(relation_conclusion, dict) else []
    record_counts = _lightweight_slot_counts(ws, focus["topic_id"], focus["claim_id"])
    slots = [_slot_summary_from_counts(slot, record_counts) for slot in _FIRST_LEVEL_SLOT_ORDER]
    recommended_slots = _recommended_slots_from_counts(record_counts)
    if not recommended_slots:
        recommended_slots = ["source_asset", "reference_location", "proof_obligation", "evidence"]

    return {
        "ok": True,
        "kind": "recording_navigation_state",
        "navigation_mode": "lightweight_first_level",
        "session_id": focus["session_id"] or session_id,
        "requested_session_id": focus["requested_session_id"] or session_id,
        "recovery_selection_source": focus["recovery_selection_source"],
        "topic_id": focus["topic_id"],
        "claim_id": focus["claim_id"],
        "warnings": warnings,
        "active_claim_focus_reconciliation": focus_reconciliation,
        "current_position": focus,
        "first_level_slots": slots,
        "recommended_slots": recommended_slots,
        "graph_context": {
            "mode": "lightweight_slot_counts",
            "node_count": 0,
            "edge_count": 0,
            "record_counts": record_counts,
            "recommended_moments": _lightweight_recommended_moments(record_counts),
            "provenance_gaps": _lightweight_provenance_gaps(record_counts)[: max(1, min(limit, 20))],
            "open_obligations": _lightweight_open_obligation_hints(relation_map)[: max(1, min(limit, 20))],
            "route_state": {},
            "moment_policy": {
                "mode": "lightweight_first_level",
                "next_read_tool": "aitp_v5_expand_recording_slot",
                "agent_should_not_record_every_step": True,
            },
        },
        "brief_context": {
            "available": False,
            "current_focus": {
                "active_claim": focus["claim_id"],
                "active_route": focus["active_route"],
                "active_cycle": focus["active_cycle"],
                "claim_statement": focus["claim_statement"],
                "confidence_state": focus["confidence_state"],
                "evidence_profile": focus["evidence_profile"],
                "main_uncertainty": focus["main_uncertainty"],
            },
            "flow_profile": {},
            "evidence_coverage": {},
            "next_action_candidates": [],
            "forbidden_now": ["lightweight_navigation_state_does_not_replace_execution_brief"],
        },
        "relation_context": {
            "available": bool(relation_map and relation_map.get("kind") != "recording_navigation_error"),
            "relation_map_scope": (relation_map or {}).get("relation_map_scope", "active_claim_only"),
            "not_authoritative_for_current_goal_if_rebind_needed": drift_detected,
            "current_conclusion": (relation_map or {}).get("current_conclusion", {}),
            "current_blockers": (relation_map or {}).get("current_blockers", []),
            "next_valid_actions": (relation_map or {}).get("next_valid_actions", []),
        },
        "next_step": {
            "read_tool": "aitp_v5_expand_recording_slot",
            "write_boundary": "only the expanded deepest slot names the write/preflight tool",
            "verify_tool": "aitp_v5_verify_recording_effect",
        },
        "trust_boundary_reasons": [
            "recording_navigation_state is read-only",
            "recording_navigation_state uses lightweight first-level slot counts by default",
            "call process graph or execution brief separately when full graph context is needed",
            "slot expansion can recommend typed writes but cannot perform them",
            "active-claim focus drift warnings are read-only and cannot rebind without confirmation",
        ],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }

def expand_recording_slot(
    ws: WorkspacePaths,
    session_id: str,
    slot: str,
    *,
    claim_id: str = "",
    candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Expand one first-level recording slot into concrete write/preflight guidance."""

    normalized_slot = _clean_slot(slot)
    if normalized_slot not in _SLOT_EXPANSIONS:
        return _unknown_slot_expansion(session_id, slot)

    focus = _lightweight_focus(ws, session_id, claim_id=claim_id)
    expansion = deepcopy(_SLOT_EXPANSIONS[normalized_slot])
    expanded_required = _fill_known_field_hints(expansion["required_fields"], focus)
    expanded_optional = _fill_known_field_hints(expansion["optional_fields"], focus)
    candidate = dict(candidate or {})

    return {
        "ok": True,
        "kind": "recording_slot_expansion",
        "slot": normalized_slot,
        "navigation_mode": "lightweight_slot_expansion",
        "session_id": focus["session_id"] or session_id,
        "requested_session_id": focus["requested_session_id"] or session_id,
        "topic_id": focus["topic_id"],
        "claim_id": focus["claim_id"],
        "recommended_write_tool": expansion["recommended_write_tool"],
        "cli_template": expansion["cli_template"],
        "record_kind": expansion["record_kind"],
        "required_fields": expanded_required,
        "optional_fields": expanded_optional,
        "recommended_links": expansion["recommended_links"],
        "graph_edges_created": expansion["graph_edges_created"],
        "when_to_use": expansion["when_to_use"],
        "candidate_context": {
            "event_type": str(candidate.get("event_type") or ""),
            "decision": str(candidate.get("decision") or ""),
            "suggested_slots": list(candidate.get("suggested_slots") or []),
            "candidate_refs": list(candidate.get("candidate_refs") or candidate.get("touched_refs") or []),
            "produced_artifacts": list(candidate.get("produced_artifacts") or []),
        },
        "recording_sequence": [
            "read recording_navigation_state",
            "expand one slot",
            "call the recommended existing typed write/preflight tool with complete fields",
            "call aitp_v5_verify_recording_effect with expected refs or before graph ids",
        ],
        "trust_effect": {
            "writes_kernel_state": bool(expansion["writes_kernel_state"]),
            "can_update_claim_trust": False,
            "claim_trust_mutation": "none",
            "trust_preflight_required_for_trust_change": normalized_slot == "trust_preflight",
        },
        "warnings": _slot_warnings(normalized_slot),
        "verify_with": "aitp_v5_verify_recording_effect",
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }

def verify_recording_effect(
    ws: WorkspacePaths,
    session_id: str,
    *,
    expected_refs: list[str] | None = None,
    before_node_ids: list[str] | None = None,
    before_edge_ids: list[str] | None = None,
    claim_id: str = "",
    limit: int = 80,
) -> dict[str, Any]:
    """Read back typed records and graph deltas after a write step."""

    expected_refs = _clean_list(expected_refs)
    before_node_ids = _clean_list(before_node_ids)
    before_edge_ids = _clean_list(before_edge_ids)
    ref_lookup = lookup_record_refs(ws, expected_refs)
    graph = build_process_graph_slice(ws, session_id, claim_id=claim_id, limit=limit)
    node_ids = {str(node.get("id")) for node in graph.get("nodes", [])}
    edge_ids = {str(edge.get("id")) for edge in graph.get("edges", [])}
    new_node_ids = sorted(node_ids - set(before_node_ids)) if before_node_ids else []
    new_edge_ids = sorted(edge_ids - set(before_edge_ids)) if before_edge_ids else []
    found_refs = [item["ref"] for item in ref_lookup["refs"] if item["status"] == "found"]
    missing_refs = [item["ref"] for item in ref_lookup["refs"] if item["status"] != "found"]
    verified = (not expected_refs or not missing_refs) and (not before_node_ids or bool(new_node_ids) or bool(found_refs))

    return {
        "ok": True,
        "kind": "recording_effect_verification",
        "verified": verified,
        "session_id": graph.get("session_id") or session_id,
        "requested_session_id": graph.get("requested_session_id", session_id),
        "topic_id": graph.get("topic_id", ""),
        "claim_id": graph.get("claim_id", claim_id),
        "expected_refs": expected_refs,
        "found_refs": found_refs,
        "missing_refs": missing_refs,
        "record_ref_lookup": ref_lookup,
        "graph_delta": {
            "before_node_count": len(before_node_ids),
            "after_node_count": len(node_ids),
            "new_node_ids": new_node_ids,
            "before_edge_count": len(before_edge_ids),
            "after_edge_count": len(edge_ids),
            "new_edge_ids": new_edge_ids,
        },
        "current_recommended_slots": _recommended_slots_from_graph(graph),
        "failure_reasons": _verification_failures(expected_refs, missing_refs, before_node_ids, new_node_ids, found_refs),
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }

def recording_slot_names() -> list[str]:
    return list(_FIRST_LEVEL_SLOT_ORDER)

def _decision_for_event(
    event_type: str,
    summary: str,
    risk_hint: str,
    touched_refs: list[str],
    produced_artifacts: list[str],
    tool_call_id: str,
) -> str:
    lowered = " ".join([event_type, summary, risk_hint]).lower()
    if event_type in _TRUST_CHANGING_EVENT_TYPES or "trust" in lowered or "promote" in lowered or "confidence" in lowered:
        return DECISION_CHECKPOINT
    if event_type in _NAVIGATION_EVENT_TYPES:
        if event_type in _DEFER_EVENT_TYPES and not touched_refs and not produced_artifacts and not tool_call_id:
            return DECISION_DEFER
        return DECISION_NAVIGATE
    if touched_refs or produced_artifacts or tool_call_id:
        return DECISION_NAVIGATE
    if "without durable" in lowered or "no durable" in lowered:
        return DECISION_DEFER
    if any(token in lowered for token in ("maybe later", "brainstorm", "casual", "explain", "explanation", "question")):
        return DECISION_DEFER
    if any(token in lowered for token in ("evidence", "validation", "proof", "gap", "artifact", "source", "claim", "result")):
        return DECISION_NAVIGATE
    return DECISION_IGNORE

def _suggested_slots(
    event_type: str,
    summary: str,
    touched_refs: list[str],
    produced_artifacts: list[str],
    tool_call_id: str,
) -> list[str]:
    slots = list(_EVENT_SLOT_HINTS.get(event_type, []))
    lowered = summary.lower()
    if touched_refs:
        slots.extend(["reference_location", "source_asset"])
    if produced_artifacts:
        slots.extend(["artifact", "source_asset"])
    if tool_call_id:
        slots.extend(["tool_run", "code_state"])
    if "validation" in lowered or "checked" in lowered or "passed" in lowered or "failed" in lowered:
        slots.extend(["validation_result", "evidence"])
    if "proof" in lowered or "gap" in lowered or "missing" in lowered:
        slots.append("proof_obligation")
    if "route" in lowered or "pivot" in lowered or "abandon" in lowered:
        slots.append("research_route")
    return _unique_slots(slots)

def _trigger_reasons(
    event_type: str,
    summary: str,
    risk_hint: str,
    touched_refs: list[str],
    produced_artifacts: list[str],
    tool_call_id: str,
) -> list[str]:
    reasons: list[str] = []
    if event_type in _RECORDING_EVENT_TYPES:
        reasons.append(f"recognized event_type:{event_type}")
    if event_type in _TRUST_CHANGING_EVENT_TYPES:
        reasons.append("trust-changing event requires checkpoint/preflight navigation")
    if touched_refs:
        reasons.append("candidate includes touched typed/source refs")
    if produced_artifacts:
        reasons.append("candidate includes produced artifacts")
    if tool_call_id:
        reasons.append("candidate includes a tool call id")
    lowered = " ".join([summary, risk_hint]).lower()
    for token in ("evidence", "validation", "proof", "gap", "artifact", "source", "claim", "result", "trust"):
        if token in lowered:
            reasons.append(f"summary_or_risk_mentions:{token}")
    return list(dict.fromkeys(reasons))

def _next_read_tool(decision: str) -> str:
    if decision == DECISION_NAVIGATE:
        return "aitp_v5_get_recording_navigation_state"
    if decision == DECISION_CHECKPOINT:
        return "aitp_v5_expand_recording_slot"
    if decision == DECISION_DEFER:
        return "aitp_v5_get_recording_navigation_state"
    return ""

def _clean_event_type(event_type: str) -> str:
    return str(event_type or "").strip().lower().replace("-", "_").replace(" ", "_")

def _clean_slot(slot: str) -> str:
    return str(slot or "").strip().lower().replace("-", "_").replace(" ", "_")

def _clean_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return [str(value).strip() for value in values if str(value).strip()]

def _unique_slots(slots: list[str]) -> list[str]:
    seen: set[str] = set()
    clean: list[str] = []
    for slot in slots:
        normalized = _clean_slot(slot)
        if normalized in _SLOT_EXPANSIONS and normalized not in seen:
            seen.add(normalized)
            clean.append(normalized)
    return clean

def _safe_brief(ws: WorkspacePaths, session_id: str) -> dict[str, Any]:
    try:
        return build_execution_brief(ws, session_id)
    except (FileNotFoundError, TypeError, ValueError, OSError) as error:
        return {
            "kind": "recording_navigation_error",
            "surface": "execution_brief",
            "reason": str(error) or error.__class__.__name__,
        }

def _safe_relation_map(ws: WorkspacePaths, session_id: str) -> dict[str, Any]:
    try:
        return build_claim_relation_map(ws, session_id)
    except (FileNotFoundError, TypeError, ValueError, OSError) as error:
        return {
            "kind": "recording_navigation_error",
            "surface": "claim_relation_map",
            "reason": str(error) or error.__class__.__name__,
        }

def _lightweight_focus(ws: WorkspacePaths, session_id: str, *, claim_id: str) -> dict[str, Any]:
    try:
        recovered = recover_session_binding_for_read(ws, session_id)
        session = recovered.session
        focus_claim_id = str(claim_id or session.active_claim or "")
        claim = get_claim(ws, focus_claim_id) if focus_claim_id else None
        return {
            "requested_session_id": recovered.requested_session_id,
            "recovery_selection_source": recovered.recovery_selection_source,
            "session_id": session.session_id,
            "topic_id": session.topic_id,
            "claim_id": focus_claim_id,
            "active_route": session.active_route,
            "active_cycle": session.active_cycle,
            "claim_statement": claim.statement if claim else "",
            "confidence_state": claim.confidence_state if claim else "",
            "evidence_profile": claim.evidence_profile if claim else "",
            "main_uncertainty": claim.active_uncertainty if claim else "",
            "can_say": [],
            "cannot_say": [],
        }
    except (FileNotFoundError, TypeError, ValueError, OSError):
        return {
            "requested_session_id": session_id,
            "recovery_selection_source": "unbound_session",
            "session_id": session_id,
            "topic_id": "unbound-session",
            "claim_id": claim_id,
            "active_route": "",
            "active_cycle": "",
            "claim_statement": "",
            "confidence_state": "",
            "evidence_profile": "",
            "main_uncertainty": "",
            "can_say": [],
            "cannot_say": [],
        }

def _focus_from_surfaces(
    graph: dict[str, Any],
    brief: dict[str, Any] | None,
    relation_map: dict[str, Any] | None,
    claim_id: str,
) -> dict[str, Any]:
    recovered = (brief or {}).get("recovered_focus", {}) if isinstance(brief, dict) else {}
    current_focus = (brief or {}).get("current_focus", {}) if isinstance(brief, dict) else {}
    relation_conclusion = (relation_map or {}).get("current_conclusion", {}) if isinstance(relation_map, dict) else {}
    return {
        "session_id": str(graph.get("session_id") or recovered.get("session_id") or ""),
        "topic_id": str(graph.get("topic_id") or recovered.get("topic_id") or ""),
        "claim_id": str(claim_id or graph.get("claim_id") or recovered.get("active_claim") or current_focus.get("active_claim") or ""),
        "active_route": str(recovered.get("active_route") or current_focus.get("active_route") or ""),
        "active_cycle": str(recovered.get("active_cycle") or current_focus.get("active_cycle") or ""),
        "claim_statement": str(recovered.get("claim_statement") or current_focus.get("claim_statement") or ""),
        "confidence_state": str(recovered.get("confidence_state") or ""),
        "evidence_profile": str(recovered.get("evidence_profile") or ""),
        "main_uncertainty": str(current_focus.get("main_uncertainty") or ""),
        "can_say": relation_conclusion.get("can_say", []) if isinstance(relation_conclusion, dict) else [],
        "cannot_say": relation_conclusion.get("cannot_say", []) if isinstance(relation_conclusion, dict) else [],
    }

def _lightweight_slot_counts(ws: WorkspacePaths, topic_id: str, claim_id: str) -> dict[str, int]:
    counts = {slot: 0 for slot in _SLOT_COUNT_FAMILIES}
    counts["trust_preflight"] = 0
    if not topic_id:
        return counts
    for slot, family in _SLOT_COUNT_FAMILIES.items():
        root = ws.registry_dir(family)
        if not root.exists():
            continue
        for path in root.glob("*.md"):
            try:
                frontmatter, _body = read_md(path)
            except (OSError, TypeError, ValueError):
                continue
            record_topic = str(frontmatter.get("topic_id") or frontmatter.get("topic") or "")
            if record_topic != topic_id:
                continue
            record_claim = str(
                frontmatter.get("claim_id")
                or frontmatter.get("active_claim_id")
                or frontmatter.get("source_claim_id")
                or ""
            )
            if claim_id and record_claim and record_claim != claim_id:
                continue
            counts[slot] = counts.get(slot, 0) + 1
    return counts

def _slot_summary_from_counts(slot: str, counts: dict[str, int]) -> dict[str, Any]:
    expansion = _SLOT_EXPANSIONS[slot]
    count_key = expansion["record_kind"]
    if count_key == "trust_update_preflight":
        current_count = 0
    else:
        current_count = int(counts.get(slot, counts.get(count_key, 0)) or 0)
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

def _recommended_slots_from_counts(counts: dict[str, int]) -> list[str]:
    slots: list[str] = []
    for slot in (
        "reference_location",
        "source_asset",
        "code_state",
        "artifact",
        "evidence",
        "proof_obligation",
        "source_reconstruction_review",
        "validation_contract",
        "validation_result",
    ):
        if int(counts.get(slot, 0) or 0) == 0:
            slots.append(slot)
    return _unique_slots(slots)
