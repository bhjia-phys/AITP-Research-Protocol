from __future__ import annotations

import json
from pathlib import Path


def _setup_promoted_code_memory(tmp_path: Path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.code import record_code_state
    from brain.v5.evidence import record_evidence
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.tools import record_tool_run
    from brain.v5.validation import create_validation_contract, record_validation_result
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The recorded Si GW workflow reproduces the benchmark within tolerance.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="formula-code translation provenance",
    )
    code_state = record_code_state(
        ws,
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="master",
        upstream_commit="abc123",
        local_branch="topic/si-gw",
        worktree_path="D:/worktrees/librpa/si-gw",
        dirty=False,
        linked_records={"claim_id": claim.claim_id},
    )
    contract = create_validation_contract(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        required_checks=["reproduce Si GW benchmark"],
        failure_modes=["wrong code version", "formula-code mismatch"],
        required_evidence_outputs=["benchmark_consistency"],
        tool_recipe_ids=["recipe-librpa-si-gw"],
        executor_ids=["pytest"],
    )
    run = record_tool_run(
        ws,
        recipe_id="recipe-librpa-si-gw",
        tool_family="domain",
        tool_name="pytest",
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        outputs={"benchmark_consistency": "passed"},
        code_state_ids=[code_state.code_state_id],
    )
    validation = record_validation_result(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        contract_id=contract.contract_id,
        tool_run_id=run.run_id,
        status="passed",
        checked_outputs=["benchmark_consistency"],
        summary="Si GW benchmark output is within tolerance.",
    )
    evidence = record_evidence(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        evidence_type="benchmark",
        status="supports",
        summary="Validated LibRPA benchmark evidence.",
        tool_run_ids=[run.run_id],
        validation_result_ids=[validation.result_id],
    )
    packet = create_promotion_packet(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        scope="Si GW benchmark, recorded code state abc123.",
        evidence_refs=[evidence.evidence_id],
        validation_result_ids=[validation.result_id],
        known_failure_modes=["wrong code version", "formula-code mismatch"],
    )
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        reason="L2 memory promotion for benchmark workflow.",
        requested_by="promotion_policy",
        options=["approve", "revise"],
    )
    decided = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="Evidence, code provenance, and validation result are explicit.",
        decided_by="human",
    )
    entry = apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=decided.checkpoint_id)
    return ws, claim, code_state, validation, evidence, packet, decided, entry


def _setup_failure_mode_audit_gap(tmp_path: Path):
    from brain.v5.evidence import record_evidence
    from brain.v5.memory import create_promotion_packet
    from brain.v5.validation import create_validation_contract
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The counting table identifies the FQHE edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="locally_checked",
        active_uncertainty="frequency grid mismatch may mimic the edge count",
        strongest_failure_mode="frequency grid mismatch",
    )
    create_validation_contract(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        required_checks=["frequency-grid and basis-cutoff sanity checks"],
        failure_modes=["frequency grid mismatch", "basis cutoff mismatch"],
        required_evidence_outputs=["grid_table"],
    )
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="toy_numeric",
        status="supports",
        summary="Counting evidence without tool-run provenance.",
    )
    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        scope="Finite-size toy-model edge counting only.",
        evidence_refs=[evidence.evidence_id],
        known_failure_modes=["finite-size aliasing"],
    )
    return ws, claim, packet


def test_l2_memory_audit_surfaces_typed_promotion_provenance(tmp_path):
    from brain.v5.memory_audit import audit_l2_memory_context
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim, code_state, validation, evidence, packet, checkpoint, entry = _setup_promoted_code_memory(tmp_path)

    payload = audit_l2_memory_context(ws, claim_id=claim.claim_id)

    assert require_valid_public_surface("l2_memory_audit", payload) == payload
    assert payload["kind"] == "l2_memory_audit"
    assert payload["truth_source"] == "typed_records"
    assert payload["summary_inputs_trusted"] is False
    assert payload["can_update_kernel_state"] is False
    assert payload["entry_count"] == 1
    audited = payload["memory_entries"][0]
    assert audited["entry_id"] == entry.entry_id
    assert audited["source_packet_id"] == packet.packet_id
    assert audited["promotion_packet_status"] == "promoted"
    assert audited["human_checkpoint_id"] == checkpoint.checkpoint_id
    assert audited["failure_mode_review_checkpoint_id"] == ""
    assert audited["human_checkpoint_decision"] == "approve"
    assert audited["evidence_refs"] == [evidence.evidence_id]
    assert audited["validation_result_ids"] == [validation.result_id]
    assert audited["code_state_ids"] == [code_state.code_state_id]
    assert audited["missing_links"] == []
    assert audited["orientation_only"] is True


