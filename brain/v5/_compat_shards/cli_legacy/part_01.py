# Compatibility shard 1 for cli_legacy.
from __future__ import annotations

import json

from pathlib import Path

from brain.v5.legacy_l2_graph import build_legacy_l2_graph_manifest, build_legacy_l2_typed_migration_packet

from brain.v5.legacy_l2_seed_audit import (
    audit_canonical_legacy_l2_seeds,
    build_canonical_legacy_l2_seed_review_worklist,
    record_legacy_l2_seed_group_review_result,
)

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
    compact_canonical_legacy_l2_seed_audit,
    compact_canonical_legacy_l2_seed_review_worklist,
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
    l2_seed_audit = legacy_subparsers.add_parser("l2-seed-audit")
    l2_seed_audit.add_argument("--sample-limit", type=int, default=50)
    l2_seed_audit.add_argument("--compact", "--progress", action="store_true", dest="compact")
    l2_seed_review = legacy_subparsers.add_parser("l2-seed-review-worklist")
    l2_seed_review.add_argument("--group-limit", type=int, default=50)
    l2_seed_review.add_argument("--sample-limit", type=int, default=5)
    l2_seed_review.add_argument("--compact", "--progress", action="store_true", dest="compact")
    l2_seed_review_result = legacy_subparsers.add_parser("l2-seed-review-result")
    l2_seed_review_result.add_argument("--group-id", required=True)
    l2_seed_review_result.add_argument("--status", required=True)
    l2_seed_review_result.add_argument("--decision", required=True)
    l2_seed_review_result.add_argument("--summary", required=True)
    l2_seed_review_result.add_argument("--source-family", default="")
    l2_seed_review_result.add_argument("--source-object-id", default="")
    l2_seed_review_result.add_argument("--seed-entry-id", action="append", default=[], dest="reviewed_seed_entry_ids")
    l2_seed_review_result.add_argument("--seed-entry-id-file", action="append", default=[], dest="reviewed_seed_entry_id_files")
    l2_seed_review_result.add_argument("--seed-ref", action="append", default=[], dest="reviewed_seed_refs")
    l2_seed_review_result.add_argument("--seed-ref-file", action="append", default=[], dest="reviewed_seed_ref_files")
    l2_seed_review_result.add_argument("--typed-ref", action="append", default=[], dest="reviewed_typed_refs")
    l2_seed_review_result.add_argument("--typed-ref-file", action="append", default=[], dest="reviewed_typed_ref_files")
    l2_seed_review_result.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    l2_seed_review_result.add_argument("--evidence-ref-file", action="append", default=[], dest="evidence_ref_files")
    l2_seed_review_result.add_argument("--validation-result-id", action="append", default=[], dest="validation_result_ids")
    l2_seed_review_result.add_argument(
        "--validation-result-id-file",
        action="append",
        default=[],
        dest="validation_result_id_files",
    )
    l2_seed_review_result.add_argument("--remaining-action", action="append", default=[], dest="remaining_actions")
    l2_seed_review_result.add_argument("--remaining-action-file", action="append", default=[], dest="remaining_action_files")
    l2_seed_review_result.add_argument("--checkpoint", default="", dest="checkpoint_id")
    l2_seed_review_result.add_argument("--reviewer-role", default="human_or_adversarial_reviewer")
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
