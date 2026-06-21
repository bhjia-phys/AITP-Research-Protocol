"""Tests for the lightweight record router (plan-only surface).

Covers the acceptance criteria from the implementation spec §10:
- no_write for casual chat
- artifact + sensemaking for old/new plot boundary
- proof_obligation for gaps
- evidence only when a verified tool_run/validation_result ref exists
- runtime failure is NOT algorithm failure
- active-claim mismatch does not default to active
- trust request produces only preflight, no apply
- native MCP advertises the planner
- runtime entrypoint catalog includes it
- contract rejects plans that try to update trust
"""

from __future__ import annotations

from pathlib import Path

import pytest


# --------------------------------------------------------------------------- #
# fixture helpers
# --------------------------------------------------------------------------- #

def _make_workspace(tmp_path: Path, *, topic_id: str = "fqhe", claim_id: str = "claim-fqhe", statement: str = "FQHE energy gap finite-size evidence"):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, topic_id, context_id="ctx", title="T")
    claim = create_claim(
        ws, topic_id=topic_id, statement=statement,
        evidence_profile="code_method", confidence_state="hypothesis",
        active_uncertainty="finite-size",
    )
    bind_session(ws, session_id="s1", topic_id=topic_id, context_id="ctx", active_claim=claim.claim_id)
    return ws, claim


def _make_sibling_claims(tmp_path: Path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "t", context_id="ctx", title="T")
    claim_a = create_claim(
        ws, topic_id="t", statement="G0W0 band gap for silicon 8-atom cell",
        evidence_profile="code_method", confidence_state="hypothesis", active_uncertainty="k-mesh",
    )
    claim_b = create_claim(
        ws, topic_id="t", statement="QSGW self-consistent cycle convergence for librpa",
        evidence_profile="code_method", confidence_state="hypothesis", active_uncertainty="mixing",
    )
    bind_session(ws, session_id="s1", topic_id="t", context_id="ctx", active_claim=claim_a.claim_id)
    return ws, claim_a, claim_b


def _make_tool_run(tmp_path: Path):
    from brain.v5.models import ToolRunRecord
    from brain.v5.store import write_record

    ws, claim = _make_workspace(tmp_path)
    run = ToolRunRecord(
        run_id="run-abc",
        recipe_id="recipe-1",
        tool_family="diag",
        tool_name="energy_gap",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_status="supports",
    )
    path = ws.registry_dir("tool_runs") / "run-abc.md"
    write_record(path, run, body="# tool run\n")
    return ws, claim, run


# --------------------------------------------------------------------------- #
# 1. no_write for casual chat
# --------------------------------------------------------------------------- #

def test_no_write_for_casual_chat(tmp_path):
    from brain.v5.lightweight_record_router import plan_lightweight_record_write

    ws, claim = _make_workspace(tmp_path)
    result = plan_lightweight_record_write(
        ws, topic_id="fqhe", current_session_id="s1", active_claim_id=claim.claim_id,
        event_summary="我们只是讨论一下下一段话怎么表达,没有新结果。",
    )
    assert result["decision"] == "no_write"
    assert result["typed_write_plan"] == []
    assert result["can_update_claim_trust"] is False
    assert result["no_write_reason"]


# --------------------------------------------------------------------------- #
# 2. artifact + sensemaking for old/new plot boundary
# --------------------------------------------------------------------------- #

def test_artifact_and_sensemaking_for_old_new_plot_boundary(tmp_path):
    from brain.v5.lightweight_record_router import plan_lightweight_record_write

    ws, claim = _make_workspace(tmp_path, claim_id="claim-qsgw-final", statement="qsgw final report")
    result = plan_lightweight_record_write(
        ws, topic_id="fqhe", current_session_id="s1", active_claim_id=claim.claim_id,
        event_summary="旧的 kconv 图使用 diagnostic lane 口径,不能和新 final report 混用。",
        touched_files_or_artifacts=["reports/old_kconv.png"],
    )
    assert result["decision"] == "plan_write"
    types = result["selected_record_types"]
    assert "artifact" in types
    assert "sensemaking_report" in types
    assert "evidence" not in types
    # artifact must come before sensemaking (fixed priority order)
    assert types.index("artifact") < types.index("sensemaking_report")
    assert result["can_update_claim_trust"] is False


# --------------------------------------------------------------------------- #
# 3. gap routes to proof obligation only
# --------------------------------------------------------------------------- #

