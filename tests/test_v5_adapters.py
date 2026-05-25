from __future__ import annotations

import json
import os
from pathlib import Path
from io import BytesIO
import subprocess
import sys


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


def _read_content_length_message(stream) -> dict:
    header = b""
    while not (header.endswith(b"\r\n\r\n") or header.endswith(b"\n\n")):
        chunk = stream.read(1)
        assert chunk, f"unexpected EOF while reading MCP header: {header!r}"
        header += chunk
    length = None
    for line in header.decode("utf-8").replace("\r\n", "\n").split("\n"):
        if line.lower().startswith("content-length:"):
            length = int(line.split(":", 1)[1].strip())
            break
    assert length is not None
    return json.loads(stream.read(length).decode("utf-8"))


def test_v5_native_mcp_content_length_stdio_smoke(tmp_path):
    script = Path(__file__).resolve().parents[1] / "brain" / "v5" / "native_mcp.py"
    env = {**os.environ, "AITP_V5_MCP_LOG": str(tmp_path / "mcp.log")}
    input_bytes = b""
    for message in [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]:
        body = json.dumps(message).encode("utf-8")
        input_bytes += f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8") + body

    process = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        input=input_bytes,
        capture_output=True,
        env=env,
        timeout=10,
    )
    assert process.returncode == 0, process.stderr.decode("utf-8", "replace")
    stdout = BytesIO(process.stdout)
    initialized = _read_content_length_message(stdout)
    assert initialized["result"]["serverInfo"]["name"] == "aitp-v5-brain"
    tools = _read_content_length_message(stdout)["result"]["tools"]
    assert tools
    assert all(tool["name"].startswith("aitp_v5_") for tool in tools)
    assert not any(tool["name"].startswith("aitp_") and not tool["name"].startswith("aitp_v5_") for tool in tools)


