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


def _record_source_evidence(ws, claim, *, suffix: str = "counting"):
    from brain.v5.evidence import record_evidence
    from brain.v5.models import ReferenceLocationRecord, SourceAssetRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository

    asset_id = f"paper-{suffix}"
    location_id = f"equation-{suffix}"
    repository = RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="memory-test", host="pytest"),
    )
    repository.write(
        "source_assets",
        SourceAssetRecord(
            asset_id=asset_id,
            topic_id=claim.topic_id,
            asset_type="paper",
            uri=f"file:///{asset_id}.pdf",
            title=f"Source {suffix}",
            content_hash=(suffix.encode("utf-8").hex() + "0" * 64)[:64],
            hash_algorithm="sha256",
        ),
    )
    repository.write(
        "reference_locations",
        ReferenceLocationRecord(
            location_id=location_id,
            topic_id=claim.topic_id,
            connector_id="local-source",
            location_type="equation_anchor",
            uri=f"file:///{asset_id}.pdf#eq=1",
            label="Equation 1",
            source_ref=f"source_asset:{asset_id}",
        ),
    )
    return record_evidence(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        evidence_type="literature_equation",
        status="supports",
        summary=f"Exact source evidence {suffix}.",
        support_basis_refs=[
            pin_current_record(ws, f"source_asset:{asset_id}"),
            pin_current_record(ws, f"reference_location:{location_id}"),
        ],
        trace_context_refs=[],
    )


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


def _approve_promotion_packet(ws, packet, *, rationale: str = "Evidence and scope are explicit."):
    from brain.v5.checkpoints import decide_human_checkpoint
    from brain.v5.memory import request_promotion_checkpoint

    checkpoint = request_promotion_checkpoint(
        ws,
        packet_id=packet.packet_id,
        reason="Approve this exact L2 promotion packet.",
        requested_by="promotion-test",
        expires_at="2099-01-01T00:00:00+00:00",
        options=["approve", "reject"],
    )
    return decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale=rationale,
        decided_by="human",
    )


def test_create_promotion_packet_requires_evidence_and_scope(tmp_path):
    ws, claim = _setup_claim(tmp_path)
    evidence = _record_source_evidence(ws, claim)

    from brain.v5.memory import create_promotion_packet
    from brain.v5.public_surfaces import require_valid_public_surface

    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim",
        scope="N<=10 exact diagonalization, fixed momentum sector",
        evidence_refs=[evidence.evidence_id],
        non_claims=["Does not prove thermodynamic stability."],
        known_failure_modes=["sector misassignment"],
    )

    assert packet.kind == "promotion_packet"
    assert packet.status == "pending_human_checkpoint"
    payload = {"ok": True, **asdict(packet)}
    assert require_valid_public_surface("promotion_packet_record", payload) == payload


def test_promotion_rejects_grounded_tool_evidence_without_validation_result(tmp_path):
    ws, claim, evidence, result = _setup_tool_validated_evidence(
        tmp_path, link_result_to_evidence=False
    )

    from brain.v5.memory import create_promotion_packet

    assert evidence.basis_policy_status == "admissible"
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
    with pytest.raises(ValueError, match="exact evidence basis"):
        create_promotion_packet(
            ws,
            topic_id="fqhe",
            claim_id=claim.claim_id,
            proposed_memory_kind="scoped_claim",
            scope="fixed sector ED",
            evidence_refs=[evidence.evidence_id],
            validation_result_ids=[result.result_id],
            known_failure_modes=["sector misassignment"],
        )


