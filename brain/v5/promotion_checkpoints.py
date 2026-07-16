"""Exact human-checkpoint bindings for L2 promotion packets."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime
from typing import Sequence

from brain.v5.checkpoint_bindings import (
    CheckpointSubjectBinding,
    hash_action_payload,
    request_bound_checkpoint,
    validate_checkpoint_binding,
)
from brain.v5.models import HumanCheckpointRecord, PromotionPacketRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import (
    PinnedRecordRef,
    get_record_version,
    pin_current_record,
)
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository


_ACTION = "apply_promotion_packet"
_EFFECT_POLICY = "l2_memory_promotion_only"
_REPLAY_POLICY = "once"


def request_promotion_checkpoint(
    ws: WorkspacePaths,
    *,
    packet_id: str,
    reason: str,
    requested_by: str,
    expires_at: str,
    options: Sequence[str] = ("approve", "reject"),
    now: datetime | None = None,
) -> HumanCheckpointRecord:
    """Request human approval bound to one exact promotion-packet revision."""

    packet = _read_packet(ws, packet_id)
    packet_ref = pin_current_record(ws, f"promotion_packet:{packet.packet_id}")
    requested = request_bound_checkpoint(
        ws,
        topic_id=packet.topic_id,
        claim_id=packet.claim_id,
        reason=reason,
        requested_by=requested_by,
        action=_ACTION,
        action_payload=_action_payload(packet_ref),
        intent_ref=packet_ref,
        subject_refs=[packet_ref],
        options=options,
        expires_at=expires_at,
        replay_policy=_REPLAY_POLICY,
        target_scope_refs=_target_scope_refs(packet, packet_ref),
        effect_policy=_EFFECT_POLICY,
        actor=RecordActor(
            actor_type="tool",
            actor_id="request_promotion_checkpoint",
            host="aitp-v5",
        ),
        now=now,
    )
    return requested.record


def require_approved_promotion_checkpoint(
    ws: WorkspacePaths,
    packet: PromotionPacketRecord,
    checkpoint: HumanCheckpointRecord,
    *,
    now: datetime | None = None,
) -> None:
    """Fail closed unless approval binds the current exact packet revision."""

    if checkpoint.topic_id != packet.topic_id or checkpoint.claim_id != packet.claim_id:
        raise ValueError(
            "approved human checkpoint must belong to the same topic and claim as the promotion packet"
        )
    packet_ref = _authorized_packet_ref(ws, packet, checkpoint)
    if not _checkpoint_targets_packet(checkpoint, packet_ref):
        raise ValueError("approved human checkpoint must bind the exact promotion packet")
    expected = CheckpointSubjectBinding(
        intent=packet_ref,
        subjects=(packet_ref,),
        action=_ACTION,
        action_payload_hash=hash_action_payload(_action_payload(packet_ref)),
        request_hash=checkpoint.request_hash,
        target_scope_refs=tuple(_target_scope_refs(packet, packet_ref)),
        effect_policy=_EFFECT_POLICY,
        replay_policy=_REPLAY_POLICY,
    )
    checkpoint_ref = pin_current_record(
        ws,
        f"human_checkpoint:{checkpoint.checkpoint_id}",
    )
    validate_checkpoint_binding(
        ws,
        checkpoint_ref,
        expected,
        now=now,
        require_decided=True,
    )


def _authorized_packet_ref(
    ws: WorkspacePaths,
    packet: PromotionPacketRecord,
    checkpoint: HumanCheckpointRecord,
) -> PinnedRecordRef:
    current = pin_current_record(ws, f"promotion_packet:{packet.packet_id}")
    if packet.status != "promoted":
        return current
    authorized = PinnedRecordRef(
        record_ref=checkpoint.intent_ref,
        content_hash=checkpoint.intent_hash,
        revision=checkpoint.intent_revision,
    )
    version = get_record_version(ws, authorized)
    if not isinstance(version.record, PromotionPacketRecord):
        raise ValueError("approved human checkpoint must bind the exact promotion packet")
    expected = replace(
        version.record,
        status="promoted",
        human_checkpoint_id=checkpoint.checkpoint_id,
    )
    if (
        current.record_ref != authorized.record_ref
        or current.revision != authorized.revision + 1
        or asdict(packet) != asdict(expected)
    ):
        raise ValueError("promoted packet does not exactly supersede its approved revision")
    return authorized


def _checkpoint_targets_packet(
    checkpoint: HumanCheckpointRecord,
    packet_ref: PinnedRecordRef,
) -> bool:
    return bool(
        checkpoint.action == _ACTION
        and checkpoint.intent_ref == packet_ref.record_ref
        and checkpoint.intent_hash == packet_ref.content_hash
        and checkpoint.intent_revision == packet_ref.revision
        and checkpoint.subject_refs == [asdict(packet_ref)]
        and checkpoint.payload_hash == hash_action_payload(_action_payload(packet_ref))
    )


def _action_payload(packet_ref: PinnedRecordRef) -> dict:
    return {"packet_ref": asdict(packet_ref)}


def _target_scope_refs(
    packet: PromotionPacketRecord,
    packet_ref: PinnedRecordRef,
) -> list[str]:
    return [
        f"topic:{packet.topic_id}",
        f"claim:{packet.claim_id}",
        packet_ref.record_ref,
    ]


def _read_packet(ws: WorkspacePaths, packet_id: str) -> PromotionPacketRecord:
    result = RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="promotion_checkpoint", host="aitp-v5"),
    ).read(f"promotion_packet:{packet_id}")
    if result.status != "found" or not isinstance(result.record, PromotionPacketRecord):
        raise ValueError(f"promotion packet not found or malformed: {packet_id}")
    return result.record
