"""Canonical runtime entrypoint names for AITP v5 adapters."""

from __future__ import annotations

import io
from copy import deepcopy
from contextlib import redirect_stderr
from typing import Any

_RUNTIME_ENTRYPOINTS = {
    "public_surfaces": {
        "cli": "aitp-v5 adapter public-surfaces",
        "mcp": "aitp_v5_describe_public_surfaces",
        "surface": "public_surface_contracts",
    },
    "adapter_registry": {
        "cli": "aitp-v5 adapter registry",
        "mcp": "aitp_v5_get_adapter_protocol_registry",
        "surface": "adapter_protocol_registry",
    },
    "adapter_packet": {
        "cli": "aitp-v5 adapter packet <runtime> <session-id>",
        "mcp": "aitp_v5_get_adapter_packet",
        "surface": "adapter_packet",
    },
    "execution_brief": {
        "cli": "aitp-v5 brief <session-id>",
        "mcp": "aitp_v5_get_execution_brief",
        "surface": "execution_brief",
    },
    "record_code_state": {
        "cli": "aitp-v5 code state record <args>",
        "mcp": "aitp_v5_record_code_state",
        "surface": "code_state_record",
    },
    "record_evidence": {
        "cli": "aitp-v5 evidence record <args>",
        "mcp": "aitp_v5_record_evidence",
        "surface": "evidence_record",
    },
    "register_tool_recipe": {
        "cli": "aitp-v5 tool recipe register <args>",
        "mcp": "aitp_v5_register_tool_recipe",
        "surface": "tool_recipe_record",
    },
    "record_tool_run": {
        "cli": "aitp-v5 tool run record <args>",
        "mcp": "aitp_v5_record_tool_run",
        "surface": "tool_run_record",
    },
    "execute_tool": {
        "cli": "aitp-v5 tool execute <args>",
        "mcp": "aitp_v5_execute_tool",
        "surface": "tool_run_record",
    },
    "list_tool_executors": {
        "cli": "aitp-v5 tool executors",
        "mcp": "aitp_v5_list_tool_executors",
        "surface": "tool_executor_catalog",
    },
    "list_knowledge_connectors": {
        "cli": "aitp-v5 knowledge connectors",
        "mcp": "aitp_v5_list_knowledge_connectors",
        "surface": "knowledge_connector_catalog",
    },
    "record_reference_location": {
        "cli": "aitp-v5 reference location record <args>",
        "mcp": "aitp_v5_record_reference_location",
        "surface": "reference_location_record",
    },
    "summary_orientation": {
        "cli": "aitp-v5 summary orientation <session-id>",
        "mcp": "aitp_v5_read_summary_orientation",
        "surface": "summary_orientation",
    },
    "session_summary": {
        "cli": "aitp-v5 summary session <session-id>",
        "mcp": "aitp_v5_write_session_summary",
        "surface": "session_summary_bundle",
    },
    "trust_preflight": {
        "cli": "aitp-v5 trust preflight <args>",
        "mcp": "aitp_v5_preflight_trust_update",
        "surface": "trust_update_preflight",
    },
    "trust_apply": {
        "cli": "aitp-v5 trust apply <args>",
        "mcp": "aitp_v5_apply_trust_update",
        "surface": "trust_update_apply",
    },
    "record_physics_object": {
        "cli": "aitp-v5 object record <args>",
        "mcp": "aitp_v5_record_physics_object",
        "surface": "physics_object_record",
    },
    "record_object_relation": {
        "cli": "aitp-v5 relation record <args>",
        "mcp": "aitp_v5_record_object_relation",
        "surface": "object_relation_record",
    },
}


def runtime_entrypoints() -> dict[str, dict[str, Any]]:
    """Return canonical CLI/MCP entrypoints advertised to runtime adapters."""

    return deepcopy(_RUNTIME_ENTRYPOINTS)


def runtime_entrypoint_surfaces() -> set[str]:
    """Return the public surfaces named by advertised runtime entrypoints."""

    return {entrypoint["surface"] for entrypoint in _RUNTIME_ENTRYPOINTS.values()}


