"""File-backed CLI adapter for full-only M4 Skill operations."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from brain.v5.paths import WorkspacePaths
from brain.v5.skill_facade import decode_skill_payload, invoke_skill_operation
from brain.v5.skill_surface_contracts import skill_operation_specs


def add_skill_parser(sp: argparse._SubParsersAction) -> None:
    parser = sp.choices.get("skill")
    if parser is None:
        parser = sp.add_parser("skill")
        commands = parser.add_subparsers(dest="skill_command", required=True)
    else:
        commands = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
    for operation in skill_operation_specs():
        operation_parser = commands.add_parser(operation)
        operation_parser.add_argument("--payload-file", required=True)


def is_skill_command(args: argparse.Namespace) -> bool:
    return (
        args.command == "skill"
        and getattr(args, "skill_command", "") in skill_operation_specs()
    )


def dispatch_skill_command(args: argparse.Namespace) -> dict[str, Any]:
    payload_json = Path(args.payload_file).read_text(encoding="utf-8-sig")
    return invoke_skill_operation(
        WorkspacePaths(Path(args.base).resolve()),
        args.skill_command,
        decode_skill_payload(payload_json),
    )
