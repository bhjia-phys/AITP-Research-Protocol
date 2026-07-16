from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="project-skill-install-test", host="pytest")


def _proposal(tmp_path, *, semantic_version="0.1.0"):
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.project_skill_packages import record_skill_proposal
    from brain.v5.skill_package_artifacts import record_skill_package_artifact
    from tests.test_v5_project_skill_packages import _preview

    ws, _candidate_ref, _readiness_ref, _candidate, preview = _preview(
        tmp_path,
        semantic_version=semantic_version,
    )
    artifact_write = record_skill_package_artifact(ws, preview, actor=_actor())
    proposal_write = record_skill_proposal(ws, preview, actor=_actor())
    return (
        ws,
        PinnedRecordRef(
            proposal_write.record_ref,
            proposal_write.content_hash,
            proposal_write.revision,
        ),
        PinnedRecordRef(
            artifact_write.record_ref,
            artifact_write.content_hash,
            artifact_write.revision,
        ),
        preview,
    )


def _approval_receipt(
    *,
    secret: bytes,
    checkpoint_id: str,
    request_hash: str,
    rationale: str,
    decision: str = "approve",
):
    now = datetime.now(UTC)
    payload = {
        "version": "v1",
        "checkpoint_id": checkpoint_id,
        "checkpoint_content_hash": request_hash,
        "decision": decision,
        "rationale_hash": hashlib.sha256(rationale.encode("utf-8")).hexdigest(),
        "decided_by": "samur",
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=5)).isoformat(),
        "nonce": f"skill-install-{checkpoint_id}",
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {**payload, "signature": hmac.new(secret, encoded, hashlib.sha256).hexdigest()}


def _checkpoint(
    ws,
    plan_ref,
    monkeypatch,
    *,
    decide=True,
    action_payload=None,
    decision="approve",
    subject_refs=None,
    target_scope_refs=None,
):
    from brain.v5.checkpoint_bindings import decide_bound_checkpoint, request_bound_checkpoint
    from brain.v5.skill_install_transactions import skill_install_checkpoint_request

    now = datetime.now(UTC)
    request = skill_install_checkpoint_request(ws, plan_ref)
    requested = request_bound_checkpoint(
        ws,
        topic_id="librpa",
        claim_id=plan_ref.record_ref.partition(":")[2],
        reason="Review this exact project-local Skill deployment plan.",
        requested_by="project-skill-install-test",
        action=request["action"],
        action_payload=action_payload or request["action_payload"],
        intent_ref=plan_ref,
        subject_refs=subject_refs or request["subject_refs"],
        options=["approve", "reject"],
        expires_at=(now + timedelta(minutes=10)).isoformat(),
        replay_policy="exact_idempotent",
        target_scope_refs=target_scope_refs or request["target_scope_refs"],
        effect_policy=request["effect_policy"],
        actor=_actor(),
        now=now,
    )
    if not decide:
        return {"request_ref": requested.request_ref, "decision_ref": requested.request_ref}
    secret = b"project-skill-install-test-secret-32-bytes"
    monkeypatch.setenv(
        "AITP_HUMAN_APPROVAL_HMAC_KEY_B64",
        base64.b64encode(secret).decode("ascii"),
    )
    rationale = "Reviewed the exact package, target, diff, and validator policy."
    try:
        decided = decide_bound_checkpoint(
            ws,
            request_ref=requested.request_ref,
            expected=requested.binding,
            decision=decision,
            rationale=rationale,
            decided_by="samur",
            approval_receipt=_approval_receipt(
                secret=secret,
                checkpoint_id=requested.record.checkpoint_id,
                request_hash=requested.request_ref.content_hash,
                rationale=rationale,
                decision=decision,
            ),
            now=now,
        )
    except ValueError:
        if decision == "approve":
            raise
        from brain.v5.pinned_record_refs import pin_current_record

        return {
            "request_ref": requested.request_ref,
            "decision_ref": pin_current_record(ws, requested.request_ref.record_ref),
        }
    return {"request_ref": decided.request_ref, "decision_ref": decided.decision_ref}


