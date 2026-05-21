from __future__ import annotations

import json


def _seed_claim(tmp_path, *, evidence_profile: str = "toy_numeric"):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "fqhe", context_id="topological-order", title="FQHE")
    claim = create_claim(
        ws,
        topic_id="fqhe",
        statement="Finite-size counting identifies the FQHE edge sector.",
        evidence_profile=evidence_profile,
        confidence_state="locally_checked",
        active_uncertainty="finite-size artifact may mimic counting",
    )
    bind_session(
        ws,
        "s1",
        topic_id="fqhe",
        context_id="topological-order",
        active_claim=claim.claim_id,
    )
    return ws, claim


def _seed_passed_validation_result(tmp_path):
    from brain.v5.tools import record_tool_run
    from brain.v5.validation import create_validation_contract, record_validation_result

    ws, claim = _seed_claim(tmp_path)
    contract = create_validation_contract(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        required_checks=["finite-size counting benchmark"],
        failure_modes=["finite-size artifact"],
        required_evidence_outputs=["counting_table"],
        tool_recipe_ids=["recipe-fqhe-ed"],
        executor_ids=["pytest"],
    )
    run = record_tool_run(
        ws,
        recipe_id="recipe-fqhe-ed",
        tool_family="numerical",
        tool_name="pytest",
        topic_id="fqhe",
        claim_id=claim.claim_id,
        outputs={"counting_table": "ok"},
    )
    result = record_validation_result(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        contract_id=contract.contract_id,
        tool_run_id=run.run_id,
        status="passed",
        checked_outputs=["counting_table"],
        summary="Required counting output was checked.",
    )
    return ws, claim, run, result


def _seed_tool_evidence_for_promotion(tmp_path, *, link_result_to_evidence: bool = True):
    from brain.v5.evidence import record_evidence

    ws, claim, run, result = _seed_passed_validation_result(tmp_path)
    evidence = record_evidence(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        evidence_type="toy_numeric",
        status="supports",
        summary="Tool-derived counting evidence.",
        tool_run_ids=[run.run_id],
        validation_result_ids=[result.result_id] if link_result_to_evidence else [],
    )
    return ws, claim, evidence, result


def _invoke(args, capsys):
    from brain.v5.cli import main

    assert main(args) == 0
    output = capsys.readouterr().out
    return json.loads(output)


def test_context_pre_tool_policy_blocks_l2_promotion_without_evidence(tmp_path):
    from brain.v5.pretool_policy import evaluate_context_pre_tool_policy
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _seed_claim(tmp_path)

    payload = evaluate_context_pre_tool_policy(
        ws,
        session_id="s1",
        action="promote_to_l2",
        claim_id=claim.claim_id,
        evidence_refs=[],
        risk_level="guided",
        source_kind="typed_records",
    )

    assert payload["kind"] == "hook_decision"
    assert payload["hook_name"] == "pre_tool"
    assert payload["action"] == "promote_to_l2"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["attach_evidence_ref"]
    assert payload["can_update_kernel_state"] is False
    assert payload["summary_inputs_trusted"] is False
    assert require_valid_public_surface("pre_tool_policy_decision", {"ok": True, **payload})["ok"] is True


def test_cli_context_pre_tool_policy_returns_contract_payload(tmp_path, capsys):
    from brain.v5.public_surfaces import require_valid_public_surface

    _, claim = _seed_claim(tmp_path)

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "policy",
            "pre-tool",
            "promote_to_l2",
            "--session",
            "s1",
            "--claim",
            claim.claim_id,
            "--source-kind",
            "typed_records",
        ],
        capsys,
    )

    assert payload["ok"] is True
    assert payload["kind"] == "hook_decision"
    assert payload["action"] == "promote_to_l2"
    assert payload["block"] is True
    assert payload["required_actions"] == ["attach_evidence_ref"]
    assert require_valid_public_surface("pre_tool_policy_decision", payload) == payload


