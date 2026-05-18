from __future__ import annotations

import inspect


def test_mcp_wrappers_create_session_and_return_contract_valid_brief(tmp_path):
    from brain.v5.contracts import validate_execution_brief
    from brain.v5.mcp_tools import (
        aitp_v5_bind_session,
        aitp_v5_create_claim,
        aitp_v5_create_topic,
        aitp_v5_get_execution_brief,
        aitp_v5_init_workspace,
    )

    aitp_v5_init_workspace(str(tmp_path))
    aitp_v5_create_topic(str(tmp_path), topic_id="fqhe", context_id="topological-order", title="FQHE")
    claim = aitp_v5_create_claim(
        str(tmp_path),
        topic_id="fqhe",
        statement="Finite-size counting identifies the edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifact may mimic counting",
    )
    aitp_v5_bind_session(
        str(tmp_path),
        session_id="s1",
        topic_id="fqhe",
        context_id="topological-order",
        active_claim=claim["claim_id"],
    )

    brief = aitp_v5_get_execution_brief(str(tmp_path), session_id="s1")

    assert validate_execution_brief(brief).ok is True
    assert brief["current_focus"]["active_claim"] == claim["claim_id"]


def test_mcp_record_evidence_updates_execution_brief_coverage(tmp_path):
    from brain.v5.mcp_tools import (
        aitp_v5_bind_session,
        aitp_v5_create_claim,
        aitp_v5_create_topic,
        aitp_v5_get_execution_brief,
        aitp_v5_init_workspace,
        aitp_v5_record_evidence,
    )

    aitp_v5_init_workspace(str(tmp_path))
    aitp_v5_create_topic(str(tmp_path), topic_id="fqhe", context_id="topological-order", title="FQHE")
    claim = aitp_v5_create_claim(
        str(tmp_path),
        topic_id="fqhe",
        statement="Finite-size counting identifies the edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifact may mimic counting",
    )
    aitp_v5_record_evidence(
        str(tmp_path),
        topic_id="fqhe",
        claim_id=claim["claim_id"],
        evidence_type="toy_numeric",
        status="supports",
        summary="Finite-size provenance recorded.",
        supports_outputs=["evidence_or_provenance", "minimal_check"],
        source_refs=["tool_run:run-ed"],
    )
    aitp_v5_bind_session(
        str(tmp_path),
        session_id="s1",
        topic_id="fqhe",
        context_id="topological-order",
        active_claim=claim["claim_id"],
    )

    brief = aitp_v5_get_execution_brief(str(tmp_path), session_id="s1")

    assert "evidence_or_provenance" in brief["evidence_coverage"]["satisfied_outputs"]


def test_mcp_assess_risk_and_record_code_state_are_kernel_wrappers(tmp_path):
    from brain.v5.mcp_tools import (
        aitp_v5_assess_risk,
        aitp_v5_create_claim,
        aitp_v5_create_topic,
        aitp_v5_init_workspace,
        aitp_v5_record_code_state,
    )

    aitp_v5_init_workspace(str(tmp_path))
    aitp_v5_create_topic(str(tmp_path), topic_id="librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = aitp_v5_create_claim(
        str(tmp_path),
        topic_id="librpa-gw",
        statement="The modified self-energy kernel reproduces the Si GW benchmark.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="formula-code translation risk",
    )
    code_state = aitp_v5_record_code_state(
        str(tmp_path),
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="master",
        upstream_commit="abc123",
        local_branch="topic/self-energy",
        worktree_path="D:/worktrees/librpa/self-energy",
        dirty=False,
        linked_records={"claim_id": claim["claim_id"]},
    )
    risk = aitp_v5_assess_risk(str(tmp_path), claim_id=claim["claim_id"])

    assert code_state["code_state_id"].startswith("code-state-librpa-")
    assert risk["risk_assessment"]["signals"]


def test_mcp_adapter_protocol_registry_returns_static_metadata():
    from brain.v5.adapter_protocols import adapter_protocol_registry
    from brain.v5.mcp_tools import aitp_v5_get_adapter_protocol_registry

    payload = aitp_v5_get_adapter_protocol_registry()

    assert payload == {"ok": True, "adapter_protocol_registry": adapter_protocol_registry()}


def test_mcp_describe_public_surfaces_returns_static_audit_payload():
    from brain.v5.mcp_tools import aitp_v5_describe_public_surfaces
    from brain.v5.public_surfaces import describe_public_surfaces

    payload = aitp_v5_describe_public_surfaces()

    assert payload == {"ok": True, "public_surfaces": describe_public_surfaces()}


def test_mcp_adapter_protocol_registry_validates_payload_before_return(monkeypatch):
    import pytest

    import brain.v5.mcp_tools as mcp_tools
    from brain.v5.contracts import ContractError

    monkeypatch.setattr(mcp_tools, "adapter_protocol_registry", lambda: {"kind": "adapter_protocol_registry"})

    with pytest.raises(ContractError):
        mcp_tools.aitp_v5_get_adapter_protocol_registry()


def test_mcp_adapter_packet_validates_payload_before_return(tmp_path, monkeypatch):
    import pytest

    import brain.v5.mcp_tools as mcp_tools
    from brain.v5.contracts import ContractError

    monkeypatch.setattr(mcp_tools, "build_adapter_packet", lambda *args, **kwargs: {"kind": "adapter_packet"})

    with pytest.raises(ContractError):
        mcp_tools.aitp_v5_get_adapter_packet(str(tmp_path), runtime="codex", session_id="s1")


def test_mcp_summary_orientation_validates_payload_before_return(tmp_path, monkeypatch):
    import pytest

    import brain.v5.mcp_tools as mcp_tools
    from brain.v5.contracts import ContractError

    monkeypatch.setattr(mcp_tools, "read_summary_orientation", lambda *args, **kwargs: {"kind": "summary_orientation"})

    with pytest.raises(ContractError):
        mcp_tools.aitp_v5_read_summary_orientation(str(tmp_path), session_id="s1")


def test_mcp_write_session_summary_validates_payload_before_return(tmp_path, monkeypatch):
    import pytest

    import brain.v5.mcp_tools as mcp_tools
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
    monkeypatch.setattr(mcp_tools, "write_session_summary", lambda *args, **kwargs: bundle)

    with pytest.raises(ContractError):
        mcp_tools.aitp_v5_write_session_summary(str(tmp_path), session_id="s1")


def test_mcp_tools_do_not_import_legacy_mcp_monolith():
    import brain.v5.mcp_tools as mcp_tools

    source = inspect.getsource(mcp_tools)

    assert "require_valid_public_surface" in source
    assert "require_valid_adapter_packet" not in source
    assert "require_valid_session_summary_bundle" not in source
    assert "brain.mcp_server" not in source
    assert "mcp__aitp" not in source
    assert "aitp_get_execution_brief" not in source
