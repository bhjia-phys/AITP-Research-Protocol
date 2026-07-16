"""CLI parser and dispatch for exact promotion checkpoint requests."""

from __future__ import annotations

from dataclasses import asdict

from brain.v5.memory import request_promotion_checkpoint
from brain.v5.public_surfaces import require_valid_public_surface


def add_promotion_checkpoint_parser(subparsers) -> None:
    parser = subparsers.add_parser("promotion-checkpoint")
    commands = parser.add_subparsers(dest="promotion_checkpoint_command", required=True)
    request = commands.add_parser("request")
    request.add_argument("--packet", required=True, dest="packet_id")
    request.add_argument("--reason", required=True)
    request.add_argument("--requested-by", required=True)
    request.add_argument("--expires-at", required=True)
    request.add_argument("--option", action="append", default=[], dest="options")


def is_promotion_checkpoint_command(args) -> bool:
    return getattr(args, "command", "") == "promotion-checkpoint"


def dispatch_promotion_checkpoint(args, ws) -> dict:
    if args.promotion_checkpoint_command != "request":
        raise ValueError("unsupported promotion checkpoint command")
    checkpoint = request_promotion_checkpoint(
        ws,
        packet_id=args.packet_id,
        reason=args.reason,
        requested_by=args.requested_by,
        expires_at=args.expires_at,
        options=args.options or ["approve", "reject"],
    )
    return require_valid_public_surface(
        "human_checkpoint_record",
        {"ok": True, **asdict(checkpoint)},
    )