def test_mcp_context_pre_tool_policy_warns_code_validation_without_code_state(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy
    from brain.v5.public_surfaces import require_valid_public_surface

    _, claim = _seed_claim(tmp_path, evidence_profile="code_method")

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="validate_claim",
        claim_id=claim.claim_id,
        risk_level="guided",
        source_kind="typed_records",
    )

    assert payload["ok"] is True
    assert payload["kind"] == "hook_decision"
    assert payload["action"] == "validate_claim"
    assert payload["mode"] == "warn"
    assert payload["block"] is False
    assert payload["required_actions"] == ["record_code_state"]
    assert require_valid_public_surface("pre_tool_policy_decision", payload) == payload


def test_cli_pre_tool_policy_exposes_machine_readable_summary_source_block(tmp_path, capsys):
    from brain.v5.public_surfaces import require_valid_public_surface

    _, claim = _seed_claim(tmp_path)

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "policy",
            "pre-tool",
            "validate_claim",
            "--session",
            "s1",
            "--claim",
            claim.claim_id,
            "--source-kind",
            "summary_orientation",
            "--source-ref",
            ".aitp/surfaces/session_summaries/s1/findings.md",
            "--orientation-only",
        ],
        capsys,
    )

    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert payload["policy_reasons"] == [
        {
            "policy_id": "no_summary_surface_as_truth_source",
            "severity": "hard_block",
            "message": "derived summary surfaces are orientation only and cannot justify trust-changing actions",
        }
    ]
    assert require_valid_public_surface("pre_tool_policy_decision", payload) == payload


def test_mcp_pre_tool_policy_exposes_machine_readable_policy_reasons(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="promote_to_l2",
        claim_id=claim.claim_id,
        evidence_refs=[],
        source_kind="typed_records",
    )

    assert payload["block"] is True
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_l2_promotion_without_evidence_ref"
    ]


def test_mcp_pre_tool_policy_blocks_record_evidence_from_summary_source(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="record_evidence",
        claim_id=claim.claim_id,
        source_kind="findings",
        source_ref=".aitp/surfaces/session_summaries/s1/findings.md",
        orientation_only=True,
    )

    assert payload["action"] == "record_evidence"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_rigorous_tool_evidence_without_validation_result(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim, run, _ = _seed_passed_validation_result(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="record_evidence",
        claim_id=claim.claim_id,
        source_kind="typed_records",
        risk_level="rigorous",
        tool_run_ids=[run.run_id],
    )

    assert payload["action"] == "record_evidence"
    assert payload["risk_level"] == "rigorous"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["attach_passed_validation_result"]
    assert payload["tool_run_ids"] == [run.run_id]
    assert payload["validation_result_ids"] == []
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "high_risk_tool_evidence_requires_validation_result"
    ]


