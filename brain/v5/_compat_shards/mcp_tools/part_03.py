# Compatibility shard 3 for mcp_tools.
from __future__ import annotations

def aitp_v5_apply_workspace_recovery_binding_repair(
    base: str,
    *,
    topics: list[str] | None = None,
    session_id: str = "",
    objective_text: str = "",
    user_goal: str = "",
    write_json: str = "",
    write_report: str = "",
) -> dict:
    """Apply safe single-claim active-session binding repairs for recovery gaps."""

    ws = _ws(base)
    payload = build_workspace_recovery_binding_repair(
        ws,
        topics=topics or [],
        session_id=session_id,
        objective_text=objective_text,
        user_goal=user_goal,
    )
    payload = apply_workspace_recovery_binding_repair(payload, ws)
    if write_json or write_report:
        payload = write_workspace_recovery_binding_repair(
            payload,
            json_path=write_json or None,
            report_path=write_report or None,
        )
    return {"ok": True, **require_valid_public_surface("workspace_recovery_binding_repair", payload)}

def aitp_v5_build_workspace_recovery_audit(
    base: str,
    *,
    migration_plan_json: str = "",
    topics: list[str] | None = None,
    compact: bool = False,
) -> dict:
    """Return a read-only per-topic restart recovery audit."""

    payload = build_workspace_recovery_audit(
        _ws(base),
        migration_plan_path=migration_plan_json or None,
        topics=topics or [],
    )
    if compact:
        return require_valid_public_surface(
            "workspace_recovery_audit_progress",
            compact_workspace_recovery_audit(payload),
        )
    return require_valid_public_surface("workspace_recovery_audit", payload)

def aitp_v5_write_workspace_recovery_audit(
    base: str,
    *,
    migration_plan_json: str = "",
    topics: list[str] | None = None,
    write_json: str = "",
    write_report: str = "",
    compact: bool = True,
) -> dict:
    """Write JSON/Markdown per-topic restart recovery audit views."""

    payload = build_workspace_recovery_audit(
        _ws(base),
        migration_plan_path=migration_plan_json or None,
        topics=topics or [],
    )
    payload = write_workspace_recovery_audit(
        payload,
        json_path=write_json or None,
        report_path=write_report or None,
    )
    if compact:
        progress = compact_workspace_recovery_audit(payload)
        return {"ok": True, **require_valid_public_surface("workspace_recovery_audit_progress", progress)}
    return {"ok": True, **require_valid_public_surface("workspace_recovery_audit", payload)}

def aitp_v5_build_workspace_recording_audit(
    base: str,
    *,
    migration_plan_json: str = "",
    topics: list[str] | None = None,
    limit: int = 40,
) -> dict:
    """Return a read-only workspace-level audit of progressive recording navigation."""

    payload = build_workspace_recording_audit(
        _ws(base),
        migration_plan_path=migration_plan_json or None,
        topics=topics or [],
        limit=limit,
    )
    return require_valid_public_surface("workspace_recording_audit", payload)

def aitp_v5_write_workspace_recording_audit(
    base: str,
    *,
    migration_plan_json: str = "",
    topics: list[str] | None = None,
    write_json: str = "",
    write_report: str = "",
    limit: int = 40,
) -> dict:
    """Write JSON/Markdown workspace-level progressive recording navigation audit views."""

    payload = build_workspace_recording_audit(
        _ws(base),
        migration_plan_path=migration_plan_json or None,
        topics=topics or [],
        limit=limit,
    )
    payload = write_workspace_recording_audit(
        payload,
        json_path=write_json or None,
        report_path=write_report or None,
    )
    return {"ok": True, **require_valid_public_surface("workspace_recording_audit", payload)}