def test_v5_native_mcp_ndjson_stdio_smoke(tmp_path):
    script = Path(__file__).resolve().parents[1] / "brain" / "v5" / "native_mcp.py"
    env = {**os.environ, "AITP_V5_MCP_LOG": str(tmp_path / "mcp.log")}
    input_bytes = b"\n".join(
        json.dumps(message).encode("utf-8")
        for message in [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        ]
    ) + b"\n"
    process = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        input=input_bytes,
        capture_output=True,
        env=env,
        timeout=10,
    )
    assert process.returncode == 0, process.stderr.decode("utf-8", "replace")
    messages = [json.loads(line) for line in process.stdout.decode("utf-8").splitlines() if line.strip()]
    assert messages[0]["result"]["serverInfo"]["name"] == "aitp-v5-brain"
    tools = messages[1]["result"]["tools"]
    assert tools
    assert all(tool["name"].startswith("aitp_v5_") for tool in tools)
    assert not any(tool["name"].startswith("aitp_") and not tool["name"].startswith("aitp_v5_") for tool in tools)


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
    assert "register_tool_recipe" in packet["trust_changing_actions"]
    assert "record_reference_location" in packet["trust_changing_actions"]
    assert "record_physics_object" in packet["trust_changing_actions"]
    assert "record_object_relation" in packet["trust_changing_actions"]
    assert "record_sensemaking_report" in packet["trust_changing_actions"]
    assert "create_validation_contract" in packet["trust_changing_actions"]
    assert "record_validation_result" in packet["trust_changing_actions"]
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
    assert packet["runtime_gate_protocols"]["record_validation_result"]["sequence"][1] == "evaluate_pre_tool_policy"
    assert packet["runtime_record_protocols"]["record_evidence"] == {
        "entrypoint": "aitp_v5_record_evidence",
        "sequence": [
            "refresh_execution_brief",
            "record_evidence",
            "refresh_execution_brief",
            "write_session_summary",
        ],
        "required_typed_refs": ["topic_id", "claim_id"],
        "accepted_link_fields": ["source_refs", "tool_run_ids", "validation_result_ids", "artifact_ids"],
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
            "accepted_link_fields": ["code_state_ids", "validation_contract_ids", "artifact_ids", "source_refs"],
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
    assert packet["runtime_record_protocols"]["record_validation_result"] == {
        "entrypoint": "aitp_v5_record_validation_result",
        "sequence": [
            "refresh_execution_brief",
            "record_validation_result",
            "refresh_execution_brief",
            "write_session_summary",
        ],
        "required_typed_refs": ["topic_id", "claim_id", "contract_id", "tool_run_id"],
        "accepted_link_fields": ["checked_outputs", "covered_failure_modes", "evidence_refs", "artifact_ids"],
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
        "allowed_state_sources": ["typed_records", "typed_evidence_records", "typed_validation_records"],
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
            "allowed_state_sources": ["typed_records", "typed_tool_run_records", "typed_validation_records"],
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

    assert set(supported_runtimes()) == {"codex", "claude_code", "kimi_code", "opencode"}
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


def test_kimi_code_adapter_packet_builds_native_hook_installation_from_hook_protocols(tmp_path):
    from brain.v5.adapters import build_adapter_packet

    ws, _ = _seed_session(tmp_path)

    packet = build_adapter_packet(ws, "s1", runtime="kimi-code")

    assert packet["runtime"] == "kimi_code"
    assert "Kimi MCP tools" in packet["runtime_rules"][1]
    installation = packet["runtime_hook_installation"]
    assert installation["kind"] == "runtime_hook_installation_template"
    assert installation["runtime"] == "kimi_code"
    assert installation["source_protocol_field"] == "runtime_hook_protocols"
    assert installation["installation_mode"] == "native_lifecycle_hooks"
    assert installation["native_installer_available"] is False
    assert installation["summary_inputs_trusted"] is False
    assert {hook["hook_name"] for hook in installation["hooks"]} == {"pre_commit", "pre_tool", "post_tool"}


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
        "validation_contract_ids",
        "tool_run_ids",
        "validation_result_ids",
        "known_failure_modes",
        "recipe_id",
        "executor_id",
        "packet",
        "source_kind",
        "source_ref",
        "orientation_only",
        "risk_level",
        "human_checkpoint_id",
        "checkpoint_id",
        "failure_mode_review_checkpoint_id",
        "failure_mode_review_checkpoint",
        "failure_mode_review_result_id",
        "failure_mode_review_result",
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
                "validation_contract_ids",
                "tool_run_ids",
                "validation_result_ids",
                "known_failure_modes",
                "recipe_id",
                "executor_id",
                "packet",
                "source_kind",
                "source_ref",
                "orientation_only",
                "risk_level",
                "human_checkpoint_id",
                "checkpoint_id",
                "failure_mode_review_checkpoint_id",
                "failure_mode_review_checkpoint",
                "failure_mode_review_result_id",
                "failure_mode_review_result",
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
    assert sidecar["pre_tool_policy_entrypoint"]["input_schema"]["optional"][-1] == "failure_mode_review_result_id"
    assert "failure_mode_review_checkpoint_id" in sidecar["pre_tool_policy_entrypoint"]["input_schema"]["optional"]
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
    assert payload["fixture"]["hooks"]["post_tool"]["stdin"] == "<platform-event-json>"
    assert payload["fixture"]["hooks"]["post_tool"]["output_kind"] == "hook_trace_event_record"
    assert payload["fixture"]["hooks"]["post_tool"]["may_block"] is False
    assert payload["fixture"]["hooks"]["post_tool"]["state_mutation"] == "append_trace_event"
    assert payload["fixture"]["hooks"]["post_tool"]["argv"][1] == "hooks/aitp_v5_adapter_event_runner.py"
    assert payload["fixture"]["hooks"]["post_tool"]["argv"][2] == "post-tool"
    assert payload["fixture"]["hooks"]["post_tool"]["argv"][6] == "codex"
    assert payload["fixture"]["hooks"]["post_tool"]["argv"][8] == "s1"

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
    assert payload["fixture"]["hooks"]["post_tool"]["argv"][6] == "codex"
    assert payload["fixture"]["hooks"]["post_tool"]["output_kind"] == "hook_trace_event_record"
    assert fixture_path.exists()


def test_codex_native_hooks_json_installer_merges_lifecycle_hooks(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.hook_codex_install import install_codex_hooks_json
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, _ = _seed_session(tmp_path)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    hooks_path = tmp_path / ".codex" / "hooks.json"
    hooks_path.parent.mkdir(parents=True)
    hooks_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Write|Edit",
                            "hooks": [{"type": "command", "command": "echo keep-existing"}],
                        }
                    ],
                    "SessionStart": [{"matcher": "startup", "hooks": [{"type": "command", "command": "echo boot"}]}],
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = install_codex_hooks_json(
        hooks_path,
        packet["runtime_hook_installation"],
        packet["runtime_gate_protocols"],
        workspace_base=str(tmp_path),
        session_id="s1",
    )
    installed = json.loads(hooks_path.read_text(encoding="utf-8"))

    assert payload["kind"] == "codex_hook_installation"
    assert payload["runtime"] == "codex"
    assert payload["native_installer_available"] is True
    assert payload["native_hooks_path"] == str(hooks_path)
    assert payload["created"] is False
    assert payload["merged"] is True
    assert payload["added_hooks"] == 2
    assert payload["bridge"]["payload_path"] == str(hooks_path.parent / "AITP_V5_HOOK_BRIDGE.json")
    assert installed["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == "echo keep-existing"
    assert installed["hooks"]["SessionStart"][0]["hooks"][0]["command"] == "echo boot"
    assert "hooks/aitp_v5_adapter_event_runner.py" in installed["hooks"]["PreToolUse"][1]["hooks"][0]["command"]
    assert "--bridge-path" in installed["hooks"]["PreToolUse"][1]["hooks"][0]["command"]
    assert "post-tool" in installed["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
    assert require_valid_public_surface("codex_hook_installation", {"ok": True, **payload}) == {"ok": True, **payload}

    second_payload = install_codex_hooks_json(
        hooks_path,
        packet["runtime_hook_installation"],
        packet["runtime_gate_protocols"],
        workspace_base=str(tmp_path),
        session_id="s1",
    )
    installed_twice = json.loads(hooks_path.read_text(encoding="utf-8"))

    assert second_payload["added_hooks"] == 0
    assert installed_twice == installed


def test_cli_adapter_install_hooks_merges_codex_hooks_json(tmp_path, capsys):
    _seed_session(tmp_path)
    hooks_path = tmp_path / ".codex" / "hooks.json"
    hooks_path.parent.mkdir(parents=True)
    hooks_path.write_text(
        json.dumps({"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "echo route"}]}]}}),
        encoding="utf-8",
    )

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "install-hooks",
            "codex",
            "s1",
            "--settings",
            str(hooks_path),
        ],
        capsys,
    )
    installed = json.loads(hooks_path.read_text(encoding="utf-8"))

    assert payload["ok"] is True
    assert payload["kind"] == "codex_hook_installation"
    assert payload["native_installer_available"] is True
    assert payload["native_hooks_path"] == str(hooks_path)
    assert payload["added_hooks"] == 2
    assert installed["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"] == "echo route"
    assert "pre-tool" in installed["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert "post-tool" in installed["hooks"]["PostToolUse"][0]["hooks"][0]["command"]


def test_mcp_codex_native_hook_installer_returns_contract_payload(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_install_codex_hook_fixture

    _seed_session(tmp_path)
    hooks_path = tmp_path / ".codex" / "hooks.json"

    payload = aitp_v5_install_codex_hook_fixture(
        str(tmp_path),
        session_id="s1",
        output_path="",
        hooks_path=str(hooks_path),
    )

    assert payload["ok"] is True
    assert payload["kind"] == "codex_hook_installation"
    assert payload["native_installer_available"] is True
    assert payload["native_hooks_path"] == str(hooks_path)
    assert hooks_path.exists()


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


def test_mcp_adapter_pre_tool_event_infers_tool_recipe_policy(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge

    _seed_session(tmp_path)
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
            "tool_name": "mcp__aitp__aitp_v5_register_tool_recipe",
            "tool_input": {
                "recipe_id": "recipe-generated-summary-check",
                "tool_family": "domain",
                "tool_name": "summary-checker",
                "purpose": "Generated from findings.",
                "source_kind": "findings",
                "source_ref": ".aitp/surfaces/session_summaries/s1/findings.md",
                "orientation_only": True,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "register_tool_recipe"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "register_tool_recipe"
    assert payload["runtime_gate_protocol"]["required_typed_refs"] == [
        "recipe_id",
        "tool_family",
        "tool_name",
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


def test_mcp_adapter_pre_tool_event_infers_reference_location_policy(tmp_path):
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
            "tool_name": "mcp__aitp__aitp_v5_record_reference_location",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "connector_id": "ima",
                "uri": "ima://paper/gw-note",
                "label": "GW note",
                "source_kind": "findings",
                "source_ref": ".aitp/surfaces/session_summaries/s1/findings.md",
                "orientation_only": True,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "record_reference_location"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "record_reference_location"
    assert payload["runtime_gate_protocol"]["required_typed_refs"] == [
        "topic_id",
        "connector_id",
        "uri",
    ]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_adapter_pre_tool_event_infers_sensemaking_report_policy(tmp_path):
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
            "tool_name": "mcp__aitp__aitp_v5_record_sensemaking_report",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "title": "Generated interpretation",
                "summary": "The generated progress file says the benchmark is understood.",
                "source_kind": "progress",
                "source_ref": ".aitp/surfaces/session_summaries/s1/progress.md",
                "orientation_only": True,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "record_sensemaking_report"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "record_sensemaking_report"
    assert payload["runtime_gate_protocol"]["required_typed_refs"] == [
        "topic_id",
        "claim_id",
        "title",
        "summary",
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


def test_mcp_adapter_pre_tool_event_blocks_rigorous_execute_without_validation_contract(tmp_path):
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
            "risk_level": "rigorous",
            "tool_name": "mcp__aitp__aitp_v5_execute_tool",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "recipe_id": "recipe-si-gw",
                "executor_id": "pytest",
                "source_kind": "typed_records",
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "execute_tool"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "execute_tool"
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "high_risk_tool_execution_requires_validation_contract"
    ]


def test_mcp_adapter_pre_tool_event_accepts_rigorous_execute_with_validation_contract(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge
    from brain.v5.validation import create_validation_contract
    from brain.v5.workspace import init_workspace

    _, claim = _seed_session(tmp_path)
    ws = init_workspace(tmp_path)
    contract = create_validation_contract(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        required_checks=["reproduce Si GW benchmark"],
        failure_modes=["formula-code mismatch"],
        required_evidence_outputs=["benchmark table"],
        tool_recipe_ids=["recipe-si-gw"],
        executor_ids=["pytest"],
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
            "risk_level": "rigorous",
            "tool_name": "mcp__aitp__aitp_v5_execute_tool",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "recipe_id": "recipe-si-gw",
                "executor_id": "pytest",
                "source_kind": "typed_records",
                "validation_contract_ids": [contract.contract_id],
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "execute_tool"
    assert payload["mode"] == "log"
    assert payload["block"] is False
    assert payload["validation_contract_ids"] == [contract.contract_id]
    assert payload["policy_reasons"] == []


def test_mcp_adapter_pre_tool_event_blocks_rigorous_execute_with_unbound_validation_contract(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge
    from brain.v5.validation import create_validation_contract
    from brain.v5.workspace import init_workspace

    _, claim = _seed_session(tmp_path)
    ws = init_workspace(tmp_path)
    contract = create_validation_contract(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        required_checks=["reproduce Si GW benchmark"],
        failure_modes=["formula-code mismatch"],
        required_evidence_outputs=["benchmark table"],
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
            "risk_level": "rigorous",
            "tool_name": "mcp__aitp__aitp_v5_execute_tool",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "recipe_id": "recipe-si-gw",
                "executor_id": "pytest",
                "source_kind": "typed_records",
                "validation_contract_ids": [contract.contract_id],
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "execute_tool"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "high_risk_tool_validation_contract_mismatch"
    ]


def test_mcp_adapter_pre_tool_event_blocks_rigorous_tool_evidence_without_validation_result(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge
    from brain.v5.tools import record_tool_run
    from brain.v5.workspace import init_workspace

    _, claim = _seed_session(tmp_path)
    ws = init_workspace(tmp_path)
    run = record_tool_run(
        ws,
        recipe_id="recipe-si-gw",
        tool_family="numerical",
        tool_name="pytest",
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        outputs={"benchmark_table": "ok"},
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
            "risk_level": "rigorous",
            "tool_name": "mcp__aitp__aitp_v5_record_evidence",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "source_kind": "typed_records",
                "tool_run_ids": [run.run_id],
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "record_evidence"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["tool_run_ids"] == [run.run_id]
    assert payload["validation_result_ids"] == []
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "high_risk_tool_evidence_requires_validation_result"
    ]


def test_mcp_adapter_pre_tool_event_accepts_rigorous_tool_evidence_with_validation_result(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_adapter_pre_tool_event, aitp_v5_write_codex_hook_bridge
    from brain.v5.tools import record_tool_run
    from brain.v5.validation import create_validation_contract, record_validation_result
    from brain.v5.workspace import init_workspace

    _, claim = _seed_session(tmp_path)
    ws = init_workspace(tmp_path)
    contract = create_validation_contract(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        required_checks=["reproduce Si GW benchmark"],
        failure_modes=["formula-code mismatch"],
        required_evidence_outputs=["benchmark_table"],
        tool_recipe_ids=["recipe-si-gw"],
        executor_ids=["pytest"],
    )
    run = record_tool_run(
        ws,
        recipe_id="recipe-si-gw",
        tool_family="numerical",
        tool_name="pytest",
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        outputs={"benchmark_table": "ok"},
    )
    result = record_validation_result(
        ws,
        topic_id="librpa-gw",
        claim_id=claim.claim_id,
        contract_id=contract.contract_id,
        tool_run_id=run.run_id,
        status="passed",
        checked_outputs=["benchmark_table"],
        summary="Benchmark table passed validation.",
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
            "risk_level": "rigorous",
            "tool_name": "mcp__aitp__aitp_v5_record_evidence",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "source_kind": "typed_records",
                "tool_run_ids": [run.run_id],
                "validation_result_ids": [result.result_id],
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "record_evidence"
    assert payload["mode"] == "log"
    assert payload["block"] is False
    assert payload["tool_run_ids"] == [run.run_id]
    assert payload["validation_result_ids"] == [result.result_id]
    assert payload["policy_reasons"] == []


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
                "known_failure_modes": ["formula-code mismatch"],
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


def test_mcp_adapter_pre_tool_event_maps_failure_mode_review_checkpoint_to_human_checkpoint(tmp_path):
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
            "tool_name": "mcp__aitp__aitp_v5_request_failure_mode_review_checkpoint",
            "tool_input": {
                "claim_id": claim.claim_id,
                "source_kind": "task_plan",
                "source_ref": ".aitp/surfaces/session_summaries/s1/task_plan.md",
                "orientation_only": True,
            },
        },
    )

    assert payload["ok"] is True
    assert payload["action"] == "request_human_checkpoint"
    assert payload["block"] is True
    assert payload["runtime_gate_protocol"]["action"] == "request_human_checkpoint"
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
                "validation_contract_ids",
                "tool_run_ids",
                "validation_result_ids",
                "known_failure_modes",
                "recipe_id",
                "executor_id",
                "packet",
                "source_kind",
                "source_ref",
                "orientation_only",
                "risk_level",
                "human_checkpoint_id",
                "checkpoint_id",
                "failure_mode_review_checkpoint_id",
                "failure_mode_review_checkpoint",
                "failure_mode_review_result_id",
                "failure_mode_review_result",
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
    assert payload["fixture"]["plugin_hooks"]["post_tool"]["stdin"] == "<platform-event-json>"
    assert payload["fixture"]["plugin_hooks"]["post_tool"]["output_kind"] == "hook_trace_event_record"
    assert payload["fixture"]["plugin_hooks"]["post_tool"]["may_block"] is False
    assert payload["fixture"]["plugin_hooks"]["post_tool"]["state_mutation"] == "append_trace_event"
    assert payload["fixture"]["plugin_hooks"]["post_tool"]["argv"][1] == "hooks/aitp_v5_adapter_event_runner.py"
    assert payload["fixture"]["plugin_hooks"]["post_tool"]["argv"][2] == "post-tool"
    assert payload["fixture"]["plugin_hooks"]["post_tool"]["argv"][6] == "opencode"
    assert payload["fixture"]["plugin_hooks"]["post_tool"]["argv"][8] == "s1"

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
    assert payload["fixture"]["plugin_hooks"]["post_tool"]["argv"][6] == "opencode"
    assert payload["fixture"]["plugin_hooks"]["post_tool"]["output_kind"] == "hook_trace_event_record"
    assert fixture_path.exists()


def test_opencode_local_plugin_installer_writes_native_plugin(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.hook_opencode_install import install_opencode_plugin_file
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, _ = _seed_session(tmp_path)
    packet = build_adapter_packet(ws, "s1", runtime="opencode")
    plugin_path = tmp_path / ".opencode" / "plugins" / "aitp-v5.js"

    payload = install_opencode_plugin_file(
        plugin_path,
        packet["runtime_hook_installation"],
        packet["runtime_gate_protocols"],
        workspace_base=str(tmp_path),
        session_id="s1",
    )
    source = plugin_path.read_text(encoding="utf-8")

    assert payload["kind"] == "opencode_hook_installation"
    assert payload["runtime"] == "opencode"
    assert payload["native_installer_available"] is True
    assert payload["plugin_path"] == str(plugin_path)
    assert payload["created"] is True
    assert payload["changed"] is True
    assert payload["bridge_payload_path"] == str(tmp_path / ".opencode" / "AITP_V5_PLUGIN_BRIDGE.json")
    assert payload["plugin"]["lifecycle_events"] == ["tool.execute.before", "tool.execute.after"]
    assert "export const AITPV5Plugin" in source
    assert '"tool.execute.before"' in source
    assert '"tool.execute.after"' in source
    assert "aitp_v5_adapter_event_runner.py" in source
    assert "--bridge-path" in source
    assert "AITP_V5_PLUGIN_BRIDGE.json" in source
    assert "throw new Error" in source
    assert require_valid_public_surface("opencode_hook_installation", {"ok": True, **payload}) == {
        "ok": True,
        **payload,
    }

    second_payload = install_opencode_plugin_file(
        plugin_path,
        packet["runtime_hook_installation"],
        packet["runtime_gate_protocols"],
        workspace_base=str(tmp_path),
        session_id="s1",
    )

    assert second_payload["created"] is False
    assert second_payload["changed"] is False
    assert plugin_path.read_text(encoding="utf-8") == source


def test_cli_adapter_install_hooks_writes_opencode_local_plugin(tmp_path, capsys):
    _seed_session(tmp_path)

    plugin_path = tmp_path / ".opencode" / "plugins" / "aitp-v5.js"
    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "install-hooks",
            "opencode",
            "s1",
            "--plugin",
            str(plugin_path),
        ],
        capsys,
    )
    source = plugin_path.read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["kind"] == "opencode_hook_installation"
    assert payload["native_installer_available"] is True
    assert payload["plugin_path"] == str(plugin_path)
    assert payload["plugin"]["pre_tool"]["argv"][6] == "opencode"
    assert payload["plugin"]["post_tool"]["argv"][6] == "opencode"
    assert '"tool.execute.before"' in source
    assert '"tool.execute.after"' in source


def test_mcp_opencode_local_plugin_installer_returns_contract_payload(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_install_opencode_hook_fixture

    _seed_session(tmp_path)
    plugin_path = tmp_path / ".opencode" / "plugins" / "aitp-v5.js"

    payload = aitp_v5_install_opencode_hook_fixture(
        str(tmp_path),
        session_id="s1",
        output_path="",
        plugin_path=str(plugin_path),
    )

    assert payload["ok"] is True
    assert payload["kind"] == "opencode_hook_installation"
    assert payload["native_installer_available"] is True
    assert payload["plugin_path"] == str(plugin_path)
    assert plugin_path.exists()


def test_hook_installation_audit_reports_codex_native_hooks(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.hook_codex_install import install_codex_hooks_json
    from brain.v5.hook_install_audit import audit_hook_installation
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, _ = _seed_session(tmp_path)
    packet = build_adapter_packet(ws, "s1", runtime="codex")
    hooks_path = tmp_path / ".codex" / "hooks.json"
    install_codex_hooks_json(
        hooks_path,
        packet["runtime_hook_installation"],
        packet["runtime_gate_protocols"],
        workspace_base=str(tmp_path),
        session_id="s1",
    )

    payload = audit_hook_installation(ws, runtime="codex", settings_path=str(hooks_path))

    assert payload["kind"] == "runtime_hook_installation_audit"
    assert payload["runtime"] == "codex"
    assert payload["status"] == "installed"
    assert payload["summary_inputs_trusted"] is False
    assert payload["orientation_only"] is True
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False
    assert payload["findings"][0]["path"] == str(hooks_path)
    assert payload["findings"][0]["status"] == "installed"
    assert payload["findings"][0]["runtime_metadata_only"] is True
    assert require_valid_public_surface("runtime_hook_installation_audit", payload) == payload


def test_cli_adapter_install_audit_reports_opencode_local_plugin(tmp_path, capsys):
    _seed_session(tmp_path)
    plugin_path = tmp_path / ".opencode" / "plugins" / "aitp-v5.js"
    _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "install-hooks",
            "opencode",
            "s1",
            "--plugin",
            str(plugin_path),
        ],
        capsys,
    )

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "install-audit",
            "opencode",
            "--plugin",
            str(plugin_path),
        ],
        capsys,
    )

    assert payload["ok"] is True
    assert payload["kind"] == "runtime_hook_installation_audit"
    assert payload["runtime"] == "opencode"
    assert payload["status"] == "installed"
    assert payload["findings"][0]["path"] == str(plugin_path)
    assert payload["findings"][0]["status"] == "installed"
    assert payload["required_actions"] == []


def test_mcp_hook_installation_audit_reports_claude_settings(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.hook_install_templates import install_claude_code_hook_settings
    from brain.v5.mcp_tools import aitp_v5_audit_hook_installation

    ws, _ = _seed_session(tmp_path)
    packet = build_adapter_packet(ws, "s1", runtime="claude-code")
    settings_path = tmp_path / ".claude" / "settings.local.json"
    install_claude_code_hook_settings(
        settings_path,
        packet["runtime_hook_installation"],
        workspace_base=str(tmp_path),
        session_id="s1",
    )

    payload = aitp_v5_audit_hook_installation(
        str(tmp_path),
        runtime="claude-code",
        settings_path=str(settings_path),
    )

    assert payload["ok"] is True
    assert payload["kind"] == "runtime_hook_installation_audit"
    assert payload["runtime"] == "claude_code"
    assert payload["status"] == "installed"
    assert payload["findings"][0]["path"] == str(settings_path)
    assert payload["findings"][0]["status"] == "installed"


def test_cli_adapter_install_audit_reports_kimi_code_config(tmp_path, capsys):
    _seed_session(tmp_path)
    config_path = tmp_path / ".kimi" / "config.toml"
    _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "install-hooks",
            "kimi-code",
            "s1",
            "--settings",
            str(config_path),
        ],
        capsys,
    )

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "install-audit",
            "kimi-code",
            "--settings",
            str(config_path),
        ],
        capsys,
    )

    assert payload["ok"] is True
    assert payload["kind"] == "runtime_hook_installation_audit"
    assert payload["runtime"] == "kimi_code"
    assert payload["status"] == "installed"
    assert payload["findings"][0]["path"] == str(config_path)
    assert payload["findings"][0]["status"] == "installed"
    assert payload["required_actions"] == []


def test_hook_installation_paths_discover_workspace_defaults(tmp_path):
    from brain.v5.hook_install_paths import discover_hook_install_paths
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)

    payload = discover_hook_install_paths(ws)

    assert payload["kind"] == "runtime_hook_installation_paths"
    assert payload["truth_source"] == "workspace_conventions"
    assert payload["summary_inputs_trusted"] is False
    assert payload["orientation_only"] is True
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False
    assert {entry["runtime"] for entry in payload["paths"]} == {"codex", "claude_code", "kimi_code", "opencode"}
    by_runtime = {entry["runtime"]: entry for entry in payload["paths"]}
    assert by_runtime["codex"]["preferred"]["path"] == str(tmp_path / ".codex" / "hooks.json")
    assert by_runtime["codex"]["preferred"]["install_arg"] == "--settings"
    assert by_runtime["claude_code"]["preferred"]["path"] == str(tmp_path / ".claude" / "settings.local.json")
    assert by_runtime["claude_code"]["preferred"]["install_arg"] == "--settings"
    assert by_runtime["kimi_code"]["preferred"]["path"] == str(tmp_path / ".kimi" / "config.toml")
    assert by_runtime["kimi_code"]["preferred"]["install_arg"] == "--settings"
    assert by_runtime["kimi_code"]["alternates"][0]["path"] == str(tmp_path / ".kimi" / "AITP_V5_HOOKS.toml")
    assert by_runtime["opencode"]["preferred"]["path"] == str(tmp_path / ".opencode" / "plugins" / "aitp-v5.js")
    assert by_runtime["opencode"]["preferred"]["install_arg"] == "--plugin"
    assert "--settings" in by_runtime["codex"]["install_command"]
    assert "--settings" in by_runtime["kimi_code"]["install_command"]
    assert "--plugin" in by_runtime["opencode"]["install_command"]
    assert require_valid_public_surface("runtime_hook_installation_paths", payload) == payload


def test_cli_adapter_install_paths_returns_default_paths(tmp_path, capsys):
    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "install-paths",
        ],
        capsys,
    )

    assert payload["ok"] is True
    assert payload["kind"] == "runtime_hook_installation_paths"
    by_runtime = {entry["runtime"]: entry for entry in payload["paths"]}
    assert by_runtime["codex"]["audit_command"].endswith("adapter install-audit codex --settings .codex/hooks.json")
    assert by_runtime["kimi_code"]["install_command"].endswith(
        "adapter install-hooks kimi-code <session-id> --settings .kimi/config.toml"
    )
    assert by_runtime["opencode"]["install_command"].endswith(
        "adapter install-hooks opencode <session-id> --plugin .opencode/plugins/aitp-v5.js"
    )


def test_mcp_hook_installation_paths_returns_contract_payload(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_discover_hook_install_paths

    payload = aitp_v5_discover_hook_install_paths(str(tmp_path))

    assert payload["ok"] is True
    assert payload["kind"] == "runtime_hook_installation_paths"
    assert payload["paths"][0]["runtime"] == "codex"


def test_runtime_hook_smoke_coverage_reports_test_backed_host_smokes():
    from brain.v5.hook_smoke_coverage import runtime_hook_smoke_coverage_report
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = runtime_hook_smoke_coverage_report()

    assert payload["kind"] == "runtime_hook_smoke_coverage"
    assert payload["truth_source"] == "v5_test_contract_registry"
    assert payload["summary_inputs_trusted"] is False
    assert payload["orientation_only"] is True
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False
    assert payload["overall_status"] == "partial"
    by_runtime = {entry["runtime"]: entry for entry in payload["runtimes"]}
    assert {runtime for runtime in by_runtime} == {"codex", "claude_code", "kimi_code", "opencode"}
    assert "native_hooks_json_workspace_cwd" in {check["name"] for check in by_runtime["codex"]["checks"]}
    assert "native_hook_process_smoke" in {check["name"] for check in by_runtime["kimi_code"]["checks"]}
    assert "dynamic_host_readiness_audit_surface" in {check["name"] for check in by_runtime["claude_code"]["checks"]}
    assert "dynamic_host_lifecycle_audit_surface" in {check["name"] for check in by_runtime["codex"]["checks"]}
    assert "dynamic_host_lifecycle_audit_surface" in {check["name"] for check in by_runtime["claude_code"]["checks"]}
    assert "dynamic_host_lifecycle_audit_surface" in {check["name"] for check in by_runtime["kimi_code"]["checks"]}
    assert "local_plugin_node_lifecycle" in {check["name"] for check in by_runtime["opencode"]["checks"]}
    assert "real_interactive_lifecycle_event_smoke" in by_runtime["claude_code"]["gaps"]
    for entry in payload["runtimes"]:
        for check in entry["checks"]:
            assert check["runtime_metadata_only"] is True
            assert check["test_ids"]
    assert require_valid_public_surface("runtime_hook_smoke_coverage", payload) == payload


def test_cli_adapter_smoke_coverage_returns_contract_payload(capsys):
    payload = _invoke(["adapter", "smoke-coverage"], capsys)

    assert payload["ok"] is True
    assert payload["kind"] == "runtime_hook_smoke_coverage"
    assert payload["overall_status"] == "partial"
    assert {entry["runtime"] for entry in payload["runtimes"]} == {"codex", "claude_code", "kimi_code", "opencode"}


def test_mcp_hook_smoke_coverage_returns_contract_payload():
    from brain.v5.mcp_tools import aitp_v5_report_hook_smoke_coverage

    payload = aitp_v5_report_hook_smoke_coverage()

    assert payload["ok"] is True
    assert payload["kind"] == "runtime_hook_smoke_coverage"
    assert payload["runtimes"][0]["runtime"] == "codex"


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
    assert [event["hook_event_name"] for event in payload["events"]] == [
        "SessionStart",
        "PreToolUse",
        "PostToolUse",
    ]

    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert set(settings["hooks"]) == {"SessionStart", "PreToolUse", "PostToolUse"}
    session_command = settings["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    pre_command = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    post_command = settings["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
    assert "hooks/aitp_v5_claude_hook.py" in session_command
    assert "session-start" in session_command
    assert "hooks/aitp_v5_claude_hook.py" in pre_command
    assert str(Path.cwd() / "hooks" / "aitp_v5_claude_hook.py").replace("\\", "/") in pre_command
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
    assert payload["added_hooks"] == 3
    assert payload["summary_inputs_trusted"] is False
    assert payload["can_update_claim_trust"] is False
    assert merged["permissions"] == {"allow": ["Bash(git status)"]}
    assert merged["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == "echo existing-pre"
    assert merged["hooks"]["Stop"][0]["hooks"][0]["command"] == "echo existing-stop"
    assert len(merged["hooks"]["SessionStart"]) == 1
    assert len(merged["hooks"]["PreToolUse"]) == 2
    assert len(merged["hooks"]["PostToolUse"]) == 1
    assert "session-start" in merged["hooks"]["SessionStart"][0]["hooks"][0]["command"]

    second_payload = install_claude_code_hook_settings(
        settings_path,
        packet["runtime_hook_installation"],
        workspace_base=str(tmp_path),
        session_id="s1",
    )

    installed_twice = json.loads(settings_path.read_text(encoding="utf-8"))
    assert second_payload["added_hooks"] == 0
    assert installed_twice == merged


def test_claude_code_hook_installer_replaces_stale_relative_v5_hooks(tmp_path):
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
                            "matcher": "*",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": 'python hooks/aitp_v5_claude_hook.py pre-tool --base "old" --session-id s1',
                                }
                            ],
                        },
                        {
                            "matcher": "Bash",
                            "hooks": [{"type": "command", "command": "echo keep-existing"}],
                        },
                    ],
                    "PostToolUse": [
                        {
                            "matcher": "*",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": 'python hooks/aitp_v5_claude_hook.py post-tool --base "old" --session-id s1',
                                }
                            ],
                        }
                    ],
                }
            }
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
    session_commands = [entry["hooks"][0]["command"] for entry in merged["hooks"]["SessionStart"]]
    pre_commands = [entry["hooks"][0]["command"] for entry in merged["hooks"]["PreToolUse"]]
    post_commands = [entry["hooks"][0]["command"] for entry in merged["hooks"]["PostToolUse"]]
    assert payload["added_hooks"] == 3
    assert "echo keep-existing" in pre_commands
    assert sum("aitp_v5_claude_hook.py" in command for command in session_commands) == 1
    assert sum("aitp_v5_claude_hook.py" in command for command in pre_commands) == 1
    assert sum("aitp_v5_claude_hook.py" in command for command in post_commands) == 1
    assert "session-start" in session_commands[0]
    assert all(
        "python hooks/aitp_v5_claude_hook.py" not in command
        for command in session_commands + pre_commands + post_commands
    )


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
    assert payload["added_hooks"] == 3
    assert settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == "echo keep-me"
    assert "session-start" in settings["hooks"]["SessionStart"][0]["hooks"][0]["command"]
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
    assert payload["added_hooks"] == 3
    assert settings_path.exists()


