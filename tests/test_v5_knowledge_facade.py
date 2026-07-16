from __future__ import annotations

from dataclasses import asdict
import json

import pytest


def _candidate_payload(candidate) -> dict:
    return asdict(candidate)


def test_knowledge_facade_registers_precise_full_only_capabilities():
    from brain.v5.capability_registry import audit_capability_registry, capability_specs
    from brain.v5.capability_registry_data import COMPACT_MCP_NAMES
    from brain.v5.knowledge_surface_contracts import knowledge_operation_specs
    from brain.v5.public_surfaces import public_surface_names

    expected_effects = {
        "knowledge_diagnose_candidate": "read_only",
        "knowledge_record_review": "kernel_write",
        "knowledge_promote_candidate": "kernel_write",
        "knowledge_build_source_shelf": "runtime_write",
        "knowledge_get_source_shelf": "read_only",
        "knowledge_build_discovery_request": "read_only",
        "knowledge_normalize_discovery_result": "read_only",
        "knowledge_query": "read_only",
        "knowledge_compile_context": "read_only",
    }

    operation_specs = knowledge_operation_specs()
    capabilities = capability_specs()
    assert {name: spec.state_effect for name, spec in operation_specs.items()} == expected_effects
    assert set(expected_effects) <= set(capabilities)
    assert all(capabilities[name].compact_visibility == "full" for name in expected_effects)
    assert all(capabilities[name].cli_route for name in expected_effects)
    assert all(capabilities[name].public_surface == "knowledge_operation_result" for name in expected_effects)
    assert "knowledge_operation_result" in public_surface_names()
    assert len(COMPACT_MCP_NAMES) == 10
    assert not ({spec.mcp_name for spec in operation_specs.values()} & set(COMPACT_MCP_NAMES))
    assert audit_capability_registry()["issues"] == []


def test_knowledge_facade_diagnoses_queries_and_compiles_context_without_trust_write(
    tmp_path,
):
    from brain.v5 import mcp_tools
    from brain.v5.knowledge_candidates import KnowledgeCandidate
    from brain.v5.public_surfaces import require_valid_public_surface
    from tests.test_v5_knowledge_context import _context_workspace

    ws, shelf_report, assertion, _insight = _context_workspace(tmp_path)
    source_pin = shelf_report.manifest.source_pins[0]
    candidate = KnowledgeCandidate(
        candidate_id="generalized-entropy-definition-facade",
        content_kinds=("definition",),
        statement="Generalized entropy is area over four G_N plus bulk entropy.",
        topic_id="qg",
        subject_ref=assertion.record_ref,
        grounding_pins=(
            {
                "record_ref": source_pin.source_asset_ref,
                "content_hash": source_pin.record_content_hash,
                "revision": source_pin.record_revision,
            },
            {
                "record_ref": source_pin.source_location_pins[0].record_ref,
                "content_hash": source_pin.source_location_pins[0].content_hash,
                "revision": source_pin.source_location_pins[0].revision,
            },
        ),
        framework="semiclassical gravity",
        regime="island formula",
    )
    candidate_payload = _candidate_payload(candidate)
    before_trust = list(ws.registry_dir("trust_updates").glob("*.md"))

    diagnosed = mcp_tools.aitp_v5_knowledge_diagnose_candidate(
        str(tmp_path), payload_json=json.dumps({"candidate": candidate_payload})
    )
    retrieval = mcp_tools.aitp_v5_knowledge_query(
        str(tmp_path),
        payload_json=json.dumps(
            {
                "query": {
                    "text": "generalized entropy area bulk",
                    "topic_id": "qg",
                    "framework": "semiclassical gravity",
                    "regime": "island formula",
                    "max_results": 6,
                },
                "source_shelf_generation": shelf_report.manifest.generation,
                "source_shelf_topic_id": "qg",
            }
        ),
    )
    strong_retrieval = mcp_tools.aitp_v5_knowledge_query(
        str(tmp_path),
        payload_json=json.dumps(
            {
                "query": {
                    "text": "generalized entropy area bulk",
                    "topic_id": "qg",
                    "framework": "semiclassical gravity",
                    "regime": "island formula",
                    "max_results": 6,
                },
                "verification_mode": "strong",
                "source_shelf_generation": shelf_report.manifest.generation,
                "source_shelf_topic_id": "qg",
            }
        ),
    )
    context = mcp_tools.aitp_v5_knowledge_compile_context(
        str(tmp_path),
        payload_json=json.dumps(
            {
                "request": {
                    "query_text": "generalized entropy area bulk",
                    "topic_id": "qg",
                    "framework": "semiclassical gravity",
                    "regime": "island formula",
                    "mode": "normal",
                    "source_shelf_generation": shelf_report.manifest.generation,
                    "source_shelf_topic_id": "qg",
                }
            }
        ),
    )

    assert diagnosed["result"]["eligible_for_grounded_review"] is True
    assert retrieval["result"]["hits"]
    assert retrieval["result"]["coverage"]["complete"] is False
    assert retrieval["result"]["coverage"]["checked_scope"]["freshness_mode"] == (
        "orientation"
    )
    assert retrieval["result"]["can_claim_no_result"] is False
    assert strong_retrieval["result"]["coverage"]["complete"] is True
    assert strong_retrieval["result"]["coverage"]["checked_scope"][
        "freshness_mode"
    ] == "strong"
    assert context["result"]["entries"]
    assert context["result"]["estimated_tokens"] <= 1500
    assert context["result"]["orientation_only"] is True
    assert all(result["can_update_claim_trust"] is False for result in (diagnosed, retrieval, context))
    assert list(ws.registry_dir("trust_updates").glob("*.md")) == before_trust
    for result in (diagnosed, retrieval, context):
        assert require_valid_public_surface("knowledge_operation_result", result) is result


