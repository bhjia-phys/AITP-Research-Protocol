from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .core import (
    AITPError,
    enter_workspace,
    init_workspace,
    prepare_entry,
    prepare_note,
    save_entry,
    save_note,
)


def _emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            print(f"{key}: {json.dumps(value, ensure_ascii=False)}")
        else:
            print(f"{key}: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aitp")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="initialize a blank research repository")
    init.add_argument("--cwd", default=".")
    init.add_argument("--topic", required=True)
    init.add_argument("--title", required=True)
    init.add_argument("--dry-run", action="store_true")
    init.add_argument("--json", action="store_true")

    enter = commands.add_parser("enter", help="return grounded recorded research state")
    enter.add_argument("--cwd", default=".")
    enter.add_argument("--recent", type=int, default=20)
    enter.add_argument("--json", action="store_true")

    record = commands.add_parser("record", help="prepare or save an Entry")
    record_commands = record.add_subparsers(dest="record_command", required=True)
    record_prepare = record_commands.add_parser("prepare")
    record_prepare.add_argument("--cwd", default=".")
    record_prepare.add_argument("--kind", required=True)
    record_prepare.add_argument("--authority", default="agent")
    record_prepare.add_argument("--created-by", default="agent:unknown")
    record_prepare.add_argument("--idempotency-key")
    record_prepare.add_argument("--json", action="store_true")
    record_save = record_commands.add_parser("save")
    record_save.add_argument("draft")
    record_save.add_argument("--cwd", default=".")
    record_save.add_argument("--json", action="store_true")

    note = commands.add_parser("note", help="prepare or save a Note")
    note_commands = note.add_subparsers(dest="note_command", required=True)
    note_prepare = note_commands.add_parser("prepare")
    note_prepare.add_argument("--cwd", default=".")
    note_prepare.add_argument("--mode", choices=("working", "theory"), required=True)
    note_prepare.add_argument("--title", required=True)
    note_prepare.add_argument("--created-by", default="agent:unknown")
    note_prepare.add_argument("--json", action="store_true")
    note_save = note_commands.add_parser("save")
    note_save.add_argument("draft")
    note_save.add_argument("--cwd", default=".")
    note_save.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            payload = init_workspace(
                args.cwd,
                args.topic,
                args.title,
                dry_run=args.dry_run,
            )
        elif args.command == "enter":
            payload = enter_workspace(args.cwd, recent=args.recent)
        elif args.command == "record" and args.record_command == "prepare":
            payload = prepare_entry(
                args.cwd,
                args.kind.replace("-", "_"),
                args.authority,
                created_by=args.created_by,
                idempotency_key=args.idempotency_key,
            )
        elif args.command == "record" and args.record_command == "save":
            payload = save_entry(args.cwd, args.draft)
        elif args.command == "note" and args.note_command == "prepare":
            payload = prepare_note(
                args.cwd,
                args.mode,
                args.title,
                created_by=args.created_by,
            )
        elif args.command == "note" and args.note_command == "save":
            payload = save_note(args.cwd, args.draft)
        else:
            parser.error("unsupported command")
            return 2
        _emit(payload, getattr(args, "json", False))
        return 0
    except AITPError as exc:
        payload = {"status": "error", "code": exc.code, "message": str(exc)}
        if getattr(args, "json", False):
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"error[{exc.code}]: {exc}", file=sys.stderr)
        return 2
