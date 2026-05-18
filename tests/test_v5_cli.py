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


def test_cli_adapter_registry_returns_static_protocol_metadata_without_workspace(tmp_path, capsys):
    from brain.v5.adapter_protocols import adapter_protocol_registry

    payload = _invoke(["--base", str(tmp_path), "adapter", "registry"], capsys)

    assert payload == {"ok": True, "adapter_protocol_registry": adapter_protocol_registry()}
    assert not (tmp_path / ".aitp").exists()


def test_cli_adapter_public_surfaces_returns_static_audit_payload_without_workspace(tmp_path, capsys):
    from brain.v5.public_surfaces import describe_public_surfaces

    payload = _invoke(["--base", str(tmp_path), "adapter", "public-surfaces"], capsys)

    assert payload == {"ok": True, "public_surfaces": describe_public_surfaces()}
    assert not (tmp_path / ".aitp").exists()


def test_cli_adapter_registry_validates_payload_before_return(monkeypatch):
    import pytest

    import brain.v5.cli as cli
    from brain.v5.contracts import ContractError

    monkeypatch.setattr(cli, "adapter_protocol_registry", lambda: {"kind": "adapter_protocol_registry"})

    with pytest.raises(ContractError):
        cli.main(["adapter", "registry"])


def test_cli_adapter_packet_validates_payload_before_return(tmp_path, monkeypatch):
    import pytest

    import brain.v5.cli as cli
    from brain.v5.contracts import ContractError

    monkeypatch.setattr(cli, "build_adapter_packet", lambda *args, **kwargs: {"kind": "adapter_packet"})

    with pytest.raises(ContractError):
        cli.main(["--base", str(tmp_path), "adapter", "packet", "codex", "s1"])


def test_cli_brief_validates_payload_before_return(tmp_path, monkeypatch):
    import pytest

    import brain.v5.cli as cli
    from brain.v5.contracts import ContractError

    monkeypatch.setattr(cli, "build_execution_brief", lambda *args, **kwargs: {"session": {"session_id": "s1"}})

    with pytest.raises(ContractError):
        cli.main(["--base", str(tmp_path), "brief", "s1"])


def test_cli_summary_orientation_validates_payload_before_return(tmp_path, monkeypatch):
    import pytest

    import brain.v5.cli as cli
    from brain.v5.contracts import ContractError

    monkeypatch.setattr(cli, "read_summary_orientation", lambda *args, **kwargs: {"kind": "summary_orientation"})

    with pytest.raises(ContractError):
        cli.main(["--base", str(tmp_path), "summary", "orientation", "s1"])


def test_cli_summary_session_validates_payload_before_return(tmp_path, monkeypatch):
    import pytest

    import brain.v5.cli as cli
    from brain.v5.contracts import ContractError
    from brain.v5.summaries import SessionSummaryBundle

    bundle = SessionSummaryBundle(
        session_id="s1",
        topic_id="fqhe",
        active_claim="claim-fqhe",
        summary_dir=str(tmp_path / "summaries" / "s1"),
        files={"task_plan": "task_plan.md", "findings": "findings.md", "progress": "progress.md"},
        truth_source=True,
    )
    monkeypatch.setattr(cli, "write_session_summary", lambda *args, **kwargs: bundle)

    with pytest.raises(ContractError):
        cli.main(["--base", str(tmp_path), "summary", "session", "s1"])


def test_cli_does_not_import_legacy_mcp_monolith():
    import brain.v5.cli as cli

    source = inspect.getsource(cli)

    assert "require_valid_public_surface" in source
    assert "require_valid_adapter_packet" not in source
    assert "require_valid_session_summary_bundle" not in source
    assert "mcp__aitp" not in source
    assert "aitp_get_execution_brief" not in source
    assert "brain.PROTOCOL" not in source
