"""CLI handlers for stable final-output profiles."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.output_stability import record_final_output_profile
from brain.v5.public_surfaces import require_valid_public_surface


def add_output_parser(sp) -> None:
    op = sp.add_parser("output"); ops = op.add_subparsers(dest="output_command", required=True)
    profile = ops.add_parser("profile"); ps = profile.add_subparsers(dest="output_profile_command", required=True)
    record = ps.add_parser("record")
    record.add_argument("--topic", required=True, dest="topic_id")
    record.add_argument("--version", required=True, dest="output_version")
    record.add_argument("--audience", required=True)
    record.add_argument("--stable-section", action="append", default=[], dest="stable_sections")
    record.add_argument("--flexible-section", action="append", default=[], dest="flexible_sections")
    record.add_argument("--change-policy", default="")
    record.add_argument("--compatibility-note", default="")
    record.add_argument("--status", default="active")


def dispatch_output_command(args, ws) -> dict:
    if args.output_command == "profile" and args.output_profile_command == "record":
        profile = record_final_output_profile(
            ws,
            topic_id=args.topic_id,
            output_version=args.output_version,
            audience=args.audience,
            stable_sections=args.stable_sections,
            flexible_sections=args.flexible_sections,
            change_policy=args.change_policy,
            compatibility_note=args.compatibility_note,
            status=args.status,
        )
        return require_valid_public_surface("final_output_profile", {"ok": True, **asdict(profile)})
    raise SystemExit(f"unsupported output command: {args.output_command}")
