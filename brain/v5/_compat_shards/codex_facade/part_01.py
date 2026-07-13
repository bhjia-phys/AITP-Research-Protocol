# Compatibility shard 1 for codex_facade.
from __future__ import annotations

import re

import subprocess

from dataclasses import asdict

from pathlib import Path

from typing import Any

from brain.v5.brief import build_execution_brief

from brain.v5.capability_registry_data import (
    CODEX_FACADE_MCP_NAMES,
    CODEX_SUPPORT_MCP_NAMES,
)

from brain.v5.claim_relation_map import build_claim_relation_map

from brain.v5.code import capture_code_state_from_git

from brain.v5.context_pack import build_aitp_context_pack

from brain.v5.evidence import record_evidence

from brain.v5.literature_comparison_draft import build_literature_comparison_draft

from brain.v5.literature_intake import record_literature_candidate, suggest_literature_intake

from brain.v5.literature_source_review_handoff import build_literature_source_review_handoff

from brain.v5.lightweight_record_router import plan_lightweight_record_write

from brain.v5.note_outline import compile_note_outline

from brain.v5.objective_graph import build_compact_brief

from brain.v5.paths import WorkspacePaths

from brain.v5.physics_objects import record_object_relation, record_physics_object

from brain.v5.process_graph import build_process_graph_slice

from brain.v5.public_surfaces import require_valid_public_surface

from brain.v5.quiet_checkpoint import apply_quiet_checkpoint_batch, preview_quiet_checkpoint_batch

from brain.v5.recovery_session import recover_session_binding_for_read

from brain.v5.references import record_reference_location

from brain.v5.recording_navigator import (
    build_recording_navigation_state,
    classify_recording_candidate,
    expand_recording_slot,
    verify_recording_effect,
)

from brain.v5.research_retrieval import exact_expand

from brain.v5.research_timeline import build_research_timeline

from brain.v5.research_state import attach_artifact, create_proof_obligation

from brain.v5.sensemaking import record_sensemaking_report

from brain.v5.source_assets import register_source_asset

from brain.v5.source_reconstruction import audit_source_reconstruction

from brain.v5.tools import record_tool_run, register_tool_recipe

from brain.v5.trust_audit import audit_claim_trust

from brain.v5.validation import create_validation_contract, record_validation_result

from brain.v5.workspace_recovery_audit import build_workspace_recovery_audit, compact_workspace_recovery_audit

from brain.v5.workspace_recording_audit import build_workspace_recording_audit

CODEX_FACADE_TOOLS: tuple[str, ...] = CODEX_FACADE_MCP_NAMES

CODEX_SUPPORT_TOOLS: tuple[str, ...] = CODEX_SUPPORT_MCP_NAMES

CODEX_SURFACE_TOOL_ALLOWLIST: frozenset[str] = frozenset(CODEX_FACADE_TOOLS + CODEX_SUPPORT_TOOLS)

