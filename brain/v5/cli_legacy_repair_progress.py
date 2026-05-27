"""Compact CLI progress payloads for legacy repair surfaces."""

from __future__ import annotations

from typing import Any


def compact_legacy_semantic_repair_plan(payload: dict[str, Any]) -> dict[str, Any]:
    repairs = [item for item in payload.get("proposed_repairs", []) if isinstance(item, dict)]
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_semantic_repair_plan_progress",
        "source_surface": "legacy_semantic_repair_plan",
        "run_id": str(payload.get("run_id") or ""),
        "migration_dir": str(payload.get("migration_dir") or ""),
        "topic": str(payload.get("topic") or ""),
        "active_claim_id": str(payload.get("active_claim_id") or ""),
        "repair_status": str(payload.get("repair_status") or ""),
        "proposed_repair_count": len(repairs),
        "proposed_repair_types": [
            str(item.get("repair_type") or "")
            for item in repairs
            if str(item.get("repair_type") or "")
        ],
        "required_actions": [str(action) for action in payload.get("required_actions", []) if str(action)],
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
        "semantic_review_required": bool(payload.get("semantic_review_required", True)),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_legacy_semantic_repair_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    top_items = [item for item in payload.get("items", []) if isinstance(item, dict)][:5]
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_semantic_repair_manifest_progress",
        "source_surface": "legacy_semantic_repair_manifest",
        "run_id": str(payload.get("run_id") or ""),
        "migration_dir": str(payload.get("migration_dir") or ""),
        "workspace": str(payload.get("workspace") or ""),
        "work_item_count": int(payload.get("work_item_count") or 0),
        "repair_status_counts": dict(payload.get("repair_status_counts") or {}),
        "proposed_repair_count": int(payload.get("proposed_repair_count") or 0),
        "required_action_counts": dict(payload.get("required_action_counts") or {}),
        "next_action_count": len(payload.get("next_actions") or []),
        "next_action_refs": [str(action) for action in payload.get("next_actions", [])[:5] if str(action)],
        "top_repair_item_topics": [
            str(item.get("topic") or "")
            for item in top_items
            if str(item.get("topic") or "")
        ],
        "top_repair_statuses": [
            str(item.get("repair_status") or "")
            for item in top_items
            if str(item.get("repair_status") or "")
        ],
        "top_required_actions": [
            [str(action) for action in item.get("required_actions", []) if str(action)]
            for item in top_items
        ],
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
        "semantic_review_required": bool(payload.get("semantic_review_required", True)),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_legacy_semantic_needs_revision_basis_queue(payload: dict[str, Any]) -> dict[str, Any]:
    top_items = [item for item in payload.get("items", []) if isinstance(item, dict)][:5]
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_semantic_needs_revision_basis_queue_progress",
        "source_surface": "legacy_semantic_needs_revision_basis_queue",
        "run_id": str(payload.get("run_id") or ""),
        "migration_dir": str(payload.get("migration_dir") or ""),
        "workspace": str(payload.get("workspace") or ""),
        "basis_item_count": int(payload.get("basis_item_count") or 0),
        "status_counts": dict(payload.get("status_counts") or {}),
        "required_action_counts": dict(payload.get("required_action_counts") or {}),
        "next_action_count": len(payload.get("next_actions") or []),
        "next_action_refs": [str(action) for action in payload.get("next_actions", [])[:5] if str(action)],
        "top_topics": [str(item.get("topic") or "") for item in top_items if str(item.get("topic") or "")],
        "top_latest_review_ids": [
            str(item.get("latest_review_id") or "")
            for item in top_items
            if str(item.get("latest_review_id") or "")
        ],
        "top_required_actions": [
            [str(action) for action in item.get("required_actions", []) if str(action)]
            for item in top_items
        ],
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
        "semantic_review_required": bool(payload.get("semantic_review_required", True)),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_legacy_semantic_needs_revision_basis_packet(payload: dict[str, Any]) -> dict[str, Any]:
    review_basis = payload.get("review_basis") if isinstance(payload.get("review_basis"), dict) else {}
    likely = [item for item in payload.get("likely_repair_basis", []) if isinstance(item, dict)]
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_semantic_needs_revision_basis_packet_progress",
        "source_surface": "legacy_semantic_needs_revision_basis_packet",
        "run_id": str(payload.get("run_id") or ""),
        "migration_dir": str(payload.get("migration_dir") or ""),
        "workspace": str(payload.get("workspace") or ""),
        "topic": str(payload.get("topic") or ""),
        "active_claim_id": str(payload.get("active_claim_id") or ""),
        "latest_review_id": str(payload.get("latest_review_id") or ""),
        "review_status": str(payload.get("review_status") or ""),
        "required_actions": [str(action) for action in payload.get("required_actions", []) if str(action)],
        "likely_repair_basis_count": len(likely),
        "likely_repair_basis_actions": [
            str(item.get("action") or "")
            for item in likely
            if str(item.get("action") or "")
        ],
        "reviewed_legacy_ref_count": len(review_basis.get("reviewed_legacy_refs") or []),
        "reviewed_typed_ref_count": len(review_basis.get("reviewed_typed_refs") or []),
        "evidence_ref_count": len(review_basis.get("evidence_refs") or []),
        "validation_result_id_count": len(review_basis.get("validation_result_ids") or []),
        "open_checkpoint_ref_count": len(review_basis.get("open_checkpoint_refs") or []),
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
        "semantic_review_required": bool(payload.get("semantic_review_required", True)),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_legacy_semantic_needs_revision_basis_obsidian_view_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    files = payload.get("files") if isinstance(payload.get("files"), dict) else {}
    view_files = [str(path) for path in files.values() if str(path)]
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_semantic_needs_revision_basis_obsidian_view_bundle_progress",
        "source_surface": "legacy_semantic_needs_revision_basis_obsidian_view_bundle",
        "view_dir": str(payload.get("view_dir") or ""),
        "migration_dir": str(payload.get("migration_dir") or ""),
        "workspace": str(payload.get("workspace") or ""),
        "basis_item_count": int(payload.get("basis_item_count") or 0),
        "status_counts": dict(payload.get("status_counts") or {}),
        "required_action_counts": dict(payload.get("required_action_counts") or {}),
        "next_action_count": len(payload.get("next_actions") or []),
        "next_action_refs": [str(action) for action in payload.get("next_actions", [])[:5] if str(action)],
        "view_file_count": len(view_files),
        "view_files": view_files,
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
        "semantic_review_required": bool(payload.get("semantic_review_required", True)),
        "derived_from": str(payload.get("derived_from") or ""),
        "truth_source": bool(payload.get("truth_source", False)),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }
