from __future__ import annotations


def test_fqhe_learning_to_idea_to_toy_check_workflow(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.evidence import record_evidence
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.references import record_reference_location
    from brain.v5.tool_executors import execute_registered_tool_result
    from brain.v5.validation import create_validation_contract, record_validation_result
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
    contract = create_validation_contract(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        required_checks=["finite-size counting table agrees level by level"],
        failure_modes=["wrong sector", "finite-size aliasing"],
        required_evidence_outputs=["all_within_tolerance"],
        tool_recipe_ids=["recipe-fqhe-counting-table"],
        executor_ids=["metric_table_check"],
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
    validation = record_validation_result(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        contract_id=contract.contract_id,
        tool_run_id=result.run.run_id,
        status="passed",
        checked_outputs=["all_within_tolerance"],
        evidence_refs=[result.evidence.evidence_id],
        summary="Finite-size counting table passed the required benchmark.",
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
    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim",
        scope="recorded finite-size sector",
        evidence_refs=[result.evidence.evidence_id],
        validation_result_ids=[validation.result_id],
        non_claims=["Does not prove thermodynamic-limit uniqueness."],
        known_failure_modes=["wrong sector", "finite-size aliasing"],
    )
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        reason="Promote validated finite-size counting claim to scoped L2 memory.",
        requested_by="real_workflow_acceptance",
        options=["approve", "reject"],
    )
    decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="Tool evidence has a passed validation result and the memory scope is explicit.",
        decided_by="human",
    )
    memory = apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=checkpoint.checkpoint_id)
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    assert result.evidence is not None
    assert memory.evidence_refs == [result.evidence.evidence_id]
    assert brief["evidence_coverage"]["satisfied_outputs"]
    assert brief["known_context"]["reference_locations"]
    assert brief["known_context"]["object_relations"]
    assert brief["known_context"]["memory_entries"] == [
        {
            "entry_id": memory.entry_id,
            "memory_kind": "scoped_claim",
            "scope": "recorded finite-size sector",
            "evidence_refs": [result.evidence.evidence_id],
            "source_packet_id": packet.packet_id,
            "human_checkpoint_id": checkpoint.checkpoint_id,
            "orientation_only": True,
        }
    ]


