from __future__ import annotations

import json
from dataclasses import asdict

import pytest


_OPERATIONS = {
    "execution_get_record_version": "read_only",
    "execution_assess_scope": "read_only",
    "execution_build_compute_intake": "read_only",
    "execution_resolve_effective_attempt": "read_only",
    "execution_assess_baseline_readiness": "read_only",
    "execution_project_maturity": "read_only",
    "execution_build_formula_code_capsule": "read_only",
    "execution_project_derivation_status": "read_only",
    "execution_request_bound_checkpoint": "kernel_write",
    "execution_decide_bound_checkpoint": "kernel_write",
    "execution_apply_bound_action": "kernel_write",
}


def _workspace(tmp_path):
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "compute", context_id="theory", title="Compute")
    claim = create_claim(
        ws,
        topic_id="compute",
        statement="The execution facade remains exact and trust neutral.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="No execution has been accepted.",
    )
    return ws, claim


def test_execution_facade_registry_is_full_only_and_cli_addressable():
    from brain.v5.capability_registry import capability_specs, compact_mcp_tools
    from brain.v5.execution_surface_contracts import execution_operation_specs

    operation_specs = execution_operation_specs()
    capabilities = capability_specs()

    assert set(operation_specs) == set(_OPERATIONS)
    assert len(compact_mcp_tools()) == 10
    for operation, effect in _OPERATIONS.items():
        contract = operation_specs[operation]
        capability = capabilities[operation]
        assert contract.state_effect == effect
        assert capability.state_effect == effect
        assert capability.compact_visibility == "full"
        assert capability.public_surface == "execution_operation_result"
        assert capability.cli_route == f"aitp-v5 execution {operation} --payload-file <args>"


def test_record_version_and_compute_intake_have_mcp_cli_parity(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_execution import (
        aitp_v5_execution_build_compute_intake,
        aitp_v5_execution_get_record_version,
    )
    from brain.v5.pinned_record_refs import pin_current_record

    ws, claim = _workspace(tmp_path)
    claim_ref = pin_current_record(ws, f"claim:{claim.claim_id}")
    record_payload = json.dumps({"record_ref": asdict(claim_ref)})

    mcp_record = aitp_v5_execution_get_record_version(str(tmp_path), payload_json=record_payload)

    assert mcp_record["operation"] == "execution_get_record_version"
    assert mcp_record["state_effect"] == "read_only"
    assert mcp_record["result"]["pinned_ref"] == asdict(claim_ref)
    assert mcp_record["result"]["record"]["claim_id"] == claim.claim_id
    assert mcp_record["can_update_kernel_state"] is False
    assert mcp_record["can_update_claim_trust"] is False

    intake_payload = {
        "manifest": {
            "schema_version": "aitp.compute_run_intake.v1",
            "collector": {"id": "pytest", "version": "1.0.0"},
            "source": {"uri": "ssh://cluster/runs/42"},
        }
    }
    mcp_intake = aitp_v5_execution_build_compute_intake(
        str(tmp_path),
        payload_json=json.dumps(intake_payload),
    )
    assert mcp_intake["result"]["writes_records"] is False
    assert mcp_intake["result"]["orientation_only"] is True

    payload_path = tmp_path / "record-version.json"
    payload_path.write_text(record_payload, encoding="utf-8")
    assert main([
        "--base",
        str(tmp_path),
        "execution",
        "execution_get_record_version",
        "--payload-file",
        str(payload_path),
    ]) == 0
    cli_record = json.loads(capsys.readouterr().out)
    assert cli_record == mcp_record


def test_execution_surface_contract_rejects_forged_exact_pin():
    from brain.v5.execution_surface_contracts import validate_execution_operation_result

    forged = {
        "ok": True,
        "kind": "execution_operation_result",
        "operation": "execution_get_record_version",
        "state_effect": "read_only",
        "writes_records": False,
        "result": {
            "pinned_ref": {"record_ref": "claim:x", "content_hash": "", "revision": 1},
            "record": {},
            "body": "",
            "version_source": "current",
        },
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }

    validation = validate_execution_operation_result(forged)

    assert validation.ok is False
    assert any(issue.path.endswith("pinned_ref.content_hash") for issue in validation.issues)


def test_execution_surface_contract_rejects_forged_provenance_metadata():
    from brain.v5.execution_surface_contracts import validate_execution_operation_result

    forged = {
        "ok": True,
        "kind": "execution_operation_result",
        "operation": "execution_get_record_version",
        "state_effect": "read_only",
        "writes_records": False,
        "result": {
            "pinned_ref": {},
            "record": {},
            "body": "",
            "version_source": "current",
        },
        "truth_source": "chat_summary",
        "summary_inputs_trusted": True,
        "orientation_only": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }

    validation = validate_execution_operation_result(forged)

    assert validation.ok is False
    assert any(issue.path.endswith("truth_source") for issue in validation.issues)
    assert any(issue.path.endswith("summary_inputs_trusted") for issue in validation.issues)
    assert any(issue.path.endswith("orientation_only") for issue in validation.issues)


def test_detached_intake_preserves_its_truth_source(tmp_path):
    from brain.v5.mcp_execution import aitp_v5_execution_build_compute_intake

    _workspace(tmp_path)
    result = aitp_v5_execution_build_compute_intake(
        str(tmp_path),
        payload_json=json.dumps({
            "manifest": {
                "schema_version": "aitp.compute_run_intake.v1",
                "collector": {"id": "pytest", "version": "1.0.0"},
                "source": {"uri": "ssh://cluster/runs/42"},
            }
        }),
    )

    assert result["truth_source"] == "detached_collector_manifest"
    assert result["writes_records"] is False


def test_scope_contract_preserves_requires_revalidation():
    from brain.v5.execution_surface_contracts import validate_execution_operation_result

    pin = {"record_ref": "claim:foreign", "content_hash": "a" * 64, "revision": 1}
    payload = {
        "ok": True,
        "kind": "execution_operation_result",
        "operation": "execution_assess_scope",
        "state_effect": "read_only",
        "writes_records": False,
        "result": {
            "decision": "requires_revalidation",
            "dependency_refs": [pin],
            "reasons": ["target-side review is required"],
        },
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }

    assert validate_execution_operation_result(payload).ok is True


def test_formula_and_derivation_contracts_reject_cross_bound_pins():
    from brain.v5.execution_surface_contracts import validate_execution_operation_result

    relation = {"record_ref": "object_relation:r1", "content_hash": "a" * 64, "revision": 1}
    other = {"record_ref": "object_relation:r2", "content_hash": "b" * 64, "revision": 1}
    formula = {
        "ok": True,
        "kind": "execution_operation_result",
        "operation": "execution_build_formula_code_capsule",
        "state_effect": "read_only",
        "writes_records": False,
        "result": {
            "relation_ref": relation,
            "exact_expansion_refs": ["object_relation:r2"],
            "exact_expansion_pins": [other],
            "ready_for_edit": True,
        },
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    chain = {
        **formula,
        "operation": "execution_project_derivation_status",
        "result": {
            "chain_ref": "derivation_chain:b",
            "requested_chain_ref": {
                "record_ref": "derivation_chain:a",
                "content_hash": "c" * 64,
                "revision": 1,
            },
            "structurally_closed": False,
            "reviewed": False,
            "validated": False,
        },
    }

    assert validate_execution_operation_result(formula).ok is False
    assert validate_execution_operation_result(chain).ok is False
