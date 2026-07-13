# Compatibility shard 3 for lightweight_record_router.
from __future__ import annotations

def plan_lightweight_record_write(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    current_session_id: str,
    event_summary: str,
    active_claim_id: str = "",
    target_claim_hint: str = "",
    touched_files_or_artifacts: list[str] | None = None,
    touched_tool_runs_or_evidence_refs: list[str] | None = None,
    risk_hint: str = "",
) -> dict[str, Any]:
    """Return a plan-only payload describing what records *would* be written.

    Reads typed records + the event summary; never writes anything; never
    applies trust. See module docstring for the hard trust boundaries.
    """

    if not topic_id or not current_session_id or not (event_summary or "").strip():
        return _no_write_payload(
            topic_id=topic_id,
            current_session_id=current_session_id,
            active_claim_id=active_claim_id,
            reason="missing_required_input_topic_session_or_event_summary",
        )

    event_lower = _lower(event_summary)
    risk_lower = _lower(risk_hint)

    touched_files = [
        _classify_touched(v) for v in (touched_files_or_artifacts or []) if (v or "").strip()
    ]
    touched_refs_raw = [v for v in (touched_tool_runs_or_evidence_refs or []) if (v or "").strip()]

    # validate canonical input refs via the existing read-only lookup
    touched_ref_like = [
        t["value"] for t in touched_files
        if t["kind"] in {"canonical_ref", "ref_like"}
    ]
    canonical_input_refs = [t["value"] for t in touched_files if t["kind"] == "canonical_ref"]
    all_input_refs = touched_ref_like + touched_refs_raw
    ref_lookup = lookup_record_refs(ws, all_input_refs) if all_input_refs else None
    confirmed_refs: set[str] = set()
    malformed_refs: list[str] = []
    unconfirmed_evidence_refs: list[str] = []  # tool_run/validation_result refs that don't confirm
    unsupported_refs: list[str] = []
    missing_non_evidence_refs: list[str] = []
    artifact_claim_map: dict[str, str] = {}  # artifact:<id> -> claim_id (from confirmed records)
    if ref_lookup is not None:
        for item in ref_lookup.get("refs", []):
            ref = item.get("ref", "")
            status = item.get("status")
            kind = item.get("ref_kind", "")
            if status == "found":
                confirmed_refs.add(ref)
                if kind == "artifact":
                    claim_from_record = str(item.get("claim_id", "") or "")
                    if claim_from_record:
                        artifact_claim_map[ref] = claim_from_record
            elif status == "malformed_ref":
                malformed_refs.append(ref)
            elif kind in {"tool_run", "validation_result"}:
                # not_found / unsupported_kind for an evidence-grade ref: cannot plan evidence
                unconfirmed_evidence_refs.append(ref)
            elif status == "unsupported_kind":
                unsupported_refs.append(ref)
            elif status == "not_found":
                missing_non_evidence_refs.append(ref)

    if malformed_refs:
        return {
            "ok": True,
            "kind": "lightweight_record_write_plan",
            "decision": DECISION_UNSUPPORTED,
            "topic_id": topic_id,
            "current_session_id": current_session_id,
            "active_claim_id": active_claim_id,
            "target_claim": {
                "target_claim_id": "",
                "reason_for_target_claim": "malformed input ref",
                "confidence": "low",
            },
            "write_reasons": [],
            "no_write_reason": "",
            "selected_record_types": [],
            "typed_write_plan": [],
            "trust_boundary": dict(_TRUST_BOUNDARY),
            "final_human_readable_summary": (
                f"Malformed input ref(s) rejected: {malformed_refs}. Nothing recorded."
            ),
            **_TOP_LEVEL_TRUTH,
        }

    if unconfirmed_evidence_refs:
        return {
            "ok": True,
            "kind": "lightweight_record_write_plan",
            "decision": DECISION_UNSUPPORTED,
            "topic_id": topic_id,
            "current_session_id": current_session_id,
            "active_claim_id": active_claim_id,
            "target_claim": {
                "target_claim_id": "",
                "reason_for_target_claim": "unconfirmed evidence-grade ref",
                "confidence": "low",
            },
            "write_reasons": [],
            "no_write_reason": "",
            "selected_record_types": [],
            "typed_write_plan": [],
            "trust_boundary": dict(_TRUST_BOUNDARY),
            "final_human_readable_summary": (
                "Evidence-grade ref(s) did not resolve to a typed record, so no evidence "
                f"plan is produced and nothing is recorded: {unconfirmed_evidence_refs}. "
                "Create the tool_run/validation_result first, or supply a confirmed ref."
            ),
            **_TOP_LEVEL_TRUTH,
        }

    if unsupported_refs or missing_non_evidence_refs:
        diagnostics = []
        if unsupported_refs:
            diagnostics.append(f"unsupported ref kind(s): {unsupported_refs}")
        if missing_non_evidence_refs:
            diagnostics.append(f"missing typed record ref(s): {missing_non_evidence_refs}")
        return {
            "ok": True,
            "kind": "lightweight_record_write_plan",
            "decision": DECISION_UNSUPPORTED,
            "topic_id": topic_id,
            "current_session_id": current_session_id,
            "active_claim_id": active_claim_id,
            "target_claim": {
                "target_claim_id": "",
                "reason_for_target_claim": "unresolved or unsupported input ref",
                "confidence": "low",
            },
            "write_reasons": [],
            "no_write_reason": "",
            "selected_record_types": [],
            "typed_write_plan": [],
            "trust_boundary": dict(_TRUST_BOUNDARY),
            "final_human_readable_summary": (
                "Input ref(s) could not be resolved by the typed-record lookup surface; "
                f"{'; '.join(diagnostics)}. Nothing recorded."
            ),
            **_TOP_LEVEL_TRUTH,
        }

    # ---- decide write vs no_write -----------------------------------------
    wants_artifact = _wants_artifact(event_lower, touched_files)
    wants_sensemaking = _wants_sensemaking(event_lower, touched_files)
    wants_gap = _wants_proof_obligation(event_lower)
    wants_negative = _wants_negative(event_lower)
    wants_trust = _wants_trust(event_lower, risk_lower)
    is_runtime_failure = _has_runtime_failure(event_lower)

    verified_refs = _has_tool_run_or_validation_ref(touched_refs_raw + canonical_input_refs, confirmed_refs)
    wants_evidence = bool(verified_refs)

    any_trigger = any(
        [wants_artifact, wants_sensemaking, wants_gap, wants_negative, wants_evidence, wants_trust]
    )

    if not any_trigger:
        return _no_write_payload(
            topic_id=topic_id,
            current_session_id=current_session_id,
            active_claim_id=active_claim_id,
            reason="ordinary_chat_or_repeat_summary_without_durable_research_event",
        )

    # ---- target claim selection -------------------------------------------
    target = _choose_target_claim(
        ws,
        topic_id=topic_id,
        event_summary=event_summary,
        active_claim_id=active_claim_id,
        target_claim_hint=target_claim_hint,
        artifact_claim_map=artifact_claim_map,
    )
    target_claim_id = target["target_claim_id"]

    if not target_claim_id:
        # artifact-only without a claim still needs a claim binding (ArtifactRecord requires claim_id)
        reason = (
            "target claim unclear; artifact/sensemaking records require claim binding"
            if target.get("needs_human")
            else "target claim unclear"
        )
        return {
            "ok": True,
            "kind": "lightweight_record_write_plan",
            "decision": DECISION_NEEDS_HUMAN,
            "topic_id": topic_id,
            "current_session_id": current_session_id,
            "active_claim_id": active_claim_id,
            "target_claim": {
                "target_claim_id": "",
                "reason_for_target_claim": target["reason_for_target_claim"],
                "confidence": target["confidence"],
            },
            "write_reasons": [],
            "no_write_reason": "",
            "selected_record_types": [],
            "typed_write_plan": [],
            "trust_boundary": dict(_TRUST_BOUNDARY),
            "final_human_readable_summary": (
                f"Needs human target-claim decision: {target['reason_for_target_claim']}. "
                "Nothing recorded."
            ),
            **_TOP_LEVEL_TRUTH,
        }

    # ---- build the typed write plan ---------------------------------------
    write_plan: list[dict[str, Any]] = []
    selected_types: list[str] = []

    # Existing canonical artifact refs are preserved as verification_refs on later
    # plan items (sensemaking/proof/evidence/trust) so provenance is not silently
    # dropped. They are NOT re-attached as a second artifact plan.
    existing_artifact_refs = [
        t["value"] for t in touched_files
        if t["kind"] == "canonical_ref" and t["value"] in confirmed_refs
        and _split_ref(t["value"])[0] == "artifact"
    ]
    path_entries = [t for t in touched_files if t["kind"] == "path"]

    if wants_artifact:
        # one artifact plan per path; canonical refs are preserved as verification
        # refs on later items, not re-attached as a second artifact plan.
        if path_entries:
            write_plan.append(_artifact_plan(
                topic_id=topic_id,
                target_claim_id=target_claim_id,
                event_summary=event_summary,
                touched_entry=path_entries[0],
            ))
            selected_types.append("artifact")

    if wants_sensemaking or is_runtime_failure or wants_negative:
        write_plan.append(_sensemaking_plan(
            topic_id=topic_id,
            target_claim_id=target_claim_id,
            event_summary=event_summary,
            is_runtime_failure=is_runtime_failure,
            is_boundary=_contains_any(event_lower, _KW_BOUNDARY) or _contains_any(event_lower, _KW_OLD_NEW_CONFLICT),
            extra_verification_refs=existing_artifact_refs,
        ))
        selected_types.append("sensemaking_report")

    if wants_gap:
        write_plan.append(_proof_obligation_plan(
            topic_id=topic_id,
            target_claim_id=target_claim_id,
            event_summary=event_summary,
            extra_verification_refs=existing_artifact_refs,
        ))
        selected_types.append("proof_obligation")

    if wants_evidence:
        write_plan.append(_evidence_plan(
            topic_id=topic_id,
            target_claim_id=target_claim_id,
            event_summary=event_summary,
            verified_refs=verified_refs,
            negative=wants_negative,
            extra_verification_refs=existing_artifact_refs,
        ))
        selected_types.append("evidence")

    if wants_trust:
        write_plan.append(_trust_preflight_plan(
            topic_id=topic_id,
            target_claim_id=target_claim_id,
            current_session_id=current_session_id,
            event_summary=event_summary,
            extra_verification_refs=existing_artifact_refs,
        ))
        selected_types.append("trust_preflight")

    # dedupe selected_types while preserving order
    seen: set[str] = set()
    selected_types = [t for t in selected_types if not (t in seen or seen.add(t))]

    if not write_plan:
        # No concrete write was selected. If the only durable signal was an existing
        # canonical artifact ref (no path to attach, no other trigger), do not drop its
        # provenance: return a minimal orientation plan that carries the ref forward.
        if existing_artifact_refs and not path_entries:
            orient = _sensemaking_plan(
                topic_id=topic_id,
                target_claim_id=target_claim_id,
                event_summary=event_summary,
                is_runtime_failure=False,
                is_boundary=False,
                extra_verification_refs=existing_artifact_refs,
            )
            return {
                "ok": True,
                "kind": "lightweight_record_write_plan",
                "decision": DECISION_PLAN_WRITE,
                "topic_id": topic_id,
                "current_session_id": current_session_id,
                "active_claim_id": active_claim_id,
                "target_claim": {
                    "target_claim_id": target_claim_id,
                    "reason_for_target_claim": target["reason_for_target_claim"],
                    "confidence": target["confidence"],
                },
                "write_reasons": ["existing_artifact_ref_preserved"],
                "no_write_reason": "",
                "selected_record_types": ["sensemaking_report"],
                "typed_write_plan": [orient],
                "trust_boundary": dict(_TRUST_BOUNDARY),
                "final_human_readable_summary": (
                    "Only an existing artifact ref was provided (nothing new to attach); "
                    "preserving it on a minimal orientation sensemaking plan. "
                    "No claim trust changed."
                ),
                **_TOP_LEVEL_TRUTH,
            }
        return _no_write_payload(
            topic_id=topic_id,
            current_session_id=current_session_id,
            active_claim_id=active_claim_id,
            reason="no_concrete_record_type_selected_after_routing",
        )

    write_reasons: list[str] = []
    if wants_artifact:
        write_reasons.append("durable_artifact_located")
    if wants_sensemaking:
        write_reasons.append("boundary_or_convention_clarification")
    if is_runtime_failure:
        write_reasons.append("runtime_failure_boundary_recorded_not_algorithm_failure")
    if wants_gap:
        write_reasons.append("open_gap_or_proof_obligation")
    if wants_evidence:
        write_reasons.append("verified_tool_run_or_validation_result_ref")
    if wants_negative:
        write_reasons.append("negative_result")
    if wants_trust:
        write_reasons.append("trust_preflight_requested_only")

    final_summary_parts = [
        f"Planned {len(write_plan)} record(s): {', '.join(selected_types)}.",
    ]
    if is_runtime_failure:
        final_summary_parts.append(
            "Runtime failure boundary recorded; NOT an algorithm failure, no claim refuted."
        )
    if wants_trust:
        final_summary_parts.append(
            "Trust preflight only; confidence NOT raised (requires passed validation)."
        )
    final_summary_parts.append("No claim trust changed; this is orientation-only.")

    return {
        "ok": True,
        "kind": "lightweight_record_write_plan",
        "decision": DECISION_PLAN_WRITE,
        "topic_id": topic_id,
        "current_session_id": current_session_id,
        "active_claim_id": active_claim_id,
        "target_claim": {
            "target_claim_id": target_claim_id,
            "reason_for_target_claim": target["reason_for_target_claim"],
            "confidence": target["confidence"],
        },
        "write_reasons": write_reasons,
        "no_write_reason": "",
        "selected_record_types": selected_types,
        "typed_write_plan": write_plan,
        "trust_boundary": dict(_TRUST_BOUNDARY),
        "final_human_readable_summary": " ".join(final_summary_parts),
        **_TOP_LEVEL_TRUTH,
    }
