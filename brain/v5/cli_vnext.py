"""Aggregated CLI wiring for vNext runtime surfaces."""

from __future__ import annotations

from brain.v5.cli_lane_exemplars import add_exemplar_parser, dispatch_exemplar_command
from brain.v5.cli_operator_checkpoint import add_operator_parser, dispatch_operator_command
from brain.v5.cli_output_stability import add_output_parser, dispatch_output_command
from brain.v5.cli_research_intent import add_intent_parser, dispatch_intent_command
from brain.v5.cli_run_iterations import add_run_parser, dispatch_run_command
from brain.v5.cli_status import add_status_parser, dispatch_status_command
from brain.v5.cli_strategy_memory import add_strategy_parser, dispatch_strategy_command

VNEXT_COMMANDS = {"operator", "intent", "output", "run", "strategy", "status", "exemplar"}


def add_vnext_parsers(sp) -> None:
    add_operator_parser(sp)
    add_intent_parser(sp)
    add_output_parser(sp)
    add_run_parser(sp)
    add_strategy_parser(sp)
    add_status_parser(sp)
    add_exemplar_parser(sp)


def dispatch_vnext_command(args, ws) -> dict:
    if args.command == "operator":
        return dispatch_operator_command(args, ws)
    if args.command == "intent":
        return dispatch_intent_command(args, ws)
    if args.command == "output":
        return dispatch_output_command(args, ws)
    if args.command == "run":
        return dispatch_run_command(args, ws)
    if args.command == "strategy":
        return dispatch_strategy_command(args, ws)
    if args.command == "status":
        return dispatch_status_command(args, ws)
    if args.command == "exemplar":
        return dispatch_exemplar_command(args, ws)
    raise SystemExit(f"unsupported vNext command: {args.command}")
