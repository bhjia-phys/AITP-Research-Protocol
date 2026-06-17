from __future__ import annotations

import json


def test_process_graph_slice_reads_typed_records_and_exposes_edges(tmp_path):
    from brain.v5.code import record_code_state
    from brain.v5.evidence import record_evidence
    from brain.v5.exploration import record_exploratory_record
    from brain.v5.mcp_tools import aitp_v5_get_process_graph_slice
    from brain.v5.moment_policy_contracts import validate_host_agnostic_moment_policy
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.process_graph import build_process_graph_slice
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.process_graph_contracts import validate_process_graph_slice
    from brain.v5.references import record_reference_location
    from brain.v5.research_state import create_proof_obligation
    from brain.v5.sensemaking import record_sensemaking_report
    from brain.v5.source_assets import register_source_asset
    from brain.v5.tools import record_tool_run
    from brain.v5.validation import create_validation_contract, record_validation_result
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Sector-resolved counting identifies the edge CFT.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size aliasing",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    counting = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="observable",
        name="counting sequence",
        definition="Low-lying entanglement spectrum counting.",
    )
    cft = record_physics_object(
        ws,
        topic_id="fqhe",
        object_type="theory",
        name="edge CFT",
        definition="Candidate conformal field theory for the edge.",
    )
    ref = record_reference_location(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        connector_id="literature_search",
        location_type="paper",
        uri="arxiv:2601.00001",
        label="Edge counting source",
        source_ref="paper:edge-counting",
    )
    asset = register_source_asset(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        asset_type="paper",
        uri="arxiv:2601.00001",
        title="Edge counting source asset",
        source_kind="literature",
        source_refs=[ref.location_id],
        reference_location_ids=[ref.location_id],
        version_anchor={"arxiv_version": "v1"},
        summary="Canonical raw paper identity for source reconstruction.",
    )
    code_state = record_code_state(
        ws,
        repo_id="ed-code",
        upstream_remote="origin",
        upstream_branch="main",
        upstream_commit="abc123",
        local_branch="topic/fqhe",
        worktree_path=str(tmp_path / "ed-code"),
        dirty=False,
        linked_records={"claim_id": claim.claim_id},
    )
    run = record_tool_run(
        ws,
        recipe_id="ed-counting",
        tool_family="python",
        tool_name="counting_check",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        outputs={"matched": True},
        evidence_status="supports",
        code_state_ids=[code_state.code_state_id],
        source_refs=[ref.location_id],
    )
    contract = create_validation_contract(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        required_checks=["sector match"],
        failure_modes=["wrong momentum sector"],
        required_evidence_outputs=["sector_counting_check"],
        tool_recipe_ids=["ed-counting"],
    )
    validation = record_validation_result(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        contract_id=contract.contract_id,
        tool_run_id=run.run_id,
        status="passed",
        checked_outputs=["sector_counting_check"],
        covered_failure_modes=["wrong momentum sector"],
        summary="Sector counting check passed.",
    )
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="tool_run",
        status="supports",
        summary="Counting run supports the sector-resolved edge CFT identification.",
        supports_outputs=["sector_counting_check"],
        source_refs=[ref.location_id],
        tool_run_ids=[run.run_id],
        validation_result_ids=[validation.result_id],
    )
    relation = record_object_relation(
        ws,
        topic_id="fqhe",
        relation_type="diagnoses",
        subject_id=counting.object_id,
        object_id=cft.object_id,
        statement="The counting sequence diagnoses the edge CFT only after sector matching.",
        claim_id=claim.claim_id,
        failure_modes=["wrong momentum sector"],
        source_refs=[ref.location_id],
        evidence_refs=[evidence.evidence_id],
    )
    obligation = create_proof_obligation(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        statement="Prove the finite-size sector match is not an accidental alias.",
        obligation_type="proof_gap",
        status="open",
        maturity_level="theorem-candidate",
        next_action="derive sector matching constraints",
        required_evidence=["analytic derivation"],
        evidence_refs=[evidence.evidence_id],
    )
    report = record_sensemaking_report(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        title="Relation path sketch",
        summary="Counting is useful only through sector matching.",
        object_ids=[counting.object_id, cft.object_id],
        relation_ids=[relation.relation_id],
        evidence_refs=[evidence.evidence_id],
    )
    exploratory = record_exploratory_record(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        session_id="s1",
        exploration_type="relation_path_brainstorm",
        title="Backtrace counting to CFT",
        focal_question="Which intermediate definitions connect counting to edge CFT labels?",
        summary="The relation path is being explored before validation.",
        original_question="Does sector counting identify the edge CFT?",
        local_question="Trace sector matching definitions.",
        object_ids=[counting.object_id, cft.object_id],
        relation_ids=[relation.relation_id],
        source_refs=[ref.location_id],
        reasoning_moves=["why-question decomposition", "relation-path brainstorming"],
        backtrace_targets=[f"object:{counting.object_id}", f"object:{cft.object_id}"],
        candidate_paths=["counting sequence -> sector matching -> edge CFT"],
        relation_path_questions=["Which intermediate definition connects counting to edge CFT labels?"],
        definition_boundary_questions=["Where is sector matching defined on both sides?"],
        original_question_guard=["Keep relation brainstorming tied to edge-CFT identification."],
        unresolved_points=["finite-size aliasing"],
        next_actions=["open source backtrace"],
    )
    backtrace = record_exploratory_record(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        session_id="s1",
        exploration_type="backtrace_step",
        title="Trace sector matching source",
        focal_question="Where is the sector matching convention defined?",
        summary="The source dependency is being traced without changing claim trust.",
        original_question="Does sector counting identify the edge CFT?",
        local_question="Locate the sector matching convention.",
        source_refs=[ref.location_id],
        parent_record_ids=[exploratory.record_id],
        reasoning_moves=["source dependency backtrace", "bidirectional definition backtrace"],
        backtrace_targets=[f"source:{ref.location_id}", f"relation:{relation.relation_id}"],
        definition_boundary_questions=["Which source defines the sector matching convention?"],
        derivation_backtrace_questions=["Which derivation step assumes sector matching?"],
        source_dependency_questions=["Which cited source introduces the matching convention?"],
        original_question_guard=["Do not lose the edge-CFT identification question while tracing notation."],
        unresolved_points=["definition boundary not fully reconstructed"],
        next_actions=["reconstruct definition"],
    )

    payload = build_process_graph_slice(ws, "s1", limit=80)
    mcp_payload = aitp_v5_get_process_graph_slice(str(tmp_path), session_id="s1", limit=80)

    assert validate_process_graph_slice(payload).ok is True
    assert payload["kind"] == "process_graph_slice"
    assert payload["truth_source"] == "typed_records"
    assert payload["orientation_only"] is True
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False
    assert mcp_payload["kind"] == "process_graph_slice"

    node_ids = {node["id"] for node in payload["nodes"]}
    node_types = {node["type"] for node in payload["nodes"]}
    assert {
        "claim",
        "physics_object",
        "object_relation",
        "source_asset",
        "reference_location",
        "evidence",
        "proof_obligation",
        "code_state",
        "tool_run",
        "validation_contract",
        "validation_result",
        "sensemaking_report",
        "exploratory_record",
    }.issubset(node_types)
    assert f"claim:{claim.claim_id}" in node_ids
    assert f"reference_location:{ref.location_id}" in node_ids
    assert f"source_asset:{asset.asset_id}" in node_ids
    assert f"proof_obligation:{obligation.obligation_id}" in node_ids
    assert f"sensemaking_report:{report.report_id}" in node_ids
    assert f"exploratory_record:{exploratory.record_id}" in node_ids

    edges = {(edge["source"], edge["type"], edge["target"]) for edge in payload["edges"]}
    assert (f"claim:{claim.claim_id}", "has_evidence", f"evidence:{evidence.evidence_id}") in edges
    assert (f"claim:{claim.claim_id}", "has_reference_location", f"reference_location:{ref.location_id}") in edges
    assert (f"claim:{claim.claim_id}", "has_source_asset", f"source_asset:{asset.asset_id}") in edges
    assert (
        f"source_asset:{asset.asset_id}",
        "has_reference_location",
        f"reference_location:{ref.location_id}",
    ) in edges
    assert (f"claim:{claim.claim_id}", "has_proof_obligation", f"proof_obligation:{obligation.obligation_id}") in edges
    assert (f"claim:{claim.claim_id}", "has_object_relation", f"object_relation:{relation.relation_id}") in edges
    assert (f"object_relation:{relation.relation_id}", "relation_subject", f"physics_object:{counting.object_id}") in edges
    assert (f"object_relation:{relation.relation_id}", "relation_object", f"physics_object:{cft.object_id}") in edges
    assert (f"evidence:{evidence.evidence_id}", "uses_tool_run", f"tool_run:{run.run_id}") in edges
    assert (f"evidence:{evidence.evidence_id}", "uses_validation_result", f"validation_result:{validation.result_id}") in edges
    assert (f"tool_run:{run.run_id}", "uses_code_state", f"code_state:{code_state.code_state_id}") in edges
    assert (
        f"claim:{claim.claim_id}",
        "has_exploratory_record",
        f"exploratory_record:{exploratory.record_id}",
    ) in edges
    assert (
        f"exploratory_record:{exploratory.record_id}",
        "explores_relation",
        f"object_relation:{relation.relation_id}",
    ) in edges

    assert payload["open_obligations"][0]["obligation_id"] == obligation.obligation_id
    assert payload["open_obligations"][0]["topic_id"] == "fqhe"
    assert payload["open_obligations"][0]["severity"] == "blocking"
    assert payload["open_obligations"][0]["trust_boundary"] == "before_final_or_promotion"
    assert "aitp.create_open_obligation" in payload["open_obligations"][0]["suggested_moments"]
    assert payload["source_backtrace"][0]["complete"] is True
    assert payload["source_backtrace"][0]["topic_id"] == "fqhe"
    assert payload["source_backtrace"][0]["source_asset_ids"] == [asset.asset_id]
    assert payload["source_asset_index"][0]["asset_id"] == asset.asset_id
    assert payload["source_asset_index"][0]["asset_type"] == "paper"
    assert payload["source_asset_index"][0]["uri"] == "arxiv:2601.00001"
    assert payload["source_asset_index"][0]["version_anchor"] == {"arxiv_version": "v1"}
    assert payload["source_asset_index"][0]["reference_locations"][0]["reference_location_id"] == ref.location_id
    assert payload["source_asset_index"][0]["hash_status"] == "missing"
    assert payload["source_asset_index"][0]["orientation_only"] is True
    assert payload["source_asset_index"][0]["can_update_claim_trust"] is False
    provenance_gap = next(item for item in payload["provenance_gaps"] if item["gap_type"] == "source_asset_hash_missing")
    assert provenance_gap["target_refs"] == [f"source_asset:{asset.asset_id}"]
    assert provenance_gap["recommended_entrypoints"] == [
        "aitp_v5_capture_source_asset_auto",
        "aitp_v5_register_source_asset",
    ]
    auto_hint = _hint_by_entrypoint(provenance_gap, "aitp_v5_capture_source_asset_auto")
    assert auto_hint["record_action"] == "capture_source_asset_auto"
    assert auto_hint["required_fields"] == ["path", "topic_id"]
    assert auto_hint["draft"]["path"] == "<local source file path>"
    assert auto_hint["draft"]["topic_id"] == "fqhe"
    assert auto_hint["draft"]["claim_id"] == claim.claim_id
    assert auto_hint["draft"]["source_kind"] == "literature"
    assert auto_hint["draft_schema"]["required_fields"] == ["path", "topic_id"]
    assert auto_hint["draft_schema"]["placeholder_fields"] == ["path"]
    assert auto_hint["draft_schema"]["placeholder_values"] == {"path": "<local source file path>"}
    assert auto_hint["draft_schema"]["host_must_resolve"] == ["path"]
    assert auto_hint["draft_schema"]["summary_inputs_trusted"] is False
    assert auto_hint["draft_schema"]["can_update_claim_trust"] is False
    assert provenance_gap["required_before_trust_change"] is False
    assert payload["source_asset_index"][0]["provenance_gap_ids"] == [provenance_gap["gap_id"]]
    assert payload["source_asset_index"][0]["provenance_gap_types"] == ["source_asset_hash_missing"]
    assert payload["source_stack_coverage"]["kind"] == "source_stack_coverage_manifest"
    assert payload["source_stack_coverage"]["claim_count"] == 1
    assert payload["source_stack_coverage"]["orientation_only"] is True
    assert payload["source_stack_coverage"]["can_update_claim_trust"] is False
    assert payload["source_stack_coverage"]["coverage_status_counts"]["evidence_gap"] == 1
    coverage_item = payload["source_stack_coverage"]["items"][0]
    assert coverage_item["claim_id"] == claim.claim_id
    assert coverage_item["coverage_status"] == "evidence_gap"
    assert coverage_item["risk_level"] == "guided"
    assert coverage_item["missing_required_outputs"] == ["scoped_claim", "evidence_or_provenance"]
    assert "reconstruction_path" in coverage_item["missing_source_components"]
    assert coverage_item["source_reconstruction_review_status"] == "pending"
    assert "record_evidence_for_required_outputs:" + claim.claim_id in coverage_item["next_actions"]
    assert payload["record_counts"]["source_stack_coverage"] == 1
    assert payload["source_reconstruction_review"]["kind"] == "source_reconstruction_review_manifest"
    assert payload["source_reconstruction_review"]["claim_count"] == 1
    assert payload["source_reconstruction_review"]["orientation_only"] is True
    assert payload["source_reconstruction_review"]["can_update_claim_trust"] is False
    assert payload["source_reconstruction_review"]["review_progress"]["pending"] == 1
    review_item = payload["source_reconstruction_review"]["items"][0]
    assert review_item["claim_id"] == claim.claim_id
    assert review_item["source_reconstruction_status"] == "incomplete"
    assert review_item["review_status"] == "pending"
    assert "reconstruction_path" in review_item["missing_components"]
    assert review_item["review_packet_cli"] == f"aitp-v5 source reconstruction-review --claim {claim.claim_id}"
    assert "source_reconstruction_review" in review_item["next_actions"]
    assert f"source_reconstruction_review:{claim.claim_id}" in payload["source_reconstruction_review"]["next_actions"]
    assert payload["record_counts"]["source_reconstruction_review"] == 1
    assert payload["relation_neighborhood"][0]["relation_id"] == relation.relation_id
    assert payload["relation_neighborhood"][0]["topic_id"] == "fqhe"
    assert "relation-path brainstorming" in payload["relation_neighborhood"][0]["reasoning_moves"]
    assert "counting sequence -> sector matching -> edge CFT" in payload["relation_neighborhood"][0][
        "candidate_paths"
    ]
    assert "Which intermediate definition connects counting to edge CFT labels?" in payload[
        "relation_neighborhood"
    ][0]["relation_path_questions"]
    assert "Where is sector matching defined on both sides?" in payload["relation_neighborhood"][0][
        "definition_boundary_questions"
    ]
    exploratory_ids = {item["record_id"] for item in payload["exploratory_records"]}
    assert exploratory.record_id in exploratory_ids
    assert backtrace.record_id in exploratory_ids
    assert payload["source_backtrace"][0]["exploratory_record_ids"] == [backtrace.record_id]
    assert "source dependency backtrace" in payload["source_backtrace"][0]["reasoning_moves"]
    assert f"source:{ref.location_id}" in payload["source_backtrace"][0]["backtrace_targets"]
    assert "Which source defines the sector matching convention?" in payload["source_backtrace"][0][
        "definition_boundary_questions"
    ]
    assert "Which derivation step assumes sector matching?" in payload["source_backtrace"][0][
        "derivation_backtrace_questions"
    ]
    assert "Which cited source introduces the matching convention?" in payload["source_backtrace"][0][
        "source_dependency_questions"
    ]
    assert "this API cannot update claim trust" in payload["trust_boundary_reasons"]
    policy = payload["moment_policy"]
    assert validate_host_agnostic_moment_policy(policy).ok is True
    assert require_valid_public_surface("host_agnostic_moment_policy", policy) == policy
    assert policy["kind"] == "host_agnostic_moment_policy"
    assert policy["derived_from"] == "process_graph_slice"
    assert policy["orientation_only"] is True
    assert policy["can_update_claim_trust"] is False
    decision_types = {item["decision_type"] for item in policy["decisions"]}
    assert {"recording", "brainstorming", "backtrace", "trust_boundary"}.issubset(decision_types)
    assert any(item["moment"] == "trust_boundary_before_claim_update" for item in policy["decisions"])
    by_policy_moment = {item["moment"]: item for item in policy["decisions"]}
    recording_decision = by_policy_moment["record_or_validate_open_obligation"]
    assert recording_decision["required_now"] is True
    assert recording_decision["target_type"] == "proof_obligation"
    assert recording_decision["target_id"] == obligation.obligation_id
    assert "aitp_v5_record_evidence" in recording_decision["record_entrypoints"]
    assert "aitp_v5_record_validation_result" in recording_decision["entrypoints"]
    assert "aitp_v5_preflight_trust_update" in recording_decision["entrypoints"]
    assert recording_decision["trust_boundary"] == bool(recording_decision["required_before_trust_change"])
    evidence_hint = _hint_by_entrypoint(recording_decision, "aitp_v5_record_evidence")
    assert evidence_hint["record_action"] == "record_evidence"
    assert evidence_hint["orientation_only"] is True
    assert evidence_hint["summary_inputs_trusted"] is False
    assert evidence_hint["can_update_claim_trust"] is False
    assert evidence_hint["draft"]["topic_id"] == "fqhe"
    assert evidence_hint["draft"]["claim_id"] == claim.claim_id
    assert evidence_hint["draft"]["evidence_type"] == "proof_obligation_resolution"
    assert "analytic derivation" in evidence_hint["draft"]["supports_outputs"]
    assert "source-grounded evidence summary" in evidence_hint["draft"]["summary"]
    recording_preflight_hint = _hint_by_entrypoint(recording_decision, "aitp_v5_preflight_trust_update")
    assert recording_preflight_hint["record_action"] == "preflight_trust_update"
    assert recording_preflight_hint["orientation_only"] is True
    assert recording_preflight_hint["summary_inputs_trusted"] is False
    assert recording_preflight_hint["can_update_claim_trust"] is False
    assert recording_preflight_hint["draft"]["action"] == "change_claim_confidence"
    assert recording_preflight_hint["draft"]["session_id"] == "s1"
    assert recording_preflight_hint["draft"]["topic_id"] == "fqhe"
    assert recording_preflight_hint["draft"]["claim_id"] == claim.claim_id
    assert recording_preflight_hint["draft"]["source_kind"] == "proof_obligation_record"
    assert recording_preflight_hint["draft"]["source_ref"] == f"proof_obligation:{obligation.obligation_id}"
    assert recording_decision["lifecycle_phases"] == ["pre_turn", "pre_action", "pre_final"]
    assert recording_decision["recording_threshold"] == "blocking_before_final_or_promotion"
    assert "at pre_turn because required_now is true" in recording_decision["trigger_conditions"]
    assert recording_decision["trust_boundary_inputs"]["target_refs"] == [
        f"proof_obligation:{obligation.obligation_id}"
    ]
    assert recording_decision["trust_boundary_inputs"]["entrypoints"] == recording_decision["entrypoints"]
    assert recording_decision["trust_boundary_inputs"]["requires_preflight"] is True
    assert recording_decision["trust_boundary_inputs"]["final_gate_required"] is True
    assert any("current-turn obligation" in item for item in recording_decision["recommended_host_behavior"])
    relation_decision = next(
        item
        for item in policy["decisions"]
        if item["decision_type"] == "brainstorming" and item["target_type"] == "object_relation"
    )
    assert relation_decision["required_now"] is False
    assert relation_decision["exploration_entrypoints"] == ["aitp_v5_record_exploratory_record"]
    assert relation_decision["entrypoints"] == [
        "aitp_v5_record_exploratory_record",
        "aitp_v5_preflight_trust_update",
    ]
    exploration_hint = _hint_by_entrypoint(relation_decision, "aitp_v5_record_exploratory_record")
    assert exploration_hint["record_action"] == "record_exploratory_record"
    assert exploration_hint["draft"]["topic_id"] == "fqhe"
    assert exploration_hint["draft"]["claim_id"] == claim.claim_id
    assert exploration_hint["draft"]["exploration_type"] == "relation_path_brainstorm"
    assert "relation-path brainstorming" in exploration_hint["draft"]["reasoning_moves"]
    assert f"object:{counting.object_id}" in exploration_hint["draft"]["backtrace_targets"]
    assert "Which intermediate definition connects counting to edge CFT labels?" in exploration_hint[
        "draft"
    ]["relation_path_questions"]
    assert "Where is sector matching defined on both sides?" in exploration_hint["draft"][
        "definition_boundary_questions"
    ]
    assert "Keep relation brainstorming tied to edge-CFT identification." in exploration_hint["draft"][
        "original_question_guard"
    ]
    assert relation_decision["lifecycle_phases"] == ["pre_turn", "pre_action", "pre_final"]
    assert relation_decision["recording_threshold"] == "recommended_before_using_hypothesis_or_exploration"
    assert "before using the brainstormed path as claim support or validation basis" in relation_decision[
        "trigger_conditions"
    ]
    assert relation_decision["trust_boundary_inputs"]["target_refs"] == [f"object_relation:{relation.relation_id}"]
    assert relation_decision["trust_boundary_inputs"]["requires_preflight"] is True
    assert relation_decision["trust_boundary_inputs"]["final_gate_required"] is True
    backtrace_decision = next(
        item
        for item in policy["decisions"]
        if item["decision_type"] == "backtrace" and item["target_id"] == backtrace.record_id
    )
    assert backtrace_decision["lifecycle_phases"] == ["pre_turn", "pre_action"]
    assert backtrace_decision["recording_threshold"] == "recommended_before_following_source_chain"
    assert "when source backtrace reports missing or open reconstruction components" in backtrace_decision[
        "trigger_conditions"
    ]
    assert backtrace_decision["trust_boundary_inputs"]["target_refs"] == [
        f"exploratory_record:{backtrace.record_id}"
    ]
    assert backtrace_decision["trust_boundary_inputs"]["requires_preflight"] is False
    trust_decision = by_policy_moment["trust_boundary_before_claim_update"]
    assert trust_decision["required_now"] is True
    assert trust_decision["decision_type"] == "trust_boundary"
    assert trust_decision["entrypoints"] == ["aitp_v5_preflight_trust_update"]
    trust_preflight_hint = _hint_by_entrypoint(trust_decision, "aitp_v5_preflight_trust_update")
    assert trust_preflight_hint["record_action"] == "preflight_trust_update"
    assert trust_preflight_hint["draft"]["session_id"] == "s1"
    assert trust_preflight_hint["draft"]["topic_id"] == "fqhe"
    assert trust_preflight_hint["draft"]["claim_id"] == claim.claim_id
    assert trust_preflight_hint["draft"]["source_ref"] == f"claim:{claim.claim_id}"
    assert trust_decision["lifecycle_phases"] == ["pre_action", "pre_final"]
    assert trust_decision["recording_threshold"] == "blocking_before_claim_trust_update"
    assert "before any claim-trust update" in trust_decision["trigger_conditions"]
    assert trust_decision["trust_boundary_inputs"]["target_refs"] == [f"claim:{claim.claim_id}"]
    assert trust_decision["trust_boundary_inputs"]["requires_preflight"] is True
    assert trust_decision["trust_boundary_inputs"]["final_gate_required"] is True
    assert any("pre_final" in item for item in trust_decision["recommended_host_behavior"])
    moments = {item["moment"] for item in payload["recommended_moments"]}
    assert "record_or_validate_open_obligation" in moments
    assert "brainstorm_relation_path" in moments
    assert "audit_original_question_drift" in moments
    by_moment = {item["moment"]: item for item in payload["recommended_moments"]}
    assert by_moment["record_or_validate_open_obligation"]["priority"] == "blocking"
    assert by_moment["record_or_validate_open_obligation"]["timing"] == "before_final_or_promotion"
    assert by_moment["brainstorm_relation_path"]["timing"] == "before_using_relation_as_claim"
    assert by_moment["audit_original_question_drift"]["trust_boundary"] == "question_continuity"


