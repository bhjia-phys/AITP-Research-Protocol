# Compatibility shard 2 for codex_facade.
from __future__ import annotations

def codex_expand_context(
    ws: WorkspacePaths,
    *,
    session_id: str,
    expansion: str,
    claim_id: str = "",
    max_lines: int = 60,
    limit: int = 60,
    style: str = "jhep",
    objective_text: str = "",
    user_goal: str = "",
    record_refs: list[str] | tuple[str, ...] | None = None,
    offset: int = 0,
) -> dict[str, Any]:
    """Expand one Codex context family on demand."""

    selected = _expansion_name(expansion)
    payload: dict[str, Any] = {
        "ok": True,
        "kind": "codex_context_expansion",
        "session_id": session_id,
        "expansion": selected,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    if selected == "context_pack":
        payload["surface"] = build_aitp_context_pack(
            ws,
            session_id,
            max_lines=max_lines,
            objective_text=objective_text,
            user_goal=user_goal,
        )
    elif selected == "brief":
        payload["surface"] = build_execution_brief(ws, session_id)
    elif selected == "relation_map":
        payload["surface"] = build_claim_relation_map(
            ws,
            session_id,
            objective_text=objective_text,
            user_goal=user_goal,
        )
    elif selected == "timeline":
        payload["surface"] = build_research_timeline(ws, session_id, claim_id=claim_id, limit=limit)
    elif selected == "process_graph":
        payload["surface"] = build_process_graph_slice(ws, session_id, claim_id=claim_id, limit=limit)
    elif selected == "recording_navigation":
        payload["surface"] = build_recording_navigation_state(ws, session_id, claim_id=claim_id, limit=limit)
    elif selected == "note_outline":
        payload["surface"] = compile_note_outline(ws, session_id, style=style, candidate_limit=min(limit, 12))
    elif selected == "source_reconstruction":
        if not claim_id:
            return _needs_claim_id(selected)
        payload["surface"] = audit_source_reconstruction(ws, claim_id=claim_id)
    elif selected == "trust_audit":
        if not claim_id:
            return _needs_claim_id(selected)
        payload["surface"] = audit_claim_trust(ws, claim_id=claim_id)
    elif selected == "record_refs":
        payload["surface"] = _expand_record_refs(
            ws,
            refs=record_refs or (),
            offset=offset,
            limit=limit,
        )
        if not payload["surface"]["ok"]:
            payload["ok"] = False
    else:
        payload["ok"] = False
        payload["error"] = f"unsupported expansion: {expansion}"
        payload["allowed_expansions"] = _allowed_expansions()
    return payload

def codex_recording_step(
    ws: WorkspacePaths,
    *,
    session_id: str,
    event_type: str,
    summary: str = "",
    topic_id: str = "",
    claim_id: str = "",
    touched_refs: list[str] | None = None,
    produced_artifacts: list[str] | None = None,
    tool_call_id: str = "",
    risk_hint: str = "",
    slot: str = "",
    candidate: dict[str, Any] | None = None,
    expected_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Classify and navigate one durable recording moment without doing the write."""

    classification = classify_recording_candidate(
        ws,
        session_id=session_id,
        event_type=event_type,
        summary=summary,
        topic_id=topic_id,
        claim_id=claim_id,
        touched_refs=touched_refs,
        produced_artifacts=produced_artifacts,
        tool_call_id=tool_call_id,
        risk_hint=risk_hint,
        payload=candidate,
    )
    payload: dict[str, Any] = {
        "ok": True,
        "kind": "codex_recording_step",
        "session_id": session_id,
        "classification": classification,
        "write_executed": False,
        "recording_policy": {
            "agent_should_not_record_every_step": True,
            "classification_writes": False,
            "navigation_writes": False,
            "slot_expansion_writes": False,
            "deepest_layer_write_tool": "aitp_v5_codex_record_apply",
        },
        "truth_source": "typed_records_and_event_metadata",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    try:
        focus = recover_session_binding_for_read(ws, session_id)
        session = focus.session
        plan_topic_id = topic_id or session.topic_id
        payload["lightweight_record_write_plan"] = require_valid_public_surface(
            "lightweight_record_write_plan",
            plan_lightweight_record_write(
                ws,
                topic_id=plan_topic_id,
                current_session_id=session.session_id,
                event_summary=summary,
                active_claim_id=session.active_claim,
                target_claim_hint=claim_id,
                touched_files_or_artifacts=_recording_artifact_inputs(touched_refs, produced_artifacts),
                touched_tool_runs_or_evidence_refs=_recording_evidence_ref_inputs(touched_refs),
                risk_hint=risk_hint,
            ),
        )
    except Exception as exc:
        payload["lightweight_record_write_plan_error"] = f"{type(exc).__name__}: {exc}"
    decision = classification.get("decision")
    if decision in {"navigate", "checkpoint"}:
        payload["navigation_state"] = build_recording_navigation_state(
            ws,
            session_id,
            claim_id=claim_id,
        )
    if slot:
        slot_candidate = dict(candidate or {})
        slot_candidate.setdefault("event_type", event_type)
        slot_candidate.setdefault("decision", decision)
        slot_candidate.setdefault("suggested_slots", classification.get("suggested_slots", []))
        slot_candidate.setdefault("candidate_refs", touched_refs or [])
        slot_candidate.setdefault("produced_artifacts", produced_artifacts or [])
        payload["slot_expansion"] = expand_recording_slot(
            ws,
            session_id,
            slot,
            claim_id=claim_id,
            candidate=slot_candidate,
        )
        payload["recommended_write_tool"] = payload["slot_expansion"].get("recommended_write_tool", "")
    if expected_refs:
        payload["verification"] = verify_recording_effect(
            ws,
            session_id,
            expected_refs=expected_refs,
            claim_id=claim_id,
        )
    return payload

def _entry_payload_profile(payload_profile: str) -> str:
    clean = str(payload_profile or "minimal").strip().lower().replace("-", "_")
    aliases = {
        "": "minimal",
        "light": "minimal",
        "lite": "minimal",
        "card": "minimal",
        "entry_card": "minimal",
        "minimal_card": "minimal",
        "compact": "minimal",
        "full": "context_pack",
        "legacy": "context_pack",
        "context": "context_pack",
    }
    return aliases.get(clean, clean if clean in {"minimal", "context_pack"} else "minimal")

def _build_codex_entry_card(
    ws: WorkspacePaths,
    session_id: str,
    *,
    request_summary: str,
    process_mode: str,
    max_lines: int,
) -> dict[str, Any]:
    compact = build_compact_brief(
        ws,
        session_id,
        max_lines=min(max(8, int(max_lines or 12)), 14),
        user_goal=request_summary,
    )
    objective = compact.get("current_objective") if isinstance(compact.get("current_objective"), dict) else {}
    package = compact.get("active_work_package") if isinstance(compact.get("active_work_package"), dict) else {}
    relevant_claims = [
        {
            "claim_id": str(claim.get("claim_id") or ""),
            "statement": _excerpt(str(claim.get("statement") or ""), limit=140),
        }
        for claim in list(compact.get("relevant_claims") or [])[:3]
        if isinstance(claim, dict)
    ]
    previous_failed = [
        {
            "record_ref": str(item.get("record_ref") or ""),
            "classification": str(item.get("classification") or ""),
            "summary": _excerpt(str(item.get("summary") or ""), limit=120),
        }
        for item in list(compact.get("previous_failed_attempts") or [])[:2]
        if isinstance(item, dict)
    ]
    card = {
        "ok": True,
        "kind": "codex_entry_card",
        "session_id": str(compact.get("session_id") or session_id),
        "topic_id": str(compact.get("topic_id") or ""),
        "process_mode": process_mode,
        "current_objective": {
            "title": _excerpt(str(objective.get("title") or compact.get("topic_id") or ""), limit=140),
            "objective_id": str(objective.get("objective_id") or ""),
        },
        "active_work_package": {
            "title": _excerpt(str(package.get("title") or ""), limit=140),
            "work_package_id": str(package.get("work_package_id") or ""),
        },
        "relevant_claims": relevant_claims,
        "boundary": {
            "can_say": [_excerpt(str(item), limit=160) for item in list(compact.get("can_say") or [])[:3]],
            "cannot_say": [_excerpt(str(item), limit=160) for item in list(compact.get("cannot_say") or [])[:3]],
            "relation_map_scope": str(compact.get("relation_map_scope") or "active_claim_only"),
        },
        "blockers": [_excerpt(str(item), limit=160) for item in list(compact.get("blockers") or [])[:3]],
        "previous_failed_attempts": previous_failed,
        "next_valid_actions": [_excerpt(str(item), limit=160) for item in list(compact.get("next_valid_actions") or [])[:4]],
        "warnings": [_excerpt(str(item), limit=160) for item in list(compact.get("warnings") or [])[:3]],
        "model_policy": {
            "orientation_only": True,
            "answer_within_card_boundary": True,
            "expand_before_claim_truth_or_validation": True,
            "do_not_record_from_entry_card": True,
            "do_not_update_claim_trust": True,
        },
        "recommended_expansions": _expansions_for_mode(process_mode),
        "expand": {
            "context_pack": {"tool": "aitp_v5_codex_expand", "arguments": {"expansion": "context_pack"}},
            "timeline": {"tool": "aitp_v5_codex_expand", "arguments": {"expansion": "timeline"}},
            "relation_map": {"tool": "aitp_v5_codex_expand", "arguments": {"expansion": "relation_map"}},
            "brief": {"tool": "aitp_v5_codex_expand", "arguments": {"expansion": "brief"}},
        },
        "source_records": compact.get("source_records") or {},
        "truth_source": "typed_records_derived_entry_card_not_evidence",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    card["line_count"] = len(_entry_card_lines(card))
    card["lines"] = _entry_card_lines(card)
    return card

def _entry_card_lines(card: dict[str, Any]) -> list[str]:
    objective = card.get("current_objective") or {}
    package = card.get("active_work_package") or {}
    lines = [
        f"Session: {card.get('session_id')} | Topic: {card.get('topic_id')}",
        f"Objective: {objective.get('title') or 'unknown'}",
        f"Work package: {package.get('title') or 'none'}",
        "Boundary: orientation-only; expand before claim truth, evidence, validation, or trust-sensitive decisions.",
    ]
    blockers = list(card.get("blockers") or [])
    if blockers:
        lines.append(f"Blockers: {'; '.join(blockers[:2])}")
    next_actions = list(card.get("next_valid_actions") or [])
    if next_actions:
        lines.append(f"Next: {'; '.join(next_actions[:2])}")
    failed = list(card.get("previous_failed_attempts") or [])
    if failed:
        lines.append(
            "Prior failed/superseded: "
            + "; ".join(_excerpt(str(item.get("summary") or item.get("record_ref") or ""), limit=90) for item in failed[:2])
        )
    return lines

def _excerpt(value: str, *, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."

def _recording_artifact_inputs(touched_refs: list[str] | None, produced_artifacts: list[str] | None) -> list[str]:
    values = [_normalize_artifact_uri(str(value).strip()) for value in (produced_artifacts or []) if str(value).strip()]
    for ref in touched_refs or []:
        text = str(ref).strip()
        if text.startswith("artifact:"):
            values.append(text)
        else:
            normalized = _normalize_artifact_uri(text)
            if normalized != text:
                values.append(normalized)
    return values

def _recording_evidence_ref_inputs(touched_refs: list[str] | None) -> list[str]:
    evidence_prefixes = ("tool_run:", "validation_result:", "evidence:")
    return [
        str(ref).strip()
        for ref in (touched_refs or [])
        if str(ref).strip().startswith(evidence_prefixes)
    ]

def codex_literature_step(
    ws: WorkspacePaths,
    *,
    session_id: str,
    uri: str,
    label: str,
    action: str = "suggest",
    external_id: str = "",
    short_summary: str = "",
    detected_relevance: str = "",
    optional_claim_id: str = "",
    scoped_output: str = "",
    reviewed_refs: list[str] | None = None,
    comparison_question: str = "",
    source_refs: list[str] | None = None,
    dimensions: list[str] | None = None,
    rationale: str = "",
    asset_type: str = "",
) -> dict[str, Any]:
    """Run one literature/reference workflow layer from Codex."""

    selected = _literature_action(action)
    common = {
        "session_id": session_id,
        "uri": uri,
        "label": label,
        "external_id": external_id,
        "short_summary": short_summary,
        "detected_relevance": detected_relevance,
        "optional_claim_id": optional_claim_id,
        "scoped_output": scoped_output,
    }
    intake_common = {**common, "asset_type": asset_type}
    payload: dict[str, Any] = {
        "ok": True,
        "kind": "codex_literature_step",
        "action": selected,
        "reference_layers": _reference_layers(),
        "truth_source": "typed_records_and_agent_supplied_literature_metadata",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }
    if selected == "suggest":
        payload["surface"] = suggest_literature_intake(ws, **intake_common)
        payload["orientation_only"] = True
        payload["can_update_kernel_state"] = False
    elif selected == "record_reference":
        payload["surface"] = record_literature_candidate(ws, **intake_common)
        payload["recorded_source_asset"] = payload["surface"].get("recorded_source_asset", {})
        payload["recorded_reference_location"] = payload["surface"].get("recorded_reference_location", {})
        payload["orientation_only"] = False
        payload["can_update_kernel_state"] = True
        payload["kernel_state_change"] = "source_asset_and_reference_location_records"
    elif selected == "source_review_handoff":
        payload["surface"] = build_literature_source_review_handoff(
            ws,
            **common,
            reviewed_refs=reviewed_refs or [],
        )
        payload["orientation_only"] = True
        payload["can_update_kernel_state"] = False
    elif selected == "comparison_draft":
        payload["surface"] = build_literature_comparison_draft(
            ws,
            session_id=session_id,
            comparison_question=comparison_question,
            source_refs=source_refs or [],
            dimensions=dimensions or [],
            optional_claim_id=optional_claim_id,
            rationale=rationale,
        )
        payload["orientation_only"] = True
        payload["can_update_kernel_state"] = False
    else:
        payload["ok"] = False
        payload["error"] = f"unsupported literature action: {action}"
        payload["allowed_actions"] = _allowed_literature_actions()
        payload["orientation_only"] = True
        payload["can_update_kernel_state"] = False
    return payload

def codex_closeout(
    ws: WorkspacePaths,
    *,
    session_id: str,
    summary: str,
    apply: bool = False,
    claim_id: str = "",
    run_id: str = "",
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    changed_files: list[str] | None = None,
    generated_artifacts: list[dict] | None = None,
    validation_commands: list[str] | None = None,
    durable_observations: list[str] | None = None,
    claim_boundary: dict | None = None,
    next_blockers: list[str] | None = None,
    artifact_specs: list[dict] | None = None,
    source_specs: list[dict] | None = None,
    tool_run_specs: list[dict] | None = None,
    sensemaking_summary: str = "",
    source_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Preview or apply a session closeout checkpoint without trust mutation."""

    kwargs = {
        "claim_id": claim_id,
        "run_id": run_id,
        "summary": summary,
        "inputs": inputs,
        "outputs": outputs,
        "changed_files": changed_files,
        "generated_artifacts": generated_artifacts,
        "validation_commands": validation_commands,
        "durable_observations": durable_observations,
        "claim_boundary": claim_boundary,
        "next_blockers": next_blockers,
        "artifact_specs": artifact_specs,
        "source_specs": source_specs,
        "tool_run_specs": tool_run_specs,
        "sensemaking_summary": sensemaking_summary,
        "source_refs": source_refs,
    }
    surface = (
        apply_quiet_checkpoint_batch(ws, session_id, **kwargs)
        if apply
        else preview_quiet_checkpoint_batch(ws, session_id, **kwargs)
    )
    record_completeness_audit = surface.get("record_completeness_audit", {})
    return {
        "ok": True,
        "kind": "codex_closeout",
        "mode": "apply" if apply else "preview",
        "session_id": session_id,
        "surface": surface,
        "record_completeness_audit": record_completeness_audit,
        "missing_recommended_slots": record_completeness_audit.get("missing_recommended_slots", []),
        "recommended_next_records": record_completeness_audit.get("recommended_next_records", []),
        "write_executed": bool(apply),
        "kernel_state_change": "quiet_checkpoint_batch" if apply else "none",
        "trust_update_forbidden": True,
        "truth_source": "typed_records_and_closeout_summary",
        "summary_inputs_trusted": False,
        "orientation_only": not apply,
        "can_update_kernel_state": bool(apply),
        "can_update_claim_trust": False,
    }
