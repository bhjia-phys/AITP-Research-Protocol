from __future__ import annotations

import json


def _invoke(args, capsys):
    from brain.v5.cli import main

    assert main(args) == 0
    return json.loads(capsys.readouterr().out)


def test_authority_record_preserves_hidden_symmetry_sector_convention_without_trust(tmp_path):
    from brain.v5.authorities import authority_registry_payload, record_authority
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "quantum-chaos-long-range-spin-chains", context_id="spin-chains", title="HS hidden symmetry")
    claim = create_claim(
        ws,
        topic_id="quantum-chaos-long-range-spin-chains",
        statement="Alpha=2 motif sectors are useful for sector-resolved statistics only under explicit convention control.",
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="sector authority is not an all-L theorem",
    )

    authority = record_authority(
        ws,
        topic_id="quantum-chaos-long-range-spin-chains",
        authority_type="sector_authority",
        authority_statement="Use coefficient-discovered {J0,Q} associative/Yangian motif sectors for alpha=2 labels.",
        work_package="WP2 alpha=2 HS Yangian/motif sector authority",
        claim_id=claim.claim_id,
        scope={"alpha_class": "alpha=2", "sizes": [5, 6, 7], "formula_extension": "L<=16"},
        generator_set="{J0,Q}",
        closure_envelope="Yangian/associative",
        evidence_refs=["evidence:finite-certificate-alpha2"],
        source_refs=["source:hs-alpha-notebook"],
        limitations=[
            "not all-L Yangian proof",
            "sector-internal P(r) undefined when H is scalar",
        ],
    )
    record_payload = require_valid_public_surface("authority_record", {"ok": True, **authority.__dict__})
    registry = require_valid_public_surface(
        "authority_registry",
        authority_registry_payload(ws, topic_id="quantum-chaos-long-range-spin-chains"),
    )

    assert record_payload["kind"] == "authority"
    assert record_payload["authority_type"] == "sector_authority"
    assert record_payload["orientation_only"] is True
    assert record_payload["can_update_claim_trust"] is False
    assert registry["kind"] == "authority_registry"
    assert registry["authority_count"] == 1
    assert registry["authorities"][0]["authority_id"] == authority.authority_id
    assert registry["can_update_claim_trust"] is False


def test_authority_cli_and_mcp_list_roundtrip(tmp_path, capsys):
    from brain.v5.mcp_tools import aitp_v5_list_authorities, aitp_v5_record_authority
    from brain.v5.workspace import create_topic, init_workspace

    init_workspace(tmp_path)
    create_topic(init_workspace(tmp_path), "qsgw-headwing-update-librpa", context_id="librpa", title="LibRPA headwing")

    cli_record = _invoke(
        [
            "--base",
            str(tmp_path),
            "authority",
            "record",
            "--topic",
            "qsgw-headwing-update-librpa",
            "--type",
            "code_path_authority",
            "--statement",
            "Use final-lane LibRPA output roots, not stale diagnostic TSVs, for reusable headwing conclusions.",
            "--work-package",
            "final-lane provenance",
            "--scope-json",
            '{"lane":"final","material_set":["Si","BN","MgO"]}',
            "--limitation",
            "diagnostic TSVs cannot establish final-lane reuse",
            "--source-ref",
            "source:librpa-headwing-notebook",
        ],
        capsys,
    )
    cli_list = _invoke(
        [
            "--base",
            str(tmp_path),
            "authority",
            "list",
            "--topic",
            "qsgw-headwing-update-librpa",
            "--type",
            "code_path_authority",
        ],
        capsys,
    )
    mcp_record = aitp_v5_record_authority(
        str(tmp_path),
        topic_id="qsgw-headwing-update-librpa",
        authority_type="dataset_authority",
        authority_statement="Use explicitly tagged final dashboard inputs for convergence comparisons.",
        work_package="final-lane provenance",
        scope={"lane": "final"},
        limitations=["does not validate the physical conclusion by itself"],
        source_refs=["source:final-dashboard-manifest"],
    )
    mcp_list = aitp_v5_list_authorities(str(tmp_path), topic_id="qsgw-headwing-update-librpa")

    assert cli_record["kind"] == "authority"
    assert cli_list["kind"] == "authority_registry"
    assert cli_list["authority_count"] == 1
    assert mcp_record["kind"] == "authority"
    assert mcp_list["authority_count"] == 2
    assert all(item["can_update_claim_trust"] is False for item in mcp_list["authorities"])


def test_authority_record_cannot_satisfy_trust_preflight(tmp_path):
    from brain.v5.authorities import record_authority
    from brain.v5.models import TrustUpdateRequest
    from brain.v5.trust_updates import preflight_trust_update
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "hs-authority-trust-boundary", context_id="spin-chains", title="Authority trust boundary")
    claim = create_claim(
        ws,
        topic_id="hs-authority-trust-boundary",
        statement="Authority records orient sector conventions but do not prove level-statistics conclusions.",
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="proof and validation records remain missing",
    )
    authority = record_authority(
        ws,
        topic_id="hs-authority-trust-boundary",
        authority_type="statistics_convention",
        authority_statement="Use sector-resolved spacing ratios only after a sector authority is explicit.",
        claim_id=claim.claim_id,
        scope={"observable": "P(r)", "gate": "statistics"},
        source_refs=["source:sector-statistics-note"],
    )

    payload = preflight_trust_update(
        ws,
        TrustUpdateRequest(
            request_id="trust-req-authority-only",
            action="change_claim_confidence",
            session_id="s-authority",
            topic_id="hs-authority-trust-boundary",
            claim_id=claim.claim_id,
            requested_state="validated",
            source_kind="authority_record",
            source_ref=f"authority:{authority.authority_id}",
            evidence_refs=[],
            rationale="Authority records are orientation-only and must not satisfy trust promotion.",
        ),
    )

    assert payload["kind"] == "trust_update_preflight"
    assert payload["allowed"] is False
    assert payload["mutation_allowed_after_preflight"] is False
    assert "query_execution_brief_or_typed_record" in payload["required_actions"]
    assert any(reason["policy_id"] == "no_summary_surface_as_truth_source" for reason in payload["policy_reasons"])