def test_process_graph_policy_payload_hints_for_missing_source_components(tmp_path):
    from brain.v5.process_graph import build_process_graph_slice
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="theoretical-physics", title="QG algebra")
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="A candidate algebraic split may model an observer role.",
        evidence_profile="source_reconstruction",
        confidence_state="hypothesis",
        active_uncertainty="source chain unclear",
    )
    bind_session(ws, "s-missing", topic_id="qg", context_id="theoretical-physics", active_claim=claim.claim_id)

    payload = build_process_graph_slice(ws, "s-missing", limit=20)
    policy = payload["moment_policy"]
    backtrace_decision = next(item for item in policy["decisions"] if item["decision_type"] == "backtrace")
    reference_hint = _hint_by_entrypoint(backtrace_decision, "aitp_v5_record_reference_location")

    assert backtrace_decision["required_now"] is True
    assert backtrace_decision["lifecycle_phases"] == ["pre_turn", "pre_action", "pre_final"]
    assert backtrace_decision["recording_threshold"] == "required_before_source_dependent_support"
    assert "before using the target claim or source chain as support" in backtrace_decision["trigger_conditions"]
    assert backtrace_decision["trust_boundary_inputs"]["target_refs"] == [f"claim:{claim.claim_id}"]
    assert backtrace_decision["trust_boundary_inputs"]["requires_preflight"] is True
    assert backtrace_decision["trust_boundary_inputs"]["final_gate_required"] is True
    assert reference_hint["record_action"] == "record_reference_location"
    assert reference_hint["orientation_only"] is True
    assert reference_hint["summary_inputs_trusted"] is False
    assert reference_hint["can_update_claim_trust"] is False
    assert reference_hint["draft"]["topic_id"] == "qg"
    assert reference_hint["draft"]["claim_id"] == claim.claim_id
    assert reference_hint["draft"]["location_type"] == "paper_section"
    assert reference_hint["draft"]["uri"] == "<source URI>"
    assert reference_hint["draft_schema"]["required_fields"] == [
        "topic_id",
        "connector_id",
        "location_type",
        "uri",
        "label",
    ]
    assert reference_hint["draft_schema"]["placeholder_values"]["uri"] == "<source URI>"
    assert "uri" in reference_hint["draft_schema"]["host_must_resolve"]


