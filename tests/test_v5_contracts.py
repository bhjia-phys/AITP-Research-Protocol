from __future__ import annotations


def _minimal_execution_brief_payload():
    return {
        "session": {"session_id": "s1", "topic_id": "fqhe", "context_id": "topological-order"},
        "current_focus": {"active_claim": "claim-1"},
        "flow_profile": {"profile": "guided", "reason": "test", "escalation_triggers": []},
        "risk_assessment": {
            "level": "guided",
            "score": 2,
            "signals": [],
            "trust_reductions": [],
            "action_budget": {
                "level": "guided",
                "max_questions": 3,
                "required_outputs": ["scoped_claim"],
                "allowed_actions": ["answer_dynamic_physics_questions"],
                "requires_human_checkpoint": False,
            },
            "human_checkpoint_needed": False,
            "summary": "guided protocol",
        },
        "action_budget": {
            "level": "guided",
            "max_questions": 3,
            "required_outputs": ["scoped_claim"],
            "allowed_actions": ["answer_dynamic_physics_questions"],
            "requires_human_checkpoint": False,
        },
        "known_context": {"topic_id": "fqhe", "context_id": "topological-order"},
        "claim_relation_map": {
            "kind": "claim_relation_map",
            "topic_id": "fqhe",
            "session_id": "s1",
            "claim_id": "claim-1",
            "claim_statement": "Test claim.",
            "confidence_state": "hypothesis",
            "evidence_profile": "toy_numeric",
            "latest_claim_status": {},
            "supported_by": [],
            "limited_by": [],
            "contradicted_by": [],
            "not_tested_by": [],
            "object_relations": [],
            "current_conclusion": {
                "can_say": ["active claim remains hypothesis"],
                "cannot_say": ["cannot update or promote claim trust from this relation map alone"],
            },
            "current_blockers": [],
            "next_valid_actions": ["record explicit evidence before drawing conclusions"],
            "source_records": {
                "claims": ["claim-1"],
                "evidence": [],
                "tool_runs": [],
                "claim_statuses": [],
                "proof_obligations": [],
                "object_relations": [],
            },
            "derived_from": [],
            "truth_source": False,
            "orientation_only": True,
            "summary_inputs_trusted": False,
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
            "trust_update_allowed": False,
        },
        "mandatory_reflection": [],
        "next_action_candidates": [],
        "forbidden_now": [],
        "human_checkpoint": {"needed": False, "reason": None},
    }


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


def test_execution_brief_contract_rejects_memory_entry_truth_source():
    from brain.v5.contracts import validate_execution_brief

    payload = _minimal_execution_brief_payload()
    payload["known_context"]["memory_entries"] = [
        {
            "entry_id": "memory-fqhe",
            "memory_kind": "scoped_claim",
            "scope": "finite-size sector",
            "evidence_refs": ["evidence-counting"],
            "source_packet_id": "packet-fqhe",
            "human_checkpoint_id": "checkpoint-fqhe",
            "orientation_only": False,
        }
    ]

    result = validate_execution_brief(payload)

    assert result.ok is False
    assert any(
        issue.path == "brief.known_context.memory_entries[0].orientation_only"
        for issue in result.issues
    )


def test_execution_brief_contract_requires_memory_entry_lists():
    from brain.v5.contracts import validate_execution_brief

    payload = _minimal_execution_brief_payload()
    payload["known_context"]["memory_entries"] = [
        {
            "entry_id": "memory-gw",
            "memory_kind": "code_method_claim",
            "scope": "librpa commit abc123",
            "evidence_refs": "evidence-gw",
            "code_state_ids": "code-state-gw",
            "source_packet_id": "packet-gw",
            "human_checkpoint_id": "checkpoint-gw",
            "orientation_only": True,
        }
    ]

    result = validate_execution_brief(payload)

    assert result.ok is False
    paths = {issue.path for issue in result.issues}
    assert "brief.known_context.memory_entries[0].evidence_refs" in paths
    assert "brief.known_context.memory_entries[0].code_state_ids" in paths


def test_execution_brief_contract_requires_domain_packs_to_stay_orientation_only():
    from brain.v5.contracts import validate_execution_brief

    payload = _minimal_execution_brief_payload()
    payload["known_context"]["domain_packs"] = [
        {
            "pack_id": "gw_librpa",
            "domain": "gw_librpa",
            "description": "LibRPA/GW guidance.",
            "suggested_question_intents": ["provenance_check"],
            "risk_signals": ["reproducibility_risk"],
            "tool_recipes": ["abacus_librpa_input_audit"],
            "skill_refs": [{"skill_id": "oh-my-librpa"}],
            "manifest_refs": [{"path": "registry/domain-manifest.abacus-librpa.json"}],
            "integration_boundary": "skills guide execution; typed records carry trust",
            "truth_standard_policy": "global_only",
            "orientation_only": False,
        }
    ]

    result = validate_execution_brief(payload)

    assert result.ok is False
    assert any(
        issue.path == "brief.known_context.domain_packs[0].orientation_only"
        for issue in result.issues
    )


