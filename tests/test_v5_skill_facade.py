from __future__ import annotations

from dataclasses import asdict
import json

import pytest


def test_skill_facade_registers_precise_full_only_capabilities():
    from brain.v5.capability_registry import audit_capability_registry, capability_specs
    from brain.v5.capability_registry_data import COMPACT_MCP_NAMES
    from brain.v5.public_surfaces import public_surface_names
    from brain.v5.skill_surface_contracts import skill_operation_specs

    expected_effects = {
        "skill_distill_candidate": "kernel_write",
        "skill_assess_readiness": "kernel_write",
        "skill_build_package_preview": "runtime_write",
        "skill_record_package_proposal": "kernel_write",
        "skill_plan_deployment": "kernel_write",
        "skill_apply_deployment": "kernel_write",
        "skill_match_applicable": "read_only",
        "skill_record_usage": "kernel_write",
        "skill_propose_patch": "kernel_write",
        "skill_build_validation_request": "read_only",
    }

    operation_specs = skill_operation_specs()
    capabilities = capability_specs()

    assert {name: spec.state_effect for name, spec in operation_specs.items()} == expected_effects
    assert set(expected_effects) <= set(capabilities)
    assert all(capabilities[name].compact_visibility == "full" for name in expected_effects)
    assert all(capabilities[name].cli_route for name in expected_effects)
    assert all(
        capabilities[name].public_surface == "skill_operation_result"
        for name in expected_effects
    )
    assert "skill_operation_result" in public_surface_names()
    assert len(COMPACT_MCP_NAMES) == 10
    assert not ({spec.mcp_name for spec in operation_specs.values()} & set(COMPACT_MCP_NAMES))
    assert audit_capability_registry()["issues"] == []


def test_skill_cli_matches_mcp_and_reads_utf8_sig_payload(tmp_path, capsys):
    from brain.v5 import cli, mcp_tools

    payload = {
        "commands": [
            {
                "kind": "aitp_builtin_declarative",
                "validator_id": "skill-fixture-v1",
                "fixture": "tests/skill-smoke.json",
                "network": "forbidden",
                "writes": [],
                "timeout_seconds": 30,
            }
        ]
    }
    payload_path = tmp_path / "skill-validation.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8-sig")

    expected = mcp_tools.aitp_v5_skill_build_validation_request(
        str(tmp_path), payload_json=json.dumps(payload)
    )
    exit_code = cli.main(
        [
            "--base",
            str(tmp_path),
            "skill",
            "skill_build_validation_request",
            "--payload-file",
            str(payload_path),
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output == expected
    assert output["result"]["can_execute"] is False
    assert output["result"]["requires_m2_execution"] is False


def test_skill_surface_contract_rejects_nested_trust_and_malformed_pins():
    from brain.v5.skill_surface_contracts import validate_skill_operation_result

    payload = {
        "ok": True,
        "kind": "skill_operation_result",
        "operation": "skill_match_applicable",
        "state_effect": "read_only",
        "writes_records": False,
        "writes_derived_state": False,
        "result": {
            "matches": [
                {
                    "skill_id": "aitp-generated/librpa",
                    "name": "librpa",
                    "semantic_version": "0.1.0",
                    "package_hash": "a" * 64,
                    "proposal_ref": {
                        "record_ref": "not-a-typed-ref",
                        "content_hash": "b" * 64,
                        "revision": 1,
                    },
                    "install_receipt_ref": {
                        "record_ref": "skill_install_receipt:r1",
                        "content_hash": "c" * 64,
                        "revision": 1,
                    },
                    "selector_reasons": {},
                    "confidence": 1.0,
                    "matched": True,
                    "match_source": "derived",
                    "override_ref": {},
                    "orientation_only": True,
                    "can_update_claim_trust": True,
                }
            ],
            "rejected": [],
            "checked_count": 1,
            "orientation_only": True,
            "can_update_claim_trust": False,
            "write_executed": False,
        },
        "truth_source": "typed_records_and_current_project_skill_tree",
        "authorization_guard": "read_only_orientation",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "can_write_evidence": False,
        "can_install_skill": False,
        "can_execute_commands": False,
    }

    result = validate_skill_operation_result(payload)

    assert result.ok is False
    paths = {issue.path for issue in result.issues}
    assert any(path.endswith("proposal_ref.record_ref") for path in paths)
    assert any(path.endswith("can_update_claim_trust") for path in paths)


def test_context_compiler_exposes_only_bounded_installed_skill_cards(
    tmp_path,
    monkeypatch,
):
    from brain.v5.context_compiler import ContextRequest, compile_research_context
    from brain.v5.context_compiler_contracts import validate_context_bundle
    from brain.v5.skill_applicability import SkillApplicabilityRequest
    from brain.v5.workspace import bind_session
    from tests.test_v5_skill_usage import _installed_skill

    ws, proposal_ref, receipt_ref, _run_ref, _validations, preview = _installed_skill(
        tmp_path, monkeypatch
    )
    bind_session(ws, "session-librpa-skill", topic_id="librpa", context_id="condensed-matter")

    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id="session-librpa-skill",
            disclosure_level="startup_orientation",
            skill_request=SkillApplicabilityRequest(
                software=("librpa",),
                tasks=("chi0",),
                environments=("slurm",),
                topic_ids=("librpa",),
            ),
            max_tokens=320,
            max_bytes=1800,
        ),
    )

    assert len(bundle.applicable_skills) == 1
    card = bundle.applicable_skills[0]
    assert set(card) == {
        "skill_id",
        "name",
        "semantic_version",
        "package_hash",
        "proposal_ref",
        "install_receipt_ref",
        "match_source",
        "confidence",
        "expand_operation",
        "use_operation",
    }
    assert card["name"] == preview.name
    assert card["proposal_ref"] == asdict(proposal_ref)
    assert card["install_receipt_ref"] == asdict(receipt_ref)
    assert card["expand_operation"] == "skill_match_applicable"
    assert card["use_operation"] == "skill_record_usage"
    assert "ordered_steps" not in json.dumps(card)
    assert "validation_commands" not in json.dumps(card)
    assert "patch_body" not in json.dumps(card)
    assert bundle.byte_count <= bundle.max_bytes
    assert bundle.estimated_tokens <= bundle.max_tokens
    assert validate_context_bundle(bundle) == ()

    without_request = compile_research_context(
        ws,
        ContextRequest(
            session_id="session-librpa-skill",
            disclosure_level="startup_orientation",
            max_tokens=320,
            max_bytes=1800,
        ),
    )
    assert without_request.applicable_skills == ()


def test_skill_facade_rejects_invalid_json_payload():
    from brain.v5.skill_facade import decode_skill_payload

    with pytest.raises(ValueError, match="valid JSON"):
        decode_skill_payload("{")
