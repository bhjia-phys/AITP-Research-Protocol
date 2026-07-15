"""File-backed CLI adapter for the full M2 execution facade."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from brain.v5.execution_surface_contracts import execution_operation_specs
from brain.v5.mcp_execution import invoke_execution_operation


def add_execution_parser(sp: argparse._SubParsersAction) -> None:
    parser = sp.add_parser("execution")
    parser.add_argument("execution_operation", choices=tuple(execution_operation_specs()))
    parser.add_argument("--payload-file", required=True)


def is_execution_command(args: argparse.Namespace) -> bool:
    return args.command == "execution"


def dispatch_execution_command(args: argparse.Namespace) -> dict[str, Any]:
    payload_json = Path(args.payload_file).read_text(encoding="utf-8-sig")
    return invoke_execution_operation(
        str(args.base),
        args.execution_operation,
        payload_json,
    )
