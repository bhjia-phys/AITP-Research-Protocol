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


def compact_canonical_legacy_l2_seed_review_worklist(payload: dict[str, Any]) -> dict[str, Any]:
    top_groups = [group for group in payload.get("review_groups", []) if isinstance(group, dict)][:5]
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "canonical_legacy_l2_seed_review_worklist_progress",
        "source_surface": "canonical_legacy_l2_seed_review_worklist",
        "canonical_store": str(payload.get("canonical_store") or ""),
        "legacy_seed_count": int(payload.get("legacy_seed_count") or 0),
        "active_legacy_seed_count": int(payload.get("active_legacy_seed_count") or 0),
        "legacy_seed_topic_count": int(payload.get("legacy_seed_topic_count") or 0),
        "review_group_count": int(payload.get("review_group_count") or 0),
        "open_review_group_count": int(payload.get("open_review_group_count") or 0),
        "reviewed_group_count": int(payload.get("reviewed_group_count") or 0),
        "terminal_review_group_count": int(payload.get("terminal_review_group_count") or 0),
        "semantic_subgroup_reviewed_count": int(payload.get("semantic_subgroup_reviewed_count") or 0),
        "semantic_subgroup_terminal_review_count": int(payload.get("semantic_subgroup_terminal_review_count") or 0),
        "semantic_subgroup_open_review_count": int(payload.get("semantic_subgroup_open_review_count") or 0),
        "visible_review_group_count": int(payload.get("visible_review_group_count") or 0),
        "topic_scope_mismatch_count": int(payload.get("topic_scope_mismatch_count") or 0),
        "global_l2_seed_count": int(payload.get("global_l2_seed_count") or 0),
        "review_status_counts": dict(payload.get("review_status_counts") or {}),
        "review_decision_counts": dict(payload.get("review_decision_counts") or {}),
        "semantic_subgroup_review_status_counts": dict(payload.get("semantic_subgroup_review_status_counts") or {}),
        "semantic_subgroup_review_decision_counts": dict(payload.get("semantic_subgroup_review_decision_counts") or {}),
        "review_group_blocking_class_counts": dict(payload.get("review_group_blocking_class_counts") or {}),
        "top_group_ids": _group_strings(top_groups, "group_id"),
        "top_group_topics": _group_strings(top_groups, "topic_id"),
        "top_group_target_topics": _group_strings(top_groups, "target_topic_id"),
        "top_group_source_claim_ids": _group_strings(top_groups, "source_claim_id"),
        "top_group_memory_roles": _group_strings(top_groups, "memory_role"),
        "top_group_semantic_mix_detected": [
            bool(group.get("semantic_mix_detected", False))
            for group in top_groups
        ],
        "top_group_semantic_subgroup_counts": [
            int(group.get("semantic_subgroup_count") or 0)
            for group in top_groups
        ],
        "top_group_semantic_subgroups": [
            _semantic_subgroup_strings(group)
            for group in top_groups
        ],
        "top_group_semantic_subgroup_review_progress": [
            _semantic_subgroup_review_progress(group)
            for group in top_groups
        ],
        "top_group_blocking_classes": [
            _limited_strings(group.get("blocking_classes"))
            for group in top_groups
        ],
        "top_group_review_focus": [
            _limited_strings(group.get("review_focus"))
            for group in top_groups
        ],
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


def _group_strings(groups: list[dict[str, Any]], key: str) -> list[str]:
    return [
        str(group.get(key) or "")
        for group in groups
        if str(group.get(key) or "")
    ]


def _semantic_subgroup_strings(group: dict[str, Any], *, limit: int = 5) -> list[str]:
    subgroups = group.get("semantic_subgroups")
    if not isinstance(subgroups, list):
        return []
    values: list[str] = []
    for item in subgroups[:limit]:
        if not isinstance(item, dict):
            continue
        source_family = str(item.get("source_family") or "")
        source_object_id = str(item.get("source_object_id") or "")
        seed_count = int(item.get("seed_count") or 0)
        if source_family or source_object_id:
            values.append(f"{source_family}:{source_object_id}:{seed_count}")
    return values


def _semantic_subgroup_review_progress(group: dict[str, Any], *, limit: int = 5) -> list[str]:
    subgroups = group.get("semantic_subgroups")
    if not isinstance(subgroups, list):
        return []
    values: list[str] = []
    sorted_subgroups = sorted(
        (item for item in subgroups if isinstance(item, dict)),
        key=_semantic_subgroup_review_sort_key,
    )
    for item in sorted_subgroups[:limit]:
        if not isinstance(item, dict):
            continue
        source_family = str(item.get("source_family") or "")
        source_object_id = str(item.get("source_object_id") or "")
        status = str(item.get("review_status") or "pending")
        decision = str(item.get("review_decision") or "pending")
        if source_family or source_object_id:
            values.append(f"{source_family}:{source_object_id}:{status}/{decision}")
    return values


def _semantic_subgroup_review_sort_key(item: dict[str, Any]) -> tuple[bool, bool, str, str]:
    status = str(item.get("review_status") or "pending")
    decision = str(item.get("review_decision") or "pending")
    reviewed = bool(item.get("latest_review_result")) or status != "pending" or decision != "pending"
    terminal = bool(item.get("terminal_review_recorded"))
    return (
        not reviewed,
        not terminal,
        str(item.get("source_family") or ""),
        str(item.get("source_object_id") or ""),
    )


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
