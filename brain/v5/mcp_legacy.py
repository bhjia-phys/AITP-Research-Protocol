"""MCP wrappers for legacy migration surfaces."""

from __future__ import annotations

from pathlib import Path

from brain.v5.legacy_bridge import migrate_legacy_topic_to_v5
from brain.v5.legacy_migration_audit import audit_legacy_migration_coverage
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


def aitp_v5_build_legacy_semantic_review_queue(base: str, *, migration_dir: str = "") -> dict:
    result = build_legacy_semantic_review_queue(_ws(base), migration_dir=migration_dir or None)
    return {"ok": True, **require_valid_public_surface("legacy_semantic_review_queue", result)}


def aitp_v5_build_legacy_semantic_review_packet(base: str, *, migration_dir: str, topic: str) -> dict:
    result = build_legacy_semantic_review_packet(_ws(base), migration_dir=migration_dir, topic=topic)
    return {"ok": True, **require_valid_public_surface("legacy_semantic_review_packet", result)}


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