def _plan(ws, proposal_ref):
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.skill_install_transactions import build_skill_install_plan

    plan = build_skill_install_plan(
        ws,
        proposal_ref,
        target_root=ws.base,
        hosts=["codex"],
        actor=_actor(),
    )
    return plan, pin_current_record(ws, f"skill_install_plan:{plan.plan_id}")


def test_pending_checkpoint_leaves_target_and_transaction_state_absent(tmp_path, monkeypatch):
    from brain.v5.skill_install_transactions import apply_skill_install_plan

    ws, proposal_ref, _artifact_ref, preview = _proposal(tmp_path)
    plan, plan_ref = _plan(ws, proposal_ref)
    checkpoint = _checkpoint(ws, plan_ref, monkeypatch, decide=False)
    target = ws.base / ".agents" / "skills" / "aitp-generated" / preview.name

    with pytest.raises(ValueError, match="approved decision"):
        apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())

    assert not target.exists()
    assert not (ws.root / "runtime" / "skill_install_transactions").exists()


def test_wrong_hash_bound_checkpoint_leaves_every_target_byte_unchanged(tmp_path, monkeypatch):
    from brain.v5.skill_install_transactions import apply_skill_install_plan

    ws, proposal_ref, _artifact_ref, preview = _proposal(tmp_path)
    _plan_record, plan_ref = _plan(ws, proposal_ref)
    wrong_payload = {
        **__import__(
            "brain.v5.skill_install_transactions",
            fromlist=["skill_install_checkpoint_request"],
        ).skill_install_checkpoint_request(ws, plan_ref)["action_payload"],
        "package_hash": "f" * 64,
    }
    checkpoint = _checkpoint(
        ws,
        plan_ref,
        monkeypatch,
        action_payload=wrong_payload,
    )
    target = ws.base / ".agents" / "skills" / "aitp-generated" / preview.name

    with pytest.raises(ValueError, match="payload"):
        apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())

    assert not target.exists()


def test_approved_install_is_exact_project_local_and_idempotent(tmp_path, monkeypatch):
    from brain.v5.models import SkillInstallReceiptRecord
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_install_transactions import apply_skill_install_plan

    ws, proposal_ref, _artifact_ref, preview = _proposal(tmp_path)
    plan, plan_ref = _plan(ws, proposal_ref)
    checkpoint = _checkpoint(ws, plan_ref, monkeypatch)

    first = apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())
    second = apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())
    target = ws.base / ".agents" / "skills" / "aitp-generated" / preview.name

    assert first.receipt_ref == second.receipt_ref
    assert second.replayed is True
    assert target == __import__("pathlib").Path(plan.target_path)
    assert {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file()
    } == preview.files
    stored = RecordRepository(ws, actor=_actor()).read(first.receipt_ref.record_ref).record
    assert isinstance(stored, SkillInstallReceiptRecord)
    assert stored.status == "completed"
    assert stored.package_hash == preview.package_hash
    assert stored.can_update_claim_trust is False


def test_direct_domain_shim_apply_is_checkpoint_required_and_writes_nothing(tmp_path):
    from brain.v5.domain_skill_shims import build_domain_skill_shim_manifest
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    result = build_domain_skill_shim_manifest(ws, apply=True, overwrite=True)

    assert result["state_effect"] == "checkpoint_required"
    assert result["write_count"] == 0
    assert result["writes_project_files"] is False
    assert not (ws.base / ".agents" / "skills").exists()