def test_cli_adapter_hook_settings_writes_kimi_code_config_from_packet(tmp_path, capsys):
    _seed_session(tmp_path)

    config_path = tmp_path / ".kimi" / "AITP_V5_HOOKS.toml"
    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "hook-settings",
            "kimi-code",
            "s1",
            "--output",
            str(config_path),
        ],
        capsys,
    )

    assert payload["ok"] is True
    assert payload["kind"] == "kimi_code_hook_config"
    assert payload["runtime"] == "kimi_code"
    assert payload["source_protocol_field"] == "runtime_hook_installation"
    assert payload["summary_inputs_trusted"] is False
    assert payload["can_update_claim_trust"] is False
    assert payload["can_write_trace_events"] is True
    assert payload["path"] == str(config_path)
    assert [event["hook_event_name"] for event in payload["events"]] == [
        "SessionStart",
        "PreToolUse",
        "PostToolUse",
    ]

    text = config_path.read_text(encoding="utf-8")
    assert "# BEGIN AITP V5 KIMI HOOKS" in text
    assert text.count("[[hooks]]") == 3
    assert 'event = "SessionStart"' in text
    assert 'event = "PreToolUse"' in text
    assert 'event = "PostToolUse"' in text
    assert "hooks/aitp_v5_kimi_hook.py" in text
    assert "session-start" in text
    assert "pre-tool" in text
    assert "post-tool" in text