def codex_tool_catalog(profile: str = "entry") -> dict[str, Any]:
    """Return the compact Codex-facing surface catalog."""

    selected = _profile_name(profile)
    profiles = {
        "setup": {
            "purpose": "First-run path resolution before research tools are available.",
            "tools": ["aitp_config_status", "aitp_suggest_config", "aitp_configure"],
            "state_effect": "configuration_write_only",
        },
        "entry": {
            "purpose": "Decide whether AITP is needed, then restore a topic/session with compact context and expansion hints.",
            "tools": ["aitp_v5_codex_tool_catalog", "aitp_v5_codex_autoroute", "aitp_v5_codex_enter"],
            "state_effect": "read_only",
        },
        "read_expansion": {
            "purpose": "Expand exactly the context family needed by the next research action.",
            "tools": ["aitp_v5_codex_expand"],
            "expansions": [
                "context_pack",
                "brief",
                "timeline",
                "relation_map",
                "process_graph",
                "recording_navigation",
                "note_outline",
                "source_reconstruction",
                "trust_audit",
                "record_refs",
            ],
            "state_effect": "read_only",
        },
        "guided_recording": {
            "purpose": "Classify a durable moment, expand one recording slot, then apply one constrained typed write.",
            "tools": ["aitp_v5_codex_recording_step", "aitp_v5_codex_record_apply"],
            "state_effect": "read_only_until_slot_apply",
        },
        "literature": {
            "purpose": "Register paper/web/local-note references in layers before evidence or trust.",
            "tools": ["aitp_v5_codex_literature_step"],
            "state_effect": "read_only_or_reference_location_write",
        },
        "closeout": {
            "purpose": "Preview or explicitly write a quiet checkpoint for session handoff.",
            "tools": ["aitp_v5_codex_closeout"],
            "state_effect": "preview_by_default",
        },
        "trust": {
            "purpose": "Expose trust preflight without exposing trust apply by default.",
            "tools": ["aitp_v5_preflight_trust_update", "aitp_v5_evaluate_pre_tool_policy"],
            "state_effect": "preflight_only",
        },
    }
    return {
        "ok": True,
        "kind": "codex_mcp_surface_catalog",
        "catalog_version": "aitp.codex.1.0",
        "selected_profile": selected,
        "profile": profiles[selected],
        "profiles": profiles,
        "default_mcp_surface": "codex",
        "full_kernel_escape_hatch": "Set AITP_MCP_SURFACE=full for development or maintenance sessions.",
        "codex_surface_tools": list(CODEX_SURFACE_TOOL_ALLOWLIST),
        "hidden_in_codex_surface": [
            "aitp_v5_apply_trust_update",
            "aitp_v5_apply_promotion_packet",
            "legacy write aliases",
        ],
        "progressive_policy": {
            "start_with": "aitp_v5_codex_autoroute",
            "enter_with": "aitp_v5_codex_enter",
            "enter_payload_profile": "minimal",
            "expand_with": "aitp_v5_codex_expand",
            "record_with": "aitp_v5_codex_recording_step_then_aitp_v5_codex_record_apply",
            "literature_with": "aitp_v5_codex_literature_step",
            "closeout_with": "aitp_v5_codex_closeout",
        },
        "autoroute_semantic_contract": {
            "purpose": "Let the model make the semantic judgment, while the tool validates the safe read-only route.",
            "assessment_fields": [
                "task_kind",
                "needs_prior_research_state",
                "needs_latest_topic_state",
                "concerns_existing_topic_or_claim",
                "creates_or_updates_durable_research_output",
                "needs_validation_or_evidence_boundary",
                "mentions_failed_or_superseded_route",
                "trust_or_claim_status_sensitive",
                "is_generic_textbook_question",
                "should_use_aitp",
                "confidence",
                "rationale",
            ],
            "conservative_rule": "If a possible research request is semantically uncertain, enter AITP read-only before answering.",
            "non_goal": "This contract is not evidence, validation, or claim support.",
        },
        "truth_source": "codex_facade_catalog",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }

