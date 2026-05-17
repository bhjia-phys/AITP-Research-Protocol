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