def test_knowledge_cli_matches_mcp_and_reads_utf8_sig_payload(tmp_path, capsys):
    from brain.v5 import cli, mcp_tools
    from tests.test_v5_knowledge_context import _context_workspace

    _ws, shelf_report, _assertion, _insight = _context_workspace(tmp_path)
    payload = {
        "request": {
            "query_text": "generalized entropy",
            "topic_id": "qg",
            "framework": "semiclassical gravity",
            "regime": "island formula",
            "mode": "startup",
            "source_shelf_generation": shelf_report.manifest.generation,
            "source_shelf_topic_id": "qg",
        }
    }
    payload_path = tmp_path / "knowledge-context.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8-sig")

    expected = mcp_tools.aitp_v5_knowledge_compile_context(
        str(tmp_path), payload_json=json.dumps(payload)
    )
    exit_code = cli.main(
        [
            "--base",
            str(tmp_path),
            "knowledge",
            "knowledge_compile_context",
            "--payload-file",
            str(payload_path),
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output == expected


def test_knowledge_facade_review_and_promotion_remain_checkpoint_gated(tmp_path):
    from brain.v5 import mcp_tools
    from brain.v5.record_repository import RecordRepository
    from tests.test_v5_knowledge_promotion import (
        _actor,
        _candidate,
        _review_checkpoint,
        _setup,
    )

    ws, pins = _setup(tmp_path)
    candidate = _candidate(pins)
    checkpoint = _review_checkpoint(ws, candidate)
    candidate_payload = _candidate_payload(candidate)

    reviewed = mcp_tools.aitp_v5_knowledge_record_review(
        str(tmp_path),
        payload_json=json.dumps(
            {
                "candidate": candidate_payload,
                "checkpoint_ref": asdict(checkpoint),
                "decision": "approve",
            }
        ),
    )
    promoted = mcp_tools.aitp_v5_knowledge_promote_candidate(
        str(tmp_path),
        payload_json=json.dumps(
            {
                "candidate": candidate_payload,
                "decision_ref": reviewed["result"]["pinned_ref"],
            }
        ),
    )

    repository = RecordRepository(ws, actor=_actor())
    assertion = repository.read(promoted["result"]["pinned_ref"]["record_ref"]).record
    assert reviewed["writes_records"] is True
    assert promoted["writes_records"] is True
    assert reviewed["result"]["checkpoint_ref"] == asdict(checkpoint)
    assert promoted["result"]["decision_ref"] == reviewed["result"]["pinned_ref"]
    assert assertion.review_status == "reviewed"
    assert assertion.can_update_claim_trust is False
    assert repository.list("evidence").records == ()
    assert repository.list("trust_updates").records == ()
    assert reviewed["can_update_claim_trust"] is False
    assert promoted["can_update_claim_trust"] is False


def test_knowledge_facade_builds_only_derived_shelf_state(tmp_path):
    from brain.v5 import mcp_tools
    from brain.v5.query_index import current_canonical_watermark
    from tests.test_v5_source_shelf import _acquired_asset, _setup_topic

    ws = _setup_topic(tmp_path)
    asset, _blob, _location = _acquired_asset(
        ws,
        name="facade-source-shelf",
        content=b"# Definition\n\nDefinition 1. A bounded exact source.\n",
    )
    source_ref = f"source_asset:{asset.asset_id}"
    before = current_canonical_watermark(ws)
    built = mcp_tools.aitp_v5_knowledge_build_source_shelf(
        str(tmp_path),
        payload_json=json.dumps(
            {
                "request": {
                    "topic_id": "qg",
                    "source_asset_refs": [source_ref],
                    "curation_rationale": "Exercise the full-only derived shelf facade.",
                    "max_passage_chars": 1200,
                }
            }
        ),
    )
    loaded = mcp_tools.aitp_v5_knowledge_get_source_shelf(
        str(tmp_path),
        payload_json=json.dumps(
            {"generation": built["result"]["manifest"]["generation"]}
        ),
    )

    assert built["state_effect"] == "runtime_write"
    assert built["writes_records"] is False
    assert built["writes_derived_state"] is True
    assert loaded["result"]["manifest"] == built["result"]["manifest"]
    assert loaded["result"]["passages"]
    assert current_canonical_watermark(ws) == before


def test_knowledge_facade_discovery_stays_process_only(tmp_path):
    from brain.v5 import mcp_tools
    from brain.v5.query_index import current_canonical_watermark
    from tests.test_v5_literature_discovery import _setup_discovery, _spec

    ws, _claim, _obligation, _audit, gap_pin, audit_pin = _setup_discovery(tmp_path)
    before = current_canonical_watermark(ws)
    requested = mcp_tools.aitp_v5_knowledge_build_discovery_request(
        str(tmp_path),
        payload_json=json.dumps({"spec": asdict(_spec(gap_pin, audit_pin))}),
    )
    connector_result = {
        "connector_results": [
            {
                "connector_id": "quantum_gravity_literature",
                "status": "ok",
                "coverage": {"query_count": 1, "pages_checked": 1},
                "results": [
                    {
                        "doi": "10.1000/facade.1",
                        "title": "A bounded replica-wormhole source candidate",
                        "authors": ["A. Physicist"],
                        "year": 2025,
                        "uri": "https://doi.org/10.1000/facade.1",
                        "framework": "quantum_gravity",
                        "source_type": "primary_paper",
                        "snippet": "Orientation only.",
                        "access_disposition": "open_access",
                    }
                ],
            }
        ]
    }
    normalized = mcp_tools.aitp_v5_knowledge_normalize_discovery_result(
        str(tmp_path),
        payload_json=json.dumps(
            {"request": requested["result"], "connector_result": connector_result}
        ),
    )

    assert requested["state_effect"] == "read_only"
    assert normalized["state_effect"] == "read_only"
    assert normalized["result"]["candidates"][0]["orientation_only"] is True
    assert normalized["result"]["candidates"][0]["can_update_claim_trust"] is False
    assert normalized["result"]["can_create_source_asset"] is False
    assert current_canonical_watermark(ws) == before

    tampered_request = dict(requested["result"])
    tampered_request["can_create_source_asset"] = True
    with pytest.raises(ValueError, match="trust boundary"):
        mcp_tools.aitp_v5_knowledge_normalize_discovery_result(
            str(tmp_path),
            payload_json=json.dumps(
                {
                    "request": tampered_request,
                    "connector_result": connector_result,
                }
            ),
        )


def test_knowledge_surface_contract_rejects_nested_trust_inflation(tmp_path):
    from brain.v5 import mcp_tools
    from brain.v5.knowledge_surface_contracts import validate_knowledge_operation_result
    from tests.test_v5_knowledge_context import _context_workspace

    _ws, shelf_report, _assertion, _insight = _context_workspace(tmp_path)
    payload = mcp_tools.aitp_v5_knowledge_compile_context(
        str(tmp_path),
        payload_json=json.dumps(
            {
                "request": {
                    "query_text": "generalized entropy",
                    "topic_id": "qg",
                    "mode": "startup",
                    "source_shelf_generation": shelf_report.manifest.generation,
                    "source_shelf_topic_id": "qg",
                }
            }
        ),
    )
    payload["result"]["entries"][0]["can_update_claim_trust"] = True

    invalid = validate_knowledge_operation_result(payload)

    assert invalid.ok is False
    assert any("can_update_claim_trust" in issue.path for issue in invalid.issues)
