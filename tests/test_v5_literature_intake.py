from __future__ import annotations

from pathlib import Path


def _setup_topic(tmp_path: Path, *, active_claim: bool):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(
        ws,
        "quantum-chaos-long-range-spin-chains",
        context_id="quantum-chaos",
        title="Long-range spin-chain chaos",
    )
    claim = None
    if active_claim:
        claim = create_claim(
            ws,
            topic_id="quantum-chaos-long-range-spin-chains",
            statement=(
                "The alpha-axis classification separates the alpha=2 Haldane-Shastry "
                "Yangian point from generic long-range spin-chain chaos diagnostics."
            ),
            evidence_profile="mixed",
            confidence_state="hypothesis",
            active_uncertainty="close prior-art level-statistics results may limit the scope",
            scope="algebraic classification across the alpha axis",
            non_claims="does not claim all level-statistics behavior is novel",
        )
    bind_session(
        ws,
        "chaos-lit",
        topic_id="quantum-chaos-long-range-spin-chains",
        context_id="quantum-chaos",
        active_claim=claim.claim_id if claim else "",
    )
    return ws, claim


def test_literature_intake_without_active_claim_stays_reference_only(tmp_path):
    from brain.v5.literature_intake import suggest_literature_intake
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, _ = _setup_topic(tmp_path, active_claim=False)

    payload = suggest_literature_intake(
        ws,
        session_id="chaos-lit",
        uri="https://arxiv.org/abs/2604.14695",
        label="Level statistics in long-range spin chains",
        external_id="arXiv:2604.14695",
        short_summary=(
            "Studies 1/r^alpha PBC level statistics and finds anomalous alpha=0 "
            "and alpha=2 points."
        ),
        detected_relevance="close_prior_art",
    )
    validated = require_valid_public_surface("literature_intake_suggestion", payload)

    assert validated["recommended_action"] == "record_reference_only"
    assert validated["topic_id"] == "quantum-chaos-long-range-spin-chains"
    assert validated["active_claim"] == ""
    assert validated["reference_candidate"]["orientation_only"] is True
    assert validated["reference_candidate"]["status"] == "candidate"
    assert validated["guarded_next_steps"] == []
    assert validated["trust_update_forbidden"] is True
    assert validated["can_update_claim_trust"] is False
    assert "bind_active_claim_before_evidence" in validated["risk_notes"]
    assert validated["mcp_templates"]["record_reference_location"]["claim_id"] == ""


def test_literature_intake_ignores_optional_claim_until_session_has_active_claim(tmp_path):
    from brain.v5.literature_intake import suggest_literature_intake

    ws, claim = _setup_topic(tmp_path, active_claim=True)
    from brain.v5.workspace import bind_session

    bind_session(
        ws,
        "chaos-lit-unbound",
        topic_id="quantum-chaos-long-range-spin-chains",
        context_id="quantum-chaos",
        active_claim="",
    )

    payload = suggest_literature_intake(
        ws,
        session_id="chaos-lit-unbound",
        uri="https://arxiv.org/abs/2604.14695",
        label="Level statistics in long-range spin chains",
        external_id="arXiv:2604.14695",
        short_summary="Close prior art: level statistics already studied.",
        detected_relevance="close_prior_art; explicit claim relation",
        optional_claim_id=claim.claim_id,
        scoped_output="scope limit for alpha-axis classification",
    )

    assert payload["recommended_action"] == "record_reference_only"
    assert payload["active_claim"] == ""
    assert payload["reference_candidate"]["claim_id"] == ""
    assert payload["sensemaking_candidate"] == {}
    assert payload["evidence_candidate"] == {}
    assert payload["guarded_next_steps"] == []
    assert "bind_active_claim_before_evidence" in payload["risk_notes"]


