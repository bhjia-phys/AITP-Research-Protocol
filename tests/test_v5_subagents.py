from __future__ import annotations


def test_adversarial_brief_generates_bounded_critic_packet(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.subagents import plan_subagent_packets
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="Promote the modified self-energy kernel as a paper-ready GW benchmark result.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="conflicts with benchmark and may need expensive QSGW rerun",
    )
    bind_session(ws, "s1", topic_id="librpa-gw", context_id="gw-methods", active_claim=claim.claim_id)
    brief = build_execution_brief(ws, "s1")

    packets = plan_subagent_packets(
        brief,
        evidence_refs=["evidence:benchmark-log"],
        code_state_refs=["code_state:code-state-librpa-clean"],
    )

    critic = next(packet for packet in packets if packet.packet_type == "CriticPacket")
    assert critic.claim_id == claim.claim_id
    assert critic.risk_level == "adversarial"
    assert critic.evidence_refs == ["evidence:benchmark-log"]
    assert critic.code_state_refs == ["code_state:code-state-librpa-clean"]
    assert "counterargument" in critic.expected_output
    assert "l2_promotion" not in critic.allowed_return_records


def test_fluid_brief_does_not_generate_subagent_packets(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.code import record_code_state
    from brain.v5.subagents import plan_subagent_packets
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="Si G0W0 benchmark stays within trusted tolerance.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="routine benchmark rerun",
        recipe_id="librpa-si-g0w0",
    )
    record_code_state(
        ws,
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="master",
        upstream_commit="abc123",
        local_branch="topic/rerun",
        worktree_path="D:/worktrees/librpa/rerun",
        dirty=False,
        linked_records={"claim_id": claim.claim_id},
    )
    bind_session(ws, "s1", topic_id="librpa-gw", context_id="gw-methods", active_claim=claim.claim_id)
    brief = build_execution_brief(ws, "s1")

    packets = plan_subagent_packets(brief)

    assert brief["risk_assessment"]["level"] == "fluid"
    assert packets == []


