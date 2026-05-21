"""CLI parser and dispatcher for policy-facing AITP v5 commands."""

from __future__ import annotations

import argparse
from typing import Any

from brain.v5.pretool_policy import evaluate_context_pre_tool_policy
from brain.v5.public_surfaces import require_valid_public_surface


def add_policy_parser(sp: argparse._SubParsersAction) -> None:
    policy = sp.add_parser("policy")
    ps = policy.add_subparsers(dest="policy_command", required=True)
    pre = ps.add_parser("pre-tool")
    pre.add_argument("action")
    pre.add_argument("--session", required=True, dest="session_id")
    pre.add_argument("--claim", default="", dest="claim_id")
    pre.add_argument("--risk-level", default="guided")
    pre.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    pre.add_argument("--code-state-id", action="append", default=[], dest="code_state_ids")
    pre.add_argument("--validation-contract-id", action="append", default=[], dest="validation_contract_ids")
    pre.add_argument("--tool-run-id", action="append", default=[], dest="tool_run_ids")
    pre.add_argument("--validation-result-id", action="append", default=[], dest="validation_result_ids")
    pre.add_argument("--known-failure-mode", action="append", default=[], dest="known_failure_modes")
    pre.add_argument("--recipe", default="", dest="recipe_id")
    pre.add_argument("--executor", default="", dest="executor_id")
    pre.add_argument("--source-kind", default="")
    pre.add_argument("--source-ref", default="")
    pre.add_argument("--orientation-only", action="store_true")
    pre.add_argument("--human-checkpoint", default="", dest="human_checkpoint_id")


def dispatch_policy_command(args: argparse.Namespace, ws) -> dict[str, Any]:
    if args.policy_command != "pre-tool":
        raise SystemExit(f"unsupported policy command: {args.policy_command}")
    payload = evaluate_context_pre_tool_policy(
        ws,
        session_id=args.session_id,
        action=args.action,
        claim_id=args.claim_id,
        evidence_refs=args.evidence_refs,
        code_state_ids=args.code_state_ids,
        validation_contract_ids=args.validation_contract_ids,
        tool_run_ids=args.tool_run_ids,
        validation_result_ids=args.validation_result_ids,
        known_failure_modes=args.known_failure_modes,
        recipe_id=args.recipe_id,
        executor_id=args.executor_id,
        source_kind=args.source_kind,
        source_ref=args.source_ref,
        orientation_only=args.orientation_only,
        risk_level=args.risk_level,
        human_checkpoint_id=args.human_checkpoint_id,
    )
    return require_valid_public_surface("pre_tool_policy_decision", payload)
