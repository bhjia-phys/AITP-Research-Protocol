# Compatibility shard 1 for mcp_tools.
from __future__ import annotations

from dataclasses import asdict

from importlib import import_module

import os

from pathlib import Path

import re

from brain.v5.adapter_protocols import adapter_protocol_registry, record_gate_coverage_audit

from brain.v5.adapter_runtime import evaluate_platform_pre_tool_event

from brain.v5.adapters import build_adapter_packet

from brain.v5.active_claim_focus import (
    confirm_active_claim_rebind,
    detect_active_claim_focus_drift,
    propose_active_claim_rebind,
)

from brain.v5.authorities import authority_record_payload, authority_registry_payload, record_authority

from brain.v5.brief import build_execution_brief

from brain.v5.claim_relation_map import build_claim_relation_map, empty_claim_relation_map

from brain.v5.code import capture_code_state_from_git, record_code_state

from brain.v5.codex_facade import (
    codex_autoroute,
    codex_closeout,
    codex_enter_context,
    codex_expand_context,
    codex_literature_step,
    codex_record_apply,
    codex_recording_step,
    codex_tool_catalog,
)

from brain.v5.context_pack import build_aitp_context_pack

from brain.v5.context_profile_drafts import build_context_profile_draft

from brain.v5.context_profile_templates import build_context_profile_template_catalog

from brain.v5.curated_rag_corpus import (
    curated_rag_corpus,
    draft_curated_rag_promotion,
    ingest_curated_rag_corpus,
    read_curated_rag_chunk,
    search_curated_rag_corpus,
)

from brain.v5.exploration import exploratory_record_payload, record_exploratory_record

from brain.v5.final_readiness import audit_final_engineering_readiness

from brain.v5.harness_feedback import build_nio_harness_feedback_bundle, plan_run_dir_provenance_extractor

from brain.v5.hook_install_audit import audit_hook_installation

from brain.v5.hook_install_paths import discover_hook_install_paths

from brain.v5.hook_install_templates import (
    install_claude_code_hook_settings,
    write_claude_code_hook_settings,
    write_codex_hook_bridge,
    write_opencode_plugin_bridge,
)

from brain.v5.mcp_base_resolution import resolve_workspace_base

from brain.v5.mcp_context import (
    aitp_v5_compile_research_context,
    aitp_v5_get_capability_registry,
    aitp_v5_get_runtime_capability_audit,
)

from brain.v5.mcp_query import (
    aitp_v5_build_query_index,
    aitp_v5_exact_expand_records,
    aitp_v5_get_query_index_status,
)

from brain.v5.mcp_domain_packs import aitp_v5_build_domain_skill_shim_manifest, aitp_v5_list_domain_packs, aitp_v5_suggest_domain_packs_for_claim

from brain.v5.mcp_kimi_hooks import aitp_v5_install_kimi_code_hook_config, aitp_v5_write_kimi_code_hook_config

from brain.v5.mcp_legacy import aitp_v5_apply_legacy_semantic_repair, aitp_v5_apply_legacy_source_reconstruction_repair, aitp_v5_audit_canonical_legacy_l2_seeds, aitp_v5_build_canonical_legacy_l2_seed_review_worklist, aitp_v5_audit_legacy_migration_coverage, aitp_v5_build_legacy_executable_evidence_packet, aitp_v5_build_legacy_human_checkpoint_packet, aitp_v5_build_legacy_l2_graph_manifest, aitp_v5_build_legacy_l2_typed_migration_packet, aitp_v5_build_legacy_runtime_log_marker_audit, aitp_v5_build_legacy_semantic_needs_revision_basis_packet, aitp_v5_build_legacy_semantic_needs_revision_basis_queue, aitp_v5_build_legacy_semantic_repair_manifest, aitp_v5_build_legacy_semantic_repair_plan, aitp_v5_build_legacy_semantic_review_manifest, aitp_v5_build_legacy_semantic_review_packet, aitp_v5_build_legacy_semantic_review_queue, aitp_v5_build_legacy_semantic_review_worklist, aitp_v5_build_legacy_source_metadata_repair_packet, aitp_v5_build_legacy_source_reconstruction_manifest, aitp_v5_build_legacy_source_reconstruction_plan, aitp_v5_build_legacy_source_reconstruction_review_packet, aitp_v5_build_legacy_topic_question_backfill_packet, aitp_v5_list_curated_legacy_topics, aitp_v5_migrate_curated_legacy_topic_to_v5, aitp_v5_migrate_legacy_topic_to_v5, aitp_v5_record_legacy_l2_seed_group_review_result, aitp_v5_record_legacy_semantic_review_result, aitp_v5_write_legacy_human_checkpoint_obsidian_view, aitp_v5_write_legacy_l2_obsidian_view, aitp_v5_write_legacy_migration_accounting_run, aitp_v5_write_legacy_semantic_needs_revision_basis_obsidian_view, aitp_v5_write_legacy_semantic_review_obsidian_view, aitp_v5_write_legacy_source_reconstruction_obsidian_view

