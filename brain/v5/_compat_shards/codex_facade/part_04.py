# Compatibility shard 4 for codex_facade.
from __future__ import annotations

def _expand_record_refs(
    ws: WorkspacePaths,
    *,
    refs: list[str] | tuple[str, ...],
    offset: int,
    limit: int,
) -> dict[str, Any]:
    unique_refs = list(dict.fromkeys(str(ref).strip() for ref in refs if str(ref).strip()))
    bounded_refs = unique_refs[:50]
    clean_offset = max(0, int(offset))
    page_size = max(1, min(int(limit), 20))
    page_refs = bounded_refs[clean_offset : clean_offset + page_size]
    if not page_refs:
        return {
            "ok": False,
            "kind": "record_ref_expansion",
            "error": "record_refs expansion requires at least one ref in the requested page",
            "requested_ref_count": len(unique_refs),
            "offset": clean_offset,
            "limit": page_size,
            "summary_inputs_trusted": False,
            "orientation_only": True,
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
        }
    result = exact_expand(ws, page_refs, limit=page_size)
    next_offset = clean_offset + page_size
    if next_offset >= len(bounded_refs):
        next_offset = None
    return {
        "ok": True,
        "kind": "record_ref_expansion",
        "items": [asdict(item) for item in result.items],
        "returned_refs": [item.record_ref for item in result.items],
        "unresolved_refs": list(result.excluded_candidates),
        "requested_ref_count": len(unique_refs),
        "bounded_ref_count": len(bounded_refs),
        "input_truncated": len(unique_refs) > len(bounded_refs),
        "offset": clean_offset,
        "limit": page_size,
        "next_offset": next_offset,
        "index_status": result.index_status,
        "index_generation": result.index_generation,
        "coverage": asdict(result.coverage),
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }

def _needs_claim_id(expansion: str) -> dict[str, Any]:
    return {
        "ok": False,
        "kind": "codex_context_expansion",
        "expansion": expansion,
        "error": f"{expansion} requires claim_id",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }

def _literature_action(action: str) -> str:
    clean = str(action or "suggest").strip().lower().replace("-", "_")
    aliases = {
        "record": "record_reference",
        "register": "record_reference",
        "handoff": "source_review_handoff",
        "compare": "comparison_draft",
    }
    return aliases.get(clean, clean)

def _allowed_literature_actions() -> list[str]:
    return ["suggest", "record_reference", "source_review_handoff", "comparison_draft"]

def _reference_layers() -> list[dict[str, str]]:
    return [
        {
            "layer": "source_identity",
            "record": "source_asset",
            "rule": "A paper, web page, dataset, repository, or local note exists.",
        },
        {
            "layer": "source_location",
            "record": "reference_location",
            "rule": "Exact page, equation, section, URL, timestamp, or local path.",
        },
        {
            "layer": "reading_artifact",
            "record": "artifact or sensemaking_report",
            "rule": "Reusable reading note or comparison draft; not claim support by itself.",
        },
        {
            "layer": "claim_link",
            "record": "evidence",
            "rule": "Only after a source statement is explicitly tied to one claim and scoped output.",
        },
        {
            "layer": "physical_content",
            "record": "physics_object or object_relation",
            "rule": "Definitions, assumptions, equations, objects, regimes, or relations extracted from the source.",
        },
        {
            "layer": "validation_basis",
            "record": "validation_contract or validation_result link",
            "rule": "The source defines a check, benchmark, or failure mode.",
        },
        {
            "layer": "trust_basis",
            "record": "trust preflight, checkpoint, or promotion packet",
            "rule": "Only after typed evidence/validation and the required gate.",
        },
    ]

