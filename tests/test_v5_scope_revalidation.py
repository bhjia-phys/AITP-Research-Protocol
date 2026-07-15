from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="scope-revalidation-test", host="pytest")


def _approval_receipt(
    *,
    secret: bytes,
    checkpoint_id: str,
    checkpoint_hash: str,
    rationale: str,
):
    now = datetime.now(UTC)
    payload = {
        "version": "v1",
        "checkpoint_id": checkpoint_id,
        "checkpoint_content_hash": checkpoint_hash,
        "decision": "approve",
        "rationale_hash": hashlib.sha256(rationale.encode("utf-8")).hexdigest(),
        "decided_by": "samur",
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=5)).isoformat(),
        "nonce": "m2-scope-revalidation-test",
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {**payload, "signature": hmac.new(secret, encoded, hashlib.sha256).hexdigest()}


def _seed_scope_proposal(tmp_path, monkeypatch):
    from brain.v5.checkpoint_bindings import (
        decide_bound_checkpoint,
        request_bound_checkpoint,
    )
    from brain.v5.lifecycle_models import CrossTopicRelationRecord
    from brain.v5.models import ValidationResultRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.research_scope import record_cross_topic_relation
    from brain.v5.scope_revalidation import ScopeRevalidationRequest
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "source-topic", context_id="theory", title="Source topic")
    create_topic(ws, "target-topic", context_id="theory", title="Target topic")
    source_claim = create_claim(
        ws,
        topic_id="source-topic",
        statement="A workflow is valid in the source conventions.",
        evidence_profile="code_method",
        confidence_state="supported",
        active_uncertainty="target applicability requires revalidation",
    )
    target_claim = create_claim(
        ws,
        topic_id="target-topic",
        statement="The source workflow may apply after target-side checks.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="target-side validation is pending",
    )
    bridge = CrossTopicRelationRecord(
        relation_id="bridge-source-target-workflow",
        source_topic_id="source-topic",
        target_topic_id="target-topic",
        source_ref=f"claim:{source_claim.claim_id}",
        target_ref=f"claim:{target_claim.claim_id}",
        relation_kind="workflow_applicability",
        transfer_rationale="The numerical method is shared but conventions differ.",
        applicability_boundary="Only the reviewed target parameter regime.",
        revalidation_requirements=["target regression passes"],
        status="approved",
    )
    bridge_write = record_cross_topic_relation(ws, bridge, actor=_actor())
    validation = ValidationResultRecord(
        result_id="validation-target-regression",
        topic_id="target-topic",
        claim_id=target_claim.claim_id,
        contract_id="target-regression-v1",
        tool_run_id="target-regression-run",
        status="passed",
        executor_id="target-regression-checker",
        executor_version="1.0.0",
        executor_hash="d" * 64,
        output_manifest_hash="e" * 64,
        failure_contract_hash="f" * 64,
    )
    validation_write = RecordRepository(ws, actor=_actor()).write(
        "validation_results",
        validation,
    )
    bridge_pin = pin_current_record(ws, bridge_write.record_ref)
    source_pin = pin_current_record(ws, f"claim:{source_claim.claim_id}")
    validation_pin = pin_current_record(ws, validation_write.record_ref)
    now = datetime.now(UTC)
    proposal = ScopeRevalidationRequest(
        bridge=bridge_pin,
        source_refs=(source_pin,),
        source_scope_refs=("topic:source-topic",),
        target_topic_id="target-topic",
        target_claim_id=target_claim.claim_id,
        target_program_id="",
        target_scope_refs=("topic:target-topic", f"claim:{target_claim.claim_id}"),
        allowed_operations=("execute_bound_tool",),
        applicability_conditions=("target regression passes",),
        validation_refs=(validation_pin,),
        evidence_refs=(),
        decision="approved",
        expires_at=(now + timedelta(hours=1)).isoformat(),
    )
    requested = request_bound_checkpoint(
        ws,
        topic_id="target-topic",
        claim_id=target_claim.claim_id,
        reason="Approve exact target-side scope revalidation.",
        requested_by="scope-revalidation-test",
        action="approve_scope_revalidation",
        action_payload=proposal.action_payload(),
        intent_ref=source_pin,
        subject_refs=[bridge_pin, source_pin],
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
    rationale = "Reviewed the exact target-side revalidation and approve it."
    decided = decide_bound_checkpoint(
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
    return ws, proposal, requested, decided, now


def test_scope_revalidation_writer_pins_bridge_sources_validation_and_checkpoint(
    tmp_path,
    monkeypatch,
):
    from brain.v5.pinned_record_refs import build_frozen_dependency_manifest
    from brain.v5.scope_revalidation import record_scope_revalidation

    ws, proposal, requested, decided, now = _seed_scope_proposal(tmp_path, monkeypatch)

    capture = record_scope_revalidation(
        ws,
        proposal,
        binding=requested.binding,
        checkpoint_request_ref=requested.request_ref,
        checkpoint_decision_ref=decided.decision_ref,
        actor=_actor(),
        now=now,
    )
    replay = record_scope_revalidation(
        ws,
        proposal,
        binding=requested.binding,
        checkpoint_request_ref=requested.request_ref,
        checkpoint_decision_ref=decided.decision_ref,
        actor=_actor(),
        now=now,
    )
    closure = build_frozen_dependency_manifest(ws, [capture.pinned_ref])

    assert replay.pinned_ref == capture.pinned_ref
    assert replay.write_status == "unchanged"
    assert capture.record.bridge_ref == proposal.bridge.record_ref
    assert capture.record.bridge_hash == proposal.bridge.content_hash
    assert capture.record.bridge_revision == proposal.bridge.revision
    assert capture.record.allowed_operations == ["execute_bound_tool"]
    assert capture.record.can_update_claim_trust is False
    assert proposal.bridge in closure.nodes
    assert proposal.source_refs[0] in closure.nodes
    assert proposal.validation_refs[0] in closure.nodes
    assert decided.decision_ref in closure.nodes
    assert capture.application_receipt_ref.record_ref.startswith(
        "checkpoint_application_receipt:"
    )


def test_scope_resolver_rejects_same_id_decision_with_wrong_semantics(
    tmp_path,
    monkeypatch,
):
    from brain.v5.models import ScopeRevalidationDecisionRecord
    from brain.v5.record_repository import RecordRepository
    from brain.v5.scope_revalidation import _sha256_json, record_scope_revalidation

    ws, proposal, requested, decided, now = _seed_scope_proposal(tmp_path, monkeypatch)
    identity = {
        **proposal.action_payload(),
        "checkpoint": asdict(decided.decision_ref),
    }
    decision_id = f"scope-revalidation-{_sha256_json(identity)}"
    RecordRepository(ws, actor=_actor()).write(
        "scope_revalidation_decisions",
        ScopeRevalidationDecisionRecord(
            decision_id=decision_id,
            bridge_ref=proposal.bridge.record_ref,
            bridge_hash=proposal.bridge.content_hash,
            bridge_revision=proposal.bridge.revision,
            decision="rejected",
            topic_id="wrong-topic",
        ),
    )

    with pytest.raises(ValueError, match="content does not match"):
        record_scope_revalidation(
            ws,
            proposal,
            binding=requested.binding,
            checkpoint_request_ref=requested.request_ref,
            checkpoint_decision_ref=decided.decision_ref,
            actor=_actor(),
            now=now,
        )


def test_scope_revalidation_rejects_mismatched_checkpoint_and_expired_proposal(
    tmp_path,
    monkeypatch,
):
    from brain.v5.scope_revalidation import record_scope_revalidation

    ws, proposal, requested, decided, now = _seed_scope_proposal(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match="checkpoint payload"):
        record_scope_revalidation(
            ws,
            replace(proposal, allowed_operations=("install_skill",)),
            binding=requested.binding,
            checkpoint_request_ref=requested.request_ref,
            checkpoint_decision_ref=decided.decision_ref,
            actor=_actor(),
            now=now,
        )
    with pytest.raises(ValueError, match="expired"):
        record_scope_revalidation(
            ws,
            replace(proposal, expires_at=(now - timedelta(seconds=1)).isoformat()),
            binding=requested.binding,
            checkpoint_request_ref=requested.request_ref,
            checkpoint_decision_ref=decided.decision_ref,
            actor=_actor(),
            now=now,
        )