def test_mcp_pre_tool_policy_accepts_rigorous_tool_evidence_with_passed_validation_result(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim, run, result = _seed_passed_validation_result(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="record_evidence",
        claim_id=claim.claim_id,
        source_kind="typed_records",
        risk_level="rigorous",
        tool_run_ids=[run.run_id],
        validation_result_ids=[result.result_id],
    )

    assert payload["action"] == "record_evidence"
    assert payload["risk_level"] == "rigorous"
    assert payload["tool_run_ids"] == [run.run_id]
    assert payload["validation_result_ids"] == [result.result_id]
    assert payload["mode"] == "log"
    assert payload["block"] is False
    assert payload["policy_reasons"] == []


def test_mcp_pre_tool_policy_blocks_code_state_from_progress_source(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path, evidence_profile="code_method")

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="record_code_state",
        claim_id=claim.claim_id,
        source_kind="progress",
        source_ref=".aitp/surfaces/session_summaries/s1/progress.md",
        orientation_only=True,
    )

    assert payload["action"] == "record_code_state"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_tool_recipe_from_findings_source(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="register_tool_recipe",
        claim_id=claim.claim_id,
        source_kind="findings",
        source_ref=".aitp/surfaces/session_summaries/s1/findings.md",
        orientation_only=True,
    )

    assert payload["action"] == "register_tool_recipe"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_physics_object_from_findings_source(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="record_physics_object",
        claim_id=claim.claim_id,
        source_kind="findings",
        source_ref=".aitp/surfaces/session_summaries/s1/findings.md",
        orientation_only=True,
    )

    assert payload["action"] == "record_physics_object"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_object_relation_from_task_plan_source(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="record_object_relation",
        claim_id=claim.claim_id,
        source_kind="task_plan",
        source_ref=".aitp/surfaces/session_summaries/s1/task_plan.md",
        orientation_only=True,
    )

    assert payload["action"] == "record_object_relation"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_reference_location_from_findings_source(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="record_reference_location",
        claim_id=claim.claim_id,
        source_kind="findings",
        source_ref=".aitp/surfaces/session_summaries/s1/findings.md",
        orientation_only=True,
    )

    assert payload["action"] == "record_reference_location"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_sensemaking_report_from_progress_source(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="record_sensemaking_report",
        claim_id=claim.claim_id,
        source_kind="progress",
        source_ref=".aitp/surfaces/session_summaries/s1/progress.md",
        orientation_only=True,
    )

    assert payload["action"] == "record_sensemaking_report"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_adversarial_trust_change_without_checkpoint(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="promote_to_l2",
        claim_id=claim.claim_id,
        evidence_refs=["evidence-fqhe-counting"],
        source_kind="typed_records",
        risk_level="adversarial",
    )

    assert payload["action"] == "promote_to_l2"
    assert payload["risk_level"] == "adversarial"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["request_human_checkpoint"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "adversarial_trust_change_requires_human_checkpoint"
    ]


def test_mcp_pre_tool_policy_accepts_adversarial_trust_change_with_approved_checkpoint(tmp_path):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    ws, claim = _seed_claim(tmp_path)
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        reason="Adversarial promotion needs human checkpoint",
        requested_by="risk_policy",
        options=["approve", "reject"],
    )
    decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="Evidence and scope were checked.",
        decided_by="human",
    )

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="promote_to_l2",
        claim_id=claim.claim_id,
        evidence_refs=["evidence-fqhe-counting"],
        source_kind="typed_records",
        risk_level="adversarial",
        human_checkpoint_id=checkpoint.checkpoint_id,
    )

    assert payload["risk_level"] == "adversarial"
    assert payload["human_checkpoint_id"] == checkpoint.checkpoint_id
    assert payload["mode"] == "log"
    assert payload["block"] is False
    assert payload["policy_reasons"] == []


def test_cli_pre_tool_policy_accepts_human_checkpoint_id(tmp_path, capsys):
    from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint

    ws, claim = _seed_claim(tmp_path)
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        reason="Adversarial validation needs human checkpoint",
        requested_by="risk_policy",
        options=["approve", "reject"],
    )
    decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale="Validation is allowed.",
        decided_by="human",
    )

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "policy",
            "pre-tool",
            "validate_claim",
            "--session",
            "s1",
            "--claim",
            claim.claim_id,
            "--source-kind",
            "typed_records",
            "--risk-level",
            "adversarial",
            "--human-checkpoint",
            checkpoint.checkpoint_id,
        ],
        capsys,
    )

    assert payload["risk_level"] == "adversarial"
    assert payload["human_checkpoint_id"] == checkpoint.checkpoint_id
    assert payload["block"] is False


