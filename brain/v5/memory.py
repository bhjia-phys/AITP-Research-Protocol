"""L2 memory and promotion packet management for AITP v5."""

from __future__ import annotations

from brain.v5.ids import prefixed_id
from brain.v5.models import HumanCheckpointRecord, MemoryEntryRecord, PromotionPacketRecord
from brain.v5.store import read_record, write_record
from brain.v5.workspace import WorkspacePaths, get_claim


def create_promotion_packet(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    proposed_memory_kind: str = "scoped_claim",
    scope: str = "",
    evidence_refs: list[str] | None = None,
    non_claims: list[str] | None = None,
    known_failure_modes: list[str] | None = None,
) -> PromotionPacketRecord:
    packet_id = prefixed_id("packet", claim_id)
    packet = PromotionPacketRecord(
        packet_id=packet_id,
        topic_id=topic_id,
        claim_id=claim_id,
        proposed_memory_kind=proposed_memory_kind,
        scope=scope,
        evidence_refs=evidence_refs or [],
        non_claims=non_claims or [],
        known_failure_modes=known_failure_modes or [],
    )
    write_record(ws.registry_dir("promotion_packets") / f"{packet_id}.md", packet)
    return packet


def apply_promotion_packet(
    ws: WorkspacePaths,
    *,
    packet_id: str,
    checkpoint_id: str,
) -> MemoryEntryRecord:
    if not checkpoint_id:
        raise ValueError("approved human checkpoint is required to apply a promotion packet")

    packet_path = ws.registry_dir("promotion_packets") / f"{packet_id}.md"
    packet = read_record(packet_path, PromotionPacketRecord)

    if not packet.scope:
        raise ValueError("promotion packet scope must not be empty")
    if not packet.evidence_refs:
        raise ValueError("promotion packet evidence_refs must not be empty")
    if not packet.known_failure_modes:
        raise ValueError("promotion packet known_failure_modes must not be empty")

    chk_path = ws.registry_dir("checkpoints") / f"{checkpoint_id}.md"
    checkpoint = read_record(chk_path, HumanCheckpointRecord)

    if checkpoint.status != "decided":
        raise ValueError("approved human checkpoint is required — checkpoint not decided")
    if checkpoint.decision != "approve":
        raise ValueError(f"approved human checkpoint is required — decision was {checkpoint.decision!r}")

    claim = get_claim(ws, packet.claim_id)

    entry_id = prefixed_id("memory", packet_id)
    entry = MemoryEntryRecord(
        entry_id=entry_id,
        topic_id=packet.topic_id,
        source_claim_id=packet.claim_id,
        source_topic_id=packet.topic_id,
        statement=claim.statement,
        memory_kind=packet.proposed_memory_kind,
        scope=packet.scope,
        evidence_refs=list(packet.evidence_refs),
        non_claims=list(packet.non_claims),
        known_failure_modes=list(packet.known_failure_modes),
        source_packet_id=packet_id,
        human_checkpoint_id=checkpoint_id,
        status="active",
    )
    write_record(ws.root / "memory" / "l2" / "entries" / f"{entry_id}.md", entry)

    packet.status = "promoted"
    packet.human_checkpoint_id = checkpoint_id
    write_record(packet_path, packet)

    return entry
