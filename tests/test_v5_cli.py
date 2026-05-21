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


def test_cli_tool_recipe_and_run_record_provenance(tmp_path, capsys):
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The Si GW benchmark is reproduced by the recorded run.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="tool-run provenance",
    )

    recipe = _invoke(
        [
            "--base",
            str(tmp_path),
            "tool",
            "recipe",
            "register",
            "recipe-librpa-si-gw",
            "--family",
            "domain",
            "--name",
            "librpa-gw-runner",
            "--purpose",
            "Run a LibRPA Si GW benchmark.",
            "--required-input",
            "code_state_id",
            "--expected-output",
            "benchmark_consistency",
            "--invariant",
            "same upstream commit and build flags",
        ],
        capsys,
    )
    run = _invoke(
        [
            "--base",
            str(tmp_path),
            "tool",
            "run",
            "record",
            "--recipe",
            recipe["recipe_id"],
            "--family",
            "domain",
            "--name",
            "librpa-gw-runner",
            "--topic",
            "librpa-gw",
            "--claim",
            claim.claim_id,
            "--inputs-json",
            '{"code_state_id":"code-state-librpa-clean","input_deck":"Si-gw.in"}',
            "--outputs-json",
            '{"gap_ev":1.23,"within_tolerance":true}',
            "--environment-json",
            '{"host":"fisher","mpi_ranks":32}',
            "--evidence-status",
            "supports",
            "--code-state-id",
            "code-state-librpa-clean",
            "--artifact-id",
            "artifact-si-gw-log",
            "--source-ref",
            "benchmark:si-reference",
        ],
        capsys,
    )

    assert recipe["ok"] is True
    assert recipe["required_inputs"] == ["code_state_id"]
    assert recipe["expected_outputs"] == ["benchmark_consistency"]
    assert run["ok"] is True
    assert run["recipe_id"] == "recipe-librpa-si-gw"
    assert run["outputs"]["within_tolerance"] is True
    assert run["environment"]["mpi_ranks"] == 32
    assert run["code_state_ids"] == ["code-state-librpa-clean"]
    assert run["artifact_ids"] == ["artifact-si-gw-log"]
    assert run["source_refs"] == ["benchmark:si-reference"]


def test_cli_evidence_and_code_state_record_provenance(tmp_path, capsys):
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The code state and benchmark evidence are recorded before trust changes.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="code provenance",
    )

    code_state = _invoke(
        [
            "--base",
            str(tmp_path),
            "code",
            "state",
            "record",
            "--repo-id",
            "librpa",
            "--upstream-remote",
            "origin",
            "--upstream-branch",
            "master",
            "--upstream-commit",
            "abc123",
            "--local-branch",
            "topic/gw",
            "--worktree-path",
            "D:/worktrees/librpa/gw",
            "--build-config-json",
            '{"compiler":"gcc","mpi":true}',
            "--runtime-environment-json",
            '{"host":"fisher"}',
            "--linked-records-json",
            '{"claim_id":"%s"}' % claim.claim_id,
        ],
        capsys,
    )
    evidence = _invoke(
        [
            "--base",
            str(tmp_path),
            "evidence",
            "record",
            "--topic",
            "librpa-gw",
            "--claim",
            claim.claim_id,
            "--type",
            "benchmark",
            "--status",
            "supports",
            "--summary",
            "The Si benchmark run is within tolerance.",
            "--supports-output",
            "benchmark_consistency",
            "--source-ref",
            "benchmark:si-reference",
            "--tool-run-id",
            "tool-run-librpa-si",
            "--artifact-id",
            "artifact-si-log",
        ],
        capsys,
    )

    assert code_state["ok"] is True
    assert code_state["kind"] == "code_state"
    assert code_state["repo_id"] == "librpa"
    assert code_state["build_config"]["mpi"] is True
    assert code_state["linked_records"]["claim_id"] == claim.claim_id
    assert evidence["ok"] is True
    assert evidence["kind"] == "evidence"
    assert evidence["supports_outputs"] == ["benchmark_consistency"]
    assert evidence["tool_run_ids"] == ["tool-run-librpa-si"]
    assert evidence["artifact_ids"] == ["artifact-si-log"]


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


def test_cli_adapter_record_gate_audit_returns_static_payload_without_workspace(tmp_path, capsys):
    from brain.v5.adapter_protocols import record_gate_coverage_audit

    payload = _invoke(["--base", str(tmp_path), "adapter", "record-gate-audit"], capsys)

    assert payload == {"ok": True, "record_gate_coverage_audit": record_gate_coverage_audit()}
    assert not (tmp_path / ".aitp").exists()


def test_cli_adapter_registry_validates_payload_before_return(monkeypatch):
    import pytest

    import brain.v5.cli as cli
    import brain.v5.cli_adapters as cli_adapters
    from brain.v5.contracts import ContractError

    monkeypatch.setattr(cli_adapters, "adapter_protocol_registry", lambda: {"kind": "adapter_protocol_registry"})

    with pytest.raises(ContractError):
        cli.main(["adapter", "registry"])


def test_cli_adapter_packet_validates_payload_before_return(tmp_path, monkeypatch):
    import pytest

    import brain.v5.cli as cli
    import brain.v5.cli_adapters as cli_adapters
    from brain.v5.contracts import ContractError

    monkeypatch.setattr(cli_adapters, "build_adapter_packet", lambda *args, **kwargs: {"kind": "adapter_packet"})

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
