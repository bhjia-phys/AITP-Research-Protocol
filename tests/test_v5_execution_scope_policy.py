from __future__ import annotations

import base64
from dataclasses import replace
from datetime import timedelta


def _seed(tmp_path, monkeypatch):
    from tests.test_v5_scope_revalidation import _actor, _seed_scope_proposal

    from brain.v5.scope_revalidation import record_scope_revalidation

    ws, proposal, requested, decided, now = _seed_scope_proposal(tmp_path, monkeypatch)
    decision = record_scope_revalidation(
        ws,
        proposal,
        binding=requested.binding,
        checkpoint_request_ref=requested.request_ref,
        checkpoint_decision_ref=decided.decision_ref,
        actor=_actor(),
        now=now,
    )
    return ws, proposal, decision, now


def test_same_topic_dependencies_need_no_cross_topic_revalidation(tmp_path, monkeypatch):
    from brain.v5.execution_scope_policy import assess_execution_scope

    ws, proposal, _decision, now = _seed(tmp_path, monkeypatch)

    scope = assess_execution_scope(
        ws,
        operation="execute_bound_tool",
        consumer_scope=proposal.target_scope_refs,
        dependency_refs=proposal.validation_refs,
        now=now,
    )

    assert scope.decision == "allowed"
    assert scope.foreign_dependency_refs == ()
    assert scope.accepted_revalidation_refs == ()
    assert scope.can_update_claim_trust is False


def test_foreign_dependency_requires_exact_target_revalidation_not_bare_bridge(
    tmp_path,
    monkeypatch,
):
    from brain.v5.execution_scope_policy import assess_execution_scope

    ws, proposal, decision, now = _seed(tmp_path, monkeypatch)

    missing = assess_execution_scope(
        ws,
        operation="execute_bound_tool",
        consumer_scope=proposal.target_scope_refs,
        dependency_refs=proposal.source_refs,
        now=now,
    )
    allowed = assess_execution_scope(
        ws,
        operation="execute_bound_tool",
        consumer_scope=proposal.target_scope_refs,
        dependency_refs=proposal.source_refs,
        revalidation_decision_refs=(decision.pinned_ref,),
        now=now,
    )

    assert missing.decision == "requires_revalidation"
    assert missing.foreign_dependency_refs == proposal.source_refs
    assert "bridge presence is not target validation" in missing.reasons
    assert allowed.decision == "allowed"
    assert allowed.accepted_revalidation_refs == (decision.pinned_ref,)


def test_scope_revalidation_is_operation_and_expiry_bounded(tmp_path, monkeypatch):
    from brain.v5.execution_scope_policy import assess_execution_scope

    ws, proposal, decision, now = _seed(tmp_path, monkeypatch)

    wrong_operation = assess_execution_scope(
        ws,
        operation="install_skill",
        consumer_scope=proposal.target_scope_refs,
        dependency_refs=proposal.source_refs,
        revalidation_decision_refs=(decision.pinned_ref,),
        now=now,
    )
    expired = assess_execution_scope(
        ws,
        operation="execute_bound_tool",
        consumer_scope=proposal.target_scope_refs,
        dependency_refs=proposal.source_refs,
        revalidation_decision_refs=(decision.pinned_ref,),
        now=now + timedelta(hours=2),
    )

    assert wrong_operation.decision == "requires_revalidation"
    assert "operation is outside the reviewed applicability" in wrong_operation.reasons
    assert expired.decision == "requires_revalidation"
    assert "scope revalidation decision has expired" in expired.reasons


