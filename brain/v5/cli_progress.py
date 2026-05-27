"""Compact CLI progress payloads for high-volume audit surfaces."""

from __future__ import annotations

from typing import Any


def compact_source_reconstruction_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    incomplete_items = [
        item
        for item in payload.get("items", [])
        if isinstance(item, dict) and item.get("status") == "incomplete"
    ][:5]
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "source_reconstruction_manifest_progress",
        "source_surface": "source_reconstruction_manifest",
        "claim_count": int(payload.get("claim_count") or 0),
        "complete_claim_count": int(payload.get("complete_claim_count") or 0),
        "incomplete_claim_count": int(payload.get("incomplete_claim_count") or 0),
        "missing_component_counts": dict(payload.get("missing_component_counts") or {}),
        "next_action_count": len(payload.get("next_actions") or []),
        "next_action_refs": _limited_strings(payload.get("next_actions")),
        "top_incomplete_claim_refs": [
            f"source_reconstruction:{claim_id}"
            for claim_id in [str(item.get("claim_id") or "") for item in incomplete_items]
            if claim_id
        ],
        "top_incomplete_claim_topics": [
            str(item.get("topic_id") or "")
            for item in incomplete_items
            if str(item.get("topic_id") or "")
        ],
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_source_reconstruction_review_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    progress = dict(payload.get("review_progress") or {})
    top_review_items = [
        item
        for item in payload.get("items", [])
        if isinstance(item, dict)
        and item.get("review_status") in {"pending", "needs_revision", "inconclusive"}
    ][:5]
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
        "next_action_refs": _limited_strings(payload.get("next_actions")),
        "top_review_claim_refs": [
            f"source_reconstruction_review:{claim_id}"
            for claim_id in [str(item.get("claim_id") or "") for item in top_review_items]
            if claim_id
        ],
        "top_review_claim_topics": [
            str(item.get("topic_id") or "")
            for item in top_review_items
            if str(item.get("topic_id") or "")
        ],
        "top_review_statuses": [
            str(item.get("review_status") or "")
            for item in top_review_items
            if str(item.get("review_status") or "")
        ],
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }


def compact_source_reconstruction_review_packet(payload: dict[str, Any]) -> dict[str, Any]:
    missing = _limited_strings(payload.get("missing_components"), limit=10)
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "source_reconstruction_review_packet_progress",
        "source_surface": "source_reconstruction_review_packet",
        "topic_id": str(payload.get("topic_id") or ""),
        "claim_id": str(payload.get("claim_id") or ""),
        "source_reconstruction_status": "incomplete" if missing else "complete",
        "missing_components": missing,
        "satisfied_components": _limited_strings(payload.get("satisfied_components"), limit=10),
        "component_review_count": len(payload.get("component_reviews") or []),
        "review_result_cli": (
            f"aitp-v5 source reconstruction-review-result --claim {payload.get('claim_id') or ''} "
            "--status <passed|needs_revision|inconclusive> "
            "--reviewed-component <component> --basis-ref <typed-or-source-ref> "
            "--summary <source reconstruction review basis>"
        ),
        "requires_human_or_adversarial_review": bool(
            payload.get("requires_human_or_adversarial_review", False)
        ),
        "recommended_actions": _limited_strings(payload.get("recommended_actions")),
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


def compact_final_readiness(payload: dict[str, Any]) -> dict[str, Any]:
    backlog = payload.get("content_backlog") if isinstance(payload.get("content_backlog"), dict) else {}
    capabilities = (
        payload.get("kernel_capabilities")
        if isinstance(payload.get("kernel_capabilities"), dict)
        else {}
    )
    legacy = backlog.get("legacy_semantic_review") if isinstance(backlog.get("legacy_semantic_review"), dict) else {}
    source = backlog.get("source_reconstruction") if isinstance(backlog.get("source_reconstruction"), dict) else {}
    knowledge = (
        capabilities.get("knowledge_stack")
        if isinstance(capabilities.get("knowledge_stack"), dict)
        else {}
    )
    replay = (
        capabilities.get("long_term_replay")
        if isinstance(capabilities.get("long_term_replay"), dict)
        else {}
    )
    natural = (
        capabilities.get("natural_interaction")
        if isinstance(capabilities.get("natural_interaction"), dict)
        else {}
    )
    host = (
        capabilities.get("host_integration")
        if isinstance(capabilities.get("host_integration"), dict)
        else {}
    )
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
            "blocking_class_counts": dict(legacy.get("blocking_class_counts") or {}),
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
        "knowledge_stack": {
            "obsidian_view_surface": str(knowledge.get("obsidian_view_surface") or ""),
            "obsidian_typed_graph_supported": bool(
                knowledge.get("obsidian_typed_graph_supported", False)
            ),
            "memory_entry_count": int(knowledge.get("memory_entry_count") or 0),
            "active_memory_entry_count": int(knowledge.get("active_memory_entry_count") or 0),
            "physics_object_count": int(knowledge.get("physics_object_count") or 0),
            "object_relation_count": int(knowledge.get("object_relation_count") or 0),
            "sensemaking_report_count": int(knowledge.get("sensemaking_report_count") or 0),
        },
        "long_term_replay": {
            "surface": str(replay.get("surface") or ""),
            "workspace_refresh_surface": str(replay.get("workspace_refresh_surface") or ""),
            "legacy_semantic_backlog_surface": str(
                replay.get("legacy_semantic_backlog_surface") or ""
            ),
            "legacy_source_reconstruction_backlog_surface": str(
                replay.get("legacy_source_reconstruction_backlog_surface") or ""
            ),
            "legacy_semantic_repair_surface": str(
                replay.get("legacy_semantic_repair_surface") or ""
            ),
            "legacy_human_checkpoint_backlog_surface": str(
                replay.get("legacy_human_checkpoint_backlog_surface") or ""
            ),
            "host_startup_semantic_repair_supported": bool(
                replay.get("host_startup_semantic_repair_supported", False)
            ),
            "host_startup_checkpoint_packet_supported": bool(
                replay.get("host_startup_checkpoint_packet_supported", False)
            ),
        },
        "natural_interaction": {
            "surface": str(natural.get("surface") or ""),
            "recording_worklist_surface": str(natural.get("recording_worklist_surface") or ""),
            "host_refresh_worklist_supported": bool(
                natural.get("host_refresh_worklist_supported", False)
            ),
            "recording_decision_modes": _limited_strings(
                natural.get("recording_decision_modes"),
                limit=10,
            ),
        },
        "host_integration": {
            "priority_hosts": _limited_strings(host.get("priority_hosts"), limit=10),
            "deferred_hosts": _limited_strings(host.get("deferred_hosts"), limit=10),
            "priority_host_batch_surface": str(host.get("priority_host_batch_surface") or ""),
            "priority_host_batch_cli": str(host.get("priority_host_batch_cli") or ""),
            "priority_host_loop_count": len(host.get("priority_host_production_loops") or []),
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


def _limited_strings(value: Any, *, limit: int = 5) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value[:limit] if str(item)]
