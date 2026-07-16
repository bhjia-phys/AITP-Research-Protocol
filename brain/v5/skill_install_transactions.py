"""Checkpoint orchestration for reviewed project-local Skill deployment."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from brain.v5.checkpoint_bindings import (
    CheckpointSubjectBinding,
    hash_action_payload,
    validate_checkpoint_binding,
)
from brain.v5.checkpoint_transactions import (
    apply_bound_checkpoint_action,
    checkpoint_application_identity,
)
from brain.v5.models import HumanCheckpointRecord, SkillInstallReceiptRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.skill_install_materialization import (
    materialize_plan,
    journal_path_for,
    load_journal,
    recover_install_intent,
    resolve_install_receipt,
    validate_install_receipt,
)
from brain.v5.skill_install_planning import (
    EFFECT_POLICY,
    REPLAY_POLICY,
    build_skill_install_plan,
    build_skill_rollback_plan,
    coerce_pin,
    load_plan,
    skill_install_checkpoint_request,
    target_scopes,
)


@dataclass(frozen=True)
class SkillInstallApplication:
    record: SkillInstallReceiptRecord
    receipt_ref: PinnedRecordRef
    checkpoint_application_ref: PinnedRecordRef
    replayed: bool


def apply_skill_install_plan(
    ws: WorkspacePaths,
    plan_ref: PinnedRecordRef | Mapping[str, Any],
    checkpoint_ref: Mapping[str, Any] | Any,
    *,
    actor: RecordActor,
    now: datetime | None = None,
) -> SkillInstallApplication:
    """Consume one exact approved checkpoint and deploy its pinned package bytes."""

    plan_pin, plan = load_plan(ws, plan_ref)
    request_pin, decision_pin = _checkpoint_refs(checkpoint_ref)
    binding = _binding_for_plan(ws, plan_pin, plan, decision_pin)
    result = apply_bound_checkpoint_action(
        ws,
        binding=binding,
        request_ref=request_pin,
        decision_ref=decision_pin,
        action_payload=plan.action_payload,
        result_writer=lambda application_id: materialize_plan(
            ws,
            plan_pin=plan_pin,
            plan=plan,
            request_pin=request_pin,
            decision_pin=decision_pin,
            application_id=application_id,
            actor=actor,
            now=now,
        ),
        result_resolver=lambda application_id: resolve_install_receipt(
            ws, application_id, actor=actor
        ),
        result_validator=lambda application_id, receipt_pin: validate_install_receipt(
            ws,
            plan_pin=plan_pin,
            plan=plan,
            request_pin=request_pin,
            decision_pin=decision_pin,
            application_id=application_id,
            receipt_pin=receipt_pin,
        ),
        actor=actor,
        now=now,
    )
    if result.result_ref is None:
        raise RuntimeError("Skill install checkpoint application did not produce a receipt")
    install_record = get_record_version(ws, result.result_ref).record
    if not isinstance(install_record, SkillInstallReceiptRecord):
        raise RuntimeError("Skill install checkpoint result is not an install receipt")
    return SkillInstallApplication(
        record=install_record,
        receipt_ref=result.result_ref,
        checkpoint_application_ref=result.receipt_ref,
        replayed=result.replayed,
    )


def resume_skill_install_intent(
    ws: WorkspacePaths,
    plan_ref: PinnedRecordRef | Mapping[str, Any],
    checkpoint_ref: Mapping[str, Any] | Any,
    *,
    actor: RecordActor,
) -> SkillInstallApplication:
    return apply_skill_install_plan(ws, plan_ref, checkpoint_ref, actor=actor)


def recover_skill_install_intent(
    ws: WorkspacePaths,
    application_id: str,
) -> dict[str, Any]:
    actor = RecordActor(actor_type="system", actor_id="skill-install-recovery", host="aitp")
    with RecordRepository(ws, actor=actor).lock_record(
        "skill_install_receipts",
        application_id,
    ):
        return _recover_skill_install_intent_locked(ws, application_id)


def _recover_skill_install_intent_locked(
    ws: WorkspacePaths,
    application_id: str,
) -> dict[str, Any]:
    journal = load_journal(journal_path_for(ws, application_id))
    plan_pin, plan = load_plan(ws, journal.get("plan_ref"))
    request_pin = coerce_pin(journal.get("request_ref"))
    decision_pin = coerce_pin(journal.get("decision_ref"))
    binding = _binding_for_plan(ws, plan_pin, plan, decision_pin)
    started_at = _timestamp(str(journal.get("started_at") or ""))
    request_version = validate_checkpoint_binding(
        ws,
        request_pin,
        binding,
        now=started_at,
    )
    decision_version = validate_checkpoint_binding(
        ws,
        decision_pin,
        binding,
        now=started_at,
        require_decided=True,
    )
    if request_version.record.status != "open":
        raise ValueError("Skill install recovery request ref is not the open revision")
    predecessor = f"{request_pin.record_ref}@sha256:{request_pin.content_hash}"
    if predecessor not in (decision_version.frontmatter.get("supersedes") or []):
        raise ValueError("Skill install recovery decision does not supersede its request")
    expected_id, _application_key = checkpoint_application_identity(
        binding,
        request_pin,
        decision_pin,
    )
    if application_id != expected_id:
        raise ValueError("Skill install recovery application id is not checkpoint-bound")
    return recover_install_intent(
        ws,
        application_id,
        plan_pin=plan_pin,
        plan=plan,
        request_pin=request_pin,
        decision_pin=decision_pin,
    )


def _binding_for_plan(
    ws: WorkspacePaths,
    plan_pin: PinnedRecordRef,
    plan: Any,
    decision_pin: PinnedRecordRef,
) -> CheckpointSubjectBinding:
    record = get_record_version(ws, decision_pin).record
    if not isinstance(record, HumanCheckpointRecord):
        raise ValueError("Skill install checkpoint ref is not a human checkpoint")
    expected_payload_hash = hash_action_payload(plan.action_payload)
    if record.action != plan.checkpoint_action:
        raise ValueError("Skill install checkpoint action does not match the plan")
    if record.payload_hash != expected_payload_hash:
        raise ValueError("Skill install checkpoint payload does not match the plan")
    expected_subjects = tuple(sorted((
        coerce_pin(plan.proposal_ref),
        coerce_pin(plan.package_artifact_ref),
    )))
    actual_subjects = tuple(sorted(coerce_pin(item) for item in record.subject_refs))
    if actual_subjects != expected_subjects:
        raise ValueError("Skill install checkpoint subjects do not match the plan")
    if (
        record.intent_ref != plan_pin.record_ref
        or record.intent_hash != plan_pin.content_hash
        or record.intent_revision != plan_pin.revision
    ):
        raise ValueError("Skill install checkpoint intent does not match the plan")
    if tuple(sorted(record.target_scope_refs)) != tuple(sorted(target_scopes(plan, plan_pin))):
        raise ValueError("Skill install checkpoint target does not match the plan")
    if record.effect_policy != EFFECT_POLICY or record.replay_policy != REPLAY_POLICY:
        raise ValueError("Skill install checkpoint policy does not match the plan")
    return CheckpointSubjectBinding(
        intent=plan_pin,
        subjects=expected_subjects,
        action=plan.checkpoint_action,
        action_payload_hash=expected_payload_hash,
        request_hash=record.request_hash,
        target_scope_refs=tuple(sorted(target_scopes(plan, plan_pin))),
        effect_policy=EFFECT_POLICY,
        replay_policy=REPLAY_POLICY,
    )


def _checkpoint_refs(value):
    if hasattr(value, "request_ref") and hasattr(value, "decision_ref"):
        return coerce_pin(value.request_ref), coerce_pin(value.decision_ref)
    if not isinstance(value, Mapping):
        raise TypeError("checkpoint_ref must contain request_ref and decision_ref")
    return coerce_pin(value.get("request_ref")), coerce_pin(value.get("decision_ref"))


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Skill install transaction started_at is invalid") from exc
    if parsed.tzinfo is None:
        raise ValueError("Skill install transaction started_at must include a timezone")
    return parsed


__all__ = [
    "SkillInstallApplication",
    "apply_skill_install_plan",
    "build_skill_install_plan",
    "build_skill_rollback_plan",
    "recover_skill_install_intent",
    "resume_skill_install_intent",
    "skill_install_checkpoint_request",
]
