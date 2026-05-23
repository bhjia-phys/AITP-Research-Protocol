"""Tests for AITP v5 L2 memory and promotion packets."""

import json
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


def _setup_tool_validated_evidence(tmp_path: Path, *, link_result_to_evidence: bool = True):
    from brain.v5.evidence import record_evidence
    from brain.v5.tools import record_tool_run
    from brain.v5.validation import create_validation_contract, record_validation_result

    ws, claim = _setup_claim(tmp_path)
    contract = create_validation_contract(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        required_checks=["counting benchmark"],
        failure_modes=["sector misassignment"],
        required_evidence_outputs=["counting_table"],
        tool_recipe_ids=["recipe-fqhe-ed"],
        executor_ids=["pytest"],
    )
    run = record_tool_run(
        ws,
        recipe_id="recipe-fqhe-ed",
        tool_family="numerical",
        tool_name="pytest",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        outputs={"counting_table": "ok"},
    )
    result = record_validation_result(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        contract_id=contract.contract_id,
        tool_run_id=run.run_id,
        status="passed",
        checked_outputs=["counting_table"],
        summary="Counting table passed validation.",
    )
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="toy_numeric",
        status="supports",
        summary="Tool-derived counting evidence.",
        tool_run_ids=[run.run_id],
        validation_result_ids=[result.result_id] if link_result_to_evidence else [],
    )
    return ws, claim, evidence, result


def _approved_failure_mode_review_with_result(ws, claim, validation_result_id: str, *, status: str = "passed"):
    from brain.v5.checkpoints import decide_human_checkpoint
    from brain.v5.failure_mode_review import record_failure_mode_review_result, request_failure_mode_review_checkpoint

    checkpoint = request_failure_mode_review_checkpoint(ws, claim_id=claim.claim_id)
    approved = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve_failure_mode_review",
        rationale="Reviewed physical adequacy of known failure modes.",
        decided_by="human",
    )
    result = record_failure_mode_review_result(
        ws,
        claim_id=claim.claim_id,
        checkpoint_id=approved.checkpoint_id,
        status=status,
        reviewed_failure_modes=["sector misassignment"],
        basis_refs=["literature:fqhe-sector-review"],
        validation_result_ids=[validation_result_id],
        summary="Sector-misassignment failure mode was reviewed against typed validation basis.",
    )
    return approved, result


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


def test_create_promotion_packet_rejects_tool_evidence_without_validation_result(tmp_path):
    ws, claim, evidence, _ = _setup_tool_validated_evidence(tmp_path, link_result_to_evidence=False)

    from brain.v5.memory import create_promotion_packet

    with pytest.raises(ValueError, match="validation_result_ids"):
        create_promotion_packet(
            ws,
            topic_id="fqhe",
            claim_id=claim.claim_id,
            proposed_memory_kind="scoped_claim",
            scope="fixed sector ED",
            evidence_refs=[evidence.evidence_id],
            known_failure_modes=["sector misassignment"],
        )


def test_create_promotion_packet_records_validation_result_links_for_tool_evidence(tmp_path):
    ws, claim, evidence, result = _setup_tool_validated_evidence(tmp_path)

    from brain.v5.memory import create_promotion_packet
    from brain.v5.public_surfaces import require_valid_public_surface

    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim",
        scope="fixed sector ED",
        evidence_refs=[evidence.evidence_id],
        validation_result_ids=[result.result_id],
        known_failure_modes=["sector misassignment"],
    )

    assert packet.validation_result_ids == [result.result_id]
    payload = {"ok": True, **asdict(packet)}
    assert require_valid_public_surface("promotion_packet_record", payload) == payload