def test_receipt_write_failure_restores_absent_before_image(tmp_path, monkeypatch):
    from brain.v5.checkpoint_transactions import CheckpointApplicationFailed
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_install_transactions import apply_skill_install_plan

    ws, proposal_ref, _artifact_ref, preview = _proposal(tmp_path)
    _plan_record, plan_ref = _plan(ws, proposal_ref)
    checkpoint = _checkpoint(ws, plan_ref, monkeypatch)
    original_write = RecordRepository.write

    def fail_install_receipt(self, family, *args, **kwargs):
        if family == "skill_install_receipts":
            raise OSError("simulated install receipt persistence failure")
        return original_write(self, family, *args, **kwargs)

    monkeypatch.setattr(RecordRepository, "write", fail_install_receipt)

    with pytest.raises(CheckpointApplicationFailed):
        apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())

    target = ws.base / ".agents" / "skills" / "aitp-generated" / preview.name
    assert not target.exists()
    journals = list((ws.root / "runtime" / "skill_install_transactions").glob("*.json"))
    assert len(journals) == 1
    assert json.loads(journals[0].read_text(encoding="utf-8"))["status"] == "compensated"


def test_post_approval_target_mutation_is_not_overwritten(tmp_path, monkeypatch):
    from brain.v5.checkpoint_transactions import CheckpointApplicationFailed
    from brain.v5.skill_install_transactions import apply_skill_install_plan

    ws, proposal_ref, _artifact_ref, preview = _proposal(tmp_path)
    _plan_record, plan_ref = _plan(ws, proposal_ref)
    checkpoint = _checkpoint(ws, plan_ref, monkeypatch)
    target = ws.base / ".agents" / "skills" / "aitp-generated" / preview.name
    target.mkdir(parents=True)
    marker = target / "external.txt"
    marker.write_bytes(b"do not overwrite\n")

    with pytest.raises(CheckpointApplicationFailed):
        apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())

    assert marker.read_bytes() == b"do not overwrite\n"
    assert set(target.iterdir()) == {marker}


def test_existing_external_skill_target_cannot_be_planned_for_overwrite(tmp_path):
    from brain.v5.skill_install_transactions import build_skill_install_plan

    ws, proposal_ref, _artifact_ref, preview = _proposal(tmp_path)
    target = ws.base / ".agents" / "skills" / "aitp-generated" / preview.name
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text("external content\n", encoding="utf-8")

    with pytest.raises(ValueError, match="not a managed AITP package"):
        build_skill_install_plan(
            ws,
            proposal_ref,
            target_root=ws.base,
            hosts=["codex"],
            actor=_actor(),
        )


def test_managed_skill_tamper_is_detected_before_reinstall_plan(tmp_path, monkeypatch):
    from brain.v5.skill_install_transactions import apply_skill_install_plan, build_skill_install_plan

    ws, proposal_ref, _artifact_ref, preview = _proposal(tmp_path)
    _plan_record, plan_ref = _plan(ws, proposal_ref)
    apply_skill_install_plan(
        ws,
        plan_ref,
        _checkpoint(ws, plan_ref, monkeypatch),
        actor=_actor(),
    )
    target = ws.base / ".agents" / "skills" / "aitp-generated" / preview.name
    (target / "SKILL.md").write_text("tampered\n", encoding="utf-8")

    with pytest.raises(ValueError, match="does not match its manifest"):
        build_skill_install_plan(
            ws,
            proposal_ref,
            target_root=ws.base,
            hosts=["codex"],
            actor=_actor(),
        )


def test_user_global_and_link_like_project_roots_are_rejected(tmp_path, monkeypatch):
    import brain.v5.skill_install_planning as planning
    import brain.v5.skill_install_transactions as transactions

    ws, proposal_ref, _artifact_ref, _preview_record = _proposal(tmp_path)
    with pytest.raises(ValueError, match="user-global"):
        transactions.build_skill_install_plan(
            ws,
            proposal_ref,
            target_root=__import__("pathlib").Path.home(),
            hosts=["codex"],
            actor=_actor(),
        )

    original = planning.link_like
    monkeypatch.setattr(
        planning,
        "link_like",
        lambda path: True if path == ws.base.resolve() else original(path),
    )
    with pytest.raises(ValueError, match="link or junction"):
        transactions.build_skill_install_plan(
            ws,
            proposal_ref,
            target_root=ws.base,
            hosts=["codex"],
            actor=_actor(),
        )


