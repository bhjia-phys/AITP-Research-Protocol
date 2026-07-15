from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import pytest


def _bind_session(ws, claim_id: str, *, topic_id: str) -> None:
    from brain.v5.workspace import bind_session

    bind_session(
        ws,
        "execution-facade-session",
        topic_id=topic_id,
        context_id="theory",
        runtime="pytest",
        active_claim=claim_id,
    )


def test_bound_checkpoint_facade_requires_host_receipt_file(
    tmp_path,
    monkeypatch,
    require_real_human_approval,
):
    from tests.test_v5_checkpoint_bindings import (
        _approval_receipt,
        _seed_bound_records,
    )

    from brain.v5.mcp_execution import (
        aitp_v5_execution_decide_bound_checkpoint,
        aitp_v5_execution_request_bound_checkpoint,
    )

    ws, intent, subject = _seed_bound_records(tmp_path)
    claim_id = subject.record_ref.partition(":")[2]
    _bind_session(ws, claim_id, topic_id="qg")
    now = datetime.now(UTC)
    request_payload = {
        "session_id": "execution-facade-session",
        "topic_id": "qg",
        "claim_id": claim_id,
        "reason": "Review the exact baseline application.",
        "requested_by": "execution-facade-test",
        "action": "accept_execution_baseline",
        "action_payload": {"run_ref": subject.record_ref},
        "intent_ref": asdict(intent),
        "subject_refs": [asdict(subject)],
        "options": ["approve", "reject"],
        "expires_at": (now + timedelta(minutes=10)).isoformat(),
        "replay_policy": "exact_idempotent",
        "target_scope_refs": ["topic:qg", subject.record_ref],
        "effect_policy": "execution_maturity_only",
    }
    with pytest.raises(ValueError, match="session scope"):
        aitp_v5_execution_request_bound_checkpoint(
            str(tmp_path),
            payload_json=json.dumps({**request_payload, "claim_id": "foreign-claim"}),
        )
    requested = aitp_v5_execution_request_bound_checkpoint(
        str(tmp_path),
        payload_json=json.dumps(request_payload),
    )
    assert requested["result"]["request_ref"]["record_ref"].startswith("human_checkpoint:")
    assert requested["result"]["pre_tool_decision"]["block"] is False
    assert requested["can_update_claim_trust"] is False
    from brain.v5.pinned_record_refs import get_record_version

    stored_request = get_record_version(ws, requested["result"]["request_ref"])
    assert stored_request.frontmatter["created_by"]["actor_type"] == "tool"
    assert stored_request.frontmatter["created_by"]["actor_id"] == "execution-gated-facade"

    decision_payload = {
        "session_id": "execution-facade-session",
        "request_ref": requested["result"]["request_ref"],
        "binding": requested["result"]["binding"],
        "decision": "approve",
        "rationale": "Reviewed the exact bound request and approve it.",
        "decided_by": "samur",
    }
    with pytest.raises(ValueError, match="host-verified human approval receipt"):
        aitp_v5_execution_decide_bound_checkpoint(
            str(tmp_path),
            payload_json=json.dumps(decision_payload),
        )

    secret = b"m2-checkpoint-binding-secret-32-bytes"
    monkeypatch.setenv(
        "AITP_HUMAN_APPROVAL_HMAC_KEY_B64",
        __import__("base64").b64encode(secret).decode("ascii"),
    )
    checkpoint_id = requested["result"]["checkpoint_id"]
    rationale, receipt = _approval_receipt(
        secret=secret,
        checkpoint_id=checkpoint_id,
        request_hash=requested["result"]["request_ref"]["content_hash"],
    )
    decision_payload["rationale"] = rationale
    receipt_dir = ws.root / "runtime" / "human_approval_receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{checkpoint_id}.json").write_text(
        json.dumps(receipt),
        encoding="utf-8",
    )

    decided = aitp_v5_execution_decide_bound_checkpoint(
        str(tmp_path),
        payload_json=json.dumps(decision_payload),
    )
    assert decided["result"]["decision_ref"]["revision"] == 2
    assert decided["result"]["request_ref"] == requested["result"]["request_ref"]
    assert decided["result"]["pre_tool_decision"]["block"] is False