def test_unresolvable_revalidation_pin_fails_closed(tmp_path, monkeypatch):
    from brain.v5.execution_scope_policy import assess_execution_scope
    from brain.v5.pinned_record_refs import PinnedRecordRef

    ws, proposal, decision, now = _seed(tmp_path, monkeypatch)
    wrong = PinnedRecordRef(
        record_ref=decision.pinned_ref.record_ref,
        content_hash="0" * 64,
        revision=decision.pinned_ref.revision,
    )

    scope = assess_execution_scope(
        ws,
        operation="execute_bound_tool",
        consumer_scope=proposal.target_scope_refs,
        dependency_refs=proposal.source_refs,
        revalidation_decision_refs=(wrong,),
        now=now,
    )

    assert scope.decision == "denied"
    assert scope.read_errors


def test_superseded_scope_decision_cannot_authorize_execution(tmp_path, monkeypatch):
    from tests.test_v5_scope_revalidation import _actor, _approval_receipt

    from brain.v5.checkpoint_bindings import (
        decide_bound_checkpoint,
        request_bound_checkpoint,
    )
    from brain.v5.execution_scope_policy import assess_execution_scope
    from brain.v5.scope_revalidation import record_scope_revalidation

    ws, proposal, decision, now = _seed(tmp_path, monkeypatch)
    revocation = replace(
        proposal,
        decision="rejected",
        allowed_operations=(),
        supersedes_decision=decision.pinned_ref,
    )
    requested = request_bound_checkpoint(
        ws,
        topic_id=proposal.target_topic_id,
        claim_id=proposal.target_claim_id,
        reason="Revoke the exact target-side scope revalidation.",
        requested_by="scope-revalidation-test",
        action="approve_scope_revalidation",
        action_payload=revocation.action_payload(),
        intent_ref=proposal.source_refs[0],
        subject_refs=[proposal.bridge, *proposal.source_refs],
        options=["approve", "reject"],
        expires_at=(now + timedelta(minutes=30)).isoformat(),
        replay_policy="exact_idempotent",
        target_scope_refs=list(proposal.target_scope_refs),
        effect_policy="scope_revalidation_only",
        actor=_actor(),
        now=now,
    )
    secret = b"m2-scope-revalidation-secret-32-bytes"
    monkeypatch.setenv(
        "AITP_HUMAN_APPROVAL_HMAC_KEY_B64",
        base64.b64encode(secret).decode("ascii"),
    )
    rationale = "Reviewed the exact target-side revocation and approve it."
    checkpoint = decide_bound_checkpoint(
        ws,
        request_ref=requested.request_ref,
        expected=requested.binding,
        decision="approve",
        rationale=rationale,
        decided_by="samur",
        approval_receipt=_approval_receipt(
            secret=secret,
            checkpoint_id=requested.record.checkpoint_id,
            checkpoint_hash=requested.request_ref.content_hash,
            rationale=rationale,
        ),
        now=now,
    )
    revocation_capture = record_scope_revalidation(
        ws,
        revocation,
        binding=requested.binding,
        checkpoint_request_ref=requested.request_ref,
        checkpoint_decision_ref=checkpoint.decision_ref,
        actor=_actor(),
        now=now,
    )

    scope = assess_execution_scope(
        ws,
        operation="execute_bound_tool",
        consumer_scope=proposal.target_scope_refs,
        dependency_refs=proposal.source_refs,
        revalidation_decision_refs=(decision.pinned_ref,),
        now=now,
    )

    assert scope.decision == "requires_revalidation"
    assert "scope revalidation decision has been superseded" in scope.reasons

    from brain.v5.record_repository import RecordRepository

    RecordRepository(ws, actor=_actor()).write(
        "scope_revalidation_decisions",
        replace(
            revocation_capture.record,
            decision_id=revocation_capture.record.decision_id + "-branch",
        ),
    )
    branched = assess_execution_scope(
        ws,
        operation="execute_bound_tool",
        consumer_scope=proposal.target_scope_refs,
        dependency_refs=proposal.source_refs,
        revalidation_decision_refs=(decision.pinned_ref,),
        now=now,
    )

    assert branched.decision == "denied"
    assert "multiple successors" in branched.read_errors[0]
    assert scope.accepted_revalidation_refs == ()
