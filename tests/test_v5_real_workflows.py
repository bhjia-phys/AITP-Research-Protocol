from __future__ import annotations


def test_fqhe_learning_to_idea_to_toy_check_workflow(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.evidence import record_evidence
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.references import record_reference_location
    from brain.v5.tool_executors import execute_registered_tool_result
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The counting sequence matches the candidate edge CFT in the recorded sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size aliasing",
    )
    record_reference_location(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        connector_id="local_pdf",
        location_type="paper_pdf",
        uri="file:///papers/fqhe/counting.pdf",
        label="FQHE counting reference",
        source_ref="paper:fqhe-counting",
    )
    counting = record_physics_object(ws, topic_id="fqhe", object_type="observable", name="counting", definition="Counting table.")
    cft = record_physics_object(ws, topic_id="fqhe", object_type="theory", name="edge CFT", definition="Candidate edge theory.")
    record_object_relation(
        ws,
        topic_id="fqhe",
        relation_type="matches",
        subject_id=counting.object_id,
        object_id=cft.object_id,
        statement="Counting table matches the edge CFT sequence.",
        claim_id=claim.claim_id,
        failure_modes=["wrong sector"],
    )
    result = execute_registered_tool_result(
        ws,
        executor_id="metric_table_check",
        recipe_id="recipe-fqhe-counting-table",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        inputs={
            "metrics": [
                {"name": "level-0", "observed": 1, "expected": 1, "tolerance": 0},
                {"name": "level-1", "observed": 1, "expected": 1, "tolerance": 0},
            ]
        },
        evidence_status="supports",
        supports_outputs=["evidence_or_provenance", "minimal_check"],
        evidence_type="toy_numeric",
    )
    record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="literature_synthesis",
        status="supports",
        summary="Reference location and convention source recorded.",
        supports_outputs=["evidence_or_provenance"],
        source_refs=["paper:fqhe-counting"],
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    assert result.evidence is not None
    assert brief["evidence_coverage"]["satisfied_outputs"]
    assert brief["known_context"]["reference_locations"]
    assert brief["known_context"]["object_relations"]


def test_gw_formula_code_translation_records_code_state_and_benchmark(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.code import record_code_state
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.tool_executors import execute_registered_tool_result
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The code path reproduces the benchmark after the self-energy change.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="formula-code translation",
    )
    code_state = record_code_state(
        ws,
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="master",
        upstream_commit="abc123",
        local_branch="topic/self-energy",
        worktree_path="D:/worktrees/librpa/self-energy",
        dirty=False,
        linked_records={"claim_id": claim.claim_id},
    )
    formula = record_physics_object(ws, topic_id="librpa-gw", object_type="formula", name="correlation self-energy", definition="GW correlation self-energy formula.")
    kernel = record_physics_object(ws, topic_id="librpa-gw", object_type="code_path", name="LibRPA self-energy kernel", definition="Implementation path under test.")
    record_object_relation(
        ws,
        topic_id="librpa-gw",
        relation_type="implements",
        subject_id=kernel.object_id,
        object_id=formula.object_id,
        statement="The code path implements the correlation self-energy formula.",
        claim_id=claim.claim_id,
        failure_modes=["frequency grid mismatch", "basis cutoff mismatch"],
    )
    execute_registered_tool_result(
        ws,
        executor_id="metric_table_check",
        recipe_id="recipe-librpa-gw-benchmark-table",
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        inputs={"metrics": [{"name": "gap_ev", "observed": 1.2, "expected": 1.2, "tolerance": 0.01}]},
        evidence_status="supports",
        code_state_ids=[code_state.code_state_id],
        supports_outputs=["evidence_or_provenance", "minimal_check"],
        evidence_type="code_method",
    )
    bind_session(ws, "s1", topic_id="librpa-gw", context_id="gw-methods", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    assert brief["known_context"]["object_relations"]
    assert "evidence_or_provenance" in brief["evidence_coverage"]["satisfied_outputs"]
