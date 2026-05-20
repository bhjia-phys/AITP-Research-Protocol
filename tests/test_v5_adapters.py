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
    assert "change_claim_confidence" in packet["trust_changing_actions"]
    assert "ingest_subagent_result" in packet["trust_changing_actions"]
    assert "aitp_v5_get_execution_brief" in packet["required_kernel_entrypoints"]
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
        "preflight": "aitp_v5_preflight_trust_update",
        "sequence": [
            "refresh_execution_brief",
            "preflight_trust_update",
            "record_validation_evidence",
            "refresh_execution_brief",
            "write_session_summary",
        ],
        "required_typed_refs": ["topic_id", "claim_id", "evidence_refs"],
        "allowed_state_sources": ["typed_evidence_records", "typed_validation_records"],
        "human_checkpoint_required": False,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    }
    assert packet["runtime_gate_protocols"]["promote_to_l2"] == {
        "preflight": "aitp_v5_preflight_trust_update",
        "sequence": [
            "refresh_execution_brief",
            "preflight_trust_update",
            "human_checkpoint",
            "promote_to_l2",
        ],
        "required_typed_refs": ["topic_id", "claim_id", "evidence_refs", "validation_result_ref"],
        "allowed_state_sources": ["typed_evidence_records", "typed_validation_records", "human_checkpoint"],
        "human_checkpoint_required": True,
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
        ],
        "protocol_fingerprint_inputs": [
            "trust_changing_actions",
            "requires_kernel_call_before",
            "required_kernel_entrypoints",
            "trust_mutation_entrypoints",
            "runtime_trust_update_protocol",
            "runtime_record_protocols",
            "runtime_gate_protocols",
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
        "record_evidence",
        "record_tool_run",
        "execute_tool",
        "ingest_subagent_result",
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
