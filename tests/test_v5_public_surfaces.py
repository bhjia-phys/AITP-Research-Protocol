from __future__ import annotations


def test_public_surface_registry_names_all_runtime_facing_payloads():
    from brain.v5.public_surfaces import public_surface_names

    assert set(public_surface_names()) == {
        "adapter_packet",
        "adapter_protocol_registry",
        "code_state_record",
        "evidence_record",
        "execution_brief",
        "knowledge_connector_catalog",
        "reference_location_record",
        "session_summary_bundle",
        "summary_orientation",
        "tool_executor_catalog",
        "tool_recipe_record",
        "tool_run_record",
        "trust_update_apply",
        "trust_update_preflight",
    }


def test_public_surface_validator_accepts_valid_adapter_registry():
    from brain.v5.adapter_protocols import adapter_protocol_registry
    from brain.v5.public_surfaces import require_valid_public_surface

    registry = adapter_protocol_registry()

    assert require_valid_public_surface("adapter_protocol_registry", registry) == registry


def test_public_surface_validator_accepts_tool_executor_catalog():
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.tool_executors import describe_tool_executors

    catalog = describe_tool_executors()

    assert require_valid_public_surface("tool_executor_catalog", catalog) == catalog


def test_public_surface_validator_accepts_typed_write_records():
    from brain.v5.public_surfaces import require_valid_public_surface

    evidence = {
        "ok": True,
        "kind": "evidence",
        "evidence_id": "evidence-fqhe-counting",
        "topic_id": "fqhe",
        "claim_id": "claim-fqhe-counting",
        "evidence_type": "toy_numeric",
        "status": "supports",
        "summary": "Finite-size counting check.",
        "supports_outputs": ["minimal_check"],
        "source_refs": ["paper:example"],
        "tool_run_ids": ["tool-run-ed"],
        "artifact_ids": ["artifact-spectrum"],
    }
    tool_run = {
        "ok": True,
        "kind": "tool_run",
        "run_id": "tool-run-ed",
        "recipe_id": "recipe-ed",
        "tool_family": "numerical",
        "tool_name": "exact-diagonalization",
        "topic_id": "fqhe",
        "claim_id": "claim-fqhe-counting",
        "inputs": {"system_size": 10},
        "outputs": {"counting_matches": True},
        "environment": {"python": "3.12"},
        "evidence_status": "supports",
        "code_state_ids": ["code-state-ed"],
        "artifact_ids": ["artifact-spectrum"],
        "source_refs": ["paper:example"],
    }
    code_state = {
        "ok": True,
        "kind": "code_state",
        "code_state_id": "code-state-librpa-abc123",
        "repo_id": "librpa",
        "upstream_remote": "origin",
        "upstream_branch": "master",
        "upstream_commit": "abc123",
        "local_branch": "topic/gw",
        "worktree_path": "D:/worktrees/librpa/gw",
        "dirty": False,
        "patch_id": "",
        "diff_hash": "",
        "build_config": {},
        "runtime_environment": {},
        "linked_records": {"claim_id": "claim-gw"},
        "known_divergence": "",
    }
    recipe = {
        "ok": True,
        "kind": "tool_recipe",
        "recipe_id": "recipe-librpa-gw",
        "tool_family": "domain",
        "tool_name": "librpa-gw-runner",
        "purpose": "Run a LibRPA GW benchmark.",
        "required_inputs": ["code_state_id"],
        "expected_outputs": ["benchmark_consistency"],
        "invariants": ["same upstream commit"],
    }

    assert require_valid_public_surface("evidence_record", evidence) == evidence
    assert require_valid_public_surface("tool_run_record", tool_run) == tool_run
    assert require_valid_public_surface("code_state_record", code_state) == code_state
    assert require_valid_public_surface("tool_recipe_record", recipe) == recipe


def test_adapter_registry_exposes_public_surface_contract_names():
    from brain.v5.adapter_protocols import adapter_protocol_registry
    from brain.v5.public_surfaces import public_surface_names

    assert adapter_protocol_registry()["public_surface_contracts"] == list(public_surface_names())


def test_public_surface_validator_ref_names_shared_helper():
    from brain.v5.public_surfaces import public_surface_validator_ref

    assert public_surface_validator_ref() == "brain.v5.public_surfaces.require_valid_public_surface"


def test_adapter_registry_exposes_public_surface_validator_ref():
    from brain.v5.adapter_protocols import adapter_protocol_registry
    from brain.v5.public_surfaces import public_surface_validator_ref

    assert adapter_protocol_registry()["public_surface_validator"] == public_surface_validator_ref()


def test_describe_public_surfaces_returns_auditable_contract_payload():
    from brain.v5.public_surfaces import (
        describe_public_surfaces,
        public_surface_names,
        public_surface_validator_ref,
    )

    payload = describe_public_surfaces()

    assert payload["kind"] == "public_surface_contracts"
    assert payload["validator"] == public_surface_validator_ref()
    assert payload["surface_names"] == list(public_surface_names())
    assert payload["truth_source"] == "contract_registry"
    assert payload["summary_inputs_trusted"] is False
    assert {surface["name"] for surface in payload["surfaces"]} == set(public_surface_names())
    for surface in payload["surfaces"]:
        assert surface["validator"] == public_surface_validator_ref()
        assert surface["purpose"]


def test_runtime_entrypoint_surfaces_close_over_public_surface_contracts():
    from brain.v5.public_surfaces import public_surface_names
    from brain.v5.runtime_entrypoints import runtime_entrypoint_surfaces, runtime_entrypoints

    surfaces = runtime_entrypoint_surfaces()

    assert surfaces == set(public_surface_names()) | {"public_surface_contracts"}
    for entrypoint in runtime_entrypoints().values():
        assert entrypoint["surface"] in surfaces


def test_public_surface_validator_rejects_invalid_named_surface():
    import pytest

    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface

    with pytest.raises(ContractError):
        require_valid_public_surface("summary_orientation", {"kind": "summary_orientation"})


def test_public_surface_validator_rejects_unknown_surface():
    import pytest

    from brain.v5.public_surfaces import require_valid_public_surface

    with pytest.raises(ValueError, match="unknown public surface"):
        require_valid_public_surface("draft_notes", {})
