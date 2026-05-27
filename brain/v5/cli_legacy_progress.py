"""Compact CLI progress payloads for legacy migration surfaces."""

from __future__ import annotations

from typing import Any


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


def compact_legacy_semantic_review_worklist(payload: dict[str, Any]) -> dict[str, Any]:
    top_items = [
        item for item in payload.get("items", []) if isinstance(item, dict)
    ][:5]
    open_checkpoints = [
        item for item in payload.get("open_human_checkpoints", []) if isinstance(item, dict)
    ][:5]
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_semantic_review_worklist_progress",
        "source_surface": "legacy_semantic_review_worklist",
        "run_id": str(payload.get("run_id") or ""),
        "migration_dir": str(payload.get("migration_dir") or ""),
        "workspace": str(payload.get("workspace") or ""),
        "work_item_count": int(payload.get("work_item_count") or 0),
        "open_human_checkpoint_count": int(payload.get("open_human_checkpoint_count") or 0),
        "open_human_checkpoint_refs": [
            str(item.get("checkpoint_ref") or "")
            for item in open_checkpoints
            if str(item.get("checkpoint_ref") or "")
        ],
        "open_human_checkpoint_topics": [
            str(item.get("topic") or "")
            for item in open_checkpoints
            if str(item.get("topic") or "")
        ],
        "status_counts": dict(payload.get("status_counts") or {}),
        "pass_readiness_counts": dict(payload.get("pass_readiness_counts") or {}),
        "pass_blocker_counts": dict(payload.get("pass_blocker_counts") or {}),
        "blocking_class_counts": dict(payload.get("blocking_class_counts") or {}),
        "next_action_count": len(payload.get("next_actions") or []),
        "next_action_refs": _limited_strings(payload.get("next_actions")),
        "top_work_item_refs": [
            f"worklist_item:{topic}"
            for topic in [str(item.get("topic") or "") for item in top_items]
            if topic
        ],
        "top_work_item_topics": [
            str(item.get("topic") or "")
            for item in top_items
            if str(item.get("topic") or "")
        ],
        "top_work_item_active_claim_ids": [
            str(item.get("active_claim_id") or "")
            for item in top_items
            if str(item.get("active_claim_id") or "")
        ],
        "top_work_item_review_statuses": [
            str(item.get("review_status") or "")
            for item in top_items
            if str(item.get("review_status") or "")
        ],
        "top_work_item_blockers": [
            _limited_strings(
                item.get("pass_readiness", {}).get("blockers")
                if isinstance(item.get("pass_readiness"), dict)
                else []
            )
            for item in top_items
        ],
        "top_work_item_blocking_classes": [
            _limited_strings(item.get("blocking_classes")) for item in top_items
        ],
        "top_work_item_remaining_actions": [
            _limited_strings(
                item.get("pass_readiness", {}).get("remaining_actions")
                if isinstance(item.get("pass_readiness"), dict)
                else []
            )
            for item in top_items
        ],
        "top_work_item_review_focus": [
            _limited_strings(item.get("review_focus")) for item in top_items
        ],
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
        "semantic_review_required": bool(payload.get("semantic_review_required", True)),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_legacy_semantic_review_packet(payload: dict[str, Any]) -> dict[str, Any]:
    source = payload.get("source_reconstruction") if isinstance(payload.get("source_reconstruction"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_semantic_review_packet_progress",
        "source_surface": "legacy_semantic_review_packet",
        "run_id": str(payload.get("run_id") or ""),
        "migration_dir": str(payload.get("migration_dir") or ""),
        "topic": str(payload.get("topic") or ""),
        "active_claim_id": str(payload.get("active_claim_id") or ""),
        "semantic_review_status": str(payload.get("semantic_review_status") or ""),
        "review_status": str(payload.get("review_status") or ""),
        "review_priority": str(payload.get("review_priority") or ""),
        "latest_review_id": str(payload.get("latest_review_id") or ""),
        "source_reconstruction_status": str(source.get("status") or ""),
        "missing_components": _limited_strings(source.get("missing_components")),
        "review_basis_ref_count": len(payload.get("review_basis_refs") or []),
        "legacy_review_ref_count": len(payload.get("legacy_review_refs") or []),
        "review_checklist": _limited_strings(payload.get("review_checklist")),
        "recommended_actions": _limited_strings(payload.get("recommended_actions")),
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
        "semantic_review_required": bool(payload.get("semantic_review_required", True)),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_legacy_source_reconstruction_review_packet(payload: dict[str, Any]) -> dict[str, Any]:
    legacy_refs = payload.get("legacy_refs") if isinstance(payload.get("legacy_refs"), dict) else {}
    refs_by_prefix = legacy_refs.get("refs_by_prefix") if isinstance(legacy_refs.get("refs_by_prefix"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_source_reconstruction_review_packet_progress",
        "source_surface": "legacy_source_reconstruction_review_packet",
        "run_id": str(payload.get("run_id") or ""),
        "migration_dir": str(payload.get("migration_dir") or ""),
        "topic": str(payload.get("topic") or ""),
        "active_claim_id": str(payload.get("active_claim_id") or ""),
        "latest_review_id": str(payload.get("latest_review_id") or ""),
        "source_reconstruction_status": str(payload.get("source_reconstruction_status") or ""),
        "missing_components": _limited_strings(payload.get("missing_components"), limit=10),
        "component_review_count": int(payload.get("component_review_count") or 0),
        "review_result_cli": str(payload.get("review_result_cli") or ""),
        "reviewed_legacy_ref_count": len(legacy_refs.get("reviewed_legacy_refs") or []),
        "source_reconstruction_ref_count": len(legacy_refs.get("source_reconstruction_refs") or []),
        "refs_by_prefix_counts": {
            str(key): len(value) if isinstance(value, list) else 0
            for key, value in refs_by_prefix.items()
        },
        "recommended_actions": _limited_strings(payload.get("recommended_actions")),
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_legacy_source_reconstruction_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    top_items = [
        item for item in payload.get("items", []) if isinstance(item, dict)
    ][:5]
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_source_reconstruction_manifest_progress",
        "source_surface": "legacy_source_reconstruction_manifest",
        "run_id": str(payload.get("run_id") or ""),
        "migration_dir": str(payload.get("migration_dir") or ""),
        "work_item_count": int(payload.get("work_item_count") or 0),
        "proposed_repair_count": int(payload.get("proposed_repair_count") or 0),
        "repair_status_counts": dict(payload.get("repair_status_counts") or {}),
        "missing_component_counts": dict(payload.get("missing_component_counts") or {}),
        "required_action_counts": dict(payload.get("required_action_counts") or {}),
        "next_action_count": len(payload.get("next_actions") or []),
        "next_action_refs": _limited_strings(payload.get("next_actions")),
        "top_work_item_refs": [
            f"legacy_source_reconstruction:{topic}"
            for topic in [str(item.get("topic") or "") for item in top_items]
            if topic
        ],
        "top_work_item_topics": [
            str(item.get("topic") or "")
            for item in top_items
            if str(item.get("topic") or "")
        ],
        "top_work_item_active_claim_ids": [
            str(item.get("active_claim_id") or "")
            for item in top_items
            if str(item.get("active_claim_id") or "")
        ],
        "top_work_item_latest_review_ids": [
            str(item.get("latest_review_id") or "")
            for item in top_items
            if str(item.get("latest_review_id") or "")
        ],
        "top_work_item_repair_statuses": [
            str(item.get("repair_status") or "")
            for item in top_items
            if str(item.get("repair_status") or "")
        ],
        "top_work_item_missing_components": [
            _limited_strings(item.get("missing_components"), limit=10) for item in top_items
        ],
        "top_work_item_required_actions": [
            _limited_strings(item.get("required_actions"), limit=10) for item in top_items
        ],
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
        "semantic_review_required": bool(payload.get("semantic_review_required", True)),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_legacy_executable_evidence_packet(payload: dict[str, Any]) -> dict[str, Any]:
    evidence_items = [
        item for item in payload.get("evidence_items", []) if isinstance(item, dict)
    ][:5]
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_executable_evidence_packet_progress",
        "source_surface": "legacy_executable_evidence_packet",
        "run_id": str(payload.get("run_id") or ""),
        "migration_dir": str(payload.get("migration_dir") or ""),
        "workspace": str(payload.get("workspace") or ""),
        "topic_filter": str(payload.get("topic_filter") or ""),
        "evidence_item_count": int(payload.get("evidence_item_count") or 0),
        "executable_action_count": int(payload.get("executable_action_count") or 0),
        "next_action_count": len(payload.get("next_actions") or []),
        "next_action_refs": _limited_strings(payload.get("next_actions")),
        "top_evidence_item_refs": [
            f"legacy_executable_evidence:{topic}"
            for topic in [str(item.get("topic") or "") for item in evidence_items]
            if topic
        ],
        "top_evidence_item_topics": [
            str(item.get("topic") or "")
            for item in evidence_items
            if str(item.get("topic") or "")
        ],
        "top_evidence_item_active_claim_ids": [
            str(item.get("active_claim_id") or "")
            for item in evidence_items
            if str(item.get("active_claim_id") or "")
        ],
        "top_evidence_item_latest_review_ids": [
            str(item.get("latest_review_id") or "")
            for item in evidence_items
            if str(item.get("latest_review_id") or "")
        ],
        "top_evidence_item_review_statuses": [
            str(item.get("review_status") or "")
            for item in evidence_items
            if str(item.get("review_status") or "")
        ],
        "top_evidence_item_executable_actions": [
            _limited_strings(item.get("executable_actions"), limit=10) for item in evidence_items
        ],
        "top_evidence_item_validation_command_counts": [
            len(item.get("validation_commands") or []) for item in evidence_items
        ],
        "top_evidence_item_tool_run_command_counts": [
            len(item.get("tool_run_commands") or []) for item in evidence_items
        ],
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_legacy_source_metadata_repair_packet(payload: dict[str, Any]) -> dict[str, Any]:
    repair_items = [
        item for item in payload.get("repair_items", []) if isinstance(item, dict)
    ][:5]
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_source_metadata_repair_packet_progress",
        "source_surface": "legacy_source_metadata_repair_packet",
        "run_id": str(payload.get("run_id") or ""),
        "migration_dir": str(payload.get("migration_dir") or ""),
        "workspace": str(payload.get("workspace") or ""),
        "topic_filter": str(payload.get("topic_filter") or ""),
        "repair_item_count": int(payload.get("repair_item_count") or 0),
        "next_action_count": len(payload.get("next_actions") or []),
        "next_action_refs": _limited_strings(payload.get("next_actions")),
        "top_repair_item_refs": [
            f"legacy_source_metadata_repair:{topic}"
            for topic in [str(item.get("topic") or "") for item in repair_items]
            if topic
        ],
        "top_repair_item_topics": [
            str(item.get("topic") or "")
            for item in repair_items
            if str(item.get("topic") or "")
        ],
        "top_repair_item_active_claim_ids": [
            str(item.get("active_claim_id") or "")
            for item in repair_items
            if str(item.get("active_claim_id") or "")
        ],
        "top_repair_item_latest_review_ids": [
            str(item.get("latest_review_id") or "")
            for item in repair_items
            if str(item.get("latest_review_id") or "")
        ],
        "top_repair_item_review_statuses": [
            str(item.get("review_status") or "")
            for item in repair_items
            if str(item.get("review_status") or "")
        ],
        "top_repair_item_source_metadata_actions": [
            _limited_strings(item.get("source_metadata_actions"), limit=10) for item in repair_items
        ],
        "top_repair_item_reference_location_command_counts": [
            len(item.get("reference_location_commands") or []) for item in repair_items
        ],
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


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


def compact_legacy_human_checkpoint_packet(payload: dict[str, Any]) -> dict[str, Any]:
    checkpoint_items = [
        item for item in payload.get("checkpoint_items", []) if isinstance(item, dict)
    ]
    open_items = [
        item for item in checkpoint_items if item.get("mode") == "decide_open_checkpoint"
    ][:5]
    pending_items = [
        item for item in checkpoint_items if item.get("mode") == "request_checkpoint"
    ][:5]
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_human_checkpoint_packet_progress",
        "source_surface": "legacy_human_checkpoint_packet",
        "run_id": str(payload.get("run_id") or ""),
        "migration_dir": str(payload.get("migration_dir") or ""),
        "workspace": str(payload.get("workspace") or ""),
        "topic_filter": str(payload.get("topic_filter") or ""),
        "checkpoint_item_count": int(payload.get("checkpoint_item_count") or 0),
        "open_decision_count": int(payload.get("open_decision_count") or 0),
        "pending_request_count": int(payload.get("pending_request_count") or 0),
        "open_checkpoint_refs": [
            f"human_checkpoint:{checkpoint_id}"
            for checkpoint_id in [str(item.get("checkpoint_id") or "") for item in open_items]
            if checkpoint_id
        ],
        "open_checkpoint_topics": [
            str(item.get("topic") or "")
            for item in open_items
            if str(item.get("topic") or "")
        ],
        "pending_checkpoint_actions": [
            str(item.get("action") or "")
            for item in pending_items
            if str(item.get("action") or "")
        ],
        "pending_checkpoint_topics": [
            str(item.get("topic") or "")
            for item in pending_items
            if str(item.get("topic") or "")
        ],
        "next_action_count": len(payload.get("next_actions") or []),
        "next_action_refs": _limited_strings(payload.get("next_actions")),
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
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