def codex_record_apply(
    ws: WorkspacePaths,
    *,
    session_id: str,
    slot: str,
    payload: dict[str, Any] | None = None,
    event_type: str = "",
    summary: str = "",
    claim_id: str = "",
    expected_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Apply one constrained typed write selected through the Codex recording navigator."""

    selected = _record_apply_slot(slot)
    data = dict(payload or {})
    focus = recover_session_binding_for_read(ws, session_id)
    session = focus.session
    topic_id = str(data.pop("topic_id", "") or session.topic_id)
    active_claim = str(data.pop("claim_id", "") or claim_id or session.active_claim)
    try:
        record = _apply_record_slot(
            ws,
            selected,
            topic_id=topic_id,
            claim_id=active_claim,
            session_id=session.session_id,
            data=data,
            fallback_summary=summary,
        )
    except Exception as exc:
        return {
            "ok": False,
            "kind": "codex_record_apply",
            "session_id": session.session_id,
            "requested_session_id": focus.requested_session_id,
            "slot": selected,
            "event_type": event_type,
            "write_executed": False,
            "error": f"{type(exc).__name__}: {exc}",
            "allowed_slots": _record_apply_slots(),
            "truth_source": "typed_records_and_recording_navigator",
            "summary_inputs_trusted": False,
            "orientation_only": True,
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
        }

    record_ref = _record_ref_for_slot(selected, record)
    verify_refs = list(expected_refs or [])
    if record_ref and record_ref not in verify_refs:
        verify_refs.append(record_ref)
    verification = (
        verify_recording_effect(ws, session.session_id, expected_refs=verify_refs, claim_id=active_claim)
        if verify_refs
        else {}
    )
    return {
        "ok": True,
        "kind": "codex_record_apply",
        "session_id": session.session_id,
        "requested_session_id": focus.requested_session_id,
        "slot": selected,
        "event_type": event_type,
        "topic_id": topic_id,
        "claim_id": active_claim,
        "record_ref": record_ref,
        "record": {"ok": True, **asdict(record)},
        "verification": verification,
        "write_executed": True,
        "kernel_state_change": f"{selected}_record",
        "trust_update_forbidden": True,
        "truth_source": "typed_records_and_recording_navigator",
        "summary_inputs_trusted": False,
        "orientation_only": False,
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }

def _record_apply_slot(slot: str) -> str:
    clean = str(slot or "").strip().lower().replace("-", "_")
    aliases = {
        "source": "source_asset",
        "source_identity": "source_asset",
        "reference": "reference_location",
        "ref": "reference_location",
        "artifact_ref": "artifact",
        "recipe": "tool_recipe",
        "tool": "tool_recipe",
        "code": "code_state",
        "code_state_auto": "code_state",
        "capture_code_state": "code_state",
        "physics": "physics_object",
        "object": "physics_object",
        "relation": "object_relation",
        "sensemaking": "sensemaking_report",
        "proof_gap": "proof_obligation",
        "validation": "validation_result",
    }
    clean = aliases.get(clean, clean)
    if clean not in _record_apply_slots():
        raise ValueError(f"unsupported Codex record apply slot: {slot}")
    return clean

def _record_apply_slots() -> list[str]:
    return [
        "source_asset",
        "reference_location",
        "artifact",
        "evidence",
        "physics_object",
        "object_relation",
        "sensemaking_report",
        "proof_obligation",
        "tool_recipe",
        "code_state",
        "tool_run",
        "validation_contract",
        "validation_result",
    ]

def _apply_record_slot(
    ws: WorkspacePaths,
    slot: str,
    *,
    topic_id: str,
    claim_id: str,
    session_id: str,
    data: dict[str, Any],
    fallback_summary: str,
) -> Any:
    if slot == "source_asset":
        label_value = _pop_str(data, "label", "")
        title_value = _pop_str(data, "title", label_value)
        return register_source_asset(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            asset_type=_pop_str(data, "asset_type", "paper"),
            uri=_pop_required(data, "uri"),
            title=title_value,
            label=label_value,
            content_hash=_pop_str(data, "content_hash", ""),
            hash_algorithm=_pop_str(data, "hash_algorithm", ""),
            version_anchor=_pop_dict(data, "version_anchor"),
            acquired_at=_pop_str(data, "acquired_at", ""),
            source_kind=_pop_str(data, "source_kind", "codex_record_apply"),
            summary=_pop_str(data, "summary", fallback_summary),
            source_refs=_pop_list(data, "source_refs"),
            artifact_ids=_pop_list(data, "artifact_ids"),
            code_state_ids=_pop_list(data, "code_state_ids"),
            reference_location_ids=_pop_list(data, "reference_location_ids"),
            derived_from=_pop_list(data, "derived_from"),
            metadata=_pop_dict(data, "metadata"),
            linked_records=_pop_dict(data, "linked_records"),
        )
    if slot == "reference_location":
        return record_reference_location(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            connector_id=_pop_str(data, "connector_id", "manual"),
            location_type=_pop_str(data, "location_type", "source"),
            uri=_pop_required(data, "uri"),
            label=_pop_required(data, "label"),
            source_ref=_pop_str(data, "source_ref", ""),
            external_id=_pop_str(data, "external_id", ""),
            status=_pop_str(data, "status", "located"),
            summary=_pop_str(data, "summary", fallback_summary),
            metadata=_pop_dict(data, "metadata"),
            linked_records=_pop_dict(data, "linked_records"),
        )
    if slot == "artifact":
        uri = _normalize_artifact_uri(_pop_required(data, "uri"))
        return attach_artifact(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            artifact_type=_pop_required(data, "artifact_type"),
            uri=uri,
            summary=_pop_str(data, "summary", fallback_summary),
            size_bytes=data.pop("size_bytes", 0),
            metadata=_pop_dict(data, "metadata"),
        )
    if slot == "evidence":
        return record_evidence(
            ws,
            topic_id=topic_id,
            claim_id=_require_claim(claim_id, slot),
            evidence_type=_pop_required(data, "evidence_type"),
            status=_pop_required(data, "status"),
            summary=_pop_str(data, "summary", fallback_summary),
            supports_outputs=_pop_list(data, "supports_outputs"),
            source_refs=_pop_list(data, "source_refs"),
            tool_run_ids=_pop_list(data, "tool_run_ids"),
            validation_result_ids=_pop_list(data, "validation_result_ids"),
            artifact_ids=_pop_list(data, "artifact_ids"),
            body=data.pop("body", None),
        )
    if slot == "physics_object":
        linked = _pop_dict(data, "linked_records")
        if claim_id:
            linked.setdefault("claim_id", claim_id)
        return record_physics_object(
            ws,
            topic_id=topic_id,
            object_type=_pop_required(data, "object_type"),
            name=_pop_required(data, "name"),
            definition=_pop_required(data, "definition"),
            notation=_pop_str(data, "notation", ""),
            assumptions=_pop_list(data, "assumptions"),
            source_refs=_pop_list(data, "source_refs"),
            metadata=_pop_dict(data, "metadata"),
            linked_records=linked,
            status=_pop_str(data, "status", "active"),
        )
    if slot == "object_relation":
        return record_object_relation(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            relation_type=_pop_required(data, "relation_type"),
            subject_id=_pop_required(data, "subject_id"),
            object_id=_pop_required(data, "object_id"),
            statement=_pop_required(data, "statement"),
            assumptions=_pop_list(data, "assumptions"),
            failure_modes=_pop_list(data, "failure_modes"),
            source_refs=_pop_list(data, "source_refs"),
            evidence_refs=_pop_list(data, "evidence_refs"),
            metadata=_pop_dict(data, "metadata"),
            status=_pop_str(data, "status", "hypothesis"),
        )
    if slot == "sensemaking_report":
        return record_sensemaking_report(
            ws,
            topic_id=topic_id,
            claim_id=_require_claim(claim_id, slot),
            title=_pop_required(data, "title"),
            summary=_pop_str(data, "summary", fallback_summary),
            object_ids=_pop_list(data, "object_ids"),
            relation_ids=_pop_list(data, "relation_ids"),
            evidence_refs=_pop_list(data, "evidence_refs"),
            open_questions=_pop_list(data, "open_questions"),
            next_actions=_pop_list(data, "next_actions"),
            validation_status=_pop_str(data, "validation_status", "not_validation"),
        )
    if slot == "proof_obligation":
        return create_proof_obligation(
            ws,
            topic_id=topic_id,
            claim_id=_require_claim(claim_id, slot),
            statement=_pop_required(data, "statement"),
            obligation_type=_pop_str(data, "obligation_type", "open_gap"),
            status=_pop_str(data, "status", "open"),
            maturity_level=_pop_str(data, "maturity_level", "exploratory"),
            next_action=_pop_str(data, "next_action", "decide next proof or validation step"),
            required_evidence=_pop_list(data, "required_evidence"),
            proof_strategy=_pop_list(data, "proof_strategy"),
            failure_modes=_pop_list(data, "failure_modes"),
            source_refs=_pop_list(data, "source_refs"),
            evidence_refs=_pop_list(data, "evidence_refs"),
            artifact_ids=_pop_list(data, "artifact_ids"),
            human_gate_required=bool(data.pop("human_gate_required", True)),
        )
    if slot == "tool_recipe":
        return register_tool_recipe(
            ws,
            recipe_id=_pop_required(data, "recipe_id"),
            tool_family=_pop_required(data, "tool_family"),
            tool_name=_pop_required(data, "tool_name"),
            purpose=_pop_str(data, "purpose", fallback_summary),
            required_inputs=_pop_list(data, "required_inputs"),
            expected_outputs=_pop_list(data, "expected_outputs"),
            invariants=_pop_list(data, "invariants"),
        )
    if slot == "code_state":
        worktree_path = _pop_required(data, "worktree_path")
        changed_files = [str(item) for item in _pop_list(data, "changed_files")]
        runtime_environment = _pop_dict(data, "runtime_environment")
        runtime_environment = _enrich_code_state_runtime(
            worktree_path=worktree_path,
            changed_files=changed_files,
            runtime_environment=runtime_environment,
        )
        linked_records = _pop_dict(data, "linked_records")
        if topic_id:
            linked_records.setdefault("topic_id", topic_id)
        if claim_id:
            linked_records.setdefault("claim_id", claim_id)
        if session_id:
            linked_records.setdefault("session_id", session_id)
        known_divergence = _pop_str(data, "known_divergence", "")
        if runtime_environment.get("dirty_status_summary"):
            known_divergence = known_divergence or (
                "source tree is dirty; this code_state is not a clean reproducibility anchor"
            )
        return capture_code_state_from_git(
            ws,
            worktree_path=worktree_path,
            repo_id=_pop_str(data, "repo_id", ""),
            topic_id=topic_id,
            claim_id=claim_id,
            session_id=session_id,
            build_config=_pop_dict(data, "build_config"),
            runtime_environment=runtime_environment,
            linked_records=linked_records,
            known_divergence=known_divergence,
            write_patch_artifact=bool(data.pop("write_patch_artifact", False)),
        )
    if slot == "tool_run":
        return record_tool_run(
            ws,
            topic_id=topic_id,
            claim_id=_require_claim(claim_id, slot),
            recipe_id=_pop_required(data, "recipe_id"),
            tool_family=_pop_required(data, "tool_family"),
            tool_name=_pop_required(data, "tool_name"),
            inputs=_pop_dict(data, "inputs"),
            outputs=_pop_dict(data, "outputs"),
            environment=_pop_dict(data, "environment"),
            evidence_status=_pop_str(data, "evidence_status", "unreviewed"),
            code_state_ids=_pop_list(data, "code_state_ids"),
            artifact_ids=_pop_list(data, "artifact_ids"),
            source_refs=_pop_list(data, "source_refs"),
            scientific_run_id=_pop_str(data, "scientific_run_id", ""),
            supersedes=_pop_str(data, "supersedes", ""),
            lane=_pop_str(data, "lane", "diagnostic"),
        )
    if slot == "validation_contract":
        return create_validation_contract(
            ws,
            topic_id=topic_id,
            claim_id=_require_claim(claim_id, slot),
            required_checks=_pop_list(data, "required_checks"),
            failure_modes=_pop_list(data, "failure_modes"),
            required_evidence_outputs=_pop_list(data, "required_evidence_outputs"),
            tool_recipe_ids=_pop_list(data, "tool_recipe_ids"),
            executor_ids=_pop_list(data, "executor_ids"),
            validator_role=_pop_str(data, "validator_role", "adversarial_reviewer"),
        )
    if slot == "validation_result":
        return record_validation_result(
            ws,
            topic_id=topic_id,
            claim_id=_require_claim(claim_id, slot),
            contract_id=_pop_required(data, "contract_id"),
            tool_run_id=_pop_required(data, "tool_run_id"),
            status=_pop_required(data, "status"),
            checked_outputs=_pop_list(data, "checked_outputs"),
            summary=_pop_str(data, "summary", fallback_summary),
            evidence_refs=_pop_list(data, "evidence_refs"),
            artifact_ids=_pop_list(data, "artifact_ids"),
            covered_failure_modes=_pop_list(data, "covered_failure_modes"),
            failure_modes_observed=_pop_list(data, "failure_modes_observed"),
        )
    raise ValueError(f"unsupported slot: {slot}")
