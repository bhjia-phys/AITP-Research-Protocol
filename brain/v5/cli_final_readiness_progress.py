"""Compact progress projection for final readiness audits."""

from __future__ import annotations

from typing import Any


def compact_final_readiness(payload: dict[str, Any]) -> dict[str, Any]:
    backlog = payload.get("content_backlog") if isinstance(payload.get("content_backlog"), dict) else {}
    capabilities = payload.get("kernel_capabilities") if isinstance(payload.get("kernel_capabilities"), dict) else {}
    legacy = backlog.get("legacy_semantic_review") if isinstance(backlog.get("legacy_semantic_review"), dict) else {}
    source = backlog.get("source_reconstruction") if isinstance(backlog.get("source_reconstruction"), dict) else {}
    knowledge = capabilities.get("knowledge_stack") if isinstance(capabilities.get("knowledge_stack"), dict) else {}
    source_stack = capabilities.get("source_stack") if isinstance(capabilities.get("source_stack"), dict) else {}
    replay = capabilities.get("long_term_replay") if isinstance(capabilities.get("long_term_replay"), dict) else {}
    natural = capabilities.get("natural_interaction") if isinstance(capabilities.get("natural_interaction"), dict) else {}
    host = capabilities.get("host_integration") if isinstance(capabilities.get("host_integration"), dict) else {}
    legacy_progress = _legacy_progress(legacy)
    source_progress = dict(source.get("review_progress") or {})
    top_source_items = [item for item in source.get("top_incomplete_claims", []) if isinstance(item, dict)]
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
            "obsidian_typed_graph_supported": bool(knowledge.get("obsidian_typed_graph_supported", False)),
            "memory_entry_count": int(knowledge.get("memory_entry_count") or 0),
            "active_memory_entry_count": int(knowledge.get("active_memory_entry_count") or 0),
            "physics_object_count": int(knowledge.get("physics_object_count") or 0),
            "object_relation_count": int(knowledge.get("object_relation_count") or 0),
            "sensemaking_report_count": int(knowledge.get("sensemaking_report_count") or 0),
        },
        "source_stack": {
            "coverage_manifest_surface": str(source_stack.get("coverage_manifest_surface") or ""),
            "host_refresh_coverage_manifest_supported": bool(
                source_stack.get("host_refresh_coverage_manifest_supported", False)
            ),
        },
        "long_term_replay": {
            "surface": str(replay.get("surface") or ""),
            "workspace_refresh_surface": str(replay.get("workspace_refresh_surface") or ""),
            "legacy_semantic_backlog_surface": str(replay.get("legacy_semantic_backlog_surface") or ""),
            "legacy_source_reconstruction_backlog_surface": str(
                replay.get("legacy_source_reconstruction_backlog_surface") or ""
            ),
            "legacy_semantic_repair_surface": str(replay.get("legacy_semantic_repair_surface") or ""),
            "legacy_executable_evidence_surface": str(replay.get("legacy_executable_evidence_surface") or ""),
            "legacy_human_checkpoint_backlog_surface": str(
                replay.get("legacy_human_checkpoint_backlog_surface") or ""
            ),
            "host_startup_semantic_repair_supported": bool(
                replay.get("host_startup_semantic_repair_supported", False)
            ),
            "host_startup_executable_evidence_supported": bool(
                replay.get("host_startup_executable_evidence_supported", False)
            ),
            "host_startup_checkpoint_packet_supported": bool(
                replay.get("host_startup_checkpoint_packet_supported", False)
            ),
        },
        "natural_interaction": {
            "surface": str(natural.get("surface") or ""),
            "recording_worklist_surface": str(natural.get("recording_worklist_surface") or ""),
            "host_refresh_worklist_supported": bool(natural.get("host_refresh_worklist_supported", False)),
            "recording_decision_modes": _limited_strings(natural.get("recording_decision_modes"), limit=10),
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
            "pending": int(progress.get("pending") or 0),
            "needs_revision": int(progress.get("needs_revision") or 0),
            "inconclusive": int(progress.get("inconclusive") or 0),
            "passed": int(progress.get("passed") or 0),
        }
    return {
        "pending": int(legacy.get("pending_count") or 0),
        "needs_revision": int(legacy.get("needs_revision_count") or 0),
        "inconclusive": int(legacy.get("inconclusive_count") or 0),
        "passed": int(legacy.get("passed_count") or 0),
    }


def _limited_strings(value: Any, *, limit: int = 5) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value[:limit] if str(item)]
