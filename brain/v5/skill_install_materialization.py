"""Compensating host transaction for exact Skill package materialization."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.markdown import write_text_atomic
from brain.v5.models import SkillInstallPlanRecord, SkillInstallReceiptRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.project_skill_contracts import require_valid_skill_install_receipt
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.skill_install_planning import (
    EMPTY_TREE_HASH,
    coerce_pin,
    files_tree_hash,
    link_like,
    proposal_package,
    snapshot_target,
    target_paths,
)
from brain.v5.skill_install_host_safety import (
    PinnedDirectories,
    cleanup_backup as _cleanup_backup,
    ensure_stage_parent,
    ensure_target_parent,
    materialize_stage as _materialize_stage,
    require_exact_backup,
    revalidate_materialization_boundary,
    stage_path_for,
)
from brain.v5.skill_install_plan_validation import validate_plan_before_image
from brain.v5.skill_validation_execution import (
    classify_skill_validation_policy,
    validate_staged_skill_package,
)


def materialize_plan(
    ws: WorkspacePaths,
    *,
    plan_pin: PinnedRecordRef,
    plan: SkillInstallPlanRecord,
    request_pin: PinnedRecordRef,
    decision_pin: PinnedRecordRef,
    application_id: str,
    actor: RecordActor,
    now: datetime | None,
) -> PinnedRecordRef:
    proposal_pin, proposal, artifact_pin, _artifact, files, _manifest = proposal_package(
        ws, plan.proposal_ref
    )
    if proposal_pin != coerce_pin(plan.proposal_ref) or artifact_pin != coerce_pin(
        plan.package_artifact_ref
    ):
        raise ValueError("Skill install plan package pins changed")
    if proposal.package_hash != plan.package_hash or files_tree_hash(files) != plan.expected_after_hash:
        raise ValueError("Skill install plan package bytes changed after approval")
    policy = classify_skill_validation_policy(plan.validation_commands)
    if policy.command_digest != plan.validation_policy["command_digest"]:
        raise ValueError("Skill install validation command digest changed after approval")
    if plan.validation_policy.get("requires_m2_execution"):
        raise ValueError("Skill install requires a pinned M2 BoundExecutionReceipt")

    target = Path(plan.target_path)
    root, expected_target = target_paths(plan.target_root, plan.name)
    if root != Path(plan.target_root) or expected_target != target:
        raise ValueError("Skill install target binding is invalid")
    journal_path = journal_path_for(ws, application_id)
    stage = stage_path_for(ws, application_id)
    backup = target.parent / f".{target.name}.aitp-backup-{application_id}"
    if journal_path.exists():
        journal = load_journal(journal_path)
        _require_journal_binding(
            journal,
            application_id,
            plan_pin,
            request_pin,
            decision_pin,
            plan,
            stage,
            backup,
        )
    else:
        current_hash, current_manifest = snapshot_target(target)
        if current_hash != plan.expected_before_hash:
            raise ValueError("Skill install target changed after approval")
        validate_plan_before_image(plan, proposal, current_hash, current_manifest)
        if stage.exists() or backup.exists():
            raise ValueError("Skill install staging paths already exist")
        journal = {
            "version": "v1",
            "application_id": application_id,
            "status": "prepared",
            "plan_ref": asdict(plan_pin),
            "request_ref": asdict(request_pin),
            "decision_ref": asdict(decision_pin),
            "target_path": str(target),
            "stage_path": str(stage),
            "backup_path": str(backup),
            "before_hash": plan.expected_before_hash,
            "after_hash": plan.expected_after_hash,
            "diff_hash": plan.diff_hash,
            "started_at": utc(now).isoformat(),
            "completed_at": "",
        }
        write_journal(journal_path, journal)

    if journal["status"] == "prepared":
        current_hash, current_manifest = snapshot_target(target)
        if current_hash != plan.expected_before_hash:
            raise ValueError("prepared Skill install target no longer matches its before image")
        validate_plan_before_image(plan, proposal, current_hash, current_manifest)
        ensure_stage_parent(ws, stage)
        _materialize_stage(stage, files)
        validation_results = validate_staged_skill_package(files, plan.validation_commands)
        if plan.expected_before_hash != plan.expected_after_hash:
            ensure_target_parent(plan, target)
            with PinnedDirectories(stage.parent, target.parent) as guard:
                revalidate_materialization_boundary(
                    plan,
                    target=target,
                    stage=stage,
                    expected_target_hash=plan.expected_before_hash,
                    expected_stage_hash=plan.expected_after_hash,
                    guard=guard,
                )
                moved_before = False
                try:
                    if target.exists():
                        guard.replace(target, backup)
                        moved_before = True
                        require_exact_backup(backup, plan.expected_before_hash)
                    revalidate_materialization_boundary(
                        plan,
                        target=target,
                        stage=stage,
                        expected_target_hash=EMPTY_TREE_HASH,
                        expected_stage_hash=plan.expected_after_hash,
                        guard=guard,
                    )
                    guard.replace(stage, target)
                except Exception:
                    if moved_before and not target.exists() and backup.exists():
                        require_exact_backup(backup, plan.expected_before_hash)
                        guard.replace(backup, target)
                    raise
        else:
            with PinnedDirectories(stage.parent) as guard:
                guard.rmtree(stage)
        after_hash, _after_manifest = snapshot_target(target)
        if after_hash != plan.expected_after_hash:
            compensate(journal_path, journal)
            raise RuntimeError("Skill install readback hash does not match approved package")
        journal["status"] = "materialized"
        journal["validation_results"] = validation_results
        write_journal(journal_path, journal)
    elif journal["status"] not in {"materialized", "completed"}:
        raise ValueError(f"Skill install transaction cannot resume from {journal['status']}")

    if journal["status"] == "completed":
        resolved = resolve_install_receipt(ws, application_id, actor=actor)
        if resolved is None:
            raise RuntimeError("completed Skill install transaction lacks its receipt")
        return resolved
    after_hash, _after_manifest = snapshot_target(target)
    if after_hash != plan.expected_after_hash:
        journal["status"] = "recovery_required"
        write_journal(journal_path, journal)
        raise RuntimeError("materialized Skill install target drifted before receipt")
    expected_validation_results = validate_staged_skill_package(files, plan.validation_commands)
    if journal.get("validation_results") != expected_validation_results:
        journal["status"] = "recovery_required"
        write_journal(journal_path, journal)
        raise RuntimeError("materialized Skill install validation journal drifted")
    try:
        receipt = SkillInstallReceiptRecord(
            receipt_id=receipt_id(application_id),
            application_id=application_id,
            plan_ref=asdict(plan_pin),
            proposal_ref=asdict(proposal_pin),
            package_artifact_ref=asdict(artifact_pin),
            checkpoint_request_ref=asdict(request_pin),
            checkpoint_decision_ref=asdict(decision_pin),
            operation=plan.operation,
            skill_id=plan.skill_id,
            semantic_version=plan.semantic_version,
            package_hash=plan.package_hash,
            target_root=plan.target_root,
            target_path=plan.target_path,
            hosts=list(plan.hosts),
            before_hash=plan.expected_before_hash,
            after_hash=plan.expected_after_hash,
            diff_hash=plan.diff_hash,
            validation_policy_hash=plan.validation_policy_hash,
            validation_results=list(journal.get("validation_results") or []),
            status="completed",
            completed_at=utc(now).isoformat(),
        )
        require_valid_skill_install_receipt(receipt)
        write = RecordRepository(ws, actor=actor).write(
            "skill_install_receipts",
            receipt,
            body="# Skill Install Receipt\n\nImmutable project-local deployment result.\n",
        )
        receipt_pin = PinnedRecordRef(write.record_ref, write.content_hash, write.revision)
    except Exception:
        compensate(journal_path, journal)
        raise
    journal["status"] = "completed"
    journal["completed_at"] = receipt.completed_at
    journal["receipt_ref"] = asdict(receipt_pin)
    write_journal(journal_path, journal)
    _cleanup_backup(backup)
    return receipt_pin


def recover_install_intent(
    ws: WorkspacePaths,
    application_id: str,
    *,
    plan_pin: PinnedRecordRef,
    plan: SkillInstallPlanRecord,
    request_pin: PinnedRecordRef,
    decision_pin: PinnedRecordRef,
) -> dict[str, Any]:
    journal_path = journal_path_for(ws, application_id)
    journal = load_journal(journal_path)
    _root, target = target_paths(plan.target_root, plan.name)
    stage = stage_path_for(ws, application_id)
    backup = target.parent / f".{target.name}.aitp-backup-{application_id}"
    _require_journal_binding(
        journal,
        application_id,
        plan_pin,
        request_pin,
        decision_pin,
        plan,
        stage,
        backup,
    )
    resolved = resolve_install_receipt(ws, application_id, actor=_internal_actor())
    if resolved is not None:
        validate_install_receipt(
            ws,
            plan_pin=plan_pin,
            plan=plan,
            request_pin=request_pin,
            decision_pin=decision_pin,
            application_id=application_id,
            receipt_pin=resolved,
        )
        return load_journal(journal_path)
    if journal["status"] == "completed":
        raise RuntimeError("completed Skill install transaction lacks its receipt")
    if journal["status"] == "compensated":
        return journal
    compensate(journal_path, journal)
    return load_journal(journal_path)


def validate_install_receipt(
    ws,
    *,
    plan_pin,
    plan,
    request_pin,
    decision_pin,
    application_id,
    receipt_pin,
) -> None:
    record = get_record_version(ws, receipt_pin).record
    if not isinstance(record, SkillInstallReceiptRecord):
        raise ValueError("checkpoint result is not a Skill install receipt")
    expected = (
        receipt_id(application_id),
        application_id,
        asdict(plan_pin),
        plan.proposal_ref,
        plan.package_artifact_ref,
        asdict(request_pin),
        asdict(decision_pin),
        plan.operation,
        plan.skill_id,
        plan.semantic_version,
        plan.package_hash,
        plan.target_root,
        plan.target_path,
        plan.hosts,
        plan.expected_before_hash,
        plan.expected_after_hash,
        plan.diff_hash,
        plan.validation_policy_hash,
        "completed",
    )
    actual = (
        record.receipt_id,
        record.application_id,
        record.plan_ref,
        record.proposal_ref,
        record.package_artifact_ref,
        record.checkpoint_request_ref,
        record.checkpoint_decision_ref,
        record.operation,
        record.skill_id,
        record.semantic_version,
        record.package_hash,
        record.target_root,
        record.target_path,
        record.hosts,
        record.before_hash,
        record.after_hash,
        record.diff_hash,
        record.validation_policy_hash,
        record.status,
    )
    if actual != expected:
        raise ValueError("Skill install receipt does not match the exact approved plan")
    target_hash, _manifest = snapshot_target(Path(plan.target_path))
    if target_hash != record.after_hash:
        raise ValueError("installed Skill bytes no longer match the receipt")
    _finalize_journal_after_receipt(
        ws,
        application_id=application_id,
        plan_pin=plan_pin,
        request_pin=request_pin,
        decision_pin=decision_pin,
        plan=plan,
        receipt_pin=receipt_pin,
        receipt=record,
    )


def resolve_install_receipt(ws, application_id, *, actor):
    record_ref = receipt_ref(application_id)
    result = RecordRepository(ws, actor=actor).read(record_ref)
    if result.status == "not_found":
        return None
    if result.status != "found":
        raise ValueError("Skill install receipt is not readable")
    return pin_current_record(ws, record_ref)


def _finalize_journal_after_receipt(
    ws,
    *,
    application_id,
    plan_pin,
    request_pin,
    decision_pin,
    plan,
    receipt_pin,
    receipt,
):
    journal_path = journal_path_for(ws, application_id)
    if not journal_path.exists():
        return
    journal = load_journal(journal_path)
    target = Path(plan.target_path)
    stage = stage_path_for(ws, application_id)
    backup = target.parent / f".{target.name}.aitp-backup-{application_id}"
    _require_journal_binding(
        journal,
        application_id,
        plan_pin,
        request_pin,
        decision_pin,
        plan,
        stage,
        backup,
    )
    if journal["status"] not in {"materialized", "completed"}:
        raise ValueError("Skill install receipt cannot finalize this host journal state")
    if journal.get("validation_results") != receipt.validation_results:
        raise ValueError("Skill install receipt validation results do not match the host journal")
    journal["status"] = "completed"
    journal["completed_at"] = receipt.completed_at
    journal["receipt_ref"] = asdict(receipt_pin)
    write_journal(journal_path, journal)
    _cleanup_backup(backup)


def compensate(journal_path: Path, journal: dict[str, Any]) -> None:
    target = Path(journal["target_path"])
    stage = Path(journal["stage_path"])
    backup = Path(journal["backup_path"])
    try:
        parents = []
        if target.parent.exists():
            parents.append(target.parent)
        if stage.parent.exists():
            parents.append(stage.parent)
        with PinnedDirectories(*parents) as guard:
            current_hash, _manifest = snapshot_target(target)
            if current_hash == journal["before_hash"]:
                pass
            elif current_hash == journal["after_hash"]:
                require_exact_backup(backup, journal["before_hash"])
                guard.rmtree(target)
                if backup.exists():
                    guard.replace(backup, target)
            elif current_hash == EMPTY_TREE_HASH:
                require_exact_backup(backup, journal["before_hash"])
                if backup.exists():
                    guard.replace(backup, target)
            elif current_hash != EMPTY_TREE_HASH:
                raise RuntimeError("target drift prevents automatic compensation")
            if stage.exists():
                if link_like(stage):
                    raise RuntimeError("staging path became a link")
                guard.rmtree(stage)
        restored_hash, _manifest = snapshot_target(target)
        if restored_hash != journal["before_hash"]:
            raise RuntimeError("compensation did not restore the before image")
        journal["status"] = "compensated"
        journal["completed_at"] = datetime.now(UTC).isoformat()
    except Exception as exc:
        journal["status"] = "recovery_required"
        journal["recovery_error"] = f"{type(exc).__name__}: {exc}"
        write_journal(journal_path, journal)
        raise
    write_journal(journal_path, journal)


def _require_journal_binding(
    journal,
    application_id,
    plan_pin,
    request_pin,
    decision_pin,
    plan,
    stage,
    backup,
):
    expected = {
        "version": "v1",
        "application_id": application_id,
        "plan_ref": asdict(plan_pin),
        "request_ref": asdict(request_pin),
        "decision_ref": asdict(decision_pin),
        "target_path": plan.target_path,
        "stage_path": str(stage),
        "backup_path": str(backup),
        "before_hash": plan.expected_before_hash,
        "after_hash": plan.expected_after_hash,
        "diff_hash": plan.diff_hash,
    }
    if any(journal.get(key) != value for key, value in expected.items()):
        raise ValueError("Skill install transaction journal binding does not match")
    if journal.get("status") not in {
        "prepared", "materialized", "completed", "compensated", "recovery_required",
    }:
        raise ValueError("Skill install transaction journal status is invalid")


def journal_path_for(ws, application_id):
    if Path(application_id).name != application_id:
        raise ValueError("Skill install application id is not path-safe")
    return ws.root / "runtime" / "skill_install_transactions" / f"{application_id}.json"


def load_journal(path):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Skill install transaction journal is invalid") from exc
    if not isinstance(payload, dict):
        raise ValueError("Skill install transaction journal must be an object")
    return payload


def write_journal(path, payload):
    write_text_atomic(
        path, json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    )


def receipt_id(application_id: str) -> str:
    return prefixed_id("skill-install-receipt", application_id, max_slug=64)


def receipt_ref(application_id: str) -> str:
    return f"skill_install_receipt:{receipt_id(application_id)}"


def utc(value):
    current = value or datetime.now(UTC)
    if current.tzinfo is None:
        raise ValueError("now must include a timezone")
    return current.astimezone(UTC)


def _internal_actor():
    return RecordActor(actor_type="tool", actor_id="skill-install-recovery", host="aitp-v5")