def test_bound_execution_apply_facade_returns_exact_transaction_receipt(
    tmp_path,
    monkeypatch,
):
    from tests.test_v5_bound_execution import _approved_request

    from brain.v5.mcp_execution import aitp_v5_execution_apply_bound_action

    ws, request, requested, decided, _now = _approved_request(tmp_path, monkeypatch)
    _bind_session(ws, request.claim_id, topic_id="compute")
    payload = {
        "session_id": "execution-facade-session",
        "action": "execute_bound_tool",
        "request_ref": asdict(requested.request_ref),
        "decision_ref": asdict(decided.decision_ref),
        "binding": asdict(requested.binding),
        "action_request": request.action_payload(),
    }

    result = aitp_v5_execution_apply_bound_action(
        str(tmp_path),
        payload_json=json.dumps(payload),
    )

    assert result["result"]["action"] == "execute_bound_tool"
    assert len(result["result"]["result_refs"]) == 2
    assert {
        pin["record_ref"].partition(":")[0]
        for pin in result["result"]["result_refs"]
    } == {"tool_run", "validation_result"}
    assert result["result"]["application_receipt_ref"]["record_ref"].startswith(
        "checkpoint_application_receipt:"
    )
    assert result["result"]["pre_tool_decision"]["block"] is False
    assert result["can_update_claim_trust"] is False


def test_scope_revalidation_apply_facade_returns_exact_transaction_receipt(
    tmp_path,
    monkeypatch,
):
    from tests.test_v5_scope_revalidation import _seed_scope_proposal

    from brain.v5.mcp_execution import aitp_v5_execution_apply_bound_action

    ws, proposal, requested, decided, _now = _seed_scope_proposal(tmp_path, monkeypatch)
    _bind_session(ws, proposal.target_claim_id, topic_id=proposal.target_topic_id)
    result = aitp_v5_execution_apply_bound_action(
        str(tmp_path),
        payload_json=json.dumps({
            "session_id": "execution-facade-session",
            "action": "approve_scope_revalidation",
            "request_ref": asdict(requested.request_ref),
            "decision_ref": asdict(decided.decision_ref),
            "binding": asdict(requested.binding),
            "action_request": proposal.action_payload(),
        }),
    )

    assert result["result"]["result_refs"][0]["record_ref"].startswith(
        "scope_revalidation_decision:"
    )
    assert result["result"]["application_receipt_ref"]["record_ref"].startswith(
        "checkpoint_application_receipt:"
    )


def test_baseline_apply_facade_returns_exact_transaction_receipt(tmp_path, monkeypatch):
    from tests.test_v5_execution_baselines import _approval, _actor, _ready_chain

    from brain.v5.checkpoint_bindings import decide_bound_checkpoint, request_bound_checkpoint
    from brain.v5.execution_baselines import BaselineAcceptanceRequest, assess_baseline_readiness
    from brain.v5.mcp_execution import aitp_v5_execution_apply_bound_action

    ws, claim, claim_ref, _run, run_ref, validation_ref, _monitor_ref = _ready_chain(tmp_path)
    request = BaselineAcceptanceRequest(run_ref=run_ref, validation_refs=(validation_ref,))
    readiness = assess_baseline_readiness(ws, request)
    now = datetime.now(UTC)
    checkpoint = request_bound_checkpoint(
        ws,
        topic_id="compute",
        claim_id=claim.claim_id,
        reason="Accept exact reproducible execution baseline.",
        requested_by="execution-facade-test",
        action="accept_execution_baseline",
        action_payload=request.action_payload(),
        intent_ref=claim_ref,
        subject_refs=list(readiness.frozen_dependencies.nodes),
        options=["approve", "reject"],
        expires_at=(now + timedelta(minutes=10)).isoformat(),
        replay_policy="exact_idempotent",
        target_scope_refs=["topic:compute", f"claim:{claim.claim_id}"],
        effect_policy="execution_maturity_only",
        actor=_actor(),
        now=now,
    )
    secret = b"baseline-approval-secret-32-bytes"
    monkeypatch.setenv(
        "AITP_HUMAN_APPROVAL_HMAC_KEY_B64",
        __import__("base64").b64encode(secret).decode(),
    )
    rationale = "Reviewed the exact frozen dependency closure."
    decision = decide_bound_checkpoint(
        ws,
        request_ref=checkpoint.request_ref,
        expected=checkpoint.binding,
        decision="approve",
        rationale=rationale,
        decided_by="samur",
        approval_receipt=_approval(
            secret,
            checkpoint.record.checkpoint_id,
            checkpoint.request_ref.content_hash,
            rationale,
        ),
        now=now,
    )
    _bind_session(ws, claim.claim_id, topic_id="compute")

    result = aitp_v5_execution_apply_bound_action(
        str(tmp_path),
        payload_json=json.dumps({
            "session_id": "execution-facade-session",
            "action": "accept_execution_baseline",
            "request_ref": asdict(checkpoint.request_ref),
            "decision_ref": asdict(decision.decision_ref),
            "binding": asdict(checkpoint.binding),
            "action_request": request.action_payload(),
        }),
    )

    assert result["result"]["result_refs"][0]["record_ref"].startswith(
        "execution_baseline:"
    )
    assert result["result"]["application_receipt_ref"]["record_ref"].startswith(
        "checkpoint_application_receipt:"
    )


