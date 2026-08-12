from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .core import (
    AITPError,
    adopt_workspace,
    build_inventory,
    check_workspace,
    enter_workspace,
    init_workspace,
    list_workspace,
    prepare_entry,
    prepare_note,
    save_entry,
    save_note,
    show_entry,
)
from .query import _stored_time, _truncate


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--json", action="store_true")


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        print(f"{key}: {_frontmatter_value(value)}")


def _emit_list(payload: dict[str, Any], as_json: bool) -> None:
    if as_json: return _emit(payload, True)
    for item in payload["entries"]:
        status = item["status"] + (" legacy-derived" if item["legacy_derived"] else "")
        print(f"{item['created_at']} {item['id']} {item['kind']} {status} {_truncate(item['summary'])}")
    for warning in payload["warnings"]:
        print(f"warning[{warning['code']}]: {warning['path']}: {warning['message']}", file=sys.stderr)


def _frontmatter_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else str(value)


def _emit_show(payload: dict[str, Any], as_json: bool) -> None:
    if as_json: return _emit(payload, True)
    for key in ("id", "status", "source"):
        print(f"{key}: {payload[key]}")
    print(f"legacy_derived: {str(payload['legacy_derived']).lower()}")
    if payload["status"] == "malformed":
        warning = payload["warning"]
        print(f"warning[{warning['code']}]: {warning['message']}")
        print()
        print(payload["body"], end="")
        return
    for key, value in payload["frontmatter"].items():
        print(f"{key}: {_frontmatter_value(value)}")
    print()
    print(payload["body"], end="")


def _emit_check(payload: dict[str, Any], as_json: bool) -> None:
    if as_json: return _emit(payload, True)
    for finding in payload["findings"]:
        print(f"{finding['level']}[{finding['code']}]: {finding['path']}: {finding['message']}")
    print(f"check: {payload['counts']['errors']} error(s), {payload['counts']['warnings']} warning(s)")


def _handoff_review(payload: dict[str, Any]) -> bool:
    action = payload["next_action"]
    if not action.get("entry_id"):
        return False
    handoff_time = _stored_time(action.get("created_at"))
    return handoff_time is not None and any(
        (time := _stored_time(failure.get("created_at"))) is not None and time > handoff_time
        for failure in payload["unresolved_failures"])


def _emit_enter(payload: dict[str, Any], as_json: bool) -> None:
    if as_json: return _emit(payload, True)
    topic = payload["topic"]
    print(f"topic: {topic['id']} — {topic['title']}")
    print(f"memory_status: {payload['memory_status']}")
    print("goal_status: not_established" if topic["goal"]["text"] == "Not established yet" else f"goal: {_truncate(topic['goal']['text'], 120)}")
    counts = payload["counts"]
    print(f"recent_entries: {len(payload['recent_entries'])} of {counts['active']} active ({counts['omitted_active']} omitted)")
    for item in payload["recent_entries"]:
        print(f"  {item['created_at']} {item['id']} {item['kind']} {_truncate(item['summary'])}")
    print(f"unresolved_failures: {len(payload['unresolved_failures'])}")
    action = payload["next_action"]
    if action.get("entry_id"):
        print(f"next_action: {_truncate(action['text'])} [{action['entry_id']} @ {action['created_at']} {action['authority']}]")
    else:
        print("next_action: not_established")
    if _handoff_review(payload):
        print("handoff_status: review")
    latest = payload["latest_working_note"]
    latest_text = f"{latest['id']} @ {latest['created_at']}" if latest else "(none)"
    age = counts["active_newer_than_latest_working_note"]
    print(f"recent_notes: {len(payload['recent_notes'])}; latest_working_note: {latest_text}; active_newer: {age if age is not None else 'unknown'}")
    if payload["warnings"]:
        print(f"warnings: {len(payload['warnings'])} (run \"aitp check\" for details)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aitp")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="initialize a blank research repository")
    init.add_argument("--topic", required=True)
    init.add_argument("--title", required=True)
    init.add_argument("--adopt", action="store_true")
    init.add_argument("--dry-run", action="store_true")

    enter = commands.add_parser("enter", help="return grounded recorded research state")
    enter.add_argument("--recent", type=_positive_int, default=20)

    listing = commands.add_parser(
        "list", help="list canonical Entries with optional --kind and --since filters"
    )
    listing.add_argument(
        "--kind",
        help="only Entries of this kind (observation, result, failure, decision, source, code_change, run, closeout)",
    )
    listing.add_argument(
        "--since",
        help="only Entries recorded at or after this ISO date/timestamp (inclusive)",
    )

    show = commands.add_parser("show", help="show one Entry's complete frontmatter and body")
    show.add_argument("entry_id")

    check = commands.add_parser("check", help="validate the whole store read-only and report findings (exit 0 clean, 1 findings, 2 cannot run)")

    inventory = commands.add_parser("inventory", help="scan a legacy tree and write a hash manifest")
    inventory.add_argument("path")
    inventory.add_argument("--name", required=True)

    record = commands.add_parser("record", help="prepare or save an Entry")
    record_commands = record.add_subparsers(dest="record_command", required=True)
    record_prepare = record_commands.add_parser(
        "prepare", help="prepare an Entry draft from a kind template"
    )
    record_prepare.add_argument("--kind", required=True)
    record_prepare.add_argument("--authority", default="agent")
    record_prepare.add_argument("--created-by", default="agent:unknown")
    record_prepare.add_argument("--idempotency-key")
    record_save = record_commands.add_parser(
        "save", help="validate and save a prepared Entry draft"
    )
    record_save.add_argument("draft")

    note = commands.add_parser("note", help="prepare or save a Note")
    note_commands = note.add_subparsers(dest="note_command", required=True)
    note_prepare = note_commands.add_parser(
        "prepare", help="prepare a Note draft from a mode template"
    )
    note_prepare.add_argument("--mode", choices=("working", "theory"), required=True)
    note_prepare.add_argument("--title", required=True)
    note_prepare.add_argument("--created-by", default="agent:unknown")
    note_save = note_commands.add_parser(
        "save", help="validate and save a prepared Note draft"
    )
    note_save.add_argument("draft")
    for command_parser in (init, enter, listing, show, check, inventory, record_prepare, record_save, note_prepare, note_save):
        _add_common_options(command_parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            factory = adopt_workspace if args.adopt else init_workspace
            payload = factory(
                args.cwd,
                args.topic,
                args.title,
                dry_run=args.dry_run,
            )
        elif args.command == "enter":
            payload = enter_workspace(args.cwd, recent=args.recent)
        elif args.command == "list":
            payload = list_workspace(args.cwd, kind=args.kind, since=args.since)
        elif args.command == "show":
            payload = show_entry(args.cwd, args.entry_id)
        elif args.command == "check":
            payload = check_workspace(args.cwd)
        elif args.command == "inventory":
            payload = build_inventory(args.cwd, args.path, args.name)
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
        as_json = getattr(args, "json", False)
        renderer = {"list": _emit_list, "show": _emit_show, "enter": _emit_enter,
                    "check": _emit_check}.get(args.command, _emit)
        renderer(payload, as_json)
        if args.command == "check" and payload["status"] == "findings":
            return 1
        return 0
    except AITPError as exc:
        payload = {"status": "error", "code": exc.code, "message": str(exc)}
        if getattr(args, "json", False):
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"error[{exc.code}]: {exc}", file=sys.stderr)
        return 2