def test_execution_brief_contract_requires_operating_notes_to_stay_orientation_only():
    from brain.v5.contracts import validate_execution_brief

    payload = _minimal_execution_brief_payload()
    payload["known_context"]["operating_notes"] = [
        {
            "location_id": "reference-location-qsgw",
            "label": "QSGW dual-lane strategy",
            "uri": "file:///reports/qsgw.md",
            "summary": "Final and diagnostic lanes.",
            "status": "active_strategy_note",
            "location_type": "strategy_note",
            "diagnostic_lane_labels": ["diagnostic"],
            "orientation_only": False,
        }
    ]

    result = validate_execution_brief(payload)

    assert result.ok is False
    assert any(
        issue.path == "brief.known_context.operating_notes[0].orientation_only"
        for issue in result.issues
    )


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


def test_adapter_packet_contract_requires_protocol_registry_metadata(tmp_path):
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
    packet.pop("adapter_protocol_registry", None)

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(issue.path == "adapter.adapter_protocol_registry" for issue in result.issues)


def test_adapter_packet_contract_rejects_tampered_public_surface_audit(tmp_path):
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
        active_uncertainty="finite-size artifact may mimic counting",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    packet["public_surface_audit"]["surface_names"] = ["adapter_packet"]

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(issue.path == "adapter.public_surface_audit" for issue in result.issues)


def test_adapter_packet_contract_rejects_tampered_runtime_entrypoints(tmp_path):
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
        active_uncertainty="finite-size artifact may mimic counting",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    packet["runtime_entrypoints"]["public_surfaces"]["mcp"] = "aitp_v5_guess_public_surfaces"

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(issue.path == "adapter.runtime_entrypoints" for issue in result.issues)


def test_adapter_packet_contract_rejects_stale_canonical_runtime_entrypoints(tmp_path, monkeypatch):
    from brain.v5.adapters import build_adapter_packet
    import brain.v5.contracts as contracts
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Finite-size counting identifies the edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifact may mimic counting",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    stale_entrypoints = runtime_entrypoints()
    stale_entrypoints["public_surfaces"]["mcp"] = "aitp_v5_guess_public_surfaces"
    packet["runtime_entrypoints"] = stale_entrypoints
    monkeypatch.setattr(contracts, "runtime_entrypoints", lambda: stale_entrypoints)

    result = contracts.validate_adapter_packet(packet)

    assert result.ok is False
    assert any(
        issue.path == "adapter.runtime_entrypoints.public_surfaces.mcp"
        for issue in result.issues
    )


def test_adapter_packet_contract_requires_registry_protocol_field_list(tmp_path):
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
    packet["adapter_protocol_registry"]["protocol_fields"] = []

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(issue.path == "adapter.adapter_protocol_registry.protocol_fields" for issue in result.issues)


def test_adapter_packet_contract_requires_each_registry_protocol_field_in_packet(tmp_path):
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
    del packet["runtime_gate_protocols"]

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(
        issue.path == "adapter.adapter_protocol_registry.protocol_fields.runtime_gate_protocols"
        for issue in result.issues
    )


def test_adapter_packet_contract_recomputes_protocol_fingerprint(tmp_path):
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
    packet["trust_changing_actions"] = list(reversed(packet["trust_changing_actions"]))
    packet["requires_kernel_call_before"] = list(reversed(packet["requires_kernel_call_before"]))

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(
        issue.path == "adapter.adapter_protocol_registry.protocol_fingerprint"
        for issue in result.issues
    )


def test_adapter_packet_contract_rejects_tampered_protocol_fingerprint_algorithm(tmp_path):
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
    packet["adapter_protocol_registry"]["protocol_fingerprint_algorithm"] = "md5"

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(
        issue.path == "adapter.adapter_protocol_registry.protocol_fingerprint_algorithm"
        for issue in result.issues
    )


def test_adapter_packet_contract_rejects_tampered_protocol_fingerprint_inputs(tmp_path):
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
    packet["adapter_protocol_registry"]["protocol_fingerprint_inputs"] = ["trust_changing_actions"]

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(
        issue.path == "adapter.adapter_protocol_registry.protocol_fingerprint_inputs"
        for issue in result.issues
    )


def test_adapter_protocol_registry_contract_accepts_current_registry():
    from brain.v5.adapter_protocols import adapter_protocol_registry
    from brain.v5.contracts import validate_adapter_protocol_registry

    result = validate_adapter_protocol_registry(adapter_protocol_registry())

    assert result.ok is True


def test_adapter_protocol_registry_contract_rejects_tampered_inputs():
    from brain.v5.adapter_protocols import adapter_protocol_registry
    from brain.v5.contracts import validate_adapter_protocol_registry

    registry = adapter_protocol_registry()
    registry["protocol_fingerprint_inputs"] = ["trust_changing_actions"]

    result = validate_adapter_protocol_registry(registry)

    assert result.ok is False
    assert any(
        issue.path == "adapter_protocol_registry.protocol_fingerprint_inputs"
        for issue in result.issues
    )


