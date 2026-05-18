from __future__ import annotations


def test_public_surface_registry_names_all_runtime_facing_payloads():
    from brain.v5.public_surfaces import public_surface_names

    assert set(public_surface_names()) == {
        "adapter_packet",
        "adapter_protocol_registry",
        "execution_brief",
        "session_summary_bundle",
        "summary_orientation",
        "trust_update_apply",
        "trust_update_preflight",
    }


def test_public_surface_validator_accepts_valid_adapter_registry():
    from brain.v5.adapter_protocols import adapter_protocol_registry
    from brain.v5.public_surfaces import require_valid_public_surface

    registry = adapter_protocol_registry()

    assert require_valid_public_surface("adapter_protocol_registry", registry) == registry


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
