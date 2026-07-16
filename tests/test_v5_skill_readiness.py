from __future__ import annotations

import base64
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="skill-readiness-test", host="pytest")


def _candidate(tmp_path, *, single_use: bool = False, no_known_failures: bool = False):
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.skill_distillation_records import (
        build_skill_distillation_candidate,
        record_skill_distillation_candidate,
    )
    from tests.test_v5_skill_distillation_records import _request

    ws, request = _request(tmp_path)
    if single_use:
        request = replace(
            request,
            execution_refs=request.execution_refs[:1],
            validation_refs=request.validation_refs[:1],
            artifact_refs=request.artifact_refs[:1],
        )
    if no_known_failures:
        request = replace(
            request,
            known_failures=(),
            failure_boundary=(
                "No relevant failure is known after two independent final runs; "
                "reassess after any code, environment, or input-schema change."
            ),
        )
    report = build_skill_distillation_candidate(ws, request)
    write = record_skill_distillation_candidate(ws, report, actor=_actor())
    return ws, PinnedRecordRef(write.record_ref, write.content_hash, write.revision), report.candidate


def _approval_receipt(*, secret: bytes, checkpoint_id: str, request_hash: str, rationale: str):
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
        "nonce": "skill-readiness-exception-test",
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {**payload, "signature": hmac.new(secret, encoded, hashlib.sha256).hexdigest()}


def _expert_exception(ws, candidate_ref, monkeypatch):
    from brain.v5.checkpoint_bindings import decide_bound_checkpoint, request_bound_checkpoint

    now = datetime.now(UTC)
    requested = request_bound_checkpoint(
        ws,
        topic_id="librpa",
        claim_id=candidate_ref.record_ref.partition(":")[2],
        reason="Review one narrow validated use as a Skill readiness exception.",
        requested_by="skill-readiness-test",
        action="approve_skill_readiness_exception",
        action_payload={
            "candidate_id": candidate_ref.record_ref.partition(":")[2],
            "candidate_hash": candidate_ref.content_hash,
            "exception": "single_narrow_validated_use",
        },
        intent_ref=candidate_ref,
        subject_refs=[candidate_ref],
        options=["approve", "reject"],
        expires_at=(now + timedelta(minutes=10)).isoformat(),
        replay_policy="exact_once",
        target_scope_refs=["topic:librpa", candidate_ref.record_ref],
        effect_policy="skill_readiness_exception_only_no_claim_trust",
        actor=_actor(),
        now=now,
    )
    secret = b"skill-readiness-test-host-secret-32-bytes"
    monkeypatch.setenv(
        "AITP_HUMAN_APPROVAL_HMAC_KEY_B64",
        base64.b64encode(secret).decode("ascii"),
    )
    rationale = "Reviewed the exact narrow workflow and approve only this readiness exception."
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
    return decided.decision_ref


def test_two_independent_validated_uses_are_ready_with_external_overlap_visible(tmp_path):
    from brain.v5.models import SkillReadinessReportRecord
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_readiness import assess_skill_readiness, record_skill_readiness_report

    ws, candidate_ref, _candidate_record = _candidate(tmp_path)
    report = assess_skill_readiness(ws, candidate_ref)

    assert report.status == "ready"
    assert report.independent_use_count == 2
    assert report.ready_for_package_preview is True
    assert report.overlap["classification"] == "extension_candidate"
    assert any(match["source_kind"] == "external_domain_skill" for match in report.overlap["matches"])
    assert report.failure_coverage["status"] == "covered"
    assert report.validation_fixture_refs == ["tests/chi0-smoke.json"]
    assert report.can_install_skill is False
    assert report.can_update_claim_trust is False

    write = record_skill_readiness_report(ws, report, actor=_actor())
    stored = RecordRepository(ws, actor=_actor()).read(write.record_ref).record
    assert isinstance(stored, SkillReadinessReportRecord)
    assert stored.candidate_ref == vars(candidate_ref)
    assert RecordRepository(ws, actor=_actor()).list("trust_updates").records == ()