def test_promotion_packet_and_memory_entry_record_failure_mode_review_checkpoint(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim, evidence, result = _setup_tool_validated_evidence(tmp_path)
    approved_review, review_result = _approved_failure_mode_review_with_result(ws, claim, result.result_id)
    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim",
        scope="fixed sector ED",
        evidence_refs=[evidence.evidence_id],
        validation_result_ids=[result.result_id],
        known_failure_modes=["sector misassignment"],
        failure_mode_review_checkpoint_id=approved_review.checkpoint_id,
        failure_mode_review_result_id=review_result.result_id,
    )

    assert packet.failure_mode_review_checkpoint_id == approved_review.checkpoint_id
    assert packet.failure_mode_review_result_id == review_result.result_id
    assert require_valid_public_surface("promotion_packet_record", {"ok": True, **asdict(packet)})

    promotion_checkpoint = request_human_checkpoint(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        reason="Approve L2 memory promotion.",
        requested_by="promotion_policy",
        options=["approve"],
    )
    decided = decide_human_checkpoint(
        ws,
        checkpoint_id=promotion_checkpoint.checkpoint_id,
        decision="approve",
        rationale="Promotion packet is ready.",
        decided_by="human",
    )
    entry = apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=decided.checkpoint_id)

    assert entry.failure_mode_review_checkpoint_id == approved_review.checkpoint_id
    assert entry.failure_mode_review_result_id == review_result.result_id
    assert require_valid_public_surface("memory_entry_record", {"ok": True, **asdict(entry)})


def test_promotion_packet_rejects_checkpoint_without_passed_review_result(tmp_path):
    ws, claim, evidence, result = _setup_tool_validated_evidence(tmp_path)
    approved_review, review_result = _approved_failure_mode_review_with_result(
        ws,
        claim,
        result.result_id,
        status="needs_revision",
    )

    from brain.v5.memory import create_promotion_packet

    with pytest.raises(ValueError, match="failure_mode_review_result_id"):
        create_promotion_packet(
            ws,
            topic_id="fqhe",
            claim_id=claim.claim_id,
            proposed_memory_kind="scoped_claim",
            scope="fixed sector ED",
            evidence_refs=[evidence.evidence_id],
            validation_result_ids=[result.result_id],
            known_failure_modes=["sector misassignment"],
            failure_mode_review_checkpoint_id=approved_review.checkpoint_id,
        )
    with pytest.raises(ValueError, match="passed failure-mode review result"):
        create_promotion_packet(
            ws,
            topic_id="fqhe",
            claim_id=claim.claim_id,
            proposed_memory_kind="scoped_claim",
            scope="fixed sector ED",
            evidence_refs=[evidence.evidence_id],
            validation_result_ids=[result.result_id],
            known_failure_modes=["sector misassignment"],
            failure_mode_review_checkpoint_id=approved_review.checkpoint_id,
            failure_mode_review_result_id=review_result.result_id,
        )


