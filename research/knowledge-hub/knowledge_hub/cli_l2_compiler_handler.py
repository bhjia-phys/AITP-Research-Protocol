from __future__ import annotations

import argparse
from typing import Any


L2_COMPILER_COMMANDS = {
    "compile-l2-map",
    "compile-l2-graph-report",
    "audit-l2-hygiene",
}


def register_l2_compiler_commands(subparsers: argparse._SubParsersAction[Any]) -> None:
    compile_l2_map = subparsers.add_parser(
        "compile-l2-map",
        help="Compile the bounded L2 workspace memory map",
    )
    compile_l2_map.add_argument("--json", action="store_true")

    compile_l2_graph_report = subparsers.add_parser(
        "compile-l2-graph-report",
        help="Compile a human-facing bounded L2 graph report and derived navigation pages",
    )
    compile_l2_graph_report.add_argument("--json", action="store_true")

    audit_l2_hygiene = subparsers.add_parser(
        "audit-l2-hygiene",
        help="Audit bounded L2 hygiene findings for the current workspace",
    )
    audit_l2_hygiene.add_argument("--json", action="store_true")


def dispatch_l2_compiler_command(args: argparse.Namespace, service: Any) -> dict[str, Any] | None:
    if args.command == "compile-l2-map":
        return service.compile_l2_workspace_map()

    if args.command == "compile-l2-graph-report":
        return service.compile_l2_graph_report()

    if args.command == "audit-l2-hygiene":
        return service.audit_l2_hygiene()

    return None
