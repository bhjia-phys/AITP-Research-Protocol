from __future__ import annotations

import json


def _seed_workspace(tmp_path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="A diagnostic invariant may distinguish edge theories.",
        evidence_profile="source_and_validation",
        confidence_state="hypothesis",
        active_uncertainty="finite evidence may not survive source review",
    )
    bind_session(ws, "s1", topic_id="fqhe", context_id="topological-order", active_claim=claim.claim_id)
    return ws, claim


def test_research_run_records_are_canonical_process_surface(tmp_path):
    from brain.v5.contracts import require_valid_research_run_event_record, require_valid_research_run_record
    from brain.v5.markdown import read_md
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.research_runs import (
        record_research_run_event,
        research_run_event_payload,
        research_run_payload,
        start_research_run,
        update_research_run,
    )

    ws, claim = _seed_workspace(tmp_path)

    run = start_research_run(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        session_id="s1",
        objective="Answer the scoped edge-theory diagnostic question.",
        research_question="Is the diagnostic invariant validated or only finite evidence?",
        operator="human",
        title="Edge diagnostic audit",
        hypothesis="The invariant is diagnostic until source review and validation pass.",
        metadata={"host": "hakimi"},
    )
    event = record_research_run_event(
        ws,
        run_id=run.run_id,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        session_id="s1",
        operator="hakimi",
        event_type="context_refreshed",
        summary="Read the current AITP process graph before choosing actions.",
        phase="context_refresh",
        source_refs=["source_asset:source-a"],
        payload={"slice_ref": "aitp:process_graph_slice:s1"},
    )
    updated = update_research_run(
        ws,
        run_id=run.run_id,
        topic_id="fqhe",
        operator="hakimi",
        status="paused",
        phase="awaiting_approval",
        terminal_answer_state="draft_only",
        stop_reason="paused before trust-changing writes",
        source_refs=["source_asset:source-a"],
        action_refs=["ResearchAction.search_aitp_curated_rag_corpus"],
        event_type="status_changed",
        event_summary="Paused after context refresh.",
    )

    run_payload = research_run_payload(updated)
    event_payload = research_run_event_payload(event)
    assert require_valid_research_run_record(run_payload) == run_payload
    assert require_valid_public_surface("research_run_record", run_payload) == run_payload
    assert require_valid_research_run_event_record(event_payload) == event_payload
    assert require_valid_public_surface("research_run_event_record", event_payload) == event_payload
    assert updated.summary_inputs_trusted is False
    assert updated.orientation_only is True
    assert updated.can_update_claim_trust is False
    assert updated.status == "paused"
    assert updated.terminal_answer_state == "draft_only"
    assert updated.operator_trail[-1]["operator"] == "hakimi"
    assert event.can_update_claim_trust is False

    registry_fm, registry_body = read_md(ws.registry_dir("research_runs") / f"{run.run_id}.md")
    assert registry_fm["kind"] == "research_run"
    assert "does not validate evidence or update claim trust" in registry_body
    event_fm, event_body = read_md(ws.registry_dir("research_run_events") / f"{event.event_id}.md")
    assert event_fm["kind"] == "research_run_event"
    assert "not evidence, validation, or trust promotion" in event_body
    runtime_json = json.loads(
        (ws.topic_dir("fqhe") / "runtime" / "research_runs" / f"{run.run_id}.json").read_text(encoding="utf-8")
    )
    assert runtime_json["run_id"] == run.run_id
    assert runtime_json["can_update_claim_trust"] is False


def test_research_runs_are_append_only_ledgers_for_repeated_objectives(tmp_path):
    from brain.v5.research_runs import record_research_run_event, start_research_run

    ws, claim = _seed_workspace(tmp_path)

    first = start_research_run(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        session_id="s1",
        objective="Audit the invariant.",
        research_question="Can it answer the scoped question?",
        operator="human",
    )
    second = start_research_run(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        session_id="s1",
        objective="Audit the invariant.",
        research_question="Can it answer the scoped question?",
        operator="human",
    )

    assert first.run_id != second.run_id
    assert (ws.registry_dir("research_runs") / f"{first.run_id}.md").exists()
    assert (ws.registry_dir("research_runs") / f"{second.run_id}.md").exists()

    try:
        record_research_run_event(
            ws,
            run_id=first.run_id,
            topic_id="other-topic",
            operator="hakimi",
            event_type="context_refreshed",
            summary="This should not cross topic boundaries.",
        )
    except ValueError as exc:
        assert "belongs to topic fqhe" in str(exc)
    else:
        raise AssertionError("expected cross-topic research run event to fail")


