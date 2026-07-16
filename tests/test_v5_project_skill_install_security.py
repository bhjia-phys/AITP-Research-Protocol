from __future__ import annotations

from dataclasses import replace
import json
import os

import pytest


def _installed_old_version(tmp_path, monkeypatch):
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.skill_install_transactions import (
        apply_skill_install_plan,
        build_skill_install_plan,
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
    old_ref = pin_current_record(ws, f"skill_install_plan:{old_plan.plan_id}")
    apply_skill_install_plan(
        ws,
        old_ref,
        _checkpoint(ws, old_ref, monkeypatch),
        actor=_actor(),
    )
    return ws, old_proposal_ref, old_preview


def test_upgrade_and_reinstall_require_overwrite_checkpoint_action(tmp_path, monkeypatch):
    from brain.v5.skill_install_transactions import build_skill_install_plan
    from tests.test_v5_project_skill_install import _actor, _proposal

    ws, old_proposal_ref, _old_preview = _installed_old_version(tmp_path, monkeypatch)
    reinstall = build_skill_install_plan(
        ws,
        old_proposal_ref,
        target_root=ws.base,
        hosts=["codex"],
        actor=_actor(),
    )
    _ws, new_proposal_ref, _artifact_ref, _preview = _proposal(
        tmp_path,
        semantic_version="0.2.0",
    )
    upgrade = build_skill_install_plan(
        ws,
        new_proposal_ref,
        target_root=ws.base,
        hosts=["codex"],
        actor=_actor(),
    )

    assert reinstall.operation == "reinstall"
    assert reinstall.checkpoint_action == "overwrite_aitp_skill"
    assert upgrade.operation == "upgrade"
    assert upgrade.checkpoint_action == "overwrite_aitp_skill"


def test_load_plan_rejects_identity_that_disagrees_with_pinned_proposal(tmp_path):
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_install_planning import load_plan
    from brain.v5.skill_install_transactions import build_skill_install_plan
    from tests.test_v5_project_skill_install import _actor, _proposal

    ws, proposal_ref, _artifact_ref, _preview = _proposal(tmp_path)
    plan = build_skill_install_plan(
        ws,
        proposal_ref,
        target_root=ws.base,
        hosts=["codex"],
        actor=_actor(),
    )
    forged_id = "skill-install-plan-" + "f" * 64
    forged_payload = {**plan.action_payload, "plan_id": forged_id}
    forged = replace(
        plan,
        plan_id=forged_id,
        name="forged-unrelated-name",
        action_payload=forged_payload,
    )
    RecordRepository(ws, actor=_actor()).write(
        "skill_install_plans",
        forged,
        body="# Forged Plan\n",
    )
    forged_ref = pin_current_record(ws, f"skill_install_plan:{forged_id}")

    with pytest.raises(ValueError, match="proposal|derived identity"):
        load_plan(ws, forged_ref)


def test_load_plan_rejects_forged_validation_policy_derivation(tmp_path):
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_install_planning import load_plan
    from brain.v5.skill_install_transactions import build_skill_install_plan
    from tests.test_v5_project_skill_install import _actor, _proposal

    ws, proposal_ref, _artifact_ref, _preview = _proposal(tmp_path)
    plan = build_skill_install_plan(
        ws,
        proposal_ref,
        target_root=ws.base,
        hosts=["codex"],
        actor=_actor(),
    )
    forged_id = "skill-install-plan-" + "e" * 64
    forged_hash = "d" * 64
    forged = replace(
        plan,
        plan_id=forged_id,
        validation_policy_hash=forged_hash,
        action_payload={
            **plan.action_payload,
            "plan_id": forged_id,
            "validation_policy_hash": forged_hash,
        },
    )
    RecordRepository(ws, actor=_actor()).write(
        "skill_install_plans",
        forged,
        body="# Forged Validation Policy Plan\n",
    )
    forged_ref = pin_current_record(ws, f"skill_install_plan:{forged_id}")

    with pytest.raises(ValueError, match="validation policy derivation"):
        load_plan(ws, forged_ref)


def test_load_plan_rejects_install_action_for_existing_managed_target(tmp_path, monkeypatch):
    from dataclasses import asdict

    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_install_plan_derivations import (
        diff_projection_for,
        plan_id_for,
        plan_identity_for,
    )
    from brain.v5.skill_install_planning import coerce_pin, load_plan
    from brain.v5.skill_install_transactions import build_skill_install_plan
    from tests.test_v5_project_skill_install import _actor, _proposal

    ws, _old_proposal_ref, _old_preview = _installed_old_version(tmp_path, monkeypatch)
    _ws, new_proposal_ref, _artifact_ref, _preview = _proposal(
        tmp_path,
        semantic_version="0.2.0",
    )
    upgrade = build_skill_install_plan(
        ws,
        new_proposal_ref,
        target_root=ws.base,
        hosts=["codex"],
        actor=_actor(),
    )
    projection = diff_projection_for(
        operation="install",
        skill_id=upgrade.skill_id,
        semantic_version=upgrade.semantic_version,
        package_hash=upgrade.package_hash,
        tree_hash=upgrade.tree_hash,
        target_root=upgrade.target_root,
        target_path=upgrade.target_path,
        hosts=upgrade.hosts,
        before_hash=upgrade.expected_before_hash,
        after_hash=upgrade.expected_after_hash,
        existing_skill_id=upgrade.existing_skill_id,
        existing_semantic_version=upgrade.existing_semantic_version,
        existing_package_hash=upgrade.existing_package_hash,
        validation_policy_hash=upgrade.validation_policy_hash,
    )
    identity = plan_identity_for(
        projection,
        coerce_pin(upgrade.proposal_ref),
        coerce_pin(upgrade.package_artifact_ref),
    )
    forged_id = plan_id_for(identity)
    forged = replace(
        upgrade,
        plan_id=forged_id,
        operation="install",
        checkpoint_action="install_aitp_skill",
        diff_hash=identity["diff_hash"],
        action_payload={
            **upgrade.action_payload,
            "plan_id": forged_id,
            "operation": "install",
            "diff_hash": identity["diff_hash"],
        },
    )
    RecordRepository(ws, actor=_actor()).write(
        "skill_install_plans",
        forged,
        body="# Forged Install Operation\n",
    )
    forged_ref = pin_current_record(ws, f"skill_install_plan:{forged_id}")

    with pytest.raises(ValueError, match="operation|before-image"):
        load_plan(ws, forged_ref)
    assert forged.proposal_ref == asdict(coerce_pin(new_proposal_ref))


def test_staging_is_confined_to_aitp_runtime_not_target_parent(tmp_path, monkeypatch):
    import brain.v5.skill_install_materialization as materialization
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.skill_install_transactions import (
        apply_skill_install_plan,
        build_skill_install_plan,
    )
    from tests.test_v5_project_skill_install import _actor, _checkpoint, _proposal

    ws, proposal_ref, _artifact_ref, _preview = _proposal(tmp_path)
    plan = build_skill_install_plan(
        ws,
        proposal_ref,
        target_root=ws.base,
        hosts=["codex"],
        actor=_actor(),
    )
    plan_ref = pin_current_record(ws, f"skill_install_plan:{plan.plan_id}")
    checkpoint = _checkpoint(ws, plan_ref, monkeypatch)
    observed = []

    def capture_stage(stage, _files):
        observed.append(stage)
        raise KeyboardInterrupt("stop after observing deterministic stage path")

    monkeypatch.setattr(materialization, "_materialize_stage", capture_stage)
    with pytest.raises(KeyboardInterrupt):
        apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())

    assert len(observed) == 1
    observed[0].relative_to(ws.root / "runtime" / "skill_install_staging")
    assert observed[0].parent != __import__("pathlib").Path(plan.target_path).parent


