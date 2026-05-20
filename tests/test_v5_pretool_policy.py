from __future__ import annotations

import json


def _seed_claim(tmp_path, *, evidence_profile: str = "toy_numeric"):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Finite-size counting identifies the FQHE edge sector.",
        evidence_profile=evidence_profile,
        confidence_state="locally_checked",
        active_uncertainty="finite-size artifact may mimic counting",
    )
    bind_session(
        ws,
        "s1",
        topic_id="fqhe",
        context_id="topological-order",
        active_claim=claim.claim_id,
    )
    return ws, claim


def _invoke(args, capsys):
    from brain.v5.cli import main

    assert main(args) == 0
    output = capsys.readouterr().out
    return json.loads(output)


def test_context_pre_tool_policy_blocks_l2_promotion_without_evidence(tmp_path):
    from brain.v5.pretool_policy import evaluate_context_pre_tool_policy
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _seed_claim(tmp_path)

    payload = evaluate_context_pre_tool_policy(
        ws,
        session_id="s1",
        action="promote_to_l2",
        claim_id=claim.claim_id,
        evidence_refs=[],
        risk_level="guided",
        source_kind="typed_records",
    )

    assert payload["kind"] == "hook_decision"
    assert payload["hook_name"] == "pre_tool"
    assert payload["action"] == "promote_to_l2"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["attach_evidence_ref"]
    assert payload["can_update_kernel_state"] is False
    assert payload["summary_inputs_trusted"] is False
    assert require_valid_public_surface("pre_tool_policy_decision", {"ok": True, **payload})["ok"] is True


def test_cli_context_pre_tool_policy_returns_contract_payload(tmp_path, capsys):
    from brain.v5.public_surfaces import require_valid_public_surface

    _, claim = _seed_claim(tmp_path)

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "policy",
            "pre-tool",
            "promote_to_l2",
            "--session",
            "s1",
            "--claim",
            claim.claim_id,
            "--source-kind",
            "typed_records",
        ],
        capsys,
    )

    assert payload["ok"] is True
    assert payload["kind"] == "hook_decision"
    assert payload["action"] == "promote_to_l2"
    assert payload["block"] is True
    assert payload["required_actions"] == ["attach_evidence_ref"]
    assert require_valid_public_surface("pre_tool_policy_decision", payload) == payload


def test_mcp_context_pre_tool_policy_warns_code_validation_without_code_state(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy
    from brain.v5.public_surfaces import require_valid_public_surface

    _, claim = _seed_claim(tmp_path, evidence_profile="code_method")

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="validate_claim",
        claim_id=claim.claim_id,
        risk_level="guided",
        source_kind="typed_records",
    )

    assert payload["ok"] is True
    assert payload["kind"] == "hook_decision"
    assert payload["action"] == "validate_claim"
    assert payload["mode"] == "warn"
    assert payload["block"] is False
    assert payload["required_actions"] == ["record_code_state"]
    assert require_valid_public_surface("pre_tool_policy_decision", payload) == payload
