from __future__ import annotations


def test_init_workspace_creates_v5_layout(tmp_path):
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)

    assert ws.root == tmp_path / ".aitp"
    for rel in [
        "contexts",
        "topics",
        "registry/claims",
        "registry/questions",
        "registry/code_states",
        "registry/code_workspaces",
        "memory/l2/entries",
        "memory/code_provenance",
        "runtime/sessions",
    ]:
        assert (ws.root / rel).exists()
    assert (ws.root / "workspace.md").exists()


def test_markdown_store_round_trips_frontmatter_and_body(tmp_path):
    from brain.v5.markdown import read_md, write_md

    path = tmp_path / "record.md"
    write_md(path, {"kind": "test", "value": 3}, "# Body\n\nHello\n")

    fm, body = read_md(path)
    assert fm == {"kind": "test", "value": 3}
    assert "Hello" in body


def test_markdown_reader_ignores_body_table_dashes_when_splitting_frontmatter(tmp_path):
    from brain.v5.markdown import read_md

    path = tmp_path / "record.md"
    path.write_text(
        "---\n"
        "kind: test\n"
        "summary: table body follows\n"
        "---\n"
        "# Body\n\n"
        "| Symbol | Meaning |\n"
        "|--------|---------|\n"
        "| x | coordinate |\n",
        encoding="utf-8",
    )

    fm, body = read_md(path)
    assert fm == {"kind": "test", "summary": "table body follows"}
    assert "|--------|---------|" in body


def test_store_ignores_unknown_frontmatter_fields_for_forward_compatibility(tmp_path):
    from brain.v5.markdown import write_md
    from brain.v5.models import EvidenceRecord
    from brain.v5.store import read_record

    path = tmp_path / "evidence.md"
    write_md(
        path,
        {
            "evidence_id": "evidence-forward-compatible",
            "topic_id": "librpa-gw",
            "claim_id": "claim-librpa-gw",
            "evidence_type": "code_method",
            "status": "partial",
            "summary": "Old migrated records may carry fields unknown to this model.",
            "future_schema_extension": ["legacy-validation-result"],
            "kind": "evidence",
        },
        "# Evidence\n",
    )

    record = read_record(path, EvidenceRecord)

    assert record.evidence_id == "evidence-forward-compatible"
    assert record.summary.startswith("Old migrated records")
    assert not hasattr(record, "future_schema_extension")


def test_topic_context_and_session_binding_are_session_local(tmp_path):
    from brain.v5.workspace import (
        bind_session,
        create_context,
        create_topic,
        get_session_binding,
        init_workspace,
    )

    ws = init_workspace(tmp_path)
    create_context(ws, "topological-order", title="Topological Order")
    create_topic(ws, "fqhe-learning", context_id="topological-order", title="FQHE Learning")
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")

    bind_session(ws, session_id="s1", topic_id="fqhe-learning", context_id="topological-order")
    bind_session(ws, session_id="s2", topic_id="librpa-gw", context_id="gw-methods")

    assert get_session_binding(ws, "s1").topic_id == "fqhe-learning"
    assert get_session_binding(ws, "s2").topic_id == "librpa-gw"


def test_flow_resolver_keeps_trusted_recipe_light_and_new_claim_heavy(tmp_path):
    from brain.v5.flow import resolve_flow_profile
    from brain.v5.workspace import create_claim, init_workspace

    ws = init_workspace(tmp_path)
    routine = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="Si G0W0 benchmark stays within trusted tolerance.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="routine benchmark rerun",
        recipe_id="librpa-si-g0w0",
    )
    novel = create_claim(
        ws,
        topic_id="fqhe-learning",
        statement="The proposed finite-size signature detects fractional charge.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="new physical mechanism",
    )

    assert resolve_flow_profile(routine).profile == "fluid"
    assert resolve_flow_profile(novel).profile == "guided"


