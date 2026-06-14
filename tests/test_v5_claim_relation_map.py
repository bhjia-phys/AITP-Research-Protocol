from __future__ import annotations

import json
from pathlib import Path


def _setup_h2o_si_runtime_failure_workspace(
    tmp_path: Path,
    *,
    next_action: str = "Reproduce Si thiele baseline with the same executable, then rerun ridge.",
):
    from brain.v5.evidence import record_evidence
    from brain.v5.research_state import update_claim_status
    from brain.v5.tools import record_tool_run
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "qsgw-ac-error-molecules", context_id="librpa", title="QSGW AC error molecules")
    claim = create_claim(
        ws,
        topic_id="qsgw-ac-error-molecules",
        statement="For H2O one-iteration LibRPA QSGW diagnostics, ridge-regularized Pade reduces analytic-continuation error amplification compared with Thiele Pade.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="Cross-system Si gap and analytic-continuation behavior are not yet tested.",
    )
    h2o_support = record_evidence(
        ws,
        topic_id="qsgw-ac-error-molecules",
        claim_id=claim.claim_id,
        evidence_type="bounded_numerical_replay",
        status="supports_scoped_claim",
        summary="H2O dump plus one-iteration C++ replay support that ridge reduces AC error amplification. Failure mode remains ridge bias, and the executable path is recorded only as provenance.",
        supports_outputs=["h2o_ac_error_amplification_reduction"],
        source_refs=["artifact:h2o-dump", "tool_run:h2o-one-iteration-replay", "local:/tmp/executable/path"],
    )
    gap_limit = record_evidence(
        ws,
        topic_id="qsgw-ac-error-molecules",
        claim_id=claim.claim_id,
        evidence_type="gap_audit",
        status="mixed",
        summary="H2O gap audit limits the claim: strong ridge parameters may change the gap.",
        supports_outputs=["gap_bias_boundary"],
        source_refs=["artifact:h2o-gap-audit"],
    )
    si_run = record_tool_run(
        ws,
        recipe_id="si-g0w0-pade-baseline",
        tool_family="remote_numerics",
        tool_name="slurm-librpa",
        topic_id="qsgw-ac-error-molecules",
        claim_id=claim.claim_id,
        inputs={"system": "Si", "baseline": "thiele"},
        outputs={
            "job_id": "2023865",
            "failure_scope": "application/runtime",
            "failure_stage": "pre_ac",
            "failure_reason": "ScaLAPACK Wc executable path failed before analytic continuation",
        },
        evidence_status="failed",
        source_refs=["slurm:2023865"],
    )
    si_failure = record_evidence(
        ws,
        topic_id="qsgw-ac-error-molecules",
        claim_id=claim.claim_id,
        evidence_type="runtime_failure",
        status="negative",
        summary="Si job 2023865 failed before analytic continuation because of ScaLAPACK Wc / executable path; this falsifies application, not the ridge algorithm.",
        supports_outputs=["si_runtime_attempt"],
        tool_run_ids=[si_run.run_id],
        source_refs=["slurm:2023865"],
    )
    update_claim_status(
        ws,
        topic_id="qsgw-ac-error-molecules",
        claim_id=claim.claim_id,
        maturity_level="finite-size evidence",
        claim_status="hypothesis_with_runtime_blocker",
        scope="H2O one-iteration replay supports AC amplification reduction; Si cross-system test has not entered AC.",
        risk="Si runtime failure can be mistaken for algorithm evidence",
        next_action=next_action,
        open_gaps=[
            "Si task target is cross-system gap and AC comparison, but current Si result is a runtime failure before AC.",
            "Strong ridge parameters may alter the gap and need separate audit.",
        ],
        evidence_refs=[h2o_support.evidence_id, gap_limit.evidence_id, si_failure.evidence_id],
    )
    bind_session(
        ws,
        "qsgw-si-recovery",
        topic_id="qsgw-ac-error-molecules",
        context_id="librpa",
        active_claim=claim.claim_id,
    )
    return ws, claim, h2o_support, gap_limit, si_failure, si_run


def test_claim_relation_map_separates_runtime_failure_from_algorithm_failure(tmp_path):
    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim, h2o_support, gap_limit, si_failure, si_run = _setup_h2o_si_runtime_failure_workspace(tmp_path)

    relation_map = build_claim_relation_map(ws, "qsgw-si-recovery")

    assert require_valid_public_surface("claim_relation_map", relation_map) == relation_map
    assert relation_map["claim_id"] == claim.claim_id
    assert [entry["record_id"] for entry in relation_map["supported_by"]] == [h2o_support.evidence_id]
    assert gap_limit.evidence_id in {entry["record_id"] for entry in relation_map["limited_by"]}
    assert si_failure.evidence_id in {entry["record_id"] for entry in relation_map["not_tested_by"]}
    assert si_run.run_id in {entry["record_id"] for entry in relation_map["not_tested_by"]}
    assert relation_map["contradicted_by"] == []
    assert any("runtime/application failures" in item for item in relation_map["current_conclusion"]["cannot_say"])
    assert any("ScaLAPACK" in item for item in relation_map["current_blockers"])
    assert relation_map["next_valid_actions"] == [
        "Reproduce Si thiele baseline with the same executable, then rerun ridge."
    ]
    assert relation_map["trust_update_allowed"] is False
    assert relation_map["can_update_claim_trust"] is False


def test_claim_relation_map_prioritizes_runtime_blocker_next_action_over_generic_status(tmp_path):
    from brain.v5.claim_relation_map import build_claim_relation_map

    ws, *_ = _setup_h2o_si_runtime_failure_workspace(
        tmp_path,
        next_action="collect_required_evidence_or_provenance",
    )

    relation_map = build_claim_relation_map(ws, "qsgw-si-recovery")

    assert relation_map["next_valid_actions"][0] == (
        "resolve the runtime/application blocker, then rerun the same-executable "
        "Thiele baseline before interpreting ridge evidence"
    )
    assert "collect_required_evidence_or_provenance" in relation_map["next_valid_actions"]


def test_claim_relation_map_is_forced_into_brief_topic_status_cli_and_mcp(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_get_claim_relation_map, aitp_v5_get_execution_brief
    from brain.v5.topic_status import write_topic_status_surfaces

    ws, claim, _, _, si_failure, _ = _setup_h2o_si_runtime_failure_workspace(tmp_path)

    assert main(["--base", str(ws.base), "relation-map", "qsgw-si-recovery"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_get_claim_relation_map(str(ws.base), session_id="qsgw-si-recovery")
    brief = aitp_v5_get_execution_brief(str(ws.base), session_id="qsgw-si-recovery")
    bundle = write_topic_status_surfaces(ws, session_id="qsgw-si-recovery")

    for payload in (cli_payload, mcp_payload, brief["claim_relation_map"], bundle["topic_state"]["claim_relation_map"]):
        assert payload["kind"] == "claim_relation_map"
        assert payload["claim_id"] == claim.claim_id
        assert si_failure.evidence_id in {entry["record_id"] for entry in payload["not_tested_by"]}
        assert payload["contradicted_by"] == []

    relation_map_path = Path(bundle["files"]["claim_relation_map"])
    session_start = Path(bundle["files"]["session_start"]).read_text(encoding="utf-8")
    assert relation_map_path.exists()
    assert "Current Relation Map" in relation_map_path.read_text(encoding="utf-8")
    assert "Cannot say" in session_start
    assert "runtime/application failures" in session_start