@pytest.mark.skipif(os.name != "nt", reason="Windows delete-share contract")
def test_windows_nested_stage_parent_is_pinned_during_file_creation(tmp_path, monkeypatch):
    import brain.v5.skill_install_host_safety as host_safety

    stage = tmp_path / "runtime" / "stage"
    stage.parent.mkdir(parents=True)
    target_file = stage / "tests" / "case.json"
    original_open = host_safety.os.open
    attempted = False

    def assert_nested_parent_pinned(path, flags, *args, **kwargs):
        nonlocal attempted
        if __import__("pathlib").Path(path) == target_file and flags & os.O_CREAT:
            import ctypes
            from ctypes import wintypes

            attempted = True
            nested = target_file.parent
            moved = stage / "tests-moved"
            try:
                nested.rename(moved)
            except OSError:
                pass
            else:
                moved.rename(nested)
                pytest.fail("nested staging parent was renameable during file creation")
            create_file = ctypes.windll.kernel32.CreateFileW
            create_file.restype = wintypes.HANDLE
            write_handle = create_file(
                str(nested),
                0x40000000,
                0x00000001 | 0x00000002 | 0x00000004,
                None,
                3,
                0x02000000 | 0x00200000,
                None,
            )
            if write_handle != wintypes.HANDLE(-1).value:
                ctypes.windll.kernel32.CloseHandle(write_handle)
                pytest.fail("nested staging parent allowed a competing write handle")
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(host_safety.os, "open", assert_nested_parent_pinned)
    host_safety.materialize_stage(stage, {"tests/case.json": b"{}\n"})

    assert attempted is True
    assert target_file.read_bytes() == b"{}\n"