def codex_autoroute(
    ws: WorkspacePaths | None,
    *,
    request_summary: str,
    session_id: str = "",
    topics: list[str] | None = None,
    visible_files: list[str] | None = None,
    recent_tool_summary: str = "",
    semantic_assessment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify whether Codex should enter AITP before answering.

    This is a read-only routing decision. It never writes records, creates
    sessions, rebinds claims, or updates trust.
    """

    del ws
    clean_session = str(session_id or "").strip()
    clean_topics = [str(topic).strip() for topic in (topics or []) if str(topic).strip()]
    clean_files = [str(item).strip() for item in (visible_files or []) if str(item).strip()]
    text = " ".join(
        [str(request_summary or ""), str(recent_tool_summary or ""), " ".join(clean_topics), " ".join(clean_files)]
    )
    signals = _aitp_route_signals(text, session_id=clean_session, topics=clean_topics, visible_files=clean_files)
    semantic_signals = _semantic_route_signals(semantic_assessment)
    if semantic_signals["provided"]:
        signals = _merge_route_signals(signals, semantic_signals)
    process_mode = _process_mode("auto", text)
    required = bool(signals["required"])
    decision = "answer_without_aitp"
    recommended_tool = "none"
    recommended_args: dict[str, Any] = {}
    recommended_sequence: list[dict[str, Any]] = []

    if required and clean_session:
        decision = "enter_existing_session"
        recommended_tool = "aitp_v5_codex_enter"
        recommended_args = {
            "base": "",
            "session_id": clean_session,
            "request_summary": str(request_summary or ""),
            "process_mode": process_mode,
            "payload_profile": "minimal",
        }
    elif required and clean_topics:
        decision = "recover_topic"
        recommended_tool = "aitp_v5_codex_enter"
        recommended_args = {
            "base": "",
            "topics": clean_topics,
            "request_summary": str(request_summary or ""),
            "process_mode": process_mode,
            "payload_profile": "minimal",
        }
    elif required:
        decision = "recover_workspace"
        recommended_tool = "aitp_v5_codex_enter"
        recommended_args = {
            "base": "",
            "request_summary": str(request_summary or ""),
            "process_mode": process_mode,
            "payload_profile": "minimal",
        }

    if required:
        recommended_sequence.append({"tool": recommended_tool, "arguments": recommended_args, "state_effect": "read_only"})
        recommended_sequence.append(
            {
                "tool": "aitp_v5_codex_expand",
                "arguments": {
                    "base": "",
                    "session_id": "<session-id from enter/recovery_ready row>",
                    "expansion": "timeline",
                },
                "state_effect": "read_only",
                "condition": "after a session is selected",
            }
        )
        if process_mode in {"synthesis", "derivation", "code_numerical", "writing", "closeout"}:
            recommended_sequence.append(
                {
                    "tool": "aitp_v5_codex_expand",
                    "arguments": {
                        "base": "",
                        "session_id": "<session-id from enter/recovery_ready row>",
                        "expansion": "relation_map",
                    },
                    "state_effect": "read_only",
                    "condition": "before interpreting claim truth, support, contradiction, or validation",
                }
            )

    return {
        "ok": True,
        "kind": "codex_auto_route_decision",
        "request_summary": str(request_summary or ""),
        "decision": decision,
        "aitp_required_before_answer": required,
        "safe_to_answer_without_aitp": not required,
        "confidence": signals["confidence"],
        "process_mode": process_mode,
        "reason_codes": signals["reason_codes"],
        "matched_triggers": signals["matched_triggers"],
        "semantic_assessment": semantic_signals["normalized"],
        "semantic_assessment_used": semantic_signals["provided"],
        "semantic_assessment_issues": semantic_signals["issues"],
        "session_id": clean_session,
        "topics": clean_topics,
        "visible_files": clean_files,
        "recommended_next_tool": recommended_tool,
        "recommended_args": recommended_args,
        "recommended_sequence": recommended_sequence,
        "automatic_use_policy": {
            "read_only_first": True,
            "write_on_route": False,
            "call_enter_before_answer_when_required": True,
            "do_not_create_topic_without_user_confirmation": True,
            "do_not_rebind_claim_without_user_confirmation": True,
        },
        "trust_policy": {
            "summary_inputs_trusted": False,
            "orientation_only": True,
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
            "trust_promotion_requires_preflight_and_human_gate": True,
        },
        "truth_source": "codex_autoroute_semantic_guarded" if semantic_signals["provided"] else "codex_autoroute_heuristic_fallback",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }

def codex_enter_context(
    ws: WorkspacePaths,
    *,
    session_id: str = "",
    topics: list[str] | None = None,
    request_summary: str = "",
    process_mode: str = "auto",
    payload_profile: str = "minimal",
    max_lines: int = 60,
    candidate_limit: int = 3,
) -> dict[str, Any]:
    """Enter AITP from Codex with the smallest useful read-only payload."""

    clean_session = str(session_id or "").strip()
    clean_topics = [str(topic).strip() for topic in (topics or []) if str(topic).strip()]
    mode = _process_mode(process_mode, request_summary)
    profile = _entry_payload_profile(payload_profile)
    payload: dict[str, Any] = {
        "ok": True,
        "kind": "codex_entry_context",
        "process_mode": mode,
        "payload_profile": profile,
        "session_id": clean_session,
        "topics": clean_topics,
        "request_summary": str(request_summary or ""),
        "entry_policy": {
            "read_first": True,
            "default_context": "entry_card" if profile == "minimal" else "context_pack_when_session_is_known",
            "write_on_entry": False,
            "create_topic_only_after_durable_objective": True,
            "expand_full_graph_only_when_needed": True,
            "context_pack_requires_explicit_profile_or_expand": True,
        },
        "next_profiles": ["read_expansion", "guided_recording", "literature", "closeout"],
        "truth_source": "typed_records_or_recovery_audit",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    if clean_session:
        try:
            if profile == "context_pack":
                payload["context_pack"] = build_aitp_context_pack(
                    ws,
                    clean_session,
                    max_lines=max_lines,
                    candidate_limit=candidate_limit,
                    user_goal=request_summary,
                )
            else:
                payload["entry_card"] = _build_codex_entry_card(
                    ws,
                    clean_session,
                    request_summary=request_summary,
                    process_mode=mode,
                    max_lines=max_lines,
                )
            payload["active_session_ready"] = True
            payload["recommended_next_tool"] = "aitp_v5_codex_expand"
            payload["recommended_next_expansions"] = _expansions_for_mode(mode)
            payload["expand_context_pack_when_needed"] = {
                "tool": "aitp_v5_codex_expand",
                "arguments": {"base": "", "session_id": clean_session, "expansion": "context_pack"},
            }
        except Exception as exc:
            payload["active_session_ready"] = False
            payload["entry_error"] = f"{type(exc).__name__}: {exc}"
            payload["workspace_recovery_audit"] = compact_workspace_recovery_audit(
                build_workspace_recovery_audit(ws, topics=clean_topics)
            )
            payload["recommended_next_tool"] = "aitp_v5_codex_enter"
        return payload

    payload["active_session_ready"] = False
    payload["workspace_recovery_audit"] = compact_workspace_recovery_audit(
        build_workspace_recovery_audit(ws, topics=clean_topics)
    )
    payload["recommended_next_tool"] = "aitp_v5_codex_enter"
    payload["recommended_next_step"] = (
        "Select a recovery_ready session, or ask before creating a new topic/session if no match exists."
    )
    return payload