def _unbound_session_execution_brief(session_id: str) -> dict:
    """Return a valid brief for malformed or not-yet-bound session records."""

    return {
        "ok": False,
        "status": "needs_bind_session",
        "session": {
            "session_id": session_id or "unbound-session",
            "topic_id": "unbound-session",
            "context_id": "unbound-session",
            "runtime": "unknown",
            "interaction_profile": "collaborator",
            "interaction_steering": "call aitp_v5_bind_session before requesting an execution brief",
            "active_cycle": "",
            "active_claim": "",
            "active_route": "",
            "write_scope": "",
            "created_at": "",
        },
        "current_focus": {
            "active_claim": "",
            "active_route": "",
            "active_cycle": "",
            "claim_statement": "",
            "confidence_state": "",
            "evidence_profile": "",
            "main_uncertainty": "session binding is missing or malformed",
        },
        "flow_profile": {
            "profile": "guided",
            "reason": "execution brief cannot resolve a bound session yet",
            "escalation_triggers": [],
        },
        "risk_assessment": {
            "level": "guided",
            "score": 0,
            "signals": [],
            "required_checks": [],
            "human_checkpoint_needed": False,
            "rationale": "no active claim is available until the session is bound",
            "summary": "session binding is missing or malformed",
            "action_budget": {
                "level": "guided",
                "max_tool_calls_before_reflection": 4,
                "max_questions": 2,
                "required_outputs": [],
                "allowed_actions": ["bind_session"],
                "requires_human_checkpoint": False,
            },
        },
        "action_budget": {
            "level": "guided",
            "max_tool_calls_before_reflection": 4,
            "max_questions": 2,
            "required_outputs": [],
            "allowed_actions": ["bind_session"],
            "requires_human_checkpoint": False,
        },
        "evidence_coverage": {
            "required_outputs": [],
            "satisfied_outputs": [],
            "missing_outputs": [],
            "coverage_by_record": [],
        },
        "interaction_profile": {
            "name": "collaborator",
            "max_questions": 2,
            "effective_max_questions": 2,
            "steering": "bind session before continuing",
        },
        "known_context": {
            "topic_id": "unbound-session",
            "context_id": "unbound-session",
            "previous_failed_attempts": [],
            "recommended_tool_executors": [],
            "knowledge_connectors": [],
            "reference_locations": [],
            "operating_notes": [],
            "research_intent_gate": {"present": False},
            "innovation_direction": {"present": False},
            "final_output_profile": {"present": False},
            "operator_checkpoint": {"active": False},
            "strategy_memory": {"present": False},
            "run_iterations": [],
            "lane_exemplars": [],
            "object_relations": [],
            "memory_entries": [],
            "proof_obligations": [],
        },
        "research_gates": {
            "record_level_human_gate_required": False,
            "record_level_human_gate_count": 0,
            "open_proof_obligation_count": 0,
            "open_proof_obligation_ids": [],
            "human_checkpoint_needed": False,
            "semantics": {
                "human_gate_required": "not evaluated until the session is bound",
                "human_checkpoint_needed": "not required for the bind-session repair",
            },
        },
        "claim_relation_map": empty_claim_relation_map(
            topic_id="unbound-session",
            session_id=session_id,
            reason="session binding is missing or malformed",
        ),
        "mandatory_reflection": [],
        "next_action_candidates": [
            {
                "action": "bind_session",
                "rank": 1,
                "why": "the requested execution brief has no valid SessionBinding",
                "expected_evidence_gain": "establish topic/context/claim focus before further AITP reads",
            }
        ],
        "forbidden_now": ["continue_without_binding_session"],
        "human_checkpoint": {
            "needed": False,
            "reason": None,
            "semantics": "No human checkpoint is needed for the bind-session repair.",
        },
    }

def aitp_v5_get_process_graph_slice(base: str, *, session_id: str, claim_id: str = "", limit: int = 80) -> dict:
    return require_valid_public_surface(
        "process_graph_slice",
        build_process_graph_slice(_ws(base), session_id, claim_id=claim_id, limit=limit),
    )

def aitp_v5_get_host_agnostic_moment_policy(
    base: str,
    *,
    session_id: str,
    claim_id: str = "",
    limit: int = 80,
) -> dict:
    """Return the read-only host-agnostic moment policy for a process graph slice."""

    graph = build_process_graph_slice(_ws(base), session_id, claim_id=claim_id, limit=limit)
    return require_valid_public_surface("host_agnostic_moment_policy", graph["moment_policy"])

def aitp_v5_classify_recording_candidate(
    base: str,
    *,
    session_id: str = "",
    event_type: str,
    summary: str = "",
    topic_id: str = "",
    claim_id: str = "",
    touched_refs: list[str] | None = None,
    produced_artifacts: list[str] | None = None,
    tool_call_id: str = "",
    risk_hint: str = "",
    payload: dict | None = None,
) -> dict:
    """Classify a durable research event before progressive AITP recording navigation."""

    return require_valid_public_surface(
        "recording_candidate_classification",
        classify_recording_candidate(
            _ws(base),
            session_id=session_id,
            event_type=event_type,
            summary=summary,
            topic_id=topic_id,
            claim_id=claim_id,
            touched_refs=touched_refs or [],
            produced_artifacts=produced_artifacts or [],
            tool_call_id=tool_call_id,
            risk_hint=risk_hint,
            payload=payload or {},
        ),
    )

def aitp_v5_get_recording_navigation_state(
    base: str,
    *,
    session_id: str,
    claim_id: str = "",
    limit: int = 40,
) -> dict:
    """Return the read-only first-level AITP recording navigator for a session."""

    return require_valid_public_surface(
        "recording_navigation_state",
        build_recording_navigation_state(_ws(base), session_id, claim_id=claim_id, limit=limit),
    )

