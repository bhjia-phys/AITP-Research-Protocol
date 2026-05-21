from __future__ import annotations

import json


def _seed_session(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The modified self-energy kernel preserves the Si GW benchmark invariant.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="formula-code translation may be wrong",
    )
    record_evidence(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        evidence_type="code_method",
        status="supports",
        summary="A local benchmark log exists, but code-state provenance is still incomplete.",
        supports_outputs=["evidence_or_provenance"],
    )
    bind_session(
        ws,
        "s1",
        topic_id="librpa-gw",
        context_id="gw-methods",
        runtime="codex",
        active_claim=claim.claim_id,
    )
    return ws, claim


def _invoke(args, capsys):
    from brain.v5.cli import main

    assert main(args) == 0
    output = capsys.readouterr().out
    return json.loads(output)


def test_adapter_packet_includes_orientation_summaries_and_trusted_brief(tmp_path):
    from brain.v5.adapters import build_adapter_packet

    ws, claim = _seed_session(tmp_path)

    packet = build_adapter_packet(ws, "s1", runtime="codex")

    assert packet["runtime"] == "codex"
    assert packet["session_id"] == "s1"
    assert packet["truth_sources"] == ["typed_records", "execution_brief"]
    assert packet["summary_orientation"]["truth_source"] is False
    assert packet["summary_orientation"]["orientation_only"] is True
    assert packet["execution_brief"]["current_focus"]["active_claim"] == claim.claim_id
    assert packet["trusted_focus"]["claim_statement"] == claim.statement
    assert "record_code_state" in packet["trust_changing_actions"]
    assert "change_claim_confidence" in packet["trust_changing_actions"]
    assert "ingest_subagent_result" in packet["trust_changing_actions"]
    assert "record_physics_object" in packet["trust_changing_actions"]
    assert "record_object_relation" in packet["trust_changing_actions"]
    assert "create_validation_contract" in packet["trust_changing_actions"]
    assert "request_human_checkpoint" in packet["trust_changing_actions"]
    assert "decide_human_checkpoint" in packet["trust_changing_actions"]
    assert "create_promotion_packet" in packet["trust_changing_actions"]
    assert "apply_promotion_packet" in packet["trust_changing_actions"]
    assert "aitp_v5_get_execution_brief" in packet["required_kernel_entrypoints"]
    assert "aitp_v5_evaluate_pre_tool_policy" in packet["required_kernel_entrypoints"]
    assert "aitp_v5_preflight_trust_update" in packet["required_kernel_entrypoints"]
    assert "aitp_v5_apply_trust_update" in packet["required_kernel_entrypoints"]
    assert packet["trust_mutation_entrypoints"]["change_claim_confidence"] == {
        "preflight": "aitp_v5_preflight_trust_update",
        "apply": "aitp_v5_apply_trust_update",
    }
    assert packet["runtime_trust_update_protocol"]["change_claim_confidence"] == {
        "sequence": [
            "refresh_execution_brief",
            "preflight_trust_update",
            "apply_trust_update",
            "refresh_execution_brief",
            "write_session_summary",
        ],
        "preflight": "aitp_v5_preflight_trust_update",
        "apply": "aitp_v5_apply_trust_update",
        "refresh": ["aitp_v5_get_execution_brief", "aitp_v5_write_session_summary"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    }
    assert packet["runtime_gate_protocols"]["validate_claim"]["pre_tool_policy"] == "aitp_v5_evaluate_pre_tool_policy"
    assert packet["runtime_gate_protocols"]["validate_claim"]["sequence"][1] == "evaluate_pre_tool_policy"
    assert packet["runtime_gate_protocols"]["validate_claim"]["policy_reasons_field"] == "policy_reasons"
    assert packet["runtime_gate_protocols"]["promote_to_l2"]["pre_tool_policy"] == "aitp_v5_evaluate_pre_tool_policy"
    assert packet["runtime_gate_protocols"]["promote_to_l2"]["sequence"][1] == "evaluate_pre_tool_policy"
    assert packet["runtime_gate_protocols"]["promote_to_l2"]["policy_reasons_field"] == "policy_reasons"
    assert packet["runtime_record_protocols"]["record_evidence"] == {
        "entrypoint": "aitp_v5_record_evidence",
        "sequence": [
            "refresh_execution_brief",
            "record_evidence",
            "refresh_execution_brief",
            "write_session_summary",
        ],
        "required_typed_refs": ["topic_id", "claim_id"],
        "accepted_link_fields": ["source_refs", "tool_run_ids", "artifact_ids"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    }
    assert packet["runtime_record_protocols"]["record_tool_run"] == {
        "entrypoint": "aitp_v5_record_tool_run",
        "sequence": [
            "refresh_execution_brief",
            "record_tool_run",
            "refresh_execution_brief",
            "write_session_summary",
        ],
        "required_typed_refs": ["topic_id", "claim_id", "recipe_id"],
        "accepted_link_fields": ["code_state_ids", "artifact_ids", "source_refs"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    }
    assert packet["runtime_record_protocols"]["ingest_subagent_result"] == {
        "entrypoint": "aitp_v5_ingest_subagent_result",
        "sequence": [
            "refresh_execution_brief",
            "ingest_subagent_result",
            "refresh_execution_brief",
            "write_session_summary",
        ],
        "required_typed_refs": ["topic_id", "claim_id", "packet_id"],
        "accepted_link_fields": ["evidence_refs", "code_state_refs", "proposed_next_actions"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    }
    assert packet["runtime_gate_protocols"]["validate_claim"] == {
        "pre_tool_policy": "aitp_v5_evaluate_pre_tool_policy",
        "preflight": "aitp_v5_preflight_trust_update",
        "sequence": [
            "refresh_execution_brief",
            "evaluate_pre_tool_policy",
            "preflight_trust_update",
            "record_validation_evidence",
            "refresh_execution_brief",
            "write_session_summary",
        ],
        "required_typed_refs": ["topic_id", "claim_id", "evidence_refs"],
        "allowed_state_sources": ["typed_evidence_records", "typed_validation_records"],
        "policy_reasons_field": "policy_reasons",
        "human_checkpoint_required": False,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    }
    assert packet["runtime_gate_protocols"]["promote_to_l2"] == {
        "pre_tool_policy": "aitp_v5_evaluate_pre_tool_policy",
        "preflight": "aitp_v5_preflight_trust_update",
        "sequence": [
            "refresh_execution_brief",
            "evaluate_pre_tool_policy",
            "preflight_trust_update",
            "human_checkpoint",
            "promote_to_l2",
        ],
        "required_typed_refs": ["topic_id", "claim_id", "evidence_refs", "validation_result_ref"],
        "allowed_state_sources": ["typed_evidence_records", "typed_validation_records", "human_checkpoint"],
        "policy_reasons_field": "policy_reasons",
        "human_checkpoint_required": True,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    }
    assert packet["runtime_gate_protocols"]["record_evidence"] == {
        "pre_tool_policy": "aitp_v5_evaluate_pre_tool_policy",
        "preflight": "",
        "sequence": [
            "refresh_execution_brief",
            "evaluate_pre_tool_policy",
            "record_evidence",
            "refresh_execution_brief",
            "write_session_summary",
        ],
        "required_typed_refs": ["topic_id", "claim_id"],
        "allowed_state_sources": ["typed_records", "typed_evidence_records"],
        "policy_reasons_field": "policy_reasons",
        "human_checkpoint_required": False,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    }
    assert packet["runtime_gate_protocols"]["record_tool_run"] == {
        "pre_tool_policy": "aitp_v5_evaluate_pre_tool_policy",
        "preflight": "",
        "sequence": [
            "refresh_execution_brief",
            "evaluate_pre_tool_policy",
            "record_tool_run",
            "refresh_execution_brief",
            "write_session_summary",
        ],
        "required_typed_refs": ["topic_id", "claim_id", "recipe_id"],
        "allowed_state_sources": ["typed_records", "typed_tool_run_records"],
        "policy_reasons_field": "policy_reasons",
        "human_checkpoint_required": False,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    }
    assert "read_for_orientation" in packet["runtime_rules"][0]


def test_adapter_packet_protocols_are_generated_from_shared_registry(tmp_path):
    from brain.v5.adapter_protocols import build_adapter_protocols, supported_runtimes
    from brain.v5.adapters import build_adapter_packet

    ws, _ = _seed_session(tmp_path)

    packet = build_adapter_packet(ws, "s1", runtime="codex")
    protocols = build_adapter_protocols()

    assert set(supported_runtimes()) == {"codex", "claude_code", "opencode"}
    for key, value in protocols.items():
        assert packet[key] == value


def test_adapter_packet_exposes_hook_protocols_for_runtime_installers(tmp_path):
    from brain.v5.adapters import build_adapter_packet

    ws, _ = _seed_session(tmp_path)

    packet = build_adapter_packet(ws, "s1", runtime="codex")

    protocols = packet["runtime_hook_protocols"]
    assert set(protocols) == {"pre_commit", "pre_tool", "post_tool"}
    assert protocols["pre_commit"] == {
        "lifecycle_event": "pre_commit",
        "command": ["python", "hooks/aitp_v5_hook.py", "pre-commit"],
        "required_inputs": ["changed_files", "test_refs", "evolution_note"],
        "output_kind": "hook_decision",
        "may_block": True,
        "block_exit_code": 2,
        "state_mutation": "none",
        "summary_inputs_trusted": False,
    }
    assert protocols["pre_tool"]["command"] == ["python", "hooks/aitp_v5_hook.py", "pre-tool"]
    assert protocols["pre_tool"]["required_inputs"] == ["action", "risk_level", "policy_json"]
    assert protocols["pre_tool"]["may_block"] is True
    assert protocols["pre_tool"]["summary_inputs_trusted"] is False
    assert protocols["post_tool"] == {
        "lifecycle_event": "post_tool",
        "command": ["python", "hooks/aitp_v5_hook.py", "post-tool"],
        "required_inputs": ["session_id", "topic_id", "claim_id", "risk_level", "tool_name", "evidence_status"],
        "output_kind": "hook_trace_event",
        "may_block": False,
        "block_exit_code": 0,
        "state_mutation": "trace_event_output_only",
        "summary_inputs_trusted": False,
    }


def test_codex_adapter_packet_builds_hook_installation_from_hook_protocols(tmp_path):
    from brain.v5.adapters import build_adapter_packet

    ws, _ = _seed_session(tmp_path)

    packet = build_adapter_packet(ws, "s1", runtime="codex")

    installation = packet["runtime_hook_installation"]
    assert installation["kind"] == "runtime_hook_installation_template"
    assert installation["runtime"] == "codex"
    assert installation["source_protocol_field"] == "runtime_hook_protocols"
    assert installation["installation_mode"] == "explicit_guard_calls"
    assert installation["native_installer_available"] is False
    assert installation["summary_inputs_trusted"] is False

    protocols = packet["runtime_hook_protocols"]
    hooks = {hook["hook_name"]: hook for hook in installation["hooks"]}
    assert set(hooks) == set(protocols)
    for hook_name, protocol in protocols.items():
        hook = hooks[hook_name]
        assert hook["command"] == protocol["command"]
        assert hook["required_inputs"] == protocol["required_inputs"]
        assert hook["output_kind"] == protocol["output_kind"]
        assert hook["may_block"] == protocol["may_block"]
        assert hook["state_mutation"] == protocol["state_mutation"]


def test_codex_hook_bridge_is_rendered_from_installation_template(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.hook_install_templates import write_codex_hook_bridge

    ws, _ = _seed_session(tmp_path)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    installation = packet["runtime_hook_installation"]
    installation["hooks"][0]["command"] = ["python", "custom_hook.py", "pre-commit"]

    bridge_path = tmp_path / "AITP_V5_HOOK_BRIDGE.md"
    bridge = write_codex_hook_bridge(bridge_path, installation)

    assert bridge["kind"] == "codex_hook_bridge"
    assert bridge["runtime"] == "codex"
    assert bridge["source_protocol_field"] == "runtime_hook_installation"
    assert bridge["summary_inputs_trusted"] is False
    assert bridge["can_update_kernel_state"] is False
    assert bridge["pre_tool_policy_entrypoint"]["cli"] == "aitp-v5 policy pre-tool <args>"
    assert bridge["pre_tool_policy_entrypoint"]["mcp"] == "aitp_v5_evaluate_pre_tool_policy"
    assert bridge["pre_tool_policy_entrypoint"]["surface"] == "pre_tool_policy_decision"
    assert bridge["path"] == str(bridge_path)
    assert bridge["guard_calls"][0]["hook_name"] == "pre_commit"
    assert bridge["guard_calls"][0]["command"] == "python custom_hook.py pre-commit"
    text = bridge_path.read_text(encoding="utf-8")
    assert "python custom_hook.py pre-commit" in text
    assert "aitp-v5 policy pre-tool" in text
    assert "runtime_hook_installation" in text
    assert "summary_inputs_trusted=false" in text


def test_cli_adapter_hook_bridge_writes_codex_bridge_from_packet(tmp_path, capsys):
    _seed_session(tmp_path)

    bridge_path = tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"
    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "hook-bridge",
            "codex",
            "s1",
            "--output",
            str(bridge_path),
        ],
        capsys,
    )

    assert payload["ok"] is True
    assert payload["kind"] == "codex_hook_bridge"
    assert payload["runtime"] == "codex"
    assert payload["source_protocol_field"] == "runtime_hook_installation"
    assert payload["summary_inputs_trusted"] is False
    assert payload["can_update_kernel_state"] is False
    assert payload["pre_tool_policy_entrypoint"]["surface"] == "pre_tool_policy_decision"
    assert payload["pre_tool_policy_entrypoint"]["input_schema"]["required"] == [
        "session_id",
        "action",
        "claim_id",
        "risk_level",
    ]
    assert "human_checkpoint_id" in payload["pre_tool_policy_entrypoint"]["input_schema"]["optional"]
    assert payload["pre_tool_event_entrypoint"]["platform_event_schema"]["tool_input_optional"] == [
        "claim_id",
        "evidence_refs",
        "code_state_ids",
        "packet",
        "source_kind",
        "source_ref",
        "orientation_only",
        "risk_level",
        "human_checkpoint_id",
        "checkpoint_id",
    ]
    assert payload["pre_tool_event_entrypoint"] == {
        "cli": "aitp-v5 adapter pre-tool-event <runtime> <session-id> <args>",
        "mcp": "aitp_v5_evaluate_adapter_pre_tool_event",
        "surface": "pre_tool_policy_decision",
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "requires_bridge_payload": True,
        "requires_platform_event": True,
        "platform_event_schema": {
            "required": ["runtime", "session_id"],
            "hook_field": "hook_name_or_lifecycle_event",
            "tool_name_fields": ["tool_name", "tool.name"],
            "tool_input_fields": ["tool_input", "tool.input"],
            "tool_input_optional": [
                "claim_id",
                "evidence_refs",
                "code_state_ids",
                "packet",
                "source_kind",
                "source_ref",
                "orientation_only",
                "risk_level",
                "human_checkpoint_id",
                "checkpoint_id",
            ],
            "truth_source": "platform_event_for_routing_only",
            "summary_inputs_trusted": False,
        },
    }
    assert payload["gate_protocols"]["source_protocol_field"] == "runtime_gate_protocols"
    assert payload["gate_protocols"]["validate_claim"]["pre_tool_policy"] == "aitp_v5_evaluate_pre_tool_policy"
    assert payload["gate_protocols"]["validate_claim"]["sequence"][1] == "evaluate_pre_tool_policy"
    assert payload["gate_protocols"]["validate_claim"]["policy_reasons_field"] == "policy_reasons"
    assert payload["gate_protocols"]["promote_to_l2"]["pre_tool_policy"] == "aitp_v5_evaluate_pre_tool_policy"
    assert payload["gate_protocols"]["record_evidence"]["sequence"][1] == "evaluate_pre_tool_policy"
    assert payload["gate_protocols"]["record_tool_run"]["policy_reasons_field"] == "policy_reasons"
    assert payload["path"] == str(bridge_path)
    assert payload["payload_path"] == str(bridge_path.with_suffix(".json"))
    assert payload["pre_tool_event_runner"]["argv"] == [
        "aitp-v5",
        "adapter",
        "pre-tool-event",
        "codex",
        "s1",
        "--bridge-path",
        str(bridge_path.with_suffix(".json")),
        "--event-json",
        "<platform-event-json>",
    ]
    assert payload["pre_tool_event_runner"]["summary_inputs_trusted"] is False
    assert payload["pre_tool_event_runner"]["stdin_runner"]["argv"] == [
        "python",
        "hooks/aitp_v5_adapter_event_runner.py",
        "pre-tool",
        "--base",
        "<workspace>",
        "--runtime",
        "codex",
        "--session-id",
        "s1",
        "--bridge-path",
        str(bridge_path.with_suffix(".json")),
    ]
    assert payload["pre_tool_event_runner"]["stdin_runner"]["stdin"] == "<platform-event-json>"
    assert [call["hook_name"] for call in payload["guard_calls"]] == ["pre_commit", "pre_tool", "post_tool"]
    sidecar = json.loads(bridge_path.with_suffix(".json").read_text(encoding="utf-8"))
    assert sidecar["kind"] == "codex_hook_bridge"
    assert sidecar["path"] == str(bridge_path)
    assert sidecar["pre_tool_event_runner"]["bridge_payload_source"] == "payload_path"
    assert sidecar["pre_tool_event_entrypoint"]["mcp"] == "aitp_v5_evaluate_adapter_pre_tool_event"
    assert sidecar["pre_tool_policy_entrypoint"]["input_schema"]["optional"][-1] == "human_checkpoint_id"
    text = bridge_path.read_text(encoding="utf-8")
    assert "Generated from `runtime_hook_installation`." in text
    assert "python hooks/aitp_v5_hook.py pre-tool" in text
    assert "aitp-v5 policy pre-tool" in text
    assert "evaluate_pre_tool_policy" in text
    assert f"--bridge-path {bridge_path.with_suffix('.json')}" in text
    assert "hooks/aitp_v5_adapter_event_runner.py" in text
    assert "human_checkpoint_id" in text


def test_mcp_codex_hook_bridge_wrapper_returns_contract_payload(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_write_codex_hook_bridge

    _seed_session(tmp_path)

    bridge_path = tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"
    payload = aitp_v5_write_codex_hook_bridge(
        str(tmp_path),
        session_id="s1",
        output_path=str(bridge_path),
    )

    assert payload["ok"] is True
    assert payload["kind"] == "codex_hook_bridge"
    assert payload["summary_inputs_trusted"] is False
    assert payload["gate_protocols"]["validate_claim"]["pre_tool_policy"] == "aitp_v5_evaluate_pre_tool_policy"
    assert payload["pre_tool_event_runner"]["argv"][4] == "s1"
    assert payload["pre_tool_event_runner"]["argv"][6] == str(bridge_path.with_suffix(".json"))
    assert payload["pre_tool_event_runner"]["stdin_runner"]["argv"][8] == "s1"
    assert bridge_path.exists()


def test_cli_adapter_install_hooks_writes_codex_stdin_runner_fixture(tmp_path, capsys):
    _seed_session(tmp_path)

    fixture_path = tmp_path / ".codex" / "AITP_V5_HOOKS.json"
    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "install-hooks",
            "codex",
            "s1",
            "--output",
            str(fixture_path),
        ],
        capsys,
    )

    assert payload["ok"] is True
    assert payload["kind"] == "codex_hook_installation"
    assert payload["runtime"] == "codex"
    assert payload["summary_inputs_trusted"] is False
    assert payload["can_update_kernel_state"] is False
    assert payload["path"] == str(fixture_path)
    assert payload["bridge"]["kind"] == "codex_hook_bridge"
    assert payload["bridge"]["payload_path"] == str(fixture_path.parent / "AITP_V5_HOOK_BRIDGE.json")
    assert payload["fixture"]["hooks"]["pre_tool"]["stdin"] == "<platform-event-json>"
    assert payload["fixture"]["hooks"]["pre_tool"]["argv"][1] == "hooks/aitp_v5_adapter_event_runner.py"
    assert payload["fixture"]["hooks"]["pre_tool"]["argv"][8] == "s1"
    assert payload["fixture"]["hooks"]["pre_tool"]["argv"][10] == payload["bridge"]["payload_path"]

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert fixture == payload["fixture"]
    assert (fixture_path.parent / "AITP_V5_HOOK_BRIDGE.md").exists()
    assert (fixture_path.parent / "AITP_V5_HOOK_BRIDGE.json").exists()


def test_mcp_codex_hook_installer_returns_contract_payload(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_install_codex_hook_fixture

    _seed_session(tmp_path)

    fixture_path = tmp_path / ".codex" / "AITP_V5_HOOKS.json"
    payload = aitp_v5_install_codex_hook_fixture(
        str(tmp_path),
        session_id="s1",
        output_path=str(fixture_path),
    )

    assert payload["ok"] is True
    assert payload["kind"] == "codex_hook_installation"
    assert payload["fixture"]["hooks"]["pre_tool"]["argv"][6] == "codex"
    assert payload["fixture"]["hooks"]["pre_tool"]["argv"][10] == payload["bridge"]["payload_path"]
    assert fixture_path.exists()


def test_cli_adapter_pre_tool_event_evaluates_platform_payload(tmp_path, capsys):
    _, claim = _seed_session(tmp_path)
    bridge_path = tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"
    bridge = _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "hook-bridge",
            "codex",
            "s1",
            "--output",
            str(bridge_path),
        ],
        capsys,
    )

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "pre-tool-event",
            "codex",
            "s1",
            "--bridge-path",
            bridge["payload_path"],
            "--event-json",
            json.dumps(
                {
                    "runtime": "codex",
                    "hook_name": "pre_tool",
                    "session_id": "s1",
                    "tool_name": "mcp__aitp__aitp_v5_record_evidence",
                    "tool_input": {
                        "topic_id": "librpa-gw",
                        "claim_id": claim.claim_id,
                        "source_kind": "findings",
                        "orientation_only": True,
                    },
                }
            ),
        ],
        capsys,
    )

    assert payload["ok"] is True
    assert payload["kind"] == "hook_decision"
    assert payload["action"] == "record_evidence"
    assert payload["block"] is True
    assert payload["runtime_event"]["platform_event"] == "codex_pre_tool"
    assert payload["runtime_gate_protocol"]["action"] == "record_evidence"


