from __future__ import annotations

import json
from pathlib import Path


def _setup_topic(tmp_path: Path):
    from brain.v5.workspace import bind_session, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "qsgw-headwing-update-librpa", context_id="librpa", title="QSGW head-wing")
    bind_session(
        ws,
        "qsgw-session",
        topic_id="qsgw-headwing-update-librpa",
        context_id="librpa",
    )
    return ws


def test_record_final_output_profile_writes_versioned_contract(tmp_path):
    from brain.v5.markdown import read_md
    from brain.v5.output_stability import record_final_output_profile
    from brain.v5.public_surfaces import require_valid_public_surface

    ws = _setup_topic(tmp_path)

    profile = record_final_output_profile(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        output_version="qsgw-dual-lane-v1",
        audience="future_agent_and_human_operator",
        stable_sections=["current_data_state", "final_lane", "diagnostic_lane", "forbidden_roots", "next_actions"],
        flexible_sections=["open_questions", "recent_chat_context"],
        change_policy="Breaking layout changes require a new output_version and compatibility note.",
        compatibility_note="Keep final and diagnostic lane labels stable for existing QSGW reports.",
    )

    md_path = ws.topic_dir("qsgw-headwing-update-librpa") / "runtime" / "final_output_profile.md"
    json_path = ws.topic_dir("qsgw-headwing-update-librpa") / "runtime" / "final_output_profile.json"
    ledger_path = ws.topic_dir("qsgw-headwing-update-librpa") / "runtime" / "final_output_profiles.jsonl"
    fm, body = read_md(md_path)
    raw_json = json.loads(json_path.read_text(encoding="utf-8"))
    ledger = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]

    assert fm["kind"] == "final_output_profile"
    assert raw_json["output_version"] == "qsgw-dual-lane-v1"
    assert "final_lane" in body
    assert ledger[-1]["profile_id"] == profile.profile_id
    assert profile.can_update_claim_trust is False
    assert require_valid_public_surface("final_output_profile", {"ok": True, **profile.__dict__})


def test_execution_brief_exposes_final_output_profile(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.output_stability import record_final_output_profile

    ws = _setup_topic(tmp_path)
    record_final_output_profile(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        output_version="qsgw-dual-lane-v1",
        audience="future_agent_and_human_operator",
        stable_sections=["current_data_state", "final_lane", "diagnostic_lane"],
        flexible_sections=["open_questions"],
        change_policy="Additive changes only inside existing sections unless output_version changes.",
    )

    brief = build_execution_brief(ws, "qsgw-session")
    profile = brief["known_context"]["final_output_profile"]

    assert profile["present"] is True
    assert profile["output_version"] == "qsgw-dual-lane-v1"
    assert profile["stable_sections"] == ["current_data_state", "final_lane", "diagnostic_lane"]
    assert profile["can_update_claim_trust"] is False


def test_final_output_profile_cli_mcp_and_runtime_surfaces(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_record_final_output_profile
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ws = _setup_topic(tmp_path)

    assert main(
        [
            "--base",
            str(ws.base),
            "output",
            "profile",
            "record",
            "--topic",
            "qsgw-headwing-update-librpa",
            "--version",
            "qsgw-dual-lane-v1",
            "--audience",
            "future_agent",
            "--stable-section",
            "final_lane",
            "--stable-section",
            "diagnostic_lane",
            "--flexible-section",
            "open_questions",
            "--change-policy",
            "Breaking changes require a new version.",
        ]
    ) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_record_final_output_profile(
        str(ws.base),
        topic_id="qsgw-headwing-update-librpa",
        output_version="qsgw-dual-lane-v1",
        audience="future_agent",
        stable_sections=["final_lane", "diagnostic_lane"],
        flexible_sections=["open_questions"],
        change_policy="Breaking changes require a new version.",
    )

    assert require_valid_public_surface("final_output_profile", cli_payload) == cli_payload
    assert require_valid_public_surface("final_output_profile", mcp_payload) == mcp_payload
    assert runtime_entrypoints()["record_final_output_profile"] == {
        "cli": "aitp-v5 output profile record <args>",
        "mcp": "aitp_v5_record_final_output_profile",
        "surface": "final_output_profile",
    }


def test_aitp_spec_documents_human_facing_output_stability_spine():
    spec = Path("docs/AITP_SPEC.md").read_text(encoding="utf-8")

    assert "### Human-Facing Output Stability Contract" in spec
    for section in [
        "Core claim or current focus.",
        "Verified or validated content.",
        "Hypotheses, uncertainty, and known failure modes.",
        "AITP records written or referenced.",
        "Next actions.",
        "Long-term memory candidates and content that must not be promoted.",
    ]:
        assert section in spec
    assert "major protocol-version change" in spec