def test_question_engine_generates_state_conditioned_questions():
    from brain.v5.models import ClaimRecord, FlowDecision
    from brain.v5.question_engine import generate_questions

    claim = ClaimRecord(
        claim_id="claim-fqhe",
        topic_id="fqhe",
        statement="Entanglement spectrum identifies the FQHE edge theory.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="which finite-size signature is reliable",
    )
    flow = FlowDecision(profile="research", reason="new claim", escalation_triggers=[])

    questions = generate_questions(
        claim,
        flow,
        object_relations=["entanglement_spectrum measures edge_mode"],
    )

    text = "\n".join(q.question for q in questions)
    assert "relation" in text.lower()
    assert "failure" in text.lower() or "wrong" in text.lower()
    assert any(q.target_claim == "claim-fqhe" for q in questions)


def test_execution_brief_combines_session_claim_flow_and_questions(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Entanglement spectrum identifies the edge theory.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size reliability",
    )
    bind_session(
        ws,
        "s1",
        topic_id="fqhe",
        context_id="topological-order",
        active_claim=claim.claim_id,
    )

    brief = build_execution_brief(ws, "s1")

    assert brief["session"]["topic_id"] == "fqhe"
    assert brief["current_focus"]["active_claim"] == claim.claim_id
    assert brief["flow_profile"]["profile"] == "guided"
    assert brief["mandatory_reflection"]
    assert "forbidden_now" in brief