from brain.v5.hook_smoke_coverage import runtime_hook_smoke_coverage_report

from brain.v5.knowledge_connectors import describe_knowledge_connectors

from brain.v5.models import CodeStateRecord, TrustUpdateRequest

from brain.v5.note_outline import compile_note_outline

from brain.v5.objective_graph import build_compact_brief, build_objective_graph

from brain.v5.pretool_policy import evaluate_context_pre_tool_policy

from brain.v5.public_surfaces import describe_public_surfaces, require_valid_public_surface

from brain.v5.quiet_checkpoint import apply_quiet_checkpoint_batch, preview_quiet_checkpoint_batch

from brain.v5.research_distillation import build_research_distillation_candidates

from brain.v5.research_timeline import build_research_timeline

from brain.v5.record_refs import lookup_record_refs

from brain.v5.recording_navigator import (
    build_recording_navigation_state,
    classify_recording_candidate,
    expand_recording_slot,
    verify_recording_effect,
)

from brain.v5.physics_objects import record_object_relation, record_physics_object

from brain.v5.process_graph import build_process_graph_slice

from brain.v5.references import record_reference_location

from brain.v5.routes import record_research_route, research_route_payload

from brain.v5.runtime_bridge_targets import runtime_bridge_target_manifest

from brain.v5.runtime_mcp_bridge_acceptance import audit_runtime_mcp_bridge_acceptance

from brain.v5.runtime_payload_profiles import runtime_payload_profiles

from brain.v5.sensemaking import record_sensemaking_report

from brain.v5.source_assets import (
    acquire_arxiv_source_asset,
    acquire_pdf_source_asset,
    capture_source_asset_from_local_path,
    register_source_asset,
    source_asset_payload,
)

from brain.v5.validation import create_validation_contract, record_validation_result

from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint

from brain.v5.memory import apply_promotion_packet, create_promotion_packet

from brain.v5.mcp_evidence import aitp_v5_record_evidence

from brain.v5.mcp_lifecycle import (
    aitp_v5_apply_rehome_plan,
    aitp_v5_audit_record_routing,
    aitp_v5_build_rehome_plan,
    aitp_v5_supersede_record,
)

from brain.v5.mcp_host_readiness import aitp_v5_audit_priority_host_production_loops, aitp_v5_audit_runtime_host_lifecycle, aitp_v5_audit_runtime_host_readiness

from brain.v5.mcp_hook_install import aitp_v5_install_codex_hook_fixture, aitp_v5_install_opencode_hook_fixture

from brain.v5.mcp_interaction import aitp_v5_build_interaction_recording_worklist, aitp_v5_build_workspace_interaction_preview, aitp_v5_preview_interaction_recording

from brain.v5.mcp_knowledge_bindings import aitp_v5_bind_knowledge_connector, aitp_v5_list_knowledge_connector_bindings

from brain.v5.mcp_lane_exemplars import (
    aitp_v5_build_lane_exemplar_manifest,
    aitp_v5_record_lane_exemplar,
    aitp_v5_record_librpa_code_backed_algorithm_exemplar,
    aitp_v5_record_qft_qg_source_reconstruction_exemplar,
    aitp_v5_record_toy_numeric_finite_size_exemplar,
)

from brain.v5.mcp_literature import aitp_v5_build_literature_comparison_draft, aitp_v5_build_literature_corpus_extraction_artifact, aitp_v5_build_literature_extraction_report, aitp_v5_build_literature_reading_route, aitp_v5_build_literature_source_extraction_candidates, aitp_v5_build_literature_source_set_readiness, aitp_v5_build_literature_source_review_handoff, aitp_v5_record_literature_candidate, aitp_v5_suggest_literature_intake

from brain.v5.mcp_memory import aitp_v5_audit_failure_mode_coverage, aitp_v5_audit_l2_memory_context, aitp_v5_build_failure_mode_review_packet, aitp_v5_record_failure_mode_review_result, aitp_v5_request_failure_mode_review_checkpoint, aitp_v5_write_l2_obsidian_view

from brain.v5.mcp_operator_checkpoint import aitp_v5_answer_operator_checkpoint, aitp_v5_request_operator_checkpoint