def test_process_graph_slice_exposes_source_code_provenance_gaps(tmp_path):
    from brain.v5.process_graph import build_process_graph_slice
    from brain.v5.process_graph_contracts import validate_process_graph_slice
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "gw", context_id="code-method", title="GW code method")
    claim = create_claim(
        ws,
        topic_id="gw",
        statement="A code benchmark reproduces the Si GW reference.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="code provenance and benchmark artifact not captured",
    )
    bind_session(ws, "s-gw", topic_id="gw", context_id="code-method", active_claim=claim.claim_id)

    payload = build_process_graph_slice(ws, "s-gw", limit=40)

    assert validate_process_graph_slice(payload).ok is True
    by_type = {item["gap_type"]: item for item in payload["provenance_gaps"]}
    assert {
        "reference_location_missing",
        "source_asset_missing",
        "code_state_missing",
        "tool_run_missing",
        "validation_contract_missing",
    }.issubset(by_type)
    source_gap = by_type["source_asset_missing"]
    assert source_gap["recommended_entrypoints"] == [
        "aitp_v5_capture_source_asset_auto",
        "aitp_v5_register_source_asset",
    ]
    source_auto_hint = _hint_by_entrypoint(source_gap, "aitp_v5_capture_source_asset_auto")
    assert source_auto_hint["record_action"] == "capture_source_asset_auto"
    assert source_auto_hint["draft"]["path"] == "<local source file path>"
    assert source_auto_hint["draft"]["topic_id"] == "gw"
    assert source_auto_hint["draft"]["claim_id"] == claim.claim_id
    assert source_auto_hint["draft_schema"]["placeholder_fields"] == ["path"]
    assert source_auto_hint["draft_schema"]["host_must_resolve"] == ["path"]
    code_gap = by_type["code_state_missing"]
    assert code_gap["recommended_entrypoints"] == ["aitp_v5_capture_code_state_auto", "aitp_v5_record_code_state"]
    assert code_gap["recommended_actions"] == ["aitp.capture_code_state_auto", "aitp.record_code_state"]
    code_hint = _hint_by_entrypoint(code_gap, "aitp_v5_capture_code_state_auto")
    assert code_hint["record_action"] == "capture_code_state_auto"
    assert code_hint["orientation_only"] is True
    assert code_hint["summary_inputs_trusted"] is False
    assert code_hint["can_update_claim_trust"] is False
    assert code_hint["draft"]["topic_id"] == "gw"
    assert code_hint["draft"]["claim_id"] == claim.claim_id
    assert code_hint["draft"]["worktree_path"] == "<local worktree path>"
    assert code_hint["draft"]["linked_records"]["claim_id"] == claim.claim_id
    assert code_hint["draft_schema"]["placeholder_values"]["worktree_path"] == "<local worktree path>"
    assert "worktree_path" in code_hint["draft_schema"]["host_must_resolve"]
    assert code_gap["required_now"] is False
    assert code_gap["required_before_trust_change"] is False
    assert "benchmark_basis" in code_gap["blocking_when_used_as"]
    tool_gap = by_type["tool_run_missing"]
    assert tool_gap["recommended_entrypoints"] == [
        "aitp_v5_capture_tool_run_auto",
        "aitp_v5_record_tool_run",
    ]
    assert tool_gap["recommended_actions"] == ["aitp.capture_tool_run_auto", "aitp.record_tool_run"]
    tool_auto_hint = _hint_by_entrypoint(tool_gap, "aitp_v5_capture_tool_run_auto")
    assert tool_auto_hint["record_action"] == "capture_tool_run_auto"
    assert tool_auto_hint["draft"]["path"] == "<local tool transcript or result file path>"
    assert tool_auto_hint["draft"]["topic_id"] == "gw"
    assert tool_auto_hint["draft"]["claim_id"] == claim.claim_id
    assert tool_auto_hint["draft"]["recipe_id"] == "<tool recipe id>"
    assert tool_auto_hint["draft_schema"]["placeholder_values"]["path"] == (
        "<local tool transcript or result file path>"
    )
    assert tool_auto_hint["draft_schema"]["placeholder_values"]["recipe_id"] == "<tool recipe id>"
    tool_hint = _hint_by_entrypoint(tool_gap, "aitp_v5_record_tool_run")
    assert tool_hint["record_action"] == "record_tool_run"
    assert tool_hint["draft"]["topic_id"] == "gw"
    assert tool_hint["draft"]["claim_id"] == claim.claim_id
    assert tool_hint["draft"]["recipe_id"] == "<tool recipe id>"
    contract_hint = _hint_by_entrypoint(
        by_type["validation_contract_missing"],
        "aitp_v5_create_validation_contract",
    )
    assert contract_hint["record_action"] == "create_validation_contract"
    assert "check expected outputs" in contract_hint["draft"]["required_checks"]
    assert contract_hint["draft"]["validator_role"] == "adversarial_reviewer"
    moments = [item for item in payload["recommended_moments"] if item["moment"] == "capture_source_or_code_provenance"]
    assert moments


