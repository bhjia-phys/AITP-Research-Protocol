from __future__ import annotations

import inspect
import json


def _invoke(args, capsys):
    from brain.v5.cli import main

    assert main(args) == 0
    output = capsys.readouterr().out
    return json.loads(output)


def test_cli_init_returns_json(tmp_path, capsys):
    payload = _invoke(["init", str(tmp_path)], capsys)

    assert payload["ok"] is True
    assert payload["workspace_root"].endswith(".aitp")


def test_cli_topic_claim_session_brief_roundtrip_returns_json(tmp_path, capsys):
    _invoke(["init", str(tmp_path)], capsys)
    topic = _invoke(
        [
            "--base",
            str(tmp_path),
            "topic",
            "create",
            "fqhe",
            "--context",
            "topological-order",
            "--title",
            "FQHE",
        ],
        capsys,
    )
    claim = _invoke(
        [
            "--base",
            str(tmp_path),
            "claim",
            "create",
            "--topic",
            "fqhe",
            "--statement",
            "Finite-size counting identifies the edge sector.",
            "--evidence-profile",
            "toy_numeric",
            "--confidence-state",
            "hypothesis",
            "--uncertainty",
            "finite-size artifact may mimic counting",
        ],
        capsys,
    )
    _invoke(
        [
            "--base",
            str(tmp_path),
            "session",
            "bind",
            "s1",
            "--topic",
            "fqhe",
            "--context",
            "topological-order",
            "--claim",
            claim["claim_id"],
        ],
        capsys,
    )
    brief = _invoke(["--base", str(tmp_path), "brief", "s1"], capsys)

    assert topic["topic_id"] == "fqhe"
    assert claim["claim_id"].startswith("claim-fqhe-")
    assert brief["current_focus"]["active_claim"] == claim["claim_id"]
    assert brief["risk_assessment"]["level"] in {"guided", "rigorous"}


def test_cli_risk_assess_returns_kernel_payload(tmp_path, capsys):
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The modified self-energy kernel reproduces the Si GW benchmark.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="formula-code translation risk",
    )

    payload = _invoke(["--base", str(tmp_path), "risk", "assess", claim.claim_id], capsys)

    assert payload["claim_id"] == claim.claim_id
    assert payload["risk_assessment"]["level"] in {"guided", "rigorous", "adversarial"}
    assert payload["risk_assessment"]["signals"]


def test_cli_does_not_import_legacy_mcp_monolith():
    import brain.v5.cli as cli

    source = inspect.getsource(cli)

    assert "mcp__aitp" not in source
    assert "aitp_get_execution_brief" not in source
    assert "brain.PROTOCOL" not in source
