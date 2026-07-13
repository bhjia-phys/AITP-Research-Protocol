"""CLI parser and dispatch for M0 query/index operations."""

from __future__ import annotations

from brain.v5.mcp_query import (
    aitp_v5_build_query_index,
    aitp_v5_exact_expand_records,
    aitp_v5_get_query_index_status,
)


def add_query_parser(subparsers) -> None:
    query = subparsers.add_parser("query")
    commands = query.add_subparsers(dest="query_command", required=True)
    commands.add_parser("index-build")
    commands.add_parser("index-status")
    exact = commands.add_parser("exact")
    exact.add_argument("--ref", action="append", required=True, dest="refs")
    exact.add_argument("--limit", type=int, default=50)


def dispatch_query_command(args) -> dict:
    if args.query_command == "index-build":
        return aitp_v5_build_query_index(args.base)
    if args.query_command == "index-status":
        return aitp_v5_get_query_index_status(args.base)
    if args.query_command == "exact":
        return aitp_v5_exact_expand_records(args.base, refs=args.refs, limit=args.limit)
    raise SystemExit(f"unsupported query command: {args.query_command}")
