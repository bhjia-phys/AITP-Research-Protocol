from __future__ import annotations


def test_runtime_entrypoint_validation_confirms_advertised_targets_exist():
    from brain.v5.runtime_entrypoints import validate_runtime_entrypoints

    assert validate_runtime_entrypoints() == []


def test_runtime_entrypoints_advertise_typed_write_surfaces():
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    entrypoints = runtime_entrypoints()

    assert entrypoints["record_evidence"]["surface"] == "evidence_record"
    assert entrypoints["record_code_state"]["surface"] == "code_state_record"
    assert entrypoints["register_tool_recipe"]["surface"] == "tool_recipe_record"
    assert entrypoints["record_tool_run"]["surface"] == "tool_run_record"
    assert entrypoints["execute_tool"]["surface"] == "tool_run_record"
    assert entrypoints["record_evidence"]["mcp"] == "aitp_v5_record_evidence"
    assert entrypoints["record_code_state"]["mcp"] == "aitp_v5_record_code_state"
    assert entrypoints["register_tool_recipe"]["mcp"] == "aitp_v5_register_tool_recipe"
    assert entrypoints["record_tool_run"]["mcp"] == "aitp_v5_record_tool_run"
    assert entrypoints["execute_tool"]["mcp"] == "aitp_v5_execute_tool"


def test_runtime_entrypoint_validation_reports_bad_mcp_and_cli_targets():
    from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

    entrypoints = runtime_entrypoints()
    entrypoints["public_surfaces"]["mcp"] = "aitp_v5_guess_public_surfaces"
    entrypoints["adapter_registry"]["cli"] = "aitp-v5 missing registry"

    errors = validate_runtime_entrypoints(entrypoints)

    assert any("public_surfaces.mcp" in error for error in errors)
    assert any("adapter_registry.cli" in error for error in errors)