def test_cli_pre_tool_policy_blocks_record_tool_run_from_task_plan_source(tmp_path, capsys):
    _, claim = _seed_claim(tmp_path)

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "policy",
            "pre-tool",
            "record_tool_run",
            "--session",
            "s1",
            "--claim",
            claim.claim_id,
            "--source-kind",
            "task_plan",
            "--source-ref",
            ".aitp/surfaces/session_summaries/s1/task_plan.md",
            "--orientation-only",
        ],
        capsys,
    )

    assert payload["action"] == "record_tool_run"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_execute_tool_from_progress_source(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="execute_tool",
        claim_id=claim.claim_id,
        source_kind="progress",
        source_ref=".aitp/surfaces/session_summaries/s1/progress.md",
        orientation_only=True,
    )

    assert payload["action"] == "execute_tool"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_subagent_ingestion_from_findings_source(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="ingest_subagent_result",
        claim_id=claim.claim_id,
        source_kind="findings",
        source_ref=".aitp/surfaces/session_summaries/s1/findings.md",
        orientation_only=True,
    )

    assert payload["action"] == "ingest_subagent_result"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_validation_contract_from_findings_source(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="create_validation_contract",
        claim_id=claim.claim_id,
        source_kind="findings",
        source_ref=".aitp/surfaces/session_summaries/s1/findings.md",
        orientation_only=True,
    )

    assert payload["action"] == "create_validation_contract"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_validation_result_from_findings_source(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="record_validation_result",
        claim_id=claim.claim_id,
        source_kind="findings",
        source_ref=".aitp/surfaces/session_summaries/s1/findings.md",
        orientation_only=True,
    )

    assert payload["action"] == "record_validation_result"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_promotion_packet_from_findings_source(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="create_promotion_packet",
        claim_id=claim.claim_id,
        evidence_refs=["evidence-fqhe-counting"],
        source_kind="findings",
        source_ref=".aitp/surfaces/session_summaries/s1/findings.md",
        orientation_only=True,
    )

    assert payload["action"] == "create_promotion_packet"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_promotion_packet_without_evidence_refs(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="create_promotion_packet",
        claim_id=claim.claim_id,
        evidence_refs=[],
        source_kind="typed_records",
    )

    assert payload["action"] == "create_promotion_packet"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["attach_evidence_ref"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_l2_promotion_without_evidence_ref"
    ]


def test_mcp_pre_tool_policy_blocks_rigorous_promotion_packet_without_validation_result(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim, evidence, _ = _seed_tool_evidence_for_promotion(tmp_path, link_result_to_evidence=False)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="create_promotion_packet",
        claim_id=claim.claim_id,
        evidence_refs=[evidence.evidence_id],
        source_kind="typed_records",
        risk_level="rigorous",
    )

    assert payload["action"] == "create_promotion_packet"
    assert payload["risk_level"] == "rigorous"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["evidence_refs"] == [evidence.evidence_id]
    assert payload["validation_result_ids"] == []
    assert payload["required_actions"] == ["attach_passed_validation_result"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "high_risk_promotion_requires_validation_result"
    ]


