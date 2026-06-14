from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path


def _setup_trusted_claim(tmp_path: Path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.code import record_code_state
    from brain.v5.evidence import record_evidence
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.models import TrustUpdateRequest
    from brain.v5.tools import record_tool_run
    from brain.v5.trust_updates import apply_trust_update, preflight_trust_update
    from brain.v5.validation import create_validation_contract, record_validation_result
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The Si GW workflow is locally checked against the benchmark.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="version-sensitive formula-code translation",
    )
    bind_session(ws, "s1", topic_id="librpa-gw", context_id="gw-methods", active_claim=claim.claim_id)
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
        required_checks=["Si GW benchmark"],
        failure_modes=["wrong code state"],
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
        summary="Benchmark consistency was checked.",
    )
    evidence = record_evidence(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        evidence_type="benchmark",
        status="supports",
        summary="Validated Si GW benchmark.",
        supports_outputs=["benchmark_consistency"],
        tool_run_ids=[run.run_id],
        validation_result_ids=[validation.result_id],
    )
    packet = create_promotion_packet(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        scope="Si GW benchmark with recorded code state.",
        evidence_refs=[evidence.evidence_id],
        validation_result_ids=[validation.result_id],
        known_failure_modes=["wrong code state"],
    )
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        reason="Promote benchmark workflow memory.",
        requested_by="promotion_policy",
        options=["approve"],
    )
    decided = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="Typed evidence and validation are present.",
        decided_by="human",
    )
    memory = apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=decided.checkpoint_id)
    request = TrustUpdateRequest(
        request_id="trust-req-local-check",
        action="change_claim_confidence",
        session_id="s1",
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        requested_state="locally_checked",
        source_kind="typed_records",
        source_ref=evidence.evidence_id,
        evidence_refs=[evidence.evidence_id],
        code_state_ids=[code_state.code_state_id],
        rationale="Typed validation and benchmark evidence support local confidence.",
    )
    preflight = preflight_trust_update(ws, request)
    apply_trust_update(ws, replace(request, preflight_token=preflight["preflight_token"]))
    return ws, claim, code_state, validation, evidence, memory


def test_claim_trust_audit_reports_typed_support_for_current_confidence(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.trust_audit import audit_claim_trust

    ws, claim, code_state, validation, evidence, memory = _setup_trusted_claim(tmp_path)

    payload = audit_claim_trust(ws, claim_id=claim.claim_id)

    assert require_valid_public_surface("claim_trust_audit", payload) == payload
    assert payload["kind"] == "claim_trust_audit"
    assert payload["truth_source"] == "typed_records"
    assert payload["summary_inputs_trusted"] is False
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False
    assert payload["confidence_state"] == "locally_checked"
    assert payload["support_state"] == "validated_memory_backed"
    assert payload["supporting_evidence_refs"] == [evidence.evidence_id]
    assert payload["passed_validation_result_ids"] == [validation.result_id]
    assert payload["l2_memory_entry_ids"] == [memory.entry_id]
    assert payload["code_state_ids"] == [code_state.code_state_id]
    assert payload["review_actions"] == []
    assert payload["mutation_history_available"] is True
    assert len(payload["trust_update_record_ids"]) == 1
    assert payload["trust_update_record_ids"][0].startswith("trust-update-")


def test_claim_trust_audit_counts_scoped_support_as_evidence_only(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.trust_audit import audit_claim_trust
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qsgw-ac-error-molecules", context_id="librpa", title="QSGW AC")
    claim = create_claim(
        ws,
        topic_id="qsgw-ac-error-molecules",
        statement="Scoped H2O ridge diagnostics reduce AC amplification.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="Si cross-system test is still blocked.",
    )
    evidence = record_evidence(
        ws,
        topic_id="qsgw-ac-error-molecules",
        claim_id=claim.claim_id,
        evidence_type="bounded_numerical_replay",
        status="supports_scoped_claim",
        summary="H2O replay supports the scoped algorithm claim.",
    )

    payload = audit_claim_trust(ws, claim_id=claim.claim_id)

    assert payload["support_state"] == "evidence_only"
    assert payload["supporting_evidence_refs"] == [evidence.evidence_id]
    assert payload["passed_validation_result_ids"] == []


def test_claim_trust_audit_cli_mcp_and_runtime_entrypoint(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_audit_claim_trust
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    _, claim, code_state, *_ = _setup_trusted_claim(tmp_path)

    assert main(["--base", str(tmp_path), "trust", "audit", "--claim", claim.claim_id]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_audit_claim_trust(str(tmp_path), claim_id=claim.claim_id)

    assert cli_payload["code_state_ids"] == [code_state.code_state_id]
    assert mcp_payload == cli_payload
    assert runtime_entrypoints()["audit_claim_trust"] == {
        "cli": "aitp-v5 trust audit <args>",
        "mcp": "aitp_v5_audit_claim_trust",
        "surface": "claim_trust_audit",
    }
    assert validate_runtime_entrypoints() == []


def test_claim_trust_audit_contract_rejects_summary_truth_source():
    import pytest

    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface

    with pytest.raises(ContractError):
        require_valid_public_surface(
            "claim_trust_audit",
            {
                "ok": True,
                "kind": "claim_trust_audit",
                "claim_id": "claim-test",
                "topic_id": "topic-test",
                "confidence_state": "locally_checked",
                "evidence_profile": "toy_numeric",
                "support_state": "evidence_only",
                "supporting_evidence_refs": [],
                "challenging_evidence_refs": [],
                "passed_validation_result_ids": [],
                "failed_validation_result_ids": [],
                "l2_memory_entry_ids": [],
                "code_state_ids": [],
                "trust_update_record_ids": [],
                "review_actions": [],
                "mutation_history_available": False,
                "truth_source": "summary",
                "summary_inputs_trusted": True,
                "can_update_kernel_state": False,
                "can_update_claim_trust": False,
            },
        )