def test_source_asset_hash_gap_is_resolved_by_hashed_derived_asset(tmp_path):
    from brain.v5.process_graph import build_process_graph_slice
    from brain.v5.process_graph_contracts import validate_process_graph_slice
    from brain.v5.source_assets import capture_source_asset_from_local_path, register_source_asset
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "paper", context_id="literature", title="Paper")
    claim = create_claim(
        ws,
        topic_id="paper",
        statement="The literature claim depends on a canonical paper identity.",
        evidence_profile="literature-summary",
        confidence_state="hypothesis",
        active_uncertainty="source identity must stay reconstructable",
    )
    bind_session(ws, "s-paper", topic_id="paper", context_id="literature", active_claim=claim.claim_id)

    canonical = register_source_asset(
        ws,
        topic_id="paper",
        claim_id=claim.claim_id,
        asset_type="paper",
        uri="doi:10.1234/example",
        title="Canonical DOI identity",
        source_kind="literature",
        summary="DOI identity without a local byte hash.",
    )
    local_pdf = tmp_path / "paper.pdf"
    local_pdf.write_bytes(b"%PDF-1.4\nexample\n")
    derived = capture_source_asset_from_local_path(
        ws,
        path=str(local_pdf),
        topic_id="paper",
        claim_id=claim.claim_id,
        asset_type="paper",
        title="Canonical paper local PDF",
        derived_from=[canonical.asset_id],
        summary="Local PDF copy with stable hash.",
    )

    payload = build_process_graph_slice(ws, "s-paper", limit=40)

    assert validate_process_graph_slice(payload).ok is True
    gaps = [
        item
        for item in payload["provenance_gaps"]
        if item["gap_type"] == "source_asset_hash_missing"
    ]
    assert gaps == []
    index = {item["asset_id"]: item for item in payload["source_asset_index"]}
    assert index[canonical.asset_id]["hash_status"] == "resolved_by_derived_asset"
    assert index[canonical.asset_id]["hash_resolution_refs"] == [f"source_asset:{derived.asset_id}"]
    assert index[canonical.asset_id]["provenance_gap_types"] == []
    assert index[derived.asset_id]["hash_status"] == "present"