def test_legacy_one_file_apply_is_disabled_even_with_ids(tmp_path):
    from brain.v5.skill_candidates import apply_project_skill
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    with pytest.raises(ValueError, match="checkpoint_required"):
        apply_project_skill(ws, proposal_id="legacy", checkpoint_id="legacy")
    assert not (ws.base / ".agents" / "skills").exists()


def test_materialized_interrupt_resumes_without_replacing_changed_bytes(tmp_path, monkeypatch):
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_install_transactions import (
        apply_skill_install_plan,
        resume_skill_install_intent,
    )

    ws, proposal_ref, _artifact_ref, preview = _proposal(tmp_path)
    _plan_record, plan_ref = _plan(ws, proposal_ref)
    checkpoint = _checkpoint(ws, plan_ref, monkeypatch)
    original_write = RecordRepository.write
    interrupted = False

    def interrupt_before_receipt(self, family, *args, **kwargs):
        nonlocal interrupted
        if family == "skill_install_receipts" and not interrupted:
            interrupted = True
            raise KeyboardInterrupt("simulated process interruption")
        return original_write(self, family, *args, **kwargs)

    monkeypatch.setattr(RecordRepository, "write", interrupt_before_receipt)
    with pytest.raises(KeyboardInterrupt, match="process interruption"):
        apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())

    target = ws.base / ".agents" / "skills" / "aitp-generated" / preview.name
    assert target.is_dir()
    journal_path = next((ws.root / "runtime" / "skill_install_transactions").glob("*.json"))
    assert json.loads(journal_path.read_text(encoding="utf-8"))["status"] == "materialized"

    monkeypatch.setattr(RecordRepository, "write", original_write)
    resumed = resume_skill_install_intent(ws, plan_ref, checkpoint, actor=_actor())

    assert resumed.record.status == "completed"
    assert json.loads(journal_path.read_text(encoding="utf-8"))["status"] == "completed"
    assert not list(target.parent.glob(f".{target.name}.aitp-backup-*"))


def test_receipt_write_survives_host_journal_completion_failure(tmp_path, monkeypatch):
    import brain.v5.skill_install_materialization as materialization
    from brain.v5.skill_install_transactions import apply_skill_install_plan

    ws, proposal_ref, _artifact_ref, preview = _proposal(tmp_path)
    _plan_record, plan_ref = _plan(ws, proposal_ref)
    checkpoint = _checkpoint(ws, plan_ref, monkeypatch)
    original_write_journal = materialization.write_journal
    failed_once = False

    def fail_first_completion(path, payload):
        nonlocal failed_once
        if payload.get("status") == "completed" and not failed_once:
            failed_once = True
            raise OSError("simulated host journal completion failure")
        return original_write_journal(path, payload)

    monkeypatch.setattr(materialization, "write_journal", fail_first_completion)
    applied = apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())

    target = ws.base / ".agents" / "skills" / "aitp-generated" / preview.name
    journal_path = next((ws.root / "runtime" / "skill_install_transactions").glob("*.json"))
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    assert failed_once is True
    assert applied.record.status == "completed"
    assert journal["status"] == "completed"
    assert journal["receipt_ref"]["record_ref"] == applied.receipt_ref.record_ref
    assert not list(target.parent.glob(f".{target.name}.aitp-backup-*"))