def test_mcp_adapter_pre_tool_event_evaluates_platform_payload(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge

    _, claim = _seed_session(tmp_path)
    bridge = aitp_v5_write_codex_hook_bridge(
        str(tmp_path),
        session_id="s1",
        output_path=str(tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"),
    )

    payload = aitp_v5_evaluate_adapter_pre_tool_event(
        str(tmp_path),
        bridge_payload=bridge,
        platform_event={
            "runtime": "codex",
            "hook_name": "pre_tool",
            "session_id": "s1",
            "tool_name": "mcp__aitp__aitp_v5_record_evidence",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "source_kind": "findings",
                "orientation_only": True,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "record_evidence"
    assert payload["block"] is True
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_adapter_pre_tool_event_infers_code_state_policy(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge

    _, claim = _seed_session(tmp_path)
    bridge = aitp_v5_write_codex_hook_bridge(
        str(tmp_path),
        session_id="s1",
        output_path=str(tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"),
    )

    payload = aitp_v5_evaluate_adapter_pre_tool_event(
        str(tmp_path),
        bridge_payload=bridge,
        platform_event={
            "runtime": "codex",
            "hook_name": "pre_tool",
            "session_id": "s1",
            "tool_name": "mcp__aitp__aitp_v5_record_code_state",
            "tool_input": {
                "repo_id": "librpa",
                "upstream_commit": "abc123",
                "local_branch": "topic/gw",
                "linked_records": {"claim_id": claim.claim_id},
                "claim_id": claim.claim_id,
                "source_kind": "progress",
                "source_ref": ".aitp/surfaces/session_summaries/s1/progress.md",
                "orientation_only": True,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "record_code_state"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "record_code_state"
    assert payload["runtime_gate_protocol"]["required_typed_refs"] == [
        "repo_id",
        "upstream_commit",
        "local_branch",
    ]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_adapter_pre_tool_event_infers_physics_object_policy(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge

    _, claim = _seed_session(tmp_path)
    bridge = aitp_v5_write_codex_hook_bridge(
        str(tmp_path),
        session_id="s1",
        output_path=str(tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"),
    )

    payload = aitp_v5_evaluate_adapter_pre_tool_event(
        str(tmp_path),
        bridge_payload=bridge,
        platform_event={
            "runtime": "codex",
            "hook_name": "pre_tool",
            "session_id": "s1",
            "tool_name": "mcp__aitp__aitp_v5_record_physics_object",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "object_type": "formula",
                "name": "correlation self-energy",
                "definition": "GW self-energy expression.",
                "source_kind": "findings",
                "source_ref": ".aitp/surfaces/session_summaries/s1/findings.md",
                "orientation_only": True,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "record_physics_object"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "record_physics_object"
    assert payload["runtime_gate_protocol"]["required_typed_refs"] == [
        "topic_id",
        "object_type",
        "name",
        "definition",
    ]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_adapter_pre_tool_event_infers_object_relation_policy(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge

    _, claim = _seed_session(tmp_path)
    bridge = aitp_v5_write_codex_hook_bridge(
        str(tmp_path),
        session_id="s1",
        output_path=str(tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"),
    )

    payload = aitp_v5_evaluate_adapter_pre_tool_event(
        str(tmp_path),
        bridge_payload=bridge,
        platform_event={
            "runtime": "codex",
            "hook_name": "pre_tool",
            "session_id": "s1",
            "tool_name": "mcp__aitp__aitp_v5_record_object_relation",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "relation_type": "implements",
                "subject_id": "object-librpa-kernel",
                "object_id": "object-self-energy-formula",
                "statement": "The kernel implements the formula.",
                "source_kind": "task_plan",
                "source_ref": ".aitp/surfaces/session_summaries/s1/task_plan.md",
                "orientation_only": True,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "record_object_relation"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "record_object_relation"
    assert payload["runtime_gate_protocol"]["required_typed_refs"] == [
        "topic_id",
        "relation_type",
        "subject_id",
        "object_id",
        "statement",
    ]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_adapter_pre_tool_event_infers_execute_tool_policy(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge

    _, claim = _seed_session(tmp_path)
    bridge = aitp_v5_write_codex_hook_bridge(
        str(tmp_path),
        session_id="s1",
        output_path=str(tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"),
    )

    payload = aitp_v5_evaluate_adapter_pre_tool_event(
        str(tmp_path),
        bridge_payload=bridge,
        platform_event={
            "runtime": "codex",
            "hook_name": "pre_tool",
            "session_id": "s1",
            "tool_name": "mcp__aitp__aitp_v5_execute_tool",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "executor_id": "librpa-smoke",
                "source_kind": "progress",
                "source_ref": ".aitp/surfaces/session_summaries/s1/progress.md",
                "orientation_only": True,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "execute_tool"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "execute_tool"
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_adapter_pre_tool_event_infers_subagent_ingestion_policy(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge

    _, claim = _seed_session(tmp_path)
    bridge = aitp_v5_write_codex_hook_bridge(
        str(tmp_path),
        session_id="s1",
        output_path=str(tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"),
    )

    payload = aitp_v5_evaluate_adapter_pre_tool_event(
        str(tmp_path),
        bridge_payload=bridge,
        platform_event={
            "runtime": "codex",
            "hook_name": "pre_tool",
            "session_id": "s1",
            "tool_name": "mcp__aitp__aitp_v5_ingest_subagent_result",
            "tool_input": {
                "topic_id": "librpa-gw",
                "packet": {
                    "packet_id": "packet-critic-si-gw",
                    "packet_type": "CriticPacket",
                    "claim_id": claim.claim_id,
                    "claim_statement": claim.statement,
                },
                "source_kind": "findings",
                "source_ref": ".aitp/surfaces/session_summaries/s1/findings.md",
                "orientation_only": True,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "ingest_subagent_result"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "ingest_subagent_result"
    assert payload["claim_id"] == claim.claim_id
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_adapter_pre_tool_event_infers_validation_contract_policy(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge

    _, claim = _seed_session(tmp_path)
    bridge = aitp_v5_write_codex_hook_bridge(
        str(tmp_path),
        session_id="s1",
        output_path=str(tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"),
    )

    payload = aitp_v5_evaluate_adapter_pre_tool_event(
        str(tmp_path),
        bridge_payload=bridge,
        platform_event={
            "runtime": "codex",
            "hook_name": "pre_tool",
            "session_id": "s1",
            "tool_name": "mcp__aitp__aitp_v5_create_validation_contract",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "required_checks": ["reproduce benchmark"],
                "failure_modes": ["formula-code mismatch"],
                "source_kind": "findings",
                "source_ref": ".aitp/surfaces/session_summaries/s1/findings.md",
                "orientation_only": True,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "create_validation_contract"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "create_validation_contract"
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_adapter_pre_tool_event_infers_promotion_packet_policy(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge

    _, claim = _seed_session(tmp_path)
    bridge = aitp_v5_write_codex_hook_bridge(
        str(tmp_path),
        session_id="s1",
        output_path=str(tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"),
    )

    payload = aitp_v5_evaluate_adapter_pre_tool_event(
        str(tmp_path),
        bridge_payload=bridge,
        platform_event={
            "runtime": "codex",
            "hook_name": "pre_tool",
            "session_id": "s1",
            "tool_name": "mcp__aitp__aitp_v5_create_promotion_packet",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "proposed_memory_kind": "method_note",
                "scope": "Si GW benchmark invariant",
                "evidence_refs": ["evidence-librpa-gw-benchmark"],
                "source_kind": "findings",
                "source_ref": ".aitp/surfaces/session_summaries/s1/findings.md",
                "orientation_only": True,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "create_promotion_packet"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "create_promotion_packet"
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_adapter_pre_tool_event_infers_apply_promotion_packet_policy(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge

    _, claim = _seed_session(tmp_path)
    bridge = aitp_v5_write_codex_hook_bridge(
        str(tmp_path),
        session_id="s1",
        output_path=str(tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"),
    )

    payload = aitp_v5_evaluate_adapter_pre_tool_event(
        str(tmp_path),
        bridge_payload=bridge,
        platform_event={
            "runtime": "codex",
            "hook_name": "pre_tool",
            "session_id": "s1",
            "tool_name": "mcp__aitp__aitp_v5_apply_promotion_packet",
            "tool_input": {
                "packet_id": "packet-librpa-gw-benchmark",
                "checkpoint_id": "checkpoint-human-approval",
                "claim_id": claim.claim_id,
                "source_kind": "findings",
                "source_ref": ".aitp/surfaces/session_summaries/s1/findings.md",
                "orientation_only": True,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "apply_promotion_packet"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "apply_promotion_packet"
    assert payload["runtime_gate_protocol"]["human_checkpoint_required"] is True
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_adapter_pre_tool_event_passes_adversarial_checkpoint_context(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge

    ws, claim = _seed_session(tmp_path)
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        reason="Adversarial evidence recording needs human checkpoint",
        requested_by="risk_policy",
        options=["approve", "reject"],
    )
    decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="The source is a typed record path.",
        decided_by="human",
    )
    bridge = aitp_v5_write_codex_hook_bridge(
        str(tmp_path),
        session_id="s1",
        output_path=str(tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"),
    )

    payload = aitp_v5_evaluate_adapter_pre_tool_event(
        str(tmp_path),
        bridge_payload=bridge,
        platform_event={
            "runtime": "codex",
            "hook_name": "pre_tool",
            "session_id": "s1",
            "risk_level": "adversarial",
            "tool_name": "mcp__aitp__aitp_v5_record_evidence",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "source_kind": "typed_records",
                "human_checkpoint_id": checkpoint.checkpoint_id,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "record_evidence"
    assert payload["risk_level"] == "adversarial"
    assert payload["human_checkpoint_id"] == checkpoint.checkpoint_id
    assert payload["block"] is False
    assert payload["policy_reasons"] == []


def test_mcp_adapter_pre_tool_event_infers_human_checkpoint_request_policy(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge

    _, claim = _seed_session(tmp_path)
    bridge = aitp_v5_write_codex_hook_bridge(
        str(tmp_path),
        session_id="s1",
        output_path=str(tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"),
    )

    payload = aitp_v5_evaluate_adapter_pre_tool_event(
        str(tmp_path),
        bridge_payload=bridge,
        platform_event={
            "runtime": "codex",
            "hook_name": "pre_tool",
            "session_id": "s1",
            "tool_name": "mcp__aitp__aitp_v5_request_human_checkpoint",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "reason": "A summary suggested applying a promotion packet.",
                "requested_by": "codex",
                "source_kind": "task_plan",
                "source_ref": ".aitp/surfaces/session_summaries/s1/task_plan.md",
                "orientation_only": True,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "request_human_checkpoint"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "request_human_checkpoint"
    assert payload["runtime_gate_protocol"]["human_checkpoint_required"] is False
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_adapter_pre_tool_event_infers_human_checkpoint_decision_policy(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge

    _, claim = _seed_session(tmp_path)
    bridge = aitp_v5_write_codex_hook_bridge(
        str(tmp_path),
        session_id="s1",
        output_path=str(tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"),
    )

    payload = aitp_v5_evaluate_adapter_pre_tool_event(
        str(tmp_path),
        bridge_payload=bridge,
        platform_event={
            "runtime": "codex",
            "hook_name": "pre_tool",
            "session_id": "s1",
            "tool_name": "mcp__aitp__aitp_v5_decide_human_checkpoint",
            "tool_input": {
                "checkpoint_id": "checkpoint-human-approval",
                "claim_id": claim.claim_id,
                "decision": "approve",
                "rationale": "The findings summary says this is ready.",
                "decided_by": "codex",
                "source_kind": "findings",
                "source_ref": ".aitp/surfaces/session_summaries/s1/findings.md",
                "orientation_only": True,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "decide_human_checkpoint"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "decide_human_checkpoint"
    assert payload["runtime_gate_protocol"]["human_checkpoint_required"] is False
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_opencode_plugin_bridge_is_rendered_from_installation_template(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.hook_install_templates import write_opencode_plugin_bridge

    ws, _ = _seed_session(tmp_path)
    packet = build_adapter_packet(ws, "s1", runtime="opencode")
    bridge_path = tmp_path / ".opencode" / "AITP_V5_PLUGIN_BRIDGE.md"
    bridge = write_opencode_plugin_bridge(bridge_path, packet["runtime_hook_installation"])

    assert bridge["kind"] == "opencode_plugin_bridge"
    assert bridge["runtime"] == "opencode"
    assert bridge["source_protocol_field"] == "runtime_hook_installation"
    assert bridge["installation_mode"] == "plugin_bridge"
    assert bridge["summary_inputs_trusted"] is False
    assert bridge["can_update_kernel_state"] is False
    assert bridge["can_update_claim_trust"] is False
    assert bridge["plugin_bridge"]["pre_tool_policy_entrypoint"]["cli"] == "aitp-v5 policy pre-tool <args>"
    assert bridge["plugin_bridge"]["pre_tool_policy_entrypoint"]["mcp"] == "aitp_v5_evaluate_pre_tool_policy"
    assert bridge["plugin_bridge"]["pre_tool_policy_entrypoint"]["surface"] == "pre_tool_policy_decision"
    assert bridge["plugin_bridge"]["pre_tool_policy_entrypoint"]["input_schema"]["required"] == [
        "session_id",
        "action",
        "claim_id",
        "risk_level",
    ]
    assert "human_checkpoint_id" in bridge["plugin_bridge"]["pre_tool_policy_entrypoint"]["input_schema"]["optional"]
    assert "human_checkpoint_id" in bridge["plugin_bridge"]["pre_tool_event_entrypoint"]["platform_event_schema"][
        "tool_input_optional"
    ]
    assert "checkpoint_id" in bridge["plugin_bridge"]["pre_tool_event_entrypoint"]["platform_event_schema"][
        "tool_input_optional"
    ]
    assert "packet" in bridge["plugin_bridge"]["pre_tool_event_entrypoint"]["platform_event_schema"]["tool_input_optional"]
    assert bridge["path"] == str(bridge_path)
    assert bridge["payload_path"] == str(bridge_path.with_suffix(".json"))
    assert bridge["plugin_bridge"]["pre_tool_event_runner"]["argv"] == [
        "aitp-v5",
        "adapter",
        "pre-tool-event",
        "opencode",
        "<session-id>",
        "--bridge-path",
        str(bridge_path.with_suffix(".json")),
        "--event-json",
        "<platform-event-json>",
    ]
    assert bridge["plugin_bridge"]["pre_tool_event_runner"]["stdin_runner"]["argv"] == [
        "python",
        "hooks/aitp_v5_adapter_event_runner.py",
        "pre-tool",
        "--base",
        "<workspace>",
        "--runtime",
        "opencode",
        "--session-id",
        "<session-id>",
        "--bridge-path",
        str(bridge_path.with_suffix(".json")),
    ]
    assert [call["hook_name"] for call in bridge["plugin_bridge"]["lifecycle_calls"]] == [
        "pre_commit",
        "pre_tool",
        "post_tool",
    ]
    sidecar = json.loads(bridge_path.with_suffix(".json").read_text(encoding="utf-8"))
    assert sidecar["kind"] == "opencode_plugin_bridge"
    assert sidecar["path"] == str(bridge_path)
    assert sidecar["plugin_bridge"]["pre_tool_event_runner"]["bridge_payload_source"] == "payload_path"
    assert sidecar["plugin_bridge"]["pre_tool_event_entrypoint"]["mcp"] == "aitp_v5_evaluate_adapter_pre_tool_event"
    assert "checkpoint_id" in sidecar["plugin_bridge"]["pre_tool_event_entrypoint"]["platform_event_schema"][
        "tool_input_optional"
    ]
    text = bridge_path.read_text(encoding="utf-8")
    assert "Generated from `runtime_hook_installation`." in text
    assert "aitp_v5_persist_hook_trace_event" in text
    assert "aitp-v5 policy pre-tool" in text
    assert "summary_inputs_trusted=false" in text
    assert f"--bridge-path {bridge_path.with_suffix('.json')}" in text
    assert "hooks/aitp_v5_adapter_event_runner.py" in text
    assert "human_checkpoint_id" in text


def test_cli_adapter_hook_bridge_writes_opencode_bridge_from_packet(tmp_path, capsys):
    _seed_session(tmp_path)

    bridge_path = tmp_path / ".opencode" / "AITP_V5_PLUGIN_BRIDGE.md"
    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "hook-bridge",
            "opencode",
            "s1",
            "--output",
            str(bridge_path),
        ],
        capsys,
    )

    assert payload["ok"] is True
    assert payload["kind"] == "opencode_plugin_bridge"
    assert payload["runtime"] == "opencode"
    assert payload["plugin_bridge"]["lifecycle_calls"][1]["hook_name"] == "pre_tool"
    assert payload["plugin_bridge"]["pre_tool_policy_entrypoint"]["surface"] == "pre_tool_policy_decision"
    assert payload["plugin_bridge"]["pre_tool_event_runner"]["argv"][4] == "s1"
    assert payload["plugin_bridge"]["pre_tool_event_runner"]["argv"][6] == str(bridge_path.with_suffix(".json"))
    assert payload["plugin_bridge"]["pre_tool_event_runner"]["stdin_runner"]["argv"][8] == "s1"
    assert payload["plugin_bridge"]["pre_tool_event_entrypoint"] == {
        "cli": "aitp-v5 adapter pre-tool-event <runtime> <session-id> <args>",
        "mcp": "aitp_v5_evaluate_adapter_pre_tool_event",
        "surface": "pre_tool_policy_decision",
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "requires_bridge_payload": True,
        "requires_platform_event": True,
        "platform_event_schema": {
            "required": ["runtime", "session_id"],
            "hook_field": "hook_name_or_lifecycle_event",
            "tool_name_fields": ["tool_name", "tool.name"],
            "tool_input_fields": ["tool_input", "tool.input"],
            "tool_input_optional": [
                "claim_id",
                "evidence_refs",
                "code_state_ids",
                "packet",
                "source_kind",
                "source_ref",
                "orientation_only",
                "risk_level",
                "human_checkpoint_id",
                "checkpoint_id",
            ],
            "truth_source": "platform_event_for_routing_only",
            "summary_inputs_trusted": False,
        },
    }
    assert payload["plugin_bridge"]["gate_protocols"]["source_protocol_field"] == "runtime_gate_protocols"
    assert payload["plugin_bridge"]["gate_protocols"]["validate_claim"]["sequence"][1] == "evaluate_pre_tool_policy"
    assert payload["plugin_bridge"]["gate_protocols"]["promote_to_l2"]["policy_reasons_field"] == "policy_reasons"
    assert payload["plugin_bridge"]["gate_protocols"]["record_evidence"]["pre_tool_policy"] == "aitp_v5_evaluate_pre_tool_policy"
    assert payload["plugin_bridge"]["gate_protocols"]["record_tool_run"]["sequence"][1] == "evaluate_pre_tool_policy"
    assert bridge_path.exists()
    assert "evaluate_pre_tool_policy" in bridge_path.read_text(encoding="utf-8")


def test_mcp_opencode_plugin_bridge_wrapper_returns_contract_payload(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_write_opencode_plugin_bridge

    _seed_session(tmp_path)

    bridge_path = tmp_path / ".opencode" / "AITP_V5_PLUGIN_BRIDGE.md"
    payload = aitp_v5_write_opencode_plugin_bridge(
        str(tmp_path),
        session_id="s1",
        output_path=str(bridge_path),
    )

    assert payload["ok"] is True
    assert payload["kind"] == "opencode_plugin_bridge"
    assert payload["plugin_bridge"]["persistence_entrypoint"] == "aitp_v5_persist_hook_trace_event"
    assert payload["plugin_bridge"]["gate_protocols"]["validate_claim"]["pre_tool_policy"] == "aitp_v5_evaluate_pre_tool_policy"
    assert bridge_path.exists()


def test_cli_adapter_install_hooks_writes_opencode_stdin_runner_fixture(tmp_path, capsys):
    _seed_session(tmp_path)

    fixture_path = tmp_path / ".opencode" / "AITP_V5_PLUGIN_HOOKS.json"
    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "install-hooks",
            "opencode",
            "s1",
            "--output",
            str(fixture_path),
        ],
        capsys,
    )

    assert payload["ok"] is True
    assert payload["kind"] == "opencode_hook_installation"
    assert payload["runtime"] == "opencode"
    assert payload["summary_inputs_trusted"] is False
    assert payload["can_update_kernel_state"] is False
    assert payload["path"] == str(fixture_path)
    assert payload["bridge"]["kind"] == "opencode_plugin_bridge"
    assert payload["bridge_payload_path"] == str(fixture_path.parent / "AITP_V5_PLUGIN_BRIDGE.json")
    assert payload["fixture"]["plugin_hooks"]["pre_tool"]["stdin"] == "<platform-event-json>"
    assert payload["fixture"]["plugin_hooks"]["pre_tool"]["argv"][1] == "hooks/aitp_v5_adapter_event_runner.py"
    assert payload["fixture"]["plugin_hooks"]["pre_tool"]["argv"][6] == "opencode"
    assert payload["fixture"]["plugin_hooks"]["pre_tool"]["argv"][8] == "s1"
    assert payload["fixture"]["plugin_hooks"]["pre_tool"]["argv"][10] == payload["bridge_payload_path"]

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert fixture == payload["fixture"]
    assert (fixture_path.parent / "AITP_V5_PLUGIN_BRIDGE.md").exists()
    assert (fixture_path.parent / "AITP_V5_PLUGIN_BRIDGE.json").exists()


def test_mcp_opencode_hook_installer_returns_contract_payload(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_install_opencode_hook_fixture

    _seed_session(tmp_path)

    fixture_path = tmp_path / ".opencode" / "AITP_V5_PLUGIN_HOOKS.json"
    payload = aitp_v5_install_opencode_hook_fixture(
        str(tmp_path),
        session_id="s1",
        output_path=str(fixture_path),
    )

    assert payload["ok"] is True
    assert payload["kind"] == "opencode_hook_installation"
    assert payload["fixture"]["plugin_hooks"]["pre_tool"]["argv"][6] == "opencode"
    assert payload["fixture"]["plugin_hooks"]["pre_tool"]["argv"][10] == payload["bridge_payload_path"]
    assert fixture_path.exists()


def test_cli_adapter_hook_settings_writes_claude_code_settings_from_packet(tmp_path, capsys):
    _seed_session(tmp_path)

    settings_path = tmp_path / ".claude" / "settings.local.json"
    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "hook-settings",
            "claude-code",
            "s1",
            "--output",
            str(settings_path),
        ],
        capsys,
    )

    assert payload["ok"] is True
    assert payload["kind"] == "claude_code_hook_settings"
    assert payload["runtime"] == "claude_code"
    assert payload["source_protocol_field"] == "runtime_hook_installation"
    assert payload["summary_inputs_trusted"] is False
    assert payload["can_update_claim_trust"] is False
    assert payload["can_write_trace_events"] is True
    assert payload["path"] == str(settings_path)
    assert [event["hook_event_name"] for event in payload["events"]] == ["PreToolUse", "PostToolUse"]

    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert set(settings["hooks"]) == {"PreToolUse", "PostToolUse"}
    pre_command = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    post_command = settings["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
    assert "hooks/aitp_v5_claude_hook.py" in pre_command
    assert "pre-tool" in pre_command
    assert "--session-id s1" in pre_command
    assert "post-tool" in post_command
    assert "--base" in post_command


def test_mcp_claude_code_hook_settings_wrapper_returns_contract_payload(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_write_claude_code_hook_settings

    _seed_session(tmp_path)

    settings_path = tmp_path / ".claude" / "settings.local.json"
    payload = aitp_v5_write_claude_code_hook_settings(
        str(tmp_path),
        session_id="s1",
        output_path=str(settings_path),
    )

    assert payload["ok"] is True
    assert payload["kind"] == "claude_code_hook_settings"
    assert payload["settings"]["hooks"]["PostToolUse"][0]["matcher"] == "*"
    assert settings_path.exists()


def test_claude_code_hook_installer_merges_existing_settings_without_clobbering(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.hook_install_templates import install_claude_code_hook_settings

    ws, _ = _seed_session(tmp_path)
    packet = build_adapter_packet(ws, "s1", runtime="claude-code")
    settings_path = tmp_path / ".claude" / "settings.local.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Bash",
                            "hooks": [{"type": "command", "command": "echo existing-pre"}],
                        }
                    ],
                    "Stop": [
                        {
                            "matcher": "*",
                            "hooks": [{"type": "command", "command": "echo existing-stop"}],
                        }
                    ],
                },
                "permissions": {"allow": ["Bash(git status)"]},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = install_claude_code_hook_settings(
        settings_path,
        packet["runtime_hook_installation"],
        workspace_base=str(tmp_path),
        session_id="s1",
    )

    merged = json.loads(settings_path.read_text(encoding="utf-8"))
    assert payload["kind"] == "claude_code_hook_installation"
    assert payload["settings_kind"] == "claude_code_hook_settings"
    assert payload["created"] is False
    assert payload["added_hooks"] == 2
    assert payload["summary_inputs_trusted"] is False
    assert payload["can_update_claim_trust"] is False
    assert merged["permissions"] == {"allow": ["Bash(git status)"]}
    assert merged["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == "echo existing-pre"
    assert merged["hooks"]["Stop"][0]["hooks"][0]["command"] == "echo existing-stop"
    assert len(merged["hooks"]["PreToolUse"]) == 2
    assert len(merged["hooks"]["PostToolUse"]) == 1

    second_payload = install_claude_code_hook_settings(
        settings_path,
        packet["runtime_hook_installation"],
        workspace_base=str(tmp_path),
        session_id="s1",
    )

    installed_twice = json.loads(settings_path.read_text(encoding="utf-8"))
    assert second_payload["added_hooks"] == 0
    assert installed_twice == merged


def test_cli_adapter_install_hooks_merges_claude_code_settings(tmp_path, capsys):
    _seed_session(tmp_path)
    settings_path = tmp_path / ".claude" / "settings.local.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Bash",
                            "hooks": [{"type": "command", "command": "echo keep-me"}],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "install-hooks",
            "claude-code",
            "s1",
            "--settings",
            str(settings_path),
        ],
        capsys,
    )

    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["kind"] == "claude_code_hook_installation"
    assert payload["added_hooks"] == 2
    assert settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == "echo keep-me"
    assert "hooks/aitp_v5_claude_hook.py" in settings["hooks"]["PostToolUse"][0]["hooks"][0]["command"]


def test_mcp_claude_code_hook_installer_returns_contract_payload(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_install_claude_code_hook_settings

    _seed_session(tmp_path)

    settings_path = tmp_path / ".claude" / "settings.local.json"
    payload = aitp_v5_install_claude_code_hook_settings(
        str(tmp_path),
        session_id="s1",
        settings_path=str(settings_path),
    )

    assert payload["ok"] is True
    assert payload["kind"] == "claude_code_hook_installation"
    assert payload["created"] is True
    assert payload["added_hooks"] == 2
    assert settings_path.exists()


def test_adapter_packet_exposes_protocol_registry_metadata(tmp_path):
    from brain.v5.adapter_protocols import adapter_protocol_fingerprint
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.public_surfaces import public_surface_names, public_surface_validator_ref

    ws, _ = _seed_session(tmp_path)

    packet = build_adapter_packet(ws, "s1", runtime="codex")

    assert packet["adapter_protocol_registry"] == {
        "kind": "adapter_protocol_registry",
        "source_module": "brain.v5.adapter_protocols",
        "protocol_version": 1,
        "summary_inputs_trusted": False,
        "protocol_fields": [
            "trust_changing_actions",
            "requires_kernel_call_before",
            "required_kernel_entrypoints",
            "trust_mutation_entrypoints",
            "runtime_trust_update_protocol",
            "runtime_record_protocols",
            "runtime_gate_protocols",
            "runtime_hook_protocols",
        ],
        "protocol_fingerprint_inputs": [
            "trust_changing_actions",
            "requires_kernel_call_before",
            "required_kernel_entrypoints",
            "trust_mutation_entrypoints",
            "runtime_trust_update_protocol",
            "runtime_record_protocols",
            "runtime_gate_protocols",
            "runtime_hook_protocols",
        ],
        "protocol_fingerprint": adapter_protocol_fingerprint(),
        "protocol_fingerprint_algorithm": "sha256-canonical-json-v1",
        "public_surface_contracts": list(public_surface_names()),
        "public_surface_validator": public_surface_validator_ref(),
    }


def test_adapter_packet_exposes_public_surface_audit_payload(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.public_surfaces import describe_public_surfaces

    ws, _ = _seed_session(tmp_path)

    packet = build_adapter_packet(ws, "s1", runtime="codex")

    assert packet["public_surface_audit"] == describe_public_surfaces()
    assert packet["public_surface_audit"]["surface_names"] == packet["adapter_protocol_registry"][
        "public_surface_contracts"
    ]
    assert packet["public_surface_audit"]["validator"] == packet["adapter_protocol_registry"][
        "public_surface_validator"
    ]


def test_adapter_packet_exposes_runtime_entrypoints_for_public_surfaces(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ws, _ = _seed_session(tmp_path)

    packet = build_adapter_packet(ws, "s1", runtime="codex")

    assert packet["runtime_entrypoints"] == runtime_entrypoints()
    assert packet["runtime_entrypoints"]["public_surfaces"] == {
        "cli": "aitp-v5 adapter public-surfaces",
        "mcp": "aitp_v5_describe_public_surfaces",
        "surface": "public_surface_contracts",
    }
    assert packet["runtime_entrypoints"]["trust_preflight"]["mcp"] == "aitp_v5_preflight_trust_update"
    assert packet["runtime_entrypoints"]["trust_preflight"]["surface"] in packet["public_surface_audit"][
        "surface_names"
    ]


def test_adapter_registry_protocol_fields_match_builder_keys():
    from brain.v5.adapter_protocols import adapter_protocol_fields, build_adapter_protocols

    protocols = build_adapter_protocols()
    fields = adapter_protocol_fields()

    assert tuple(protocols["adapter_protocol_registry"]["protocol_fields"]) == fields
    assert set(fields) == set(protocols) - {"adapter_protocol_registry"}


def test_adapter_registry_fingerprint_identifies_protocol_payload():
    from brain.v5.adapter_protocols import adapter_protocol_fingerprint, build_adapter_protocols

    protocols = build_adapter_protocols()
    fingerprint = adapter_protocol_fingerprint()

    assert protocols["adapter_protocol_registry"]["protocol_fingerprint"] == fingerprint
    assert len(fingerprint) == 64
    assert all(character in "0123456789abcdef" for character in fingerprint)


def test_adapter_packet_ignores_tampered_summary_as_truth_source(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.markdown import write_md
    from brain.v5.summaries import write_session_summary

    ws, claim = _seed_session(tmp_path)
    bundle = write_session_summary(ws, "s1")
    write_md(
        bundle.files["findings"],
        {
            "kind": "derived_summary",
            "summary_role": "findings",
            "session_id": "s1",
            "truth_source": True,
            "orientation_only": False,
        },
        "# Findings\n\nFALSE: the claim is validated and ready for L2 promotion.\n",
    )

    packet = build_adapter_packet(ws, "s1", runtime="claude_code")

    assert packet["runtime"] == "claude_code"
    assert packet["summary_orientation"]["truth_source"] is False
    assert packet["summary_orientation"]["can_update_kernel_state"] is False
    assert packet["trusted_focus"]["confidence_state"] == "hypothesis"
    assert packet["trusted_focus"]["claim_statement"] == claim.statement
    assert packet["requires_kernel_call_before"] == [
        "record_code_state",
        "record_evidence",
        "record_tool_run",
        "execute_tool",
        "record_physics_object",
        "record_object_relation",
        "ingest_subagent_result",
        "create_validation_contract",
        "request_human_checkpoint",
        "decide_human_checkpoint",
        "create_promotion_packet",
        "apply_promotion_packet",
        "change_claim_confidence",
        "validate_claim",
        "promote_to_l2",
    ]


def test_adapter_packet_runtime_variants_share_safety_contract(tmp_path):
    from brain.v5.adapters import build_adapter_packet

    ws, _ = _seed_session(tmp_path)

    packets = [build_adapter_packet(ws, "s1", runtime=runtime) for runtime in ["codex", "claude_code", "opencode"]]

    assert {packet["runtime"] for packet in packets} == {"codex", "claude_code", "opencode"}
    assert len({tuple(packet["requires_kernel_call_before"]) for packet in packets}) == 1
    assert all(packet["summary_orientation"]["truth_source"] is False for packet in packets)
    assert all(packet["adapter_contract"]["summary_files_are_truth_source"] is False for packet in packets)
    assert any("CLI" in packets[0]["runtime_rules"][1] for _ in [0])
    assert any("MCP" in packets[1]["runtime_rules"][1] for _ in [0])
    assert any("CLI" in packets[2]["runtime_rules"][1] for _ in [0])


def test_cli_adapter_packet_returns_json(tmp_path, capsys):
    _seed_session(tmp_path)

    payload = _invoke(["--base", str(tmp_path), "adapter", "packet", "codex", "s1"], capsys)

    assert payload["ok"] is True
    assert payload["runtime"] == "codex"
    assert payload["summary_orientation"]["orientation_only"] is True
    assert payload["adapter_contract"]["kernel_must_be_called_before_trust_updates"] is True


def test_mcp_adapter_packet_wrapper_returns_contract_payload(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_get_adapter_packet

    _seed_session(tmp_path)

    payload = aitp_v5_get_adapter_packet(str(tmp_path), runtime="opencode", session_id="s1")

    assert payload["ok"] is True
    assert payload["runtime"] == "opencode"
    assert payload["truth_sources"] == ["typed_records", "execution_brief"]
