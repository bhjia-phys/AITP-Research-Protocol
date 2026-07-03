from __future__ import annotations

import json


def _seed_workspace(tmp_path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qsgw-headwing-update-librpa", context_id="librpa", title="QSGW head-wing")
    claim = create_claim(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        statement="The final and diagnostic lanes remain separated.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="diagnostic rows may be mistaken for final evidence",
    )
    bind_session(
        ws,
        "qsgw-session",
        topic_id="qsgw-headwing-update-librpa",
        context_id="librpa",
        active_claim=claim.claim_id,
    )
    return ws, claim


def test_record_lane_exemplar_writes_topic_local_runtime_artifacts(tmp_path):
    from brain.v5.lane_exemplars import build_lane_exemplar_manifest, record_lane_exemplar
    from brain.v5.markdown import read_md
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _seed_workspace(tmp_path)

    exemplar = record_lane_exemplar(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        lane="code_backed_algorithm",
        title="QSGW final/diagnostic dual-lane workflow",
        summary="ABACUS->PyATB->LibRPA status refresh is useful only when final and diagnostic rows stay separated.",
        claim_id=claim.claim_id,
        run_id="aitp-vnext-workflow-20260528",
        gates_demonstrated=["G1_source_grounding", "G2_executability", "G3_verification", "G4_human_steering"],
        artifact_refs=["surface:iteration_journal.md", "report:research/librpa/reports/qsgw_status.tsv"],
        domain_pack_refs=["gw_librpa"],
        context_profile_refs=["librpa_run_continuation"],
        skill_refs=["oh-my-librpa"],
        surface_refs=["aitp_context_pack", "tool_run_record", "validation_result_record"],
        validation_surface_refs=["validation_contract_record", "validation_result_record"],
        workflow_steps=[{"step_id": "record_run", "purpose": "Record the run before evidence promotion."}],
        failure_modes=[{"failure_id": "final_diagnostic_lane_mix", "required_basis": ["lane_contract_record"]}],
        forbidden_uses=["Do not promote diagnostic rows as final evidence."],
        can_say=["The workflow keeps final and diagnostic lanes separate."],
        cannot_say=["The QSGW conclusion is validated."],
        required_next_records=["tool_run_record", "validation_result_record"],
        promotion_blockers=["missing passed validation_result_ids"],
        trust_boundary="Records workflow adequacy only; does not validate a scientific QSGW conclusion.",
        source_refs=["vnext:phase5", "session:qsgw-session"],
        status="accepted",
    )

    assert exemplar.kind == "lane_exemplar"
    assert exemplar.lane == "code_backed_algorithm"
    assert exemplar.domain_pack_refs == ["gw_librpa"]
    assert exemplar.context_profile_refs == ["librpa_run_continuation"]
    assert exemplar.skill_refs == ["oh-my-librpa"]
    assert exemplar.workflow_steps[0]["step_id"] == "record_run"
    assert exemplar.failure_modes[0]["failure_id"] == "final_diagnostic_lane_mix"
    assert exemplar.can_update_claim_trust is False
    assert require_valid_public_surface("lane_exemplar_record", {"ok": True, **exemplar.__dict__})

    runtime_dir = ws.topic_dir("qsgw-headwing-update-librpa") / "runtime"
    ledger = [
        json.loads(line)
        for line in (runtime_dir / "lane_exemplars.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert ledger[0]["exemplar_id"] == exemplar.exemplar_id
    fm, body = read_md(runtime_dir / "lane_exemplars" / f"{exemplar.exemplar_id}.md")
    assert fm["kind"] == "lane_exemplar"
    assert "does not validate a scientific QSGW conclusion" in body
    assert "Domain packs" in body
    assert "gw_librpa" in body
    assert "record_run" in body

    manifest = build_lane_exemplar_manifest(ws)
    assert manifest["kind"] == "lane_exemplar_manifest"
    assert manifest["covered_lanes"] == ["code_backed_algorithm"]
    assert manifest["missing_lanes"] == ["toy_numeric", "semi_formal_theory"]
    assert manifest["lane_status_counts"]["code_backed_algorithm"]["accepted"] == 1
    assert manifest["items"][0]["domain_pack_refs"] == ["gw_librpa"]
    assert manifest["items"][0]["surface_refs"] == [
        "aitp_context_pack",
        "tool_run_record",
        "validation_result_record",
    ]
    assert manifest["can_update_claim_trust"] is False
    assert require_valid_public_surface("lane_exemplar_manifest", manifest) == manifest


def test_execution_brief_and_topic_status_expose_topic_lane_exemplars(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.lane_exemplars import record_lane_exemplar
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.topic_status import write_topic_status_surfaces

    ws, claim = _seed_workspace(tmp_path)
    record_lane_exemplar(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        lane="code_backed_algorithm",
        title="QSGW workflow exemplar",
        summary="Reusable workflow exemplar for final/diagnostic lane separation.",
        claim_id=claim.claim_id,
        run_id="run-qsgw",
        gates_demonstrated=["G2_executability"],
        artifact_refs=["surface:topic_dashboard.md"],
        trust_boundary="Exemplar is workflow memory, not evidence.",
        status="accepted",
    )

    brief = build_execution_brief(ws, "qsgw-session")
    lane_exemplars = brief["known_context"]["lane_exemplars"]
    assert lane_exemplars["present"] is True
    assert lane_exemplars["items"][0]["lane"] == "code_backed_algorithm"
    assert lane_exemplars["can_update_claim_trust"] is False
    assert require_valid_public_surface("execution_brief", brief) == brief

    status = write_topic_status_surfaces(ws, session_id="qsgw-session")
    assert status["topic_state"]["lane_exemplars"]["items"][0]["title"] == "QSGW workflow exemplar"
    assert status["topic_state"]["lane_exemplars"]["can_update_claim_trust"] is False
    assert require_valid_public_surface("topic_status_bundle", status) == status


def test_lane_exemplar_cli_mcp_and_runtime_surfaces(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import (
        aitp_v5_build_lane_exemplar_manifest,
        aitp_v5_record_lane_exemplar,
        aitp_v5_record_librpa_code_backed_algorithm_exemplar,
    )
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ws, claim = _seed_workspace(tmp_path)

    assert main([
        "--base",
        str(tmp_path),
        "exemplar",
        "lane",
        "record",
        "--topic",
        "qsgw-headwing-update-librpa",
        "--lane",
        "code_backed_algorithm",
        "--title",
        "QSGW workflow exemplar",
        "--summary",
        "Dual-lane QSGW workflow exemplar.",
        "--claim",
        claim.claim_id,
        "--run",
        "run-qsgw",
        "--gate",
        "G2_executability",
        "--artifact-ref",
        "surface:iteration_journal.md",
        "--domain-pack-ref",
        "gw_librpa",
        "--context-profile-ref",
        "librpa_run_continuation",
        "--skill-ref",
        "oh-my-librpa",
        "--surface-ref",
        "aitp_context_pack",
        "--validation-surface-ref",
        "validation_result_record",
        "--workflow-step",
        "Record the run before validating it.",
        "--failure-mode",
        "final_diagnostic_lane_mix",
        "--forbidden-use",
        "No diagnostic-to-final promotion.",
        "--can-say",
        "The workflow has a lane split.",
        "--cannot-say",
        "The physics conclusion is validated.",
        "--required-next-record",
        "validation_result_record",
        "--promotion-blocker",
        "missing passed validation_result_ids",
        "--trust-boundary",
        "Workflow exemplar only.",
        "--status",
        "accepted",
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_record_lane_exemplar(
        str(ws.base),
        topic_id="qsgw-headwing-update-librpa",
        lane="toy_numeric",
        title="Toy finite-size diagnostic exemplar",
        summary="Toy numeric lane exemplar with explicit trust boundary.",
        gates_demonstrated=["G3_verification"],
        artifact_refs=["test:test_v5_lane_exemplars.py"],
        trust_boundary="Toy exemplar is not promoted memory.",
        status="accepted",
    )
    manifest_payload = aitp_v5_build_lane_exemplar_manifest(str(ws.base))

    assert cli_payload["kind"] == "lane_exemplar"
    assert cli_payload["can_update_claim_trust"] is False
    assert cli_payload["domain_pack_refs"] == ["gw_librpa"]
    assert cli_payload["workflow_steps"][0]["step_id"] == "manual_step_1"
    assert mcp_payload["lane"] == "toy_numeric"
    librpa_payload = aitp_v5_record_librpa_code_backed_algorithm_exemplar(
        str(ws.base),
        topic_id="qsgw-headwing-update-librpa",
        claim_id=claim.claim_id,
        run_id="run-librpa-gw",
    )
    assert librpa_payload["lane"] == "code_backed_algorithm"
    assert librpa_payload["domain_pack_refs"] == ["gw_librpa"]
    assert "librpa_run_continuation" in librpa_payload["context_profile_refs"]
    assert "oh-my-librpa" in librpa_payload["skill_refs"]
    assert "hpc_cockpit" in librpa_payload["surface_refs"]
    assert any(item["failure_id"] == "hpc_runtime_not_science" for item in librpa_payload["failure_modes"])
    assert "scheduler success" in librpa_payload["forbidden_uses"][0]
    assert manifest_payload["covered_lanes"] == ["toy_numeric", "code_backed_algorithm"]
    assert manifest_payload["can_update_claim_trust"] is False
    assert runtime_entrypoints()["record_lane_exemplar"] == {
        "cli": "aitp-v5 exemplar lane record <args>",
        "mcp": "aitp_v5_record_lane_exemplar",
        "surface": "lane_exemplar_record",
    }
    assert runtime_entrypoints()["record_librpa_code_backed_algorithm_exemplar"] == {
        "cli": "aitp-v5 exemplar lane record-librpa-code <args>",
        "mcp": "aitp_v5_record_librpa_code_backed_algorithm_exemplar",
        "surface": "lane_exemplar_record",
    }
    assert runtime_entrypoints()["lane_exemplar_manifest"] == {
        "cli": "aitp-v5 exemplar lane manifest",
        "mcp": "aitp_v5_build_lane_exemplar_manifest",
        "surface": "lane_exemplar_manifest",
    }


def test_builtin_librpa_code_backed_exemplar_links_context_domain_and_validation(tmp_path):
    from brain.v5.lane_exemplars import (
        build_lane_exemplar_manifest,
        record_librpa_code_backed_algorithm_exemplar,
    )
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _seed_workspace(tmp_path)

    record = record_librpa_code_backed_algorithm_exemplar(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        claim_id=claim.claim_id,
        run_id="run-qsgw-librpa",
    )

    assert record.lane == "code_backed_algorithm"
    assert record.status == "accepted"
    assert record.domain_pack_refs == ["gw_librpa"]
    assert record.context_profile_refs == [
        "librpa_run_continuation",
        "source_reconstruction",
        "group_meeting_report",
        "closeout",
    ]
    assert record.skill_refs == [
        "oh-my-librpa",
        "oh-my-librpa-abacus-librpa",
        "oh-my-librpa-fhi-aims-qsgw",
    ]
    assert {
        "context_profile_template_catalog",
        "aitp_context_pack",
        "context_profile_draft",
        "domain_pack_catalog",
        "domain_skill_shim_manifest",
        "hpc_cockpit",
        "lane_contract_record",
        "tool_run_record",
        "validation_contract_record",
        "validation_result_record",
        "claim_trust_audit",
    } <= set(record.surface_refs)
    assert record.workflow_steps[0]["step_id"] == "compile_librpa_context"
    assert record.workflow_steps[-1]["entrypoint"] == "aitp-v5 trust audit --claim <claim-id>"
    failure_ids = {item["failure_id"] for item in record.failure_modes}
    assert {
        "final_diagnostic_lane_mix",
        "hpc_runtime_not_science",
        "code_state_or_recipe_gap",
        "librpa_metadata_mismatch",
    } <= failure_ids
    assert "tool_run_record" in record.required_next_records
    assert "validation_result_record" in record.required_next_records
    assert record.can_update_claim_trust is False
    assert require_valid_public_surface("lane_exemplar_record", {"ok": True, **record.__dict__})

    manifest = build_lane_exemplar_manifest(ws)
    assert manifest["covered_lanes"] == ["code_backed_algorithm"]
    assert manifest["items"][0]["domain_pack_refs"] == ["gw_librpa"]
    assert "hpc_cockpit" in manifest["items"][0]["surface_refs"]
