from __future__ import annotations

import json

import pytest


def test_reviewed_rollback_restores_exact_prior_package_bytes(tmp_path, monkeypatch):
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.skill_install_transactions import (
        apply_skill_install_plan,
        build_skill_install_plan,
        build_skill_rollback_plan,
    )
    from tests.test_v5_project_skill_install import _actor, _checkpoint, _proposal

    ws, old_proposal_ref, _old_artifact_ref, old_preview = _proposal(
        tmp_path,
        semantic_version="0.1.0",
    )
    old_plan = build_skill_install_plan(
        ws,
        old_proposal_ref,
        target_root=ws.base,
        hosts=["codex"],
        actor=_actor(),
    )
    old_plan_ref = pin_current_record(ws, f"skill_install_plan:{old_plan.plan_id}")
    apply_skill_install_plan(
        ws,
        old_plan_ref,
        _checkpoint(ws, old_plan_ref, monkeypatch),
        actor=_actor(),
    )

    _ws, new_proposal_ref, _new_artifact_ref, new_preview = _proposal(
        tmp_path,
        semantic_version="0.2.0",
    )
    new_plan = build_skill_install_plan(
        ws,
        new_proposal_ref,
        target_root=ws.base,
        hosts=["codex"],
        actor=_actor(),
    )
    new_plan_ref = pin_current_record(ws, f"skill_install_plan:{new_plan.plan_id}")
    apply_skill_install_plan(
        ws,
        new_plan_ref,
        _checkpoint(ws, new_plan_ref, monkeypatch),
        actor=_actor(),
    )

    rollback = build_skill_rollback_plan(
        ws,
        old_proposal_ref,
        target_root=ws.base,
        hosts=["codex"],
        expected_current_package_hash=new_preview.package_hash,
        actor=_actor(),
    )
    rollback_ref = pin_current_record(ws, f"skill_install_plan:{rollback.plan_id}")
    applied = apply_skill_install_plan(
        ws,
        rollback_ref,
        _checkpoint(ws, rollback_ref, monkeypatch),
        actor=_actor(),
    )
    target = __import__("pathlib").Path(rollback.target_path)

    assert applied.record.operation == "rollback"
    assert {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file()
    } == old_preview.files


def test_failed_upgrade_receipt_restores_exact_previous_version(tmp_path, monkeypatch):
    from brain.v5.checkpoint_transactions import CheckpointApplicationFailed
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_install_transactions import apply_skill_install_plan, build_skill_install_plan
    from tests.test_v5_project_skill_install import _actor, _checkpoint, _proposal

    ws, old_proposal_ref, _old_artifact_ref, old_preview = _proposal(
        tmp_path, semantic_version="0.1.0"
    )
    old_plan = build_skill_install_plan(
        ws, old_proposal_ref, target_root=ws.base, hosts=["codex"], actor=_actor()
    )
    old_plan_ref = pin_current_record(ws, f"skill_install_plan:{old_plan.plan_id}")
    apply_skill_install_plan(
        ws, old_plan_ref, _checkpoint(ws, old_plan_ref, monkeypatch), actor=_actor()
    )

    _ws, new_proposal_ref, _new_artifact_ref, _new_preview = _proposal(
        tmp_path, semantic_version="0.2.0"
    )
    new_plan = build_skill_install_plan(
        ws, new_proposal_ref, target_root=ws.base, hosts=["codex"], actor=_actor()
    )
    new_plan_ref = pin_current_record(ws, f"skill_install_plan:{new_plan.plan_id}")
    checkpoint = _checkpoint(ws, new_plan_ref, monkeypatch)
    original_write = RecordRepository.write

    def fail_upgrade_receipt(self, family, *args, **kwargs):
        if family == "skill_install_receipts":
            raise OSError("simulated upgrade receipt failure")
        return original_write(self, family, *args, **kwargs)

    monkeypatch.setattr(RecordRepository, "write", fail_upgrade_receipt)
    with pytest.raises(CheckpointApplicationFailed):
        apply_skill_install_plan(ws, new_plan_ref, checkpoint, actor=_actor())

    target = __import__("pathlib").Path(new_plan.target_path)
    assert {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file()
    } == old_preview.files
    journals = list((ws.root / "runtime" / "skill_install_transactions").glob("*.json"))
    assert "compensated" in {
        json.loads(path.read_text(encoding="utf-8"))["status"] for path in journals
    }


def test_prepared_upgrade_recovery_preserves_current_installed_version(tmp_path, monkeypatch):
    import brain.v5.skill_install_materialization as materialization
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.skill_install_transactions import (
        apply_skill_install_plan,
        build_skill_install_plan,
        recover_skill_install_intent,
    )
    from tests.test_v5_project_skill_install import _actor, _checkpoint, _proposal

    ws, old_proposal_ref, _old_artifact_ref, old_preview = _proposal(
        tmp_path, semantic_version="0.1.0"
    )
    old_plan = build_skill_install_plan(
        ws, old_proposal_ref, target_root=ws.base, hosts=["codex"], actor=_actor()
    )
    old_ref = pin_current_record(ws, f"skill_install_plan:{old_plan.plan_id}")
    apply_skill_install_plan(ws, old_ref, _checkpoint(ws, old_ref, monkeypatch), actor=_actor())

    _ws, new_proposal_ref, _new_artifact_ref, _new_preview = _proposal(
        tmp_path, semantic_version="0.2.0"
    )
    new_plan = build_skill_install_plan(
        ws, new_proposal_ref, target_root=ws.base, hosts=["codex"], actor=_actor()
    )
    new_ref = pin_current_record(ws, f"skill_install_plan:{new_plan.plan_id}")
    checkpoint = _checkpoint(ws, new_ref, monkeypatch)
    monkeypatch.setattr(
        materialization,
        "_materialize_stage",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            KeyboardInterrupt("interrupt prepared upgrade")
        ),
    )
    with pytest.raises(KeyboardInterrupt):
        apply_skill_install_plan(ws, new_ref, checkpoint, actor=_actor())

    journal_path = next(
        path
        for path in (ws.root / "runtime" / "skill_install_transactions").glob("*.json")
        if json.loads(path.read_text(encoding="utf-8"))["status"] == "prepared"
    )
    recovered = recover_skill_install_intent(ws, journal_path.stem)
    target = __import__("pathlib").Path(new_plan.target_path)

    assert recovered["status"] == "compensated"
    assert {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file()
    } == old_preview.files
