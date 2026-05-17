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