@pytest.mark.parametrize("case", ["rejected", "expired", "wrong_subject", "wrong_target"])
def test_invalid_checkpoint_matrix_never_creates_host_transaction(
    tmp_path,
    monkeypatch,
    case,
):
    from datetime import UTC, datetime, timedelta

    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.skill_install_transactions import (
        apply_skill_install_plan,
        build_skill_install_plan,
    )
    from tests.test_v5_project_skill_install import _actor, _checkpoint, _proposal

    ws, proposal_ref, _artifact_ref, preview = _proposal(tmp_path)
    plan = build_skill_install_plan(
        ws,
        proposal_ref,
        target_root=ws.base,
        hosts=["codex"],
        actor=_actor(),
    )
    plan_ref = pin_current_record(ws, f"skill_install_plan:{plan.plan_id}")
    options = {}
    apply_now = None
    if case == "rejected":
        options["decision"] = "reject"
    elif case == "expired":
        apply_now = datetime.now(UTC) + timedelta(hours=1)
    elif case == "wrong_subject":
        options["subject_refs"] = [proposal_ref]
    else:
        options["target_scope_refs"] = [
            plan_ref.record_ref,
            f"project-root:{ws.base}",
            f"project-skill-path:{ws.base / 'wrong-target'}",
        ]
    checkpoint = _checkpoint(ws, plan_ref, monkeypatch, **options)

    with pytest.raises(ValueError):
        apply_skill_install_plan(
            ws,
            plan_ref,
            checkpoint,
            actor=_actor(),
            now=apply_now,
        )

    target = ws.base / ".agents" / "skills" / "aitp-generated" / preview.name
    assert not target.exists()
    assert not (ws.root / "runtime" / "skill_install_transactions").exists()


def test_concurrent_target_change_after_staging_is_preserved(tmp_path, monkeypatch):
    import brain.v5.skill_install_materialization as materialization
    from brain.v5.checkpoint_transactions import CheckpointApplicationFailed
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.skill_install_transactions import (
        apply_skill_install_plan,
        build_skill_install_plan,
    )
    from tests.test_v5_project_skill_install import _actor, _checkpoint, _proposal

    ws, _old_proposal_ref, _old_preview = _installed_old_version(tmp_path, monkeypatch)
    _ws, new_proposal_ref, _artifact_ref, _preview = _proposal(
        tmp_path,
        semantic_version="0.2.0",
    )
    plan = build_skill_install_plan(
        ws,
        new_proposal_ref,
        target_root=ws.base,
        hosts=["codex"],
        actor=_actor(),
    )
    plan_ref = pin_current_record(ws, f"skill_install_plan:{plan.plan_id}")
    checkpoint = _checkpoint(ws, plan_ref, monkeypatch)
    target = __import__("pathlib").Path(plan.target_path)
    marker = target / "concurrent.txt"
    original_stage = materialization._materialize_stage

    def stage_then_change_target(stage, files):
        original_stage(stage, files)
        marker.write_bytes(b"external concurrent write\n")

    monkeypatch.setattr(materialization, "_materialize_stage", stage_then_change_target)
    with pytest.raises(CheckpointApplicationFailed):
        apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())

    assert marker.read_bytes() == b"external concurrent write\n"
    assert json.loads((target / "manifest.json").read_text(encoding="utf-8"))[
        "semantic_version"
    ] == "0.1.0"


def test_corrupt_backup_never_causes_verified_after_image_deletion(tmp_path, monkeypatch):
    from brain.v5.checkpoint_transactions import CheckpointApplicationFailed
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.skill_install_transactions import (
        apply_skill_install_plan,
        build_skill_install_plan,
    )
    from tests.test_v5_project_skill_install import _actor, _checkpoint, _proposal

    ws, _old_proposal_ref, _old_preview = _installed_old_version(tmp_path, monkeypatch)
    _ws, new_proposal_ref, _artifact_ref, new_preview = _proposal(
        tmp_path,
        semantic_version="0.2.0",
    )
    plan = build_skill_install_plan(
        ws,
        new_proposal_ref,
        target_root=ws.base,
        hosts=["codex"],
        actor=_actor(),
    )
    plan_ref = pin_current_record(ws, f"skill_install_plan:{plan.plan_id}")
    checkpoint = _checkpoint(ws, plan_ref, monkeypatch)
    original_write = RecordRepository.write

    def corrupt_backup_then_fail(self, family, *args, **kwargs):
        if family == "skill_install_receipts":
            backup = next(__import__("pathlib").Path(plan.target_path).parent.glob(".*.aitp-backup-*"))
            (backup / "SKILL.md").write_bytes(b"corrupt before image\n")
            raise OSError("simulated receipt failure after backup corruption")
        return original_write(self, family, *args, **kwargs)

    monkeypatch.setattr(RecordRepository, "write", corrupt_backup_then_fail)
    with pytest.raises(CheckpointApplicationFailed):
        apply_skill_install_plan(ws, plan_ref, checkpoint, actor=_actor())

    target = __import__("pathlib").Path(plan.target_path)
    assert {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file()
    } == new_preview.files
    states = {
        json.loads(path.read_text(encoding="utf-8"))["status"]
        for path in (ws.root / "runtime" / "skill_install_transactions").glob("*.json")
    }
    assert "recovery_required" in states