def test_research_run_cli_mcp_graph_and_bridge_target(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import (
        aitp_v5_record_research_run_event,
        aitp_v5_start_research_run,
        aitp_v5_update_research_run,
    )
    from brain.v5.native_mcp import _TOOLS
    from brain.v5.process_graph import build_process_graph_slice
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.record_refs import lookup_record_refs
    from brain.v5.runtime_bridge_targets import runtime_bridge_target_manifest
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ws, claim = _seed_workspace(tmp_path)
    assert main([
        "--base",
        str(tmp_path),
        "run",
        "research",
        "start",
        "--topic",
        "fqhe",
        "--claim",
        claim.claim_id,
        "--session",
        "s1",
        "--objective",
        "Audit the invariant.",
        "--question",
        "Can the invariant answer the scoped edge-theory question?",
        "--operator",
        "human",
    ]) == 0
    cli_run = json.loads(capsys.readouterr().out)

    mcp_run = aitp_v5_start_research_run(
        str(tmp_path),
        topic_id="fqhe",
        claim_id=claim.claim_id,
        session_id="s1",
        objective="Audit the source stack.",
        research_question="Which source and validation gaps remain?",
        operator="kimi",
    )
    event = aitp_v5_record_research_run_event(
        str(tmp_path),
        run_id=mcp_run["run_id"],
        topic_id="fqhe",
        claim_id=claim.claim_id,
        session_id="s1",
        operator="hakimi",
        event_type="action_selected",
        summary="Selected source-review action after context refresh.",
        phase="action_selection",
        action_ref="ResearchAction.inspect_aitp_curated_rag_chunk",
    )
    updated = aitp_v5_update_research_run(
        str(tmp_path),
        run_id=mcp_run["run_id"],
        topic_id="fqhe",
        operator="hakimi",
        status="active",
        phase="action_selection",
        action_refs=["ResearchAction.inspect_aitp_curated_rag_chunk"],
        event_summary="Recorded selected source-review action.",
    )

    assert cli_run["kind"] == "research_run"
    assert cli_run["operator"] == "human"
    assert mcp_run["kind"] == "research_run"
    assert event["kind"] == "research_run_event"
    assert updated["action_refs"] == ["ResearchAction.inspect_aitp_curated_rag_chunk"]
    assert updated["can_update_claim_trust"] is False

    graph = build_process_graph_slice(ws, "s1", limit=80)
    assert require_valid_public_surface("process_graph_slice", graph) == graph
    node_types = {node["type"] for node in graph["nodes"]}
    assert "research_run" in node_types
    assert "research_run_event" in node_types
    assert graph["record_counts"]["research_run"] == 2
    assert graph["record_counts"]["research_run_event"] >= 3
    edges = {(edge["source"], edge["type"], edge["target"]) for edge in graph["edges"]}
    assert (f"claim:{claim.claim_id}", "has_research_run", f"research_run:{mcp_run['run_id']}") in edges
    assert (
        f"research_run:{mcp_run['run_id']}",
        "has_run_event",
        f"research_run_event:{event['event_id']}",
    ) in edges

    refs = lookup_record_refs(ws, [f"research_run:{mcp_run['run_id']}", f"research_run_event:{event['event_id']}"])
    assert refs["found_count"] == 2
    assert refs["refs"][0]["surface"] == "research_run_record"
    assert refs["refs"][1]["surface"] == "research_run_event_record"
    assert require_valid_public_surface("record_ref_lookup", refs) == refs

    entrypoints = runtime_entrypoints()
    assert entrypoints["start_research_run"] == {
        "cli": "aitp-v5 run research start <args>",
        "mcp": "aitp_v5_start_research_run",
        "surface": "research_run_record",
    }
    assert entrypoints["update_research_run"]["surface"] == "research_run_record"
    assert entrypoints["record_research_run_event"]["surface"] == "research_run_event_record"
    assert "aitp_v5_start_research_run" in _TOOLS
    assert "aitp_v5_update_research_run" in _TOOLS
    assert "aitp_v5_record_research_run_event" in _TOOLS

    by_operation = {target["operation"]: target for target in runtime_bridge_target_manifest()["targets"]}
    assert by_operation["startResearchRun"]["entrypoint_key"] == "start_research_run"
    assert by_operation["startResearchRun"]["surface"] == "research_run_record"
    assert by_operation["startResearchRun"]["execution_role"] == "write"
    assert by_operation["startResearchRun"]["claim_trust_mutation"] == "none"
    assert by_operation["updateResearchRun"]["entrypoint_key"] == "update_research_run"
    assert by_operation["recordResearchRunEvent"]["surface"] == "research_run_event_record"