def test_promotion_packet_rejects_empty_evidence_refs(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.memory import create_promotion_packet
    from brain.v5.models import PromotionPacketRecord
    from brain.v5.store import list_records

    with pytest.raises(ValueError, match="evidence_refs"):
        create_promotion_packet(
            ws, topic_id="fqhe", claim_id=claim.claim_id,
            proposed_memory_kind="scoped_claim", scope="test",
            evidence_refs=[], known_failure_modes=["test"],
        )
    assert list_records(ws.registry_dir("promotion_packets"), PromotionPacketRecord) == []


def test_promotion_packet_rejects_empty_failure_modes(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.memory import create_promotion_packet
    from brain.v5.models import PromotionPacketRecord
    from brain.v5.store import list_records

    with pytest.raises(ValueError, match="known_failure_modes"):
        create_promotion_packet(
            ws, topic_id="fqhe", claim_id=claim.claim_id,
            proposed_memory_kind="scoped_claim", scope="test",
            evidence_refs=["evidence-1"], known_failure_modes=[],
        )
    assert list_records(ws.registry_dir("promotion_packets"), PromotionPacketRecord) == []


def test_promotion_packet_rejects_empty_scope_before_write(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.memory import create_promotion_packet
    from brain.v5.models import PromotionPacketRecord
    from brain.v5.store import list_records

    with pytest.raises(ValueError, match="scope"):
        create_promotion_packet(
            ws, topic_id="fqhe", claim_id=claim.claim_id,
            proposed_memory_kind="scoped_claim", scope="",
            evidence_refs=["evidence-1"], known_failure_modes=["test"],
        )
    assert list_records(ws.registry_dir("promotion_packets"), PromotionPacketRecord) == []


def test_promotion_packet_rejects_empty_memory_kind_before_write(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.memory import create_promotion_packet
    from brain.v5.models import PromotionPacketRecord
    from brain.v5.store import list_records

    with pytest.raises(ValueError, match="proposed_memory_kind"):
        create_promotion_packet(
            ws, topic_id="fqhe", claim_id=claim.claim_id,
            proposed_memory_kind="", scope="test scope",
            evidence_refs=["evidence-1"], known_failure_modes=["test"],
        )
    assert list_records(ws.registry_dir("promotion_packets"), PromotionPacketRecord) == []


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


def test_multiple_promotion_packets_for_same_claim_do_not_overwrite(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.memory import create_promotion_packet
    from brain.v5.models import PromotionPacketRecord
    from brain.v5.store import list_records

    first = create_promotion_packet(
        ws, topic_id="fqhe", claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim", scope="fixed sector ED",
        evidence_refs=["evidence-1"], known_failure_modes=["sector misassignment"],
    )
    second = create_promotion_packet(
        ws, topic_id="fqhe", claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim", scope="larger-size ED",
        evidence_refs=["evidence-2"], known_failure_modes=["finite-size aliasing"],
    )

    records = list_records(ws.registry_dir("promotion_packets"), PromotionPacketRecord)
    assert first.packet_id != second.packet_id
    assert {record.packet_id for record in records} == {first.packet_id, second.packet_id}
    assert {record.scope for record in records} == {"fixed sector ED", "larger-size ED"}


def test_promotion_cli(tmp_path, capsys):
    ws, claim, evidence, validation_result = _setup_tool_validated_evidence(tmp_path)
    from brain.v5.cli import main

    approved_review, review_result = _approved_failure_mode_review_with_result(ws, claim, validation_result.result_id)

    result = main([
        "--base", str(tmp_path), "promotion", "packet", "create",
        "--topic", "fqhe", "--claim", claim.claim_id,
        "--proposed-kind", "scoped_claim", "--scope", "N<=10 ED",
        "--evidence-ref", evidence.evidence_id,
        "--validation-result-id", validation_result.result_id,
        "--failure-mode", "misassignment",
        "--failure-mode-review-checkpoint", approved_review.checkpoint_id,
        "--failure-mode-review-result", review_result.result_id,
    ])
    payload = json.loads(capsys.readouterr().out)

    assert result == 0
    assert payload["validation_result_ids"] == [validation_result.result_id]
    assert payload["failure_mode_review_checkpoint_id"] == approved_review.checkpoint_id
    assert payload["failure_mode_review_result_id"] == review_result.result_id


def test_promotion_mcp(tmp_path):
    ws, claim, evidence, validation_result = _setup_tool_validated_evidence(tmp_path)

    from brain.v5.mcp_tools import aitp_v5_create_promotion_packet

    approved_review, review_result = _approved_failure_mode_review_with_result(ws, claim, validation_result.result_id)
    result = aitp_v5_create_promotion_packet(
        str(tmp_path), topic_id="fqhe", claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim", scope="N<=10 ED",
        evidence_refs=[evidence.evidence_id],
        validation_result_ids=[validation_result.result_id],
        known_failure_modes=["test"],
        failure_mode_review_checkpoint_id=approved_review.checkpoint_id,
        failure_mode_review_result_id=review_result.result_id,
    )
    assert result["ok"] is True
    assert result["kind"] == "promotion_packet"
    assert result["validation_result_ids"] == [validation_result.result_id]
    assert result["failure_mode_review_checkpoint_id"] == approved_review.checkpoint_id
    assert result["failure_mode_review_result_id"] == review_result.result_id


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


def test_apply_promotion_rejects_tool_evidence_packet_without_validation_result(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.ids import prefixed_id
    from brain.v5.memory import apply_promotion_packet
    from brain.v5.models import PromotionPacketRecord
    from brain.v5.store import write_record

    ws, claim, evidence, _ = _setup_tool_validated_evidence(tmp_path, link_result_to_evidence=False)
    packet_id = prefixed_id("packet", f"{claim.claim_id}:tool-evidence-without-validation")
    packet = PromotionPacketRecord(
        packet_id=packet_id,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        scope="fixed sector ED",
        evidence_refs=[evidence.evidence_id],
        known_failure_modes=["sector misassignment"],
    )
    write_record(ws.registry_dir("promotion_packets") / f"{packet_id}.md", packet)
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        reason="L2 promotion requires approval.",
        requested_by="promotion_policy",
        options=["approve"],
    )
    decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="Human approval is not enough without validation result links.",
        decided_by="human",
    )

    with pytest.raises(ValueError, match="validation_result_ids"):
        apply_promotion_packet(ws, packet_id=packet_id, checkpoint_id=checkpoint.checkpoint_id)


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


def test_apply_promotion_rejects_corrupt_packet_contract_before_memory_write(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.memory import apply_promotion_packet
    from brain.v5.models import MemoryEntryRecord, PromotionPacketRecord
    from brain.v5.store import list_records, write_record
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
    packet = PromotionPacketRecord(
        packet_id="packet-corrupt-memory-kind",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        proposed_memory_kind="",
        scope="fixed sector ED",
        evidence_refs=["evidence-counting"],
        known_failure_modes=["sector misassignment"],
    )
    write_record(ws.registry_dir("promotion_packets") / f"{packet.packet_id}.md", packet)
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        reason="L2 promotion",
        requested_by="risk_policy",
        options=["approve"],
    )
    decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="Human approval cannot repair corrupt packet contract.",
        decided_by="human",
    )

    with pytest.raises(ValueError, match="promotion_packet_record.proposed_memory_kind"):
        apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=checkpoint.checkpoint_id)
    assert list_records(ws.root / "memory" / "l2" / "entries", MemoryEntryRecord) == []


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


def test_apply_promotion_rejects_already_promoted_packet(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
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

    apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=checkpoint.checkpoint_id)

    with pytest.raises(ValueError, match="already promoted"):
        apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=checkpoint.checkpoint_id)


def test_apply_promotion_rejects_checkpoint_for_different_claim(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim_a = create_claim(
        ws,
        topic_id="fqhe",
        statement="Claim A.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="promotion readiness",
    )
    claim_b = create_claim(
        ws,
        topic_id="fqhe",
        statement="Claim B.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="promotion readiness",
    )
    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim_a.claim_id,
        scope="claim A scope",
        evidence_refs=["evidence-a"],
        known_failure_modes=["failure-a"],
    )
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="fqhe",
        claim_id=claim_b.claim_id,
        reason="Approve different claim.",
        requested_by="risk_policy",
        options=["approve"],
    )
    decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="Only claim B is approved.",
        decided_by="human",
    )

    with pytest.raises(ValueError, match="same topic and claim"):
        apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=checkpoint.checkpoint_id)