def test_mcp_kimi_code_hook_config_wrapper_returns_contract_payload(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_write_kimi_code_hook_config

    _seed_session(tmp_path)

    config_path = tmp_path / ".kimi" / "AITP_V5_HOOKS.toml"
    payload = aitp_v5_write_kimi_code_hook_config(
        str(tmp_path),
        session_id="s1",
        output_path=str(config_path),
    )

    assert payload["ok"] is True
    assert payload["kind"] == "kimi_code_hook_config"
    assert [event["hook_event_name"] for event in payload["events"]] == [
        "SessionStart",
        "PreToolUse",
        "PostToolUse",
    ]
    assert payload["events"][0]["matcher"] == "startup|resume"
    assert payload["events"][1]["matcher"] == "*"
    assert config_path.exists()


def test_kimi_code_hook_config_installer_merges_existing_config(tmp_path):
    from brain.v5.adapters import build_adapter_packet
    from brain.v5.hook_kimi_install import install_kimi_code_hook_config

    ws, _ = _seed_session(tmp_path)
    packet = build_adapter_packet(ws, "s1", runtime="kimi-code")
    config_path = tmp_path / ".kimi" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        '\n'.join(
            [
                'model = "kimi-k2-turbo-preview"',
                "",
                "[mcpServers.keep_me]",
                'command = "python"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    payload = install_kimi_code_hook_config(
        config_path,
        packet["runtime_hook_installation"],
        workspace_base=str(tmp_path),
        session_id="s1",
    )

    merged = config_path.read_text(encoding="utf-8")
    assert payload["kind"] == "kimi_code_hook_installation"
    assert payload["config_kind"] == "kimi_code_hook_config"
    assert payload["created"] is False
    assert payload["merged"] is True
    assert payload["added_hooks"] == 3
    assert payload["summary_inputs_trusted"] is False
    assert payload["can_update_claim_trust"] is False
    assert 'model = "kimi-k2-turbo-preview"' in merged
    assert "[mcpServers.keep_me]" in merged
    assert "# BEGIN AITP V5 KIMI HOOKS" in merged
    assert merged.count("aitp_v5_kimi_hook.py") == 3
    assert 'event = "SessionStart"' in merged
    assert "session-start" in merged

    second_payload = install_kimi_code_hook_config(
        config_path,
        packet["runtime_hook_installation"],
        workspace_base=str(tmp_path),
        session_id="s1",
    )

    installed_twice = config_path.read_text(encoding="utf-8")
    assert second_payload["added_hooks"] == 0
    assert installed_twice == merged


def test_cli_adapter_install_hooks_merges_kimi_code_config(tmp_path, capsys):
    _seed_session(tmp_path)
    config_path = tmp_path / ".kimi" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text('model = "kimi-k2"\n', encoding="utf-8")

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "install-hooks",
            "kimi-code",
            "s1",
            "--settings",
            str(config_path),
        ],
        capsys,
    )

    text = config_path.read_text(encoding="utf-8")
    assert payload["ok"] is True
    assert payload["kind"] == "kimi_code_hook_installation"
    assert payload["added_hooks"] == 3
    assert 'model = "kimi-k2"' in text
    assert "session-start" in text
    assert "hooks/aitp_v5_kimi_hook.py" in text


