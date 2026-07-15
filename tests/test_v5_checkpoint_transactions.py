from __future__ import annotations

import base64
import hashlib
import hmac
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest


ACTION_PAYLOAD = {
    "baseline_id": "baseline-qg-001",
    "run_ref": "tool_run:qg-run-001",
}


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="checkpoint-transaction-test", host="pytest")


def _approved_checkpoint(root, monkeypatch):
    from brain.v5.checkpoint_bindings import (
        decide_bound_checkpoint,
        request_bound_checkpoint,
    )
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(root)
    create_topic(ws, "qg", context_id="theory", title="Quantum gravity")
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="An exact execution may become a reviewed baseline.",
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="execution review is pending",
    )
    repository = RecordRepository(ws, actor=_actor())
    intent_write = repository.write(
        "intents",
        {
            "intent_id": "intent-qg-baseline",
            "kind": "research_intent",
            "topic_id": "qg",
            "objective": "Review one exact execution baseline.",
        },
        body="# Research Intent\n",
    )
    intent = pin_current_record(ws, intent_write.record_ref)
    subject = pin_current_record(ws, f"claim:{claim.claim_id}")
    now = datetime.now(UTC)
    requested = request_bound_checkpoint(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        reason="Review the exact baseline application.",
        requested_by="checkpoint-transaction-test",
        action="accept_execution_baseline",
        action_payload=ACTION_PAYLOAD,
        intent_ref=intent,
        subject_refs=[subject],
        options=["approve", "reject"],
        expires_at=(now + timedelta(minutes=10)).isoformat(),
        replay_policy="exact_idempotent",
        target_scope_refs=["topic:qg", subject.record_ref],
        effect_policy="execution_maturity_only",
        actor=_actor(),
        now=now,
    )
    secret = b"m2-checkpoint-transaction-secret-32-bytes"
    monkeypatch.setenv(
        "AITP_HUMAN_APPROVAL_HMAC_KEY_B64",
        base64.b64encode(secret).decode("ascii"),
    )
    rationale = "Reviewed the exact bound request and approve it."
    receipt = _approval_receipt(
        secret=secret,
        checkpoint_id=requested.record.checkpoint_id,
        request_hash=requested.request_ref.content_hash,
        rationale=rationale,
    )
    decided = decide_bound_checkpoint(
        ws,
        request_ref=requested.request_ref,
        expected=requested.binding,
        decision="approve",
        rationale=rationale,
        decided_by="samur",
        approval_receipt=receipt,
        now=now,
    )
    return ws, requested, decided, now


def _approval_receipt(
    *,
    secret: bytes,
    checkpoint_id: str,
    request_hash: str,
    rationale: str,
):
    now = datetime.now(UTC)
    payload = {
        "version": "v1",
        "checkpoint_id": checkpoint_id,
        "checkpoint_content_hash": request_hash,
        "decision": "approve",
        "rationale_hash": hashlib.sha256(rationale.encode("utf-8")).hexdigest(),
        "decided_by": "samur",
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=5)).isoformat(),
        "nonce": "m2-checkpoint-transaction-test",
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {**payload, "signature": hmac.new(secret, encoded, hashlib.sha256).hexdigest()}


def _write_result(ws, application_id):
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.record_repository import RecordRepository

    result_id = f"result-{application_id}"
    write = RecordRepository(ws, actor=_actor()).write(
        "attempts",
        {
            "attempt_id": result_id,
            "kind": "attempt",
            "topic_id": "qg",
            "result": "baseline accepted",
        },
        body="# Applied Checkpoint Result\n",
    )
    return PinnedRecordRef(
        record_ref=write.record_ref,
        content_hash=write.content_hash,
        revision=write.revision,
    )


def _resolve_result(ws, application_id):
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository

    record_ref = f"attempt:result-{application_id}"
    if RecordRepository(ws, actor=_actor()).read(record_ref).status != "found":
        return None
    return pin_current_record(ws, record_ref)


def _validate_result(application_id, result_pin):
    expected = f"attempt:result-{application_id}"
    if result_pin.record_ref != expected:
        raise ValueError("checkpoint result does not belong to the application")


