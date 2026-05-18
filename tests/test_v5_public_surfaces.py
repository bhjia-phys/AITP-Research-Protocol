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
