"""File-backed CLI adapter for full-only M3 knowledge operations."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from brain.v5.knowledge_facade import decode_knowledge_payload, invoke_knowledge_operation
from brain.v5.knowledge_surface_contracts import knowledge_operation_specs
from brain.v5.paths import WorkspacePaths


def add_knowledge_parser(sp: argparse._SubParsersAction) -> None:
    parser = sp.choices.get("knowledge")
    if parser is None:
        parser = sp.add_parser("knowledge")
        commands = parser.add_subparsers(dest="knowledge_command", required=True)
    else:
        commands = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
    for operation in knowledge_operation_specs():
        operation_parser = commands.add_parser(operation)
        operation_parser.add_argument("--payload-file", required=True)


def is_knowledge_command(args: argparse.Namespace) -> bool:
    return (
        args.command == "knowledge"
        and getattr(args, "knowledge_command", "") in knowledge_operation_specs()
    )


def dispatch_knowledge_command(args: argparse.Namespace) -> dict[str, Any]:
    payload_json = Path(args.payload_file).read_text(encoding="utf-8-sig")
    return invoke_knowledge_operation(
        WorkspacePaths(Path(args.base).resolve()),
        args.knowledge_command,
        decode_knowledge_payload(payload_json),
    )
