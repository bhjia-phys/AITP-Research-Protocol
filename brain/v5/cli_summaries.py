"""CLI parser and dispatch helpers for v5 summary surfaces."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.replay import write_workspace_replay_packet
from brain.v5.summaries import read_summary_orientation, write_session_summary, write_workspace_summary


def add_summary_parser(subparsers) -> None:
    summary = subparsers.add_parser("summary")
    commands = summary.add_subparsers(dest="summary_command", required=True)
    commands.add_parser("session").add_argument("session_id")
    commands.add_parser("orientation").add_argument("session_id")
    commands.add_parser("workspace")
    commands.add_parser("replay")


def dispatch_summary_command(args, ws) -> dict:
    if args.summary_command == "session":
        bundle = write_session_summary(ws, args.session_id)
        return {"ok": True, **require_valid_public_surface("session_summary_bundle", asdict(bundle))}
    if args.summary_command == "orientation":
        return {"ok": True, **require_valid_public_surface("summary_orientation", read_summary_orientation(ws, args.session_id))}
    if args.summary_command == "workspace":
        bundle = write_workspace_summary(ws)
        return {"ok": True, **require_valid_public_surface("workspace_summary_bundle", asdict(bundle))}
    if args.summary_command == "replay":
        bundle = write_workspace_replay_packet(ws)
        return {"ok": True, **require_valid_public_surface("workspace_replay_packet", asdict(bundle))}
    raise ValueError(f"unknown summary command: {args.summary_command}")