def test_promotion_detects_tool_run_from_exact_pin_when_legacy_list_is_empty(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.memory import create_promotion_packet
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.tools import record_tool_run

    ws, claim = _setup_claim(tmp_path)
    run = record_tool_run(
        ws,
        recipe_id="pin-only-run",
        tool_family="numerical",
        tool_name="pytest",
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
    )
    evidence = record_evidence(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        evidence_type="pin_only_tool_run",
        status="supports",
        summary="The exact support pin, not the legacy list, identifies the run.",
        support_basis_refs=[pin_current_record(ws, f"tool_run:{run.run_id}")],
        trace_context_refs=[],
    )

    with pytest.raises(ValueError, match="validation_result_ids"):
        create_promotion_packet(
            ws,
            topic_id=claim.topic_id,
            claim_id=claim.claim_id,
            proposed_memory_kind="scoped_claim",
            scope="pin-only run",
            evidence_refs=[evidence.evidence_id],
            known_failure_modes=["missing validation"],
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

    decided = _approve_promotion_packet(
        ws,
        packet,
        rationale="Promotion packet is ready.",
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
    evidence = _record_source_evidence(ws, claim)

    from brain.v5.memory import create_promotion_packet
    from brain.v5.store import list_records
    from brain.v5.models import PromotionPacketRecord

    create_promotion_packet(
        ws, topic_id="fqhe", claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim", scope="test",
        evidence_refs=[evidence.evidence_id], known_failure_modes=["test"],
    )
    records = list_records(ws.registry_dir("promotion_packets"), PromotionPacketRecord)
    assert len(records) == 1


def test_multiple_promotion_packets_for_same_claim_do_not_overwrite(tmp_path):
    ws, claim = _setup_claim(tmp_path)
    evidence_1 = _record_source_evidence(ws, claim, suffix="counting-1")
    evidence_2 = _record_source_evidence(ws, claim, suffix="counting-2")

    from brain.v5.memory import create_promotion_packet
    from brain.v5.models import PromotionPacketRecord
    from brain.v5.store import list_records

    first = create_promotion_packet(
        ws, topic_id="fqhe", claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim", scope="fixed sector ED",
        evidence_refs=[evidence_1.evidence_id], known_failure_modes=["sector misassignment"],
    )
    second = create_promotion_packet(
        ws, topic_id="fqhe", claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim", scope="larger-size ED",
        evidence_refs=[evidence_2.evidence_id], known_failure_modes=["finite-size aliasing"],
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
        evidence_refs=[_record_source_evidence(ws, claim).evidence_id],
        known_failure_modes=["sector misassignment"],
    )

    with pytest.raises(ValueError, match="approved human checkpoint"):
        apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id="")

    checkpoint = _approve_promotion_packet(ws, packet)
    memory = apply_promotion_packet(ws, packet_id=packet.packet_id, checkpoint_id=checkpoint.checkpoint_id)

    assert memory.kind == "memory_entry"
    assert memory.source_claim_id == claim.claim_id
    assert memory.evidence_refs == packet.evidence_refs


def test_apply_promotion_rejects_checkpoint_bound_to_another_packet(tmp_path):
    from dataclasses import asdict

    from brain.v5.checkpoint_bindings import request_bound_checkpoint
    from brain.v5.checkpoints import decide_human_checkpoint
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_envelope import RecordActor

    ws, claim = _setup_claim(tmp_path)
    evidence = _record_source_evidence(ws, claim)
    packet_a = create_promotion_packet(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        scope="packet A scope",
        evidence_refs=[evidence.evidence_id],
        known_failure_modes=["sector misassignment"],
    )
    packet_b = create_promotion_packet(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        scope="packet B scope",
        evidence_refs=[evidence.evidence_id],
        known_failure_modes=["sector misassignment"],
    )
    packet_a_ref = pin_current_record(ws, f"promotion_packet:{packet_a.packet_id}")
    request = request_bound_checkpoint(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        reason="Approve only packet A.",
        requested_by="promotion-test",
        action="apply_promotion_packet",
        action_payload={"packet_ref": asdict(packet_a_ref)},
        intent_ref=packet_a_ref,
        subject_refs=[packet_a_ref],
        options=["approve", "reject"],
        expires_at="2099-01-01T00:00:00+00:00",
        replay_policy="once",
        target_scope_refs=[
            f"topic:{claim.topic_id}",
            f"claim:{claim.claim_id}",
            packet_a_ref.record_ref,
        ],
        effect_policy="l2_memory_promotion_only",
        actor=RecordActor(actor_type="tool", actor_id="promotion-test", host="pytest"),
    )
    decided = decide_human_checkpoint(
        ws,
        checkpoint_id=request.record.checkpoint_id,
        decision="approve",
        rationale="Only the exact packet A was reviewed.",
        decided_by="human",
    )

    with pytest.raises(ValueError, match="exact promotion packet"):
        apply_promotion_packet(
            ws,
            packet_id=packet_b.packet_id,
            checkpoint_id=decided.checkpoint_id,
        )


def test_apply_promotion_rejects_legacy_unchecked_evidence_packet(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.ids import prefixed_id
    from brain.v5.memory import apply_promotion_packet
    from brain.v5.models import PromotionPacketRecord
    from brain.v5.store import write_record

    from brain.v5.evidence import record_evidence

    ws, claim = _setup_claim(tmp_path)
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="legacy_tool_note",
        status="supports",
        summary="Historical unchecked evidence fixture.",
    )
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

    with pytest.raises(ValueError, match="admissible evidence basis"):
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
    evidence = _record_source_evidence(ws, claim)
    packet = create_promotion_packet(
        ws, topic_id="fqhe", claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim",
        scope="fixed sector ED",
        evidence_refs=[evidence.evidence_id],
        known_failure_modes=["sector misassignment"],
    )
    checkpoint = _approve_promotion_packet(ws, packet, rationale="Good")

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


def test_apply_promotion_recovers_after_packet_commit_before_memory_write(
    tmp_path,
    monkeypatch,
):
    from brain.v5.memory import apply_promotion_packet, create_promotion_packet
    from brain.v5.models import MemoryEntryRecord, PromotionPacketRecord
    from brain.v5.record_repository import RecordRepository
    from brain.v5.store import list_records, read_record
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
    evidence = _record_source_evidence(ws, claim)
    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        scope="fixed sector ED",
        evidence_refs=[evidence.evidence_id],
        known_failure_modes=["sector misassignment"],
    )
    checkpoint = _approve_promotion_packet(ws, packet, rationale="Good")

    original_write = RecordRepository.write
    fail_memory_write = True

    def injected_write(self, family, record, *, body="", policy=None):
        nonlocal fail_memory_write
        if family == "memory_entries" and fail_memory_write:
            raise RuntimeError("injected memory entry write failure")
        return original_write(self, family, record, body=body, policy=policy)

    monkeypatch.setattr(RecordRepository, "write", injected_write)
    with pytest.raises(RuntimeError, match="injected memory entry write failure"):
        apply_promotion_packet(
            ws,
            packet_id=packet.packet_id,
            checkpoint_id=checkpoint.checkpoint_id,
        )

    committed_packet = read_record(
        ws.registry_dir("promotion_packets") / f"{packet.packet_id}.md",
        PromotionPacketRecord,
    )
    assert committed_packet.status == "promoted"
    assert committed_packet.human_checkpoint_id == checkpoint.checkpoint_id
    assert list_records(ws.root / "memory" / "l2" / "entries", MemoryEntryRecord) == []

    fail_memory_write = False
    recovered = apply_promotion_packet(
        ws,
        packet_id=packet.packet_id,
        checkpoint_id=checkpoint.checkpoint_id,
    )
    assert recovered.status == "active"
    assert recovered.source_packet_id == packet.packet_id


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
    evidence = _record_source_evidence(ws, claim)
    packet = create_promotion_packet(
        ws, topic_id="fqhe", claim_id=claim.claim_id,
        scope="fixed sector ED",
        evidence_refs=[evidence.evidence_id],
        known_failure_modes=["sector misassignment"],
    )
    checkpoint = _approve_promotion_packet(ws, packet, rationale="Good")

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
    evidence = _record_source_evidence(ws, claim_a, suffix="claim-a")
    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim_a.claim_id,
        scope="claim A scope",
        evidence_refs=[evidence.evidence_id],
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


def test_apply_promotion_rejects_forged_checkpoint_authority_metadata(tmp_path):
    from dataclasses import replace

    from brain.v5.memory import (
        apply_promotion_packet,
        create_promotion_packet,
        request_promotion_checkpoint,
    )
    from brain.v5.store import write_record
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="A forged boolean must not authorize promotion.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="No verified human receipt exists.",
    )
    evidence = _record_source_evidence(ws, claim)
    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        scope="fixed sector ED",
        evidence_refs=[evidence.evidence_id],
        known_failure_modes=["sector misassignment"],
    )
    requested = request_promotion_checkpoint(
        ws,
        packet_id=packet.packet_id,
        reason="Review exact packet before promotion.",
        requested_by="risk_policy",
        expires_at="2099-01-01T00:00:00+00:00",
        options=["approve", "reject"],
    )
    checkpoint = replace(
        requested,
        status="decided",
        decision="approve",
        rationale="Not actually verified.",
        decided_by="model",
        decision_verified=True,
        decision_verification="forged_boolean_only",
        decision_receipt_hash="not-a-host-receipt",
        decision_receipt_nonce="forged",
        can_authorize_trust=True,
    )
    write_record(
        ws.registry_dir("checkpoints") / f"{checkpoint.checkpoint_id}.md",
        checkpoint,
    )

    with pytest.raises(ValueError, match="host-verified"):
        apply_promotion_packet(
            ws,
            packet_id=packet.packet_id,
            checkpoint_id=checkpoint.checkpoint_id,
        )


