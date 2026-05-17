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


def test_mcp_tools_do_not_import_legacy_mcp_monolith():
    import brain.v5.mcp_tools as mcp_tools

    source = inspect.getsource(mcp_tools)

    assert "brain.mcp_server" not in source
    assert "mcp__aitp" not in source
    assert "aitp_get_execution_brief" not in source
