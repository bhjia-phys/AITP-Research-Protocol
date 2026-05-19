"""Tests for AITP v5 local sense-making report records."""

from dataclasses import asdict
from pathlib import Path

import pytest


def _init_ws(tmp_path: Path):
    from brain.v5.workspace import init_workspace

    return init_workspace(tmp_path / "ws")


def _setup_claim(tmp_path: Path):
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "fqhe", context_id="ctx", title="FQHE counting")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Edge sector counting matches bulk filling fraction.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size effects may spoil the count",
    )
    return ws, claim


def test_record_sensemaking_report_is_orientation_not_validation(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.sensemaking import record_sensemaking_report

    report = record_sensemaking_report(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        title="Edge counting sanity check",
        summary="The edge sector count matches the bulk filling fraction for N=8.",
        object_ids=["object-sector-8"],
        relation_ids=["relation-edge-bulk"],
        evidence_refs=["evidence-fqhe-counting"],
        open_questions=["Does this hold for N=12?"],
        next_actions=["run_finite_size_check"],
    )

    payload = {"ok": True, **asdict(report)}
    assert payload["kind"] == "sensemaking_report"
    assert payload["validation_status"] == "not_validation"
    validated = require_valid_public_surface("sensemaking_report_record", payload)
    assert validated["report_id"]
    assert validated["title"] == "Edge counting sanity check"


def test_sensemaking_report_contract_rejects_validation_status(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.sensemaking import record_sensemaking_report

    report = record_sensemaking_report(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        title="Should not validate",
        summary="This tries to use a validation status.",
        validation_status="validated",
    )

    payload = {"ok": True, **asdict(report)}
    with pytest.raises(Exception, match="sensemaking"):
        require_valid_public_surface("sensemaking_report_record", payload)


def test_record_sensemaking_report_persists(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.sensemaking import record_sensemaking_report
    from brain.v5.store import list_records
    from brain.v5.models import SensemakingReportRecord

    report = record_sensemaking_report(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        title="Persisted report",
        summary="Should be readable from disk.",
    )

    records = list_records(ws.registry_dir("sensemaking_reports"), SensemakingReportRecord)
    assert len(records) == 1
    assert records[0].report_id == report.report_id


def test_sensemaking_cli_json_output(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.cli import main
    import json

    result = main(
        [
            "--base",
            str(tmp_path / "ws"),
            "sensemaking",
            "report",
            "--topic",
            claim.topic_id,
            "--claim",
            claim.claim_id,
            "--title",
            "CLI report",
            "--summary",
            "Report from CLI.",
        ]
    )
    assert result == 0


def test_sensemaking_mcp_valid_surface(tmp_path):
    ws, claim = _setup_claim(tmp_path)

    from brain.v5.mcp_tools import aitp_v5_record_sensemaking_report

    result = aitp_v5_record_sensemaking_report(
        str(tmp_path / "ws"),
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        title="MCP report",
        summary="Report from MCP.",
    )
    assert result["ok"] is True
    assert result["kind"] == "sensemaking_report"
    assert result["validation_status"] == "not_validation"


def test_sensemaking_runtime_entrypoint_exists():
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ep = runtime_entrypoints()
    assert "record_sensemaking_report" in ep
    assert ep["record_sensemaking_report"]["surface"] == "sensemaking_report_record"