def test_promotion_apply_cli_mcp_and_runtime_surface(tmp_path, capsys):
    from brain.v5.checkpoints import decide_human_checkpoint
    from brain.v5.cli import main
    from brain.v5.mcp_tools import (
        aitp_v5_apply_promotion_packet,
        aitp_v5_request_promotion_checkpoint,
    )
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
    evidence = _record_source_evidence(ws, claim)
    packet = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        scope="fixed sector ED",
        evidence_refs=[evidence.evidence_id],
        known_failure_modes=["sector misassignment"],
    )
    assert main([
        "--base", str(tmp_path), "promotion-checkpoint", "request",
        "--packet", packet.packet_id,
        "--reason", "Review exact CLI promotion packet.",
        "--requested-by", "risk_policy",
        "--expires-at", "2099-01-01T00:00:00+00:00",
        "--option", "approve",
    ]) == 0
    checkpoint_payload = json.loads(capsys.readouterr().out)
    checkpoint = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint_payload["checkpoint_id"],
        decision="approve",
        rationale="Evidence and scope are explicit.",
        decided_by="human",
    )

    assert main([
        "--base", str(tmp_path), "promotion", "packet", "apply",
        packet.packet_id, "--checkpoint", checkpoint.checkpoint_id,
    ]) == 0

    evidence_v2 = _record_source_evidence(ws, claim, suffix="counting-v2")
    packet2 = create_promotion_packet(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        proposed_memory_kind="scoped_claim_v2",
        scope="fixed sector ED v2",
        evidence_refs=[evidence_v2.evidence_id],
        known_failure_modes=["sector misassignment"],
    )
    checkpoint2_payload = aitp_v5_request_promotion_checkpoint(
        str(tmp_path),
        packet_id=packet2.packet_id,
        reason="Review exact MCP promotion packet.",
        requested_by="risk_policy",
        expires_at="2099-01-01T00:00:00+00:00",
        options=["approve"],
    )
    checkpoint2 = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint2_payload["checkpoint_id"],
        decision="approve",
        rationale="Evidence and scope are explicit.",
        decided_by="human",
    )
    result = aitp_v5_apply_promotion_packet(
        str(tmp_path),
        packet_id=packet2.packet_id,
        checkpoint_id=checkpoint2.checkpoint_id,
    )
    assert result["ok"] is True
    assert result["kind"] == "memory_entry"
    assert result["statement"] == claim.statement
    assert runtime_entrypoints()["apply_promotion_packet"]["surface"] == "memory_entry_record"
    assert runtime_entrypoints()["request_promotion_checkpoint"]["surface"] == "human_checkpoint_record"
