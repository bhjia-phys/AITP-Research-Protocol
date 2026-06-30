"""Codex App facade surfaces for compact, progressive AITP v5 use."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.brief import build_execution_brief
from brain.v5.claim_relation_map import build_claim_relation_map
from brain.v5.context_pack import build_aitp_context_pack
from brain.v5.evidence import record_evidence
from brain.v5.literature_comparison_draft import build_literature_comparison_draft
from brain.v5.literature_intake import record_literature_candidate, suggest_literature_intake
from brain.v5.literature_source_review_handoff import build_literature_source_review_handoff
from brain.v5.note_outline import compile_note_outline
from brain.v5.paths import WorkspacePaths
from brain.v5.physics_objects import record_object_relation, record_physics_object
from brain.v5.process_graph import build_process_graph_slice
from brain.v5.quiet_checkpoint import apply_quiet_checkpoint_batch, preview_quiet_checkpoint_batch
from brain.v5.recovery_session import recover_session_binding_for_read
from brain.v5.references import record_reference_location
from brain.v5.recording_navigator import (
    build_recording_navigation_state,
    classify_recording_candidate,
    expand_recording_slot,
    verify_recording_effect,
)
from brain.v5.research_state import attach_artifact, create_proof_obligation
from brain.v5.sensemaking import record_sensemaking_report
from brain.v5.source_assets import register_source_asset
from brain.v5.source_reconstruction import audit_source_reconstruction
from brain.v5.tools import record_tool_run
from brain.v5.trust_audit import audit_claim_trust
from brain.v5.validation import create_validation_contract, record_validation_result
from brain.v5.workspace_recovery_audit import build_workspace_recovery_audit, compact_workspace_recovery_audit
from brain.v5.workspace_recording_audit import build_workspace_recording_audit


CODEX_FACADE_TOOLS: tuple[str, ...] = (
    "aitp_v5_codex_tool_catalog",
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
            "start_with": "aitp_v5_codex_enter",
            "expand_with": "aitp_v5_codex_expand",
            "record_with": "aitp_v5_codex_recording_step_then_aitp_v5_codex_record_apply",
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
            "deepest_layer_write_tool": "aitp_v5_codex_record_apply",
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
        return attach_artifact(
            ws,
            topic_id=topic_id,
            claim_id=claim_id,
            artifact_type=_pop_required(data, "artifact_type"),
            uri=_pop_required(data, "uri"),
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
