from __future__ import annotations


def test_teacher_profile_changes_question_style_without_lowering_truth_standard():
    from brain.v5.interaction import resolve_interaction_profile

    plan = resolve_interaction_profile(
        "teacher",
        risk_level="rigorous",
        max_questions=3,
    )

    assert plan.profile.role == "teacher"
    assert plan.profile.question_style == "scaffold_with_prerequisites"
    assert plan.profile.explanation_style == "teach_concepts_before_checks"
    assert plan.truth_standard == "unchanged"
    assert plan.effective_risk_level == "rigorous"
    assert plan.effective_max_questions == 3
    assert plan.policy_bounds["may_lower_truth_standard"] is False


def test_student_profile_prefers_clarifying_questions_and_mirroring():
    from brain.v5.interaction import resolve_interaction_profile

    plan = resolve_interaction_profile(
        "student",
        risk_level="guided",
        max_questions=3,
    )

    assert plan.profile.first_move == "mirror_user_claim"
    assert plan.profile.question_priorities[:2] == ["mirror_user_claim", "clarify_terms"]
    assert "ask_when_unsure" in plan.profile.answer_constraints
    assert plan.truth_standard == "unchanged"


def test_critic_profile_raises_adversarial_priority_only_when_risk_permits():
    from brain.v5.interaction import resolve_interaction_profile

    fluid_plan = resolve_interaction_profile("critic", risk_level="fluid", max_questions=1)
    rigorous_plan = resolve_interaction_profile("critic", risk_level="rigorous", max_questions=3)

    assert fluid_plan.adversarial_priority_enabled is False
    assert fluid_plan.profile.question_priorities[0] != "failure_or_counterexample"
    assert rigorous_plan.adversarial_priority_enabled is True
    assert rigorous_plan.profile.question_priorities[0] == "failure_or_counterexample"
    assert rigorous_plan.effective_risk_level == "rigorous"


def test_user_steering_can_lighten_friction_inside_policy_bounds():
    from brain.v5.interaction import resolve_interaction_profile

    guided_plan = resolve_interaction_profile(
        "collaborator",
        risk_level="guided",
        max_questions=3,
        user_steering="lighter, keep it moving",
    )
    rigorous_plan = resolve_interaction_profile(
        "collaborator",
        risk_level="rigorous",
        max_questions=3,
        user_steering="lighter, keep it moving",
    )

    assert guided_plan.effective_max_questions == 2
    assert guided_plan.policy_bounds["risk_level_changed"] is False
    assert rigorous_plan.effective_max_questions == 3
    assert any("not reduced" in note for note in rigorous_plan.boundary_notes)


def test_interaction_profile_prioritizes_questions_without_mutating_questions():
    from brain.v5.interaction import prioritize_questions, resolve_interaction_profile
    from brain.v5.models import ClaimRecord, FlowDecision
    from brain.v5.question_engine import generate_questions

    claim = ClaimRecord(
        claim_id="claim-code",
        topic_id="librpa-gw",
        statement="The modified self-energy kernel reproduces the benchmark.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="formula-code translation risk",
    )
    flow = FlowDecision(profile="rigorous", reason="code method risk")
    questions = generate_questions(claim, flow)
    plan = resolve_interaction_profile("critic", risk_level="rigorous", max_questions=3)

    prioritized = prioritize_questions(questions, plan)

    assert prioritized[0].question_id in {q.question_id for q in questions}
    assert "wrong" in prioritized[0].question.lower() or "failure" in prioritized[0].question.lower()
    assert {q.question_id for q in prioritized} == {q.question_id for q in questions}


def test_execution_brief_includes_interaction_profile_and_keeps_policy_guards(tmp_path):
    from brain.v5.brief import build_execution_brief
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The modified self-energy kernel reproduces the benchmark.",
        evidence_profile="code_method",
        confidence_state="locally_checked",
        active_uncertainty="formula-code translation risk",
    )
    bind_session(
        ws,
        "s1",
        topic_id="librpa-gw",
        context_id="gw-methods",
        active_claim=claim.claim_id,
        interaction_profile="teacher",
        interaction_steering="lighter",
    )

    brief = build_execution_brief(ws, "s1")

    assert brief["interaction_profile"]["profile"]["role"] == "teacher"
    assert brief["interaction_profile"]["truth_standard"] == "unchanged"
    assert brief["interaction_profile"]["effective_risk_level"] == brief["risk_assessment"]["level"]
    assert len(brief["mandatory_reflection"]) <= brief["interaction_profile"]["effective_max_questions"]
    assert "policy:no_code_method_validation_without_code_state" in brief["forbidden_now"]


