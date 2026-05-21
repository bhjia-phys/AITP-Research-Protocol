from __future__ import annotations


def _seed_session(tmp_path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="The edge counting claim is ready to consider for L2 memory.",
        evidence_profile="literature_synthesis",
        confidence_state="locally_checked",
        active_uncertainty="promotion still needs cited evidence refs",
    )
    bind_session(
        ws,
        "s1",
        topic_id="fqhe",
        context_id="topological-order",
        active_claim=claim.claim_id,
    )
    return ws, claim


def _seed_tool_validated_evidence(ws, claim):
    from brain.v5.evidence import record_evidence
    from brain.v5.tools import record_tool_run
    from brain.v5.validation import create_validation_contract, record_validation_result

    contract = create_validation_contract(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        required_checks=["edge counting benchmark"],
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
        validation_result_ids=[result.result_id],
    )
    return evidence, result


def test_generated_bridges_can_drive_gate_pre_tool_policy_decision(tmp_path):
    from brain.v5.adapter_runtime import evaluate_bridge_gate_pre_tool_policy
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.hook_install_templates import write_codex_hook_bridge, write_opencode_plugin_bridge
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _seed_session(tmp_path)
    codex_packet = build_adapter_packet(ws, "s1", runtime="codex")
    opencode_packet = build_adapter_packet(ws, "s1", runtime="opencode")
    codex_bridge = {
        "ok": True,
        **write_codex_hook_bridge(
            tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md",
            codex_packet["runtime_hook_installation"],
            codex_packet["runtime_gate_protocols"],
        ),
    }
    opencode_bridge = {
        "ok": True,
        **write_opencode_plugin_bridge(
            tmp_path / ".opencode" / "AITP_V5_PLUGIN_BRIDGE.md",
            opencode_packet["runtime_hook_installation"],
            opencode_packet["runtime_gate_protocols"],
        ),
    }

    for bridge in (codex_bridge, opencode_bridge):
        payload = evaluate_bridge_gate_pre_tool_policy(
            ws,
            bridge,
            session_id="s1",
            action="promote_to_l2",
            claim_id=claim.claim_id,
            evidence_refs=[],
        )

        assert payload["kind"] == "hook_decision"
        assert require_valid_public_surface("pre_tool_policy_decision", payload) == payload
        assert payload["block"] is True
        assert payload["required_actions"] == ["attach_evidence_ref"]
        assert payload["runtime_gate_protocol"]["source_protocol_field"] == "runtime_gate_protocols"
        assert payload["runtime_gate_protocol"]["action"] == "promote_to_l2"
        assert payload["runtime_gate_protocol"]["pre_tool_policy"] == "aitp_v5_evaluate_pre_tool_policy"
        assert payload["runtime_gate_protocol"]["sequence"][1] == "evaluate_pre_tool_policy"
        assert payload["runtime_gate_protocol"]["policy_reasons_field"] == "policy_reasons"


def test_bridge_lifecycle_event_maps_to_gate_pre_tool_policy(tmp_path):
    from brain.v5.adapter_runtime import evaluate_bridge_lifecycle_event
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.hook_install_templates import write_codex_hook_bridge, write_opencode_plugin_bridge
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _seed_session(tmp_path)
    bridges = []
    for runtime in ("codex", "opencode"):
        packet = build_adapter_packet(ws, "s1", runtime=runtime)
        if runtime == "codex":
            bridge = {
                "ok": True,
                **write_codex_hook_bridge(
                    tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md",
                    packet["runtime_hook_installation"],
                    packet["runtime_gate_protocols"],
                ),
            }
        else:
            bridge = {
                "ok": True,
                **write_opencode_plugin_bridge(
                    tmp_path / ".opencode" / "AITP_V5_PLUGIN_BRIDGE.md",
                    packet["runtime_hook_installation"],
                    packet["runtime_gate_protocols"],
                ),
            }
        bridges.append(bridge)

    event = {
        "lifecycle_event": "pre_tool",
        "session_id": "s1",
        "action": "promote_to_l2",
        "claim_id": claim.claim_id,
        "evidence_refs": [],
        "source_kind": "typed_records",
    }

    for bridge in bridges:
        payload = evaluate_bridge_lifecycle_event(ws, bridge, event)

        assert payload["block"] is True
        assert require_valid_public_surface("pre_tool_policy_decision", payload) == payload
        assert payload["runtime_event"]["lifecycle_event"] == "pre_tool"
        assert payload["runtime_event"]["action"] == "promote_to_l2"
        assert payload["runtime_gate_protocol"]["action"] == "promote_to_l2"


