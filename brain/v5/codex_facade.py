"""Codex App facade surfaces for compact, progressive AITP v5 use."""

from __future__ import annotations

import re
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

from brain.v5.brief import build_execution_brief
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


CODEX_FACADE_TOOLS: tuple[str, ...] = (
    "aitp_v5_codex_tool_catalog",
    "aitp_v5_codex_autoroute",
    "aitp_v5_codex_enter",
    "aitp_v5_codex_expand",
    "aitp_v5_codex_recording_step",
    "aitp_v5_codex_record_apply",
    "aitp_v5_codex_literature_step",
    "aitp_v5_codex_closeout",
)

CODEX_SUPPORT_TOOLS: tuple[str, ...] = (
    "aitp_v5_get_runtime_bridge_target_manifest",
    "aitp_v5_get_runtime_payload_profiles",
    "aitp_v5_audit_runtime_mcp_bridge_acceptance",
    "aitp_v5_evaluate_pre_tool_policy",
    "aitp_v5_preflight_trust_update",
    "aitp_v5_audit_hook_installation",
    "aitp_v5_discover_hook_install_paths",
    "aitp_v5_report_hook_smoke_coverage",
)

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


def codex_expand_context(
    ws: WorkspacePaths,
    *,
    session_id: str,
    expansion: str,
    claim_id: str = "",
    max_lines: int = 60,
    limit: int = 60,
    style: str = "jhep",
    objective_text: str = "",
    user_goal: str = "",
    record_refs: list[str] | tuple[str, ...] | None = None,
    offset: int = 0,
) -> dict[str, Any]:
    """Expand one Codex context family on demand."""

    selected = _expansion_name(expansion)
    payload: dict[str, Any] = {
        "ok": True,
        "kind": "codex_context_expansion",
        "session_id": session_id,
        "expansion": selected,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    if selected == "context_pack":
        payload["surface"] = build_aitp_context_pack(
            ws,
            session_id,
            max_lines=max_lines,
            objective_text=objective_text,
            user_goal=user_goal,
        )
    elif selected == "brief":
        payload["surface"] = build_execution_brief(ws, session_id)
    elif selected == "relation_map":
        payload["surface"] = build_claim_relation_map(
            ws,
            session_id,
            objective_text=objective_text,
            user_goal=user_goal,
        )
    elif selected == "timeline":
        payload["surface"] = build_research_timeline(ws, session_id, claim_id=claim_id, limit=limit)
    elif selected == "process_graph":
        payload["surface"] = build_process_graph_slice(ws, session_id, claim_id=claim_id, limit=limit)
    elif selected == "recording_navigation":
        payload["surface"] = build_recording_navigation_state(ws, session_id, claim_id=claim_id, limit=limit)
    elif selected == "note_outline":
        payload["surface"] = compile_note_outline(ws, session_id, style=style, candidate_limit=min(limit, 12))
    elif selected == "source_reconstruction":
        if not claim_id:
            return _needs_claim_id(selected)
        payload["surface"] = audit_source_reconstruction(ws, claim_id=claim_id)
    elif selected == "trust_audit":
        if not claim_id:
            return _needs_claim_id(selected)
        payload["surface"] = audit_claim_trust(ws, claim_id=claim_id)
    elif selected == "record_refs":
        payload["surface"] = _expand_record_refs(
            ws,
            refs=record_refs or (),
            offset=offset,
            limit=limit,
        )
        if not payload["surface"]["ok"]:
            payload["ok"] = False
    else:
        payload["ok"] = False
        payload["error"] = f"unsupported expansion: {expansion}"
        payload["allowed_expansions"] = _allowed_expansions()
    return payload


def codex_recording_step(
    ws: WorkspacePaths,
    *,
    session_id: str,
    event_type: str,
    summary: str = "",
    topic_id: str = "",
    claim_id: str = "",
    touched_refs: list[str] | None = None,
    produced_artifacts: list[str] | None = None,
    tool_call_id: str = "",
    risk_hint: str = "",
    slot: str = "",
    candidate: dict[str, Any] | None = None,
    expected_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Classify and navigate one durable recording moment without doing the write."""

    classification = classify_recording_candidate(
        ws,
        session_id=session_id,
        event_type=event_type,
        summary=summary,
        topic_id=topic_id,
        claim_id=claim_id,
        touched_refs=touched_refs,
        produced_artifacts=produced_artifacts,
        tool_call_id=tool_call_id,
        risk_hint=risk_hint,
        payload=candidate,
    )
    payload: dict[str, Any] = {
        "ok": True,
        "kind": "codex_recording_step",
        "session_id": session_id,
        "classification": classification,
        "write_executed": False,
        "recording_policy": {
            "agent_should_not_record_every_step": True,
            "classification_writes": False,
            "navigation_writes": False,
            "slot_expansion_writes": False,
            "deepest_layer_write_tool": "aitp_v5_codex_record_apply",
        },
        "truth_source": "typed_records_and_event_metadata",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    try:
        focus = recover_session_binding_for_read(ws, session_id)
        session = focus.session
        plan_topic_id = topic_id or session.topic_id
        payload["lightweight_record_write_plan"] = require_valid_public_surface(
            "lightweight_record_write_plan",
            plan_lightweight_record_write(
                ws,
                topic_id=plan_topic_id,
                current_session_id=session.session_id,
                event_summary=summary,
                active_claim_id=session.active_claim,
                target_claim_hint=claim_id,
                touched_files_or_artifacts=_recording_artifact_inputs(touched_refs, produced_artifacts),
                touched_tool_runs_or_evidence_refs=_recording_evidence_ref_inputs(touched_refs),
                risk_hint=risk_hint,
            ),
        )
    except Exception as exc:
        payload["lightweight_record_write_plan_error"] = f"{type(exc).__name__}: {exc}"
    decision = classification.get("decision")
    if decision in {"navigate", "checkpoint"}:
        payload["navigation_state"] = build_recording_navigation_state(
            ws,
            session_id,
            claim_id=claim_id,
        )
    if slot:
        slot_candidate = dict(candidate or {})
        slot_candidate.setdefault("event_type", event_type)
        slot_candidate.setdefault("decision", decision)
        slot_candidate.setdefault("suggested_slots", classification.get("suggested_slots", []))
        slot_candidate.setdefault("candidate_refs", touched_refs or [])
        slot_candidate.setdefault("produced_artifacts", produced_artifacts or [])
        payload["slot_expansion"] = expand_recording_slot(
            ws,
            session_id,
            slot,
            claim_id=claim_id,
            candidate=slot_candidate,
        )
        payload["recommended_write_tool"] = payload["slot_expansion"].get("recommended_write_tool", "")
    if expected_refs:
        payload["verification"] = verify_recording_effect(
            ws,
            session_id,
            expected_refs=expected_refs,
            claim_id=claim_id,
        )
    return payload


def _entry_payload_profile(payload_profile: str) -> str:
    clean = str(payload_profile or "minimal").strip().lower().replace("-", "_")
    aliases = {
        "": "minimal",
        "light": "minimal",
        "lite": "minimal",
        "card": "minimal",
        "entry_card": "minimal",
        "minimal_card": "minimal",
        "compact": "minimal",
        "full": "context_pack",
        "legacy": "context_pack",
        "context": "context_pack",
    }
    return aliases.get(clean, clean if clean in {"minimal", "context_pack"} else "minimal")


def _build_codex_entry_card(
    ws: WorkspacePaths,
    session_id: str,
    *,
    request_summary: str,
    process_mode: str,
    max_lines: int,
) -> dict[str, Any]:
    compact = build_compact_brief(
        ws,
        session_id,
        max_lines=min(max(8, int(max_lines or 12)), 14),
        user_goal=request_summary,
    )
    objective = compact.get("current_objective") if isinstance(compact.get("current_objective"), dict) else {}
    package = compact.get("active_work_package") if isinstance(compact.get("active_work_package"), dict) else {}
    relevant_claims = [
        {
            "claim_id": str(claim.get("claim_id") or ""),
            "statement": _excerpt(str(claim.get("statement") or ""), limit=140),
        }
        for claim in list(compact.get("relevant_claims") or [])[:3]
        if isinstance(claim, dict)
    ]
    previous_failed = [
        {
            "record_ref": str(item.get("record_ref") or ""),
            "classification": str(item.get("classification") or ""),
            "summary": _excerpt(str(item.get("summary") or ""), limit=120),
        }
        for item in list(compact.get("previous_failed_attempts") or [])[:2]
        if isinstance(item, dict)
    ]
    card = {
        "ok": True,
        "kind": "codex_entry_card",
        "session_id": str(compact.get("session_id") or session_id),
        "topic_id": str(compact.get("topic_id") or ""),
        "process_mode": process_mode,
        "current_objective": {
            "title": _excerpt(str(objective.get("title") or compact.get("topic_id") or ""), limit=140),
            "objective_id": str(objective.get("objective_id") or ""),
        },
        "active_work_package": {
            "title": _excerpt(str(package.get("title") or ""), limit=140),
            "work_package_id": str(package.get("work_package_id") or ""),
        },
        "relevant_claims": relevant_claims,
        "boundary": {
            "can_say": [_excerpt(str(item), limit=160) for item in list(compact.get("can_say") or [])[:3]],
            "cannot_say": [_excerpt(str(item), limit=160) for item in list(compact.get("cannot_say") or [])[:3]],
            "relation_map_scope": str(compact.get("relation_map_scope") or "active_claim_only"),
        },
        "blockers": [_excerpt(str(item), limit=160) for item in list(compact.get("blockers") or [])[:3]],
        "previous_failed_attempts": previous_failed,
        "next_valid_actions": [_excerpt(str(item), limit=160) for item in list(compact.get("next_valid_actions") or [])[:4]],
        "warnings": [_excerpt(str(item), limit=160) for item in list(compact.get("warnings") or [])[:3]],
        "model_policy": {
            "orientation_only": True,
            "answer_within_card_boundary": True,
            "expand_before_claim_truth_or_validation": True,
            "do_not_record_from_entry_card": True,
            "do_not_update_claim_trust": True,
        },
        "recommended_expansions": _expansions_for_mode(process_mode),
        "expand": {
            "context_pack": {"tool": "aitp_v5_codex_expand", "arguments": {"expansion": "context_pack"}},
            "timeline": {"tool": "aitp_v5_codex_expand", "arguments": {"expansion": "timeline"}},
            "relation_map": {"tool": "aitp_v5_codex_expand", "arguments": {"expansion": "relation_map"}},
            "brief": {"tool": "aitp_v5_codex_expand", "arguments": {"expansion": "brief"}},
        },
        "source_records": compact.get("source_records") or {},
        "truth_source": "typed_records_derived_entry_card_not_evidence",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    card["line_count"] = len(_entry_card_lines(card))
    card["lines"] = _entry_card_lines(card)
    return card


def _entry_card_lines(card: dict[str, Any]) -> list[str]:
    objective = card.get("current_objective") or {}
    package = card.get("active_work_package") or {}
    lines = [
        f"Session: {card.get('session_id')} | Topic: {card.get('topic_id')}",
        f"Objective: {objective.get('title') or 'unknown'}",
        f"Work package: {package.get('title') or 'none'}",
        "Boundary: orientation-only; expand before claim truth, evidence, validation, or trust-sensitive decisions.",
    ]
    blockers = list(card.get("blockers") or [])
    if blockers:
        lines.append(f"Blockers: {'; '.join(blockers[:2])}")
    next_actions = list(card.get("next_valid_actions") or [])
    if next_actions:
        lines.append(f"Next: {'; '.join(next_actions[:2])}")
    failed = list(card.get("previous_failed_attempts") or [])
    if failed:
        lines.append(
            "Prior failed/superseded: "
            + "; ".join(_excerpt(str(item.get("summary") or item.get("record_ref") or ""), limit=90) for item in failed[:2])
        )
    return lines


def _excerpt(value: str, *, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _recording_artifact_inputs(touched_refs: list[str] | None, produced_artifacts: list[str] | None) -> list[str]:
    values = [_normalize_artifact_uri(str(value).strip()) for value in (produced_artifacts or []) if str(value).strip()]
    for ref in touched_refs or []:
        text = str(ref).strip()
        if text.startswith("artifact:"):
            values.append(text)
        else:
            normalized = _normalize_artifact_uri(text)
            if normalized != text:
                values.append(normalized)
    return values


def _recording_evidence_ref_inputs(touched_refs: list[str] | None) -> list[str]:
    evidence_prefixes = ("tool_run:", "validation_result:", "evidence:")
    return [
        str(ref).strip()
        for ref in (touched_refs or [])
        if str(ref).strip().startswith(evidence_prefixes)
    ]


def codex_literature_step(
    ws: WorkspacePaths,
    *,
    session_id: str,
    uri: str,
    label: str,
    action: str = "suggest",
    external_id: str = "",
    short_summary: str = "",
    detected_relevance: str = "",
    optional_claim_id: str = "",
    scoped_output: str = "",
    reviewed_refs: list[str] | None = None,
    comparison_question: str = "",
    source_refs: list[str] | None = None,
    dimensions: list[str] | None = None,
    rationale: str = "",
    asset_type: str = "",
) -> dict[str, Any]:
    """Run one literature/reference workflow layer from Codex."""

    selected = _literature_action(action)
    common = {
        "session_id": session_id,
        "uri": uri,
        "label": label,
        "external_id": external_id,
        "short_summary": short_summary,
        "detected_relevance": detected_relevance,
        "optional_claim_id": optional_claim_id,
        "scoped_output": scoped_output,
    }
    intake_common = {**common, "asset_type": asset_type}
    payload: dict[str, Any] = {
        "ok": True,
        "kind": "codex_literature_step",
        "action": selected,
        "reference_layers": _reference_layers(),
        "truth_source": "typed_records_and_agent_supplied_literature_metadata",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }
    if selected == "suggest":
        payload["surface"] = suggest_literature_intake(ws, **intake_common)
        payload["orientation_only"] = True
        payload["can_update_kernel_state"] = False
    elif selected == "record_reference":
        payload["surface"] = record_literature_candidate(ws, **intake_common)
        payload["recorded_source_asset"] = payload["surface"].get("recorded_source_asset", {})
        payload["recorded_reference_location"] = payload["surface"].get("recorded_reference_location", {})
        payload["orientation_only"] = False
        payload["can_update_kernel_state"] = True
        payload["kernel_state_change"] = "source_asset_and_reference_location_records"
    elif selected == "source_review_handoff":
        payload["surface"] = build_literature_source_review_handoff(
            ws,
            **common,
            reviewed_refs=reviewed_refs or [],
        )
        payload["orientation_only"] = True
        payload["can_update_kernel_state"] = False
    elif selected == "comparison_draft":
        payload["surface"] = build_literature_comparison_draft(
            ws,
            session_id=session_id,
            comparison_question=comparison_question,
            source_refs=source_refs or [],
            dimensions=dimensions or [],
            optional_claim_id=optional_claim_id,
            rationale=rationale,
        )
        payload["orientation_only"] = True
        payload["can_update_kernel_state"] = False
    else:
        payload["ok"] = False
        payload["error"] = f"unsupported literature action: {action}"
        payload["allowed_actions"] = _allowed_literature_actions()
        payload["orientation_only"] = True
        payload["can_update_kernel_state"] = False
    return payload


def codex_closeout(
    ws: WorkspacePaths,
    *,
    session_id: str,
    summary: str,
    apply: bool = False,
    claim_id: str = "",
    run_id: str = "",
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    changed_files: list[str] | None = None,
    generated_artifacts: list[dict] | None = None,
    validation_commands: list[str] | None = None,
    durable_observations: list[str] | None = None,
    claim_boundary: dict | None = None,
    next_blockers: list[str] | None = None,
    artifact_specs: list[dict] | None = None,
    source_specs: list[dict] | None = None,
    tool_run_specs: list[dict] | None = None,
    sensemaking_summary: str = "",
    source_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Preview or apply a session closeout checkpoint without trust mutation."""

    kwargs = {
        "claim_id": claim_id,
        "run_id": run_id,
        "summary": summary,
        "inputs": inputs,
        "outputs": outputs,
        "changed_files": changed_files,
        "generated_artifacts": generated_artifacts,
        "validation_commands": validation_commands,
        "durable_observations": durable_observations,
        "claim_boundary": claim_boundary,
        "next_blockers": next_blockers,
        "artifact_specs": artifact_specs,
        "source_specs": source_specs,
        "tool_run_specs": tool_run_specs,
        "sensemaking_summary": sensemaking_summary,
        "source_refs": source_refs,
    }
    surface = (
        apply_quiet_checkpoint_batch(ws, session_id, **kwargs)
        if apply
        else preview_quiet_checkpoint_batch(ws, session_id, **kwargs)
    )
    record_completeness_audit = surface.get("record_completeness_audit", {})
    return {
        "ok": True,
        "kind": "codex_closeout",
        "mode": "apply" if apply else "preview",
        "session_id": session_id,
        "surface": surface,
        "record_completeness_audit": record_completeness_audit,
        "missing_recommended_slots": record_completeness_audit.get("missing_recommended_slots", []),
        "recommended_next_records": record_completeness_audit.get("recommended_next_records", []),
        "write_executed": bool(apply),
        "kernel_state_change": "quiet_checkpoint_batch" if apply else "none",
        "trust_update_forbidden": True,
        "truth_source": "typed_records_and_closeout_summary",
        "summary_inputs_trusted": False,
        "orientation_only": not apply,
        "can_update_kernel_state": bool(apply),
        "can_update_claim_trust": False,
    }


def _profile_name(profile: str) -> str:
    clean = str(profile or "entry").strip().lower().replace("-", "_")
    aliases = {"read": "read_expansion", "recording": "guided_recording"}
    clean = aliases.get(clean, clean)
    allowed = {
        "setup",
        "entry",
        "read_expansion",
        "guided_recording",
        "literature",
        "closeout",
        "trust",
    }
    return clean if clean in allowed else "entry"


def _process_mode(process_mode: str, request_summary: str) -> str:
    clean = str(process_mode or "").strip().lower().replace("-", "_")
    allowed = {
        "setup",
        "new_topic",
        "continuation",
        "literature",
        "derivation",
        "code_numerical",
        "writing",
        "synthesis",
        "closeout",
    }
    if clean in allowed:
        return clean
    text = str(request_summary or "").lower()
    if any(token in text for token in ("paper", "literature", "arxiv", "reference", "citation")):
        return "literature"
    if any(token in text for token in ("文献", "论文", "参考文献", "引用", "读文献", "学习文献", "阅读文献")):
        return "literature"
    if any(token in text for token in ("note", "draft", "write", "article", "jhep")):
        return "writing"
    if any(token in text for token in ("笔记", "文章", "写作", "草稿", "写note", "写 note", "模板")):
        return "writing"
    if any(token in text for token in ("end", "handoff", "closeout", "summary")):
        return "closeout"
    if any(token in text for token in ("结束", "收尾", "交接", "总结", "会话结束")):
        return "closeout"
    if any(token in text for token in ("synthesis", "final", "conclusion", "综述", "综合", "结论", "最终")):
        return "synthesis"
    if any(token in text for token in ("derive", "derivation", "proof", "theorem", "algebra")):
        return "derivation"
    if any(token in text for token in ("推导", "证明", "定理", "代数", "公式")):
        return "derivation"
    if any(token in text for token in ("code", "run", "numerical", "hpc", "validation")):
        return "code_numerical"
    if any(token in text for token in ("代码", "运行", "数值", "计算", "验证", "测试", "程序")):
        return "code_numerical"
    return "continuation"


def _aitp_route_signals(
    text: str,
    *,
    session_id: str,
    topics: list[str],
    visible_files: list[str],
) -> dict[str, Any]:
    lowered = str(text or "").lower()
    reason_codes: list[str] = []
    matched: list[str] = []

    def add(code: str, token: str) -> None:
        if code not in reason_codes:
            reason_codes.append(code)
        if token and token not in matched:
            matched.append(token)

    explicit_tokens = [
        "aitp",
        "typed record",
        "claim trust",
        "trust preflight",
        "record_completeness",
        "quiet_checkpoint",
        "sensemaking_report",
        "evidence",
        "validation_result",
        "tool_run",
        "code_state",
        "claim boundary",
        "l2 memory",
    ]
    topic_tokens = [
        "topic",
        "session",
        "claim",
        "checkpoint",
        "open gap",
        "failed route",
        "wrong route",
        "superseded",
        "continue research",
        "continue this topic",
        "current topic",
        "prior result",
        "latest result",
        "research note",
        "latex",
        "pdf",
        "report",
    ]
    research_tokens = [
        "theoretical physics",
        "derivation",
        "proof",
        "theorem",
        "paper",
        "literature",
        "arxiv",
        "numerical",
        "simulation",
        "benchmark",
        "validation",
        "qsgw",
        "librpa",
        "dmft",
        "syk",
        "green function",
        "topology",
    ]
    durable_tokens = [
        "compile",
        "build",
        "artifact",
        "plot",
        "dataset",
        "log",
        "source",
        "record",
        "closeout",
        "handoff",
    ]
    chinese_tokens = [
        "\u7814\u7a76",
        "\u79d1\u7814",
        "\u8bfe\u9898",
        "\u7ee7\u7eed",
        "\u8bb0\u5f55",
        "\u8bba\u70b9",
        "\u8bc1\u636e",
        "\u9a8c\u8bc1",
        "\u4fe1\u4efb",
        "\u63a8\u5bfc",
        "\u8bc1\u660e",
        "\u8bba\u6587",
        "\u6587\u732e",
        "\u7b14\u8bb0",
        "\u62a5\u544a",
        "\u7f16\u8bd1",
        "\u9519\u8bef\u8def\u7ebf",
        "\u6700\u65b0\u7ed3\u679c",
        "\u7406\u8bba\u7269\u7406",
        "研究",
        "科研",
        "课题",
        "继续",
        "记录",
        "论点",
        "证据",
        "验证",
        "信任",
        "推导",
        "证明",
        "论文",
        "文献",
        "笔记",
        "报告",
        "编译",
        "错误路线",
        "最新结果",
        "理论物理",
    ]
    generic_question_markers = [
        "what is ",
        "explain ",
        "define ",
        "\u6982\u5ff5",
        "\u89e3\u91ca\u4e00\u4e0b",
        "\u662f\u4ec0\u4e48",
        "概念",
        "解释一下",
        "是什么",
    ]

    for token in explicit_tokens:
        if token in lowered:
            add("explicit_aitp_protocol_reference", token)
    for token in topic_tokens:
        if token in lowered:
            add("topic_or_continuation_reference", token)
    for token in research_tokens:
        if token in lowered:
            add("research_domain_reference", token)
    for token in durable_tokens:
        if token in lowered:
            add("durable_research_output_or_recording", token)
    for token in chinese_tokens:
        if token in text:
            add("chinese_research_or_protocol_reference", token)
    for path in visible_files:
        suffix = Path(path).suffix.lower()
        if suffix in {".tex", ".pdf", ".bib", ".ipynb", ".py", ".log", ".md"}:
            add("research_file_context_present", suffix)
            break
    if session_id:
        add("session_hint_present", "session_id")
    if topics:
        add("topic_hint_present", "topics")

    has_project_signal = any(
        code in reason_codes
        for code in (
            "explicit_aitp_protocol_reference",
            "topic_or_continuation_reference",
            "durable_research_output_or_recording",
            "chinese_research_or_protocol_reference",
            "research_file_context_present",
            "session_hint_present",
            "topic_hint_present",
        )
    )
    has_research_signal = "research_domain_reference" in reason_codes
    generic_only = (
        has_research_signal
        and not has_project_signal
        and any(marker in lowered or marker in text for marker in generic_question_markers)
    )
    required = False
    if "explicit_aitp_protocol_reference" in reason_codes:
        required = True
    elif session_id or topics:
        required = has_project_signal or has_research_signal
    elif has_project_signal and not generic_only:
        required = True
    elif has_research_signal and "durable_research_output_or_recording" in reason_codes:
        required = True

    confidence = "none"
    if required:
        if "explicit_aitp_protocol_reference" in reason_codes or session_id or topics:
            confidence = "high"
        elif len(reason_codes) >= 2:
            confidence = "medium"
        else:
            confidence = "low"
    elif generic_only:
        confidence = "medium"

    if not reason_codes:
        reason_codes.append("no_aitp_research_trigger_detected")
    if generic_only:
        reason_codes.append("generic_knowledge_question_without_project_context")

    return {
        "required": required,
        "confidence": confidence,
        "reason_codes": reason_codes,
        "matched_triggers": matched,
    }


def _semantic_route_signals(assessment: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(assessment, dict) or not assessment:
        return {
            "provided": False,
            "required": None,
            "confidence": "none",
            "reason_codes": [],
            "matched_triggers": [],
            "normalized": {},
            "issues": [],
        }

    def clean_text(key: str) -> str:
        return str(assessment.get(key, "") or "").strip()

    def truthy(key: str) -> bool:
        value = assessment.get(key)
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        return str(value or "").strip().lower() in {"1", "true", "yes", "y", "required", "needed"}

    task_kind = clean_text("task_kind").lower().replace("-", "_")
    confidence = clean_text("confidence").lower() or clean_text("route_confidence").lower()
    if confidence not in {"high", "medium", "low", "none"}:
        confidence = "medium"
    should_use = clean_text("should_use_aitp").lower().replace("-", "_")
    if should_use not in {"true", "false", "yes", "no", "required", "not_required", "uncertain", "unknown", ""}:
        should_use = ""

    research_fields = {
        "needs_prior_research_state": "semantic_needs_prior_research_state",
        "needs_latest_topic_state": "semantic_needs_latest_topic_state",
        "concerns_existing_topic_or_claim": "semantic_existing_topic_or_claim",
        "creates_or_updates_durable_research_output": "semantic_durable_research_output",
        "needs_validation_or_evidence_boundary": "semantic_validation_or_evidence_boundary",
        "mentions_failed_or_superseded_route": "semantic_failed_or_superseded_route",
        "trust_or_claim_status_sensitive": "semantic_trust_or_claim_status_sensitive",
    }
    true_fields = [field for field in research_fields if truthy(field)]
    generic_textbook = truthy("is_generic_textbook_question")
    uncertain = truthy("uncertain") or should_use in {"uncertain", "unknown"} or task_kind in {"uncertain", "ambiguous"}
    task_requires_aitp = task_kind in {
        "project_research",
        "topic_continuation",
        "prior_status",
        "literature_reading",
        "derivation",
        "validation",
        "note_writing",
        "report_writing",
        "closeout",
        "numerical_work",
        "artifact_production",
        "claim_boundary",
    }

    reason_codes: list[str] = []
    matched: list[str] = []

    def add(code: str, token: str) -> None:
        if code not in reason_codes:
            reason_codes.append(code)
        if token and token not in matched:
            matched.append(token)

    for field in true_fields:
        add(research_fields[field], field)
    if task_requires_aitp:
        add("semantic_task_kind_requires_aitp", task_kind)
    if generic_textbook:
        add("semantic_generic_textbook_question", "is_generic_textbook_question")
    if uncertain:
        add("semantic_route_uncertain", "uncertain")
    if should_use in {"true", "yes", "required"}:
        add("semantic_should_use_aitp", "should_use_aitp")
    elif should_use in {"false", "no", "not_required"}:
        add("semantic_should_not_use_aitp", "should_use_aitp")

    project_semantic = bool(true_fields) or task_requires_aitp
    if project_semantic:
        required: bool | None = True
    elif generic_textbook and should_use not in {"true", "yes", "required"}:
        required = False
    elif should_use in {"true", "yes", "required"}:
        required = True
    elif should_use in {"false", "no", "not_required"}:
        required = False
    elif uncertain:
        required = True
    else:
        required = None

    issues: list[str] = []
    if generic_textbook and project_semantic:
        issues.append("generic_textbook_question_conflicts_with_project_research_flags")
    if should_use in {"false", "no", "not_required"} and project_semantic:
        issues.append("should_use_aitp_false_conflicts_with_project_research_flags")

    normalized = {
        "task_kind": task_kind,
        "should_use_aitp": should_use,
        "confidence": confidence,
        "rationale": clean_text("rationale"),
        "is_generic_textbook_question": generic_textbook,
        "uncertain": uncertain,
        "true_research_fields": true_fields,
    }
    normalized.update({field: truthy(field) for field in research_fields})

    return {
        "provided": True,
        "required": required,
        "confidence": confidence,
        "reason_codes": reason_codes,
        "matched_triggers": matched,
        "normalized": normalized,
        "issues": issues,
    }


def _merge_route_signals(heuristic: dict[str, Any], semantic: dict[str, Any]) -> dict[str, Any]:
    reason_codes = list(heuristic.get("reason_codes", []))
    matched = list(heuristic.get("matched_triggers", []))
    for code in semantic.get("reason_codes", []):
        if code not in reason_codes:
            reason_codes.append(code)
    for token in semantic.get("matched_triggers", []):
        if token and token not in matched:
            matched.append(token)

    semantic_required = semantic.get("required")
    required = bool(heuristic.get("required"))
    hard_heuristic = any(
        code in reason_codes
        for code in (
            "explicit_aitp_protocol_reference",
            "session_hint_present",
            "topic_hint_present",
            "research_file_context_present",
        )
    )
    if semantic_required is True:
        required = True
    elif semantic_required is False and not hard_heuristic:
        required = False

    confidence_rank = {"none": 0, "low": 1, "medium": 2, "high": 3}
    confidence = str(heuristic.get("confidence", "none"))
    semantic_confidence = str(semantic.get("confidence", "none"))
    if semantic_required is not None and confidence_rank.get(semantic_confidence, 0) >= confidence_rank.get(confidence, 0):
        confidence = semantic_confidence
    if required and confidence == "none":
        confidence = "low"

    return {
        "required": required,
        "confidence": confidence,
        "reason_codes": reason_codes,
        "matched_triggers": matched,
    }


def _expansions_for_mode(mode: str) -> list[str]:
    by_mode = {
        "literature": ["context_pack", "timeline", "relation_map", "note_outline"],
        "writing": ["timeline", "note_outline", "source_reconstruction", "trust_audit"],
        "synthesis": ["timeline", "relation_map", "source_reconstruction", "trust_audit"],
        "closeout": ["timeline", "recording_navigation", "context_pack"],
        "code_numerical": ["timeline", "relation_map", "process_graph", "recording_navigation"],
        "derivation": ["timeline", "relation_map", "note_outline", "recording_navigation"],
    }
    return by_mode.get(mode, ["context_pack", "timeline", "relation_map", "recording_navigation"])


def _allowed_expansions() -> list[str]:
    return [
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
    ]

def _expansion_name(expansion: str) -> str:
    clean = str(expansion or "context_pack").strip().lower().replace("-", "_")
    aliases = {
        "context": "context_pack",
        "execution_brief": "brief",
        "continuation": "timeline",
        "research_timeline": "timeline",
        "claim_relation_map": "relation_map",
        "recording": "recording_navigation",
        "source": "source_reconstruction",
        "trust": "trust_audit",
    }
    return aliases.get(clean, clean)


def _expand_record_refs(
    ws: WorkspacePaths,
    *,
    refs: list[str] | tuple[str, ...],
    offset: int,
    limit: int,
) -> dict[str, Any]:
    unique_refs = list(dict.fromkeys(str(ref).strip() for ref in refs if str(ref).strip()))
    bounded_refs = unique_refs[:50]
    clean_offset = max(0, int(offset))
    page_size = max(1, min(int(limit), 20))
    page_refs = bounded_refs[clean_offset : clean_offset + page_size]
    if not page_refs:
        return {
            "ok": False,
            "kind": "record_ref_expansion",
            "error": "record_refs expansion requires at least one ref in the requested page",
            "requested_ref_count": len(unique_refs),
            "offset": clean_offset,
            "limit": page_size,
            "summary_inputs_trusted": False,
            "orientation_only": True,
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
        }
    result = exact_expand(ws, page_refs, limit=page_size)
    next_offset = clean_offset + page_size
    if next_offset >= len(bounded_refs):
        next_offset = None
    return {
        "ok": True,
        "kind": "record_ref_expansion",
        "items": [asdict(item) for item in result.items],
        "returned_refs": [item.record_ref for item in result.items],
        "unresolved_refs": list(result.excluded_candidates),
        "requested_ref_count": len(unique_refs),
        "bounded_ref_count": len(bounded_refs),
        "input_truncated": len(unique_refs) > len(bounded_refs),
        "offset": clean_offset,
        "limit": page_size,
        "next_offset": next_offset,
        "index_status": result.index_status,
        "index_generation": result.index_generation,
        "coverage": asdict(result.coverage),
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _needs_claim_id(expansion: str) -> dict[str, Any]:
    return {
        "ok": False,
        "kind": "codex_context_expansion",
        "expansion": expansion,
        "error": f"{expansion} requires claim_id",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _literature_action(action: str) -> str:
    clean = str(action or "suggest").strip().lower().replace("-", "_")
    aliases = {
        "record": "record_reference",
        "register": "record_reference",
        "handoff": "source_review_handoff",
        "compare": "comparison_draft",
    }
    return aliases.get(clean, clean)


def _allowed_literature_actions() -> list[str]:
    return ["suggest", "record_reference", "source_review_handoff", "comparison_draft"]


def _reference_layers() -> list[dict[str, str]]:
    return [
        {
            "layer": "source_identity",
            "record": "source_asset",
            "rule": "A paper, web page, dataset, repository, or local note exists.",
        },
        {
            "layer": "source_location",
            "record": "reference_location",
            "rule": "Exact page, equation, section, URL, timestamp, or local path.",
        },
        {
            "layer": "reading_artifact",
            "record": "artifact or sensemaking_report",
            "rule": "Reusable reading note or comparison draft; not claim support by itself.",
        },
        {
            "layer": "claim_link",
            "record": "evidence",
            "rule": "Only after a source statement is explicitly tied to one claim and scoped output.",
        },
        {
            "layer": "physical_content",
            "record": "physics_object or object_relation",
            "rule": "Definitions, assumptions, equations, objects, regimes, or relations extracted from the source.",
        },
        {
            "layer": "validation_basis",
            "record": "validation_contract or validation_result link",
            "rule": "The source defines a check, benchmark, or failure mode.",
        },
        {
            "layer": "trust_basis",
            "record": "trust preflight, checkpoint, or promotion packet",
            "rule": "Only after typed evidence/validation and the required gate.",
        },
    ]


def codex_record_apply(
    ws: WorkspacePaths,
    *,
    session_id: str,
    slot: str,
    payload: dict[str, Any] | None = None,
    event_type: str = "",
    summary: str = "",
    claim_id: str = "",
    expected_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Apply one constrained typed write selected through the Codex recording navigator."""

    selected = _record_apply_slot(slot)
    data = dict(payload or {})
    focus = recover_session_binding_for_read(ws, session_id)
    session = focus.session
    topic_id = str(data.pop("topic_id", "") or session.topic_id)
    active_claim = str(data.pop("claim_id", "") or claim_id or session.active_claim)
    try:
        record = _apply_record_slot(
            ws,
            selected,
            topic_id=topic_id,
            claim_id=active_claim,
            session_id=session.session_id,
            data=data,
            fallback_summary=summary,
        )
    except Exception as exc:
        return {
            "ok": False,
            "kind": "codex_record_apply",
            "session_id": session.session_id,
            "requested_session_id": focus.requested_session_id,
            "slot": selected,
            "event_type": event_type,
            "write_executed": False,
            "error": f"{type(exc).__name__}: {exc}",
            "allowed_slots": _record_apply_slots(),
            "truth_source": "typed_records_and_recording_navigator",
            "summary_inputs_trusted": False,
            "orientation_only": True,
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
        }

    record_ref = _record_ref_for_slot(selected, record)
    verify_refs = list(expected_refs or [])
    if record_ref and record_ref not in verify_refs:
        verify_refs.append(record_ref)
    verification = (
        verify_recording_effect(ws, session.session_id, expected_refs=verify_refs, claim_id=active_claim)
        if verify_refs
        else {}
    )
    return {
        "ok": True,
        "kind": "codex_record_apply",
        "session_id": session.session_id,
        "requested_session_id": focus.requested_session_id,
        "slot": selected,
        "event_type": event_type,
        "topic_id": topic_id,
        "claim_id": active_claim,
        "record_ref": record_ref,
        "record": {"ok": True, **asdict(record)},
        "verification": verification,
        "write_executed": True,
        "kernel_state_change": f"{selected}_record",
        "trust_update_forbidden": True,
        "truth_source": "typed_records_and_recording_navigator",
        "summary_inputs_trusted": False,
        "orientation_only": False,
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }


def _record_apply_slot(slot: str) -> str:
    clean = str(slot or "").strip().lower().replace("-", "_")
    aliases = {
        "source": "source_asset",
        "source_identity": "source_asset",
        "reference": "reference_location",
        "ref": "reference_location",
        "artifact_ref": "artifact",
        "recipe": "tool_recipe",
        "tool": "tool_recipe",
        "code": "code_state",
        "code_state_auto": "code_state",
        "capture_code_state": "code_state",
        "physics": "physics_object",
        "object": "physics_object",
        "relation": "object_relation",
        "sensemaking": "sensemaking_report",
        "proof_gap": "proof_obligation",
        "validation": "validation_result",
    }
    clean = aliases.get(clean, clean)
    if clean not in _record_apply_slots():
        raise ValueError(f"unsupported Codex record apply slot: {slot}")
    return clean


def _record_apply_slots() -> list[str]:
    return [
        "source_asset",
        "reference_location",
        "artifact",
        "evidence",
        "physics_object",
        "object_relation",
        "sensemaking_report",
        "proof_obligation",
        "tool_recipe",
        "code_state",
        "tool_run",
        "validation_contract",
        "validation_result",
    ]


def _apply_record_slot(
    ws: WorkspacePaths,
    slot: str,
    *,
    topic_id: str,
    claim_id: str,
    session_id: str,
    data: dict[str, Any],
    fallback_summary: str,
) -> Any:
    if slot == "source_asset":
        label_value = _pop_str(data, "label", "")
        title_value = _pop_str(data, "title", label_value)
        return register_source_asset(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            asset_type=_pop_str(data, "asset_type", "paper"),
            uri=_pop_required(data, "uri"),
            title=title_value,
            label=label_value,
            content_hash=_pop_str(data, "content_hash", ""),
            hash_algorithm=_pop_str(data, "hash_algorithm", ""),
            version_anchor=_pop_dict(data, "version_anchor"),
            acquired_at=_pop_str(data, "acquired_at", ""),
            source_kind=_pop_str(data, "source_kind", "codex_record_apply"),
            summary=_pop_str(data, "summary", fallback_summary),
            source_refs=_pop_list(data, "source_refs"),
            artifact_ids=_pop_list(data, "artifact_ids"),
            code_state_ids=_pop_list(data, "code_state_ids"),
            reference_location_ids=_pop_list(data, "reference_location_ids"),
            derived_from=_pop_list(data, "derived_from"),
            metadata=_pop_dict(data, "metadata"),
            linked_records=_pop_dict(data, "linked_records"),
        )
    if slot == "reference_location":
        return record_reference_location(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            connector_id=_pop_str(data, "connector_id", "manual"),
            location_type=_pop_str(data, "location_type", "source"),
            uri=_pop_required(data, "uri"),
            label=_pop_required(data, "label"),
            source_ref=_pop_str(data, "source_ref", ""),
            external_id=_pop_str(data, "external_id", ""),
            status=_pop_str(data, "status", "located"),
            summary=_pop_str(data, "summary", fallback_summary),
            metadata=_pop_dict(data, "metadata"),
            linked_records=_pop_dict(data, "linked_records"),
        )
    if slot == "artifact":
        uri = _normalize_artifact_uri(_pop_required(data, "uri"))
        return attach_artifact(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            artifact_type=_pop_required(data, "artifact_type"),
            uri=uri,
            summary=_pop_str(data, "summary", fallback_summary),
            size_bytes=data.pop("size_bytes", 0),
            metadata=_pop_dict(data, "metadata"),
        )
    if slot == "evidence":
        return record_evidence(
            ws,
            topic_id=topic_id,
            claim_id=_require_claim(claim_id, slot),
            evidence_type=_pop_required(data, "evidence_type"),
            status=_pop_required(data, "status"),
            summary=_pop_str(data, "summary", fallback_summary),
            supports_outputs=_pop_list(data, "supports_outputs"),
            source_refs=_pop_list(data, "source_refs"),
            tool_run_ids=_pop_list(data, "tool_run_ids"),
            validation_result_ids=_pop_list(data, "validation_result_ids"),
            artifact_ids=_pop_list(data, "artifact_ids"),
            body=data.pop("body", None),
        )
    if slot == "physics_object":
        linked = _pop_dict(data, "linked_records")
        if claim_id:
            linked.setdefault("claim_id", claim_id)
        return record_physics_object(
            ws,
            topic_id=topic_id,
            object_type=_pop_required(data, "object_type"),
            name=_pop_required(data, "name"),
            definition=_pop_required(data, "definition"),
            notation=_pop_str(data, "notation", ""),
            assumptions=_pop_list(data, "assumptions"),
            source_refs=_pop_list(data, "source_refs"),
            metadata=_pop_dict(data, "metadata"),
            linked_records=linked,
            status=_pop_str(data, "status", "active"),
        )
    if slot == "object_relation":
        return record_object_relation(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            relation_type=_pop_required(data, "relation_type"),
            subject_id=_pop_required(data, "subject_id"),
            object_id=_pop_required(data, "object_id"),
            statement=_pop_required(data, "statement"),
            assumptions=_pop_list(data, "assumptions"),
            failure_modes=_pop_list(data, "failure_modes"),
            source_refs=_pop_list(data, "source_refs"),
            evidence_refs=_pop_list(data, "evidence_refs"),
            metadata=_pop_dict(data, "metadata"),
            status=_pop_str(data, "status", "hypothesis"),
        )
    if slot == "sensemaking_report":
        return record_sensemaking_report(
            ws,
            topic_id=topic_id,
            claim_id=_require_claim(claim_id, slot),
            title=_pop_required(data, "title"),
            summary=_pop_str(data, "summary", fallback_summary),
            object_ids=_pop_list(data, "object_ids"),
            relation_ids=_pop_list(data, "relation_ids"),
            evidence_refs=_pop_list(data, "evidence_refs"),
            open_questions=_pop_list(data, "open_questions"),
            next_actions=_pop_list(data, "next_actions"),
            validation_status=_pop_str(data, "validation_status", "not_validation"),
        )
    if slot == "proof_obligation":
        return create_proof_obligation(
            ws,
            topic_id=topic_id,
            claim_id=_require_claim(claim_id, slot),
            statement=_pop_required(data, "statement"),
            obligation_type=_pop_str(data, "obligation_type", "open_gap"),
            status=_pop_str(data, "status", "open"),
            maturity_level=_pop_str(data, "maturity_level", "exploratory"),
            next_action=_pop_str(data, "next_action", "decide next proof or validation step"),
            required_evidence=_pop_list(data, "required_evidence"),
            proof_strategy=_pop_list(data, "proof_strategy"),
            failure_modes=_pop_list(data, "failure_modes"),
            source_refs=_pop_list(data, "source_refs"),
            evidence_refs=_pop_list(data, "evidence_refs"),
            artifact_ids=_pop_list(data, "artifact_ids"),
            human_gate_required=bool(data.pop("human_gate_required", True)),
        )
    if slot == "tool_recipe":
        return register_tool_recipe(
            ws,
            recipe_id=_pop_required(data, "recipe_id"),
            tool_family=_pop_required(data, "tool_family"),
            tool_name=_pop_required(data, "tool_name"),
            purpose=_pop_str(data, "purpose", fallback_summary),
            required_inputs=_pop_list(data, "required_inputs"),
            expected_outputs=_pop_list(data, "expected_outputs"),
            invariants=_pop_list(data, "invariants"),
        )
    if slot == "code_state":
        worktree_path = _pop_required(data, "worktree_path")
        changed_files = [str(item) for item in _pop_list(data, "changed_files")]
        runtime_environment = _pop_dict(data, "runtime_environment")
        runtime_environment = _enrich_code_state_runtime(
            worktree_path=worktree_path,
            changed_files=changed_files,
            runtime_environment=runtime_environment,
        )
        linked_records = _pop_dict(data, "linked_records")
        if topic_id:
            linked_records.setdefault("topic_id", topic_id)
        if claim_id:
            linked_records.setdefault("claim_id", claim_id)
        if session_id:
            linked_records.setdefault("session_id", session_id)
        known_divergence = _pop_str(data, "known_divergence", "")
        if runtime_environment.get("dirty_status_summary"):
            known_divergence = known_divergence or (
                "source tree is dirty; this code_state is not a clean reproducibility anchor"
            )
        return capture_code_state_from_git(
            ws,
            worktree_path=worktree_path,
            repo_id=_pop_str(data, "repo_id", ""),
            topic_id=topic_id,
            claim_id=claim_id,
            session_id=session_id,
            build_config=_pop_dict(data, "build_config"),
            runtime_environment=runtime_environment,
            linked_records=linked_records,
            known_divergence=known_divergence,
            write_patch_artifact=bool(data.pop("write_patch_artifact", False)),
        )
    if slot == "tool_run":
        return record_tool_run(
            ws,
            topic_id=topic_id,
            claim_id=_require_claim(claim_id, slot),
            recipe_id=_pop_required(data, "recipe_id"),
            tool_family=_pop_required(data, "tool_family"),
            tool_name=_pop_required(data, "tool_name"),
            inputs=_pop_dict(data, "inputs"),
            outputs=_pop_dict(data, "outputs"),
            environment=_pop_dict(data, "environment"),
            evidence_status=_pop_str(data, "evidence_status", "unreviewed"),
            code_state_ids=_pop_list(data, "code_state_ids"),
            artifact_ids=_pop_list(data, "artifact_ids"),
            source_refs=_pop_list(data, "source_refs"),
            scientific_run_id=_pop_str(data, "scientific_run_id", ""),
            supersedes=_pop_str(data, "supersedes", ""),
            lane=_pop_str(data, "lane", "diagnostic"),
        )
    if slot == "validation_contract":
        return create_validation_contract(
            ws,
            topic_id=topic_id,
            claim_id=_require_claim(claim_id, slot),
            required_checks=_pop_list(data, "required_checks"),
            failure_modes=_pop_list(data, "failure_modes"),
            required_evidence_outputs=_pop_list(data, "required_evidence_outputs"),
            tool_recipe_ids=_pop_list(data, "tool_recipe_ids"),
            executor_ids=_pop_list(data, "executor_ids"),
            validator_role=_pop_str(data, "validator_role", "adversarial_reviewer"),
        )
    if slot == "validation_result":
        return record_validation_result(
            ws,
            topic_id=topic_id,
            claim_id=_require_claim(claim_id, slot),
            contract_id=_pop_required(data, "contract_id"),
            tool_run_id=_pop_required(data, "tool_run_id"),
            status=_pop_required(data, "status"),
            checked_outputs=_pop_list(data, "checked_outputs"),
            summary=_pop_str(data, "summary", fallback_summary),
            evidence_refs=_pop_list(data, "evidence_refs"),
            artifact_ids=_pop_list(data, "artifact_ids"),
            covered_failure_modes=_pop_list(data, "covered_failure_modes"),
            failure_modes_observed=_pop_list(data, "failure_modes_observed"),
        )
    raise ValueError(f"unsupported slot: {slot}")


def _record_ref_for_slot(slot: str, record: Any) -> str:
    fields = {
        "source_asset": ("source_asset", "asset_id"),
        "reference_location": ("reference_location", "location_id"),
        "artifact": ("artifact", "artifact_id"),
        "evidence": ("evidence", "evidence_id"),
        "physics_object": ("physics_object", "object_id"),
        "object_relation": ("object_relation", "relation_id"),
        "sensemaking_report": ("sensemaking_report", "report_id"),
        "proof_obligation": ("proof_obligation", "obligation_id"),
        "tool_recipe": ("tool_recipe", "recipe_id"),
        "code_state": ("code_state", "code_state_id"),
        "tool_run": ("tool_run", "run_id"),
        "validation_contract": ("validation_contract", "contract_id"),
        "validation_result": ("validation_result", "result_id"),
    }
    prefix, attr = fields[slot]
    return f"{prefix}:{getattr(record, attr)}"


def _pop_required(data: dict[str, Any], key: str) -> str:
    value = str(data.pop(key, "") or "").strip()
    if not value:
        raise ValueError(f"payload.{key} is required")
    return value


def _pop_str(data: dict[str, Any], key: str, default: str) -> str:
    return str(data.pop(key, default) or "")


def _pop_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.pop(key, None)
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _pop_dict(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.pop(key, None)
    return value if isinstance(value, dict) else {}


def _require_claim(claim_id: str, slot: str) -> str:
    if not claim_id:
        raise ValueError(f"{slot} requires an active claim_id")
    return claim_id


def _normalize_artifact_uri(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    for prefix in ("local:file:", "path:", "file:"):
        if lowered.startswith(prefix) and not lowered.startswith("file://"):
            rest = text[len(prefix) :].strip()
            if _looks_like_windows_drive_path(rest):
                return "file:///" + rest.replace("\\", "/")
            if rest.startswith(("/", "\\")):
                return "file://" + rest.replace("\\", "/")
            return rest or text
    return text


def _looks_like_windows_drive_path(value: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:[\\/]", str(value or "")))


def _enrich_code_state_runtime(
    *,
    worktree_path: str,
    changed_files: list[str],
    runtime_environment: dict[str, Any],
) -> dict[str, Any]:
    runtime = dict(runtime_environment or {})
    runtime.setdefault("changed_files_relevant", changed_files)
    status_lines = _git_status_lines(worktree_path)
    runtime.setdefault("dirty_status_summary", status_lines)
    runtime.setdefault("changed_files_tracking", _changed_file_tracking(worktree_path, changed_files, status_lines))
    runtime.setdefault("clean_reproducibility_anchor", not status_lines)
    if status_lines:
        runtime.setdefault(
            "dirty_reproducibility_note",
            "source tree is dirty; this code_state is not a clean reproducibility anchor",
        )
    return runtime


def _git_status_lines(worktree_path: str) -> list[str]:
    root = _git_root(worktree_path)
    if root is None:
        return []
    result = _run_git(root, ["status", "--porcelain=v1"])
    return [line for line in result.splitlines() if line.strip()]


def _changed_file_tracking(worktree_path: str, changed_files: list[str], status_lines: list[str]) -> list[dict[str, Any]]:
    if not changed_files:
        return []
    root = _git_root(worktree_path)
    status_by_path = _status_by_path(status_lines)
    rows: list[dict[str, Any]] = []
    for value in changed_files:
        rel_path = _relative_git_path(root, value)
        status = status_by_path.get(rel_path, "")
        rows.append(
            {
                "path": value,
                "git_path": rel_path,
                "tracked": _is_tracked(root, rel_path) if root is not None else False,
                "status": status or "clean_or_not_reported_by_git_status",
                "untracked": status.startswith("??"),
            }
        )
    return rows


def _git_root(worktree_path: str) -> Path | None:
    worktree = Path(worktree_path).expanduser()
    result = _run_git(worktree, ["rev-parse", "--show-toplevel"])
    return Path(result) if result else None


def _run_git(cwd: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip()


def _status_by_path(status_lines: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for line in status_lines:
        if len(line) < 4:
            continue
        status = line[:2]
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        mapping[path.replace("\\", "/")] = status
    return mapping


def _relative_git_path(root: Path | None, value: str) -> str:
    text = _normalize_artifact_uri(str(value or "").strip())
    if text.startswith("file:///"):
        text = text[len("file:///") :]
    elif text.startswith("file://"):
        text = text[len("file://") :]
    path = Path(text)
    if root is not None:
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except (OSError, ValueError):
            pass
    return text.replace("\\", "/")


def _is_tracked(root: Path | None, git_path: str) -> bool:
    if root is None or not git_path:
        return False
    try:
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", git_path],
            cwd=str(root),
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    return True
