from __future__ import annotations

import json


def _invoke(args, capsys):
    from brain.v5.cli import main

    assert main(args) == 0
    return json.loads(capsys.readouterr().out)


def _seed_workspace(tmp_path, *, session_id: str = "s-draft"):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qsgw-librpa", context_id="librpa", title="QSGW LibRPA workflow")
    claim = create_claim(
        ws,
        topic_id="qsgw-librpa",
        statement="The LibRPA QSGW continuation must keep diagnostic runs out of final evidence.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="final lane validation is incomplete",
    )
    bind_session(
        ws,
        session_id,
        topic_id="qsgw-librpa",
        context_id="librpa",
        active_claim=claim.claim_id,
    )
    return ws, claim


def test_context_profile_draft_materializes_group_meeting_report_without_trust(tmp_path):
    from brain.v5.context_profile_drafts import build_context_profile_draft
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, _claim = _seed_workspace(tmp_path)

    draft = require_valid_public_surface(
        "context_profile_draft",
        build_context_profile_draft(ws, "s-draft", profile_id="group_meeting_report"),
    )

    assert draft["kind"] == "context_profile_draft"
    assert draft["draft_kind"] == "group_meeting_report_draft"
    assert draft["profile_id"] == "group_meeting_report"
    assert draft["profile_template_hint"]["profile_id"] == "group_meeting_report"
    assert draft["read_only"] is True
    assert draft["orientation_only"] is True
    assert draft["draft_creates_records"] is False
    assert draft["can_update_claim_trust"] is False
    assert draft["claim_trust_mutation"] == "none"
    assert "profile_report_as_evidence" in draft["draft_policy"]["forbidden_uses"]
    section_ids = [section["section_id"] for section in draft["sections"]]
    assert section_ids == [
        "current_focus",
        "verified_content",
        "uncertainty",
        "records",
        "next_actions",
        "non_promotable_content",
    ]
    assert "AITP Group Meeting Draft" in draft["markdown"]
    assert "not evidence, validation, memory, final gate, or trust update" in draft["markdown"]


def test_context_profile_draft_cli_and_mcp_materialize_closeout(tmp_path, capsys):
    from brain.v5.mcp_tools import aitp_v5_build_context_profile_draft

    _seed_workspace(tmp_path, session_id="s-cli")

    cli_draft = _invoke(
        [
            "--base",
            str(tmp_path),
            "status",
            "context-profile-draft",
            "s-cli",
            "--profile",
            "closeout",
        ],
        capsys,
    )
    mcp_draft = aitp_v5_build_context_profile_draft(
        str(tmp_path),
        session_id="s-cli",
        profile_id="closeout",
    )

    assert cli_draft == mcp_draft
    assert cli_draft["draft_kind"] == "closeout_draft"
    assert cli_draft["profile_id"] == "closeout"
    assert [section["section_id"] for section in cli_draft["sections"]] == [
        "durable_records_created",
        "missing_typed_records",
        "must_verify_next",
        "safe_resume_entrypoints",
        "non_promotable_content",
    ]
    assert cli_draft["source_records"]["derived_surfaces"] == [
        "aitp_context_pack",
        "context_profile_template_catalog",
        "compact_execution_brief",
    ]