def test_gap_routes_to_proof_obligation_only(tmp_path):
    from brain.v5.lightweight_record_router import plan_lightweight_record_write

    ws, claim = _make_workspace(tmp_path, claim_id="claim-qsgw-final", statement="qsgw final report BN convergence validation")
    result = plan_lightweight_record_write(
        ws, topic_id="fqhe", current_session_id="s1", active_claim_id=claim.claim_id,
        event_summary="BN 的 final lane 还缺少可复现的 k 点收敛 validation gap,下一步要重跑。",
    )
    assert result["decision"] == "plan_write"
    assert result["selected_record_types"] == ["proof_obligation"]
    plan_item = result["typed_write_plan"][0]
    assert plan_item["required_fields"]["obligation_type"] == "validation_gap"
    assert plan_item["required_fields"]["status"] == "open"
    # exploratory is a real MATURITY_LEVELS value; plan said "hypothesis" which does NOT exist
    assert plan_item["required_fields"]["maturity_level"] == "exploratory"
    assert "evidence" not in result["selected_record_types"]


# --------------------------------------------------------------------------- #
# 4. tool_run verified result can plan evidence
# --------------------------------------------------------------------------- #

def test_tool_run_verified_result_can_plan_evidence(tmp_path):
    from brain.v5.lightweight_record_router import plan_lightweight_record_write

    ws, claim, run = _make_tool_run(tmp_path)
    result = plan_lightweight_record_write(
        ws, topic_id="fqhe", current_session_id="s1", active_claim_id=claim.claim_id,
        event_summary="Reproducible tool run produced a checked energy gap result.",
        touched_tool_runs_or_evidence_refs=["tool_run:run-abc"],
    )
    assert result["decision"] == "plan_write"
    assert "evidence" in result["selected_record_types"]
    ev_plan = next(p for p in result["typed_write_plan"] if p["record_type"] == "evidence")
    # spec §6.4 puts tool_run_ids in optional_fields, not required_fields
    assert ev_plan["optional_fields"]["tool_run_ids"] == ["run-abc"]
    # verification_ref keeps the canonical prefixed form
    assert "tool_run:run-abc" in str(ev_plan["verification_refs"])


# --------------------------------------------------------------------------- #
# 5. runtime failure is not algorithm failure
# --------------------------------------------------------------------------- #

def test_runtime_failure_not_algorithm_failure(tmp_path):
    from brain.v5.lightweight_record_router import plan_lightweight_record_write

    ws, claim = _make_workspace(tmp_path, claim_id="claim-qsgw-final", statement="qsgw final report matplotlib rendering pipeline")
    result = plan_lightweight_record_write(
        ws, topic_id="fqhe", current_session_id="s1", active_claim_id=claim.claim_id,
        event_summary="脚本失败是因为远端环境 matplotlib dependency 问题,不是算法路线失败。",
    )
    assert result["decision"] == "plan_write"
    assert "sensemaking_report" in result["selected_record_types"]
    assert "evidence" not in result["selected_record_types"]
    summary = result["final_human_readable_summary"]
    assert "algorithm" in summary.lower() or "算法" in summary
    sm_plan = next(p for p in result["typed_write_plan"] if p["record_type"] == "sensemaking_report")
    assert "not an algorithm failure" in sm_plan["required_fields"]["summary"].lower() or "不是算法" in sm_plan["required_fields"]["summary"]


# --------------------------------------------------------------------------- #
# 6. active-claim mismatch does not default to active
# --------------------------------------------------------------------------- #

def test_active_claim_mismatch_does_not_default_to_active(tmp_path):
    from brain.v5.lightweight_record_router import plan_lightweight_record_write

    ws, claim_a, claim_b = _make_sibling_claims(tmp_path)
    # event_summary is about librpa QSGW (claim_b), active claim is claim_a (silicon G0W0)
    result = plan_lightweight_record_write(
        ws, topic_id="t", current_session_id="s1", active_claim_id=claim_a.claim_id,
        event_summary="记录一下 librpa QSGW self-consistent cycle convergence 的进展。",
    )
    # should NOT target the active claim_a
    assert result["target_claim"]["target_claim_id"] != claim_a.claim_id


# --------------------------------------------------------------------------- #
# 7. trust request only preflight, no apply
# --------------------------------------------------------------------------- #