def test_process_graph_slice_exposes_workspace_migration_health_boundary(tmp_path):
    from brain.v5.process_graph import build_process_graph_slice
    from brain.v5.process_graph_contracts import validate_process_graph_slice
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Legacy migration requires semantic review.",
        evidence_profile="legacy_migration",
        confidence_state="hypothesis",
        active_uncertainty="legacy L2 seed reassignment is incomplete",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    ledger_dir = ws.root / "migrations" / "workspace-inventory"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    (ledger_dir / "workspace_file_migration_ledger.json").write_text(
        json.dumps(
            {
                "kind": "aitp_workspace_file_migration_ledger",
                "workspace_root": str(tmp_path),
                "canonical_topics_root": str(ws.base),
                "canonical_store": str(ws.root),
                "summary": {
                    "file_decision_count": 1,
                    "expected_total_file_count": 1,
                    "no_omission_check": True,
                    "blocking_file_count": 1,
                    "decision_counts": {"semantic_review_basis": 1},
                    "review_status_counts": {"semantic_review_required": 1},
                    "old_store_retirement_safe": False,
                    "semantic_review_required": True,
                    "root_l2_global_memory_decision_count": 1,
                    "root_l2_global_memory_topic_count": 1,
                    "root_l2_global_memory_entries_per_topic": 1,
                    "root_l2_global_memory_replay_key_count": 0,
                    "root_l2_global_memory_max_topic_repetition": 1,
                    "root_l2_global_memory_uniform_topic_copy_pattern": True,
                    "root_l2_global_memory_risk": True,
                    "root_l2_global_memory_risk_triggers": ["uniform_entries_per_topic"],
                    "root_l2_global_memory_risk_reason": "root L2 entries require semantic reassignment",
                },
                "file_decisions": [
                    {
                        "decision_ref": "legacy:fqhe:L2/entries/claim.md",
                        "topic_id": "fqhe",
                        "source_family": "legacy_accounting",
                        "source_path": "L2/entries/claim.md",
                        "recommended_decision": "semantic_review_basis",
                        "review_status": "semantic_review_required",
                        "blocks_old_store_retirement": True,
                        "summary_inputs_trusted": False,
                        "can_update_claim_trust": False,
                    }
                ],
                "orientation_only": True,
                "summary_inputs_trusted": False,
                "can_update_kernel_state": False,
                "can_update_claim_trust": False,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    seed_dir = ws.root / "memory" / "l2" / "entries"
    seed_dir.mkdir(parents=True, exist_ok=True)
    (seed_dir / "memory-legacy-l2-fqhe-claim.md").write_text(
        "\n".join(
            [
                "---",
                "entry_id: memory-legacy-l2-fqhe-claim",
                "topic_id: fqhe",
                "source_topic_id: L2",
                f"source_claim_id: {claim.claim_id}",
                "status: legacy_seed",
                "memory_kind: legacy_l2_entry:claim",
                "source_packet_id: legacy_l2:L2/entries/claim.md",
                "---",
                "Legacy seed body.",
                "",
            ],
        ),
        encoding="utf-8",
    )

    payload = build_process_graph_slice(ws, "s1", limit=80)

    assert validate_process_graph_slice(payload).ok is True
    assert require_valid_public_surface(
        "workspace_migration_health",
        payload["migration_health"],
    ) == payload["migration_health"]
    assert payload["migration_health"]["status"] == "blocked"
    assert payload["migration_health"]["old_store_retirement_safe"] is False
    assert payload["migration_health"]["root_l2_global_memory_risk"] is True
    assert payload["migration_health"]["canonical_legacy_seed_count"] == 1
    assert payload["migration_health"]["active_legacy_seed_count"] == 0
    assert payload["migration_health"]["legacy_seed_review_group_count"] == 1
    assert payload["migration_health"]["legacy_seed_open_review_group_count"] == 1
    assert payload["migration_health"]["legacy_seed_reviewed_group_count"] == 0
    assert payload["migration_health"]["legacy_seed_terminal_review_group_count"] == 0
    assert payload["migration_health"]["legacy_seed_topic_scope_mismatch_count"] == 0
    assert payload["migration_health"]["legacy_seed_review_groups"][0]["memory_role"] == "claim"
    assert "use_legacy_l2_seed_review_worklist_for_grouped_semantic_reassignment" in (
        payload["migration_health"]["next_actions"]
    )
    assert "legacy_seed memory is recovery orientation only" in "\n".join(
        payload["migration_health"]["summary_lines"],
    )
    assert "topic-level semantic review can be complete while open per-seed L2 review remains required" in "\n".join(
        payload["migration_health"]["summary_lines"],
    )
    assert "canonical legacy L2 seed memory must not be treated as active claim support" in "\n".join(
        payload["trust_boundary_reasons"],
    )


def test_process_graph_slice_returns_unbound_orientation_surface_for_missing_topic_session(tmp_path):
    from brain.v5.process_graph import build_process_graph_slice
    from brain.v5.process_graph_contracts import validate_process_graph_slice
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)

    payload = build_process_graph_slice(ws, "topic:l0-l4", limit=20)

    assert validate_process_graph_slice(payload).ok is True
    assert payload["recovery_selection_source"] == "unbound_session"
    assert payload["topic_id"] == "unbound-session"
    assert payload["migration_health"]["kind"] == "aitp_workspace_migration_health"
    assert payload["provenance_gaps"][0]["gap_type"] == "session_binding_missing"
    assert "requested session binding is missing or malformed" in "\n".join(
        payload["trust_boundary_reasons"],
    )


def test_mcp_bind_session_normalizes_topic_token_session_ids(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_bind_session

    payload = aitp_v5_bind_session(
        str(tmp_path),
        session_id="topic:l0-l4",
        topic_id="l0-l4",
        context_id="frame.aitp.l0-l4",
    )

    assert payload["ok"] is True
    assert payload["requested_session_id"] == "topic:l0-l4"
    assert payload["session_id"] == "session-l0-l4-recovery"
    assert (tmp_path / ".aitp" / "runtime" / "sessions" / "session-l0-l4-recovery.md").exists()


def test_process_graph_slice_is_registered_for_native_mcp_and_runtime_entrypoints():
    from brain.v5.native_mcp import _TOOLS
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    assert "aitp_v5_get_process_graph_slice" in _TOOLS
    assert runtime_entrypoints()["process_graph_slice"] == {
        "cli": "aitp-v5 graph slice <session-id>",
        "mcp": "aitp_v5_get_process_graph_slice",
        "surface": "process_graph_slice",
    }
    assert validate_runtime_entrypoints() == []


def _hint_by_entrypoint(decision: dict, entrypoint: str) -> dict:
    for hint in decision["payload_hints"]:
        if hint["entrypoint"] == entrypoint:
            return hint
    raise AssertionError(f"missing payload hint {entrypoint}")
