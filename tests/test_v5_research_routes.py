from __future__ import annotations


def test_research_route_record_and_mcp_surface_are_orientation_only(tmp_path):
    from brain.v5.contracts import require_valid_research_route_record
    from brain.v5.mcp_tools import aitp_v5_record_research_route
    from brain.v5.routes import record_research_route, research_route_payload
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")

    route = record_research_route(
        ws,
        topic_id="fqhe",
        claim_id="claim-fqhe",
        session_id="s1",
        route_type="relation_path",
        status="live",
        title="Counting to CFT relation route",
        rationale="Try the relation path before treating counting as evidence.",
        current_question="Can sector counting be traced to CFT labels?",
        next_action="trace source definitions",
        failure_modes=["finite-size aliasing"],
        source_refs=["paper:edge-counting"],
    )

    payload = require_valid_research_route_record(research_route_payload(route))
    assert payload["kind"] == "research_route"
    assert payload["orientation_only"] is True
    assert payload["can_update_claim_trust"] is False
    assert payload["status"] == "live"

    mcp_payload = aitp_v5_record_research_route(
        str(tmp_path),
        topic_id="fqhe",
        claim_id="claim-fqhe",
        session_id="s1",
        route_type="source_backtrace",
        status="blocked",
        title="Trace imported theorem route",
        rationale="Source dependency is unclear.",
        failure_modes=["missing theorem source"],
        pivot_reason="Need a different source chain.",
    )
    assert mcp_payload["kind"] == "research_route"
    assert mcp_payload["status"] == "blocked"
    assert mcp_payload["orientation_only"] is True
    assert mcp_payload["can_update_claim_trust"] is False