def _apply(ws, requested, decided, now, result_writer, **kwargs):
    from brain.v5.checkpoint_transactions import apply_bound_checkpoint_action

    result_resolver = kwargs.pop(
        "result_resolver",
        lambda application_id: _resolve_result(ws, application_id),
    )
    result_validator = kwargs.pop("result_validator", _validate_result)
    return apply_bound_checkpoint_action(
        ws,
        binding=requested.binding,
        request_ref=requested.request_ref,
        decision_ref=decided.decision_ref,
        action_payload=ACTION_PAYLOAD,
        result_writer=result_writer,
        result_resolver=result_resolver,
        result_validator=result_validator,
        actor=_actor(),
        now=now,
        **kwargs,
    )


def test_application_receipt_is_exact_idempotent_and_closes_archived_dependencies(
    tmp_path,
    monkeypatch,
):
    from brain.v5.pinned_record_refs import build_frozen_dependency_manifest

    ws, requested, decided, now = _approved_checkpoint(tmp_path, monkeypatch)
    calls = []

    def result_writer(application_id):
        calls.append(application_id)
        return _write_result(ws, application_id)

    applied = _apply(ws, requested, decided, now, result_writer)
    replayed = _apply(ws, requested, decided, now, result_writer)
    closure = build_frozen_dependency_manifest(ws, [applied.receipt_ref])

    assert calls == [applied.record.application_id]
    assert applied.replayed is False
    assert replayed.replayed is True
    assert replayed.receipt_ref == applied.receipt_ref
    assert applied.record.intent_ref == requested.binding.intent.record_ref
    assert applied.record.intent_hash == requested.binding.intent.content_hash
    assert applied.record.request_ref == requested.request_ref.record_ref
    assert applied.record.request_hash == requested.request_ref.content_hash
    assert applied.record.request_revision == requested.request_ref.revision
    assert applied.record.decision_ref == decided.decision_ref.record_ref
    assert applied.record.decision_hash == decided.decision_ref.content_hash
    assert applied.record.decision_revision == decided.decision_ref.revision
    assert applied.record.result_ref == applied.result_ref.record_ref
    assert applied.record.status == "applied"
    assert requested.request_ref in closure.nodes
    assert decided.decision_ref in closure.nodes
    assert applied.result_ref in closure.nodes


def test_failed_application_is_recorded_and_same_intent_cannot_retry(tmp_path, monkeypatch):
    from brain.v5.checkpoint_transactions import (
        CheckpointApplicationFailed,
        CheckpointReplayRejected,
    )
    from brain.v5.record_repository import RecordRepository

    ws, requested, decided, now = _approved_checkpoint(tmp_path, monkeypatch)

    def failing_writer(_application_id):
        raise RuntimeError("simulated external action failure")

    with pytest.raises(CheckpointApplicationFailed, match="simulated external action failure"):
        _apply(ws, requested, decided, now, failing_writer)

    report = RecordRepository(ws, actor=_actor()).list("checkpoint_application_receipts")
    assert report.loaded_count == 1
    assert report.records[0].status == "failed"
    assert report.records[0].errors[0]["error_type"] == "RuntimeError"

    with pytest.raises(CheckpointReplayRejected, match="failed application"):
        _apply(ws, requested, decided, now, lambda app_id: _write_result(ws, app_id))


def test_interruption_before_and_after_result_write_reconciles_on_retry(
    tmp_path,
    monkeypatch,
):
    from brain.v5.checkpoint_transactions import CheckpointApplicationInterrupted

    before_ws, before_request, before_decision, before_now = _approved_checkpoint(
        tmp_path / "before",
        monkeypatch,
    )
    before_calls = []

    def before_writer(application_id):
        before_calls.append(application_id)
        return _write_result(before_ws, application_id)

    with pytest.raises(CheckpointApplicationInterrupted, match="before result write"):
        _apply(
            before_ws,
            before_request,
            before_decision,
            before_now,
            before_writer,
            failpoint="before_result_write",
        )
    before_applied = _apply(
        before_ws,
        before_request,
        before_decision,
        before_now,
        before_writer,
    )
    assert before_calls == [before_applied.record.application_id]

    after_ws, after_request, after_decision, after_now = _approved_checkpoint(
        tmp_path / "after",
        monkeypatch,
    )
    after_calls = []

    def after_writer(application_id):
        after_calls.append(application_id)
        return _write_result(after_ws, application_id)

    with pytest.raises(CheckpointApplicationInterrupted, match="after result write"):
        _apply(
            after_ws,
            after_request,
            after_decision,
            after_now,
            after_writer,
            failpoint="after_result_write",
        )
    after_applied = _apply(
        after_ws,
        after_request,
        after_decision,
        after_now,
        after_writer,
    )
    assert after_calls == [after_applied.record.application_id]


