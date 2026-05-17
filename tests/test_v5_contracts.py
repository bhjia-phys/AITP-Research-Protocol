from __future__ import annotations


def test_execution_brief_contract_accepts_current_brief(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.contracts import validate_execution_brief
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Finite-size entanglement counting identifies the edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifact may mimic counting",
    )
    bind_session(
        ws,
        "s1",
        topic_id="fqhe",
        context_id="topological-order",
        active_claim=claim.claim_id,
    )

    result = validate_execution_brief(build_execution_brief(ws, "s1"))

    assert result.ok is True
    assert result.issues == []


def test_execution_brief_contract_rejects_missing_risk_assessment():
    from brain.v5.contracts import validate_execution_brief

    result = validate_execution_brief(
        {
            "session": {"session_id": "s1", "topic_id": "fqhe", "context_id": "topological-order"},
            "current_focus": {"active_claim": "claim-1"},
            "flow_profile": {"profile": "guided", "reason": "test", "escalation_triggers": []},
            "action_budget": {
                "level": "guided",
                "max_questions": 3,
                "required_outputs": ["scoped_claim"],
                "allowed_actions": ["answer_dynamic_physics_questions"],
                "requires_human_checkpoint": False,
            },
            "known_context": {"topic_id": "fqhe", "context_id": "topological-order"},
            "mandatory_reflection": [],
            "next_action_candidates": [],
            "forbidden_now": [],
            "human_checkpoint": {"needed": False, "reason": None},
        }
    )

    assert result.ok is False
    assert any(issue.path == "risk_assessment" for issue in result.issues)


def test_action_budget_contract_rejects_unbounded_questions():
    from brain.v5.contracts import validate_action_budget

    result = validate_action_budget(
        {
            "level": "fluid",
            "max_questions": 4,
            "required_outputs": ["session_trace"],
            "allowed_actions": ["continue_fluid_work"],
            "requires_human_checkpoint": False,
        },
        path="action_budget",
    )

    assert result.ok is False
    assert any("fluid" in issue.message and "max_questions" in issue.message for issue in result.issues)


def test_risk_assessment_contract_rejects_signal_without_evidence_ref():
    from brain.v5.contracts import validate_risk_assessment

    result = validate_risk_assessment(
        {
            "level": "rigorous",
            "score": 6,
            "signals": [
                {
                    "kind": "reproducibility_risk",
                    "severity": 3,
                    "reason": "code state missing",
                    "evidence_ref": "",
                    "suggested_action": "record code state",
                }
            ],
            "trust_reductions": [],
            "action_budget": {
                "level": "rigorous",
                "max_questions": 3,
                "required_outputs": ["evidence_or_provenance"],
                "allowed_actions": ["record_evidence"],
                "requires_human_checkpoint": False,
            },
            "human_checkpoint_needed": False,
            "summary": "rigorous protocol",
        },
        path="risk_assessment",
    )

    assert result.ok is False
    assert any(issue.path.endswith("evidence_ref") for issue in result.issues)


