"""CLI helpers for L2 memory audit surfaces."""

from __future__ import annotations

import argparse
from typing import Any

from brain.v5.failure_mode_audit import audit_failure_mode_coverage
from dataclasses import asdict

from brain.v5.failure_mode_review import build_failure_mode_review_packet, record_failure_mode_review_result, request_failure_mode_review_checkpoint
from brain.v5.memory_audit import audit_l2_memory_context
from brain.v5.obsidian_views import write_l2_obsidian_view
from brain.v5.public_surfaces import require_valid_public_surface


def add_memory_parser(sp: argparse._SubParsersAction) -> None:
    memory = sp.add_parser("memory")
    ms = memory.add_subparsers(dest="memory_command", required=True)
    audit = ms.add_parser("audit")
    audit.add_argument("--claim", required=True, dest="claim_id")
    failure_modes = ms.add_parser("failure-modes")
    failure_modes.add_argument("--claim", required=True, dest="claim_id")
    review = ms.add_parser("failure-mode-review")
    review.add_argument("--claim", required=True, dest="claim_id")
    review_checkpoint = ms.add_parser("request-failure-mode-review")
    review_checkpoint.add_argument("--claim", required=True, dest="claim_id")
    review_result = ms.add_parser("failure-mode-review-result")
    review_result.add_argument("--claim", required=True, dest="claim_id")
    review_result.add_argument("--checkpoint", required=True, dest="checkpoint_id")
    review_result.add_argument("--status", required=True)
    review_result.add_argument("--reviewed-mode", action="append", default=[], dest="reviewed_failure_modes")
    review_result.add_argument("--basis-ref", action="append", default=[], dest="basis_refs")
    review_result.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    review_result.add_argument("--validation-result-id", action="append", default=[], dest="validation_result_ids")
    review_result.add_argument("--tool-run-id", action="append", default=[], dest="tool_run_ids")
    review_result.add_argument("--reference-location-id", action="append", default=[], dest="reference_location_ids")
    review_result.add_argument("--artifact-id", action="append", default=[], dest="artifact_ids")
    review_result.add_argument("--reviewer-role", default="adversarial_reviewer")
    review_result.add_argument("--summary", required=True)
    obsidian_view = ms.add_parser("obsidian-view")
    obsidian_view.add_argument("--output", default="", dest="output_dir")


def dispatch_memory_command(args: argparse.Namespace, ws: Any) -> dict[str, Any]:
    if args.memory_command == "audit":
        return require_valid_public_surface(
            "l2_memory_audit",
            audit_l2_memory_context(ws, claim_id=args.claim_id),
        )
    if args.memory_command == "failure-modes":
        return require_valid_public_surface(
            "failure_mode_audit",
            audit_failure_mode_coverage(ws, claim_id=args.claim_id),
        )
    if args.memory_command == "failure-mode-review":
        return require_valid_public_surface(
            "failure_mode_review_packet",
            build_failure_mode_review_packet(ws, claim_id=args.claim_id),
        )
    if args.memory_command == "request-failure-mode-review":
        return require_valid_public_surface(
            "human_checkpoint_record",
            {"ok": True, **asdict(request_failure_mode_review_checkpoint(ws, claim_id=args.claim_id))},
        )
    if args.memory_command == "failure-mode-review-result":
        result = record_failure_mode_review_result(
            ws,
            claim_id=args.claim_id,
            checkpoint_id=args.checkpoint_id,
            status=args.status,
            reviewed_failure_modes=args.reviewed_failure_modes,
            basis_refs=args.basis_refs,
            evidence_refs=args.evidence_refs,
            validation_result_ids=args.validation_result_ids,
            tool_run_ids=args.tool_run_ids,
            reference_location_ids=args.reference_location_ids,
            artifact_ids=args.artifact_ids,
            reviewer_role=args.reviewer_role,
            summary=args.summary,
        )
        return require_valid_public_surface("failure_mode_review_result_record", {"ok": True, **asdict(result)})
    if args.memory_command == "obsidian-view":
        return require_valid_public_surface(
            "l2_obsidian_view_bundle",
            write_l2_obsidian_view(ws, output_dir=args.output_dir),
        )
    raise SystemExit(f"unsupported memory command: {args.memory_command}")