def test_duplicate_retries_do_not_satisfy_default_readiness(tmp_path):
    from brain.v5.skill_distillation_records import (
        build_skill_distillation_candidate,
        record_skill_distillation_candidate,
    )
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.skill_readiness import assess_skill_readiness
    from tests.test_v5_skill_distillation_records import _request

    ws, request = _request(tmp_path, duplicate_retry=True)
    candidate = build_skill_distillation_candidate(ws, request)
    write = record_skill_distillation_candidate(ws, candidate, actor=_actor())
    candidate_ref = PinnedRecordRef(write.record_ref, write.content_hash, write.revision)

    report = assess_skill_readiness(ws, candidate_ref)

    assert report.status == "blocked"
    assert report.independent_use_count == 1
    assert "insufficient_independent_uses" in report.blockers
    assert report.ready_for_package_preview is False


def test_single_narrow_use_requires_exact_host_attested_exception(
    tmp_path,
    monkeypatch,
):
    from brain.v5.skill_readiness import assess_skill_readiness

    ws, candidate_ref, _candidate_record = _candidate(tmp_path, single_use=True)
    blocked = assess_skill_readiness(ws, candidate_ref)
    exception_ref = _expert_exception(ws, candidate_ref, monkeypatch)
    excepted = assess_skill_readiness(
        ws,
        candidate_ref,
        expert_exception_ref=exception_ref,
    )

    assert blocked.status == "blocked"
    assert "insufficient_independent_uses" in blocked.blockers
    assert excepted.status == "ready"
    assert excepted.expert_exception_ref == vars(exception_ref)
    assert excepted.readiness_basis == "single_narrow_use_with_expert_exception"
    assert excepted.can_update_claim_trust is False


def test_justified_none_known_failure_boundary_is_explicit(tmp_path):
    from brain.v5.skill_readiness import assess_skill_readiness

    ws, candidate_ref, _candidate_record = _candidate(tmp_path, no_known_failures=True)
    report = assess_skill_readiness(ws, candidate_ref)

    assert report.status == "ready"
    assert report.failure_coverage["status"] == "none_known_justified"
    assert "reassess" in report.failure_coverage["boundary"].lower()


def test_installed_exact_signature_is_a_blocking_duplicate(tmp_path):
    from brain.v5.skill_readiness import assess_skill_readiness

    ws, candidate_ref, candidate = _candidate(tmp_path)
    manifest = ws.base / ".agents" / "skills" / "aitp-generated" / "existing" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {
                "skill_id": "aitp-generated/existing",
                "name": "existing",
                "workflow_signature": candidate.workflow_signature,
                "package_hash": "c" * 64,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    report = assess_skill_readiness(ws, candidate_ref)

    assert report.status == "blocked"
    assert report.overlap["classification"] == "duplicate"
    assert "duplicate_skill" in report.blockers
    assert report.overlap["matches"][0]["manifest_path"] == str(manifest)


def test_readiness_contract_rejects_trust_or_install_authority(tmp_path):
    from brain.v5.skill_readiness import assess_skill_readiness
    from brain.v5.skill_readiness_contracts import validate_skill_readiness_report

    ws, candidate_ref, _candidate_record = _candidate(tmp_path)
    report = assess_skill_readiness(ws, candidate_ref)
    payload = vars(report) | {"can_install_skill": True, "can_update_claim_trust": True}

    result = validate_skill_readiness_report(payload)

    assert result.ok is False
    assert any(issue.path.endswith("can_install_skill") for issue in result.issues)
    assert any(issue.path.endswith("can_update_claim_trust") for issue in result.issues)


def test_readiness_writer_rejects_a_shape_valid_forged_ready_report(tmp_path):
    from brain.v5.skill_readiness import assess_skill_readiness, record_skill_readiness_report

    ws, candidate_ref, _candidate_record = _candidate(tmp_path, single_use=True)
    blocked = assess_skill_readiness(ws, candidate_ref)
    forged = replace(
        blocked,
        status="ready",
        blockers=[],
        required_actions=[],
        ready_for_package_preview=True,
    )

    with pytest.raises(ValueError, match="current assessment"):
        record_skill_readiness_report(ws, forged, actor=_actor())