def test_codex_platform_pre_tool_event_maps_mcp_call_to_gate_policy(tmp_path):
    from brain.v5.adapter_runtime import evaluate_platform_pre_tool_event
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.hook_install_templates import write_codex_hook_bridge
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _seed_session(tmp_path)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    bridge = {
        "ok": True,
        **write_codex_hook_bridge(
            tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md",
            packet["runtime_hook_installation"],
            packet["runtime_gate_protocols"],
        ),
    }

    payload = evaluate_platform_pre_tool_event(
        ws,
        bridge,
        {
            "runtime": "codex",
            "hook_name": "pre_tool",
            "session_id": "s1",
            "tool_name": "mcp__aitp__aitp_v5_create_promotion_packet",
            "tool_input": {
                "topic_id": "fqhe",
                "claim_id": claim.claim_id,
                "source_kind": "typed_records",
            },
        },
    )

    assert payload["block"] is True
    assert require_valid_public_surface("pre_tool_policy_decision", payload) == payload
    assert payload["runtime_event"]["runtime"] == "codex"
    assert payload["runtime_event"]["platform_event"] == "codex_pre_tool"
    assert payload["runtime_event"]["tool_name"] == "mcp__aitp__aitp_v5_create_promotion_packet"
    assert payload["runtime_gate_protocol"]["action"] == "create_promotion_packet"


def test_codex_platform_pre_tool_event_passes_promotion_validation_links(tmp_path):
    from brain.v5.adapter_runtime import evaluate_platform_pre_tool_event
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.hook_install_templates import write_codex_hook_bridge
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _seed_session(tmp_path)
    evidence, validation_result = _seed_tool_validated_evidence(ws, claim)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    bridge = {
        "ok": True,
        **write_codex_hook_bridge(
            tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md",
            packet["runtime_hook_installation"],
            packet["runtime_gate_protocols"],
        ),
    }

    payload = evaluate_platform_pre_tool_event(
        ws,
        bridge,
        {
            "runtime": "codex",
            "hook_name": "pre_tool",
            "session_id": "s1",
            "tool_name": "mcp__aitp__aitp_v5_create_promotion_packet",
            "tool_input": {
                "topic_id": "fqhe",
                "claim_id": claim.claim_id,
                "evidence_refs": [evidence.evidence_id],
                "validation_result_ids": [validation_result.result_id],
                "known_failure_modes": ["finite-size aliasing"],
                "source_kind": "typed_records",
                "risk_level": "rigorous",
            },
        },
    )

    assert payload["block"] is False
    assert require_valid_public_surface("pre_tool_policy_decision", payload) == payload
    assert payload["action"] == "create_promotion_packet"
    assert payload["evidence_refs"] == [evidence.evidence_id]
    assert payload["validation_result_ids"] == [validation_result.result_id]
    assert payload["runtime_gate_protocol"]["action"] == "create_promotion_packet"


