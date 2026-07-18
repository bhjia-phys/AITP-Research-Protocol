"""Canonical runtime entrypoint names for AITP v5 adapters."""

from __future__ import annotations

import io
from copy import deepcopy
from contextlib import redirect_stderr
from typing import Any

from brain.v5.runtime_entrypoint_catalog import RUNTIME_ENTRYPOINTS, sample_args_for_template


def runtime_entrypoints() -> dict[str, dict[str, Any]]:
    """Return canonical CLI/MCP entrypoints advertised to runtime adapters."""

    return deepcopy(RUNTIME_ENTRYPOINTS)


def runtime_entrypoint_surfaces() -> set[str]:
    """Return the public surfaces named by advertised runtime entrypoints."""

    return {entrypoint["surface"] for entrypoint in RUNTIME_ENTRYPOINTS.values()}


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
            argv.extend(sample_args_for_template(template))
        elif token == "<runtime>":
            argv.append("codex")
        elif token == "<session-id>":
            argv.append("s1")
        elif token == "<mode>":
            argv.append("dynamic")
        else:
            argv.append(token)
    return argv