def test_bound_apply_pretool_blocks_without_approved_checkpoint(tmp_path):
    from tests.test_v5_checkpoint_bindings import _seed_bound_records

    from brain.v5.pretool_policy import evaluate_context_pre_tool_policy

    ws, _intent, subject = _seed_bound_records(tmp_path)
    claim_id = subject.record_ref.partition(":")[2]
    _bind_session(ws, claim_id, topic_id="qg")

    for action in (
        "accept_execution_baseline",
        "approve_scope_revalidation",
        "execute_bound_tool",
    ):
        decision = evaluate_context_pre_tool_policy(
            ws,
            session_id="execution-facade-session",
            action=action,
            claim_id=claim_id,
            source_kind="typed_records",
            risk_level="guided",
        )
        assert decision["block"] is True
        assert "human_checkpoint" in decision["message"]


def test_apply_surface_rejects_cross_checkpoint_and_duplicate_results():
    from brain.v5.execution_surface_contracts import validate_execution_operation_result

    request_ref = {
        "record_ref": "human_checkpoint:a",
        "content_hash": "a" * 64,
        "revision": 1,
    }
    decision_ref = {
        "record_ref": "human_checkpoint:b",
        "content_hash": "b" * 64,
        "revision": 3,
    }
    run = {"record_ref": "tool_run:r", "content_hash": "c" * 64, "revision": 1}
    receipt = {
        "record_ref": "checkpoint_application_receipt:x",
        "content_hash": "d" * 64,
        "revision": 1,
    }
    payload = {
        "ok": True,
        "kind": "execution_operation_result",
        "operation": "execution_apply_bound_action",
        "state_effect": "kernel_write",
        "writes_records": True,
        "result": {
            "status": "applied",
            "session_id": "s1",
            "claim_id": "c1",
            "action": "execute_bound_tool",
            "request_ref": request_ref,
            "decision_ref": decision_ref,
            "result_refs": [run, run],
            "application_receipt_ref": receipt,
            "replayed": False,
            "pre_tool_decision": {
                "block": False,
                "action": "execute_bound_tool",
                "session_id": "s1",
                "claim_id": "c1",
                "human_checkpoint_id": "b",
                "truth_source": "typed_records",
                "can_update_kernel_state": False,
                "can_update_claim_trust": False,
            },
        },
        "truth_source": "typed_records_and_host_attestation",
        "summary_inputs_trusted": False,
        "orientation_only": False,
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }

    validation = validate_execution_operation_result(payload)
    assert validation.ok is False
    assert any(issue.path.endswith("decision_ref.record_ref") for issue in validation.issues)
    assert any(issue.path.endswith("decision_ref.revision") for issue in validation.issues)
    assert any(issue.path.endswith("result_refs") for issue in validation.issues)