def test_adapter_protocol_registry_require_raises_on_invalid_registry():
    import pytest

    from brain.v5.adapter_protocols import adapter_protocol_registry
    from brain.v5.contracts import ContractError, require_valid_adapter_protocol_registry

    registry = adapter_protocol_registry()
    registry["protocol_fingerprint_algorithm"] = "md5"

    with pytest.raises(ContractError):
        require_valid_adapter_protocol_registry(registry)


def test_adapter_protocol_registry_contract_rejects_tampered_public_surface_contracts():
    from brain.v5.adapter_protocols import adapter_protocol_registry
    from brain.v5.contracts import validate_adapter_protocol_registry

    registry = adapter_protocol_registry()
    registry["public_surface_contracts"] = ["adapter_packet"]

    result = validate_adapter_protocol_registry(registry)

    assert result.ok is False
    assert any(
        issue.path == "adapter_protocol_registry.public_surface_contracts"
        for issue in result.issues
    )


def test_adapter_protocol_registry_contract_rejects_tampered_public_surface_validator():
    from brain.v5.adapter_protocols import adapter_protocol_registry
    from brain.v5.contracts import validate_adapter_protocol_registry

    registry = adapter_protocol_registry()
    registry["public_surface_validator"] = "brain.v5.contracts.require_valid_adapter_packet"

    result = validate_adapter_protocol_registry(registry)

    assert result.ok is False
    assert any(
        issue.path == "adapter_protocol_registry.public_surface_validator"
        for issue in result.issues
    )


def test_session_summary_bundle_contract_accepts_orientation_only_bundle(tmp_path):
    from brain.v5.contracts import validate_session_summary_bundle

    payload = {
        "kind": "session_summary_bundle",
        "session_id": "s1",
        "topic_id": "fqhe",
        "active_claim": "claim-fqhe",
        "summary_dir": str(tmp_path / "summaries" / "s1"),
        "files": {
            "task_plan": str(tmp_path / "task_plan.md"),
            "findings": str(tmp_path / "findings.md"),
            "progress": str(tmp_path / "progress.md"),
        },
        "derived_from": "kernel_state",
        "truth_source": False,
        "orientation_only": True,
        "adapter_rule": "read_for_orientation_then_call_kernel_before_trust_updates",
        "source_records": {
            "sessions": ["s1"],
            "claims": ["claim-fqhe"],
            "evidence": [],
            "tool_runs": [],
        },
    }

    result = validate_session_summary_bundle(payload)

    assert result.ok is True


def test_session_summary_bundle_contract_rejects_truth_source_bundle(tmp_path):
    from brain.v5.contracts import validate_session_summary_bundle

    payload = {
        "kind": "session_summary_bundle",
        "session_id": "s1",
        "topic_id": "fqhe",
        "active_claim": "claim-fqhe",
        "summary_dir": str(tmp_path / "summaries" / "s1"),
        "files": {
            "task_plan": str(tmp_path / "task_plan.md"),
            "findings": str(tmp_path / "findings.md"),
            "progress": str(tmp_path / "progress.md"),
        },
        "derived_from": "kernel_state",
        "truth_source": True,
        "orientation_only": True,
        "adapter_rule": "read_for_orientation_then_call_kernel_before_trust_updates",
        "source_records": {"sessions": ["s1"]},
    }

    result = validate_session_summary_bundle(payload)

    assert result.ok is False
    assert any(issue.path == "session_summary_bundle.truth_source" for issue in result.issues)


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


def test_adapter_packet_contract_requires_gate_pre_tool_policy(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.contracts import validate_adapter_packet
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Validation must go through the shared pre-tool policy surface.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="adapter gate could skip policy",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    del packet["runtime_gate_protocols"]["validate_claim"]["pre_tool_policy"]

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(
        issue.path == "adapter.runtime_gate_protocols.validate_claim.pre_tool_policy"
        for issue in result.issues
    )


def test_adapter_packet_contract_requires_hook_protocol_summary_guard(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.contracts import validate_adapter_packet
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Hook output must not become a truth source.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="adapter hook contract",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    packet["runtime_hook_protocols"]["post_tool"]["summary_inputs_trusted"] = True

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(
        issue.path == "adapter.runtime_hook_protocols.post_tool.summary_inputs_trusted"
        for issue in result.issues
    )


def test_adapter_packet_contract_rejects_stale_hook_installation_template(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.contracts import validate_adapter_packet
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Hook installation template must derive from hook protocols.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="stale adapter template",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    packet["runtime_hook_installation"]["hooks"][0]["command"] = ["python", "stale_hook.py"]

    result = validate_adapter_packet(packet)

    assert result.ok is False
    assert any(issue.path == "adapter.runtime_hook_installation" for issue in result.issues)


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