def test_opencode_platform_pre_tool_event_maps_plugin_call_to_gate_policy(tmp_path):
    from brain.v5.adapter_runtime import evaluate_platform_pre_tool_event
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.hook_install_templates import write_opencode_plugin_bridge
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _seed_session(tmp_path)
    packet = build_adapter_packet(ws, "s1", runtime="opencode")
    bridge = {
        "ok": True,
        **write_opencode_plugin_bridge(
            tmp_path / ".opencode" / "AITP_V5_PLUGIN_BRIDGE.md",
            packet["runtime_hook_installation"],
            packet["runtime_gate_protocols"],
        ),
    }

    payload = evaluate_platform_pre_tool_event(
        ws,
        bridge,
        {
            "runtime": "opencode",
            "lifecycle_event": "pre_tool",
            "session_id": "s1",
            "tool": {
                "name": "mcp__aitp__aitp_v5_create_promotion_packet",
                "input": {
                    "topic_id": "fqhe",
                    "claim_id": claim.claim_id,
                    "source_kind": "typed_records",
                },
            },
        },
    )

    assert payload["block"] is True
    assert require_valid_public_surface("pre_tool_policy_decision", payload) == payload
    assert payload["runtime_event"]["runtime"] == "opencode"
    assert payload["runtime_event"]["platform_event"] == "opencode_pre_tool"
    assert payload["runtime_event"]["tool_name"] == "mcp__aitp__aitp_v5_create_promotion_packet"
    assert payload["runtime_gate_protocol"]["action"] == "create_promotion_packet"


def test_opencode_platform_pre_tool_event_reads_nested_promotion_packet_links(tmp_path):
    from brain.v5.adapter_runtime import evaluate_platform_pre_tool_event
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.hook_install_templates import write_opencode_plugin_bridge
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _seed_session(tmp_path)
    evidence, validation_result = _seed_tool_validated_evidence(ws, claim)
    packet = build_adapter_packet(ws, "s1", runtime="opencode")
    bridge = {
        "ok": True,
        **write_opencode_plugin_bridge(
            tmp_path / ".opencode" / "AITP_V5_PLUGIN_BRIDGE.md",
            packet["runtime_hook_installation"],
            packet["runtime_gate_protocols"],
        ),
    }

    payload = evaluate_platform_pre_tool_event(
        ws,
        bridge,
        {
            "runtime": "opencode",
            "lifecycle_event": "pre_tool",
            "session_id": "s1",
            "risk_level": "rigorous",
            "tool": {
                "name": "mcp__aitp__aitp_v5_create_promotion_packet",
                "input": {
                    "source_kind": "typed_records",
                    "packet": {
                        "topic_id": "fqhe",
                        "claim_id": claim.claim_id,
                        "evidence_refs": [evidence.evidence_id],
                        "validation_result_ids": [validation_result.result_id],
                        "known_failure_modes": ["finite-size aliasing"],
                    },
                },
            },
        },
    )

    assert payload["block"] is False
    assert require_valid_public_surface("pre_tool_policy_decision", payload) == payload
    assert payload["claim_id"] == claim.claim_id
    assert payload["evidence_refs"] == [evidence.evidence_id]
    assert payload["validation_result_ids"] == [validation_result.result_id]
    assert payload["runtime_gate_protocol"]["action"] == "create_promotion_packet"


def test_platform_pre_tool_event_blocks_summary_sourced_record_evidence(tmp_path):
    from brain.v5.adapter_runtime import evaluate_platform_pre_tool_event
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.hook_install_templates import write_codex_hook_bridge
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _seed_session(tmp_path)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    bridge = {
        "ok": True,
        **write_codex_hook_bridge(
            tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md",
            packet["runtime_hook_installation"],
            packet["runtime_gate_protocols"],
        ),
    }

    payload = evaluate_platform_pre_tool_event(
        ws,
        bridge,
        {
            "runtime": "codex",
            "hook_name": "pre_tool",
            "session_id": "s1",
            "tool_name": "mcp__aitp__aitp_v5_record_evidence",
            "tool_input": {
                "topic_id": "fqhe",
                "claim_id": claim.claim_id,
                "source_kind": "findings",
                "source_ref": ".aitp/surfaces/session_summaries/s1/findings.md",
                "orientation_only": True,
            },
        },
    )

    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "record_evidence"
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]
    assert require_valid_public_surface("pre_tool_policy_decision", payload) == payload