def validate_runtime_entrypoints(entrypoints: dict[str, dict[str, Any]] | None = None) -> list[str]:
    """Validate that advertised runtime entrypoints resolve to real CLI/MCP targets."""

    payload = runtime_entrypoints() if entrypoints is None else entrypoints
    errors: list[str] = []

    for key, entrypoint in payload.items():
        if not isinstance(entrypoint, dict):
            errors.append(f"{key}: entrypoint must be a mapping")
            continue
        mcp_name = entrypoint.get("mcp")
        cli_command = entrypoint.get("cli")
        surface = entrypoint.get("surface")
        if not isinstance(mcp_name, str) or not mcp_name:
            errors.append(f"{key}.mcp: must be a non-empty string")
        elif not _mcp_entrypoint_exists(mcp_name):
            errors.append(f"{key}.mcp: unknown MCP wrapper {mcp_name!r}")
        if not isinstance(cli_command, str) or not cli_command:
            errors.append(f"{key}.cli: must be a non-empty string")
        elif not _cli_command_parses(cli_command):
            errors.append(f"{key}.cli: command template does not parse")
        if not isinstance(surface, str) or surface not in runtime_entrypoint_surfaces():
            errors.append(f"{key}.surface: unknown public surface {surface!r}")

    return errors


def _mcp_entrypoint_exists(name: str) -> bool:
    from brain.v5 import mcp_tools

    return callable(getattr(mcp_tools, name, None))


def _cli_command_parses(command: str) -> bool:
    from brain.v5.cli import _build_parser

    if not command.startswith("aitp-v5 "):
        return False
    argv = _sample_argv(command.removeprefix("aitp-v5 "))
    parser = _build_parser()
    try:
        with redirect_stderr(io.StringIO()):
            parser.parse_args(argv)
    except SystemExit:
        return False
    return True


def _sample_argv(template: str) -> list[str]:
    argv: list[str] = []
    for token in template.split():
        if token == "<args>":
            argv.extend(_sample_args_for_template(template))
        elif token == "<runtime>":
            argv.append("codex")
        elif token == "<session-id>":
            argv.append("s1")
        else:
            argv.append(token)
    return argv


def _sample_args_for_template(template: str) -> list[str]:
    if template.startswith("trust "):
        return [
            "change_claim_confidence",
            "--session",
            "s1",
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
        ]
    if template.startswith("code state record"):
        return [
            "--repo-id",
            "librpa",
            "--upstream-remote",
            "origin",
            "--upstream-branch",
            "master",
            "--upstream-commit",
            "abc123",
            "--local-branch",
            "topic/gw",
            "--worktree-path",
            "D:/worktrees/librpa/gw",
        ]
    if template.startswith("evidence record"):
        return [
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
            "--type",
            "toy_numeric",
            "--status",
            "supports",
            "--summary",
            "Finite-size check.",
        ]
    if template.startswith("tool recipe register"):
        return [
            "recipe-ed",
            "--family",
            "numerical",
            "--name",
            "exact-diagonalization",
            "--purpose",
            "Run an ED check.",
        ]
    if template.startswith("tool run record"):
        return [
            "--recipe",
            "recipe-ed",
            "--family",
            "numerical",
            "--name",
            "exact-diagonalization",
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
        ]
    if template.startswith("tool execute"):
        return [
            "scalar_tolerance_check",
            "--recipe",
            "recipe-ed",
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
            "--inputs-json",
            '{"observed":1,"expected":1,"tolerance":0}',
        ]
    if template.startswith("reference location record"):
        return [
            "--topic",
            "fqhe",
            "--connector",
            "local_pdf",
            "--type",
            "paper_pdf",
            "--uri",
            "file:///papers/fqhe.pdf",
            "--label",
            "FQHE paper PDF",
        ]
    if template.startswith("object record"):
        return [
            "--topic",
            "fqhe",
            "--type",
            "hilbert_sector",
            "--name",
            "N=8 sector",
            "--definition",
            "Finite-size Hilbert sector.",
        ]
    if template.startswith("relation record"):
        return [
            "--topic",
            "fqhe",
            "--type",
            "diagnoses",
            "--subject",
            "object-a",
            "--object",
            "object-b",
            "--statement",
            "A diagnoses B.",
        ]
    return []
