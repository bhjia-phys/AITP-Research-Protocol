"""CLI dispatch for legacy migration surfaces."""

from __future__ import annotations

from brain.v5.legacy_bridge import migrate_legacy_topic_to_v5
from brain.v5.legacy_migration_audit import audit_legacy_migration_coverage
from brain.v5.legacy_semantic_review import (
    build_legacy_semantic_review_queue,
    record_legacy_semantic_review_result,
)
from brain.v5.public_surfaces import require_valid_public_surface


def add_legacy_parser(subparsers) -> None:
    parser = subparsers.add_parser("legacy")
    legacy_subparsers = parser.add_subparsers(dest="legacy_command", required=True)
    migrate = legacy_subparsers.add_parser("migrate")
    migrate.add_argument("topic_dir")
    migrate.add_argument("--context", required=True, dest="context_id")
    migrate.add_argument("--session", required=True, dest="session_id")
    audit = legacy_subparsers.add_parser("migration-audit")
    audit.add_argument("--migration-dir", default="")
    review = legacy_subparsers.add_parser("semantic-review-queue")
    review.add_argument("--migration-dir", default="")
    result = legacy_subparsers.add_parser("semantic-review-result")
    result.add_argument("--migration-dir", required=True)
    result.add_argument("--topic", required=True)
    result.add_argument("--status", required=True)
    result.add_argument("--summary", required=True)
    result.add_argument("--active-claim", default="", dest="active_claim_id")
    result.add_argument("--legacy-ref", action="append", default=[], dest="reviewed_legacy_refs")
    result.add_argument("--typed-ref", action="append", default=[], dest="reviewed_typed_refs")
    result.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    result.add_argument("--validation-result-id", action="append", default=[], dest="validation_result_ids")
    result.add_argument("--remaining-action", action="append", default=[], dest="remaining_actions")
    result.add_argument("--checkpoint", default="", dest="checkpoint_id")
    result.add_argument("--reviewer-role", default="human_or_adversarial_reviewer")


def dispatch_legacy_command(args, ws) -> dict:
    if args.legacy_command == "migrate":
        result = migrate_legacy_topic_to_v5(
            ws,
            args.topic_dir,
            context_id=args.context_id,
            session_id=args.session_id,
        )
        return {"ok": True, **require_valid_public_surface("legacy_migration_result", result)}
    if args.legacy_command == "migration-audit":
        audit = audit_legacy_migration_coverage(ws, migration_dir=args.migration_dir or None)
        return {"ok": True, **require_valid_public_surface("legacy_migration_coverage_audit", audit)}
    if args.legacy_command == "semantic-review-queue":
        queue = build_legacy_semantic_review_queue(ws, migration_dir=args.migration_dir or None)
        return {"ok": True, **require_valid_public_surface("legacy_semantic_review_queue", queue)}
    if args.legacy_command == "semantic-review-result":
        result = record_legacy_semantic_review_result(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
            status=args.status,
            summary=args.summary,
            active_claim_id=args.active_claim_id,
            reviewed_legacy_refs=args.reviewed_legacy_refs,
            reviewed_typed_refs=args.reviewed_typed_refs,
            evidence_refs=args.evidence_refs,
            validation_result_ids=args.validation_result_ids,
            remaining_actions=args.remaining_actions,
            checkpoint_id=args.checkpoint_id,
            reviewer_role=args.reviewer_role,
        )
        return {
            "ok": True,
            **require_valid_public_surface(
                "legacy_semantic_review_result_record",
                {"ok": True, **result.__dict__},
            ),
        }
    raise ValueError(f"unsupported legacy command: {args.legacy_command}")
