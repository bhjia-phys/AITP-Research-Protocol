from __future__ import annotations


def test_process_graph_slice_reads_typed_records_and_exposes_edges(tmp_path):
    from brain.v5.code import record_code_state
    from brain.v5.evidence import record_evidence
    from brain.v5.mcp_tools import aitp_v5_get_process_graph_slice
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.process_graph import build_process_graph_slice
    from brain.v5.process_graph_contracts import validate_process_graph_slice
    from brain.v5.references import record_reference_location
    from brain.v5.research_state import create_proof_obligation
    from brain.v5.sensemaking import record_sensemaking_report
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
        "reference_location",
        "evidence",
        "proof_obligation",
        "code_state",
        "tool_run",
        "validation_contract",
        "validation_result",
        "sensemaking_report",
    }.issubset(node_types)
    assert f"claim:{claim.claim_id}" in node_ids
    assert f"reference_location:{ref.location_id}" in node_ids
    assert f"proof_obligation:{obligation.obligation_id}" in node_ids
    assert f"sensemaking_report:{report.report_id}" in node_ids

    edges = {(edge["source"], edge["type"], edge["target"]) for edge in payload["edges"]}
    assert (f"claim:{claim.claim_id}", "has_evidence", f"evidence:{evidence.evidence_id}") in edges
    assert (f"claim:{claim.claim_id}", "has_reference_location", f"reference_location:{ref.location_id}") in edges
    assert (f"claim:{claim.claim_id}", "has_proof_obligation", f"proof_obligation:{obligation.obligation_id}") in edges
    assert (f"claim:{claim.claim_id}", "has_object_relation", f"object_relation:{relation.relation_id}") in edges
    assert (f"object_relation:{relation.relation_id}", "relation_subject", f"physics_object:{counting.object_id}") in edges
    assert (f"object_relation:{relation.relation_id}", "relation_object", f"physics_object:{cft.object_id}") in edges
    assert (f"evidence:{evidence.evidence_id}", "uses_tool_run", f"tool_run:{run.run_id}") in edges
    assert (f"evidence:{evidence.evidence_id}", "uses_validation_result", f"validation_result:{validation.result_id}") in edges
    assert (f"tool_run:{run.run_id}", "uses_code_state", f"code_state:{code_state.code_state_id}") in edges

    assert payload["open_obligations"][0]["obligation_id"] == obligation.obligation_id
    assert payload["source_backtrace"][0]["complete"] is True
    assert payload["relation_neighborhood"][0]["relation_id"] == relation.relation_id
    assert "this API cannot update claim trust" in payload["trust_boundary_reasons"]
    moments = {item["moment"] for item in payload["recommended_moments"]}
    assert "record_or_validate_open_obligation" in moments
    assert "brainstorm_relation_path" in moments


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