from brain.v5.mcp_output_stability import aitp_v5_build_vnext_readiness_manifest, aitp_v5_record_final_output_profile

from brain.v5.mcp_qsgw_cockpit import aitp_v5_write_qsgw_cockpit_surfaces, aitp_v5_write_qsgw_cockpit_surfaces_compact

from brain.v5.mcp_research_cockpit import aitp_v5_write_research_cockpit_surfaces, aitp_v5_write_research_cockpit_surfaces_compact

from brain.v5.mcp_research_state import aitp_v5_attach_artifact, aitp_v5_attach_artifact_auto, aitp_v5_classify_research_event, aitp_v5_create_proof_obligation, aitp_v5_record_bounded_numerical_evidence, aitp_v5_register_source, aitp_v5_update_claim_status, aitp_v5_update_proof_obligation

from brain.v5.mcp_research_intent import aitp_v5_materialize_steering_redirect, aitp_v5_record_research_intent_packet

from brain.v5.mcp_research_runs import aitp_v5_record_research_run_event, aitp_v5_start_research_run, aitp_v5_update_research_run

from brain.v5.mcp_lane_contracts import aitp_v5_record_lane_contract

from brain.v5.mcp_hpc_cockpit import aitp_v5_hpc_cockpit

from brain.v5.mcp_run_iterations import aitp_v5_record_run_iteration

from brain.v5.mcp_source import aitp_v5_audit_source_reconstruction, aitp_v5_build_source_reconstruction_manifest, aitp_v5_build_source_reconstruction_review_manifest, aitp_v5_build_source_reconstruction_review_packet, aitp_v5_build_source_stack_coverage_manifest, aitp_v5_record_source_reconstruction_review_result, aitp_v5_write_source_reconstruction_obsidian_view

from brain.v5.mcp_strategy_memory import aitp_v5_record_strategy_memory

from brain.v5.mcp_summaries import aitp_v5_read_summary_orientation, aitp_v5_refresh_workspace_views, aitp_v5_write_session_summary, aitp_v5_write_workspace_replay_packet, aitp_v5_write_workspace_summary

from brain.v5.mcp_topic_status import aitp_v5_write_topic_status_surfaces, aitp_v5_write_topic_status_surfaces_compact

from brain.v5.mcp_trust_audit import aitp_v5_audit_claim_trust

from brain.v5.mcp_goal import aitp_v5_list_goal_continuations, aitp_v5_read_latest_goal_continuation, aitp_v5_write_goal_continuation

from brain.v5.risk import assess_claim_risk

from brain.v5.store import list_records

from brain.v5.subagents import ingest_subagent_result

from brain.v5.tool_executors import describe_tool_executors, execute_registered_tool_result

from brain.v5.tools import capture_tool_run_from_local_path, record_tool_run, register_tool_recipe, tool_run_payload

from brain.v5.trace import persist_hook_trace_event

from brain.v5.trust_updates import apply_trust_update, get_trust_update_record, preflight_trust_update

from brain.v5.workspace import bind_session, create_claim, create_topic, get_claim, init_workspace

from brain.v5.workspace_file_migration_ledger import (
    build_workspace_file_migration_ledger,
    compact_workspace_file_migration_ledger,
    write_workspace_file_migration_ledger,
)

from brain.v5.workspace_migration_health import build_workspace_migration_health

from brain.v5.workspace_old_store_import import (
    apply_workspace_old_store_import_plan,
    build_workspace_old_store_import_plan,
    write_workspace_old_store_import_result,
)

from brain.v5.workspace_recovery_binding_repair import (
    apply_workspace_recovery_binding_repair,
    build_workspace_recovery_binding_repair,
    write_workspace_recovery_binding_repair,
)

from brain.v5.workspace_recovery_audit import (
    build_workspace_recovery_audit,
    compact_workspace_recovery_audit,
    write_workspace_recovery_audit,
)

from brain.v5.workspace_recording_audit import (
    build_workspace_recording_audit,
    write_workspace_recording_audit,
)

def _ws(base: str):
    return init_workspace(resolve_workspace_base(base))

def _resolve_workspace_base(base: str) -> Path:
    """Resolve common agent-provided AITP paths to the v5 topics root.

    Agents sometimes pass the workspace-root `.aitp` directory because older
    AITP layouts used it as a visible control surface.  The v5 canonical store
    for this workspace lives under `<topics-root>/.aitp`; when
    AITP_TOPICS_ROOT is configured by the MCP launcher, prefer that canonical
    root over an ambiguous root-level `.aitp` path.
    """

    return resolve_workspace_base(base)

