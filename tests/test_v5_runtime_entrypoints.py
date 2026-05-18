from __future__ import annotations


def test_runtime_entrypoint_validation_confirms_advertised_targets_exist():
    from brain.v5.runtime_entrypoints import validate_runtime_entrypoints

    assert validate_runtime_entrypoints() == []


def test_runtime_entrypoint_validation_reports_bad_mcp_and_cli_targets():
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    entrypoints = runtime_entrypoints()
    entrypoints["public_surfaces"]["mcp"] = "aitp_v5_guess_public_surfaces"
    entrypoints["adapter_registry"]["cli"] = "aitp-v5 missing registry"

    errors = validate_runtime_entrypoints(entrypoints)

    assert any("public_surfaces.mcp" in error for error in errors)
    assert any("adapter_registry.cli" in error for error in errors)
