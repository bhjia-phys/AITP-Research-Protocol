from __future__ import annotations

import json
from pathlib import Path


def _seed_workspace(tmp_path: Path):
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(
        ws,
        "quantum-chaos-long-range-spin-chains",
        context_id="theory",
        title="Quantum chaos in long-range spin chains",
    )
    claim = create_claim(
        ws,
        topic_id="quantum-chaos-long-range-spin-chains",
        statement="At the PBC alpha=2 point, H4^HS refines residual Lambda2 blocks and matches the motif formula through finite-L Fisherd checks.",
        evidence_profile="formula_and_numerics",
        confidence_state="hypothesis",
        active_uncertainty="Finite-L checks are not a theorem and need proof obligations before publication.",
        scope="PBC alpha=2, L=10-12 finite Hilbert spaces",
        strongest_failure_mode="Motif formula could match finite samples without proving all-L Yangian classification.",
    )
    result_path = tmp_path / "alpha2_h4_motif_formula_check_L10_L12_fisherd_v1.json"
    result_path.write_text(
        json.dumps(
            {
                "tool": "alpha2_h4_motif_formula_check",
                "created_at": "2026-05-31T22:14:06+0800",
                "cases": [
                    {
                        "sites": 10,
                        "counts": {"matched_groups": 82, "mismatch_groups": 0},
                        "status": "complete_h4_formula_match",
                    },
                    {
                        "sites": 12,
                        "counts": {"matched_groups": 290, "mismatch_groups": 0},
                        "status": "complete_h4_formula_match",
                    },
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return ws, claim, result_path


def test_research_state_records_bounded_fisherd_evidence_without_trust_promotion(tmp_path):
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.research_state import record_bounded_numerical_evidence
    from brain.v5.workspace import get_claim

    ws, claim, result_path = _seed_workspace(tmp_path)

    payload = record_bounded_numerical_evidence(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        artifact_uri=str(result_path),
        artifact_type="fisherd_result_json",
        artifact_summary="Fisherd L=10-12 H4 motif formula result has zero mismatch groups.",
        status="supports",
        supports_outputs=["finite_L_H4_motif_formula_check_L10_L12"],
        scope="Finite L=10-12 Fisherd JSON audit only; not an all-L theorem.",
        command="python alpha2_h4_motif_formula_check.py",
        machine="fisherd",
        remote_root="/home/bhj/ai-runs/quantum-chaos/20260531-spectral-commutant",
        outputs={"status_by_case": ["complete_h4_formula_match"]},
        source_refs=["note:alpha2_yangian_algebra_structure_20260531"],
        open_gaps=["prove all-L H4 motif formula from Yangian/HS algebra"],
    )

    assert require_valid_public_surface("bounded_numerical_evidence_bundle", payload) == payload
    assert payload["artifact"]["metadata"]["sha256"]
    assert payload["artifact"]["metadata"]["remote_root"].endswith("20260531-spectral-commutant")
    assert payload["tool_run"]["evidence_status"] == "supports"
    assert payload["evidence"]["supports_outputs"] == ["finite_L_H4_motif_formula_check_L10_L12"]
    assert payload["claim_status"]["maturity_level"] == "finite-size evidence"
    assert payload["claim_status"]["can_update_claim_trust"] is False
    assert payload["trust_update_forbidden"] is True
    assert payload["can_update_claim_trust"] is False
    assert get_claim(ws, claim.claim_id).confidence_state == "hypothesis"
    assert list((ws.registry_dir("trust_updates")).glob("*.md")) == []
    assert list((ws.root / "memory" / "l2" / "entries").glob("*.md")) == []


def test_research_state_cli_mcp_and_runtime_entrypoints(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import (
        aitp_v5_attach_artifact,
        aitp_v5_attach_artifact_auto,
        aitp_v5_classify_research_event,
        aitp_v5_create_proof_obligation,
        aitp_v5_record_bounded_numerical_evidence,
        aitp_v5_register_source,
        aitp_v5_update_claim_status,
        aitp_v5_update_proof_obligation,
    )
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.brief import build_execution_brief
    from brain.v5.workspace import bind_session

    ws, claim, result_path = _seed_workspace(tmp_path)

    assert main(
        [
            "--base",
            str(ws.base),
            "research-state",
            "bounded-evidence",
            "--topic",
            claim.topic_id,
            "--claim",
            claim.claim_id,
            "--artifact-uri",
            str(result_path),
            "--artifact-type",
            "fisherd_result_json",
            "--artifact-summary",
            "Fisherd JSON confirms H4 motif formula matches through L=10-12.",
            "--status",
            "supports",
            "--supports-output",
            "finite_L_H4_motif_formula_check_L10_L12",
            "--scope",
            "Finite L=10-12 only; no all-L theorem.",
            "--machine",
            "fisherd",
            "--remote-root",
            "/home/bhj/ai-runs/quantum-chaos/20260531-spectral-commutant",
            "--open-gap",
            "derive all-L theorem",
        ]
    ) == 0
    cli_payload = json.loads(capsys.readouterr().out)

    source = aitp_v5_register_source(
        str(ws.base),
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        uri="arxiv:2604.14695",
        label="Close prior-art literature source",
        connector_id="literature_search",
        location_type="paper",
        summary="Prior-art threat to level-statistics novelty, not direct proof of algebraic classification.",
    )
    artifact = aitp_v5_attach_artifact(
        str(ws.base),
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        artifact_type="fisherd_result_json",
        uri=str(result_path),
        summary="Fisherd result file.",
        size_bytes=str(result_path.stat().st_size),
    )
    auto_artifact = aitp_v5_attach_artifact_auto(
        str(ws.base),
        path=str(result_path),
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        artifact_type="fisherd_result_json",
        summary="Auto-attached Fisherd result file.",
        metadata={"role": "benchmark_output"},
    )
    status = aitp_v5_update_claim_status(
        str(ws.base),
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        maturity_level="finite-size evidence",
        claim_status="bounded_check_recorded",
        scope="L=10-12 only",
        risk="not a theorem",
        next_action="create proof obligation",
        artifact_ids=[artifact["artifact_id"]],
    )
    obligation = aitp_v5_create_proof_obligation(
        str(ws.base),
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        statement="Prove the H4 motif formula for all L from HS/Yangian structure.",
        obligation_type="theorem_gap",
        status="open",
        maturity_level="theorem-candidate",
        next_action="derive from motif occupation formula",
        required_evidence=["symbolic derivation", "independent finite-L audit"],
    )
    updated_obligation = aitp_v5_update_proof_obligation(
        str(ws.base),
        obligation_id=obligation["obligation_id"],
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        status="refined",
        next_action="derive from motif occupation formula and log remaining exception classes",
        proof_strategy=["Yangian/motif derivation"],
        evidence_refs=["evidence:finite_L_H4_motif_formula_check_L10_L12"],
    )
    classification = aitp_v5_classify_research_event(
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        event_kind="fisherd_result_json",
        event_summary="Fisherd JSON result with hashes and zero H4 motif mismatches.",
        source_uri=str(result_path),
    )
    mcp_payload = aitp_v5_record_bounded_numerical_evidence(
        str(ws.base),
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        artifact_uri=str(result_path),
        artifact_type="fisherd_result_json",
        artifact_summary="Fisherd JSON confirms H4 motif formula matches through L=10-12.",
        status="supports",
        supports_outputs=["finite_L_H4_motif_formula_check_L10_L12"],
        scope="Finite L=10-12 only; no all-L theorem.",
    )

    assert cli_payload["kind"] == "bounded_numerical_evidence_bundle"
    assert source["orientation_only"] is True
    assert artifact["kind"] == "artifact"
    assert isinstance(artifact["size_bytes"], int)
    assert auto_artifact["kind"] == "artifact"
    assert auto_artifact["uri"].startswith("file://")
    assert auto_artifact["size_bytes"] == result_path.stat().st_size
    assert auto_artifact["metadata"]["capture_tool"] == "aitp_v5_attach_artifact_auto"
    assert auto_artifact["metadata"]["sha256"]
    assert auto_artifact["metadata"]["mtime_utc"]
    assert auto_artifact["metadata"]["role"] == "benchmark_output"
    assert status["kind"] == "claim_status"
    assert status["can_update_claim_trust"] is False
    assert obligation["kind"] == "proof_obligation"
    assert obligation["can_update_claim_trust"] is False
    assert updated_obligation["status"] == "refined"
    assert "Yangian/motif derivation" in updated_obligation["proof_strategy"]
    assert classification["recommended_action"] == "record_bounded_numerical_evidence"
    assert classification["trust_update_forbidden"] is True
    assert mcp_payload["kind"] == "bounded_numerical_evidence_bundle"
    assert mcp_payload["trust_update_forbidden"] is True
    assert runtime_entrypoints()["register_source"]["mcp"] == "aitp_v5_register_source"
    assert runtime_entrypoints()["attach_artifact"]["surface"] == "artifact_record"
    assert runtime_entrypoints()["attach_artifact_auto"]["mcp"] == "aitp_v5_attach_artifact_auto"
    assert runtime_entrypoints()["update_proof_obligation"]["mcp"] == "aitp_v5_update_proof_obligation"
    assert runtime_entrypoints()["research_event_classifier"]["surface"] == "research_event_classification"

    bind_session(
        ws,
        "session-alpha2",
        topic_id=claim.topic_id,
        context_id="theory",
        active_claim=claim.claim_id,
    )
    brief = build_execution_brief(ws, "session-alpha2")
    assert brief["research_gates"]["record_level_human_gate_required"] is True
    assert brief["research_gates"]["open_proof_obligation_count"] >= 1
    assert brief["human_checkpoint"]["needed"] is False


def test_attach_artifact_cli_preserves_hash_metadata_and_entrypoint_contract(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.runtime_entrypoints import runtime_entrypoints
    from brain.v5.runtime_entrypoint_samples import sample_args_for_template

    ws, claim, result_path = _seed_workspace(tmp_path)

    assert main(
        [
            "--base",
            str(ws.base),
            "research-state",
            "attach-artifact",
            "--topic",
            claim.topic_id,
            "--claim",
            claim.claim_id,
            "--type",
            "benchmark_log",
            "--uri",
            str(result_path),
            "--summary",
            "Benchmark log/result artifact attached by reference.",
            "--metadata-json",
            '{"role":"benchmark_output"}',
        ]
    ) == 0

    payload = json.loads(capsys.readouterr().out)

    assert payload["kind"] == "artifact"
    assert payload["artifact_type"] == "benchmark_log"
    assert payload["topic_id"] == claim.topic_id
    assert payload["claim_id"] == claim.claim_id
    assert payload["size_bytes"] == result_path.stat().st_size
    assert payload["metadata"]["sha256"]
    assert payload["metadata"]["role"] == "benchmark_output"
    assert payload["metadata"]["can_update_claim_trust"] is False
    attach_entrypoint = runtime_entrypoints()["attach_artifact"]
    assert attach_entrypoint["cli"] == "aitp-v5 research-state attach-artifact <args>"
    assert attach_entrypoint["mcp"] == "aitp_v5_attach_artifact"
    assert attach_entrypoint["surface"] == "artifact_record"
    sample_args = sample_args_for_template("research-state attach-artifact <args>")
    assert "--type" in sample_args
    assert "result_json" in sample_args
    assert "--uri" in sample_args


def test_attach_artifact_auto_cli_captures_local_file_metadata(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.runtime_bridge_targets import runtime_bridge_target_manifest
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints
    from brain.v5.runtime_entrypoint_samples import sample_args_for_template

    ws, claim, result_path = _seed_workspace(tmp_path)

    assert main(
        [
            "--base",
            str(ws.base),
            "research-state",
            "attach-artifact-auto",
            "--path",
            str(result_path),
            "--topic",
            claim.topic_id,
            "--claim",
            claim.claim_id,
            "--type",
            "benchmark_log",
            "--summary",
            "Benchmark log/result artifact auto-attached by reference.",
            "--metadata-json",
            '{"role":"benchmark_output"}',
        ]
    ) == 0

    payload = json.loads(capsys.readouterr().out)

    assert payload["kind"] == "artifact"
    assert payload["artifact_type"] == "benchmark_log"
    assert payload["uri"].startswith("file://")
    assert payload["size_bytes"] == result_path.stat().st_size
    assert payload["metadata"]["capture_tool"] == "aitp_v5_attach_artifact_auto"
    assert payload["metadata"]["sha256"]
    assert payload["metadata"]["hash_algorithm"] == "sha256"
    assert payload["metadata"]["mtime_utc"]
    assert payload["metadata"]["mime_type"]
    assert payload["metadata"]["can_update_claim_trust"] is False
    attach_auto_entrypoint = runtime_entrypoints()["attach_artifact_auto"]
    assert attach_auto_entrypoint == {
        "cli": "aitp-v5 research-state attach-artifact-auto <args>",
        "mcp": "aitp_v5_attach_artifact_auto",
        "surface": "artifact_record",
    }
    manifest = runtime_bridge_target_manifest()
    by_operation = {target["operation"]: target for target in manifest["targets"]}
    assert by_operation["attachArtifactAuto"]["mcp_tool"] == "aitp_v5_attach_artifact_auto"
    assert by_operation["attachArtifactAuto"]["cli_fallback"] == (
        "aitp-v5 research-state attach-artifact-auto <args>"
    )
    assert sample_args_for_template("research-state attach-artifact-auto <args>")[0] == "--path"
    assert validate_runtime_entrypoints() == []


def test_public_surface_validators_accept_research_state_payloads():
    from brain.v5.public_surfaces import require_valid_public_surface

    artifact = {
        "ok": True,
        "kind": "artifact",
        "artifact_id": "artifact-fisherd-abc",
        "topic_id": "quantum-chaos-long-range-spin-chains",
        "claim_id": "claim-alpha2",
        "artifact_type": "fisherd_result_json",
        "uri": "results/alpha2.json",
        "summary": "Finite-L Fisherd result.",
        "size_bytes": 123,
        "metadata": {"sha256": "abc"},
    }
    claim_status = {
        "ok": True,
        "kind": "claim_status",
        "status_id": "claim-status-alpha2",
        "topic_id": "quantum-chaos-long-range-spin-chains",
        "claim_id": "claim-alpha2",
        "maturity_level": "finite-size evidence",
        "claim_status": "bounded_check_recorded",
        "scope": "L=10-12",
        "risk": "not an all-L proof",
        "next_action": "create proof obligation",
        "assumptions": [],
        "open_gaps": ["all-L theorem"],
        "source_refs": [],
        "evidence_refs": ["evidence-alpha2"],
        "artifact_ids": ["artifact-fisherd-abc"],
        "human_gate_required": True,
        "can_update_claim_trust": False,
    }
    obligation = {
        "ok": True,
        "kind": "proof_obligation",
        "obligation_id": "proof-obligation-alpha2",
        "topic_id": "quantum-chaos-long-range-spin-chains",
        "claim_id": "claim-alpha2",
        "statement": "Prove the H4 motif formula for all L.",
        "obligation_type": "theorem_gap",
        "status": "open",
        "maturity_level": "theorem-candidate",
        "next_action": "derive from motif formula",
        "required_evidence": ["symbolic proof"],
        "proof_strategy": ["Yangian/motif derivation"],
        "failure_modes": ["finite-L overfit"],
        "source_refs": [],
        "evidence_refs": ["evidence-alpha2"],
        "artifact_ids": ["artifact-fisherd-abc"],
        "human_gate_required": True,
        "can_update_claim_trust": False,
    }
    classification = {
        "ok": True,
        "kind": "research_event_classification",
        "topic_id": "quantum-chaos-long-range-spin-chains",
        "claim_id": "claim-alpha2",
        "event_kind": "fisherd_result_json",
        "event_summary": "Fisherd JSON result.",
        "source_uri": "results/alpha2.json",
        "candidate_record_types": ["artifact", "tool_run", "evidence"],
        "recommended_action": "record_bounded_numerical_evidence",
        "needs_claim_binding": False,
        "needs_human_gate": False,
        "risk_notes": ["classification is orientation-only"],
        "trust_update_forbidden": True,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }

    assert require_valid_public_surface("artifact_record", artifact) == artifact
    assert require_valid_public_surface("claim_status_record", claim_status) == claim_status
    assert require_valid_public_surface("proof_obligation_record", obligation) == obligation
    assert require_valid_public_surface("research_event_classification", classification) == classification
