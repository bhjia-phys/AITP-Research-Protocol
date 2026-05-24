"""CLI helpers for source reconstruction audit surfaces."""

from __future__ import annotations

import argparse

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.source_reconstruction import audit_source_reconstruction


def add_source_parser(sp: argparse._SubParsersAction) -> None:
    source = sp.add_parser("source")
    commands = source.add_subparsers(dest="source_command", required=True)
    audit = commands.add_parser("reconstruction-audit")
    audit.add_argument("--claim", required=True, dest="claim_id")


def dispatch_source_command(args: argparse.Namespace, ws) -> dict:
    if args.source_command == "reconstruction-audit":
        return require_valid_public_surface(
            "source_reconstruction_audit",
            audit_source_reconstruction(ws, claim_id=args.claim_id),
        )
    raise SystemExit(f"unsupported source command: {args.source_command}")
