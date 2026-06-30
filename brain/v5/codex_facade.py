"""Codex App facade surfaces for compact, progressive AITP v5 use."""

from __future__ import annotations

from typing import Any

from brain.v5.brief import build_execution_brief
from brain.v5.claim_relation_map import build_claim_relation_map
from brain.v5.context_pack import build_aitp_context_pack
from brain.v5.literature_comparison_draft import build_literature_comparison_draft
from brain.v5.literature_intake import record_literature_candidate, suggest_literature_intake
from brain.v5.literature_source_review_handoff import build_literature_source_review_handoff
from brain.v5.note_outline import compile_note_outline
from brain.v5.paths import WorkspacePaths
from brain.v5.process_graph import build_process_graph_slice
from brain.v5.quiet_checkpoint import apply_quiet_checkpoint_batch, preview_quiet_checkpoint_batch
from brain.v5.recording_navigator import (
    build_recording_navigation_state,
    classify_recording_candidate,
    expand_recording_slot,
    verify_recording_effect,
)
from brain.v5.source_reconstruction import audit_source_reconstruction
from brain.v5.trust_audit import audit_claim_trust
from brain.v5.workspace_recovery_audit import build_workspace_recovery_audit, compact_workspace_recovery_audit
from brain.v5.workspace_recording_audit import build_workspace_recording_audit


CODEX_FACADE_TOOLS: tuple[str, ...] = (
    "aitp_v5_codex_tool_catalog",
    "aitp_v5_codex_enter",
    "aitp_v5_codex_expand",
    "aitp_v5_codex_recording_step",
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
            "purpose": "Restore a topic/session with compact context and expansion hints.",
            "tools": ["aitp_v5_codex_tool_catalog", "aitp_v5_codex_enter"],
            "state_effect": "read_only",
        },
        "read_expansion": {
            "purpose": "Expand exactly the context family needed by the next research action.",
            "tools": ["aitp_v5_codex_expand"],
            "expansions": [
                "context_pack",
                "brief",
                "relation_map",
                "process_graph",
                "recording_navigation",
                "note_outline",
                "source_reconstruction",
                "trust_audit",
            ],
            "state_effect": "read_only",
        },
        "guided_recording": {
            "purpose": "Classify a durable moment and expand one recording slot before any write.",
            "tools": ["aitp_v5_codex_recording_step"],
            "state_effect": "read_only_until_named_typed_write",
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
            "start_with": "aitp_v5_codex_enter",
            "expand_with": "aitp_v5_codex_expand",
            "record_with": "aitp_v5_codex_recording_step_then_named_typed_write",
            "literature_with": "aitp_v5_codex_literature_step",
            "closeout_with": "aitp_v5_codex_closeout",
        },
        "truth_source": "codex_facade_catalog",
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
    max_lines: int = 60,
    candidate_limit: int = 3,
) -> dict[str, Any]:
    """Enter AITP from Codex with the smallest useful read-only payload."""

    clean_session = str(session_id or "").strip()
    clean_topics = [str(topic).strip() for topic in (topics or []) if str(topic).strip()]
    mode = _process_mode(process_mode, request_summary)
    payload: dict[str, Any] = {
        "ok": True,
        "kind": "codex_entry_context",
        "process_mode": mode,
        "session_id": clean_session,
        "topics": clean_topics,
        "request_summary": str(request_summary or ""),
        "entry_policy": {
            "read_first": True,
            "default_context": "context_pack_when_session_is_known",
            "write_on_entry": False,
            "create_topic_only_after_durable_objective": True,
            "expand_full_graph_only_when_needed": True,
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
            payload["context_pack"] = build_aitp_context_pack(
                ws,
                clean_session,
                max_lines=max_lines,
                candidate_limit=candidate_limit,
                user_goal=request_summary,
            )
            payload["active_session_ready"] = True
            payload["recommended_next_tool"] = "aitp_v5_codex_expand"
            payload["recommended_next_expansions"] = _expansions_for_mode(mode)
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
            "deepest_layer_write_tool_must_be_explicit": True,
        },
        "truth_source": "typed_records_and_event_metadata",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
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
        payload["surface"] = suggest_literature_intake(ws, **common)
        payload["orientation_only"] = True
        payload["can_update_kernel_state"] = False
    elif selected == "record_reference":
        payload["surface"] = record_literature_candidate(ws, **common)
        payload["orientation_only"] = False
        payload["can_update_kernel_state"] = True
        payload["kernel_state_change"] = "reference_location_record_only"
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
    return {
        "ok": True,
        "kind": "codex_closeout",
        "mode": "apply" if apply else "preview",
        "session_id": session_id,
        "surface": surface,
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
    if any(token in text for token in ("note", "draft", "write", "article", "jhep")):
        return "writing"
    if any(token in text for token in ("end", "handoff", "closeout", "summary")):
        return "closeout"
    if any(token in text for token in ("code", "run", "numerical", "hpc", "validation")):
        return "code_numerical"
    return "continuation"


def _expansions_for_mode(mode: str) -> list[str]:
    by_mode = {
        "literature": ["context_pack", "relation_map", "note_outline"],
        "writing": ["note_outline", "source_reconstruction", "trust_audit"],
        "synthesis": ["relation_map", "source_reconstruction", "trust_audit"],
        "closeout": ["recording_navigation", "context_pack"],
        "code_numerical": ["relation_map", "process_graph", "recording_navigation"],
        "derivation": ["relation_map", "note_outline", "recording_navigation"],
    }
    return by_mode.get(mode, ["context_pack", "relation_map", "recording_navigation"])


def _allowed_expansions() -> list[str]:
    return [
        "context_pack",
        "brief",
        "relation_map",
        "process_graph",
        "recording_navigation",
        "note_outline",
        "source_reconstruction",
        "trust_audit",
    ]

def _expansion_name(expansion: str) -> str:
    clean = str(expansion or "context_pack").strip().lower().replace("-", "_")
    aliases = {
        "context": "context_pack",
        "execution_brief": "brief",
        "claim_relation_map": "relation_map",
        "recording": "recording_navigation",
        "source": "source_reconstruction",
        "trust": "trust_audit",
    }
    return aliases.get(clean, clean)


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