def test_l2_memory_audit_cli_mcp_and_runtime_entrypoint(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_audit_l2_memory_context
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    ws, claim, code_state, *_ = _setup_promoted_code_memory(tmp_path)

    assert main(["--base", str(tmp_path), "memory", "audit", "--claim", claim.claim_id]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_audit_l2_memory_context(str(tmp_path), claim_id=claim.claim_id)

    assert cli_payload["memory_entries"][0]["code_state_ids"] == [code_state.code_state_id]
    assert mcp_payload == cli_payload
    entrypoints = runtime_entrypoints()
    assert entrypoints["audit_l2_memory_context"] == {
        "cli": "aitp-v5 memory audit <args>",
        "mcp": "aitp_v5_audit_l2_memory_context",
        "surface": "l2_memory_audit",
    }
    assert validate_runtime_entrypoints() == []


def test_l2_memory_audit_reports_failure_mode_review_checkpoint(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.evidence import record_evidence
    from brain.v5.failure_mode_review import record_failure_mode_review_result, request_failure_mode_review_checkpoint
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.memory_audit import audit_l2_memory_context
    from brain.v5.validation import create_validation_contract, record_validation_result
    from brain.v5.tools import record_tool_run
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Counting identifies the edge CFT in the recorded sector.",
        evidence_profile="toy_numeric",
        confidence_state="locally_checked",
        active_uncertainty="sector assignment",
    )
    contract = create_validation_contract(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        required_checks=["counting benchmark"],
        failure_modes=["sector misassignment"],
        required_evidence_outputs=["counting_table"],
    )
    run = record_tool_run(
        ws,
        recipe_id="recipe-fqhe-ed",
        tool_family="numerical",
        tool_name="pytest",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        outputs={"counting_table": "ok"},
    )
    validation = record_validation_result(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        contract_id=contract.contract_id,
        tool_run_id=run.run_id,
        status="passed",
        checked_outputs=["counting_table"],
        summary="Counting table passed validation.",
    )
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="toy_numeric",
        status="supports",
        summary="Tool-derived counting evidence.",
        tool_run_ids=[run.run_id],
        validation_result_ids=[validation.result_id],
    )
    review = request_failure_mode_review_checkpoint(ws, claim_id=claim.claim_id)
    approved_review = decide_human_checkpoint(
        ws,
        checkpoint_id=review.checkpoint_id,
        decision="approve_failure_mode_review",
        rationale="Reviewed failure-mode adequacy.",
        decided_by="human",
    )
    review_result = record_failure_mode_review_result(
        ws,
        claim_id=claim.claim_id,
        checkpoint_id=approved_review.checkpoint_id,
        status="passed",
        reviewed_failure_modes=["sector misassignment"],
        validation_result_ids=[validation.result_id],
        summary="Sector-misassignment review passed against validation basis.",
    )
    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        scope="fixed sector ED",
        evidence_refs=[evidence.evidence_id],
        validation_result_ids=[validation.result_id],
        known_failure_modes=["sector misassignment"],
        failure_mode_review_checkpoint_id=approved_review.checkpoint_id,
        failure_mode_review_result_id=review_result.result_id,
    )
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        reason="Approve L2 memory promotion.",
        requested_by="promotion_policy",
        options=["approve"],
    )
    decided = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="Promotion packet is ready.",
        decided_by="human",
    )
    apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=decided.checkpoint_id)

    payload = audit_l2_memory_context(ws, claim_id=claim.claim_id)

    assert payload["memory_entries"][0]["failure_mode_review_checkpoint_id"] == approved_review.checkpoint_id
    assert payload["memory_entries"][0]["failure_mode_review_result_id"] == review_result.result_id
    assert payload["memory_entries"][0]["missing_links"] == []


