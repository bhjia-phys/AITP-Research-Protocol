from __future__ import annotations

import json


def _invoke(args, capsys):
    from brain.v5.cli import main

    assert main(args) == 0
    return json.loads(capsys.readouterr().out)


def test_research_distillation_compiles_qsgw_method_candidate_from_run_journal(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.research_distillation import build_research_distillation_candidates
    from brain.v5.run_iterations import record_run_iteration
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qsgw-ac-error-molecules", context_id="librpa", title="QSGW AC error in molecules")
    claim = create_claim(
        ws,
        topic_id="qsgw-ac-error-molecules",
        statement="Ridge rational Pade can suppress H2O QSGW AC amplification, but same-base gap shifts must bound reuse.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="ridge parameter selection remains a validation boundary",
        scope="H2O QSGW first-iteration same-base diagnostic only",
        non_claims="Not molecule-general and not a default LibRPA setting.",
        strongest_failure_mode="Ridge stabilization may hide same-base gap shifts.",
    )
    bind_session(
        ws,
        "s-qsgw",
        topic_id="qsgw-ac-error-molecules",
        context_id="librpa",
        active_claim=claim.claim_id,
    )
    record_run_iteration(
        ws,
        topic_id="qsgw-ac-error-molecules",
        run_id="h2o-ridge-pade",
        iteration_id="20260608-gap-audit",
        plan_summary="Parse existing H2O QSGW diagnostics, plot regularized Pade behavior, and audit same-base gap shifts.",
        deliverables=["gap_audit_summary.tsv", "regularized_pade_ac_prl_note_20260608.pdf"],
        checks=["pdflatex completed twice", "same-base gap audit checked", "ridge remains opt-in"],
        stop_rules=["Do not claim molecule-general validation", "Do not update claim trust"],
        l4_return_summary="Recorded bounded numerical evidence with supports-with-limitations status.",
        l3_synthesis_summary=(
            "Ridge rational Pade suppresses AC amplification but shifts same-base QSGW gaps; "
            "treat the method as a parameter-selection warning, not a default workflow."
        ),
        decision="Keep ridge opt-in and require a same-base gap audit before reuse.",
        status="l4_returned",
        claim_id=claim.claim_id,
        source_refs=["source-asset:qsgw-note", "evidence:evidence-qsgw-h2o-gap-audit"],
        l4_artifact_refs=["artifact:qsgw-h2o-gap-audit"],
    )

    payload = require_valid_public_surface(
        "research_distillation_candidates",
        build_research_distillation_candidates(ws, "s-qsgw"),
    )

    assert payload["kind"] == "research_distillation_candidates"
    assert payload["orientation_only"] is True
    assert payload["can_update_claim_trust"] is False
    candidate = payload["candidates"][0]
    assert candidate["candidate_kind"] == "method_capsule_candidate"
    assert candidate["can_draft_reusable_block"] is True
    assert candidate["can_materialize_without_human_review"] is False
    assert candidate["can_promote_claim_trust"] is False
    assert candidate["missing_requirements"] == []
    assert "tool_recipe_record" in candidate["target_surfaces"]
    assert "H2O QSGW first-iteration" in candidate["reuse_boundary"]["scope"]
    assert "evidence-qsgw-h2o-gap-audit" in candidate["source_records"]["evidence"]
    assert payload["distillation_boundary"]["does_not_create_skills"] is True
    assert any("review candidate" in action for action in payload["next_valid_actions"])


def test_research_distillation_reports_missing_gates_before_reuse(tmp_path):
    from brain.v5.research_distillation import build_research_distillation_candidates
    from brain.v5.run_iterations import record_run_iteration
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qsgw-headwing-update-librpa", context_id="librpa", title="LibRPA headwing update")
    claim = create_claim(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        statement="The headwing update needs final-lane provenance before reuse.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="diagnostic and final lanes are not separated yet",
    )
    bind_session(
        ws,
        "s-headwing",
        topic_id="qsgw-headwing-update-librpa",
        context_id="librpa",
        active_claim=claim.claim_id,
    )
    record_run_iteration(
        ws,
        topic_id="qsgw-headwing-update-librpa",
        run_id="diagnostic-refresh",
        iteration_id="rough-note",
        plan_summary="Try a quick plot refresh for the current diagnostic table.",
        claim_id=claim.claim_id,
    )

    payload = build_research_distillation_candidates(ws, "s-headwing")
    candidate = payload["candidates"][0]

    assert candidate["can_draft_reusable_block"] is False
    assert candidate["distillation_state"] == "needs_more_records"
    assert {
        "reproducible_steps",
        "provenance_refs",
        "validation_boundary",
        "reuse_boundary",
    }.issubset(set(candidate["missing_requirements"]))
    assert candidate["recommended_record_actions"][0]["action"] == "complete_first_layer_records"
    assert payload["can_update_kernel_state"] is False


def test_research_distillation_cli_and_mcp_return_valid_public_surface(tmp_path, capsys):
    from brain.v5.mcp_tools import aitp_v5_get_research_distillation_candidates
    from brain.v5.run_iterations import record_run_iteration
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "quantum-chaos-long-range-spin-chains", context_id="spin-chains", title="HS hidden symmetry")
    claim = create_claim(
        ws,
        topic_id="quantum-chaos-long-range-spin-chains",
        statement="Finite symbolic certificates suggest an all-L symmetry route but do not close the proof.",
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="the all-L proof obligation remains open",
        scope="finite modular certificates plus symbolic proof-route sketch",
        non_claims="No all-L theorem is established.",
        strongest_failure_mode="Finite-L evidence may not lift to the algebraic closure argument.",
    )
    bind_session(
        ws,
        "s-hs",
        topic_id="quantum-chaos-long-range-spin-chains",
        context_id="spin-chains",
        active_claim=claim.claim_id,
    )
    record_run_iteration(
        ws,
        topic_id="quantum-chaos-long-range-spin-chains",
        run_id="alpha-axis-proof-route",
        iteration_id="proof-gap-audit",
        plan_summary="Derive the operator-sector closure route and identify symbolic proof obligations.",
        deliverables=["proof_obligation:all-L-closure", "finite_certificate:L8-alpha2"],
        checks=["finite certificate reviewed", "open all-L proof gap preserved"],
        stop_rules=["Do not promote to theorem", "Do not treat finite-L evidence as proof"],
        l3_synthesis_summary="The Schur/commutant closure route is semantically useful but remains blocked by the all-L proof obligation.",
        decision="Keep as a physics semantic fragment with an explicit proof gap.",
        status="synthesized",
        claim_id=claim.claim_id,
        source_refs=["source:hs-alpha-notebook", "artifact:finite-certificates"],
    )

    cli_payload = _invoke(["--base", str(tmp_path), "status", "distillation-candidates", "s-hs"], capsys)
    mcp_payload = aitp_v5_get_research_distillation_candidates(str(tmp_path), session_id="s-hs")

    assert cli_payload["kind"] == "research_distillation_candidates"
    assert mcp_payload["kind"] == "research_distillation_candidates"
    assert cli_payload["candidates"][0]["candidate_kind"] == "physics_semantic_fragment_candidate"
    assert cli_payload["candidates"][0]["can_promote_claim_trust"] is False
    assert mcp_payload["candidates"][0]["orientation_only"] is True