def test_gw_formula_code_translation_records_code_state_and_benchmark(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.code import record_code_state
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.tool_executors import execute_registered_tool_result
    from brain.v5.validation import create_validation_contract, record_validation_result
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
    contract = create_validation_contract(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        required_checks=["benchmark gap remains within tolerance after formula-code translation"],
        failure_modes=["frequency grid mismatch", "basis cutoff mismatch"],
        required_evidence_outputs=["all_within_tolerance"],
        tool_recipe_ids=["recipe-librpa-gw-benchmark-table"],
        executor_ids=["metric_table_check"],
    )
    result = execute_registered_tool_result(
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
    validation = record_validation_result(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        contract_id=contract.contract_id,
        tool_run_id=result.run.run_id,
        status="passed",
        checked_outputs=["all_within_tolerance"],
        evidence_refs=[result.evidence.evidence_id],
        summary="GW benchmark gap passed for the recorded code state.",
    )
    packet = create_promotion_packet(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        proposed_memory_kind="code_method_claim",
        scope="librpa commit abc123 self-energy worktree",
        evidence_refs=[result.evidence.evidence_id],
        validation_result_ids=[validation.result_id],
        non_claims=["Does not validate other upstream commits."],
        known_failure_modes=["frequency grid mismatch", "basis cutoff mismatch"],
    )
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        reason="Promote validated GW code-method benchmark to scoped L2 memory.",
        requested_by="real_workflow_acceptance",
        options=["approve", "reject"],
    )
    decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="Benchmark evidence is tied to the exact code state and passed validation.",
        decided_by="human",
    )
    memory = apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=checkpoint.checkpoint_id)
    bind_session(ws, "s1", topic_id="librpa-gw", context_id="gw-methods", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")

    assert memory.evidence_refs == [result.evidence.evidence_id]
    assert brief["known_context"]["object_relations"]
    assert "evidence_or_provenance" in brief["evidence_coverage"]["satisfied_outputs"]
    assert brief["known_context"]["memory_entries"] == [
        {
            "entry_id": memory.entry_id,
            "memory_kind": "code_method_claim",
            "scope": "librpa commit abc123 self-energy worktree",
            "evidence_refs": [result.evidence.evidence_id],
            "code_state_ids": [code_state.code_state_id],
            "source_packet_id": packet.packet_id,
            "human_checkpoint_id": checkpoint.checkpoint_id,
            "orientation_only": True,
        }
    ]


def test_gw_high_risk_promotion_uses_tool_backed_failure_mode_review_basis(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.code import record_code_state
    from brain.v5.failure_mode_review import (
        record_failure_mode_review_result,
        request_failure_mode_review_checkpoint,
    )
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.memory_audit import audit_l2_memory_context
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy
    from brain.v5.tool_executors import execute_registered_tool_result
    from brain.v5.validation import create_validation_contract, record_validation_result
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The self-energy code path reproduces the GW benchmark.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="formula-code translation",
        strongest_failure_mode="frequency grid mismatch",
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
    benchmark_contract = create_validation_contract(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        required_checks=["GW benchmark table within tolerance"],
        failure_modes=["frequency grid mismatch"],
        required_evidence_outputs=["all_within_tolerance"],
        tool_recipe_ids=["recipe-librpa-gw-benchmark-table"],
        executor_ids=["metric_table_check"],
        validator_role="benchmark_validator",
    )
    benchmark = execute_registered_tool_result(
        ws,
        executor_id="metric_table_check",
        recipe_id="recipe-librpa-gw-benchmark-table",
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        inputs={"metrics": [{"name": "gap_ev", "observed": 1.2, "expected": 1.2, "tolerance": 0.01}]},
        code_state_ids=[code_state.code_state_id],
        supports_outputs=["evidence_or_provenance", "minimal_check"],
        evidence_type="code_method",
    )
    benchmark_validation = record_validation_result(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        contract_id=benchmark_contract.contract_id,
        tool_run_id=benchmark.run.run_id,
        status="passed",
        checked_outputs=["all_within_tolerance"],
        evidence_refs=[benchmark.evidence.evidence_id],
        summary="GW benchmark table stayed within tolerance.",
    )
    basis_contract = create_validation_contract(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        required_checks=["Each promotion failure mode has concrete review basis"],
        failure_modes=["frequency grid mismatch"],
        required_evidence_outputs=["all_failure_modes_covered"],
        tool_recipe_ids=["recipe-librpa-gw-failure-mode-review-basis"],
        executor_ids=["failure_mode_basis_check"],
        validator_role="failure_mode_basis_validator",
    )
    basis = execute_registered_tool_result(
        ws,
        executor_id="failure_mode_basis_check",
        recipe_id="recipe-librpa-gw-failure-mode-review-basis",
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        inputs={
            "failure_modes": ["frequency grid mismatch"],
            "basis_items": [
                {
                    "failure_mode": "frequency grid mismatch",
                    "basis_ref": benchmark_validation.result_id,
                    "basis_type": "validation_result",
                    "question_answered": "The frequency-grid-sensitive benchmark stayed inside tolerance.",
                }
            ],
        },
        code_state_ids=[code_state.code_state_id],
        supports_outputs=["failure_mode_review_basis", "minimal_check"],
        evidence_type="code_method",
        evidence_summary="Failure-mode basis check covered the recorded GW risk.",
    )
    basis_validation = record_validation_result(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        contract_id=basis_contract.contract_id,
        tool_run_id=basis.run.run_id,
        status="passed",
        checked_outputs=["all_failure_modes_covered"],
        evidence_refs=[basis.evidence.evidence_id],
        summary="Failure-mode basis check covered every recorded promotion risk.",
    )
    review_checkpoint = request_failure_mode_review_checkpoint(ws, claim_id=claim.claim_id)
    approved_review = decide_human_checkpoint(
        ws,
        checkpoint_id=review_checkpoint.checkpoint_id,
        decision="approve_failure_mode_review",
        rationale="The GW frequency-grid risk has a typed tool-backed review basis.",
        decided_by="human",
    )
    review_result = record_failure_mode_review_result(
        ws,
        claim_id=claim.claim_id,
        checkpoint_id=approved_review.checkpoint_id,
        status="passed",
        reviewed_failure_modes=["frequency grid mismatch"],
        evidence_refs=[basis.evidence.evidence_id],
        validation_result_ids=[basis_validation.result_id],
        tool_run_ids=[basis.run.run_id],
        basis_refs=[f"validation:{basis_validation.result_id}"],
        summary="Tool-backed failure-mode basis review passed for the GW promotion risk.",
    )
    policy = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="create_promotion_packet",
        claim_id=claim.claim_id,
        evidence_refs=[benchmark.evidence.evidence_id],
        validation_result_ids=[benchmark_validation.result_id],
        known_failure_modes=["frequency grid mismatch"],
        failure_mode_review_checkpoint_id=approved_review.checkpoint_id,
        failure_mode_review_result_id=review_result.result_id,
        source_kind="typed_records",
        risk_level="rigorous",
    )
    packet = create_promotion_packet(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        proposed_memory_kind="code_method_claim",
        scope="librpa commit abc123 with reviewed frequency-grid risk",
        evidence_refs=[benchmark.evidence.evidence_id],
        validation_result_ids=[benchmark_validation.result_id],
        known_failure_modes=["frequency grid mismatch"],
        failure_mode_review_checkpoint_id=approved_review.checkpoint_id,
        failure_mode_review_result_id=review_result.result_id,
    )
    promotion_checkpoint = request_human_checkpoint(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        reason="Promote high-risk GW code-method result after typed review.",
        requested_by="real_workflow_acceptance",
        options=["approve", "reject"],
    )
    decide_human_checkpoint(
        ws,
        checkpoint_id=promotion_checkpoint.checkpoint_id,
        decision="approve",
        rationale="Promotion includes validated benchmark evidence and a passed failure-mode review result.",
        decided_by="human",
    )
    memory = apply_promotion_packet(
        ws,
        packet_id=packet.packet_id,
        checkpoint_id=promotion_checkpoint.checkpoint_id,
    )
    bind_session(ws, "s1", topic_id="librpa-gw", context_id="gw-methods", active_claim=claim.claim_id)

    brief = build_execution_brief(ws, "s1")
    audit = audit_l2_memory_context(ws, claim_id=claim.claim_id)

    assert policy["block"] is False
    assert memory.failure_mode_review_result_id == review_result.result_id
    assert "failure_mode_review_basis" in brief["evidence_coverage"]["satisfied_outputs"]
    brief_entry = brief["known_context"]["memory_entries"][0]
    assert brief_entry["failure_mode_review_checkpoint_id"] == approved_review.checkpoint_id
    assert brief_entry["failure_mode_review_result_id"] == review_result.result_id
    audit_entry = audit["memory_entries"][0]
    assert audit_entry["failure_mode_review_result_ids"] == [review_result.result_id]
    assert audit_entry["failure_mode_review_results"][0]["tool_run_ids"] == [basis.run.run_id]
