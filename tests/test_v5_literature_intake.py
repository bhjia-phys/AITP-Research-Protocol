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
