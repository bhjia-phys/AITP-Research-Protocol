"""CLI dispatch for legacy migration surfaces."""

from __future__ import annotations

import json
from pathlib import Path

from brain.v5.legacy_l2_graph import build_legacy_l2_graph_manifest, build_legacy_l2_typed_migration_packet
from brain.v5.legacy_l2_obsidian import write_legacy_l2_obsidian_view
from brain.v5.legacy_bridge import migrate_legacy_topic_to_v5
from brain.v5.curated_legacy_migration import known_curated_legacy_topics, migrate_curated_legacy_topic_to_v5
from brain.v5.legacy_executable_evidence import build_legacy_executable_evidence_packet
from brain.v5.legacy_human_checkpoint_obsidian import write_legacy_human_checkpoint_obsidian_view
from brain.v5.legacy_human_checkpoint_packet import build_legacy_human_checkpoint_packet
from brain.v5.legacy_migration_accounting import write_legacy_migration_accounting_run
from brain.v5.legacy_migration_audit import audit_legacy_migration_coverage
from brain.v5.legacy_runtime_log_audit import build_legacy_runtime_log_marker_audit
from brain.v5.legacy_semantic_review_manifest import build_legacy_semantic_review_manifest
from brain.v5.legacy_semantic_needs_revision_obsidian import write_legacy_semantic_needs_revision_basis_obsidian_view
from brain.v5.legacy_semantic_needs_revision_packet import build_legacy_semantic_needs_revision_basis_packet
from brain.v5.legacy_semantic_review_obsidian import write_legacy_semantic_review_obsidian_view
from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
from brain.v5.legacy_semantic_needs_revision import build_legacy_semantic_needs_revision_basis_queue
from brain.v5.legacy_semantic_repair import apply_legacy_semantic_repair, build_legacy_semantic_repair_plan
from brain.v5.legacy_semantic_repair_manifest import build_legacy_semantic_repair_manifest
from brain.v5.legacy_source_metadata_repair import build_legacy_source_metadata_repair_packet
from brain.v5.legacy_source_reconstruction_obsidian import write_legacy_source_reconstruction_obsidian_view
from brain.v5.legacy_topic_question_backfill import build_legacy_topic_question_backfill_packet
from brain.v5.legacy_source_reconstruction import (
    apply_legacy_source_reconstruction_repair,
    build_legacy_source_reconstruction_manifest,
    build_legacy_source_reconstruction_plan,
    build_legacy_source_reconstruction_review_packet,
)
from brain.v5.cli_legacy_progress import (
    compact_legacy_executable_evidence_packet,
    compact_legacy_human_checkpoint_obsidian_view_bundle,
    compact_legacy_human_checkpoint_packet,
    compact_legacy_semantic_review_packet,
    compact_legacy_semantic_review_manifest,
    compact_legacy_semantic_review_obsidian_view_bundle,
    compact_legacy_semantic_review_worklist,
    compact_legacy_source_metadata_repair_packet,
    compact_legacy_source_reconstruction_manifest,
    compact_legacy_source_reconstruction_obsidian_view_bundle,
    compact_legacy_source_reconstruction_review_packet,
)
from brain.v5.cli_legacy_topic_question_progress import compact_legacy_topic_question_backfill_packet
from brain.v5.cli_legacy_coverage_progress import compact_legacy_migration_coverage_audit
from brain.v5.cli_legacy_l2_progress import (
    compact_legacy_l2_graph_manifest,
    compact_legacy_l2_obsidian_view_bundle,
    compact_legacy_l2_typed_migration_packet,
)
from brain.v5.cli_legacy_repair_progress import (
    compact_legacy_semantic_needs_revision_basis_packet,
    compact_legacy_semantic_needs_revision_basis_queue,
    compact_legacy_semantic_needs_revision_basis_obsidian_view_bundle,
    compact_legacy_semantic_repair_manifest,
    compact_legacy_semantic_repair_plan,
)
from brain.v5.legacy_semantic_review import (
    build_legacy_semantic_review_packet,
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
    curated = legacy_subparsers.add_parser("curated-migrate")
    curated.add_argument("topic_dir")
    curated.add_argument("--context", default="", dest="context_id")
    curated.add_argument("--session", default="", dest="session_id")
    legacy_subparsers.add_parser("curated-known-topics")
    audit = legacy_subparsers.add_parser("migration-audit")
    audit.add_argument("--migration-dir", default="")
    audit.add_argument("--compact", "--progress", action="store_true", dest="compact")
    accounting = legacy_subparsers.add_parser("migration-accounting-run")
    accounting.add_argument("--legacy-root", default="")
    accounting.add_argument("--run-id", default="")
    accounting.add_argument("--compact", "--progress", action="store_true", dest="compact")
    l2_graph = legacy_subparsers.add_parser("l2-graph-manifest")
    l2_graph.add_argument("--legacy-l2-dir", default="")
    l2_graph.add_argument("--compact", "--progress", action="store_true", dest="compact")
    l2_typed = legacy_subparsers.add_parser("l2-typed-migration-packet")
    l2_typed.add_argument("--legacy-l2-dir", default="")
    l2_typed.add_argument("--compact", "--progress", action="store_true", dest="compact")
    l2_obsidian = legacy_subparsers.add_parser("l2-obsidian-view")
    l2_obsidian.add_argument("--legacy-l2-dir", default="")
    l2_obsidian.add_argument("--output-dir", default="")
    l2_obsidian.add_argument("--compact", "--progress", action="store_true", dest="compact")
    runtime_log = legacy_subparsers.add_parser("runtime-log-marker-audit")
    runtime_log.add_argument("--migration-dir", default="")
    runtime_log.add_argument("--topic", required=True)
    runtime_log.add_argument("--marker", action="append", required=True, dest="markers")
    runtime_log.add_argument("--expected-min-count", type=int, default=1)
    runtime_log.add_argument("--raw-log-file", action="append", default=[], dest="raw_log_files")
    runtime_log.add_argument("--orientation-log-file", action="append", default=[], dest="orientation_log_files")
    review = legacy_subparsers.add_parser("semantic-review-queue")
    review.add_argument("--migration-dir", default="")
    manifest = legacy_subparsers.add_parser("semantic-review-manifest")
    manifest.add_argument("--migration-dir", required=True)
    manifest.add_argument("--compact", "--progress", action="store_true", dest="compact")
    worklist = legacy_subparsers.add_parser("semantic-review-worklist")
    worklist.add_argument("--migration-dir", required=True)
    worklist.add_argument("--compact", "--progress", action="store_true", dest="compact")
    needs_revision = legacy_subparsers.add_parser("semantic-needs-revision-basis")
    needs_revision.add_argument("--migration-dir", required=True)
    needs_revision.add_argument("--compact", "--progress", action="store_true", dest="compact")
    needs_revision_packet = legacy_subparsers.add_parser("semantic-needs-revision-basis-packet")
    needs_revision_packet.add_argument("--migration-dir", required=True)
    needs_revision_packet.add_argument("--topic", required=True)
    needs_revision_packet.add_argument("--compact", "--progress", action="store_true", dest="compact")
    needs_revision_obsidian = legacy_subparsers.add_parser("semantic-needs-revision-basis-obsidian-view")
    needs_revision_obsidian.add_argument("--migration-dir", required=True)
    needs_revision_obsidian.add_argument("--output-dir", default="")
    needs_revision_obsidian.add_argument("--compact", "--progress", action="store_true", dest="compact")
    worklist_obsidian = legacy_subparsers.add_parser("semantic-review-obsidian-view")
    worklist_obsidian.add_argument("--migration-dir", required=True)
    worklist_obsidian.add_argument("--output-dir", default="")
    worklist_obsidian.add_argument("--compact", "--progress", action="store_true", dest="compact")
    packet = legacy_subparsers.add_parser("semantic-review-packet")
    packet.add_argument("--migration-dir", required=True)
    packet.add_argument("--topic", required=True)
    packet.add_argument("--compact", "--progress", action="store_true", dest="compact")
    repair = legacy_subparsers.add_parser("semantic-repair-plan")
    repair.add_argument("--migration-dir", required=True)
    repair.add_argument("--topic", required=True)
    repair.add_argument("--compact", "--progress", action="store_true", dest="compact")
    repair_manifest = legacy_subparsers.add_parser("semantic-repair-manifest")
    repair_manifest.add_argument("--migration-dir", required=True)
    repair_manifest.add_argument("--compact", "--progress", action="store_true", dest="compact")
    repair_apply = legacy_subparsers.add_parser("semantic-repair-apply")
    repair_apply.add_argument("--migration-dir", required=True)
    repair_apply.add_argument("--topic", required=True)
    repair_apply.add_argument("--repair-type", required=True)
    repair_apply.add_argument("--review-id", required=True)
    source_repair = legacy_subparsers.add_parser("source-reconstruction-plan")
    source_repair.add_argument("--migration-dir", required=True)
    source_repair.add_argument("--topic", required=True)
    source_manifest = legacy_subparsers.add_parser("source-reconstruction-manifest")
    source_manifest.add_argument("--migration-dir", required=True)
    source_manifest.add_argument("--compact", "--progress", action="store_true", dest="compact")
    source_obsidian = legacy_subparsers.add_parser("source-reconstruction-obsidian-view")
    source_obsidian.add_argument("--migration-dir", required=True)
    source_obsidian.add_argument("--output-dir", default="")
    source_obsidian.add_argument("--compact", "--progress", action="store_true", dest="compact")
    source_review = legacy_subparsers.add_parser("source-reconstruction-review")
    source_review.add_argument("--migration-dir", required=True)
    source_review.add_argument("--topic", required=True)
    source_review.add_argument("--compact", "--progress", action="store_true", dest="compact")
    source_metadata = legacy_subparsers.add_parser("source-metadata-repair-packet")
    source_metadata.add_argument("--migration-dir", required=True)
    source_metadata.add_argument("--topic", default="")
    source_metadata.add_argument("--compact", "--progress", action="store_true", dest="compact")
    executable = legacy_subparsers.add_parser("executable-evidence-packet")
    executable.add_argument("--migration-dir", required=True)
    executable.add_argument("--topic", default="")
    executable.add_argument("--compact", "--progress", action="store_true", dest="compact")
    human_checkpoint = legacy_subparsers.add_parser("human-checkpoint-packet")
    human_checkpoint.add_argument("--migration-dir", required=True)
    human_checkpoint.add_argument("--topic", default="")
    human_checkpoint.add_argument("--compact", "--progress", action="store_true", dest="compact")
    topic_question = legacy_subparsers.add_parser("topic-question-backfill-packet")
    topic_question.add_argument("--migration-dir", required=True)
    topic_question.add_argument("--compact", "--progress", action="store_true", dest="compact")
    human_checkpoint_obsidian = legacy_subparsers.add_parser("human-checkpoint-obsidian-view")
    human_checkpoint_obsidian.add_argument("--migration-dir", required=True)
    human_checkpoint_obsidian.add_argument("--topic", default="")
    human_checkpoint_obsidian.add_argument("--output-dir", default="")
    human_checkpoint_obsidian.add_argument("--compact", "--progress", action="store_true", dest="compact")
    source_repair_apply = legacy_subparsers.add_parser("source-reconstruction-apply")
    source_repair_apply.add_argument("--migration-dir", required=True)
    source_repair_apply.add_argument("--topic", required=True)
    source_repair_apply.add_argument("--repair-type", required=True)
    source_repair_apply.add_argument("--review-id", required=True)
    result = legacy_subparsers.add_parser("semantic-review-result")
    result.add_argument("--migration-dir", required=True)
    result.add_argument("--topic", required=True)
    result.add_argument("--status", required=True)
    result.add_argument("--summary", required=True)
    result.add_argument("--active-claim", default="", dest="active_claim_id")
    result.add_argument("--legacy-ref", action="append", default=[], dest="reviewed_legacy_refs")
    result.add_argument("--legacy-ref-file", action="append", default=[], dest="reviewed_legacy_ref_files")
    result.add_argument("--typed-ref", action="append", default=[], dest="reviewed_typed_refs")
    result.add_argument("--typed-ref-file", action="append", default=[], dest="reviewed_typed_ref_files")
    result.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    result.add_argument("--evidence-ref-file", action="append", default=[], dest="evidence_ref_files")
    result.add_argument("--validation-result-id", action="append", default=[], dest="validation_result_ids")
    result.add_argument(
        "--validation-result-id-file",
        action="append",
        default=[],
        dest="validation_result_id_files",
    )
    result.add_argument("--remaining-action", action="append", default=[], dest="remaining_actions")
    result.add_argument("--remaining-action-file", action="append", default=[], dest="remaining_action_files")
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
    if args.legacy_command == "curated-migrate":
        result = migrate_curated_legacy_topic_to_v5(
            ws,
            args.topic_dir,
            context_id=args.context_id,
            session_id=args.session_id,
        )
        return {"ok": True, **require_valid_public_surface("legacy_migration_result", result)}
    if args.legacy_command == "curated-known-topics":
        return {
            "ok": True,
            "kind": "curated_legacy_topic_catalog",
            "topics": known_curated_legacy_topics(),
            "summary_inputs_trusted": False,
        }
    if args.legacy_command == "migration-audit":
        audit = audit_legacy_migration_coverage(ws, migration_dir=args.migration_dir or None)
        payload = {"ok": True, **require_valid_public_surface("legacy_migration_coverage_audit", audit)}
        if getattr(args, "compact", False):
            return compact_legacy_migration_coverage_audit(payload)
        return payload
    if args.legacy_command == "migration-accounting-run":
        run_dir = write_legacy_migration_accounting_run(
            ws,
            legacy_root=args.legacy_root or None,
            run_id=args.run_id,
        )
        audit = audit_legacy_migration_coverage(ws, migration_dir=run_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_migration_coverage_audit", audit)}
        if getattr(args, "compact", False):
            return compact_legacy_migration_coverage_audit(payload)
        return payload
    if args.legacy_command == "l2-graph-manifest":
        manifest = build_legacy_l2_graph_manifest(ws, legacy_l2_dir=args.legacy_l2_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_l2_graph_manifest", manifest)}
        if getattr(args, "compact", False):
            return compact_legacy_l2_graph_manifest(payload)
        return payload
    if args.legacy_command == "l2-typed-migration-packet":
        packet = build_legacy_l2_typed_migration_packet(ws, legacy_l2_dir=args.legacy_l2_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_l2_typed_migration_packet", packet)}
        if getattr(args, "compact", False):
            return compact_legacy_l2_typed_migration_packet(payload)
        return payload
    if args.legacy_command == "l2-obsidian-view":
        bundle = write_legacy_l2_obsidian_view(
            ws,
            legacy_l2_dir=args.legacy_l2_dir,
            output_dir=args.output_dir,
        )
        payload = {"ok": True, **require_valid_public_surface("legacy_l2_obsidian_view_bundle", bundle)}
        if getattr(args, "compact", False):
            return compact_legacy_l2_obsidian_view_bundle(payload)
        return payload
    if args.legacy_command == "runtime-log-marker-audit":
        audit = build_legacy_runtime_log_marker_audit(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
            markers=args.markers,
            expected_min_count=args.expected_min_count,
            raw_log_files=args.raw_log_files,
            orientation_log_files=args.orientation_log_files,
        )
        return {"ok": True, **require_valid_public_surface("legacy_runtime_log_marker_audit", audit)}
    if args.legacy_command == "semantic-review-queue":
        queue = build_legacy_semantic_review_queue(ws, migration_dir=args.migration_dir or None)
        return {"ok": True, **require_valid_public_surface("legacy_semantic_review_queue", queue)}
    if args.legacy_command == "semantic-review-manifest":
        manifest = build_legacy_semantic_review_manifest(ws, migration_dir=args.migration_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_semantic_review_manifest", manifest)}
        if getattr(args, "compact", False):
            return compact_legacy_semantic_review_manifest(payload)
        return payload
    if args.legacy_command == "semantic-review-worklist":
        worklist = build_legacy_semantic_review_worklist(ws, migration_dir=args.migration_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_semantic_review_worklist", worklist)}
        if getattr(args, "compact", False):
            return compact_legacy_semantic_review_worklist(payload)
        return payload
    if args.legacy_command == "semantic-needs-revision-basis":
        queue = build_legacy_semantic_needs_revision_basis_queue(ws, migration_dir=args.migration_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_semantic_needs_revision_basis_queue", queue)}
        if getattr(args, "compact", False):
            return compact_legacy_semantic_needs_revision_basis_queue(payload)
        return payload
    if args.legacy_command == "semantic-needs-revision-basis-packet":
        packet = build_legacy_semantic_needs_revision_basis_packet(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
        )
        payload = {
            "ok": True,
            **require_valid_public_surface("legacy_semantic_needs_revision_basis_packet", packet),
        }
        if getattr(args, "compact", False):
            return compact_legacy_semantic_needs_revision_basis_packet(payload)
        return payload
    if args.legacy_command == "semantic-needs-revision-basis-obsidian-view":
        bundle = write_legacy_semantic_needs_revision_basis_obsidian_view(
            ws,
            migration_dir=args.migration_dir,
            output_dir=args.output_dir,
        )
        payload = {
            "ok": True,
            **require_valid_public_surface("legacy_semantic_needs_revision_basis_obsidian_view_bundle", bundle),
        }
        if getattr(args, "compact", False):
            return compact_legacy_semantic_needs_revision_basis_obsidian_view_bundle(payload)
        return payload
    if args.legacy_command == "semantic-review-obsidian-view":
        bundle = write_legacy_semantic_review_obsidian_view(
            ws,
            migration_dir=args.migration_dir,
            output_dir=args.output_dir,
        )
        payload = {"ok": True, **require_valid_public_surface("legacy_semantic_review_obsidian_view_bundle", bundle)}
        if getattr(args, "compact", False):
            return compact_legacy_semantic_review_obsidian_view_bundle(payload)
        return payload
    if args.legacy_command == "semantic-review-packet":
        packet = build_legacy_semantic_review_packet(ws, migration_dir=args.migration_dir, topic=args.topic)
        payload = {"ok": True, **require_valid_public_surface("legacy_semantic_review_packet", packet)}
        if getattr(args, "compact", False):
            return compact_legacy_semantic_review_packet(payload)
        return payload
    if args.legacy_command == "semantic-repair-plan":
        plan = build_legacy_semantic_repair_plan(ws, migration_dir=args.migration_dir, topic=args.topic)
        payload = {"ok": True, **require_valid_public_surface("legacy_semantic_repair_plan", plan)}
        if getattr(args, "compact", False):
            return compact_legacy_semantic_repair_plan(payload)
        return payload
    if args.legacy_command == "semantic-repair-manifest":
        manifest = build_legacy_semantic_repair_manifest(ws, migration_dir=args.migration_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_semantic_repair_manifest", manifest)}
        if getattr(args, "compact", False):
            return compact_legacy_semantic_repair_manifest(payload)
        return payload
    if args.legacy_command == "semantic-repair-apply":
        result = apply_legacy_semantic_repair(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
            repair_type=args.repair_type,
            review_id=args.review_id,
        )
        return {"ok": True, **require_valid_public_surface("legacy_semantic_repair_apply", result)}
    if args.legacy_command == "source-reconstruction-plan":
        plan = build_legacy_source_reconstruction_plan(ws, migration_dir=args.migration_dir, topic=args.topic)
        return {"ok": True, **require_valid_public_surface("legacy_source_reconstruction_plan", plan)}
    if args.legacy_command == "source-reconstruction-manifest":
        manifest = build_legacy_source_reconstruction_manifest(ws, migration_dir=args.migration_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_source_reconstruction_manifest", manifest)}
        if getattr(args, "compact", False):
            return compact_legacy_source_reconstruction_manifest(payload)
        return payload
    if args.legacy_command == "source-reconstruction-obsidian-view":
        bundle = write_legacy_source_reconstruction_obsidian_view(
            ws,
            migration_dir=args.migration_dir,
            output_dir=args.output_dir,
        )
        payload = {"ok": True, **require_valid_public_surface("legacy_source_reconstruction_obsidian_view_bundle", bundle)}
        if getattr(args, "compact", False):
            return compact_legacy_source_reconstruction_obsidian_view_bundle(payload)
        return payload
    if args.legacy_command == "source-reconstruction-review":
        packet = build_legacy_source_reconstruction_review_packet(ws, migration_dir=args.migration_dir, topic=args.topic)
        payload = {"ok": True, **require_valid_public_surface("legacy_source_reconstruction_review_packet", packet)}
        if getattr(args, "compact", False):
            return compact_legacy_source_reconstruction_review_packet(payload)
        return payload
    if args.legacy_command == "source-metadata-repair-packet":
        packet = build_legacy_source_metadata_repair_packet(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
        )
        payload = {"ok": True, **require_valid_public_surface("legacy_source_metadata_repair_packet", packet)}
        if getattr(args, "compact", False):
            return compact_legacy_source_metadata_repair_packet(payload)
        return payload
    if args.legacy_command == "executable-evidence-packet":
        packet = build_legacy_executable_evidence_packet(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
        )
        payload = {"ok": True, **require_valid_public_surface("legacy_executable_evidence_packet", packet)}
        if getattr(args, "compact", False):
            return compact_legacy_executable_evidence_packet(payload)
        return payload
    if args.legacy_command == "human-checkpoint-packet":
        packet = build_legacy_human_checkpoint_packet(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
        )
        payload = {"ok": True, **require_valid_public_surface("legacy_human_checkpoint_packet", packet)}
        if getattr(args, "compact", False):
            return compact_legacy_human_checkpoint_packet(payload)
        return payload
    if args.legacy_command == "topic-question-backfill-packet":
        packet = build_legacy_topic_question_backfill_packet(ws, migration_dir=args.migration_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_topic_question_backfill_packet", packet)}
        if getattr(args, "compact", False):
            return compact_legacy_topic_question_backfill_packet(payload)
        return payload
    if args.legacy_command == "human-checkpoint-obsidian-view":
        bundle = write_legacy_human_checkpoint_obsidian_view(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
            output_dir=args.output_dir,
        )
        payload = {"ok": True, **require_valid_public_surface("legacy_human_checkpoint_obsidian_view_bundle", bundle)}
        if getattr(args, "compact", False):
            return compact_legacy_human_checkpoint_obsidian_view_bundle(payload)
        return payload
    if args.legacy_command == "source-reconstruction-apply":
        result = apply_legacy_source_reconstruction_repair(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
            repair_type=args.repair_type,
            review_id=args.review_id,
        )
        return {"ok": True, **require_valid_public_surface("legacy_source_reconstruction_apply", result)}
    if args.legacy_command == "semantic-review-result":
        result = record_legacy_semantic_review_result(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
            status=args.status,
            summary=args.summary,
            active_claim_id=args.active_claim_id,
            reviewed_legacy_refs=_merge_inline_and_file_values(
                args.reviewed_legacy_refs,
                args.reviewed_legacy_ref_files,
            ),
            reviewed_typed_refs=_merge_inline_and_file_values(
                args.reviewed_typed_refs,
                args.reviewed_typed_ref_files,
            ),
            evidence_refs=_merge_inline_and_file_values(
                args.evidence_refs,
                args.evidence_ref_files,
            ),
            validation_result_ids=_merge_inline_and_file_values(
                args.validation_result_ids,
                args.validation_result_id_files,
            ),
            remaining_actions=_merge_inline_and_file_values(
                args.remaining_actions,
                args.remaining_action_files,
            ),
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


def _merge_inline_and_file_values(inline_values: list[str], file_paths: list[str]) -> list[str]:
    values = [value for value in inline_values if str(value).strip()]
    for path in file_paths:
        values.extend(_read_value_file(path))
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        clean = str(value).strip()
        if clean and clean not in seen:
            seen.add(clean)
            unique.append(clean)
    return unique


def _read_value_file(path: str) -> list[str]:
    target = Path(path)
    text = target.read_text(encoding="utf-8-sig")
    stripped = text.strip().lstrip("\ufeff")
    if not stripped:
        return []
    if stripped.startswith("["):
        payload = json.loads(stripped)
        if not isinstance(payload, list) or not all(isinstance(value, str) for value in payload):
            raise ValueError(f"value file must contain a JSON string array: {path}")
        return payload
    return [line.strip().lstrip("\ufeff") for line in text.splitlines() if line.strip()]
