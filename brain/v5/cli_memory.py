"""CLI helpers for L2 memory audit surfaces."""

from __future__ import annotations

import argparse
from typing import Any

from brain.v5.memory_audit import audit_l2_memory_context
from brain.v5.public_surfaces import require_valid_public_surface


def add_memory_parser(sp: argparse._SubParsersAction) -> None:
    memory = sp.add_parser("memory")
    ms = memory.add_subparsers(dest="memory_command", required=True)
    audit = ms.add_parser("audit")
    audit.add_argument("--claim", required=True, dest="claim_id")


def dispatch_memory_command(args: argparse.Namespace, ws: Any) -> dict[str, Any]:
    if args.memory_command == "audit":
        return require_valid_public_surface(
            "l2_memory_audit",
            audit_l2_memory_context(ws, claim_id=args.claim_id),
        )
    raise SystemExit(f"unsupported memory command: {args.memory_command}")
