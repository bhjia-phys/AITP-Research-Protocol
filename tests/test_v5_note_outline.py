from __future__ import annotations

import json


def _invoke(args, capsys):
    from brain.v5.cli import main

    assert main(args) == 0
    return json.loads(capsys.readouterr().out)


def _seed_hidden_symmetry_topic(tmp_path):
    from brain.v5.authorities import record_authority
    from brain.v5.physics_objects import record_object_relation, record_physics_object
    from brain.v5.research_state import attach_artifact, create_proof_obligation, update_claim_status
    from brain.v5.sensemaking import record_sensemaking_report
    from brain.v5.source_assets import register_source_asset
    from brain.v5.tools import record_tool_run
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    topic_id = "quantum-chaos-long-range-spin-chains"
    create_topic(ws, topic_id, context_id="spin-chains", title="HS hidden symmetry")
    claim = create_claim(
        ws,
        topic_id=topic_id,
        statement=(
            "Alpha=2 motif-sector authority helps organize level-statistics diagnostics, "
            "but the all-L hidden-symmetry proof remains open."
        ),
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="all-L closure proof is still a proof obligation",
        scope="finite symbolic certificates and sector-resolved diagnostics",
        non_claims="No all-L theorem or limiting-case conclusion is established.",
        strongest_failure_mode="Finite-L sector certificates may not lift to the closure algebra.",
    )
    bind_session(ws, "s-hs", topic_id=topic_id, context_id="spin-chains", active_claim=claim.claim_id)
    register_source_asset(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        asset_type="note",
        uri="file:///theory/hs-alpha-axis-notes.md",
        title="HS alpha-axis notebook",
        summary="Working notes for alpha=2 sector authority and generic-alpha proof gaps.",
    )
    sector = record_physics_object(
        ws,
        topic_id=topic_id,
        object_type="sector",
        name="alpha=2 motif sector",
        definition="Coefficient-discovered {J0,Q} sector labels used for alpha=2 diagnostics.",
        notation="{J0,Q}",
        source_refs=["source_asset:hs-alpha-axis-notes"],
    )
    closure = record_physics_object(
        ws,
        topic_id=topic_id,
        object_type="operator_algebra",
        name="commutant closure",
        definition="Candidate operator closure envelope for the hidden-symmetry proof route.",
        notation="Comm(H)",
        source_refs=["source_asset:hs-alpha-axis-notes"],
    )
    relation = record_object_relation(
        ws,
        topic_id=topic_id,
        relation_type="sector_authority_relation",
        subject_id=sector.object_id,
        object_id=closure.object_id,
        statement="The alpha=2 HS sector authority is useful only inside the commutant closure route.",
        claim_id=claim.claim_id,
        assumptions=["finite symbolic certificates are not all-L proof"],
        failure_modes=["sector labels may fail to lift to the all-L algebra"],
        source_refs=["source_asset:hs-alpha-axis-notes"],
        status="hypothesis",
    )
    record_authority(
        ws,
        topic_id=topic_id,
        authority_type="sector_authority",
        authority_statement="Use coefficient-discovered {J0,Q} associative/Yangian motif sectors for alpha=2 labels.",
        work_package="alpha=2 sector authority",
        claim_id=claim.claim_id,
        scope={"alpha_class": "alpha=2", "sizes": [5, 6, 7]},
        generator_set="{J0,Q}",
        closure_envelope="Yangian/associative",
        source_refs=["source_asset:hs-alpha-axis-notes"],
        limitations=["not an all-L Yangian proof"],
    )
    artifact = attach_artifact(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        artifact_type="finite_certificate_table",
        uri="file:///results/hs-alpha2-finite-certificates.json",
        summary="Finite certificate table for alpha=2 sector diagnostics.",
    )
    record_tool_run(
        ws,
        recipe_id="recipe-symbolic-sector-check",
        tool_family="symbolic",
        tool_name="sector_certificate_scan",
        topic_id=topic_id,
        claim_id=claim.claim_id,
        inputs={"alpha": 2, "sizes": [5, 6, 7]},
        outputs={"finite_certificate": artifact.artifact_id, "level_statistics": "diagnostic_only"},
        artifact_ids=[artifact.artifact_id],
        source_refs=["source_asset:hs-alpha-axis-notes"],
    )
    record_sensemaking_report(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        title="Commutant closure route and alpha=2 boundary",
        summary=(
            "Schur/commutant closure is the useful algebraic method; alpha=2 sectors are "
            "recorded as authority-controlled diagnostics, not as theorem evidence."
        ),
        object_ids=[sector.object_id, closure.object_id],
        relation_ids=[relation.relation_id],
        open_questions=["Can the closure residual be bounded for all L?"],
        next_actions=["split the all-L proof into typed proof obligations"],
    )
    create_proof_obligation(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        statement="Prove the commutant closure route for all chain lengths L.",
        obligation_type="all_L_theorem_gap",
        status="open",
        maturity_level="theorem-candidate",
        next_action="derive closure residual identities",
        required_evidence=["symbolic proof or formalized all-L derivation"],
        source_refs=["source_asset:hs-alpha-axis-notes"],
    )
    update_claim_status(
        ws,
        topic_id=topic_id,
        claim_id=claim.claim_id,
        maturity_level="theorem-candidate",
        claim_status="open_gap_preserved",
        scope="finite symbolic certificates only",
        risk="finite-L evidence may not lift to all L",
        next_action="keep limiting-case and all-L conclusions separate",
        open_gaps=["limiting-case section has no typed relation or authority yet"],
        source_refs=["source_asset:hs-alpha-axis-notes"],
        artifact_ids=[artifact.artifact_id],
    )
    return ws, claim