def test_trust_request_only_preflight_no_apply(tmp_path):
    from brain.v5.lightweight_record_router import plan_lightweight_record_write

    ws, claim = _make_workspace(tmp_path)
    result = plan_lightweight_record_write(
        ws, topic_id="fqhe", current_session_id="s1", active_claim_id=claim.claim_id,
        event_summary="The FQHE energy gap finite-size evidence should promote confidence to verified.",
    )
    assert result["decision"] == "plan_write"
    assert "trust_preflight" in result["selected_record_types"]
    assert result["can_update_claim_trust"] is False
    tp_plan = next(p for p in result["typed_write_plan"] if p["record_type"] == "trust_preflight")
    assert tp_plan["recommended_mcp_tool"] == "aitp_v5_preflight_trust_update"
    # the apply tool must never be referenced
    assert "aitp_v5_apply_trust_update" not in str(result)


# --------------------------------------------------------------------------- #
# 8. native MCP tools/list advertises the planner
# --------------------------------------------------------------------------- #

def test_native_mcp_tools_list_advertises_planner():
    from brain.v5.native_mcp import _handle_request

    response = _handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response is not None
    tools = response.get("result", {}).get("tools", [])
    names = {t.get("name") for t in tools}
    assert "aitp_v5_plan_lightweight_record_write" in names
    planner = next(t for t in tools if t.get("name") == "aitp_v5_plan_lightweight_record_write")
    desc = (planner.get("description") or "").lower()
    assert "plan" in desc  # name/description must signal this is plan, not write


# --------------------------------------------------------------------------- #
# 9. runtime entrypoint catalog includes the planner
# --------------------------------------------------------------------------- #

def test_runtime_entrypoint_catalog_includes_planner():
    from brain.v5.runtime_entrypoint_catalog import RUNTIME_ENTRYPOINTS

    entry = RUNTIME_ENTRYPOINTS.get("lightweight_record_write_plan")
    assert entry is not None
    assert entry["mcp"] == "aitp_v5_plan_lightweight_record_write"
    assert entry["surface"] == "lightweight_record_write_plan"
    assert "plan-lightweight-write" in entry["cli"]


# --------------------------------------------------------------------------- #
# 10. contract rejects a plan that tries to update trust
# --------------------------------------------------------------------------- #

def test_contract_rejects_plan_that_can_update_trust():
    from brain.v5.contracts import ContractError
    from brain.v5.lightweight_record_router_contracts import require_valid_lightweight_record_write_plan

    bad_payload = {
        "kind": "lightweight_record_write_plan",
        "decision": "no_write",
        "target_claim": {"target_claim_id": "", "reason_for_target_claim": "n/a", "confidence": "low"},
        "write_reasons": [],
        "no_write_reason": "test",
        "selected_record_types": [],
        "typed_write_plan": [],
        "trust_boundary": {"can_update_claim_trust": True},  # forbidden
        "final_human_readable_summary": "x",
        "truth_source": "event_metadata_and_typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    with pytest.raises(ContractError):
        require_valid_lightweight_record_write_plan(bad_payload)


# --------------------------------------------------------------------------- #
# 11. bonus: planner never writes a record (orientation-only invariant)
# --------------------------------------------------------------------------- #

def test_planner_writes_nothing_to_disk(tmp_path):
    from brain.v5.lightweight_record_router import plan_lightweight_record_write

    ws, claim = _make_workspace(tmp_path, statement="FQHE final report plot")
    # count record files before
    before = sum(p.stat().st_size for p in (tmp_path / "ws").rglob("*.md"))
    result = plan_lightweight_record_write(
        ws, topic_id="fqhe", current_session_id="s1", active_claim_id=claim.claim_id,
        event_summary="old plot cannot mix with new final report.",
        touched_files_or_artifacts=["reports/old.png"],
    )
    after = sum(p.stat().st_size for p in (tmp_path / "ws").rglob("*.md"))
    assert result["decision"] == "plan_write"
    assert before == after  # no bytes written by the planner


# --------------------------------------------------------------------------- #
# 12. bonus: malformed ref -> unsupported, not silently stripped
# --------------------------------------------------------------------------- #

def test_malformed_ref_returns_unsupported(tmp_path):
    from brain.v5.lightweight_record_router import plan_lightweight_record_write

    ws, claim = _make_workspace(tmp_path)
    result = plan_lightweight_record_write(
        ws, topic_id="fqhe", current_session_id="s1", active_claim_id=claim.claim_id,
        event_summary="reproducible tool run produced a checked result.",
        touched_tool_runs_or_evidence_refs=["not-a-canonical-ref"],
    )
    assert result["decision"] in ("unsupported", "no_write")