def _env_topics_root() -> Path | None:
    value = os.environ.get("AITP_TOPICS_ROOT", "").strip()
    return Path(value).expanduser() if value else None

def _looks_like_v5_base(path: Path) -> bool:
    store = path / ".aitp"
    return (store / "workspace.md").exists() or (store / "topics").exists() or (store / "registry").exists()

def _looks_like_v5_store(path: Path) -> bool:
    return path.name == ".aitp" and (
        (path / "workspace.md").exists() or (path / "topics").exists() or (path / "registry").exists()
    )

def _same_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return left.absolute() == right.absolute()

def _safe_bind_session_id(session_id: str, *, topic_id: str) -> str:
    """Normalize read-only topic tokens before writing a SessionBinding file."""

    raw = str(session_id or "").strip()
    if raw.startswith("topic:") or raw.startswith("aitp:topic:"):
        topic = raw.split(":", 1)[-1]
        return f"session-{_slug(topic_id or topic)}-recovery"
    safe = _slug(raw)
    return safe or f"session-{_slug(topic_id or 'unbound')}-recovery"

def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value or "").strip()).strip(".-")
    return text[:160]

def aitp_v5_codex_tool_catalog(profile: str = "entry") -> dict:
    """Return the compact Codex App 1.0 MCP surface catalog."""

    return codex_tool_catalog(profile=profile)

def aitp_v5_codex_autoroute(
    base: str,
    *,
    request_summary: str,
    session_id: str = "",
    topics: list[str] | None = None,
    visible_files: list[str] | None = None,
    recent_tool_summary: str = "",
    semantic_assessment: dict | None = None,
) -> dict:
    """Decide whether Codex should enter AITP before answering."""

    return codex_autoroute(
        None,
        request_summary=request_summary,
        session_id=session_id,
        topics=topics,
        visible_files=visible_files,
        recent_tool_summary=recent_tool_summary,
        semantic_assessment=semantic_assessment,
    )

def aitp_v5_codex_enter(
    base: str,
    *,
    session_id: str = "",
    topics: list[str] | None = None,
    request_summary: str = "",
    process_mode: str = "auto",
    payload_profile: str = "minimal",
    max_lines: int = 60,
    candidate_limit: int = 3,
) -> dict:
    """Enter AITP from Codex with compact context or recovery hints."""

    return codex_enter_context(
        _ws(base),
        session_id=session_id,
        topics=topics,
        request_summary=request_summary,
        process_mode=process_mode,
        payload_profile=payload_profile,
        max_lines=max_lines,
        candidate_limit=candidate_limit,
    )

def aitp_v5_codex_expand(
    base: str,
    *,
    session_id: str,
    expansion: str,
    claim_id: str = "",
    max_lines: int = 60,
    limit: int = 60,
    style: str = "jhep",
    objective_text: str = "",
    user_goal: str = "",
    record_refs: list[str] | None = None,
    offset: int = 0,
) -> dict:
    """Expand one Codex context family on demand."""

    return codex_expand_context(
        _ws(base),
        session_id=session_id,
        expansion=expansion,
        claim_id=claim_id,
        max_lines=max_lines,
        limit=limit,
        style=style,
        objective_text=objective_text,
        user_goal=user_goal,
        record_refs=record_refs,
        offset=offset,
    )

def aitp_v5_codex_recording_step(
    base: str,
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
    candidate: dict | None = None,
    expected_refs: list[str] | None = None,
) -> dict:
    """Classify and expand one durable recording moment without doing the write."""

    return codex_recording_step(
        _ws(base),
        session_id=session_id,
        event_type=event_type,
        summary=summary,
        topic_id=topic_id,
        claim_id=claim_id,
        touched_refs=touched_refs,
        produced_artifacts=produced_artifacts,
        tool_call_id=tool_call_id,
        risk_hint=risk_hint,
        slot=slot,
        candidate=candidate,
        expected_refs=expected_refs,
    )

def aitp_v5_codex_record_apply(
    base: str,
    *,
    session_id: str,
    slot: str,
    payload: dict | None = None,
    event_type: str = "",
    summary: str = "",
    claim_id: str = "",
    expected_refs: list[str] | None = None,
) -> dict:
    """Apply one constrained typed record selected through the Codex facade."""

    return codex_record_apply(
        _ws(base),
        session_id=session_id,
        slot=slot,
        payload=payload,
        event_type=event_type,
        summary=summary,
        claim_id=claim_id,
        expected_refs=expected_refs,
    )