def test_interaction_recording_preview_is_read_only_and_defers_heavy_records(tmp_path):
    from brain.v5.interaction_preview import build_interaction_recording_preview
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "hs-otoc", context_id="quantum-chaos", title="HS OTOC")
    claim = create_claim(
        ws,
        topic_id="hs-otoc",
        statement="The fixed-Sz OTOC definition is the correct finite-size baseline.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size and operator-choice artifacts remain possible",
    )
    bind_session(
        ws,
        "s1",
        topic_id="hs-otoc",
        context_id="quantum-chaos",
        active_claim=claim.claim_id,
        interaction_profile="collaborator",
        interaction_steering="lighter, keep it moving",
    )

    preview = build_interaction_recording_preview(ws, "s1")
    validated = require_valid_public_surface("interaction_recording_preview", preview)

    assert validated["orientation_only"] is True
    assert validated["summary_inputs_trusted"] is False
    assert validated["can_update_kernel_state"] is False
    assert validated["can_update_claim_trust"] is False
    assert validated["mandatory_question_count"] <= validated["max_questions"]
    assert "continue_natural_research_conversation" in validated["natural_workflow"]
    assert validated["recording_decision"] == {
        "mode": "guarded_recording",
        "can_continue_without_kernel_write": True,
        "next_kernel_entrypoint": "aitp_v5_record_sensemaking_report",
        "required_before_trust_change": [
            "aitp_v5_record_evidence_or_tool_run",
            "aitp_v5_preflight_trust_update",
        ],
        "why": "active claim can continue naturally, but missing evidence outputs require typed provenance before trust changes",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    assert "trust_update_apply" in {item["record_type"] for item in validated["deferred_records"]}
    assert "source_is_only_a_summary_task_plan_findings_or_progress_file" in validated["heavier_triggers"]


def test_interaction_recording_preview_without_claim_stays_orientation_only(tmp_path):
    from brain.v5.interaction_preview import build_interaction_recording_preview
    from brain.v5.workspace import bind_session, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "new-topic", context_id="scratch", title="New Topic")
    bind_session(ws, "s1", topic_id="new-topic", context_id="scratch")

    preview = build_interaction_recording_preview(ws, "s1")

    assert preview["active_claim"] == ""
    assert preview["can_stay_lightweight"] is True
    assert preview["recording_decision"] == {
        "mode": "lightweight_trace",
        "can_continue_without_kernel_write": True,
        "next_kernel_entrypoint": "",
        "required_before_trust_change": ["bind_or_create_claim", "aitp_v5_preflight_trust_update"],
        "why": "no active claim is bound, so natural exploration can stay lightweight until a stable research question emerges",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    assert [item["record_type"] for item in preview["recommended_records"]] == ["execution_brief"]
    assert preview["natural_workflow"] == [
        "continue_natural_research_conversation",
        "bind_or_create_a_claim_only_after_a_stable_research_question_emerges",
    ]


def test_workspace_interaction_preview_bundle_summarizes_active_sessions(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace
    from brain.v5.workspace_interaction_preview import build_workspace_interaction_preview

    ws = init_workspace(tmp_path)
    create_topic(ws, "hs-otoc", context_id="quantum-chaos", title="HS OTOC")
    claim = create_claim(
        ws,
        topic_id="hs-otoc",
        statement="The fixed-Sz OTOC definition is the correct finite-size baseline.",
        evidence_profile="toy_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size and operator-choice artifacts remain possible",
    )
    bind_session(
        ws,
        "s-claim",
        topic_id="hs-otoc",
        context_id="quantum-chaos",
        active_claim=claim.claim_id,
        interaction_profile="collaborator",
        interaction_steering="lighter, keep it moving",
    )
    create_topic(ws, "scratch", context_id="scratch", title="Scratch")
    bind_session(ws, "s-empty", topic_id="scratch", context_id="scratch")

    payload = require_valid_public_surface(
        "workspace_interaction_preview_bundle",
        build_workspace_interaction_preview(ws),
    )

    assert payload["kind"] == "workspace_interaction_preview_bundle"
    assert payload["session_count"] == 2
    assert payload["decision_mode_counts"] == {
        "guarded_recording": 1,
        "lightweight_trace": 1,
    }
    assert payload["source_records"]["sessions"] == ["s-claim", "s-empty"]
    assert payload["source_records"]["topics"] == ["hs-otoc", "scratch"]
    assert payload["source_records"]["claims"] == [claim.claim_id]
    assert payload["preview_refs"] == [
        "interaction_recording_preview:s-claim",
        "interaction_recording_preview:s-empty",
    ]
    by_session = {item["session_id"]: item for item in payload["items"]}
    assert by_session["s-claim"]["topic_id"] == "hs-otoc"
    assert by_session["s-claim"]["active_claim"] == claim.claim_id
    assert by_session["s-claim"]["recording_mode"] == "guarded_recording"
    assert by_session["s-claim"]["next_kernel_entrypoint"] == "aitp_v5_record_sensemaking_report"
    assert by_session["s-empty"]["active_claim"] == ""
    assert by_session["s-empty"]["recording_mode"] == "lightweight_trace"
    assert by_session["s-empty"]["can_stay_lightweight"] is True
    assert all(item["can_update_claim_trust"] is False for item in payload["items"])
    assert payload["derived_from"] == "interaction_recording_preview"
    assert payload["truth_source"] == "typed_records"
    assert payload["summary_inputs_trusted"] is False
    assert payload["orientation_only"] is True
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False


def test_interaction_recording_preview_cli_and_mcp(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_preview_interaction_recording
    from brain.v5.workspace import bind_session, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "new-topic", context_id="scratch", title="New Topic")
    bind_session(ws, "s1", topic_id="new-topic", context_id="scratch")

    assert main(["--base", str(tmp_path), "interaction", "preview", "s1"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_preview_interaction_recording(str(tmp_path), session_id="s1")

    assert cli_payload["kind"] == "interaction_recording_preview"
    assert mcp_payload["kind"] == "interaction_recording_preview"
    assert cli_payload["recording_decision"]["mode"] == "lightweight_trace"
    assert mcp_payload["recording_decision"]["mode"] == "lightweight_trace"
    assert cli_payload["can_update_kernel_state"] is False
    assert mcp_payload["can_update_claim_trust"] is False


def test_workspace_interaction_preview_cli_mcp_and_runtime(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_build_workspace_interaction_preview
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.workspace import bind_session, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "new-topic", context_id="scratch", title="New Topic")
    bind_session(ws, "s1", topic_id="new-topic", context_id="scratch")

    assert main(["--base", str(tmp_path), "interaction", "workspace-preview"]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_build_workspace_interaction_preview(str(tmp_path))

    assert cli_payload["kind"] == "workspace_interaction_preview_bundle"
    assert mcp_payload["kind"] == "workspace_interaction_preview_bundle"
    assert cli_payload["session_count"] == 1
    assert mcp_payload["decision_mode_counts"] == {"lightweight_trace": 1}
    assert cli_payload["can_update_kernel_state"] is False
    assert mcp_payload["can_update_claim_trust"] is False
    assert runtime_entrypoints()["workspace_interaction_preview"] == {
        "cli": "aitp-v5 interaction workspace-preview",
        "mcp": "aitp_v5_build_workspace_interaction_preview",
        "surface": "workspace_interaction_preview_bundle",
    }


def test_interaction_recording_preview_blocks_natural_recording_at_adversarial_checkpoint(tmp_path):
    from brain.v5.interaction_preview import build_interaction_recording_preview
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "gw-conflict", context_id="gw-methods", title="GW Conflict")
    claim = create_claim(
        ws,
        topic_id="gw-conflict",
        statement="This publication-ready QSGW proof contradicts the benchmark.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="conflict with reference paper and formula-code kernel mismatch",
    )
    bind_session(ws, "s1", topic_id="gw-conflict", context_id="gw-methods", active_claim=claim.claim_id)

    preview = require_valid_public_surface("interaction_recording_preview", build_interaction_recording_preview(ws, "s1"))

    assert preview["risk_level"] == "adversarial"
    assert preview["can_stay_lightweight"] is False
    assert preview["recording_decision"] == {
        "mode": "trust_boundary_checkpoint",
        "can_continue_without_kernel_write": False,
        "next_kernel_entrypoint": "aitp_v5_request_human_checkpoint",
        "required_before_trust_change": [
            "aitp_v5_request_human_checkpoint",
            "aitp_v5_record_evidence_or_tool_run",
            "aitp_v5_preflight_trust_update",
        ],
        "why": "adversarial risk requires a human checkpoint before recording content that could drive trust changes",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