def test_mcp_pre_tool_policy_accepts_rigorous_promotion_packet_with_validation_result(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim, evidence, result = _seed_tool_evidence_for_promotion(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="create_promotion_packet",
        claim_id=claim.claim_id,
        evidence_refs=[evidence.evidence_id],
        validation_result_ids=[result.result_id],
        source_kind="typed_records",
        risk_level="rigorous",
    )

    assert payload["action"] == "create_promotion_packet"
    assert payload["evidence_refs"] == [evidence.evidence_id]
    assert payload["validation_result_ids"] == [result.result_id]
    assert payload["mode"] == "log"
    assert payload["block"] is False
    assert payload["policy_reasons"] == []


def test_mcp_pre_tool_policy_blocks_apply_promotion_packet_from_findings_source(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="apply_promotion_packet",
        claim_id=claim.claim_id,
        source_kind="findings",
        source_ref=".aitp/surfaces/session_summaries/s1/findings.md",
        orientation_only=True,
    )

    assert payload["action"] == "apply_promotion_packet"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_human_checkpoint_request_from_task_plan_source(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="request_human_checkpoint",
        claim_id=claim.claim_id,
        source_kind="task_plan",
        source_ref=".aitp/surfaces/session_summaries/s1/task_plan.md",
        orientation_only=True,
    )

    assert payload["action"] == "request_human_checkpoint"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_human_checkpoint_decision_from_findings_source(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="decide_human_checkpoint",
        claim_id=claim.claim_id,
        source_kind="findings",
        source_ref=".aitp/surfaces/session_summaries/s1/findings.md",
        orientation_only=True,
    )

    assert payload["action"] == "decide_human_checkpoint"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["query_execution_brief_or_typed_record"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "no_summary_surface_as_truth_source"
    ]


def test_mcp_pre_tool_policy_blocks_rigorous_execute_tool_without_validation_contract(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy

    _, claim = _seed_claim(tmp_path)

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="execute_tool",
        claim_id=claim.claim_id,
        source_kind="typed_records",
        risk_level="rigorous",
    )

    assert payload["action"] == "execute_tool"
    assert payload["risk_level"] == "rigorous"
    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["create_validation_contract"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "high_risk_tool_execution_requires_validation_contract"
    ]


def test_mcp_pre_tool_policy_accepts_rigorous_execute_tool_with_validation_contract(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy
    from brain.v5.validation import create_validation_contract

    ws, claim = _seed_claim(tmp_path)
    contract = create_validation_contract(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        required_checks=["finite-size scaling sanity check"],
        failure_modes=["finite-size artifact"],
        required_evidence_outputs=["diagnostic plot"],
        tool_recipe_ids=["recipe-fqhe-ed"],
        executor_ids=["pytest"],
    )

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="execute_tool",
        claim_id=claim.claim_id,
        source_kind="typed_records",
        risk_level="rigorous",
        recipe_id="recipe-fqhe-ed",
        executor_id="pytest",
        validation_contract_ids=[contract.contract_id],
    )

    assert payload["risk_level"] == "rigorous"
    assert payload["validation_contract_ids"] == [contract.contract_id]
    assert payload["mode"] == "log"
    assert payload["block"] is False
    assert payload["policy_reasons"] == []


def test_mcp_pre_tool_policy_blocks_rigorous_execute_tool_with_unbound_validation_contract(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_evaluate_pre_tool_policy
    from brain.v5.validation import create_validation_contract

    ws, claim = _seed_claim(tmp_path)
    contract = create_validation_contract(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        required_checks=["finite-size scaling sanity check"],
        failure_modes=["finite-size artifact"],
        required_evidence_outputs=["diagnostic plot"],
    )

    payload = aitp_v5_evaluate_pre_tool_policy(
        str(tmp_path),
        session_id="s1",
        action="execute_tool",
        claim_id=claim.claim_id,
        source_kind="typed_records",
        risk_level="rigorous",
        recipe_id="recipe-fqhe-ed",
        executor_id="pytest",
        validation_contract_ids=[contract.contract_id],
    )

    assert payload["mode"] == "block"
    assert payload["block"] is True
    assert payload["required_actions"] == ["bind_validation_contract_to_tool"]
    assert [reason["policy_id"] for reason in payload["policy_reasons"]] == [
        "high_risk_tool_validation_contract_mismatch"
    ]


def test_cli_pre_tool_policy_accepts_validation_contract_id(tmp_path, capsys):
    from brain.v5.validation import create_validation_contract

    ws, claim = _seed_claim(tmp_path)
    contract = create_validation_contract(
        ws,
        topic_id="fqhe",
        claim_id=claim.claim_id,
        required_checks=["compare neutral sector counting"],
        failure_modes=["wrong edge-mode identification"],
        required_evidence_outputs=["counting table"],
        tool_recipe_ids=["recipe-fqhe-ed"],
        executor_ids=["pytest"],
    )

    payload = _invoke(
        [
            "--base",
            str(tmp_path),
            "policy",
            "pre-tool",
            "execute_tool",
            "--session",
            "s1",
            "--claim",
            claim.claim_id,
            "--source-kind",
            "typed_records",
            "--risk-level",
            "rigorous",
            "--recipe",
            "recipe-fqhe-ed",
            "--executor",
            "pytest",
            "--validation-contract-id",
            contract.contract_id,
        ],
        capsys,
    )

    assert payload["validation_contract_ids"] == [contract.contract_id]
    assert payload["block"] is False
