from __future__ import annotations

import json


def _seed_session(tmp_path):
    from brain.v5.evidence import record_evidence
    from brain.v5.tools import record_tool_run
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE Learning")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Finite-size counting identifies the FQHE edge sector.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size artifacts can mimic edge counting",
    )
    run = record_tool_run(
        ws,
        recipe_id="recipe-ed-counting",
        tool_family="toy_numeric",
        tool_name="exact-diagonalization",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        inputs={"sizes": [8, 10]},
        outputs={"counting_matches": True},
        evidence_status="supports",
    )
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="toy_numeric",
        status="supports",
        summary="ED counting was checked for two finite sizes with provenance.",
        supports_outputs=["evidence_or_provenance", "minimal_check"],
        tool_run_ids=[run.run_id],
    )
    bind_session(
        ws,
        "s1",
        topic_id="fqhe",
        context_id="topological-order",
        active_claim=claim.claim_id,
        active_route="route-ed-counting",
        active_cycle="cycle-fqhe-learning",
    )
    return ws, claim, run, evidence


def _invoke(args, capsys):
    from brain.v5.cli import main

    assert main(args) == 0
    output = capsys.readouterr().out
    return json.loads(output)


def test_write_session_summary_creates_plan_findings_progress_from_kernel_state(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.markdown import read_md
    from brain.v5.summaries import write_session_summary

    ws, claim, run, evidence = _seed_session(tmp_path)
    expected_action = build_execution_brief(ws, "s1")["next_action_candidates"][0]["action"]

    bundle = write_session_summary(ws, "s1")

    assert bundle.truth_source is False
    assert bundle.orientation_only is True
    assert set(bundle.files) == {"task_plan", "findings", "progress"}
    for role, path in bundle.files.items():
        fm, body = read_md(path)
        assert fm["kind"] == "derived_summary"
        assert fm["summary_role"] == role
        assert fm["derived_from"] == "kernel_state"
        assert fm["truth_source"] is False
        assert fm["orientation_only"] is True
        assert fm["session_id"] == "s1"
        assert fm["active_claim"] == claim.claim_id
        assert claim.statement in body

    _, findings = read_md(bundle.files["findings"])
    _, progress = read_md(bundle.files["progress"])
    _, task_plan = read_md(bundle.files["task_plan"])
    assert evidence.evidence_id in findings
    assert "ED counting was checked" in findings
    assert run.run_id in progress
    assert expected_action in task_plan


def test_summary_files_do_not_become_truth_source_when_edited(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.markdown import write_md
    from brain.v5.summaries import read_summary_orientation, write_session_summary
    from brain.v5.workspace import get_claim

    ws, claim, _, _ = _seed_session(tmp_path)
    bundle = write_session_summary(ws, "s1")
    write_md(
        bundle.files["findings"],
        {
            "kind": "derived_summary",
            "summary_role": "findings",
            "session_id": "s1",
            "truth_source": True,
        },
        "# Findings\n\nFALSE: this summary says the claim is already validated.\n",
    )

    brief = build_execution_brief(ws, "s1")
    persisted_claim = get_claim(ws, claim.claim_id)
    orientation = read_summary_orientation(ws, "s1")

    assert persisted_claim.statement == claim.statement
    assert brief["current_focus"]["claim_statement"] == claim.statement
    assert brief["current_focus"]["confidence_state"] == "hypothesis"
    assert orientation["truth_source"] is False
    assert orientation["orientation_only"] is True
    assert orientation["can_update_kernel_state"] is False


def test_rewriting_session_summary_regenerates_from_kernel_state(tmp_path):
    from brain.v5.markdown import read_md, write_md
    from brain.v5.summaries import write_session_summary

    ws, claim, _, _ = _seed_session(tmp_path)
    bundle = write_session_summary(ws, "s1")
    write_md(
        bundle.files["task_plan"],
        {"kind": "derived_summary", "summary_role": "task_plan", "session_id": "s1"},
        "# Task Plan\n\nFALSE PLAN: skip validation and promote immediately.\n",
    )

    regenerated = write_session_summary(ws, "s1")
    _, task_plan = read_md(regenerated.files["task_plan"])

    assert "FALSE PLAN" not in task_plan
    assert claim.statement in task_plan
    assert "promote immediately" not in task_plan


def test_cli_summary_session_returns_orientation_only_file_paths(tmp_path, capsys):
    _seed_session(tmp_path)

    payload = _invoke(["--base", str(tmp_path), "summary", "session", "s1"], capsys)

    assert payload["ok"] is True
    assert payload["session_id"] == "s1"
    assert payload["truth_source"] is False
    assert payload["orientation_only"] is True
    assert set(payload["files"]) == {"task_plan", "findings", "progress"}
    assert payload["files"]["task_plan"].endswith("task_plan.md")


def test_cli_summary_orientation_returns_read_only_payload(tmp_path, capsys):
    from brain.v5.markdown import write_md
    from brain.v5.summaries import write_session_summary

    ws, _, _, _ = _seed_session(tmp_path)
    bundle = write_session_summary(ws, "s1")
    write_md(
        bundle.files["findings"],
        {
            "kind": "derived_summary",
            "summary_role": "findings",
            "session_id": "s1",
            "truth_source": True,
            "orientation_only": False,
        },
        "# Findings\n\nFALSE: this file claims authority.\n",
    )

    payload = _invoke(["--base", str(tmp_path), "summary", "orientation", "s1"], capsys)

    assert payload["ok"] is True
    assert payload["truth_source"] is False
    assert payload["orientation_only"] is True
    assert payload["can_update_kernel_state"] is False
    assert payload["files"]["findings"]["truth_source"] is False


def test_mcp_write_session_summary_returns_orientation_only_payload(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_write_session_summary

    _seed_session(tmp_path)

    payload = aitp_v5_write_session_summary(str(tmp_path), session_id="s1")

    assert payload["ok"] is True
    assert payload["truth_source"] is False
    assert payload["orientation_only"] is True
    assert payload["derived_from"] == "kernel_state"
    assert payload["files"]["findings"].endswith("findings.md")


def test_mcp_read_summary_orientation_returns_contract_payload(tmp_path):
    from brain.v5.contracts import validate_summary_orientation
    from brain.v5.mcp_tools import aitp_v5_read_summary_orientation, aitp_v5_write_session_summary

    _seed_session(tmp_path)
    aitp_v5_write_session_summary(str(tmp_path), session_id="s1")

    payload = aitp_v5_read_summary_orientation(str(tmp_path), session_id="s1")

    assert payload["ok"] is True
    assert payload["truth_source"] is False
    assert payload["orientation_only"] is True
    assert validate_summary_orientation(payload).ok is True