def test_adapter_packet_contract_accepts_current_packet(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.contracts import validate_adapter_packet
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Finite-size counting identifies the edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifacts",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)

    result = validate_adapter_packet(build_adapter_packet(ws, "s1", runtime="codex"))

    assert result.ok is True
    assert result.issues == []


def test_adapter_packet_contract_rejects_summary_as_truth_source(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.contracts import validate_adapter_packet
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The benchmark is ready for promotion.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="code provenance incomplete",
    )
    bind_session(ws, "s1", topic_id="librpa-gw", context_id="gw-methods", active_claim=claim.claim_id)
    packet = build_adapter_packet(ws, "s1", runtime="opencode")
    packet["summary_orientation"]["truth_source"] = True
    packet["adapter_contract"]["summary_files_are_truth_source"] = True
    packet["adapter_contract"]["kernel_must_be_called_before_trust_updates"] = False

    result = validate_adapter_packet(packet)

    assert result.ok is False
    paths = {issue.path for issue in result.issues}
    assert "adapter.summary_orientation.truth_source" in paths
    assert "adapter.adapter_contract.summary_files_are_truth_source" in paths
    assert "adapter.adapter_contract.kernel_must_be_called_before_trust_updates" in paths


def test_adapter_packet_contract_requires_trust_preflight_entrypoint(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.contracts import validate_adapter_packet
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Finite-size counting identifies the edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifacts",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    packet["required_kernel_entrypoints"].remove("aitp_v5_preflight_trust_update")

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(issue.path == "adapter.required_kernel_entrypoints" for issue in result.issues)


def test_adapter_packet_contract_requires_trust_apply_entrypoint(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.contracts import validate_adapter_packet
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Finite-size counting identifies the edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifacts",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    packet["required_kernel_entrypoints"].remove("aitp_v5_apply_trust_update")

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(issue.path == "adapter.required_kernel_entrypoints" for issue in result.issues)


def test_adapter_packet_contract_requires_structured_trust_mutation_entrypoints(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.contracts import validate_adapter_packet
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Finite-size counting identifies the edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifacts",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    del packet["trust_mutation_entrypoints"]["change_claim_confidence"]["apply"]

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(
        issue.path == "adapter.trust_mutation_entrypoints.change_claim_confidence.apply"
        for issue in result.issues
    )


def test_adapter_packet_contract_requires_runtime_trust_update_protocol_sequence(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.contracts import validate_adapter_packet
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Finite-size counting identifies the edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifacts",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    packet["runtime_trust_update_protocol"]["change_claim_confidence"]["sequence"].remove(
        "preflight_trust_update"
    )

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(
        issue.path == "adapter.runtime_trust_update_protocol.change_claim_confidence.sequence"
        for issue in result.issues
    )


def test_adapter_packet_contract_requires_record_protocol_typed_refs(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.contracts import validate_adapter_packet
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The benchmark log is linked to the active claim.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="code state provenance",
    )
    bind_session(ws, "s1", topic_id="librpa-gw", context_id="gw-methods", active_claim=claim.claim_id)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    packet["runtime_record_protocols"]["record_tool_run"]["required_typed_refs"].remove("claim_id")

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(
        issue.path == "adapter.runtime_record_protocols.record_tool_run.required_typed_refs"
        for issue in result.issues
    )


def test_adapter_packet_contract_requires_promotion_human_checkpoint(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.contracts import validate_adapter_packet
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The validated counting result is ready for reusable memory.",
        evidence_profile="toy_numeric",
        confidence_state="locally_checked",
        active_uncertainty="promotion boundary",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    packet["runtime_gate_protocols"]["promote_to_l2"]["human_checkpoint_required"] = False

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(
        issue.path == "adapter.runtime_gate_protocols.promote_to_l2.human_checkpoint_required"
        for issue in result.issues
    )


def test_summary_orientation_contract_accepts_current_payload(tmp_path):
    from brain.v5.contracts import validate_summary_orientation
    from brain.v5.summaries import read_summary_orientation, write_session_summary
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The summary orientation is a readable shell only.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="summary may be stale",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    write_session_summary(ws, "s1")

    result = validate_summary_orientation(read_summary_orientation(ws, "s1"))

    assert result.ok is True
    assert result.issues == []


def test_summary_orientation_contract_rejects_truth_source_payload():
    from brain.v5.contracts import validate_summary_orientation

    result = validate_summary_orientation(
        {
            "kind": "summary_orientation",
            "session_id": "s1",
            "summary_dir": ".aitp/surfaces/session_summaries/s1",
            "files": {},
            "truth_source": True,
            "orientation_only": False,
            "can_update_kernel_state": True,
        }
    )

    assert result.ok is False
    paths = {issue.path for issue in result.issues}
    assert "summary_orientation.truth_source" in paths
    assert "summary_orientation.orientation_only" in paths
    assert "summary_orientation.can_update_kernel_state" in paths