def aitp_v5_expand_recording_slot(
    base: str,
    *,
    session_id: str,
    slot: str,
    claim_id: str = "",
    candidate: dict | None = None,
) -> dict:
    """Expand one AITP recording slot into required fields and typed write guidance."""

    return require_valid_public_surface(
        "recording_slot_expansion",
        expand_recording_slot(_ws(base), session_id, slot, claim_id=claim_id, candidate=candidate or {}),
    )

def aitp_v5_verify_recording_effect(
    base: str,
    *,
    session_id: str,
    expected_refs: list[str] | None = None,
    before_node_ids: list[str] | None = None,
    before_edge_ids: list[str] | None = None,
    claim_id: str = "",
    limit: int = 80,
) -> dict:
    """Verify typed refs or graph deltas after an AITP recording write."""

    return require_valid_public_surface(
        "recording_effect_verification",
        verify_recording_effect(
            _ws(base),
            session_id,
            expected_refs=expected_refs or [],
            before_node_ids=before_node_ids or [],
            before_edge_ids=before_edge_ids or [],
            claim_id=claim_id,
            limit=limit,
        ),
    )

def aitp_v5_plan_lightweight_record_write(
    base: str,
    *,
    topic_id: str,
    current_session_id: str,
    event_summary: str,
    active_claim_id: str = "",
    target_claim_hint: str = "",
    touched_files_or_artifacts: list[str] | None = None,
    touched_tool_runs_or_evidence_refs: list[str] | None = None,
    risk_hint: str = "",
) -> dict:
    """Plan-only surface: propose a minimal typed-record write set for a short research event.

    This tool NEVER writes records and NEVER applies trust updates. It returns a plan that
    an agent or human reviews before invoking the concrete record-write MCP tools.
    """

    from brain.v5.lightweight_record_router import plan_lightweight_record_write

    return require_valid_public_surface(
        "lightweight_record_write_plan",
        plan_lightweight_record_write(
            _ws(base),
            topic_id=topic_id,
            current_session_id=current_session_id,
            event_summary=event_summary,
            active_claim_id=active_claim_id,
            target_claim_hint=target_claim_hint,
            touched_files_or_artifacts=touched_files_or_artifacts or [],
            touched_tool_runs_or_evidence_refs=touched_tool_runs_or_evidence_refs or [],
            risk_hint=risk_hint,
        ),
    )

def aitp_v5_lookup_record_refs(base: str, *, refs: list[str]) -> dict:
    return {
        "ok": True,
        "record_ref_lookup": require_valid_public_surface(
            "record_ref_lookup",
            lookup_record_refs(_ws(base), refs),
        ),
    }

def aitp_v5_record_exploratory_record(
    base: str,
    *,
    topic_id: str,
    exploration_type: str,
    title: str,
    focal_question: str,
    summary: str,
    claim_id: str = "",
    session_id: str = "",
    original_question: str = "",
    local_question: str = "",
    status: str = "open",
    object_ids: list[str] | None = None,
    relation_ids: list[str] | None = None,
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    parent_record_ids: list[str] | None = None,
    derived_record_ids: list[str] | None = None,
    reasoning_moves: list[str] | None = None,
    backtrace_targets: list[str] | None = None,
    candidate_paths: list[str] | None = None,
    relation_path_questions: list[str] | None = None,
    definition_boundary_questions: list[str] | None = None,
    derivation_backtrace_questions: list[str] | None = None,
    source_dependency_questions: list[str] | None = None,
    original_question_guard: list[str] | None = None,
    unresolved_points: list[str] | None = None,
    next_actions: list[str] | None = None,
    human_steering: str = "",
    metadata: dict | None = None,
) -> dict:
    record = record_exploratory_record(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        session_id=session_id,
        exploration_type=exploration_type,
        title=title,
        focal_question=focal_question,
        summary=summary,
        original_question=original_question,
        local_question=local_question,
        status=status,
        object_ids=object_ids,
        relation_ids=relation_ids,
        source_refs=source_refs,
        artifact_ids=artifact_ids,
        parent_record_ids=parent_record_ids,
        derived_record_ids=derived_record_ids,
        reasoning_moves=reasoning_moves,
        backtrace_targets=backtrace_targets,
        candidate_paths=candidate_paths,
        relation_path_questions=relation_path_questions,
        definition_boundary_questions=definition_boundary_questions,
        derivation_backtrace_questions=derivation_backtrace_questions,
        source_dependency_questions=source_dependency_questions,
        original_question_guard=original_question_guard,
        unresolved_points=unresolved_points,
        next_actions=next_actions,
        human_steering=human_steering,
        metadata=metadata,
    )
    return require_valid_public_surface("exploratory_record", exploratory_record_payload(record))
