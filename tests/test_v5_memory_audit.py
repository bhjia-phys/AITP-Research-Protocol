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
