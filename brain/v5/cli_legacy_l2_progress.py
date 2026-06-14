"""Compact CLI progress payloads for legacy L2 surfaces."""

from __future__ import annotations

from typing import Any


def compact_legacy_l2_typed_migration_packet(payload: dict[str, Any]) -> dict[str, Any]:
    review_groups = payload.get("review_groups") if isinstance(payload.get("review_groups"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_l2_typed_migration_packet_progress",
        "source_surface": "legacy_l2_typed_migration_packet",
        "legacy_l2_dir": str(payload.get("legacy_l2_dir") or ""),
        "legacy_shape": str(payload.get("legacy_shape") or ""),
        "typed_migration_status": str(payload.get("typed_migration_status") or ""),
        "work_item_count": int(payload.get("work_item_count") or 0),
        "work_item_counts_by_kind": dict(payload.get("work_item_counts_by_kind") or {}),
        "review_group_counts": {
            str(surface): int(group.get("count") or 0)
            for surface, group in review_groups.items()
            if isinstance(group, dict)
        },
        "next_action_count": len(payload.get("next_actions") or []),
        "next_action_refs": _limited_strings(payload.get("next_actions")),
        "top_review_group_surfaces": [
            str(surface)
            for surface in review_groups.keys()
            if str(surface)
        ][:5],
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_legacy_l2_graph_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    maturity = payload.get("obsidian_view_maturity") if isinstance(payload.get("obsidian_view_maturity"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_l2_graph_manifest_progress",
        "source_surface": "legacy_l2_graph_manifest",
        "legacy_l2_dir": str(payload.get("legacy_l2_dir") or ""),
        "legacy_shape": str(payload.get("legacy_shape") or ""),
        "typed_migration_status": str(payload.get("typed_migration_status") or ""),
        "migration_worklist_status": str(payload.get("migration_worklist_status") or ""),
        "counts": dict(payload.get("counts") or {}),
        "entries_by_role": dict(payload.get("entries_by_role") or {}),
        "entries_by_status": dict(payload.get("entries_by_status") or {}),
        "work_item_count": int(payload.get("work_item_count") or 0),
        "work_item_counts_by_kind": dict(payload.get("work_item_counts_by_kind") or {}),
        "obsidian_view_maturity_status": str(maturity.get("status") or ""),
        "core_obsidian_views_available": bool(maturity.get("core_views_available", False)),
        "available_obsidian_view_targets": _limited_strings(maturity.get("available_targets"), limit=10),
        "missing_core_obsidian_view_targets": _limited_strings(maturity.get("missing_core_targets"), limit=10),
        "next_action_count": len(payload.get("next_actions") or []),
        "next_action_refs": _limited_strings(payload.get("next_actions")),
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_legacy_l2_obsidian_view_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    maturity = payload.get("obsidian_view_maturity") if isinstance(payload.get("obsidian_view_maturity"), dict) else {}
    files = payload.get("files") if isinstance(payload.get("files"), dict) else {}
    view_files = [
        str(files.get("overview") or ""),
        str(files.get("entries_index") or ""),
        str(files.get("graph_index") or ""),
        str(payload.get("worklist_file") or ""),
    ]
    view_files = [path for path in view_files if path]
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_l2_obsidian_view_bundle_progress",
        "source_surface": "legacy_l2_obsidian_view_bundle",
        "view_dir": str(payload.get("view_dir") or ""),
        "legacy_l2_dir": str(payload.get("legacy_l2_dir") or ""),
        "legacy_entry_count": int(payload.get("legacy_entry_count") or 0),
        "memory_entry_count": int(payload.get("memory_entry_count") or 0),
        "migration_work_item_count": int(payload.get("migration_work_item_count") or 0),
        "entries_by_role": dict(payload.get("entries_by_role") or {}),
        "entries_by_status": dict(payload.get("entries_by_status") or {}),
        "graph_counts": dict(payload.get("graph_counts") or {}),
        "obsidian_view_maturity_status": str(maturity.get("status") or ""),
        "core_obsidian_views_available": bool(maturity.get("core_views_available", False)),
        "available_obsidian_view_targets": _limited_strings(maturity.get("available_targets"), limit=10),
        "missing_core_obsidian_view_targets": _limited_strings(maturity.get("missing_core_targets"), limit=10),
        "next_action_count": len(payload.get("next_actions") or []),
        "next_action_refs": _limited_strings(payload.get("next_actions")),
        "view_file_count": len(view_files),
        "view_files": view_files,
        "derived_from": str(payload.get("derived_from") or ""),
        "truth_source": bool(payload.get("truth_source", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_canonical_legacy_l2_seed_audit(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "canonical_legacy_l2_seed_audit_progress",
        "source_surface": "canonical_legacy_l2_seed_audit",
        "canonical_store": str(payload.get("canonical_store") or ""),
        "total_memory_file_count": int(payload.get("total_memory_file_count") or 0),
        "legacy_seed_count": int(payload.get("legacy_seed_count") or 0),
        "active_legacy_seed_count": int(payload.get("active_legacy_seed_count") or 0),
        "legacy_seed_topic_count": int(payload.get("legacy_seed_topic_count") or 0),
        "quarantine_status": str(payload.get("quarantine_status") or ""),
        "status_counts": dict(payload.get("status_counts") or {}),
        "top_topics": _top_mapping_keys(payload.get("topic_counts")),
        "memory_kind_counts": dict(payload.get("memory_kind_counts") or {}),
        "next_action_count": len(payload.get("next_actions") or []),
        "next_action_refs": _limited_strings(payload.get("next_actions")),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def _limited_strings(value: Any, *, limit: int = 5) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value[:limit] if str(item)]


def _top_mapping_keys(value: Any, *, limit: int = 10) -> list[str]:
    if not isinstance(value, dict):
        return []
    return [
        str(key)
        for key, _count in sorted(
            value.items(),
            key=lambda item: (-int(item[1] or 0), str(item[0])),
        )[:limit]
        if str(key)
    ]