def test_process_graph_slice_exposes_route_state_and_route_policy(tmp_path):
    from brain.v5.checkpoints import request_human_checkpoint
    from brain.v5.exploration import record_exploratory_record
    from brain.v5.mcp_tools import aitp_v5_get_process_graph_slice
    from brain.v5.moment_policy_contracts import validate_host_agnostic_moment_policy
    from brain.v5.process_graph import build_process_graph_slice
    from brain.v5.process_graph_contracts import validate_process_graph_slice
    from brain.v5.routes import record_research_route
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="formal-theory", title="QG algebra")
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="A candidate algebraic split may model an observer role.",
        evidence_profile="source_reconstruction",
        confidence_state="hypothesis",
        active_uncertainty="route choice unclear",
    )

    failed = record_research_route(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        session_id="s-qg",
        route_type="source_backtrace",
        status="abandoned",
        title="Follow informal observer analogy source chain",
        rationale="Initial route follows a secondary analogy source.",
        current_question="Where did the observer-role algebra analogy enter?",
        failure_modes=["secondary source never defines the algebraic split"],
        source_refs=["source_asset:secondary-observer-note"],
        decision_rationale="Abandon because the imported concept remains undefined.",
        next_action="switch to definition backtrace",
    )
    exploration = record_exploratory_record(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        session_id="s-qg",
        exploration_type="backtrace_step",
        title="Backtrace algebraic split definition",
        focal_question="Which primary source defines the split?",
        summary="Definition source is being traced.",
        source_refs=["source_asset:primary-algebra-paper"],
    )
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        reason="Choose whether to pivot from observer analogy to definition-first route.",
        requested_by="route_policy",
        options=["continue_old_route", "switch_to_definition_route", "pause"],
    )
    live = record_research_route(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        session_id="s-qg",
        route_type="derivation",
        status="live",
        title="Definition-first algebra route",
        rationale="Trace both sides back to the algebraic split definition.",
        current_question="Can the two objects be related from their definitions?",
        parent_route_ids=[failed.route_id],
        checkpoint_ids=[checkpoint.checkpoint_id],
        exploratory_record_ids=[exploration.record_id],
        pivot_reason="Secondary source chain did not define the imported algebra.",
        next_action="derive from definitions",
    )
    bind_session(
        ws,
        "s-qg",
        topic_id="qg",
        context_id="formal-theory",
        active_claim=claim.claim_id,
        active_route=live.route_id,
    )

    payload = build_process_graph_slice(ws, "s-qg", limit=80)
    mcp_payload = aitp_v5_get_process_graph_slice(str(tmp_path), session_id="s-qg", limit=80)

    assert validate_process_graph_slice(payload).ok is True
    assert mcp_payload["route_state"]["active_route_id"] == live.route_id
    assert payload["record_counts"]["research_route"] == 2
    assert payload["record_counts"]["human_checkpoint"] == 1
    assert payload["route_state"]["active_route_id"] == live.route_id
    assert live.route_id in payload["route_state"]["live_route_ids"]
    assert failed.route_id in payload["route_state"]["abandoned_route_ids"]
    assert live.route_id in payload["route_state"]["pivot_required_route_ids"]
    assert payload["route_state"]["orientation_only"] is True
    assert payload["route_state"]["can_update_claim_trust"] is False

    node_ids = {node["id"] for node in payload["nodes"]}
    assert f"research_route:{live.route_id}" in node_ids
    assert f"research_route:{failed.route_id}" in node_ids
    assert f"human_checkpoint:{checkpoint.checkpoint_id}" in node_ids

    edges = {(edge["source"], edge["type"], edge["target"]) for edge in payload["edges"]}
    assert (f"claim:{claim.claim_id}", "has_research_route", f"research_route:{live.route_id}") in edges
    assert (f"session:s-qg", "active_route", f"research_route:{live.route_id}") in edges
    assert (f"research_route:{live.route_id}", "branches_from", f"research_route:{failed.route_id}") in edges
    assert (
        f"research_route:{live.route_id}",
        "requires_checkpoint",
        f"human_checkpoint:{checkpoint.checkpoint_id}",
    ) in edges
    assert (
        f"research_route:{live.route_id}",
        "uses_exploration",
        f"exploratory_record:{exploration.record_id}",
    ) in edges

    policy = payload["moment_policy"]
    assert validate_host_agnostic_moment_policy(policy).ok is True
    assert "route" in policy["policy_axes"]
    route_decisions = [item for item in policy["decisions"] if item["decision_type"] == "route"]
    route_moments = {item["moment"] for item in route_decisions}
    assert "record_route_choice" in route_moments
    assert "record_failed_route_lesson" in route_moments
    assert "checkpoint_before_route_switch" in route_moments

    choice = next(item for item in route_decisions if item["moment"] == "record_route_choice")
    assert choice["required_now"] is False
    assert choice["trust_boundary"] is False
    assert choice["lifecycle_phases"] == ["pre_turn", "pre_action"]
    assert choice["recording_threshold"] == "recommended_before_route_dependent_work"
    choice_hint = _hint_by_entrypoint(choice, "aitp_v5_record_research_route")
    assert choice_hint["record_action"] == "record_research_route"
    assert choice_hint["draft"]["route_type"] == "derivation"
    assert choice_hint["draft"]["status"] == "live"
    assert choice_hint["draft_schema"]["required_fields"] == [
        "topic_id",
        "title",
        "route_type",
        "status",
        "rationale",
    ]
    assert choice_hint["draft_schema"]["placeholder_fields"] == []
    assert choice_hint["draft_schema"]["host_must_resolve"] == []

    failed_decision = next(item for item in route_decisions if item["moment"] == "record_failed_route_lesson")
    failed_hint = _hint_by_entrypoint(failed_decision, "aitp_v5_record_research_route")
    assert failed_hint["draft"]["status"] == "abandoned"
    assert "secondary source never defines" in failed_hint["draft"]["failure_modes"][0]

    checkpoint_decision = next(item for item in route_decisions if item["moment"] == "checkpoint_before_route_switch")
    assert "aitp_v5_request_human_checkpoint" in checkpoint_decision["entrypoints"]
    checkpoint_hint = _hint_by_entrypoint(checkpoint_decision, "aitp_v5_request_human_checkpoint")
    assert checkpoint_hint["record_action"] == "request_human_checkpoint"
    assert checkpoint_hint["draft"]["requested_by"] == "route_policy"
    assert checkpoint_hint["draft_schema"]["field_case"] == "snake_case"
    assert checkpoint_hint["draft_schema"]["summary_inputs_trusted"] is False
    assert checkpoint_hint["draft_schema"]["can_update_claim_trust"] is False


def test_research_route_entrypoint_is_registered():
    from brain.v5.native_mcp import _TOOLS
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    assert "aitp_v5_record_research_route" in _TOOLS
    assert runtime_entrypoints()["record_research_route"] == {
        "cli": "aitp-v5 route record <args>",
        "mcp": "aitp_v5_record_research_route",
        "surface": "research_route_record",
    }
    assert validate_runtime_entrypoints() == []


def _hint_by_entrypoint(decision: dict, entrypoint: str) -> dict:
    for hint in decision["payload_hints"]:
        if hint["entrypoint"] == entrypoint:
            return hint
    raise AssertionError(f"missing payload hint {entrypoint}")