def test_literature_intake_for_close_prior_art_suggests_sensemaking_and_mixed_evidence_candidate(tmp_path):
    from brain.v5.literature_intake import suggest_literature_intake

    ws, claim = _setup_topic(tmp_path, active_claim=True)

    payload = suggest_literature_intake(
        ws,
        session_id="chaos-lit",
        uri="https://arxiv.org/abs/2604.14695",
        label="Level statistics in long-range spin chains",
        external_id="arXiv:2604.14695",
        short_summary=(
            "Close prior art: 1/r^alpha PBC level statistics are already studied; "
            "alpha=0 and alpha=2 are anomalous, while strict algebraic classification "
            "across the alpha axis remains open."
        ),
        detected_relevance="close_prior_art; scope-limiting; explicit claim relation",
        optional_claim_id=claim.claim_id,
        scoped_output="algebraic classification scope versus level-statistics prior art",
    )

    assert payload["recommended_action"] == "record_reference_plus_evidence_candidate"
    assert payload["active_claim"] == claim.claim_id
    assert payload["reference_candidate"]["claim_id"] == claim.claim_id
    assert payload["sensemaking_candidate"]["summary"] == (
        "close prior art; level statistics already studied; algebraic classification remains open"
    )
    assert payload["evidence_candidate"]["status"] == "mixed"
    assert payload["evidence_candidate"]["supports_outputs"] == [
        "algebraic classification scope versus level-statistics prior art"
    ]
    assert "not_a_supports_claim_by_default" in payload["risk_notes"]
    assert "aitp_v5_preflight_trust_update" in payload["forbidden_without_preflight"]
    assert payload["trust_update_forbidden"] is True
    assert payload["can_update_kernel_state"] is False


def test_record_literature_candidate_writes_only_reference_location_and_no_trust_records(tmp_path):
    from brain.v5.literature_intake import record_literature_candidate
    from brain.v5.models import ReferenceLocationRecord, TrustUpdateRecord
    from brain.v5.store import list_records

    ws, claim = _setup_topic(tmp_path, active_claim=True)

    payload = record_literature_candidate(
        ws,
        session_id="chaos-lit",
        uri="https://arxiv.org/abs/2604.14695",
        label="Level statistics in long-range spin chains",
        external_id="arXiv:2604.14695",
        short_summary=(
            "Close prior art: level statistics already studied; algebraic classification remains open."
        ),
        detected_relevance="close_prior_art; explicit claim relation",
        optional_claim_id=claim.claim_id,
        scoped_output="scope limit for alpha-axis classification",
    )

    references = list_records(ws.registry_dir("reference_locations"), ReferenceLocationRecord)
    trust_updates = list_records(ws.registry_dir("trust_updates"), TrustUpdateRecord)

    assert payload["kind"] == "literature_intake_record_result"
    assert payload["recorded_reference_location"]["orientation_only"] is True
    assert payload["recorded_reference_location"]["claim_id"] == claim.claim_id
    assert payload["evidence_written"] is False
    assert payload["sensemaking_written"] is False
    assert payload["trust_update_forbidden"] is True
    assert len(references) == 1
    assert references[0].external_id == "arXiv:2604.14695"
    assert trust_updates == []


