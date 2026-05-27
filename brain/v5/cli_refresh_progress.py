"""Compact CLI progress payload for workspace refresh."""

from __future__ import annotations

from typing import Any


def compact_workspace_replay_packet(payload: dict[str, Any]) -> dict[str, Any]:
    backlog = (
        payload.get("workspace_backlog_summary")
        if isinstance(payload.get("workspace_backlog_summary"), dict)
        else {}
    )
    source = (
        backlog.get("source_reconstruction")
        if isinstance(backlog.get("source_reconstruction"), dict)
        else {}
    )
    resume = backlog.get("resume_attention") if isinstance(backlog.get("resume_attention"), dict) else {}
    source_stack = (
        backlog.get("source_stack_coverage")
        if isinstance(backlog.get("source_stack_coverage"), dict)
        else {}
    )
    entries = [entry for entry in payload.get("entries", []) if isinstance(entry, dict)]
    source_records = payload.get("source_records") if isinstance(payload.get("source_records"), dict) else {}
    compact = {
        "ok": bool(payload.get("ok", True)),
        "kind": "workspace_replay_packet_progress",
        "source_surface": "workspace_replay_packet",
        "entry_count": int(payload.get("entry_count") or 0),
        "attention_count": int(payload.get("attention_count") or 0),
        "active_session_count": int(backlog.get("active_session_count") or 0),
        "active_topic_count": int(backlog.get("active_topic_count") or 0),
        "active_claim_count": int(backlog.get("active_claim_count") or 0),
        "source_reconstruction": {
            "complete_claim_count": int(source.get("complete_claim_count") or 0),
            "incomplete_claim_count": int(source.get("incomplete_claim_count") or 0),
            "missing_component_counts": dict(source.get("missing_component_counts") or {}),
            "review_status_counts": dict(source.get("review_status_counts") or {}),
            "top_incomplete_claim_refs": [
                f"source_reconstruction:{claim_id}"
                for claim_id in [
                    str(item.get("claim_id") or "")
                    for item in source.get("top_incomplete_claims", [])
                    if isinstance(item, dict)
                ]
                if claim_id
            ],
        },
        "resume_attention": {
            "attention_count": int(resume.get("attention_count") or 0),
            "top_session_refs": [
                f"session:{session_id}"
                for session_id in [
                    str(item.get("session_id") or "")
                    for item in resume.get("top_items", [])
                    if isinstance(item, dict)
                ]
                if session_id
            ],
        },
        "source_stack_coverage": {
            "claim_count": int(source_stack.get("claim_count") or 0),
            "coverage_status_counts": dict(source_stack.get("coverage_status_counts") or {}),
            "missing_required_output_counts": dict(source_stack.get("missing_required_output_counts") or {}),
            "source_component_gap_counts": dict(source_stack.get("source_component_gap_counts") or {}),
            "source_review_status_counts": dict(source_stack.get("source_review_status_counts") or {}),
        },
        "source_record_counts": {
            str(key): len(value) if isinstance(value, list) else 0
            for key, value in source_records.items()
        },
        "top_entry_refs": [
            f"replay_entry:{entry.get('session_id')}:{entry.get('claim_id')}"
            for entry in entries[:5]
            if str(entry.get("session_id") or "") and str(entry.get("claim_id") or "")
        ],
        "derived_from": str(payload.get("derived_from") or ""),
        "truth_source": bool(payload.get("truth_source", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }
    if "legacy_semantic_review" in backlog:
        legacy = backlog.get("legacy_semantic_review") if isinstance(backlog.get("legacy_semantic_review"), dict) else {}
        compact["legacy_semantic_review"] = {
            "review_item_count": int(legacy.get("review_item_count") or 0),
            "review_progress": dict(legacy.get("review_progress") or {}),
            "open_human_checkpoint_count": int(legacy.get("open_human_checkpoint_count") or 0),
            "semantic_lossless_proven": bool(legacy.get("semantic_lossless_proven", False)),
        }
    if "legacy_source_reconstruction" in backlog:
        legacy_source = (
            backlog.get("legacy_source_reconstruction")
            if isinstance(backlog.get("legacy_source_reconstruction"), dict)
            else {}
        )
        compact["legacy_source_reconstruction"] = {
            "work_item_count": int(legacy_source.get("work_item_count") or 0),
            "repair_status_counts": dict(legacy_source.get("repair_status_counts") or {}),
            "proposed_repair_count": int(legacy_source.get("proposed_repair_count") or 0),
        }
    if "legacy_semantic_repair" in backlog:
        repair = backlog.get("legacy_semantic_repair") if isinstance(backlog.get("legacy_semantic_repair"), dict) else {}
        compact["legacy_semantic_repair"] = {
            "work_item_count": int(repair.get("work_item_count") or 0),
            "repair_status_counts": dict(repair.get("repair_status_counts") or {}),
            "proposed_repair_count": int(repair.get("proposed_repair_count") or 0),
            "required_action_counts": dict(repair.get("required_action_counts") or {}),
        }
    if "legacy_semantic_needs_revision_basis" in backlog:
        basis = (
            backlog.get("legacy_semantic_needs_revision_basis")
            if isinstance(backlog.get("legacy_semantic_needs_revision_basis"), dict)
            else {}
        )
        compact["legacy_semantic_needs_revision_basis"] = {
            "basis_item_count": int(basis.get("basis_item_count") or 0),
            "status_counts": dict(basis.get("status_counts") or {}),
            "required_action_counts": dict(basis.get("required_action_counts") or {}),
        }
    if "legacy_human_checkpoints" in backlog:
        checkpoints = (
            backlog.get("legacy_human_checkpoints")
            if isinstance(backlog.get("legacy_human_checkpoints"), dict)
            else {}
        )
        compact["legacy_human_checkpoints"] = {
            "checkpoint_item_count": int(checkpoints.get("checkpoint_item_count") or 0),
            "open_decision_count": int(checkpoints.get("open_decision_count") or 0),
            "pending_request_count": int(checkpoints.get("pending_request_count") or 0),
            "semantic_lossless_proven": bool(checkpoints.get("semantic_lossless_proven", False)),
        }
    return compact


def compact_workspace_refresh(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("workspace_summary") if isinstance(payload.get("workspace_summary"), dict) else {}
    replay = payload.get("workspace_replay") if isinstance(payload.get("workspace_replay"), dict) else {}
    backlog = (
        replay.get("workspace_backlog_summary")
        if isinstance(replay.get("workspace_backlog_summary"), dict)
        else {}
    )
    source = (
        backlog.get("source_reconstruction")
        if isinstance(backlog.get("source_reconstruction"), dict)
        else {}
    )
    source_stack_coverage = (
        payload.get("source_stack_coverage")
        if isinstance(payload.get("source_stack_coverage"), dict)
        else {}
    )
    semantic_repair = (
        backlog.get("legacy_semantic_repair")
        if isinstance(backlog.get("legacy_semantic_repair"), dict)
        else {}
    )
    needs_revision_basis = (
        backlog.get("legacy_semantic_needs_revision_basis")
        if isinstance(backlog.get("legacy_semantic_needs_revision_basis"), dict)
        else {}
    )
    executable = (
        backlog.get("legacy_executable_evidence")
        if isinstance(backlog.get("legacy_executable_evidence"), dict)
        else {}
    )
    source_review = (
        payload.get("source_reconstruction_obsidian_view")
        if isinstance(payload.get("source_reconstruction_obsidian_view"), dict)
        else {}
    )
    l2_view = (
        payload.get("l2_obsidian_view")
        if isinstance(payload.get("l2_obsidian_view"), dict)
        else {}
    )
    interaction = (
        payload.get("workspace_interaction_preview")
        if isinstance(payload.get("workspace_interaction_preview"), dict)
        else {}
    )
    interaction_worklist = (
        payload.get("interaction_recording_worklist")
        if isinstance(payload.get("interaction_recording_worklist"), dict)
        else {}
    )
    legacy = (
        payload.get("legacy_semantic_review_obsidian_view")
        if isinstance(payload.get("legacy_semantic_review_obsidian_view"), dict)
        else {}
    )
    legacy_source = (
        payload.get("legacy_source_reconstruction_obsidian_view")
        if isinstance(payload.get("legacy_source_reconstruction_obsidian_view"), dict)
        else {}
    )
    checkpoints = (
        payload.get("legacy_human_checkpoint_obsidian_view")
        if isinstance(payload.get("legacy_human_checkpoint_obsidian_view"), dict)
        else {}
    )
    compact = {
        "ok": bool(payload.get("ok", True)),
        "kind": "workspace_refresh_progress",
        "source_surface": "workspace_refresh_bundle",
        "refreshed_surface_count": len(payload.get("refreshed_surfaces") or []),
        "refreshed_surfaces": list(payload.get("refreshed_surfaces") or []),
        "workspace_summary": {
            "session_count": int(summary.get("session_count") or 0),
            "active_claim_count": int(summary.get("active_claim_count") or 0),
            "memory_entry_count": int(summary.get("memory_entry_count") or 0),
        },
        "workspace_replay": {
            "entry_count": int(replay.get("entry_count") or 0),
            "attention_count": int(replay.get("attention_count") or 0),
            "active_session_count": int(backlog.get("active_session_count") or 0),
        },
        "source_stack_coverage": {
            "claim_count": int(source_stack_coverage.get("claim_count") or 0),
            "coverage_status_counts": dict(source_stack_coverage.get("coverage_status_counts") or {}),
            "missing_required_output_counts": dict(
                source_stack_coverage.get("missing_required_output_counts") or {}
            ),
            "next_action_count": len(source_stack_coverage.get("next_actions") or []),
        },
        "l2_typed_graph": {
            "memory_entry_count": int(l2_view.get("memory_entry_count") or 0),
            "physics_object_count": int(l2_view.get("physics_object_count") or 0),
            "object_relation_count": int(l2_view.get("object_relation_count") or 0),
            "sensemaking_report_count": int(l2_view.get("sensemaking_report_count") or 0),
        },
        "source_reconstruction": {
            "incomplete_claim_count": int(source.get("incomplete_claim_count") or 0),
            "complete_claim_count": int(source.get("complete_claim_count") or 0),
            "top_incomplete_claim_refs": [
                f"source_reconstruction:{claim_id}"
                for claim_id in [
                    str(item.get("claim_id") or "")
                    for item in source.get("top_incomplete_claims", [])
                    if isinstance(item, dict)
                ]
                if claim_id
            ],
        },
        "source_reconstruction_review": {
            "claim_count": int(source_review.get("claim_count") or 0),
            "incomplete_claim_count": int(source_review.get("incomplete_claim_count") or 0),
            "review_progress": dict(source_review.get("review_progress") or {}),
            "next_action_count": len(source_review.get("next_actions") or []),
        },
        "workspace_interaction_preview": {
            "session_count": int(interaction.get("session_count") or 0),
            "decision_mode_counts": dict(interaction.get("decision_mode_counts") or {}),
        },
        "interaction_recording_worklist": {
            "work_item_count": int(interaction_worklist.get("work_item_count") or 0),
            "required_now_count": int(interaction_worklist.get("required_now_count") or 0),
            "decision_mode_counts": dict(interaction_worklist.get("decision_mode_counts") or {}),
        },
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }
    if legacy:
        compact["legacy_semantic_review"] = {
            "work_item_count": int(legacy.get("work_item_count") or 0),
            "status_counts": dict(legacy.get("status_counts") or {}),
            "pass_readiness_counts": dict(legacy.get("pass_readiness_counts") or {}),
            "open_human_checkpoint_count": int(legacy.get("open_human_checkpoint_count") or 0),
            "semantic_lossless_proven": bool(legacy.get("semantic_lossless_proven", False)),
        }
    if legacy_source:
        compact["legacy_source_reconstruction"] = {
            "work_item_count": int(legacy_source.get("work_item_count") or 0),
            "repair_status_counts": dict(legacy_source.get("repair_status_counts") or {}),
            "proposed_repair_count": int(legacy_source.get("proposed_repair_count") or 0),
        }
    if semantic_repair:
        compact["legacy_semantic_repair"] = {
            "work_item_count": int(semantic_repair.get("work_item_count") or 0),
            "repair_status_counts": dict(semantic_repair.get("repair_status_counts") or {}),
            "proposed_repair_count": int(semantic_repair.get("proposed_repair_count") or 0),
            "required_action_counts": dict(semantic_repair.get("required_action_counts") or {}),
        }
    if needs_revision_basis:
        compact["legacy_semantic_needs_revision_basis"] = {
            "basis_item_count": int(needs_revision_basis.get("basis_item_count") or 0),
            "status_counts": dict(needs_revision_basis.get("status_counts") or {}),
            "required_action_counts": dict(needs_revision_basis.get("required_action_counts") or {}),
        }
    if executable:
        compact["legacy_executable_evidence"] = {
            "evidence_item_count": int(executable.get("evidence_item_count") or 0),
            "executable_action_count": int(executable.get("executable_action_count") or 0),
        }
    if checkpoints:
        compact["legacy_human_checkpoints"] = {
            "checkpoint_item_count": int(checkpoints.get("checkpoint_item_count") or 0),
            "open_decision_count": int(checkpoints.get("open_decision_count") or 0),
            "pending_request_count": int(checkpoints.get("pending_request_count") or 0),
            "semantic_lossless_proven": bool(checkpoints.get("semantic_lossless_proven", False)),
        }
    return compact