def test_execution_brief_skips_malformed_code_state_and_tool_run_records(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.markdown import write_md
    from brain.v5.models import CodeStateRecord, ToolRunRecord
    from brain.v5.store import write_record
    from brain.v5.summaries import write_session_summary
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qsgw", context_id="librpa-qsgw", title="QSGW")
    claim = create_claim(
        ws,
        topic_id="qsgw",
        statement="Final rows are separated from diagnostic rows.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="dirty code state may contaminate final plots",
    )
    bind_session(
        ws,
        "s1",
        topic_id="qsgw",
        context_id="librpa-qsgw",
        active_claim=claim.claim_id,
    )
    write_md(
        ws.registry_dir("code_states") / "malformed-code-state.md",
        {"kind": "code_state", "id": "legacy-malformed"},
        "# Legacy malformed code state\n",
    )
    write_md(
        ws.registry_dir("tool_runs") / "malformed-tool-run.md",
        {"kind": "tool_run", "id": "legacy-malformed"},
        "# Legacy malformed tool run\n",
    )
    write_md(
        ws.registry_dir("reference_locations") / "malformed-reference-location.md",
        {"kind": "reference_location", "id": "legacy-malformed"},
        "# Legacy malformed reference location\n",
    )
    write_record(
        ws.registry_dir("code_states") / "code-state-dirty.md",
        CodeStateRecord(
            code_state_id="code-state-dirty",
            repo_id="theory-workspace",
            upstream_remote="origin",
            upstream_branch="main",
            upstream_commit="abc123",
            local_branch="main",
            worktree_path=str(tmp_path),
            dirty=True,
            linked_records={"claim_id": claim.claim_id},
        ),
    )
    write_record(
        ws.registry_dir("tool_runs") / "tool-run-valid.md",
        ToolRunRecord(
            run_id="tool-run-valid",
            recipe_id="recipe-final-lane-check",
            tool_family="python",
            tool_name="plot_guard",
            topic_id="qsgw",
            claim_id=claim.claim_id,
        ),
    )

    brief = build_execution_brief(ws, "s1")

    assert brief["current_focus"]["active_claim"] == claim.claim_id
    assert any(
        signal["kind"] == "reproducibility_risk"
        for signal in brief["risk_assessment"]["signals"]
    )
    summary = write_session_summary(ws, "s1")
    assert summary.source_records["tool_runs"] == ["tool-run-valid"]


def test_list_evidence_for_claim_skips_malformed_legacy_records(tmp_path):
    from brain.v5.evidence import list_evidence_for_claim, record_evidence
    from brain.v5.markdown import write_md
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qsgw", context_id="librpa-qsgw", title="QSGW")
    claim = create_claim(
        ws,
        topic_id="qsgw",
        statement="Final rows are separated from diagnostic rows.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="diagnostic rows may be mistaken for final rows",
    )
    write_md(
        ws.registry_dir("evidence") / "legacy-malformed-evidence.md",
        {"kind": "evidence", "id": "legacy-malformed"},
        "# Legacy malformed evidence\n",
    )
    evidence = record_evidence(
        ws,
        topic_id="qsgw",
        claim_id=claim.claim_id,
        evidence_type="code_method",
        status="supports",
        summary="Plot guard uses final-lane allowlist.",
    )

    records = list_evidence_for_claim(ws, claim.claim_id)

    assert [record.evidence_id for record in records] == [evidence.evidence_id]


def test_execution_brief_highlights_orientation_operating_notes(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.references import record_reference_location
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qsgw-headwing-update-librpa", context_id="librpa-qsgw", title="QSGW")
    claim = create_claim(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        statement="Final comparison uses final-lane rows only.",
        evidence_profile="code_method",
        confidence_state="partial",
        active_uncertainty="diagnostic rows may be confused with final rows",
    )
    bind_session(
        ws,
        "qsgw-session",
        topic_id="qsgw-headwing-update-librpa",
        context_id="librpa-qsgw",
        active_claim=claim.claim_id,
    )
    record_reference_location(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        claim_id=claim.claim_id,
        connector_id="local_report",
        location_type="strategy_note",
        uri="file:///reports/aitp_qsgw_dual_lane.md",
        label="QSGW dual-lane strategy",
        status="active_strategy_note",
        summary="Final lane uses usable_for_final rows; diagnostic lane is nonfinal.",
        metadata={
            "lane_policy": "final_vs_diagnostic",
            "final_lane_gate": "usable_for_final=True for QSGW",
            "diagnostic_lane_labels": ["diagnostic", "iter20_assumed", "nonfinal"],
            "forbidden_root": "/bad/root",
            "clean_mgo_root": "/clean/root",
        },
        linked_records={"artifact_role": "agent_operating_strategy"},
    )

    brief = build_execution_brief(ws, "qsgw-session")
    notes = brief["known_context"]["operating_notes"]

    assert [note["label"] for note in notes] == ["QSGW dual-lane strategy"]
    assert notes[0]["orientation_only"] is True
    assert notes[0]["lane_policy"] == "final_vs_diagnostic"
    assert notes[0]["final_lane_gate"] == "usable_for_final=True for QSGW"
    assert notes[0]["diagnostic_lane_labels"] == ["diagnostic", "iter20_assumed", "nonfinal"]
    assert notes[0]["forbidden_root"] == "/bad/root"
    assert notes[0]["clean_root"] == "/clean/root"
    assert brief["known_context"]["reference_locations"][0]["orientation_only"] is True


def test_code_state_and_workspace_records_make_code_results_reproducible(tmp_path):
    from brain.v5.code import record_code_state, record_code_workspace
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    cw = record_code_workspace(
        ws,
        topic_id="librpa-gw",
        session_id="s1",
        repo_id="librpa",
        worktree_path="D:/worktrees/librpa/headwing-test",
        branch_name="topic/headwing-test",
        base_commit="abc123",
        purpose="test head-wing patch",
    )
    cs = record_code_state(
        ws,
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="master",
        upstream_commit="abc123",
        local_branch="topic/headwing-test",
        worktree_path=cw.worktree_path,
        dirty=False,
        patch_id="patch-headwing-v1",
        build_config={"compiler": "gcc", "cmake_options": ["-DUSE_MPI=ON"]},
    )

    assert cs.code_state_id.startswith("code-state-librpa-")
    assert (ws.root / "registry" / "code_states" / f"{cs.code_state_id}.md").exists()
