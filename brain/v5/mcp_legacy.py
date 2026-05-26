"""MCP wrappers for legacy migration surfaces."""

from __future__ import annotations

from pathlib import Path

from brain.v5.legacy_l2_graph import build_legacy_l2_graph_manifest, build_legacy_l2_typed_migration_packet
from brain.v5.legacy_l2_obsidian import write_legacy_l2_obsidian_view
from brain.v5.legacy_bridge import migrate_legacy_topic_to_v5
from brain.v5.legacy_migration_audit import audit_legacy_migration_coverage
from brain.v5.legacy_runtime_log_audit import build_legacy_runtime_log_marker_audit
from brain.v5.legacy_semantic_review_manifest import build_legacy_semantic_review_manifest
from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
from brain.v5.legacy_semantic_repair import apply_legacy_semantic_repair, build_legacy_semantic_repair_plan
from brain.v5.legacy_source_reconstruction import (
    apply_legacy_source_reconstruction_repair,
    build_legacy_source_reconstruction_plan,
    build_legacy_source_reconstruction_review_packet,
)
from brain.v5.legacy_semantic_review import (
    build_legacy_semantic_review_packet,
    build_legacy_semantic_review_queue,
    record_legacy_semantic_review_result,
)
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(Path(base))


def aitp_v5_migrate_legacy_topic_to_v5(
    base: str,
    *,
    topic_dir: str,
    context_id: str,
    session_id: str,
) -> dict:
    result = migrate_legacy_topic_to_v5(
        _ws(base),
        topic_dir,
        context_id=context_id,
        session_id=session_id,
    )
    return {"ok": True, **require_valid_public_surface("legacy_migration_result", result)}


def aitp_v5_audit_legacy_migration_coverage(base: str, *, migration_dir: str = "") -> dict:
    result = audit_legacy_migration_coverage(_ws(base), migration_dir=migration_dir or None)
    return {"ok": True, **require_valid_public_surface("legacy_migration_coverage_audit", result)}


def aitp_v5_build_legacy_l2_graph_manifest(base: str, *, legacy_l2_dir: str = "") -> dict:
    result = build_legacy_l2_graph_manifest(_ws(base), legacy_l2_dir=legacy_l2_dir)
    return {"ok": True, **require_valid_public_surface("legacy_l2_graph_manifest", result)}


def aitp_v5_build_legacy_l2_typed_migration_packet(base: str, *, legacy_l2_dir: str = "") -> dict:
    result = build_legacy_l2_typed_migration_packet(_ws(base), legacy_l2_dir=legacy_l2_dir)
    return {"ok": True, **require_valid_public_surface("legacy_l2_typed_migration_packet", result)}


def aitp_v5_write_legacy_l2_obsidian_view(
    base: str,
    *,
    legacy_l2_dir: str = "",
    output_dir: str = "",
) -> dict:
    result = write_legacy_l2_obsidian_view(
        _ws(base),
        legacy_l2_dir=legacy_l2_dir,
        output_dir=output_dir,
    )
    return {"ok": True, **require_valid_public_surface("legacy_l2_obsidian_view_bundle", result)}


def aitp_v5_build_legacy_runtime_log_marker_audit(
    base: str,
    *,
    topic: str,
    markers: list[str] | None = None,
    expected_min_count: int = 1,
    raw_log_files: list[str] | None = None,
    orientation_log_files: list[str] | None = None,
    migration_dir: str = "",
) -> dict:
    result = build_legacy_runtime_log_marker_audit(
        _ws(base),
        migration_dir=migration_dir,
        topic=topic,
        markers=markers or [],
        expected_min_count=expected_min_count,
        raw_log_files=raw_log_files,
        orientation_log_files=orientation_log_files,
    )
    return {"ok": True, **require_valid_public_surface("legacy_runtime_log_marker_audit", result)}


def aitp_v5_build_legacy_semantic_review_queue(base: str, *, migration_dir: str = "") -> dict:
    result = build_legacy_semantic_review_queue(_ws(base), migration_dir=migration_dir or None)
    return {"ok": True, **require_valid_public_surface("legacy_semantic_review_queue", result)}


