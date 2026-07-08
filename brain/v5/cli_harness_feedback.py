"""CLI commands for trust-neutral harness feedback payloads."""

from __future__ import annotations

import argparse

from brain.v5.harness_feedback import build_nio_harness_feedback_bundle, plan_run_dir_provenance_extractor
from brain.v5.public_surfaces import require_valid_public_surface


def add_harness_feedback_parser(sp: argparse._SubParsersAction) -> None:
    parser = sp.add_parser("harness-feedback")
    sub = parser.add_subparsers(dest="harness_feedback_command", required=True)
    sub.add_parser("nio-seed")
    extractor = sub.add_parser("extractor-plan")
    extractor.add_argument("--case-id", default="g0w0-magnetic-nio")


def dispatch_harness_feedback_command(args: argparse.Namespace, ws) -> dict:
    if args.harness_feedback_command == "nio-seed":
        return require_valid_public_surface("harness_feedback_bundle", build_nio_harness_feedback_bundle())
    if args.harness_feedback_command == "extractor-plan":
        return require_valid_public_surface(
            "run_dir_provenance_extractor_plan",
            plan_run_dir_provenance_extractor(case_id=args.case_id),
        )
    raise SystemExit(f"unsupported harness-feedback command: {args.harness_feedback_command}")