def test_failure_mode_audit_reports_uncovered_claim_and_contract_modes(tmp_path):
    from brain.v5.failure_mode_audit import audit_failure_mode_coverage
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim, packet = _setup_failure_mode_audit_gap(tmp_path)

    payload = audit_failure_mode_coverage(ws, claim_id=claim.claim_id)

    assert require_valid_public_surface("failure_mode_audit", payload) == payload
    assert payload["kind"] == "failure_mode_audit"
    assert payload["truth_source"] == "typed_records"
    assert payload["summary_inputs_trusted"] is False
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False
    assert payload["active_uncertainty"] == "frequency grid mismatch may mimic the edge count"
    assert payload["strongest_failure_mode"] == "frequency grid mismatch"
    assert payload["promotion_packet_ids"] == [packet.packet_id]
    assert payload["promotion_packet_failure_modes"] == ["finite-size aliasing"]
    assert payload["validation_contract_failure_modes"] == [
        "frequency grid mismatch",
        "basis cutoff mismatch",
    ]
    assert payload["uncovered_claim_failure_modes"] == ["frequency grid mismatch"]
    assert payload["uncovered_validation_failure_modes"] == [
        "frequency grid mismatch",
        "basis cutoff mismatch",
    ]
    assert payload["coverage_status"] == "gap"
    assert payload["recommended_actions"] == [
        "align_promotion_failure_modes_with_claim_risk",
        "cover_validation_contract_failure_modes",
    ]


def test_failure_mode_audit_counts_partial_validation_coverage_without_promotion(tmp_path):
    from brain.v5.failure_mode_audit import audit_failure_mode_coverage
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.tools import record_tool_run
    from brain.v5.validation import record_validation_result

    ws, claim, _ = _setup_failure_mode_audit_gap(tmp_path)
    contract_id = audit_failure_mode_coverage(ws, claim_id=claim.claim_id)["validation_contract_ids"][0]
    run = record_tool_run(
        ws,
        recipe_id="recipe-fqhe-ed",
        tool_family="numerical",
        tool_name="pytest",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        outputs={"grid_table": "checked"},
    )
    validation = record_validation_result(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        contract_id=contract_id,
        tool_run_id=run.run_id,
        status="partial",
        checked_outputs=["frequency grid sanity check"],
        covered_failure_modes=["frequency grid mismatch"],
        summary="Frequency grid mismatch failure mode was checked; basis cutoff remains open.",
    )

    payload = audit_failure_mode_coverage(ws, claim_id=claim.claim_id)

    assert require_valid_public_surface("failure_mode_audit", payload) == payload
    assert payload["validation_covered_failure_modes"] == ["frequency grid mismatch"]
    assert payload["validation_result_coverage"] == [
        {
            "result_id": validation.result_id,
            "contract_id": contract_id,
            "status": "partial",
            "checked_outputs": ["frequency grid sanity check"],
            "missing_outputs": ["grid_table"],
            "declared_covered_failure_modes": ["frequency grid mismatch"],
            "covered_failure_modes": ["frequency grid mismatch"],
            "orientation_only": True,
        }
    ]
    assert payload["uncovered_claim_failure_modes"] == []
    assert payload["uncovered_validation_failure_modes"] == ["basis cutoff mismatch"]
    assert payload["coverage_status"] == "gap"
    assert payload["recommended_actions"] == ["cover_validation_contract_failure_modes"]


