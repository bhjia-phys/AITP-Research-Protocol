"""CLI helpers for source reconstruction audit surfaces."""

from __future__ import annotations

import argparse
from dataclasses import asdict

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.source_reconstruction_obsidian import write_source_reconstruction_obsidian_view
from brain.v5.cli_progress import (
    compact_source_reconstruction_manifest,
    compact_source_reconstruction_review_manifest,
    compact_source_reconstruction_review_packet,
)
from brain.v5.source_reconstruction import (
    audit_source_reconstruction,
    build_source_reconstruction_manifest,
    build_source_reconstruction_review_packet,
)
from brain.v5.source_reconstruction_review import (
    build_source_reconstruction_review_manifest,
    record_source_reconstruction_review_result,
)


def add_source_parser(sp: argparse._SubParsersAction) -> None:
    source = sp.add_parser("source")
    commands = source.add_subparsers(dest="source_command", required=True)
    audit = commands.add_parser("reconstruction-audit")
    audit.add_argument("--claim", required=True, dest="claim_id")
    manifest = commands.add_parser("reconstruction-manifest")
    manifest.add_argument("--compact", "--progress", action="store_true", dest="compact")
    review_manifest = commands.add_parser("reconstruction-review-manifest")
    review_manifest.add_argument("--compact", "--progress", action="store_true", dest="compact")
    obsidian = commands.add_parser("reconstruction-obsidian-view")
    obsidian.add_argument("--output-dir", default="")
    review = commands.add_parser("reconstruction-review")
    review.add_argument("--claim", required=True, dest="claim_id")
    review.add_argument("--compact", "--progress", action="store_true", dest="compact")
    result = commands.add_parser("reconstruction-review-result")
    result.add_argument("--claim", required=True, dest="claim_id")
    result.add_argument("--status", required=True)
    result.add_argument("--reviewed-component", action="append", default=[], dest="reviewed_components")
    result.add_argument("--basis-ref", action="append", default=[], dest="basis_refs")
    result.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    result.add_argument("--validation-result-id", action="append", default=[], dest="validation_result_ids")
    result.add_argument("--reference-location-id", action="append", default=[], dest="reference_location_ids")
    result.add_argument("--object-id", action="append", default=[], dest="object_ids")
    result.add_argument("--relation-id", action="append", default=[], dest="relation_ids")
    result.add_argument("--remaining-action", action="append", default=[], dest="remaining_actions")
    result.add_argument("--reviewer-role", default="human_or_adversarial_reviewer")
    result.add_argument("--summary", required=True)


def dispatch_source_command(args: argparse.Namespace, ws) -> dict:
    if args.source_command == "reconstruction-audit":
        return require_valid_public_surface(
            "source_reconstruction_audit",
            audit_source_reconstruction(ws, claim_id=args.claim_id),
        )
    if args.source_command == "reconstruction-manifest":
        manifest = require_valid_public_surface(
            "source_reconstruction_manifest",
            build_source_reconstruction_manifest(ws),
        )
        if getattr(args, "compact", False):
            return compact_source_reconstruction_manifest(manifest)
        return manifest
    if args.source_command == "reconstruction-review-manifest":
        manifest = require_valid_public_surface(
            "source_reconstruction_review_manifest",
            build_source_reconstruction_review_manifest(ws),
        )
        if getattr(args, "compact", False):
            return compact_source_reconstruction_review_manifest(manifest)
        return manifest
    if args.source_command == "reconstruction-obsidian-view":
        return require_valid_public_surface(
            "source_reconstruction_obsidian_view_bundle",
            write_source_reconstruction_obsidian_view(ws, output_dir=args.output_dir),
        )
    if args.source_command == "reconstruction-review":
        packet = require_valid_public_surface(
            "source_reconstruction_review_packet",
            build_source_reconstruction_review_packet(ws, claim_id=args.claim_id),
        )
        if getattr(args, "compact", False):
            return compact_source_reconstruction_review_packet(packet)
        return packet
    if args.source_command == "reconstruction-review-result":
        result = record_source_reconstruction_review_result(
            ws,
            claim_id=args.claim_id,
            status=args.status,
            reviewed_components=args.reviewed_components,
            basis_refs=args.basis_refs,
            evidence_refs=args.evidence_refs,
            validation_result_ids=args.validation_result_ids,
            reference_location_ids=args.reference_location_ids,
            object_ids=args.object_ids,
            relation_ids=args.relation_ids,
            remaining_actions=args.remaining_actions,
            reviewer_role=args.reviewer_role,
            summary=args.summary,
        )
        return require_valid_public_surface(
            "source_reconstruction_review_result_record",
            {"ok": True, **asdict(result)},
        )
    raise SystemExit(f"unsupported source command: {args.source_command}")
