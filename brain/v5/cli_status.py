"""CLI handlers for topic status surfaces."""

from __future__ import annotations

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.topic_status import write_topic_status_surfaces


def add_status_parser(sp) -> None:
    status = sp.add_parser("status"); ss = status.add_subparsers(dest="status_command", required=True)
    topic = ss.add_parser("topic")
    topic.add_argument("session_id")


def dispatch_status_command(args, ws) -> dict:
    if args.status_command == "topic":
        return require_valid_public_surface(
            "topic_status_bundle",
            write_topic_status_surfaces(ws, session_id=args.session_id),
        )
    raise SystemExit(f"unsupported status command: {args.status_command}")