def test_failure_mode_audit_does_not_count_summary_only_partial_coverage(tmp_path):
    from brain.v5.failure_mode_audit import audit_failure_mode_coverage
    from brain.v5.tools import record_tool_run
    from brain.v5.validation import record_validation_result

    ws, claim, _ = _setup_failure_mode_audit_gap(tmp_path)
    contract_id = audit_failure_mode_coverage(ws, claim_id=claim.claim_id)["validation_contract_ids"][0]
    run = record_tool_run(
        ws,
        recipe_id="recipe-fqhe-ed",
        tool_family="numerical",
        tool_name="pytest",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        outputs={"grid_table": "checked"},
    )
    record_validation_result(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        contract_id=contract_id,
        tool_run_id=run.run_id,
        status="partial",
        checked_outputs=["grid_table"],
        summary="Mentions frequency grid mismatch but did not declare it covered.",
    )

    payload = audit_failure_mode_coverage(ws, claim_id=claim.claim_id)

    assert payload["validation_covered_failure_modes"] == []
    assert payload["uncovered_claim_failure_modes"] == ["frequency grid mismatch"]
    assert payload["uncovered_validation_failure_modes"] == [
        "frequency grid mismatch",
        "basis cutoff mismatch",
    ]


def test_failure_mode_audit_cli_mcp_and_runtime_entrypoint(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_audit_failure_mode_coverage
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    _, claim, _ = _setup_failure_mode_audit_gap(tmp_path)

    assert main(["--base", str(tmp_path), "memory", "failure-modes", "--claim", claim.claim_id]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_audit_failure_mode_coverage(str(tmp_path), claim_id=claim.claim_id)

    assert cli_payload["coverage_status"] == "gap"
    assert mcp_payload == cli_payload
    assert runtime_entrypoints()["audit_failure_mode_coverage"] == {
        "cli": "aitp-v5 memory failure-modes <args>",
        "mcp": "aitp_v5_audit_failure_mode_coverage",
        "surface": "failure_mode_audit",
    }
    assert validate_runtime_entrypoints() == []


def test_failure_mode_review_packet_generates_physics_adequacy_questions(tmp_path):
    from brain.v5.failure_mode_review import build_failure_mode_review_packet
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim, _ = _setup_failure_mode_audit_gap(tmp_path)

    packet = build_failure_mode_review_packet(ws, claim_id=claim.claim_id)

    assert require_valid_public_surface("failure_mode_review_packet", packet) == packet
    assert packet["kind"] == "failure_mode_review_packet"
    assert packet["truth_source"] == "typed_records"
    assert packet["summary_inputs_trusted"] is False
    assert packet["can_update_kernel_state"] is False
    assert packet["can_update_claim_trust"] is False
    assert packet["claim_id"] == claim.claim_id
    assert packet["coverage_status"] == "gap"
    assert packet["requires_human_or_adversarial_review"] is True
    assert packet["review_scope"] == "physical_adequacy_before_promotion"
    modes = {item["failure_mode"]: item for item in packet["review_items"]}
    assert modes["frequency grid mismatch"]["sources"] == [
        "claim.strongest_failure_mode",
        "validation_contract.failure_modes",
    ]
    assert modes["frequency grid mismatch"]["coverage"] == "uncovered"
    assert modes["basis cutoff mismatch"]["sources"] == [
        "validation_contract.failure_modes",
    ]
    assert modes["finite-size aliasing"]["coverage"] == "promotion_packet_only"
    assert any(
        "frequency grid mismatch" in question
        for question in modes["frequency grid mismatch"]["review_questions"]
    )
    assert "review_physical_adequacy_of_failure_modes" in packet["recommended_actions"]


def test_failure_mode_review_packet_cli_mcp_and_runtime_entrypoint(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_build_failure_mode_review_packet
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    _, claim, _ = _setup_failure_mode_audit_gap(tmp_path)

    assert main(["--base", str(tmp_path), "memory", "failure-mode-review", "--claim", claim.claim_id]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_build_failure_mode_review_packet(str(tmp_path), claim_id=claim.claim_id)

    assert cli_payload["kind"] == "failure_mode_review_packet"
    assert cli_payload["review_items"]
    assert mcp_payload == cli_payload
    assert runtime_entrypoints()["build_failure_mode_review_packet"] == {
        "cli": "aitp-v5 memory failure-mode-review <args>",
        "mcp": "aitp_v5_build_failure_mode_review_packet",
        "surface": "failure_mode_review_packet",
    }
    assert validate_runtime_entrypoints() == []


def test_failure_mode_review_checkpoint_requests_typed_human_review(tmp_path):
    from brain.v5.failure_mode_review import request_failure_mode_review_checkpoint
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim, _ = _setup_failure_mode_audit_gap(tmp_path)

    checkpoint = request_failure_mode_review_checkpoint(ws, claim_id=claim.claim_id)
    payload = {"ok": True, **checkpoint.__dict__}

    assert require_valid_public_surface("human_checkpoint_record", payload) == payload
    assert checkpoint.kind == "human_checkpoint"
    assert checkpoint.topic_id == "fqhe"
    assert checkpoint.claim_id == claim.claim_id
    assert checkpoint.status == "open"
    assert checkpoint.requested_by == "failure_mode_review_packet"
    assert checkpoint.options == ["approve_failure_mode_review", "revise_failure_modes"]
    assert "physical adequacy" in checkpoint.reason
    assert "frequency grid mismatch" in checkpoint.reason
    assert "basis cutoff mismatch" in checkpoint.reason


def test_failure_mode_review_checkpoint_cli_mcp_and_runtime_entrypoint(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_request_failure_mode_review_checkpoint
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    _, claim, _ = _setup_failure_mode_audit_gap(tmp_path)

    assert main(["--base", str(tmp_path), "memory", "request-failure-mode-review", "--claim", claim.claim_id]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_request_failure_mode_review_checkpoint(str(tmp_path), claim_id=claim.claim_id)

    assert cli_payload["kind"] == "human_checkpoint"
    assert cli_payload["requested_by"] == "failure_mode_review_packet"
    assert mcp_payload == cli_payload
    assert runtime_entrypoints()["request_failure_mode_review_checkpoint"] == {
        "cli": "aitp-v5 memory request-failure-mode-review <args>",
        "mcp": "aitp_v5_request_failure_mode_review_checkpoint",
        "surface": "human_checkpoint_record",
    }
    assert validate_runtime_entrypoints() == []


def test_failure_mode_review_result_records_typed_review_basis(tmp_path):
    import pytest
    from dataclasses import asdict

    from brain.v5.checkpoints import decide_human_checkpoint
    from brain.v5.failure_mode_review import (
        record_failure_mode_review_result,
        request_failure_mode_review_checkpoint,
    )
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim, _ = _setup_failure_mode_audit_gap(tmp_path)
    checkpoint = request_failure_mode_review_checkpoint(ws, claim_id=claim.claim_id)
    approved = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve_failure_mode_review",
        rationale="Failure modes were checked against the counting setup.",
        decided_by="human",
    )

    result = record_failure_mode_review_result(
        ws,
        claim_id=claim.claim_id,
        checkpoint_id=approved.checkpoint_id,
        status="passed",
        reviewed_failure_modes=["frequency grid mismatch", "basis cutoff mismatch"],
        basis_refs=["literature:fqhe-edge-counting"],
        reviewer_role="adversarial_reviewer",
        summary="The review checked whether grid and cutoff mismatches could fake the edge count.",
    )
    payload = {"ok": True, **asdict(result)}

    assert require_valid_public_surface("failure_mode_review_result_record", payload) == payload
    assert result.kind == "failure_mode_review_result"
    assert result.topic_id == "fqhe"
    assert result.claim_id == claim.claim_id
    assert result.checkpoint_id == approved.checkpoint_id
    assert result.reviewed_failure_modes == ["frequency grid mismatch", "basis cutoff mismatch"]
    assert result.basis_refs == ["literature:fqhe-edge-counting"]
    assert result.evidence_refs == []
    assert result.validation_result_ids == []
    assert result.summary_inputs_trusted is False
    assert result.can_update_claim_trust is False

    with pytest.raises(ValueError, match="review basis"):
        record_failure_mode_review_result(
            ws,
            claim_id=claim.claim_id,
            checkpoint_id=approved.checkpoint_id,
            status="passed",
            reviewed_failure_modes=["frequency grid mismatch"],
            summary="A basis-free review result must not be accepted.",
        )


def test_failure_mode_review_result_rejects_missing_typed_basis_refs(tmp_path):
    import pytest

    from brain.v5.checkpoints import decide_human_checkpoint
    from brain.v5.failure_mode_review import (
        record_failure_mode_review_result,
        request_failure_mode_review_checkpoint,
    )

    ws, claim, _ = _setup_failure_mode_audit_gap(tmp_path)
    checkpoint = request_failure_mode_review_checkpoint(ws, claim_id=claim.claim_id)
    approved = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve_failure_mode_review",
        rationale="Failure modes were checked.",
        decided_by="human",
    )

    with pytest.raises(ValueError, match="unknown evidence ref"):
        record_failure_mode_review_result(
            ws,
            claim_id=claim.claim_id,
            checkpoint_id=approved.checkpoint_id,
            status="passed",
            reviewed_failure_modes=["frequency grid mismatch"],
            evidence_refs=["evidence-missing"],
            summary="Missing typed evidence refs must not be accepted.",
        )


def test_failure_mode_review_result_accepts_existing_typed_basis_refs(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint
    from brain.v5.evidence import record_artifact_ref, record_evidence
    from brain.v5.failure_mode_review import (
        record_failure_mode_review_result,
        request_failure_mode_review_checkpoint,
    )
    from brain.v5.references import record_reference_location
    from brain.v5.tools import record_tool_run
    from brain.v5.validation import create_validation_contract, record_validation_result
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Counting identifies the edge CFT in the recorded sector.",
        evidence_profile="toy_numeric",
        confidence_state="locally_checked",
        active_uncertainty="sector assignment",
        strongest_failure_mode="sector misassignment",
    )
    artifact = record_artifact_ref(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        artifact_type="table",
        uri="file:///tmp/counting-table.csv",
        summary="Counting table artifact.",
    )
    reference = record_reference_location(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        connector_id="local_pdf",
        location_type="paper_pdf",
        uri="file:///papers/fqhe.pdf",
        label="FQHE edge counting paper",
    )
    contract = create_validation_contract(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        required_checks=["counting benchmark"],
        failure_modes=["sector misassignment"],
        required_evidence_outputs=["counting_table"],
    )
    run = record_tool_run(
        ws,
        recipe_id="recipe-fqhe-ed",
        tool_family="numerical",
        tool_name="pytest",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        outputs={"counting_table": "ok"},
        artifact_ids=[artifact.artifact_id],
    )
    validation = record_validation_result(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        contract_id=contract.contract_id,
        tool_run_id=run.run_id,
        status="passed",
        checked_outputs=["counting_table"],
        artifact_ids=[artifact.artifact_id],
        summary="Counting table passed validation.",
    )
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="toy_numeric",
        status="supports",
        summary="Tool-derived counting evidence.",
        tool_run_ids=[run.run_id],
        validation_result_ids=[validation.result_id],
        artifact_ids=[artifact.artifact_id],
    )
    checkpoint = request_failure_mode_review_checkpoint(ws, claim_id=claim.claim_id)
    approved = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve_failure_mode_review",
        rationale="Typed basis refs were checked.",
        decided_by="human",
    )

    result = record_failure_mode_review_result(
        ws,
        claim_id=claim.claim_id,
        checkpoint_id=approved.checkpoint_id,
        status="passed",
        reviewed_failure_modes=["sector misassignment"],
        evidence_refs=[evidence.evidence_id],
        validation_result_ids=[validation.result_id],
        tool_run_ids=[run.run_id],
        reference_location_ids=[reference.location_id],
        artifact_ids=[artifact.artifact_id],
        summary="All typed basis refs resolve to the same claim.",
    )

    assert result.evidence_refs == [evidence.evidence_id]
    assert result.validation_result_ids == [validation.result_id]
    assert result.tool_run_ids == [run.run_id]
    assert result.reference_location_ids == [reference.location_id]
    assert result.artifact_ids == [artifact.artifact_id]


def test_failure_mode_review_result_cli_mcp_and_runtime_entrypoint(tmp_path, capsys):
    from brain.v5.checkpoints import decide_human_checkpoint
    from brain.v5.cli import main
    from brain.v5.failure_mode_review import request_failure_mode_review_checkpoint
    from brain.v5.mcp_tools import aitp_v5_record_failure_mode_review_result
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    ws, claim, _ = _setup_failure_mode_audit_gap(tmp_path)
    checkpoint = request_failure_mode_review_checkpoint(ws, claim_id=claim.claim_id)
    approved = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve_failure_mode_review",
        rationale="Failure modes were reviewed.",
        decided_by="human",
    )

    assert main(
        [
            "--base",
            str(tmp_path),
            "memory",
            "failure-mode-review-result",
            "--claim",
            claim.claim_id,
            "--checkpoint",
            approved.checkpoint_id,
            "--status",
            "passed",
            "--reviewed-mode",
            "frequency grid mismatch",
            "--basis-ref",
            "literature:fqhe-edge-counting",
            "--summary",
            "Physical adequacy review linked to literature basis.",
        ]
    ) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_record_failure_mode_review_result(
        str(tmp_path),
        claim_id=claim.claim_id,
        checkpoint_id=approved.checkpoint_id,
        status="passed",
        reviewed_failure_modes=["frequency grid mismatch"],
        basis_refs=["literature:fqhe-edge-counting"],
        summary="Physical adequacy review linked to literature basis.",
    )

    assert cli_payload["kind"] == "failure_mode_review_result"
    assert cli_payload["checkpoint_id"] == approved.checkpoint_id
    assert cli_payload["can_update_claim_trust"] is False
    assert mcp_payload == cli_payload
    assert runtime_entrypoints()["record_failure_mode_review_result"] == {
        "cli": "aitp-v5 memory failure-mode-review-result <args>",
        "mcp": "aitp_v5_record_failure_mode_review_result",
        "surface": "failure_mode_review_result_record",
    }
    assert validate_runtime_entrypoints() == []


def test_failure_mode_audit_surfaces_review_result_basis(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint
    from brain.v5.failure_mode_audit import audit_failure_mode_coverage
    from brain.v5.failure_mode_review import (
        record_failure_mode_review_result,
        request_failure_mode_review_checkpoint,
    )
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim, _ = _setup_failure_mode_audit_gap(tmp_path)
    checkpoint = request_failure_mode_review_checkpoint(ws, claim_id=claim.claim_id)
    approved = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve_failure_mode_review",
        rationale="Reviewed grid and cutoff failure modes.",
        decided_by="human",
    )
    result = record_failure_mode_review_result(
        ws,
        claim_id=claim.claim_id,
        checkpoint_id=approved.checkpoint_id,
        status="passed",
        reviewed_failure_modes=["frequency grid mismatch", "basis cutoff mismatch"],
        basis_refs=["literature:fqhe-edge-counting"],
        summary="Reviewed whether grid and cutoff artifacts can mimic the edge count.",
    )

    audit = audit_failure_mode_coverage(ws, claim_id=claim.claim_id)

    assert require_valid_public_surface("failure_mode_audit", audit) == audit
    assert audit["failure_mode_review_result_ids"] == [result.result_id]
    assert audit["reviewed_failure_modes"] == ["frequency grid mismatch", "basis cutoff mismatch"]
    reviewed = audit["failure_mode_review_results"][0]
    assert reviewed["result_id"] == result.result_id
    assert reviewed["checkpoint_id"] == approved.checkpoint_id
    assert reviewed["status"] == "passed"
    assert reviewed["basis_refs"] == ["literature:fqhe-edge-counting"]
    assert reviewed["validation_result_ids"] == []
    assert reviewed["summary_inputs_trusted"] is False
    assert reviewed["can_update_claim_trust"] is False


def test_l2_memory_audit_links_review_result_basis_to_memory_entry(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.evidence import record_evidence
    from brain.v5.failure_mode_review import (
        record_failure_mode_review_result,
        request_failure_mode_review_checkpoint,
    )
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.memory_audit import audit_l2_memory_context
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.tools import record_tool_run
    from brain.v5.validation import create_validation_contract, record_validation_result
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Counting identifies the edge CFT in the recorded sector.",
        evidence_profile="toy_numeric",
        confidence_state="locally_checked",
        active_uncertainty="sector assignment",
        strongest_failure_mode="sector misassignment",
    )
    contract = create_validation_contract(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        required_checks=["counting benchmark"],
        failure_modes=["sector misassignment"],
        required_evidence_outputs=["counting_table"],
    )
    run = record_tool_run(
        ws,
        recipe_id="recipe-fqhe-ed",
        tool_family="numerical",
        tool_name="pytest",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        outputs={"counting_table": "ok"},
    )
    validation = record_validation_result(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        contract_id=contract.contract_id,
        tool_run_id=run.run_id,
        status="passed",
        checked_outputs=["counting_table"],
        summary="Counting table passed validation.",
    )
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="toy_numeric",
        status="supports",
        summary="Tool-derived counting evidence.",
        tool_run_ids=[run.run_id],
        validation_result_ids=[validation.result_id],
    )
    review_checkpoint = request_failure_mode_review_checkpoint(ws, claim_id=claim.claim_id)
    approved_review = decide_human_checkpoint(
        ws,
        checkpoint_id=review_checkpoint.checkpoint_id,
        decision="approve_failure_mode_review",
        rationale="Sector misassignment was reviewed against the counting table.",
        decided_by="human",
    )
    review_result = record_failure_mode_review_result(
        ws,
        claim_id=claim.claim_id,
        checkpoint_id=approved_review.checkpoint_id,
        status="passed",
        reviewed_failure_modes=["sector misassignment"],
        validation_result_ids=[validation.result_id],
        tool_run_ids=[run.run_id],
        summary="Tool run and validation result address sector misassignment.",
    )
    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        scope="fixed sector ED",
        evidence_refs=[evidence.evidence_id],
        validation_result_ids=[validation.result_id],
        known_failure_modes=["sector misassignment"],
        failure_mode_review_checkpoint_id=approved_review.checkpoint_id,
        failure_mode_review_result_id=review_result.result_id,
    )
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        reason="Approve L2 memory promotion.",
        requested_by="promotion_policy",
        options=["approve"],
    )
    decided = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="Promotion packet is ready.",
        decided_by="human",
    )
    apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=decided.checkpoint_id)

    audit = audit_l2_memory_context(ws, claim_id=claim.claim_id)

    assert require_valid_public_surface("l2_memory_audit", audit) == audit
    entry = audit["memory_entries"][0]
    assert entry["failure_mode_review_checkpoint_id"] == approved_review.checkpoint_id
    assert entry["failure_mode_review_result_id"] == review_result.result_id
    assert entry["failure_mode_review_result_ids"] == [review_result.result_id]
    reviewed = entry["failure_mode_review_results"][0]
    assert reviewed["result_id"] == review_result.result_id
    assert reviewed["validation_result_ids"] == [validation.result_id]
    assert reviewed["tool_run_ids"] == [run.run_id]
    assert reviewed["can_update_claim_trust"] is False
    assert entry["missing_links"] == []


def test_l2_memory_audit_public_surface_contract_rejects_summary_truth_source():
    import pytest

    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface

    with pytest.raises(ContractError):
        require_valid_public_surface(
            "l2_memory_audit",
            {
                "ok": True,
                "kind": "l2_memory_audit",
                "claim_id": "claim-test",
                "topic_id": "topic-test",
                "truth_source": "summary",
                "summary_inputs_trusted": True,
                "can_update_kernel_state": False,
                "entry_count": 0,
                "memory_entries": [],
            },
        )
