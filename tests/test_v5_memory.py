"""Tests for AITP v5 L2 memory and promotion packets."""

from dataclasses import asdict
from pathlib import Path

import pytest


def _setup_claim(tmp_path: Path):
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Counting identifies the edge CFT in the recorded sector.",
        evidence_profile="toy_numeric",
        confidence_state="locally_checked",
        active_uncertainty="scope of finite-size evidence",
    )
    return ws, claim


def test_create_promotion_packet_requires_evidence_and_scope(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.memory import create_promotion_packet
    from brain.v5.public_surfaces import require_valid_public_surface

    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim",
        scope="N<=10 exact diagonalization, fixed momentum sector",
        evidence_refs=["evidence-counting-table"],
        non_claims=["Does not prove thermodynamic stability."],
        known_failure_modes=["sector misassignment"],
    )

    assert packet.kind == "promotion_packet"
    assert packet.status == "pending_human_checkpoint"
    payload = {"ok": True, **asdict(packet)}
    assert require_valid_public_surface("promotion_packet_record", payload) == payload


def test_promotion_packet_rejects_empty_evidence_refs(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.contracts import ContractError
    from brain.v5.memory import create_promotion_packet
    from brain.v5.public_surfaces import require_valid_public_surface

    packet = create_promotion_packet(
        ws, topic_id="fqhe", claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim", scope="test",
        evidence_refs=[], known_failure_modes=["test"],
    )
    with pytest.raises(ContractError, match="evidence_refs"):
        require_valid_public_surface("promotion_packet_record", {"ok": True, **asdict(packet)})


def test_promotion_packet_rejects_empty_failure_modes(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.contracts import ContractError
    from brain.v5.memory import create_promotion_packet
    from brain.v5.public_surfaces import require_valid_public_surface

    packet = create_promotion_packet(
        ws, topic_id="fqhe", claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim", scope="test",
        evidence_refs=["evidence-1"], known_failure_modes=[],
    )
    with pytest.raises(ContractError, match="failure_modes"):
        require_valid_public_surface("promotion_packet_record", {"ok": True, **asdict(packet)})


def test_promotion_packet_persists(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.memory import create_promotion_packet
    from brain.v5.store import list_records
    from brain.v5.models import PromotionPacketRecord

    create_promotion_packet(
        ws, topic_id="fqhe", claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim", scope="test",
        evidence_refs=["evidence-1"], known_failure_modes=["test"],
    )
    records = list_records(ws.registry_dir("promotion_packets"), PromotionPacketRecord)
    assert len(records) == 1


def test_promotion_cli(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.cli import main

    result = main([
        "--base", str(tmp_path), "promotion", "packet", "create",
        "--topic", "fqhe", "--claim", claim.claim_id,
        "--proposed-kind", "scoped_claim", "--scope", "N<=10 ED",
        "--evidence-ref", "evidence-1", "--failure-mode", "misassignment",
    ])
    assert result == 0


def test_promotion_mcp(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.mcp_tools import aitp_v5_create_promotion_packet

    result = aitp_v5_create_promotion_packet(
        str(tmp_path), topic_id="fqhe", claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim", scope="N<=10 ED",
        evidence_refs=["evidence-1"], known_failure_modes=["test"],
    )
    assert result["ok"] is True
    assert result["kind"] == "promotion_packet"


def test_promotion_runtime_entrypoint():
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ep = runtime_entrypoints()
    assert "create_promotion_packet" in ep
    assert ep["create_promotion_packet"]["surface"] == "promotion_packet_record"


def test_apply_promotion_requires_approved_human_checkpoint(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Counting identifies the edge CFT in the recorded sector.",
        evidence_profile="toy_numeric",
        confidence_state="locally_checked",
        active_uncertainty="promotion readiness",
    )
    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim",
        scope="fixed sector ED",
        evidence_refs=["evidence-counting"],
        known_failure_modes=["sector misassignment"],
    )

    with pytest.raises(ValueError, match="approved human checkpoint"):
        apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id="")

    checkpoint = request_human_checkpoint(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        reason="L2 promotion requires approval.",
        requested_by="promotion_policy",
        options=["approve", "revise"],
    )
    decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="Evidence and scope are explicit.",
        decided_by="human",
    )
    memory = apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=checkpoint.checkpoint_id)

    assert memory.kind == "memory_entry"
    assert memory.source_claim_id == claim.claim_id
    assert memory.evidence_refs == ["evidence-counting"]


def test_apply_promotion_rejects_packet_with_empty_evidence_refs(tmp_path):
    """A packet with empty evidence_refs must not be promotable to L2."""
    import pytest

    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(ws, topic_id="fqhe", statement="test", evidence_profile="toy_numeric",
        confidence_state="hypothesis", active_uncertainty="test")
    # Manually create a packet with empty evidence_refs (kernel allows creation, but promotion must reject)
    from brain.v5.store import write_record
    from brain.v5.ids import prefixed_id
    from brain.v5.models import PromotionPacketRecord
    packet_id = prefixed_id("packet", claim.claim_id)
    packet = PromotionPacketRecord(
        packet_id=packet_id, topic_id="fqhe", claim_id=claim.claim_id,
        scope="test", evidence_refs=[], known_failure_modes=["test"],
    )
    write_record(ws.registry_dir("promotion_packets") / f"{packet_id}.md", packet)

    with pytest.raises(ValueError, match="evidence_refs"):
        apply_promotion_packet(ws, packet_id=packet_id, checkpoint_id="bypass")


def test_apply_promotion_rejects_packet_with_empty_failure_modes(tmp_path):
    """A packet with empty known_failure_modes must not be promotable to L2."""
    import pytest

    from brain.v5.memory import apply_promotion_packet
    from brain.v5.workspace import create_claim, create_topic, init_workspace
    from brain.v5.store import write_record
    from brain.v5.ids import prefixed_id
    from brain.v5.models import PromotionPacketRecord

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(ws, topic_id="fqhe", statement="test", evidence_profile="toy_numeric",
        confidence_state="hypothesis", active_uncertainty="test")
    packet_id = prefixed_id("packet", claim.claim_id)
    packet = PromotionPacketRecord(
        packet_id=packet_id, topic_id="fqhe", claim_id=claim.claim_id,
        scope="test", evidence_refs=["ev-1"], known_failure_modes=[],
    )
    write_record(ws.registry_dir("promotion_packets") / f"{packet_id}.md", packet)

    with pytest.raises(ValueError, match="failure_modes"):
        apply_promotion_packet(ws, packet_id=packet_id, checkpoint_id="bypass")


def test_apply_promotion_rejects_packet_with_empty_scope(tmp_path):
    """A packet with empty scope must not be promotable to L2."""
    import pytest

    from brain.v5.memory import apply_promotion_packet
    from brain.v5.workspace import create_claim, create_topic, init_workspace
    from brain.v5.store import write_record
    from brain.v5.ids import prefixed_id
    from brain.v5.models import PromotionPacketRecord

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(ws, topic_id="fqhe", statement="test", evidence_profile="toy_numeric",
        confidence_state="hypothesis", active_uncertainty="test")
    packet_id = prefixed_id("packet", claim.claim_id)
    packet = PromotionPacketRecord(
        packet_id=packet_id, topic_id="fqhe", claim_id=claim.claim_id,
        scope="", evidence_refs=["ev-1"], known_failure_modes=["test"],
    )
    write_record(ws.registry_dir("promotion_packets") / f"{packet_id}.md", packet)

    with pytest.raises(ValueError, match="scope"):
        apply_promotion_packet(ws, packet_id=packet_id, checkpoint_id="bypass")


def test_apply_promotion_populates_memory_entry_and_packet_fields(tmp_path):
    """After promotion, MemoryEntryRecord must have source_topic_id/statement/status and
    PromotionPacketRecord must record human_checkpoint_id and status=promoted."""
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.store import read_record
    from brain.v5.models import PromotionPacketRecord
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws, topic_id="fqhe",
        statement="Counting identifies the edge CFT in the recorded sector.",
        evidence_profile="toy_numeric", confidence_state="locally_checked",
        active_uncertainty="promotion readiness",
    )
    packet = create_promotion_packet(
        ws, topic_id="fqhe", claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim",
        scope="fixed sector ED",
        evidence_refs=["evidence-counting"],
        known_failure_modes=["sector misassignment"],
    )
    checkpoint = request_human_checkpoint(
        ws, topic_id="fqhe", claim_id=claim.claim_id,
        reason="L2 promotion", requested_by="risk_policy",
        options=["approve"],
    )
    decide_human_checkpoint(
        ws, checkpoint_id=checkpoint.checkpoint_id,
        decision="approve", rationale="Good", decided_by="human",
    )

    entry = apply_promotion_packet(
        ws, packet_id=packet.packet_id, checkpoint_id=checkpoint.checkpoint_id,
    )

    # MemoryEntryRecord fields
    assert entry.source_topic_id == "fqhe"
    assert entry.statement == claim.statement
    assert entry.status == "active"

    # PromotionPacketRecord updated
    refreshed_packet = read_record(
        ws.registry_dir("promotion_packets") / f"{packet.packet_id}.md",
        PromotionPacketRecord,
    )
    assert refreshed_packet.status == "promoted"
    assert refreshed_packet.human_checkpoint_id == checkpoint.checkpoint_id
