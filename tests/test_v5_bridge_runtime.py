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