def test_literature_conflict_signal_generates_literature_scout_packet(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.subagents import plan_subagent_packets
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The proposed counting signature is paper-ready.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="conflicts with literature counting convention",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    brief = build_execution_brief(ws, "s1")

    packets = plan_subagent_packets(brief)

    assert any(packet.packet_type == "LiteratureScoutPacket" for packet in packets)


def test_subagent_packet_excludes_noisy_history_and_returns_records_only():
    from brain.v5.subagents import SubagentPacket

    packet = SubagentPacket(
        packet_id="packet-critic-1",
        packet_type="CriticPacket",
        claim_id="claim-1",
        claim_statement="A local claim.",
        risk_level="adversarial",
        risk_signals=["claim_importance"],
        evidence_refs=[],
        code_state_refs=[],
        expected_output="counterargument_or_falsification_path",
        allowed_return_records=["evidence", "proposal"],
        excluded_context_note="No unrelated topic history included.",
    )

    payload = packet.to_payload()

    assert "topic_history" not in payload
    assert payload["excluded_context_note"] == "No unrelated topic history included."
    assert payload["allowed_return_records"] == ["evidence", "proposal"]


def test_ingest_critic_result_records_evidence_and_proposal_not_promotion(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.subagents import ingest_subagent_result, plan_subagent_packets
    from brain.v5.workspace import bind_session, create_claim, create_topic, get_claim, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="Promote the modified self-energy kernel as a paper-ready GW benchmark result.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="conflicts with benchmark and may need expensive QSGW rerun",
    )
    bind_session(ws, "s1", topic_id="librpa-gw", context_id="gw-methods", active_claim=claim.claim_id)
    packet = next(
        packet
        for packet in plan_subagent_packets(build_execution_brief(ws, "s1"), evidence_refs=["evidence:benchmark-log"])
        if packet.packet_type == "CriticPacket"
    )

    result = ingest_subagent_result(
        ws,
        packet,
        topic_id="librpa-gw",
        result_payload={
            "summary": "The critic found that a finite-size aliasing path can mimic the reported benchmark stability.",
            "critique_summary": "Strongest falsification route: rerun the negative-control sector before promotion.",
            "status": "raises_risk",
            "proposed_next_actions": ["run_negative_control_benchmark"],
        },
    )

    assert result.kind == "subagent_result_ingestion"
    assert result.direct_trust_mutation is False
    assert result.l2_promotion_allowed is False
    assert result.evidence.evidence_type == "subagent_critique"
    assert result.evidence.status == "raises_risk"
    assert result.evidence.supports_outputs == [
        "counterargument_or_falsification_path",
        "evidence_or_provenance",
    ]
    assert f"subagent_packet:{packet.packet_id}" in result.evidence.source_refs
    assert result.proposal.kind == "sensemaking_report"
    assert result.proposal.validation_status == "not_validation"
    assert result.proposal.evidence_refs == [result.evidence.evidence_id]
    assert result.proposal.next_actions == ["run_negative_control_benchmark"]
    assert get_claim(ws, claim.claim_id).confidence_state == "hypothesis"

    refreshed = build_execution_brief(ws, "s1")
    assert "counterargument_or_falsification_path" in refreshed["evidence_coverage"]["satisfied_outputs"]


def test_subagent_result_rejects_direct_trust_mutation_without_writing(tmp_path):
    import pytest

    from brain.v5.models import EvidenceRecord, SensemakingReportRecord
    from brain.v5.store import list_records
    from brain.v5.subagents import SubagentPacket, ingest_subagent_result
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The counting result is ready for promotion.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="adversarial check missing",
    )
    packet = SubagentPacket(
        packet_id="packet-critic-fqhe",
        packet_type="CriticPacket",
        claim_id=claim.claim_id,
        claim_statement=claim.statement,
        risk_level="adversarial",
        expected_output="counterargument_or_falsification_path",
    )

    with pytest.raises(ValueError, match="cannot mutate trust state"):
        ingest_subagent_result(
            ws,
            packet,
            topic_id="fqhe",
            result_payload={
                "summary": "Looks good.",
                "confidence_state": "human_accepted",
            },
        )

    assert list_records(ws.registry_dir("evidence"), EvidenceRecord) == []
    assert list_records(ws.registry_dir("sensemaking_reports"), SensemakingReportRecord) == []


def test_cli_mcp_and_runtime_surface_ingest_subagent_result(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_ingest_subagent_result
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.subagents import SubagentPacket
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The edge counting result survives a critic check.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="counterexample not checked",
    )
    packet = SubagentPacket(
        packet_id="packet-critic-fqhe",
        packet_type="CriticPacket",
        claim_id=claim.claim_id,
        claim_statement=claim.statement,
        risk_level="adversarial",
        expected_output="counterargument_or_falsification_path",
    ).to_payload()

    assert main([
        "--base", str(tmp_path), "subagent", "ingest-result",
        "--topic", "fqhe",
        "--packet-json", json.dumps(packet),
        "--result-json", json.dumps({
            "summary": "Critic asks for a negative-control sector.",
            "proposed_next_actions": ["compare_with_negative_control"],
        }),
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    assert cli_payload["ok"] is True
    assert cli_payload["kind"] == "subagent_result_ingestion"
    assert cli_payload["evidence"]["kind"] == "evidence"
    assert cli_payload["proposal"]["kind"] == "sensemaking_report"

    mcp_payload = aitp_v5_ingest_subagent_result(
        str(tmp_path),
        topic_id="fqhe",
        packet=packet,
        result_payload={"summary": "MCP critic result is stored as a proposal."},
    )
    assert mcp_payload["ok"] is True
    assert mcp_payload["direct_trust_mutation"] is False
    assert runtime_entrypoints()["ingest_subagent_result"]["mcp"] == "aitp_v5_ingest_subagent_result"