def test_promotion_apply_cli_mcp_and_runtime_surface(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_apply_promotion_packet
    from brain.v5.memory import create_promotion_packet
    from brain.v5.runtime_entrypoints import runtime_entrypoints
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
        scope="fixed sector ED",
        evidence_refs=["evidence-counting"],
        known_failure_modes=["sector misassignment"],
    )
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        reason="L2 promotion",
        requested_by="risk_policy",
        options=["approve"],
    )
    decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="Evidence and scope are explicit.",
        decided_by="human",
    )

    assert main([
        "--base", str(tmp_path), "promotion", "packet", "apply",
        packet.packet_id, "--checkpoint", checkpoint.checkpoint_id,
    ]) == 0

    packet2 = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim_v2",
        scope="fixed sector ED v2",
        evidence_refs=["evidence-counting-v2"],
        known_failure_modes=["sector misassignment"],
    )
    result = aitp_v5_apply_promotion_packet(
        str(tmp_path),
        packet_id=packet2.packet_id,
        checkpoint_id=checkpoint.checkpoint_id,
    )
    assert result["ok"] is True
    assert result["kind"] == "memory_entry"
    assert result["statement"] == claim.statement
    assert runtime_entrypoints()["apply_promotion_packet"]["surface"] == "memory_entry_record"
