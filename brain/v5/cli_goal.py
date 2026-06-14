"""CLI handlers for goal continuation audit packets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from brain.v5.goal_continuation import (
    empty_goal_continuation_packet,
    list_goal_continuations,
    read_latest_goal_continuation,
    write_goal_continuation,
)
from brain.v5.public_surfaces import require_valid_public_surface


def add_goal_parser(sp) -> None:
    goal = sp.add_parser("goal")
    gs = goal.add_subparsers(dest="goal_command", required=True)

    write_p = gs.add_parser("write")
    write_p.add_argument("--objective", required=True)
    write_p.add_argument("--changed-files", default="")
    write_p.add_argument("--changed-file", action="append", default=[], dest="changed_file_items")
    write_p.add_argument("--changed-file-stats-json", default="[]")
    write_p.add_argument("--changed-file-stats-json-file", default="")
    write_p.add_argument("--tests-run", default="")
    write_p.add_argument("--test-run", action="append", default=[], dest="test_run_items")
    write_p.add_argument("--tests-passed", default=None, dest="tests_passed_raw")
    write_p.add_argument("--smoke-commands", default="")
    write_p.add_argument("--smoke-command", action="append", default=[], dest="smoke_command_items")
    write_p.add_argument("--smoke-passed", default=None, dest="smoke_passed_raw")
    write_p.add_argument("--readiness-json", default="{}")
    write_p.add_argument("--readiness-json-file", default="")
    write_p.add_argument("--next-actions", default="")
    write_p.add_argument("--next-action", action="append", default=[], dest="next_action_items")
    write_p.add_argument("--trust-boundary", default="")
    write_p.add_argument("--blocking-backlog", default="")
    write_p.add_argument("--blocking-backlog-item", action="append", default=[], dest="blocking_backlog_items")
    write_p.add_argument("--notes", default="")
    write_p.add_argument("--session-id", default="")
    write_p.add_argument("--commit-ref", default="")
    write_p.add_argument("--commit-range", default="")
    write_p.add_argument("--commits-json", default="[]")
    write_p.add_argument("--commits-json-file", default="")
    write_p.add_argument("--audit-command", action="append", default=[], dest="audit_command_items")

    gs.add_parser("latest")
    gs.add_parser("list")


def _csv(value: str) -> list[str]:
    return [s.strip() for s in value.split(",") if s.strip()]


def _list_arg(repeated: list[str], legacy_csv: str) -> list[str]:
    if repeated:
        return [s for s in repeated if s]
    return _csv(legacy_csv)


def _bool_or_none(value: str | None) -> bool | None:
    if value is None:
        return None
    return value.lower() in ("true", "1", "yes")


def _json_arg(inline_value: str, file_value: str, default: str) -> Any:
    raw = default
    if file_value:
        raw = Path(file_value).read_text(encoding="utf-8-sig")
    elif inline_value:
        raw = inline_value
    return json.loads(raw)


def dispatch_goal_command(args, ws) -> dict:
    if args.goal_command == "write":
        readiness = {}
        readiness = _json_arg(args.readiness_json, args.readiness_json_file, "{}")
        packet = write_goal_continuation(
            ws,
            objective=args.objective,
            changed_files=_list_arg(args.changed_file_items, args.changed_files),
            changed_file_stats=_json_arg(
                args.changed_file_stats_json,
                args.changed_file_stats_json_file,
                "[]",
            ),
            tests_run=_list_arg(args.test_run_items, args.tests_run),
            tests_passed=_bool_or_none(args.tests_passed_raw),
            smoke_commands=_list_arg(args.smoke_command_items, args.smoke_commands),
            smoke_passed=_bool_or_none(args.smoke_passed_raw),
            readiness_outcome=readiness or None,
            next_actions=_list_arg(args.next_action_items, args.next_actions),
            trust_boundary=args.trust_boundary,
            blocking_backlog=_list_arg(args.blocking_backlog_items, args.blocking_backlog),
            notes=args.notes,
            session_id=args.session_id,
            commit_ref=args.commit_ref,
            commit_range=args.commit_range,
            commits=_json_arg(args.commits_json, args.commits_json_file, "[]"),
            audit_commands=args.audit_command_items,
        )
        return require_valid_public_surface("goal_continuation_packet", packet)
    if args.goal_command == "latest":
        result = read_latest_goal_continuation(ws)
        if result is None:
            return require_valid_public_surface("goal_continuation_packet", empty_goal_continuation_packet())
        return require_valid_public_surface("goal_continuation_packet", result)
    if args.goal_command == "list":
        packets = list_goal_continuations(ws)
        result = {
            "kind": "goal_continuation_list",
            "count": len(packets),
            "packet_ids": [p.get("packet_id", "") for p in packets],
            "latest_objectives": [
                {"packet_id": p.get("packet_id", ""), "objective": (p.get("objective") or "")[:120]}
                for p in packets[-5:]
            ],
        }
        return require_valid_public_surface("goal_continuation_list", result)
    raise SystemExit(f"unsupported goal command: {args.goal_command}")