def test_literature_intake_cli_mcp_runtime_and_surface_contract(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_suggest_literature_intake
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ws, _ = _setup_topic(tmp_path, active_claim=False)

    assert main(
        [
            "--base",
            str(ws.base),
            "literature",
            "suggest-intake",
            "--session",
            "chaos-lit",
            "--uri",
            "https://arxiv.org/abs/2604.14695",
            "--label",
            "Level statistics in long-range spin chains",
            "--external-id",
            "arXiv:2604.14695",
            "--summary",
            "Level statistics prior art.",
            "--detected-relevance",
            "close_prior_art",
        ]
    ) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_suggest_literature_intake(
        str(ws.base),
        session_id="chaos-lit",
        uri="https://arxiv.org/abs/2604.14695",
        label="Level statistics in long-range spin chains",
        external_id="arXiv:2604.14695",
        short_summary="Level statistics prior art.",
        detected_relevance="close_prior_art",
    )

    assert require_valid_public_surface("literature_intake_suggestion", cli_payload) == cli_payload
    assert require_valid_public_surface("literature_intake_suggestion", mcp_payload) == mcp_payload
    assert cli_payload["recommended_action"] == "record_reference_only"
    assert mcp_payload["reference_candidate"]["external_id"] == "arXiv:2604.14695"
    assert runtime_entrypoints()["suggest_literature_intake"] == {
        "cli": "aitp-v5 literature suggest-intake <args>",
        "mcp": "aitp_v5_suggest_literature_intake",
        "surface": "literature_intake_suggestion",
    }
    assert runtime_entrypoints()["record_literature_candidate"]["surface"] == (
        "literature_intake_record_result"
    )


def test_literature_source_review_handoff_composes_read_only_surfaces(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.literature_source_review_handoff import build_literature_source_review_handoff
    from brain.v5.mcp_tools import aitp_v5_build_literature_source_review_handoff
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    ws, claim = _setup_topic(tmp_path, active_claim=True)

    payload = build_literature_source_review_handoff(
        ws,
        session_id="chaos-lit",
        uri="https://arxiv.org/abs/2604.14695",
        label="Level statistics in long-range spin chains",
        external_id="arXiv:2604.14695",
        short_summary="Level statistics prior art.",
        detected_relevance="close_prior_art",
        scoped_output="alpha-axis classification scope",
        reviewed_refs=["source_asset:missing-source", "reference_location:missing-location"],
    )
    assert require_valid_public_surface("literature_source_review_handoff", payload) == payload
    assert payload["kind"] == "literature_source_review_handoff"
    assert payload["claim_id"] == claim.claim_id
    assert payload["literature_intake_suggestion"]["kind"] == "literature_intake_suggestion"
    assert payload["record_ref_lookup"]["kind"] == "record_ref_lookup"
    assert payload["record_ref_lookup"]["source_support_result"] is False
    assert payload["record_ref_lookup"]["evidence_created"] is False
    assert payload["source_stack_coverage_item"]["claim_id"] == claim.claim_id
    assert payload["source_reconstruction_review_packet"]["claim_id"] == claim.claim_id
    assert payload["handoff_policy"]["requires_explicit_next_entrypoint"] is True
    assert "source_support_result" in payload["handoff_policy"]["forbidden_uses"]
    assert payload["allowed_next_tool_call"] == {
        "action": "plan_primitive_tools",
        "action_id": "source.review_context",
        "requires_explicit_next_action": True,
        "records_validation_result": False,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }
    assert payload["read_only"] is True
    assert payload["requires_explicit_next_action"] is True
    assert payload["bridge_called"] is False
    assert payload["executes_write_now"] is False
    assert payload["mutates_next_payload_now"] is False
    assert payload["infers_payload_values"] is False
    assert payload["summary_inputs_trusted"] is False
    assert payload["orientation_only"] is True
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False
    assert payload["records_validation_result"] is False
    assert payload["source_support_result"] is False
    assert payload["evidence_created"] is False
    assert payload["validation_created"] is False
    assert payload["write_executed"] is False
    assert payload["trust_update_forbidden"] is True
    assert payload["claim_trust_mutation"] == "none"

    assert main(
        [
            "--base",
            str(ws.base),
            "literature",
            "source-review-handoff",
            "--session",
            "chaos-lit",
            "--uri",
            "https://arxiv.org/abs/2604.14695",
            "--label",
            "Level statistics in long-range spin chains",
            "--external-id",
            "arXiv:2604.14695",
            "--summary",
            "Level statistics prior art.",
            "--detected-relevance",
            "close_prior_art",
            "--scoped-output",
            "alpha-axis classification scope",
            "--reviewed-ref",
            "source_asset:missing-source",
        ]
    ) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_build_literature_source_review_handoff(
        str(ws.base),
        session_id="chaos-lit",
        uri="https://arxiv.org/abs/2604.14695",
        label="Level statistics in long-range spin chains",
        external_id="arXiv:2604.14695",
        short_summary="Level statistics prior art.",
        detected_relevance="close_prior_art",
        scoped_output="alpha-axis classification scope",
        reviewed_refs=["source_asset:missing-source"],
    )

    assert require_valid_public_surface("literature_source_review_handoff", cli_payload) == cli_payload
    assert require_valid_public_surface("literature_source_review_handoff", mcp_payload) == mcp_payload
    assert cli_payload["record_ref_lookup"]["lookup_count"] == 1
    assert mcp_payload["record_ref_lookup"]["refs"][0]["suggested_next_entrypoint"] == "register_source_asset"
    assert runtime_entrypoints()["literature_source_review_handoff"] == {
        "cli": "aitp-v5 literature source-review-handoff <args>",
        "mcp": "aitp_v5_build_literature_source_review_handoff",
        "surface": "literature_source_review_handoff",
    }


def test_literature_comparison_draft_is_read_only_planning_packet(tmp_path, capsys):
    import json

    from brain.v5.cli import main
    from brain.v5.literature_comparison_draft import build_literature_comparison_draft
    from brain.v5.mcp_tools import aitp_v5_build_literature_comparison_draft
    from brain.v5.models import EvidenceRecord, ReferenceLocationRecord, TrustUpdateRecord, ValidationResultRecord
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.store import list_records

    ws, claim = _setup_topic(tmp_path, active_claim=True)

    before = (
        list_records(ws.registry_dir("reference_locations"), ReferenceLocationRecord),
        list_records(ws.registry_dir("evidence"), EvidenceRecord),
        list_records(ws.registry_dir("validation_results"), ValidationResultRecord),
        list_records(ws.registry_dir("trust_updates"), TrustUpdateRecord),
    )
    payload = build_literature_comparison_draft(
        ws,
        session_id="chaos-lit",
        comparison_question="How do the source assumptions compare on the alpha-axis claim?",
        source_refs=["source_asset:missing-source", "reference_location:missing-location"],
        dimensions=["method_assumptions", "evidence_basis", "open_directions"],
        rationale="Compare close prior art before drafting evidence.",
    )
    after = (
        list_records(ws.registry_dir("reference_locations"), ReferenceLocationRecord),
        list_records(ws.registry_dir("evidence"), EvidenceRecord),
        list_records(ws.registry_dir("validation_results"), ValidationResultRecord),
        list_records(ws.registry_dir("trust_updates"), TrustUpdateRecord),
    )

    assert before == after
    assert require_valid_public_surface("literature_comparison_draft", payload) == payload
    assert payload["kind"] == "literature_comparison_draft"
    assert payload["claim_id"] == claim.claim_id
    assert payload["source_ref_count"] == 2
    assert payload["comparison_dimension_count"] == 3
    assert payload["record_ref_lookup"]["kind"] == "record_ref_lookup"
    assert payload["record_ref_lookup"]["source_support_result"] is False
    assert payload["draft_record_intent"]["kind"] == "literature_comparison_record_candidate"
    assert payload["draft_record_intent"]["creates_record_now"] is False
    assert payload["draft_record_intent"]["records_validation_result"] is False
    assert payload["draft_record_intent"]["source_support_result"] is False
    assert payload["draft_record_intent"]["claim_trust_mutation"] == "none"
    assert payload["draft_policy"]["requires_explicit_next_entrypoint"] is True
    assert "literature_comparison_record" in payload["draft_policy"]["forbidden_uses"]
    assert "trust_apply" in payload["draft_policy"]["forbidden_uses"]
    assert payload["allowed_next_tool_call"] == {
        "action": "plan_primitive_tools",
        "action_id": "source.compare_literature",
        "requires_explicit_next_action": True,
        "records_validation_result": False,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }
    assert payload["read_surface_effect"] == "comparison_draft_only"
    assert payload["read_only"] is True
    assert payload["draft_creates_records"] is False
    assert payload["requires_explicit_next_action"] is True
    assert payload["bridge_called"] is False
    assert payload["executes_write_now"] is False
    assert payload["mutates_next_payload_now"] is False
    assert payload["infers_payload_values"] is False
    assert payload["summary_inputs_trusted"] is False
    assert payload["orientation_only"] is True
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False
    assert payload["records_validation_result"] is False
    assert payload["source_support_result"] is False
    assert payload["evidence_created"] is False
    assert payload["validation_created"] is False
    assert payload["write_executed"] is False
    assert payload["trust_update_forbidden"] is True
    assert payload["claim_trust_mutation"] == "none"

    assert main(
        [
            "--base",
            str(ws.base),
            "literature",
            "comparison-draft",
            "--session",
            "chaos-lit",
            "--question",
            "How do the source assumptions compare on the alpha-axis claim?",
            "--source-ref",
            "source_asset:missing-source",
            "--source-ref",
            "reference_location:missing-location",
            "--dimension",
            "method_assumptions",
            "--dimension",
            "evidence_basis",
            "--rationale",
            "Compare close prior art before drafting evidence.",
        ]
    ) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_build_literature_comparison_draft(
        str(ws.base),
        session_id="chaos-lit",
        comparison_question="How do the source assumptions compare on the alpha-axis claim?",
        source_refs=["source_asset:missing-source", "reference_location:missing-location"],
        dimensions=["method_assumptions", "evidence_basis"],
        rationale="Compare close prior art before drafting evidence.",
    )

    assert require_valid_public_surface("literature_comparison_draft", cli_payload) == cli_payload
    assert require_valid_public_surface("literature_comparison_draft", mcp_payload) == mcp_payload
    assert cli_payload["source_ref_count"] == 2
    assert mcp_payload["comparison_dimensions"][0]["creates_record_now"] is False
    assert runtime_entrypoints()["literature_comparison_draft"] == {
        "cli": "aitp-v5 literature comparison-draft <args>",
        "mcp": "aitp_v5_build_literature_comparison_draft",
        "surface": "literature_comparison_draft",
    }


def test_literature_intake_includes_output_profile_context_when_topic_has_profile(tmp_path):
    from brain.v5.literature_intake import suggest_literature_intake
    from brain.v5.output_stability import record_final_output_profile

    ws, _ = _setup_topic(tmp_path, active_claim=False)
    record_final_output_profile(
        ws,
        topic_id="quantum-chaos-long-range-spin-chains",
        output_version="qsgw-headwing-dual-lane-v1",
        audience="research_human",
        stable_sections=["current_data_state", "final_lane", "diagnostic_lane"],
        flexible_sections=["open_questions"],
        change_policy="Additive changes only; never mix final and diagnostic lanes.",
        compatibility_note="Final lane uses usable_for_final=True sources only.",
    )
    result = suggest_literature_intake(
        ws,
        session_id="chaos-lit",
        uri="https://arxiv.org/abs/2605.99999",
        label="New chaos paper",
        short_summary="Relevant to diagnostic lane only.",
        detected_relevance="scope",
    )
    assert result["output_profile_context"]["output_version"] == "qsgw-headwing-dual-lane-v1"
    assert "final_lane" in result["output_profile_context"]["stable_sections"]
    assert "usable_for_final" in result["output_profile_context"]["lane_boundary_note"]
    assert "artifact_path" in result["output_profile_context"]


def test_literature_intake_output_profile_context_empty_without_profile(tmp_path):
    from brain.v5.literature_intake import suggest_literature_intake

    ws, _ = _setup_topic(tmp_path, active_claim=False)
    result = suggest_literature_intake(
        ws,
        session_id="chaos-lit",
        uri="https://arxiv.org/abs/2605.99999",
        label="New chaos paper",
        short_summary="Generic paper.",
    )
    assert result["output_profile_context"] == {}


def test_literature_intake_output_profile_note_comes_from_profile_not_hardcoded_qsgw(tmp_path):
    from brain.v5.literature_intake import suggest_literature_intake
    from brain.v5.output_stability import record_final_output_profile

    ws, _ = _setup_topic(tmp_path, active_claim=False)
    record_final_output_profile(
        ws,
        topic_id="quantum-chaos-long-range-spin-chains",
        output_version="quantum-chaos-related-work-v1",
        audience="research_human",
        stable_sections=["claim_scope", "prior_art_boundary"],
        flexible_sections=["open_questions"],
        change_policy="Separate rigorous theorem claims from heuristic numerical motivation.",
        compatibility_note="Do not treat related-work similarity as proof evidence.",
    )
    result = suggest_literature_intake(
        ws,
        session_id="chaos-lit",
        uri="https://arxiv.org/abs/2605.99999",
        label="New chaos paper",
        short_summary="Generic paper.",
    )
    note = result["output_profile_context"]["lane_boundary_note"]
    assert "rigorous theorem claims" in note
    assert "related-work similarity" in note
    assert "usable_for_final=True" not in note