def test_mcp_kimi_code_hook_installer_returns_contract_payload(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_install_kimi_code_hook_config

    _seed_session(tmp_path)

    config_path = tmp_path / ".kimi" / "config.toml"
    payload = aitp_v5_install_kimi_code_hook_config(
        str(tmp_path),
        session_id="s1",
        settings_path=str(config_path),
    )

    assert payload["ok"] is True
    assert payload["kind"] == "kimi_code_hook_installation"
    assert payload["created"] is True
    assert payload["added_hooks"] == 3
    assert config_path.exists()


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


def test_record_gate_coverage_audit_reports_no_ungated_record_protocols():
    from brain.v5.adapter_protocols import mandatory_record_protocols, record_gate_coverage_audit
    from brain.v5.gate_protocols import mandatory_gate_protocols

    record_protocols = mandatory_record_protocols()
    gate_protocols = mandatory_gate_protocols()
    audit = record_gate_coverage_audit()

    assert audit["kind"] == "record_gate_coverage_audit"
    assert audit["record_protocols"] == sorted(record_protocols)
    assert audit["gate_protocols"] == sorted(gate_protocols)
    assert audit["gated_record_protocols"] == sorted(record_protocols)
    assert audit["ungated_record_protocols"] == []
    assert audit["extra_gate_protocols"] == sorted(set(gate_protocols) - set(record_protocols))
    assert audit["truth_source"] == "adapter_protocol_registry"
    assert audit["summary_inputs_trusted"] is False


def test_mcp_record_gate_coverage_audit_returns_contract_payload():
    from brain.v5.adapter_protocols import record_gate_coverage_audit
    from brain.v5.mcp_tools import aitp_v5_audit_record_gate_coverage

    assert aitp_v5_audit_record_gate_coverage() == {
        "ok": True,
        "record_gate_coverage_audit": record_gate_coverage_audit(),
    }


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
        "register_tool_recipe",
        "record_reference_location",
        "record_physics_object",
        "record_object_relation",
        "record_sensemaking_report",
        "ingest_subagent_result",
        "create_validation_contract",
        "record_validation_result",
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

    packets = [
        build_adapter_packet(ws, "s1", runtime=runtime)
        for runtime in ["codex", "claude_code", "kimi_code", "opencode"]
    ]

    assert {packet["runtime"] for packet in packets} == {"codex", "claude_code", "kimi_code", "opencode"}
    assert len({tuple(packet["requires_kernel_call_before"]) for packet in packets}) == 1
    assert all(packet["summary_orientation"]["truth_source"] is False for packet in packets)
    assert all(packet["adapter_contract"]["summary_files_are_truth_source"] is False for packet in packets)
    assert any("CLI" in packets[0]["runtime_rules"][1] for _ in [0])
    assert any("MCP" in packets[1]["runtime_rules"][1] for _ in [0])
    assert any("Kimi MCP" in packets[2]["runtime_rules"][1] for _ in [0])
    assert any("CLI" in packets[3]["runtime_rules"][1] for _ in [0])


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
