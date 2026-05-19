"""Tests for AITP v5 validation contract records."""

from dataclasses import asdict
from pathlib import Path

import pytest


def _init_ws(tmp_path: Path):
    from brain.v5.workspace import init_workspace

    return init_workspace(tmp_path)


def _setup_claim(tmp_path: Path):
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "gw", context_id="gw-methods", title="GW")
    claim = create_claim(
        ws,
        topic_id="gw",
        statement="The modified self-energy kernel reproduces the benchmark.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="formula-code translation",
    )
    return ws, claim


def test_create_validation_contract_requires_claim_checks_and_failure_modes(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.validation import create_validation_contract

    contract = create_validation_contract(
        ws,
        topic_id="gw",
        claim_id=claim.claim_id,
        required_checks=["code_state_present", "benchmark_table_within_tolerance"],
        failure_modes=["wrong frequency grid", "dirty worktree"],
        required_evidence_outputs=["evidence_or_provenance", "minimal_check"],
        validator_role="adversarial_reviewer",
    )

    payload = {"ok": True, **asdict(contract)}
    assert contract.kind == "validation_contract"
    assert contract.status == "open"
    assert require_valid_public_surface("validation_contract_record", payload) == payload


def test_validation_contract_rejects_empty_required_checks(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.validation import create_validation_contract

    contract = create_validation_contract(
        ws,
        topic_id="gw",
        claim_id=claim.claim_id,
        required_checks=[],
        failure_modes=["something"],
        required_evidence_outputs=["something_else"],
    )

    payload = {"ok": True, **asdict(contract)}
    with pytest.raises(ContractError, match="required_checks"):
        require_valid_public_surface("validation_contract_record", payload)


def test_validation_contract_rejects_empty_failure_modes(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.validation import create_validation_contract

    contract = create_validation_contract(
        ws,
        topic_id="gw",
        claim_id=claim.claim_id,
        required_checks=["code_state_present"],
        failure_modes=[],
        required_evidence_outputs=["evidence_or_provenance"],
    )

    payload = {"ok": True, **asdict(contract)}
    with pytest.raises(ContractError, match="failure_modes"):
        require_valid_public_surface("validation_contract_record", payload)


def test_validation_contract_rejects_empty_required_evidence_outputs(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.validation import create_validation_contract

    contract = create_validation_contract(
        ws,
        topic_id="gw",
        claim_id=claim.claim_id,
        required_checks=["code_state_present"],
        failure_modes=["dirty worktree"],
        required_evidence_outputs=[],
    )

    payload = {"ok": True, **asdict(contract)}
    with pytest.raises(ContractError, match="required_evidence_outputs"):
        require_valid_public_surface("validation_contract_record", payload)


def test_validation_contract_persists(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.validation import create_validation_contract
    from brain.v5.store import list_records
    from brain.v5.models import ValidationContractRecord

    contract = create_validation_contract(
        ws,
        topic_id="gw",
        claim_id=claim.claim_id,
        required_checks=["code_state_present"],
        failure_modes=["dirty worktree"],
        required_evidence_outputs=["evidence_or_provenance"],
    )

    records = list_records(ws.registry_dir("validation_contracts"), ValidationContractRecord)
    assert len(records) == 1
    assert records[0].contract_id == contract.contract_id


def test_validation_cli_json_output(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.cli import main

    result = main(
        [
            "--base",
            str(tmp_path),
            "validation",
            "contract",
            "create",
            "--topic",
            "gw",
            "--claim",
            claim.claim_id,
            "--required-check",
            "code_state_present",
            "--failure-mode",
            "dirty worktree",
            "--required-output",
            "evidence_or_provenance",
        ]
    )
    assert result == 0


def test_validation_mcp_valid_surface(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.mcp_tools import aitp_v5_create_validation_contract

    result = aitp_v5_create_validation_contract(
        str(tmp_path),
        topic_id="gw",
        claim_id=claim.claim_id,
        required_checks=["code_state_present"],
        failure_modes=["dirty worktree"],
        required_evidence_outputs=["evidence_or_provenance"],
        validator_role="adversarial_reviewer",
    )
    assert result["ok"] is True
    assert result["kind"] == "validation_contract"
    assert result["status"] == "open"


def test_validation_runtime_entrypoint_exists():
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ep = runtime_entrypoints()
    assert "create_validation_contract" in ep
    assert ep["create_validation_contract"]["surface"] == "validation_contract_record"


def test_human_checkpoint_records_reason_and_decision(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")

    checkpoint = request_human_checkpoint(
        ws,
        topic_id="fqhe",
        claim_id="claim-fqhe",
        reason="Promotion to reusable L2 memory requires human judgment.",
        requested_by="risk_policy",
        options=["approve", "revise", "reject"],
    )

    decided = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="revise",
        rationale="Need a negative control before promotion.",
        decided_by="human",
    )

    assert decided.status == "decided"
    assert decided.decision == "revise"
    payload = {"ok": True, **asdict(decided)}
    assert require_valid_public_surface("human_checkpoint_record", payload) == payload


def test_human_checkpoint_contract_rejects_empty_options(tmp_path):
    from brain.v5.checkpoints import request_human_checkpoint
    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")

    checkpoint = request_human_checkpoint(
        ws, topic_id="fqhe", claim_id="claim-fqhe",
        reason="test", requested_by="test", options=[],
    )
    payload = {"ok": True, **asdict(checkpoint)}
    with pytest.raises(ContractError, match="options"):
        require_valid_public_surface("human_checkpoint_record", payload)


def test_human_checkpoint_contract_rejects_invalid_decision(tmp_path):
    """Kernel-level validation rejects invalid decision before writing."""
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")

    checkpoint = request_human_checkpoint(
        ws, topic_id="fqhe", claim_id="claim-fqhe",
        reason="test", requested_by="test", options=["approve", "reject"],
    )
    with pytest.raises(ValueError, match="decision.*must be one of options"):
        decide_human_checkpoint(
            ws, checkpoint_id=checkpoint.checkpoint_id,
            decision="invalid_choice", rationale="test", decided_by="human",
        )


def test_human_checkpoint_persists(tmp_path):
    from brain.v5.checkpoints import request_human_checkpoint
    from brain.v5.store import list_records
    from brain.v5.models import HumanCheckpointRecord
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")

    checkpoint = request_human_checkpoint(
        ws, topic_id="fqhe", claim_id="claim-fqhe",
        reason="test", requested_by="test", options=["approve"],
    )
    records = list_records(ws.registry_dir("checkpoints"), HumanCheckpointRecord)
    assert len(records) == 1
    assert records[0].checkpoint_id == checkpoint.checkpoint_id


def test_human_checkpoint_cli(tmp_path):
    from brain.v5.cli import main
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")

    result = main([
        "--base", str(tmp_path), "checkpoint", "request",
        "--topic", "fqhe", "--claim", "claim-fqhe",
        "--reason", "Promotion requires human judgment",
        "--requested-by", "risk_policy", "--option", "approve", "--option", "revise",
    ])
    assert result == 0


def test_human_checkpoint_decide_cli(tmp_path):
    from brain.v5.checkpoints import request_human_checkpoint
    from brain.v5.cli import main
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    chk = request_human_checkpoint(ws, topic_id="fqhe", claim_id="claim-fqhe",
        reason="test", requested_by="test", options=["approve", "revise"])

    result = main([
        "--base", str(tmp_path), "checkpoint", "decide",
        chk.checkpoint_id, "--decision", "approve",
        "--rationale", "Good to go", "--decided-by", "human",
    ])
    assert result == 0


def test_human_checkpoint_decide_mcp(tmp_path):
    from brain.v5.checkpoints import request_human_checkpoint
    from brain.v5.mcp_tools import aitp_v5_decide_human_checkpoint
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    chk = request_human_checkpoint(ws, topic_id="fqhe", claim_id="claim-fqhe",
        reason="test", requested_by="test", options=["approve", "revise"])

    result = aitp_v5_decide_human_checkpoint(
        str(tmp_path), checkpoint_id=chk.checkpoint_id,
        decision="approve", rationale="Good to go", decided_by="human",
    )
    assert result["ok"] is True
    assert result["status"] == "decided"
    assert result["decision"] == "approve"


def test_human_checkpoint_decide_runtime_entrypoint():
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ep = runtime_entrypoints()
    assert "decide_human_checkpoint" in ep
    assert ep["decide_human_checkpoint"]["surface"] == "human_checkpoint_record"
    assert ep["decide_human_checkpoint"]["mcp"] == "aitp_v5_decide_human_checkpoint"


def test_human_checkpoint_mcp(tmp_path):
    from brain.v5.checkpoints import request_human_checkpoint
    from brain.v5.mcp_tools import aitp_v5_request_human_checkpoint
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")

    result = aitp_v5_request_human_checkpoint(
        str(tmp_path), topic_id="fqhe", claim_id="claim-fqhe",
        reason="test", requested_by="test", options=["approve", "reject"],
    )
    assert result["ok"] is True
    assert result["kind"] == "human_checkpoint"


def test_human_checkpoint_runtime_entrypoint():
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ep = runtime_entrypoints()
    assert "request_human_checkpoint" in ep
    assert ep["request_human_checkpoint"]["surface"] == "human_checkpoint_record"


def test_decide_human_checkpoint_kernel_rejects_decision_not_in_options(tmp_path):
    """Kernel must reject a decision that is not in the declared options."""
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")

    checkpoint = request_human_checkpoint(
        ws, topic_id="fqhe", claim_id="claim-fqhe",
        reason="test", requested_by="test", options=["revise", "reject"],
    )
    with pytest.raises(ValueError, match="decision.*must be one of options"):
        decide_human_checkpoint(
            ws, checkpoint_id=checkpoint.checkpoint_id,
            decision="approve", rationale="sneaky", decided_by="human",
        )


def test_invalid_decision_checkpoint_blocks_promotion(tmp_path):
    """A checkpoint with wrong decision must not be usable for promotion."""
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(ws, topic_id="fqhe",
        statement="Test claim", evidence_profile="toy_numeric",
        confidence_state="hypothesis", active_uncertainty="test")
    packet = create_promotion_packet(ws, topic_id="fqhe", claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim", scope="test scope",
        evidence_refs=["ev-1"], known_failure_modes=["test"])
    checkpoint = request_human_checkpoint(ws, topic_id="fqhe", claim_id=claim.claim_id,
        reason="test", requested_by="test", options=["approve", "revise"])
    decided = decide_human_checkpoint(ws, checkpoint_id=checkpoint.checkpoint_id,
        decision="revise", rationale="Not ready", decided_by="human")
    assert decided.decision == "revise"

    with pytest.raises(ValueError, match="decision was"):
        apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=checkpoint.checkpoint_id)
