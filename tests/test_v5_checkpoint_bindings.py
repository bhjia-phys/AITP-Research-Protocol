from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="checkpoint-binding-test", host="pytest")


def _seed_bound_records(tmp_path):
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="theory", title="Quantum gravity")
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="An exact execution may become a reviewed baseline.",
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="execution review is pending",
    )
    intent_write = RecordRepository(ws, actor=_actor()).write(
        "intents",
        {
            "intent_id": "intent-qg-baseline",
            "kind": "research_intent",
            "topic_id": "qg",
            "objective": "Review one exact execution baseline.",
        },
        body="# Research Intent\n",
    )
    return (
        ws,
        pin_current_record(ws, intent_write.record_ref),
        pin_current_record(ws, f"claim:{claim.claim_id}"),
    )


def _request(ws, intent, subject, *, now: datetime):
    from brain.v5.checkpoint_bindings import request_bound_checkpoint

    return request_bound_checkpoint(
        ws,
        topic_id="qg",
        claim_id=subject.record_ref.partition(":")[2],
        reason="Review the exact baseline application.",
        requested_by="checkpoint-binding-test",
        action="accept_execution_baseline",
        action_payload={
            "baseline_id": "baseline-qg-001",
            "run_ref": "tool_run:qg-run-001",
        },
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


def _approval_receipt(*, secret: bytes, checkpoint_id: str, request_hash: str):
    rationale = "Reviewed the exact bound request and approve it."
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
        "nonce": "m2-checkpoint-binding-test",
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    receipt = {**payload, "signature": hmac.new(secret, encoded, hashlib.sha256).hexdigest()}
    return rationale, receipt


def test_bound_checkpoint_request_pins_intent_subjects_action_and_payload(tmp_path):
    from brain.v5.checkpoint_bindings import validate_checkpoint_binding

    now = datetime(2026, 7, 15, 0, 0, tzinfo=UTC)
    ws, intent, subject = _seed_bound_records(tmp_path)

    requested = _request(ws, intent, subject, now=now)
    resolved = validate_checkpoint_binding(
        ws,
        requested.request_ref,
        requested.binding,
        now=now,
    )

    assert requested.record.status == "open"
    assert requested.record.action == "accept_execution_baseline"
    assert requested.record.intent_ref == intent.record_ref
    assert requested.record.intent_hash == intent.content_hash
    assert requested.record.intent_revision == intent.revision
    assert requested.record.subject_refs == [
        {
            "record_ref": subject.record_ref,
            "content_hash": subject.content_hash,
            "revision": subject.revision,
        }
    ]
    assert requested.record.payload_hash == requested.binding.action_payload_hash
    assert requested.record.request_hash == requested.binding.request_hash
    assert requested.request_ref.content_hash == resolved.pinned_ref.content_hash
    assert requested.write_status == "created"


def test_checkpoint_binding_rejects_wrong_action_subject_payload_and_expiry(tmp_path):
    from brain.v5.checkpoint_bindings import validate_checkpoint_binding

    now = datetime(2026, 7, 15, 0, 0, tzinfo=UTC)
    ws, intent, subject = _seed_bound_records(tmp_path)
    requested = _request(ws, intent, subject, now=now)

    with pytest.raises(ValueError, match="action does not match"):
        validate_checkpoint_binding(
            ws,
            requested.request_ref,
            replace(requested.binding, action="install_skill"),
            now=now,
        )
    with pytest.raises(ValueError, match="subjects do not match"):
        validate_checkpoint_binding(
            ws,
            requested.request_ref,
            replace(requested.binding, subjects=(intent,)),
            now=now,
        )
    with pytest.raises(ValueError, match="payload hash does not match"):
        validate_checkpoint_binding(
            ws,
            requested.request_ref,
            replace(requested.binding, action_payload_hash="f" * 64),
            now=now,
        )
    with pytest.raises(ValueError, match="expired"):
        validate_checkpoint_binding(
            ws,
            requested.request_ref,
            requested.binding,
            now=now + timedelta(minutes=11),
        )


def test_bound_decision_pins_request_revision_and_requires_host_approval(
    tmp_path,
    monkeypatch,
):
    from brain.v5.checkpoint_bindings import (
        decide_bound_checkpoint,
        validate_checkpoint_binding,
    )
    from brain.v5.pinned_record_refs import get_record_version

    now = datetime.now(UTC)
    ws, intent, subject = _seed_bound_records(tmp_path)
    requested = _request(ws, intent, subject, now=now)
    secret = b"m2-checkpoint-binding-secret-32-bytes"
    monkeypatch.setenv(
        "AITP_HUMAN_APPROVAL_HMAC_KEY_B64",
        base64.b64encode(secret).decode("ascii"),
    )
    rationale, receipt = _approval_receipt(
        secret=secret,
        checkpoint_id=requested.record.checkpoint_id,
        request_hash=requested.request_ref.content_hash,
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
    resolved = validate_checkpoint_binding(
        ws,
        decided.decision_ref,
        requested.binding,
        now=now,
        require_decided=True,
    )

    assert decided.request_ref == requested.request_ref
    assert decided.decision_ref.record_ref == requested.request_ref.record_ref
    assert decided.decision_ref.revision == requested.request_ref.revision + 1
    assert decided.record.status == "decided"
    assert decided.record.decision == "approve"
    assert resolved.frontmatter["supersedes"] == [
        f"{requested.request_ref.record_ref}@sha256:{requested.request_ref.content_hash}"
    ]
    assert get_record_version(ws, requested.request_ref).version_source == "archive"

    receipt_path = (
        ws.root
        / "runtime"
        / "human_approval_receipts"
        / f"{requested.record.checkpoint_id}.json"
    )
    persisted_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    persisted_receipt["nonce"] = "tampered-runtime-receipt"
    receipt_path.write_text(json.dumps(persisted_receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="host-verified approval"):
        validate_checkpoint_binding(
            ws,
            decided.decision_ref,
            requested.binding,
            now=now,
            require_decided=True,
        )


def test_bound_decision_rejects_forged_receipt_metadata_without_signed_receipt(
    tmp_path,
):
    from brain.v5.checkpoint_bindings import validate_checkpoint_binding
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository, WritePolicy

    now = datetime.now(UTC)
    ws, intent, subject = _seed_bound_records(tmp_path)
    requested = _request(ws, intent, subject, now=now)
    forged = replace(
        requested.record,
        status="decided",
        decision="approve",
        rationale="Forged canonical decision metadata.",
        decided_by="model",
        decision_verified=True,
        decision_verification="hmac_sha256_v1",
        decision_receipt_hash=f"sha256:{'a' * 64}",
        decision_receipt_nonce="forged-but-well-shaped",
        can_authorize_trust=True,
    )
    RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="decide_human_checkpoint",
            host="aitp",
        ),
    ).write(
        "checkpoints",
        forged,
        body="# Forged Human Checkpoint Decision\n",
        policy=WritePolicy(
            mode="revision",
            expected_hash=requested.request_ref.content_hash,
        ),
    )

    with pytest.raises(ValueError, match="host-verified approval"):
        validate_checkpoint_binding(
            ws,
            pin_current_record(ws, requested.request_ref.record_ref),
            requested.binding,
            now=now,
            require_decided=True,
        )


def test_bound_decision_rejects_valid_receipt_with_mismatched_canonical_metadata(
    tmp_path,
    monkeypatch,
):
    from brain.v5.checkpoint_bindings import validate_checkpoint_binding
    from brain.v5.human_approval import (
        persist_human_approval_receipt,
        verify_human_approval_receipt,
    )
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository, WritePolicy

    now = datetime.now(UTC)
    ws, intent, subject = _seed_bound_records(tmp_path)
    requested = _request(ws, intent, subject, now=now)
    secret = b"m2-checkpoint-metadata-secret-32-bytes"
    monkeypatch.setenv(
        "AITP_HUMAN_APPROVAL_HMAC_KEY_B64",
        base64.b64encode(secret).decode("ascii"),
    )
    rationale, receipt = _approval_receipt(
        secret=secret,
        checkpoint_id=requested.record.checkpoint_id,
        request_hash=requested.request_ref.content_hash,
    )
    verification = verify_human_approval_receipt(
        ws,
        checkpoint_id=requested.record.checkpoint_id,
        checkpoint_content_hash=requested.request_ref.content_hash,
        decision="approve",
        rationale=rationale,
        decided_by="samur",
        approval_receipt=receipt,
    )
    persist_human_approval_receipt(
        ws,
        requested.record.checkpoint_id,
        receipt,
    )
    mismatched = replace(
        requested.record,
        status="decided",
        decision="approve",
        rationale=rationale,
        decided_by="samur",
        decision_verified=True,
        decision_verification=verification.method,
        decision_receipt_hash=f"sha256:{'b' * 64}",
        decision_receipt_nonce=verification.nonce,
        can_authorize_trust=True,
    )
    RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="decide_human_checkpoint",
            host="aitp",
        ),
    ).write(
        "checkpoints",
        mismatched,
        body="# Mismatched Human Checkpoint Decision\n",
        policy=WritePolicy(
            mode="revision",
            expected_hash=requested.request_ref.content_hash,
        ),
    )

    with pytest.raises(ValueError, match="does not match persisted metadata"):
        validate_checkpoint_binding(
            ws,
            pin_current_record(ws, requested.request_ref.record_ref),
            requested.binding,
            now=now,
            require_decided=True,
        )


def test_legacy_unbound_checkpoint_cannot_authorize_v2_action(tmp_path):
    from brain.v5.checkpoint_bindings import validate_checkpoint_binding
    from brain.v5.checkpoints import request_human_checkpoint
    from brain.v5.pinned_record_refs import pin_current_record

    now = datetime(2026, 7, 15, 0, 0, tzinfo=UTC)
    ws, intent, subject = _seed_bound_records(tmp_path)
    requested = _request(ws, intent, subject, now=now)
    legacy = request_human_checkpoint(
        ws,
        topic_id="qg",
        claim_id=subject.record_ref.partition(":")[2],
        reason="Legacy human review.",
        requested_by="legacy-test",
        options=["approve", "reject"],
    )

    with pytest.raises(ValueError, match="not a v2 bound checkpoint"):
        validate_checkpoint_binding(
            ws,
            pin_current_record(ws, f"human_checkpoint:{legacy.checkpoint_id}"),
            requested.binding,
            now=now,
        )
