"""CLI parser and dispatcher for validation-facing AITP v5 commands."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from typing import Any

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.validation import create_validation_contract, record_validation_result


def add_validation_parser(sp: argparse._SubParsersAction) -> None:
    vp = sp.add_parser("validation")
    vs = vp.add_subparsers(dest="validation_command", required=True)
    vcp = vs.add_parser("contract")
    vcs = vcp.add_subparsers(dest="validation_contract_command", required=True)
    vcr = vcs.add_parser("create")
    vcr.add_argument("--topic", required=True, dest="topic_id")
    vcr.add_argument("--claim", required=True, dest="claim_id")
    vcr.add_argument("--required-check", action="append", default=[], dest="required_checks")
    vcr.add_argument("--failure-mode", action="append", default=[], dest="failure_modes")
    vcr.add_argument("--required-output", action="append", default=[], dest="required_evidence_outputs")
    vcr.add_argument("--recipe-id", action="append", default=[], dest="tool_recipe_ids")
    vcr.add_argument("--executor-id", action="append", default=[], dest="executor_ids")
    vcr.add_argument("--validator-role", default="adversarial_reviewer")

    vrp = vs.add_parser("result")
    vrs = vrp.add_subparsers(dest="validation_result_command", required=True)
    vrr = vrs.add_parser("record")
    vrr.add_argument("--topic", required=True, dest="topic_id")
    vrr.add_argument("--claim", required=True, dest="claim_id")
    vrr.add_argument("--contract", required=True, dest="contract_id")
    vrr.add_argument("--tool-run", required=True, dest="tool_run_id")
    vrr.add_argument("--status", required=True)
    vrr.add_argument("--checked-output", action="append", default=[], dest="checked_outputs")
    vrr.add_argument("--covered-failure-mode", action="append", default=[], dest="covered_failure_modes")
    vrr.add_argument("--failure-mode", action="append", default=[], dest="failure_modes_observed")
    vrr.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    vrr.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")
    vrr.add_argument("--summary", required=True)


def dispatch_validation_command(args: argparse.Namespace, ws) -> dict[str, Any]:
    if args.validation_command == "contract" and args.validation_contract_command == "create":
        record = create_validation_contract(
            ws,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            required_checks=args.required_checks,
            failure_modes=args.failure_modes,
            required_evidence_outputs=args.required_evidence_outputs,
            tool_recipe_ids=args.tool_recipe_ids,
            executor_ids=args.executor_ids,
            validator_role=args.validator_role,
        )
        return {"ok": True, **require_valid_public_surface("validation_contract_record", {"ok": True, **asdict(record)})}
    if args.validation_command == "result" and args.validation_result_command == "record":
        record = record_validation_result(
            ws,
            topic_id=args.topic_id,
            claim_id=args.claim_id,
            contract_id=args.contract_id,
            tool_run_id=args.tool_run_id,
            status=args.status,
            checked_outputs=args.checked_outputs,
            covered_failure_modes=args.covered_failure_modes,
            failure_modes_observed=args.failure_modes_observed,
            evidence_refs=args.evidence_refs,
            artifact_ids=args.artifact_ids,
            summary=args.summary,
        )
        return {"ok": True, **require_valid_public_surface("validation_result_record", {"ok": True, **asdict(record)})}
    raise SystemExit(f"unsupported validation command: {args.validation_command}")