def aitp_v5_build_legacy_semantic_review_manifest(base: str, *, migration_dir: str) -> dict:
    result = build_legacy_semantic_review_manifest(_ws(base), migration_dir=migration_dir)
    return {"ok": True, **require_valid_public_surface("legacy_semantic_review_manifest", result)}


def aitp_v5_build_legacy_semantic_review_worklist(base: str, *, migration_dir: str) -> dict:
    result = build_legacy_semantic_review_worklist(_ws(base), migration_dir=migration_dir)
    return {"ok": True, **require_valid_public_surface("legacy_semantic_review_worklist", result)}


def aitp_v5_build_legacy_semantic_review_packet(base: str, *, migration_dir: str, topic: str) -> dict:
    result = build_legacy_semantic_review_packet(_ws(base), migration_dir=migration_dir, topic=topic)
    return {"ok": True, **require_valid_public_surface("legacy_semantic_review_packet", result)}


def aitp_v5_build_legacy_semantic_repair_plan(base: str, *, migration_dir: str, topic: str) -> dict:
    result = build_legacy_semantic_repair_plan(_ws(base), migration_dir=migration_dir, topic=topic)
    return {"ok": True, **require_valid_public_surface("legacy_semantic_repair_plan", result)}


def aitp_v5_apply_legacy_semantic_repair(
    base: str,
    *,
    migration_dir: str,
    topic: str,
    repair_type: str,
    review_id: str,
) -> dict:
    result = apply_legacy_semantic_repair(
        _ws(base),
        migration_dir=migration_dir,
        topic=topic,
        repair_type=repair_type,
        review_id=review_id,
    )
    return {"ok": True, **require_valid_public_surface("legacy_semantic_repair_apply", result)}


def aitp_v5_build_legacy_source_reconstruction_plan(base: str, *, migration_dir: str, topic: str) -> dict:
    result = build_legacy_source_reconstruction_plan(_ws(base), migration_dir=migration_dir, topic=topic)
    return {"ok": True, **require_valid_public_surface("legacy_source_reconstruction_plan", result)}


def aitp_v5_build_legacy_source_reconstruction_review_packet(base: str, *, migration_dir: str, topic: str) -> dict:
    result = build_legacy_source_reconstruction_review_packet(_ws(base), migration_dir=migration_dir, topic=topic)
    return {"ok": True, **require_valid_public_surface("legacy_source_reconstruction_review_packet", result)}


def aitp_v5_apply_legacy_source_reconstruction_repair(
    base: str,
    *,
    migration_dir: str,
    topic: str,
    repair_type: str,
    review_id: str,
) -> dict:
    result = apply_legacy_source_reconstruction_repair(
        _ws(base),
        migration_dir=migration_dir,
        topic=topic,
        repair_type=repair_type,
        review_id=review_id,
    )
    return {"ok": True, **require_valid_public_surface("legacy_source_reconstruction_apply", result)}


def aitp_v5_record_legacy_semantic_review_result(
    base: str,
    *,
    migration_dir: str,
    topic: str,
    status: str,
    summary: str,
    active_claim_id: str = "",
    reviewed_legacy_refs: list[str] | None = None,
    reviewed_typed_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    validation_result_ids: list[str] | None = None,
    remaining_actions: list[str] | None = None,
    checkpoint_id: str = "",
    reviewer_role: str = "human_or_adversarial_reviewer",
) -> dict:
    result = record_legacy_semantic_review_result(
        _ws(base),
        migration_dir=migration_dir,
        topic=topic,
        status=status,
        summary=summary,
        active_claim_id=active_claim_id,
        reviewed_legacy_refs=reviewed_legacy_refs,
        reviewed_typed_refs=reviewed_typed_refs,
        evidence_refs=evidence_refs,
        validation_result_ids=validation_result_ids,
        remaining_actions=remaining_actions,
        checkpoint_id=checkpoint_id,
        reviewer_role=reviewer_role,
    )
    return {
        "ok": True,
        **require_valid_public_surface(
            "legacy_semantic_review_result_record",
            {"ok": True, **result.__dict__},
        ),
    }
