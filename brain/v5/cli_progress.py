"""Compact CLI progress payloads for high-volume audit surfaces."""

from __future__ import annotations

from typing import Any


def compact_source_reconstruction_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "source_reconstruction_manifest_progress",
        "source_surface": "source_reconstruction_manifest",
        "claim_count": int(payload.get("claim_count") or 0),
        "complete_claim_count": int(payload.get("complete_claim_count") or 0),
        "incomplete_claim_count": int(payload.get("incomplete_claim_count") or 0),
        "missing_component_counts": dict(payload.get("missing_component_counts") or {}),
        "next_action_count": len(payload.get("next_actions") or []),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_source_reconstruction_review_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    progress = dict(payload.get("review_progress") or {})
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "source_reconstruction_review_manifest_progress",
        "source_surface": "source_reconstruction_review_manifest",
        "claim_count": int(payload.get("claim_count") or 0),
        "review_progress": progress,
        "pending_review_count": int(progress.get("pending") or 0),
        "needs_revision_count": int(progress.get("needs_revision") or 0),
        "inconclusive_count": int(progress.get("inconclusive") or 0),
        "passed_count": int(progress.get("passed") or 0),
        "next_action_count": len(payload.get("next_actions") or []),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_legacy_semantic_review_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    progress = dict(payload.get("review_progress") or {})
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_semantic_review_manifest_progress",
        "source_surface": "legacy_semantic_review_manifest",
        "migration_dir": str(payload.get("migration_dir") or ""),
        "run_id": str(payload.get("run_id") or ""),
        "topic_count": int(payload.get("topic_count") or 0),
        "review_item_count": int(payload.get("review_item_count") or 0),
        "priority_counts": dict(payload.get("priority_counts") or {}),
        "review_progress": progress,
        "pending_count": int(payload.get("pending_count") or progress.get("pending") or 0),
        "needs_revision_count": int(payload.get("needs_revision_count") or progress.get("needs_revision") or 0),
        "inconclusive_count": int(payload.get("inconclusive_count") or progress.get("inconclusive") or 0),
        "passed_count": int(payload.get("passed_count") or progress.get("passed") or 0),
        "next_action_count": len(payload.get("next_actions") or []),
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
        "semantic_review_required": bool(payload.get("semantic_review_required", True)),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_final_readiness(payload: dict[str, Any]) -> dict[str, Any]:
    backlog = payload.get("content_backlog") if isinstance(payload.get("content_backlog"), dict) else {}
    legacy = backlog.get("legacy_semantic_review") if isinstance(backlog.get("legacy_semantic_review"), dict) else {}
    source = backlog.get("source_reconstruction") if isinstance(backlog.get("source_reconstruction"), dict) else {}
    legacy_progress = _legacy_progress(legacy)
    source_progress = dict(source.get("review_progress") or {})
    top_source_items = [
        item for item in source.get("top_incomplete_claims", []) if isinstance(item, dict)
    ]
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "final_engineering_readiness_progress",
        "source_surface": "final_engineering_readiness_audit",
        "completion_status": str(payload.get("completion_status") or ""),
        "kernel_capability_status": str(payload.get("kernel_capability_status") or ""),
        "content_backlog_status": str(payload.get("content_backlog_status") or ""),
        "blocking_gaps": list(payload.get("blocking_gaps") or []),
        "legacy_semantic_review": {
            "status": str(legacy.get("status") or ""),
            "run_id": str(legacy.get("run_id") or ""),
            "topic_count": int(legacy.get("topic_count") or 0),
            "review_item_count": int(legacy.get("review_item_count") or 0),
            "work_item_count": int(legacy.get("work_item_count") or 0),
            "open_human_checkpoint_count": int(legacy.get("open_human_checkpoint_count") or 0),
            "open_human_checkpoint_refs": [
                str(item.get("checkpoint_ref") or "")
                for item in legacy.get("open_human_checkpoints", [])
                if isinstance(item, dict) and str(item.get("checkpoint_ref") or "")
            ],
            "open_human_checkpoint_topics": [
                str(item.get("topic") or "")
                for item in legacy.get("open_human_checkpoints", [])
                if isinstance(item, dict) and str(item.get("topic") or "")
            ],
            "pass_readiness_counts": dict(legacy.get("pass_readiness_counts") or {}),
            "pass_blocker_counts": dict(legacy.get("pass_blocker_counts") or {}),
            "review_progress": legacy_progress,
            "pending_count": int(legacy.get("pending_count") or legacy_progress.get("pending") or 0),
            "needs_revision_count": int(
                legacy.get("needs_revision_count") or legacy_progress.get("needs_revision") or 0
            ),
            "inconclusive_count": int(
                legacy.get("inconclusive_count") or legacy_progress.get("inconclusive") or 0
            ),
            "passed_count": int(legacy.get("passed_count") or legacy_progress.get("passed") or 0),
            "semantic_lossless_proven": bool(legacy.get("semantic_lossless_proven", False)),
            "can_update_claim_trust": bool(legacy.get("can_update_claim_trust", False)),
        },
        "source_reconstruction": {
            "status": str(source.get("status") or ""),
            "active_claim_count": int(source.get("active_claim_count") or 0),
            "complete_claim_count": int(source.get("complete_claim_count") or 0),
            "incomplete_claim_count": int(source.get("incomplete_claim_count") or 0),
            "review_progress": source_progress,
            "pending_review_count": int(source_progress.get("pending") or 0),
            "top_incomplete_claim_refs": [
                f"source_reconstruction:{claim_id}"
                for claim_id in [str(item.get("claim_id") or "") for item in top_source_items]
                if claim_id
            ],
            "top_incomplete_claim_topics": [
                str(item.get("topic_id") or "")
                for item in top_source_items
                if str(item.get("topic_id") or "")
            ],
            "top_incomplete_review_statuses": [
                str(item.get("review_status") or "")
                for item in top_source_items
                if str(item.get("review_status") or "")
            ],
            "review_next_action_refs": [
                str(action) for action in list(source.get("review_next_actions") or [])[:5] if str(action)
            ],
            "can_update_claim_trust": bool(source.get("can_update_claim_trust", False)),
        },
        "backlog_refs": list(payload.get("backlog_refs") or []),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def _legacy_progress(legacy: dict[str, Any]) -> dict[str, int]:
    progress = legacy.get("review_progress")
    if isinstance(progress, dict):
        return {
            "passed": int(progress.get("passed") or 0),
            "inconclusive": int(progress.get("inconclusive") or 0),
            "needs_revision": int(progress.get("needs_revision") or 0),
            "pending": int(progress.get("pending") or 0),
        }
    return {
        "passed": int(legacy.get("passed_count") or 0),
        "inconclusive": int(legacy.get("inconclusive_count") or 0),
        "needs_revision": int(legacy.get("needs_revision_count") or 0),
        "pending": int(legacy.get("pending_count") or 0),
    }