def test_note_outline_compiles_hidden_symmetry_sections_without_trust(tmp_path):
    from brain.v5.note_outline import compile_note_outline
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _seed_hidden_symmetry_topic(tmp_path)

    payload = require_valid_public_surface("note_outline", compile_note_outline(ws, "s-hs", style="jhep"))

    assert payload["kind"] == "note_outline"
    assert payload["orientation_only"] is True
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False
    assert payload["note_boundary"]["does_not_write_note"] is True
    sections = {section["section_id"]: section for section in payload["sections"]}
    assert sections["model_conventions"]["readiness_state"] == "draftable"
    assert sections["alpha_2"]["readiness_state"] == "draftable"
    assert sections["limitations"]["readiness_state"] == "draftable"
    assert sections["alpha_infinity"]["readiness_state"] == "needs_records"
    assert "source_assets" in sections["alpha_infinity"]["missing_requirements"]
    assert claim.claim_id in sections["alpha_2"]["claim_ids"]
    assert any(ref.startswith("authority:") for ref in sections["alpha_2"]["record_refs"]["authorities"])
    assert payload["compile_summary"]["needs_records_sections"] >= 1
    assert any(action["record_type"] == "source_assets" for action in payload["next_valid_actions"])


def test_note_outline_cli_mcp_and_trust_preflight_boundary(tmp_path, capsys):
    from brain.v5.mcp_tools import aitp_v5_compile_note_outline
    from brain.v5.models import TrustUpdateRequest
    from brain.v5.trust_updates import preflight_trust_update

    ws, claim = _seed_hidden_symmetry_topic(tmp_path)

    cli_payload = _invoke(
        ["--base", str(tmp_path), "status", "note-outline", "s-hs", "--style", "jhep"],
        capsys,
    )
    mcp_payload = aitp_v5_compile_note_outline(str(tmp_path), session_id="s-hs", style="jhep")
    preflight = preflight_trust_update(
        ws,
        TrustUpdateRequest(
            request_id="trust-req-note-outline",
            action="change_claim_confidence",
            session_id="s-hs",
            topic_id="quantum-chaos-long-range-spin-chains",
            claim_id=claim.claim_id,
            requested_state="validated",
            source_kind="note_outline",
            source_ref=cli_payload["outline_id"],
            rationale="A note outline is orientation-only and cannot validate a claim.",
        ),
    )

    assert cli_payload["kind"] == "note_outline"
    assert mcp_payload["kind"] == "note_outline"
    assert cli_payload["section_count"] == mcp_payload["section_count"]
    assert preflight["allowed"] is False
    assert any(reason["policy_id"] == "no_summary_surface_as_truth_source" for reason in preflight["policy_reasons"])
