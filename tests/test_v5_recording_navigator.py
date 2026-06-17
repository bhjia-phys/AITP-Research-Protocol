from __future__ import annotations

import json


def _workspace_with_claim(tmp_path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Sector counting identifies the candidate edge CFT only after source reconstruction.",
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="finite-size aliasing and source definition drift",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    return ws, claim


def test_recording_candidate_classifier_is_trigger_not_write(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.recording_navigator import classify_recording_candidate

    ws, claim = _workspace_with_claim(tmp_path)

    tool_event = classify_recording_candidate(
        ws,
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        event_type="tool_run_completed",
        summary="ED diagnostic run completed and produced a finite-size result artifact.",
        tool_call_id="tool-call-1",
        produced_artifacts=["results/ed.json"],
    )

    assert require_valid_public_surface("recording_candidate_classification", tool_event) == tool_event
    assert tool_event["decision"] == "navigate"
    assert "tool_run" in tool_event["suggested_slots"]
    assert "artifact" in tool_event["suggested_slots"]
    assert tool_event["navigation_policy"]["write_at_classification"] is False
    assert tool_event["can_update_kernel_state"] is False
    assert tool_event["can_update_claim_trust"] is False

    trust_event = classify_recording_candidate(
        ws,
        session_id="s1",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        event_type="trust_change_requested",
        summary="Promote the claim confidence after validation.",
    )
    assert trust_event["decision"] == "checkpoint"
    assert trust_event["suggested_slots"][0] == "trust_preflight"

    casual_event = classify_recording_candidate(
        ws,
        session_id="s1",
        event_type="chat",
        summary="Casual explanation question without durable result.",
    )
    assert casual_event["decision"] in {"defer", "ignore"}
    assert casual_event["can_update_kernel_state"] is False


def test_recording_navigation_state_exposes_first_level_slots_and_position(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.recording_navigator import build_recording_navigation_state

    ws, claim = _workspace_with_claim(tmp_path)

    state = build_recording_navigation_state(ws, "s1", limit=20)

    assert require_valid_public_surface("recording_navigation_state", state) == state
    assert state["kind"] == "recording_navigation_state"
    assert state["navigation_mode"] == "lightweight_first_level"
    assert state["topic_id"] == "fqhe"
    assert state["claim_id"] == claim.claim_id
    assert state["current_position"]["claim_statement"].startswith("Sector counting")
    assert "lightweight_navigation_state_does_not_replace_execution_brief" in state["brief_context"]["forbidden_now"]
    assert state["graph_context"]["mode"] == "lightweight_slot_counts"
    assert state["graph_context"]["moment_policy"]["agent_should_not_record_every_step"] is True
    assert {slot["slot"] for slot in state["first_level_slots"]} >= {
        "source_asset",
        "reference_location",
        "tool_run",
        "evidence",
        "proof_obligation",
        "source_reconstruction_review",
        "validation_result",
        "human_checkpoint",
        "trust_preflight",
    }
    assert state["next_step"]["read_tool"] == "aitp_v5_expand_recording_slot"
    assert state["next_step"]["verify_tool"] == "aitp_v5_verify_recording_effect"
    assert state["orientation_only"] is True


def test_recording_navigation_state_handles_unbound_session(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.recording_navigator import build_recording_navigation_state
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)

    state = build_recording_navigation_state(ws, "missing-session")

    assert require_valid_public_surface("recording_navigation_state", state) == state
    assert state["recovery_selection_source"] == "unbound_session"
    assert state["topic_id"] == "unbound-session"
    assert any(slot["slot"] == "evidence" for slot in state["first_level_slots"])
    assert state["can_update_kernel_state"] is False


def test_recording_slot_expansion_names_existing_write_tool_and_boundaries(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.recording_navigator import expand_recording_slot

    ws, claim = _workspace_with_claim(tmp_path)

    evidence = expand_recording_slot(ws, "s1", "evidence", claim_id=claim.claim_id)
    assert require_valid_public_surface("recording_slot_expansion", evidence) == evidence
    assert evidence["recommended_write_tool"] == "aitp_v5_record_evidence"
    assert [field["name"] for field in evidence["required_fields"]] == [
        "base",
        "topic_id",
        "claim_id",
        "evidence_type",
        "status",
        "summary",
    ]
    assert _known(evidence, "topic_id") == "fqhe"
    assert _known(evidence, "claim_id") == claim.claim_id
    assert evidence["trust_effect"]["can_update_claim_trust"] is False
    assert evidence["verify_with"] == "aitp_v5_verify_recording_effect"

    checkpoint = expand_recording_slot(ws, "s1", "trust_preflight", claim_id=claim.claim_id)
    assert checkpoint["recommended_write_tool"] == "aitp_v5_preflight_trust_update"
    assert checkpoint["trust_effect"]["writes_kernel_state"] is False
    assert any("cannot apply trust" in warning for warning in checkpoint["warnings"])

    source_review = expand_recording_slot(ws, "s1", "source_reconstruction_review", claim_id=claim.claim_id)
    assert source_review["recommended_write_tool"] == "aitp_v5_record_source_reconstruction_review_result"
    assert [field["name"] for field in source_review["required_fields"]] == [
        "base",
        "claim_id",
        "status",
        "reviewed_components",
        "summary",
    ]
    assert _known(source_review, "claim_id") == claim.claim_id
    assert any("do not promote claim trust" in warning for warning in source_review["warnings"])


def test_recording_effect_verification_reads_back_typed_write(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.process_graph import build_process_graph_slice
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.recording_navigator import verify_recording_effect

    ws, claim = _workspace_with_claim(tmp_path)
    before = build_process_graph_slice(ws, "s1")
    before_node_ids = [node["id"] for node in before["nodes"]]
    before_edge_ids = [edge["id"] for edge in before["edges"]]

    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="diagnostic",
        status="supports",
        summary="A bounded diagnostic result was observed.",
        supports_outputs=["finite_size_diagnostic"],
    )

    verification = verify_recording_effect(
        ws,
        "s1",
        expected_refs=[f"evidence:{evidence.evidence_id}"],
        before_node_ids=before_node_ids,
        before_edge_ids=before_edge_ids,
    )

    assert require_valid_public_surface("recording_effect_verification", verification) == verification
    assert verification["verified"] is True
    assert verification["found_refs"] == [f"evidence:{evidence.evidence_id}"]
    assert verification["missing_refs"] == []
    assert any(node_id.startswith("evidence:") for node_id in verification["graph_delta"]["new_node_ids"])
    assert verification["can_update_claim_trust"] is False


def test_recording_effect_verification_reads_back_source_reconstruction_review(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.recording_navigator import verify_recording_effect
    from brain.v5.source_reconstruction_review import record_source_reconstruction_review_result

    ws, claim = _workspace_with_claim(tmp_path)
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="source_reconstruction",
        status="supports",
        summary="A source reconstruction review basis exists for definitions.",
        supports_outputs=["definitions"],
    )
    review = record_source_reconstruction_review_result(
        ws,
        claim_id=claim.claim_id,
        status="inconclusive",
        reviewed_components=["definitions"],
        evidence_refs=[evidence.evidence_id],
        remaining_actions=["review_remaining_source_reconstruction_components"],
        summary="Definitions have a typed basis, but source reconstruction remains incomplete.",
    )

    verification = verify_recording_effect(
        ws,
        "s1",
        expected_refs=[f"source_reconstruction_review:{review.result_id}"],
    )

    assert require_valid_public_surface("recording_effect_verification", verification) == verification
    assert verification["verified"] is True
    assert verification["found_refs"] == [f"source_reconstruction_review:{review.result_id}"]
    assert verification["missing_refs"] == []
    ref_item = verification["record_ref_lookup"]["refs"][0]
    assert ref_item["ref_kind"] == "source_reconstruction_review"
    assert ref_item["surface"] == "source_reconstruction_review_result_record"
    assert ref_item["record_kind"] == "source_reconstruction_review_result"
    assert ref_item["can_update_record_claim_trust"] is False
    assert verification["can_update_claim_trust"] is False


def test_recording_mcp_wrappers_and_cli_return_valid_surfaces(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import (
        aitp_v5_classify_recording_candidate,
        aitp_v5_expand_recording_slot,
        aitp_v5_get_recording_navigation_state,
        aitp_v5_verify_recording_effect,
    )

    ws, claim = _workspace_with_claim(tmp_path)
    del ws

    classified = aitp_v5_classify_recording_candidate(
        str(tmp_path),
        session_id="s1",
        event_type="result_observed",
        summary="A validation result was observed.",
        topic_id="fqhe",
        claim_id=claim.claim_id,
    )
    assert classified["kind"] == "recording_candidate_classification"
    assert classified["decision"] == "navigate"

    state = aitp_v5_get_recording_navigation_state(str(tmp_path), session_id="s1")
    assert state["kind"] == "recording_navigation_state"
    assert state["topic_id"] == "fqhe"

    expansion = aitp_v5_expand_recording_slot(str(tmp_path), session_id="s1", slot="validation_result")
    assert expansion["kind"] == "recording_slot_expansion"
    assert expansion["navigation_mode"] == "lightweight_slot_expansion"
    assert expansion["recommended_write_tool"] == "aitp_v5_record_validation_result"

    source_review = aitp_v5_expand_recording_slot(str(tmp_path), session_id="s1", slot="source_reconstruction_review")
    assert source_review["kind"] == "recording_slot_expansion"
    assert source_review["recommended_write_tool"] == "aitp_v5_record_source_reconstruction_review_result"

    verification = aitp_v5_verify_recording_effect(str(tmp_path), session_id="s1")
    assert verification["kind"] == "recording_effect_verification"
    assert verification["record_ref_lookup"]["lookup_count"] == 0

    assert main(["--base", str(tmp_path), "recording", "expand-slot", "s1", "--slot", "evidence"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["kind"] == "recording_slot_expansion"
    assert output["recommended_write_tool"] == "aitp_v5_record_evidence"


def test_recording_native_mcp_tools_list_advertises_navigator_tools():
    import brain.v5.native_mcp as native_mcp

    response = native_mcp._handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    tools = {tool["name"]: tool for tool in response["result"]["tools"]}

    expected_descriptions = {
        "aitp_v5_classify_recording_candidate": "classify a durable research event",
        "aitp_v5_get_recording_navigation_state": "read-only first-level aitp recording navigator",
        "aitp_v5_expand_recording_slot": "expand one aitp recording slot",
        "aitp_v5_verify_recording_effect": "verify typed refs or graph deltas",
    }
    for name, description in expected_descriptions.items():
        assert name in tools
        assert description in tools[name]["description"].lower()

    assert tools["aitp_v5_classify_recording_candidate"]["inputSchema"]["required"] == [
        "base",
        "event_type",
    ]
    assert tools["aitp_v5_get_recording_navigation_state"]["inputSchema"]["required"] == [
        "base",
        "session_id",
    ]


def _known(payload: dict, field: str) -> str:
    for item in payload["required_fields"] + payload["optional_fields"]:
        if item["name"] == field:
            return item["known_value"]
    raise AssertionError(field)