def test_result_written_before_journal_is_recovered_without_reexecuting(
    tmp_path,
    monkeypatch,
):
    from brain.v5.checkpoint_transactions import CheckpointApplicationInterrupted

    ws, requested, decided, now = _approved_checkpoint(tmp_path, monkeypatch)
    calls = []

    def result_writer(application_id):
        calls.append(application_id)
        return _write_result(ws, application_id)

    with pytest.raises(CheckpointApplicationInterrupted, match="before journal"):
        _apply(
            ws,
            requested,
            decided,
            now,
            result_writer,
            failpoint="after_result_before_journal",
        )

    recovered = _apply(ws, requested, decided, now, result_writer)

    assert calls == [recovered.record.application_id]
    assert recovered.record.status == "applied"
    assert recovered.result_ref == _resolve_result(ws, recovered.record.application_id)


def test_journal_result_is_revalidated_before_receipt_is_written(tmp_path, monkeypatch):
    from brain.v5.checkpoint_transactions import CheckpointApplicationInterrupted

    ws, requested, decided, now = _approved_checkpoint(tmp_path, monkeypatch)

    with pytest.raises(CheckpointApplicationInterrupted, match="after result write"):
        _apply(
            ws,
            requested,
            decided,
            now,
            lambda application_id: _write_result(ws, application_id),
            result_validator=lambda _application_id, _result: None,
            failpoint="after_result_write",
        )

    def reject_stale_semantics(_application_id, _result):
        raise ValueError("journal result semantics do not match")

    with pytest.raises(ValueError, match="semantics do not match"):
        _apply(
            ws,
            requested,
            decided,
            now,
            lambda application_id: _write_result(ws, application_id),
            result_validator=reject_stale_semantics,
        )


def test_writer_exception_after_result_creation_recovers_instead_of_recording_failure(
    tmp_path,
    monkeypatch,
):
    ws, requested, decided, now = _approved_checkpoint(tmp_path, monkeypatch)

    def write_then_raise(application_id):
        _write_result(ws, application_id)
        raise RuntimeError("crashed after canonical result write")

    recovered = _apply(ws, requested, decided, now, write_then_raise)

    assert recovered.record.status == "applied"
    assert recovered.result_ref == _resolve_result(ws, recovered.record.application_id)
    assert recovered.record.errors == []


def test_resolver_cannot_claim_unrelated_result_for_application(tmp_path, monkeypatch):
    from brain.v5.record_repository import RecordRepository

    ws, requested, decided, now = _approved_checkpoint(tmp_path, monkeypatch)
    unrelated = _write_result(ws, "unrelated-application")

    with pytest.raises(ValueError, match="does not belong"):
        _apply(
            ws,
            requested,
            decided,
            now,
            lambda application_id: _write_result(ws, application_id),
            result_resolver=lambda _application_id: unrelated,
        )

    assert (
        RecordRepository(ws, actor=_actor())
        .list("checkpoint_application_receipts")
        .loaded_count
        == 0
    )


def test_concurrent_consumers_produce_one_result_and_one_receipt(tmp_path, monkeypatch):
    ws, requested, decided, now = _approved_checkpoint(tmp_path, monkeypatch)
    entered = threading.Event()
    release = threading.Event()
    calls = []
    calls_lock = threading.Lock()

    def result_writer(application_id):
        with calls_lock:
            calls.append(application_id)
        entered.set()
        assert release.wait(timeout=5)
        return _write_result(ws, application_id)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(_apply, ws, requested, decided, now, result_writer)
        assert entered.wait(timeout=5)
        second = executor.submit(_apply, ws, requested, decided, now, result_writer)
        release.set()
        outcomes = [first.result(timeout=10), second.result(timeout=10)]

    assert len(calls) == 1
    assert outcomes[0].receipt_ref == outcomes[1].receipt_ref
    assert sorted(outcome.replayed for outcome in outcomes) == [False, True]