def test_recovery_compensates_materialized_interrupt_without_receipt(tmp_path, monkeypatch):
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_install_transactions import (
        apply_skill_install_plan,
        recover_skill_install_intent,
    )

    ws, proposal_ref, _artifact_ref, preview = _proposal(tmp_path)
    _plan_record, plan_ref = _plan(ws, proposal_ref)
    checkpoint = _checkpoint(ws, plan_ref, monkeypatch)
    original_write = RecordRepository.write

    def interrupt_before_receipt(self, family, *args, **kwargs):
        if family == "skill_install_receipts":
            raise KeyboardInterrupt("simulated process interruption")
        return original_write(self, family, *args, **kwargs)

    monkeypatch.setattr(RecordRepository, "write", interrupt_before_receipt)
    with pytest.raises(KeyboardInterrupt):
        apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())
    monkeypatch.setattr(RecordRepository, "write", original_write)

    journal_path = next((ws.root / "runtime" / "skill_install_transactions").glob("*.json"))
    recovered = recover_skill_install_intent(ws, journal_path.stem)
    target = ws.base / ".agents" / "skills" / "aitp-generated" / preview.name

    assert recovered["status"] == "compensated"
    assert not target.exists()


def test_resume_rejects_changed_staging_bytes_without_deleting_them(tmp_path, monkeypatch):
    import brain.v5.skill_install_materialization as materialization
    from brain.v5.checkpoint_transactions import CheckpointApplicationFailed
    from brain.v5.skill_install_transactions import (
        apply_skill_install_plan,
        resume_skill_install_intent,
    )

    ws, proposal_ref, _artifact_ref, preview = _proposal(tmp_path)
    _plan_record, plan_ref = _plan(ws, proposal_ref)
    checkpoint = _checkpoint(ws, plan_ref, monkeypatch)
    original_stage = materialization._materialize_stage
    monkeypatch.setattr(
        materialization,
        "_materialize_stage",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            KeyboardInterrupt("interrupt before staging")
        ),
    )
    with pytest.raises(KeyboardInterrupt):
        apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())

    journal_path = next((ws.root / "runtime" / "skill_install_transactions").glob("*.json"))
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    stage = __import__("pathlib").Path(journal["stage_path"])
    stage.mkdir(parents=True)
    marker = stage / "unapproved.txt"
    marker.write_bytes(b"unapproved\n")
    monkeypatch.setattr(materialization, "_materialize_stage", original_stage)

    with pytest.raises(CheckpointApplicationFailed):
        resume_skill_install_intent(ws, plan_ref, checkpoint, actor=_actor())

    target = ws.base / ".agents" / "skills" / "aitp-generated" / preview.name
    assert not target.exists()
    assert marker.read_bytes() == b"unapproved\n"


def test_recovery_rejects_forged_runtime_journal_without_touching_external_path(tmp_path):
    from brain.v5.pinned_record_refs import PinnedRecordMismatchError
    from brain.v5.skill_install_transactions import recover_skill_install_intent
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    external = tmp_path / "external"
    external.mkdir()
    marker = external / "keep.txt"
    marker.write_bytes(b"keep\n")
    application_id = "checkpoint-application-" + "a" * 64
    journal = ws.root / "runtime" / "skill_install_transactions" / f"{application_id}.json"
    journal.parent.mkdir(parents=True)
    journal.write_text(
        json.dumps(
            {
                "version": "v1",
                "application_id": application_id,
                "status": "materialized",
                "plan_ref": {
                    "record_ref": "skill_install_plan:missing",
                    "content_hash": "b" * 64,
                    "revision": 1,
                },
                "request_ref": {},
                "decision_ref": {},
                "target_path": str(external),
                "stage_path": str(tmp_path / "stage"),
                "backup_path": str(tmp_path / "backup"),
                "before_hash": "c" * 64,
                "after_hash": "d" * 64,
                "diff_hash": "e" * 64,
                "started_at": datetime.now(UTC).isoformat(),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    with pytest.raises(PinnedRecordMismatchError):
        recover_skill_install_intent(ws, application_id)

    assert marker.read_bytes() == b"keep\n"
