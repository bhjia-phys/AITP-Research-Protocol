"""Thin MCP-facing wrappers around the AITP v5 kernel."""

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
    codex_closeout,
    codex_enter_context,
    codex_expand_context,
    codex_literature_step,
    codex_record_apply,
    codex_recording_step,
    codex_tool_catalog,
)
from brain.v5.context_pack import build_aitp_context_pack
from brain.v5.curated_rag_corpus import (
    curated_rag_corpus,
    draft_curated_rag_promotion,
    ingest_curated_rag_corpus,
    read_curated_rag_chunk,
    search_curated_rag_corpus,
)
from brain.v5.exploration import exploratory_record_payload, record_exploratory_record
from brain.v5.final_readiness import audit_final_engineering_readiness
from brain.v5.hook_install_audit import audit_hook_installation
from brain.v5.hook_install_paths import discover_hook_install_paths
from brain.v5.hook_install_templates import (
    install_claude_code_hook_settings,
    write_claude_code_hook_settings,
    write_codex_hook_bridge,
    write_opencode_plugin_bridge,
)
from brain.v5.mcp_base_resolution import resolve_workspace_base
from brain.v5.mcp_domain_packs import aitp_v5_list_domain_packs, aitp_v5_suggest_domain_packs_for_claim
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
from brain.v5.mcp_lane_exemplars import aitp_v5_build_lane_exemplar_manifest, aitp_v5_record_lane_exemplar
from brain.v5.mcp_literature import aitp_v5_build_literature_comparison_draft, aitp_v5_build_literature_source_extraction_candidates, aitp_v5_build_literature_source_review_handoff, aitp_v5_record_literature_candidate, aitp_v5_suggest_literature_intake
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


def aitp_v5_codex_enter(
    base: str,
    *,
    session_id: str = "",
    topics: list[str] | None = None,
    request_summary: str = "",
    process_mode: str = "auto",
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


def aitp_v5_codex_literature_step(
    base: str,
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
) -> dict:
    """Run a layered literature/reference workflow step from Codex."""

    return codex_literature_step(
        _ws(base),
        session_id=session_id,
        uri=uri,
        label=label,
        action=action,
        external_id=external_id,
        short_summary=short_summary,
        detected_relevance=detected_relevance,
        optional_claim_id=optional_claim_id,
        scoped_output=scoped_output,
        reviewed_refs=reviewed_refs,
        comparison_question=comparison_question,
        source_refs=source_refs,
        dimensions=dimensions,
        rationale=rationale,
        asset_type=asset_type,
    )


def aitp_v5_codex_closeout(
    base: str,
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
) -> dict:
    """Preview or apply a quiet closeout checkpoint without trust mutation."""

    return codex_closeout(
        _ws(base),
        session_id=session_id,
        summary=summary,
        apply=apply,
        claim_id=claim_id,
        run_id=run_id,
        inputs=inputs,
        outputs=outputs,
        changed_files=changed_files,
        generated_artifacts=generated_artifacts,
        validation_commands=validation_commands,
        durable_observations=durable_observations,
        claim_boundary=claim_boundary,
        next_blockers=next_blockers,
        artifact_specs=artifact_specs,
        source_specs=source_specs,
        tool_run_specs=tool_run_specs,
        sensemaking_summary=sensemaking_summary,
        source_refs=source_refs,
    )


def aitp_v5_init_workspace(base: str) -> dict:
    return {"ok": True, "workspace_root": str(_ws(base).root)}


def aitp_v5_create_topic(base: str, *, topic_id: str, context_id: str, title: str) -> dict:
    return {"ok": True, **asdict(create_topic(_ws(base), topic_id, context_id=context_id, title=title))}


def aitp_v5_create_claim(
    base: str, *, topic_id: str, statement: str, evidence_profile: str,
    confidence_state: str, active_uncertainty: str, recipe_id: str = "",
    scope: str = "", non_claims: str = "", strongest_failure_mode: str = "",
) -> dict:
    claim = create_claim(_ws(base), topic_id=topic_id, statement=statement,
        evidence_profile=evidence_profile, confidence_state=confidence_state,
        active_uncertainty=active_uncertainty, recipe_id=recipe_id,
        scope=scope, non_claims=non_claims, strongest_failure_mode=strongest_failure_mode)
    return {"ok": True, **asdict(claim)}


def aitp_v5_bind_session(
    base: str, *, session_id: str, topic_id: str, context_id: str,
    active_claim: str = "", interaction_profile: str = "collaborator", interaction_steering: str = "",
) -> dict:
    requested_session_id = session_id
    safe_session_id = _safe_bind_session_id(session_id, topic_id=topic_id)
    session = bind_session(_ws(base), safe_session_id, topic_id=topic_id, context_id=context_id,
        active_claim=active_claim, interaction_profile=interaction_profile,
        interaction_steering=interaction_steering)
    return {"ok": True, "requested_session_id": requested_session_id, **asdict(session)}


def aitp_v5_get_execution_brief(base: str, *, session_id: str) -> dict:
    try:
        brief = build_execution_brief(_ws(base), session_id)
    except TypeError as error:
        if "SessionBinding.__init__()" not in str(error):
            raise
        brief = _unbound_session_execution_brief(session_id)
    return require_valid_public_surface("execution_brief", brief)


def aitp_v5_get_claim_relation_map(
    base: str,
    *,
    session_id: str,
    objective_text: str = "",
    user_goal: str = "",
) -> dict:
    """Return the derived relation map and conclusion boundary for the active claim."""

    try:
        relation_map = build_claim_relation_map(
            _ws(base),
            session_id,
            objective_text=objective_text,
            user_goal=user_goal,
        )
    except TypeError as error:
        if "SessionBinding.__init__()" not in str(error):
            raise
        relation_map = empty_claim_relation_map(
            topic_id="unbound-session",
            session_id=session_id,
            reason="session binding is missing or malformed",
        )
    return require_valid_public_surface(
        "claim_relation_map",
        relation_map,
    )


def aitp_v5_get_objective_graph(base: str, *, session_id: str) -> dict:
    """Return a read-only objective/work-package projection for the session."""

    return require_valid_public_surface("objective_graph", build_objective_graph(_ws(base), session_id))


def aitp_v5_get_compact_brief(
    base: str,
    *,
    session_id: str,
    max_lines: int = 40,
    objective_text: str = "",
    user_goal: str = "",
) -> dict:
    """Return a short continuation brief; full brief/relation-map remain explicit."""

    return require_valid_public_surface(
        "compact_execution_brief",
        build_compact_brief(
            _ws(base),
            session_id,
            max_lines=max_lines,
            objective_text=objective_text,
            user_goal=user_goal,
        ),
    )


def aitp_v5_get_context_pack(
    base: str,
    *,
    session_id: str,
    max_lines: int = 60,
    candidate_limit: int = 3,
    objective_text: str = "",
    user_goal: str = "",
    task_profile: str = "",
) -> dict:
    """Return a Codex-friendly bounded context pack for turn-input injection."""

    return require_valid_public_surface(
        "aitp_context_pack",
        build_aitp_context_pack(
            _ws(base),
            session_id,
            max_lines=max_lines,
            candidate_limit=candidate_limit,
            objective_text=objective_text,
            user_goal=user_goal,
            task_profile=task_profile,
        ),
    )


def aitp_v5_detect_active_claim_focus_drift(
    base: str,
    *,
    session_id: str,
    objective_text: str = "",
    user_goal: str = "",
    candidate_limit: int = 5,
) -> dict:
    """Detect active-claim focus drift without changing any binding or trust state."""

    return require_valid_public_surface(
        "active_claim_focus_reconciliation",
        detect_active_claim_focus_drift(
            _ws(base),
            session_id,
            objective_text=objective_text,
            user_goal=user_goal,
            candidate_limit=candidate_limit,
        ),
    )


def aitp_v5_propose_active_claim_rebind(
    base: str,
    *,
    session_id: str,
    candidate_claim_id: str = "",
    reason: str = "",
    objective_text: str = "",
    user_goal: str = "",
) -> dict:
    """Return a read-only active-claim rebind proposal requiring confirmation."""

    return require_valid_public_surface(
        "active_claim_rebind_proposal",
        propose_active_claim_rebind(
            _ws(base),
            session_id,
            candidate_claim_id=candidate_claim_id,
            reason=reason,
            objective_text=objective_text,
            user_goal=user_goal,
        ),
    )


def aitp_v5_confirm_active_claim_rebind(
    base: str,
    *,
    session_id: str,
    new_claim_id: str,
    reason: str,
    user_confirmation: str,
    operator: str = "human",
) -> dict:
    """Explicitly rebind the session active claim and write an audit record."""

    return require_valid_public_surface(
        "active_claim_rebind_confirmation",
        confirm_active_claim_rebind(
            _ws(base),
            session_id,
            new_claim_id=new_claim_id,
            reason=reason,
            user_confirmation=user_confirmation,
            operator=operator,
        ),
    )


def aitp_v5_get_research_distillation_candidates(base: str, *, session_id: str, limit: int = 8) -> dict:
    """Return read-only reusable-block candidates and missing gates for a session."""

    return require_valid_public_surface(
        "research_distillation_candidates",
        build_research_distillation_candidates(_ws(base), session_id, limit=limit),
    )


def aitp_v5_compile_note_outline(
    base: str,
    *,
    session_id: str,
    style: str = "jhep",
    candidate_limit: int = 8,
) -> dict:
    """Return a read-only research-note outline coverage surface."""

    return require_valid_public_surface(
        "note_outline",
        compile_note_outline(_ws(base), session_id, style=style, candidate_limit=candidate_limit),
    )


def aitp_v5_build_workspace_file_migration_ledger(
    base: str,
    *,
    workspace_root: str = "",
    migration_plan_json: str = "",
    old_store_manifest_json: str = "",
    legacy_accounting_dir: str = "",
    compact: bool = False,
) -> dict:
    """Return the file-level import/archive/review ledger for old AITP stores."""

    payload = build_workspace_file_migration_ledger(
        _ws(base),
        workspace_root=workspace_root or None,
        migration_plan_path=migration_plan_json or None,
        old_store_manifest_path=old_store_manifest_json or None,
        legacy_accounting_dir=legacy_accounting_dir or None,
    )
    if compact:
        return require_valid_public_surface(
            "workspace_file_migration_ledger_progress",
            compact_workspace_file_migration_ledger(payload),
        )
    return require_valid_public_surface("workspace_file_migration_ledger", payload)


def aitp_v5_write_workspace_file_migration_ledger(
    base: str,
    *,
    workspace_root: str = "",
    migration_plan_json: str = "",
    old_store_manifest_json: str = "",
    legacy_accounting_dir: str = "",
    write_json: str = "",
    write_report: str = "",
    compact: bool = True,
) -> dict:
    """Write JSON/Markdown file-level migration ledger views for old AITP stores."""

    payload = build_workspace_file_migration_ledger(
        _ws(base),
        workspace_root=workspace_root or None,
        migration_plan_path=migration_plan_json or None,
        old_store_manifest_path=old_store_manifest_json or None,
        legacy_accounting_dir=legacy_accounting_dir or None,
    )
    payload = write_workspace_file_migration_ledger(
        payload,
        json_path=write_json or None,
        report_path=write_report or None,
    )
    if compact:
        progress = compact_workspace_file_migration_ledger(payload)
        return {"ok": True, **require_valid_public_surface("workspace_file_migration_ledger_progress", progress)}
    return {"ok": True, **require_valid_public_surface("workspace_file_migration_ledger", payload)}


def aitp_v5_get_workspace_migration_health(
    base: str,
    *,
    sample_limit: int = 5,
) -> dict:
    """Return compact migration/recovery boundary status for the canonical store."""

    return require_valid_public_surface(
        "workspace_migration_health",
        build_workspace_migration_health(_ws(base), sample_limit=sample_limit),
    )


def aitp_v5_build_workspace_old_store_import_plan(
    base: str,
    *,
    workspace_root: str = "",
    old_store_manifest_json: str = "",
    topics: list[str] | None = None,
) -> dict:
    """Return a conflict-checked plan for importing old-store typed files."""

    payload = build_workspace_old_store_import_plan(
        _ws(base),
        workspace_root=workspace_root or None,
        old_store_manifest_path=old_store_manifest_json or None,
        topics=topics or [],
    )
    return require_valid_public_surface("workspace_old_store_import_result", payload)


def aitp_v5_apply_workspace_old_store_import(
    base: str,
    *,
    workspace_root: str = "",
    old_store_manifest_json: str = "",
    topics: list[str] | None = None,
    write_json: str = "",
    write_report: str = "",
) -> dict:
    """Apply a conflict-checked import of old-store typed files into canonical AITP."""

    payload = build_workspace_old_store_import_plan(
        _ws(base),
        workspace_root=workspace_root or None,
        old_store_manifest_path=old_store_manifest_json or None,
        topics=topics or [],
    )
    payload = apply_workspace_old_store_import_plan(payload)
    if write_json or write_report:
        payload = write_workspace_old_store_import_result(
            payload,
            json_path=write_json or None,
            report_path=write_report or None,
        )
    return {"ok": True, **require_valid_public_surface("workspace_old_store_import_result", payload)}


def aitp_v5_build_workspace_recovery_binding_repair(
    base: str,
    *,
    topics: list[str] | None = None,
    session_id: str = "",
    objective_text: str = "",
    user_goal: str = "",
) -> dict:
    """Return a conservative active-claim binding repair plan for recovery gaps."""

    payload = build_workspace_recovery_binding_repair(
        _ws(base),
        topics=topics or [],
        session_id=session_id,
        objective_text=objective_text,
        user_goal=user_goal,
    )
    return require_valid_public_surface("workspace_recovery_binding_repair", payload)


def aitp_v5_apply_workspace_recovery_binding_repair(
    base: str,
    *,
    topics: list[str] | None = None,
    session_id: str = "",
    objective_text: str = "",
    user_goal: str = "",
    write_json: str = "",
    write_report: str = "",
) -> dict:
    """Apply safe single-claim active-session binding repairs for recovery gaps."""

    ws = _ws(base)
    payload = build_workspace_recovery_binding_repair(
        ws,
        topics=topics or [],
        session_id=session_id,
        objective_text=objective_text,
        user_goal=user_goal,
    )
    payload = apply_workspace_recovery_binding_repair(payload, ws)
    if write_json or write_report:
        payload = write_workspace_recovery_binding_repair(
            payload,
            json_path=write_json or None,
            report_path=write_report or None,
        )
    return {"ok": True, **require_valid_public_surface("workspace_recovery_binding_repair", payload)}


def aitp_v5_build_workspace_recovery_audit(
    base: str,
    *,
    migration_plan_json: str = "",
    topics: list[str] | None = None,
    compact: bool = False,
) -> dict:
    """Return a read-only per-topic restart recovery audit."""

    payload = build_workspace_recovery_audit(
        _ws(base),
        migration_plan_path=migration_plan_json or None,
        topics=topics or [],
    )
    if compact:
        return require_valid_public_surface(
            "workspace_recovery_audit_progress",
            compact_workspace_recovery_audit(payload),
        )
    return require_valid_public_surface("workspace_recovery_audit", payload)


def aitp_v5_write_workspace_recovery_audit(
    base: str,
    *,
    migration_plan_json: str = "",
    topics: list[str] | None = None,
    write_json: str = "",
    write_report: str = "",
    compact: bool = True,
) -> dict:
    """Write JSON/Markdown per-topic restart recovery audit views."""

    payload = build_workspace_recovery_audit(
        _ws(base),
        migration_plan_path=migration_plan_json or None,
        topics=topics or [],
    )
    payload = write_workspace_recovery_audit(
        payload,
        json_path=write_json or None,
        report_path=write_report or None,
    )
    if compact:
        progress = compact_workspace_recovery_audit(payload)
        return {"ok": True, **require_valid_public_surface("workspace_recovery_audit_progress", progress)}
    return {"ok": True, **require_valid_public_surface("workspace_recovery_audit", payload)}


def aitp_v5_build_workspace_recording_audit(
    base: str,
    *,
    migration_plan_json: str = "",
    topics: list[str] | None = None,
    limit: int = 40,
) -> dict:
    """Return a read-only workspace-level audit of progressive recording navigation."""

    payload = build_workspace_recording_audit(
        _ws(base),
        migration_plan_path=migration_plan_json or None,
        topics=topics or [],
        limit=limit,
    )
    return require_valid_public_surface("workspace_recording_audit", payload)


def aitp_v5_write_workspace_recording_audit(
    base: str,
    *,
    migration_plan_json: str = "",
    topics: list[str] | None = None,
    write_json: str = "",
    write_report: str = "",
    limit: int = 40,
) -> dict:
    """Write JSON/Markdown workspace-level progressive recording navigation audit views."""

    payload = build_workspace_recording_audit(
        _ws(base),
        migration_plan_path=migration_plan_json or None,
        topics=topics or [],
        limit=limit,
    )
    payload = write_workspace_recording_audit(
        payload,
        json_path=write_json or None,
        report_path=write_report or None,
    )
    return {"ok": True, **require_valid_public_surface("workspace_recording_audit", payload)}


def _unbound_session_execution_brief(session_id: str) -> dict:
    """Return a valid brief for malformed or not-yet-bound session records."""

    return {
        "ok": False,
        "status": "needs_bind_session",
        "session": {
            "session_id": session_id or "unbound-session",
            "topic_id": "unbound-session",
            "context_id": "unbound-session",
            "runtime": "unknown",
            "interaction_profile": "collaborator",
            "interaction_steering": "call aitp_v5_bind_session before requesting an execution brief",
            "active_cycle": "",
            "active_claim": "",
            "active_route": "",
            "write_scope": "",
            "created_at": "",
        },
        "current_focus": {
            "active_claim": "",
            "active_route": "",
            "active_cycle": "",
            "claim_statement": "",
            "confidence_state": "",
            "evidence_profile": "",
            "main_uncertainty": "session binding is missing or malformed",
        },
        "flow_profile": {
            "profile": "guided",
            "reason": "execution brief cannot resolve a bound session yet",
            "escalation_triggers": [],
        },
        "risk_assessment": {
            "level": "guided",
            "score": 0,
            "signals": [],
            "required_checks": [],
            "human_checkpoint_needed": False,
            "rationale": "no active claim is available until the session is bound",
            "summary": "session binding is missing or malformed",
            "action_budget": {
                "level": "guided",
                "max_tool_calls_before_reflection": 4,
                "max_questions": 2,
                "required_outputs": [],
                "allowed_actions": ["bind_session"],
                "requires_human_checkpoint": False,
            },
        },
        "action_budget": {
            "level": "guided",
            "max_tool_calls_before_reflection": 4,
            "max_questions": 2,
            "required_outputs": [],
            "allowed_actions": ["bind_session"],
            "requires_human_checkpoint": False,
        },
        "evidence_coverage": {
            "required_outputs": [],
            "satisfied_outputs": [],
            "missing_outputs": [],
            "coverage_by_record": [],
        },
        "interaction_profile": {
            "name": "collaborator",
            "max_questions": 2,
            "effective_max_questions": 2,
            "steering": "bind session before continuing",
        },
        "known_context": {
            "topic_id": "unbound-session",
            "context_id": "unbound-session",
            "previous_failed_attempts": [],
            "recommended_tool_executors": [],
            "knowledge_connectors": [],
            "reference_locations": [],
            "operating_notes": [],
            "research_intent_gate": {"present": False},
            "innovation_direction": {"present": False},
            "final_output_profile": {"present": False},
            "operator_checkpoint": {"active": False},
            "strategy_memory": {"present": False},
            "run_iterations": [],
            "lane_exemplars": [],
            "object_relations": [],
            "memory_entries": [],
            "proof_obligations": [],
        },
        "research_gates": {
            "record_level_human_gate_required": False,
            "record_level_human_gate_count": 0,
            "open_proof_obligation_count": 0,
            "open_proof_obligation_ids": [],
            "human_checkpoint_needed": False,
            "semantics": {
                "human_gate_required": "not evaluated until the session is bound",
                "human_checkpoint_needed": "not required for the bind-session repair",
            },
        },
        "claim_relation_map": empty_claim_relation_map(
            topic_id="unbound-session",
            session_id=session_id,
            reason="session binding is missing or malformed",
        ),
        "mandatory_reflection": [],
        "next_action_candidates": [
            {
                "action": "bind_session",
                "rank": 1,
                "why": "the requested execution brief has no valid SessionBinding",
                "expected_evidence_gain": "establish topic/context/claim focus before further AITP reads",
            }
        ],
        "forbidden_now": ["continue_without_binding_session"],
        "human_checkpoint": {
            "needed": False,
            "reason": None,
            "semantics": "No human checkpoint is needed for the bind-session repair.",
        },
    }


def aitp_v5_get_process_graph_slice(base: str, *, session_id: str, claim_id: str = "", limit: int = 80) -> dict:
    return require_valid_public_surface(
        "process_graph_slice",
        build_process_graph_slice(_ws(base), session_id, claim_id=claim_id, limit=limit),
    )


def aitp_v5_get_host_agnostic_moment_policy(
    base: str,
    *,
    session_id: str,
    claim_id: str = "",
    limit: int = 80,
) -> dict:
    """Return the read-only host-agnostic moment policy for a process graph slice."""

    graph = build_process_graph_slice(_ws(base), session_id, claim_id=claim_id, limit=limit)
    return require_valid_public_surface("host_agnostic_moment_policy", graph["moment_policy"])


def aitp_v5_classify_recording_candidate(
    base: str,
    *,
    session_id: str = "",
    event_type: str,
    summary: str = "",
    topic_id: str = "",
    claim_id: str = "",
    touched_refs: list[str] | None = None,
    produced_artifacts: list[str] | None = None,
    tool_call_id: str = "",
    risk_hint: str = "",
    payload: dict | None = None,
) -> dict:
    """Classify a durable research event before progressive AITP recording navigation."""

    return require_valid_public_surface(
        "recording_candidate_classification",
        classify_recording_candidate(
            _ws(base),
            session_id=session_id,
            event_type=event_type,
            summary=summary,
            topic_id=topic_id,
            claim_id=claim_id,
            touched_refs=touched_refs or [],
            produced_artifacts=produced_artifacts or [],
            tool_call_id=tool_call_id,
            risk_hint=risk_hint,
            payload=payload or {},
        ),
    )


def aitp_v5_get_recording_navigation_state(
    base: str,
    *,
    session_id: str,
    claim_id: str = "",
    limit: int = 40,
) -> dict:
    """Return the read-only first-level AITP recording navigator for a session."""

    return require_valid_public_surface(
        "recording_navigation_state",
        build_recording_navigation_state(_ws(base), session_id, claim_id=claim_id, limit=limit),
    )


def aitp_v5_expand_recording_slot(
    base: str,
    *,
    session_id: str,
    slot: str,
    claim_id: str = "",
    candidate: dict | None = None,
) -> dict:
    """Expand one AITP recording slot into required fields and typed write guidance."""

    return require_valid_public_surface(
        "recording_slot_expansion",
        expand_recording_slot(_ws(base), session_id, slot, claim_id=claim_id, candidate=candidate or {}),
    )


def aitp_v5_verify_recording_effect(
    base: str,
    *,
    session_id: str,
    expected_refs: list[str] | None = None,
    before_node_ids: list[str] | None = None,
    before_edge_ids: list[str] | None = None,
    claim_id: str = "",
    limit: int = 80,
) -> dict:
    """Verify typed refs or graph deltas after an AITP recording write."""

    return require_valid_public_surface(
        "recording_effect_verification",
        verify_recording_effect(
            _ws(base),
            session_id,
            expected_refs=expected_refs or [],
            before_node_ids=before_node_ids or [],
            before_edge_ids=before_edge_ids or [],
            claim_id=claim_id,
            limit=limit,
        ),
    )


def aitp_v5_plan_lightweight_record_write(
    base: str,
    *,
    topic_id: str,
    current_session_id: str,
    event_summary: str,
    active_claim_id: str = "",
    target_claim_hint: str = "",
    touched_files_or_artifacts: list[str] | None = None,
    touched_tool_runs_or_evidence_refs: list[str] | None = None,
    risk_hint: str = "",
) -> dict:
    """Plan-only surface: propose a minimal typed-record write set for a short research event.

    This tool NEVER writes records and NEVER applies trust updates. It returns a plan that
    an agent or human reviews before invoking the concrete record-write MCP tools.
    """

    from brain.v5.lightweight_record_router import plan_lightweight_record_write

    return require_valid_public_surface(
        "lightweight_record_write_plan",
        plan_lightweight_record_write(
            _ws(base),
            topic_id=topic_id,
            current_session_id=current_session_id,
            event_summary=event_summary,
            active_claim_id=active_claim_id,
            target_claim_hint=target_claim_hint,
            touched_files_or_artifacts=touched_files_or_artifacts or [],
            touched_tool_runs_or_evidence_refs=touched_tool_runs_or_evidence_refs or [],
            risk_hint=risk_hint,
        ),
    )


def aitp_v5_lookup_record_refs(base: str, *, refs: list[str]) -> dict:
    return {
        "ok": True,
        "record_ref_lookup": require_valid_public_surface(
            "record_ref_lookup",
            lookup_record_refs(_ws(base), refs),
        ),
    }


def aitp_v5_record_exploratory_record(
    base: str,
    *,
    topic_id: str,
    exploration_type: str,
    title: str,
    focal_question: str,
    summary: str,
    claim_id: str = "",
    session_id: str = "",
    original_question: str = "",
    local_question: str = "",
    status: str = "open",
    object_ids: list[str] | None = None,
    relation_ids: list[str] | None = None,
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    parent_record_ids: list[str] | None = None,
    derived_record_ids: list[str] | None = None,
    reasoning_moves: list[str] | None = None,
    backtrace_targets: list[str] | None = None,
    candidate_paths: list[str] | None = None,
    relation_path_questions: list[str] | None = None,
    definition_boundary_questions: list[str] | None = None,
    derivation_backtrace_questions: list[str] | None = None,
    source_dependency_questions: list[str] | None = None,
    original_question_guard: list[str] | None = None,
    unresolved_points: list[str] | None = None,
    next_actions: list[str] | None = None,
    human_steering: str = "",
    metadata: dict | None = None,
) -> dict:
    record = record_exploratory_record(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        session_id=session_id,
        exploration_type=exploration_type,
        title=title,
        focal_question=focal_question,
        summary=summary,
        original_question=original_question,
        local_question=local_question,
        status=status,
        object_ids=object_ids,
        relation_ids=relation_ids,
        source_refs=source_refs,
        artifact_ids=artifact_ids,
        parent_record_ids=parent_record_ids,
        derived_record_ids=derived_record_ids,
        reasoning_moves=reasoning_moves,
        backtrace_targets=backtrace_targets,
        candidate_paths=candidate_paths,
        relation_path_questions=relation_path_questions,
        definition_boundary_questions=definition_boundary_questions,
        derivation_backtrace_questions=derivation_backtrace_questions,
        source_dependency_questions=source_dependency_questions,
        original_question_guard=original_question_guard,
        unresolved_points=unresolved_points,
        next_actions=next_actions,
        human_steering=human_steering,
        metadata=metadata,
    )
    return require_valid_public_surface("exploratory_record", exploratory_record_payload(record))


def aitp_v5_register_source_asset(
    base: str,
    *,
    topic_id: str,
    asset_type: str,
    uri: str,
    title: str,
    claim_id: str = "",
    label: str = "",
    content_hash: str = "",
    hash_algorithm: str = "",
    version_anchor: dict | None = None,
    acquired_at: str = "",
    source_kind: str = "manual",
    summary: str = "",
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    reference_location_ids: list[str] | None = None,
    derived_from: list[str] | None = None,
    metadata: dict | None = None,
    linked_records: dict | None = None,
) -> dict:
    record = register_source_asset(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        asset_type=asset_type,
        uri=uri,
        title=title,
        label=label,
        content_hash=content_hash,
        hash_algorithm=hash_algorithm,
        version_anchor=version_anchor,
        acquired_at=acquired_at,
        source_kind=source_kind,
        summary=summary,
        source_refs=source_refs,
        artifact_ids=artifact_ids,
        code_state_ids=code_state_ids,
        reference_location_ids=reference_location_ids,
        derived_from=derived_from,
        metadata=metadata,
        linked_records=linked_records,
    )
    return require_valid_public_surface("source_asset_record", source_asset_payload(record))


def aitp_v5_capture_source_asset_auto(
    base: str,
    *,
    path: str,
    topic_id: str,
    claim_id: str = "",
    asset_type: str = "",
    title: str = "",
    label: str = "",
    version_anchor: dict | None = None,
    acquired_at: str = "",
    source_kind: str = "local_file_auto",
    summary: str = "",
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    reference_location_ids: list[str] | None = None,
    derived_from: list[str] | None = None,
    metadata: dict | None = None,
    linked_records: dict | None = None,
    copy_to_store: bool = False,
    force_refresh: bool = False,
) -> dict:
    """Inspect a local file and register it as an AITP source asset."""

    record = capture_source_asset_from_local_path(
        _ws(base),
        path=path,
        topic_id=topic_id,
        claim_id=claim_id,
        asset_type=asset_type,
        title=title,
        label=label,
        version_anchor=version_anchor,
        acquired_at=acquired_at,
        source_kind=source_kind,
        summary=summary,
        source_refs=source_refs,
        artifact_ids=artifact_ids,
        code_state_ids=code_state_ids,
        reference_location_ids=reference_location_ids,
        derived_from=derived_from,
        metadata=metadata,
        linked_records=linked_records,
        copy_to_store=copy_to_store,
        force_refresh=force_refresh,
    )
    return require_valid_public_surface("source_asset_record", source_asset_payload(record))


def aitp_v5_acquire_pdf_source_asset(
    base: str,
    *,
    topic_id: str,
    url: str,
    title: str,
    claim_id: str = "",
    asset_type: str = "paper",
    label: str = "",
    timeout_seconds: int = 120,
    max_bytes: int = 200 * 1024 * 1024,
    force_refresh: bool = False,
    version_anchor: dict | None = None,
    acquired_at: str = "",
    source_kind: str = "literature_pdf",
    summary: str = "",
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    reference_location_ids: list[str] | None = None,
    derived_from: list[str] | None = None,
    metadata: dict | None = None,
    linked_records: dict | None = None,
) -> dict:
    """Acquire a PDF into the topic-scoped v5 source blob store."""

    record = acquire_pdf_source_asset(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        asset_type=asset_type,
        url=url,
        title=title,
        label=label,
        timeout_seconds=timeout_seconds,
        max_bytes=max_bytes,
        force_refresh=force_refresh,
        version_anchor=version_anchor,
        acquired_at=acquired_at,
        source_kind=source_kind,
        summary=summary,
        source_refs=source_refs,
        artifact_ids=artifact_ids,
        code_state_ids=code_state_ids,
        reference_location_ids=reference_location_ids,
        derived_from=derived_from,
        metadata=metadata,
        linked_records=linked_records,
    )
    return require_valid_public_surface("source_asset_record", source_asset_payload(record))


def aitp_v5_acquire_arxiv_source_asset(
    base: str,
    *,
    topic_id: str,
    arxiv_id: str,
    title: str = "",
    claim_id: str = "",
    version: str = "",
    label: str = "",
    timeout_seconds: int = 120,
    max_bytes: int = 200 * 1024 * 1024,
    force_refresh: bool = False,
    version_anchor: dict | None = None,
    source_kind: str = "arxiv_pdf",
    summary: str = "",
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    reference_location_ids: list[str] | None = None,
    derived_from: list[str] | None = None,
    metadata: dict | None = None,
    linked_records: dict | None = None,
) -> dict:
    """Acquire an arXiv PDF into the topic-scoped v5 source blob store."""

    record = acquire_arxiv_source_asset(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        arxiv_id=arxiv_id,
        title=title,
        version=version,
        label=label,
        timeout_seconds=timeout_seconds,
        max_bytes=max_bytes,
        force_refresh=force_refresh,
        version_anchor=version_anchor,
        source_kind=source_kind,
        summary=summary,
        source_refs=source_refs,
        artifact_ids=artifact_ids,
        code_state_ids=code_state_ids,
        reference_location_ids=reference_location_ids,
        derived_from=derived_from,
        metadata=metadata,
        linked_records=linked_records,
    )
    return require_valid_public_surface("source_asset_record", source_asset_payload(record))


def aitp_v5_record_research_route(
    base: str,
    *,
    topic_id: str,
    title: str,
    route_type: str,
    status: str,
    rationale: str,
    claim_id: str = "",
    session_id: str = "",
    current_question: str = "",
    next_action: str = "",
    failure_modes: list[str] | None = None,
    source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    parent_route_ids: list[str] | None = None,
    checkpoint_ids: list[str] | None = None,
    exploratory_record_ids: list[str] | None = None,
    object_ids: list[str] | None = None,
    relation_ids: list[str] | None = None,
    decision_rationale: str = "",
    pivot_reason: str = "",
    metadata: dict | None = None,
) -> dict:
    record = record_research_route(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        session_id=session_id,
        title=title,
        route_type=route_type,
        status=status,
        rationale=rationale,
        current_question=current_question,
        next_action=next_action,
        failure_modes=failure_modes,
        source_refs=source_refs,
        evidence_refs=evidence_refs,
        artifact_ids=artifact_ids,
        parent_route_ids=parent_route_ids,
        checkpoint_ids=checkpoint_ids,
        exploratory_record_ids=exploratory_record_ids,
        object_ids=object_ids,
        relation_ids=relation_ids,
        decision_rationale=decision_rationale,
        pivot_reason=pivot_reason,
        metadata=metadata,
    )
    return require_valid_public_surface("research_route_record", research_route_payload(record))


_LEGACY_MCP_MODULE = ".".join(("brain", "mcp_" + "server"))


def _legacy_mcp_tool(tool_name: str):
    return getattr(import_module(_LEGACY_MCP_MODULE), tool_name)


def _legacy_list_topics_alias(topics_root: str) -> list[dict]:
    """Legacy discovery alias only; migrate/bind a v5 session before real work."""
    return _legacy_mcp_tool("aitp_" + "list_topics")(topics_root)


def _legacy_execution_brief_alias(topics_root: str, topic_slug: str) -> dict:
    """Legacy stage brief alias only; prefer aitp_v5_get_execution_brief."""
    return _legacy_mcp_tool("aitp_" + "get_execution_brief")(topics_root, topic_slug)


def _legacy_bootstrap_topic_alias(
    topics_root: str,
    topic_slug: str,
    title: str,
    question: str,
    lane: str = "unspecified",
    research_intensity: str = "standard",
    interaction_level: str = "collaborative",
) -> dict:
    """Legacy topic bootstrap alias; prefer v5 topic/claim/session records."""
    result = _legacy_mcp_tool("aitp_" + "bootstrap_topic")(
        topics_root,
        topic_slug,
        title,
        question,
        lane=lane,
        research_intensity=research_intensity,
        interaction_level=interaction_level,
    )
    if isinstance(result, dict):
        return result
    return {"ok": True, "message": str(result), "topic_slug": topic_slug}


aitp_list_topics = _legacy_list_topics_alias
aitp_list_topics.__name__ = "aitp_" + "list_topics"
globals()["aitp_" + "get_execution_brief"] = _legacy_execution_brief_alias
_legacy_execution_brief_alias.__name__ = "aitp_" + "get_execution_brief"
globals()["aitp_" + "bootstrap_topic"] = _legacy_bootstrap_topic_alias
_legacy_bootstrap_topic_alias.__name__ = "aitp_" + "bootstrap_topic"


def aitp_v5_assess_risk(base: str, *, claim_id: str) -> dict:
    ws = _ws(base); claim = get_claim(ws, claim_id)
    return {"ok": True, "claim_id": claim_id, "risk_assessment": asdict(assess_claim_risk(claim, code_states=_linked_code_states(ws, claim_id)))}


def aitp_v5_record_code_state(
    base: str, *, repo_id: str, upstream_remote: str, upstream_branch: str,
    upstream_commit: str, local_branch: str, worktree_path: str, dirty: bool,
    patch_id: str = "", diff_hash: str = "", build_config: dict | None = None,
    runtime_environment: dict | None = None, linked_records: dict | None = None,
    known_divergence: str = "",
) -> dict:
    state = record_code_state(_ws(base), repo_id=repo_id, upstream_remote=upstream_remote,
        upstream_branch=upstream_branch, upstream_commit=upstream_commit,
        local_branch=local_branch, worktree_path=worktree_path, dirty=dirty,
        patch_id=patch_id, diff_hash=diff_hash, build_config=build_config,
        runtime_environment=runtime_environment, linked_records=linked_records,
        known_divergence=known_divergence)
    return require_valid_public_surface("code_state_record", {"ok": True, **asdict(state)})


def aitp_v5_capture_code_state_auto(
    base: str,
    *,
    worktree_path: str,
    repo_id: str = "",
    topic_id: str = "",
    claim_id: str = "",
    session_id: str = "",
    build_config: dict | None = None,
    runtime_environment: dict | None = None,
    linked_records: dict | None = None,
    known_divergence: str = "",
    write_patch_artifact: bool = False,
) -> dict:
    state = capture_code_state_from_git(
        _ws(base),
        worktree_path=worktree_path,
        repo_id=repo_id,
        topic_id=topic_id,
        claim_id=claim_id,
        session_id=session_id,
        build_config=build_config,
        runtime_environment=runtime_environment,
        linked_records=linked_records,
        known_divergence=known_divergence,
        write_patch_artifact=write_patch_artifact,
    )
    return require_valid_public_surface("code_state_record", {"ok": True, **asdict(state)})


def aitp_v5_register_tool_recipe(
    base: str, *, recipe_id: str, tool_family: str, tool_name: str, purpose: str,
    required_inputs: list[str] | None = None, expected_outputs: list[str] | None = None,
    invariants: list[str] | None = None,
) -> dict:
    recipe = register_tool_recipe(_ws(base), recipe_id=recipe_id, tool_family=tool_family,
        tool_name=tool_name, purpose=purpose, required_inputs=required_inputs,
        expected_outputs=expected_outputs, invariants=invariants)
    return require_valid_public_surface("tool_recipe_record", {"ok": True, **asdict(recipe)})


def aitp_v5_record_tool_run(
    base: str, *, recipe_id: str, tool_family: str, tool_name: str, topic_id: str,
    claim_id: str, inputs: dict | None = None, outputs: dict | None = None,
    environment: dict | None = None, evidence_status: str = "unreviewed",
    code_state_ids: list[str] | None = None, artifact_ids: list[str] | None = None,
    source_refs: list[str] | None = None,
) -> dict:
    run = record_tool_run(_ws(base), recipe_id=recipe_id, tool_family=tool_family,
        tool_name=tool_name, topic_id=topic_id, claim_id=claim_id, inputs=inputs,
        outputs=outputs, environment=environment, evidence_status=evidence_status,
        code_state_ids=code_state_ids, artifact_ids=artifact_ids, source_refs=source_refs)
    return require_valid_public_surface("tool_run_record", {"ok": True, **asdict(run)})


def aitp_v5_capture_tool_run_auto(
    base: str,
    *,
    path: str,
    recipe_id: str,
    tool_family: str,
    tool_name: str,
    topic_id: str,
    claim_id: str,
    inputs: dict | None = None,
    outputs: dict | None = None,
    environment: dict | None = None,
    evidence_status: str = "unreviewed",
    code_state_ids: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    source_refs: list[str] | None = None,
    summary: str = "",
    max_preview_chars: int = 1200,
) -> dict:
    """Inspect a local transcript/result file and record tool-run provenance."""

    run = capture_tool_run_from_local_path(
        _ws(base),
        path=path,
        recipe_id=recipe_id,
        tool_family=tool_family,
        tool_name=tool_name,
        topic_id=topic_id,
        claim_id=claim_id,
        inputs=inputs,
        outputs=outputs,
        environment=environment,
        evidence_status=evidence_status,
        code_state_ids=code_state_ids,
        artifact_ids=artifact_ids,
        source_refs=source_refs,
        summary=summary,
        max_preview_chars=max_preview_chars,
    )
    return require_valid_public_surface("tool_run_record", tool_run_payload(run))


def aitp_v5_execute_tool(
    base: str, *, executor_id: str, recipe_id: str, topic_id: str, claim_id: str,
    inputs: dict, evidence_status: str = "", code_state_ids: list[str] | None = None,
    artifact_ids: list[str] | None = None, source_refs: list[str] | None = None,
    supports_outputs: list[str] | None = None, evidence_type: str = "tool_run",
    evidence_summary: str = "",
) -> dict:
    result = execute_registered_tool_result(_ws(base), executor_id=executor_id,
        recipe_id=recipe_id, topic_id=topic_id, claim_id=claim_id, inputs=inputs,
        evidence_status=evidence_status, code_state_ids=code_state_ids,
        artifact_ids=artifact_ids, source_refs=source_refs, supports_outputs=supports_outputs,
        evidence_type=evidence_type, evidence_summary=evidence_summary)
    payload = {"ok": True, **asdict(result.run)}
    if result.evidence is not None:
        payload["evidence_id"] = result.evidence.evidence_id
        payload["evidence"] = require_valid_public_surface("evidence_record", {"ok": True, **asdict(result.evidence)})
    return require_valid_public_surface("tool_run_record", payload)


def aitp_v5_list_tool_executors() -> dict:
    return require_valid_public_surface("tool_executor_catalog", describe_tool_executors())


def aitp_v5_list_knowledge_connectors() -> dict:
    return require_valid_public_surface("knowledge_connector_catalog", describe_knowledge_connectors())

def aitp_v5_persist_hook_trace_event(base: str, *, hook_payload: dict) -> dict:
    return require_valid_public_surface("hook_trace_event_record", persist_hook_trace_event(_ws(base), hook_payload))


def aitp_v5_record_reference_location(
    base: str, *, topic_id: str, connector_id: str, location_type: str, uri: str,
    label: str, claim_id: str = "", source_ref: str = "", external_id: str = "",
    status: str = "located", summary: str = "", metadata: dict | None = None,
    linked_records: dict | None = None,
) -> dict:
    loc = record_reference_location(_ws(base), topic_id=topic_id, claim_id=claim_id,
        connector_id=connector_id, location_type=location_type, uri=uri, label=label,
        source_ref=source_ref, external_id=external_id, status=status, summary=summary,
        metadata=metadata, linked_records=linked_records)
    return require_valid_public_surface("reference_location_record", {"ok": True, **asdict(loc)})


def aitp_v5_get_adapter_packet(base: str, *, runtime: str, session_id: str) -> dict:
    return {"ok": True, **require_valid_public_surface("adapter_packet", build_adapter_packet(_ws(base), session_id, runtime=runtime))}


def aitp_v5_write_codex_hook_bridge(base: str, *, session_id: str, output_path: str) -> dict:
    ws = _ws(base)
    packet = require_valid_public_surface("adapter_packet", build_adapter_packet(ws, session_id, runtime="codex"))
    bridge = {
        "ok": True,
        **write_codex_hook_bridge(
            output_path,
            packet["runtime_hook_installation"],
            packet["runtime_gate_protocols"],
            session_id=session_id,
        ),
    }
    return require_valid_public_surface("codex_hook_bridge", bridge)


def aitp_v5_write_opencode_plugin_bridge(base: str, *, session_id: str, output_path: str) -> dict:
    ws = _ws(base)
    packet = require_valid_public_surface("adapter_packet", build_adapter_packet(ws, session_id, runtime="opencode"))
    bridge = {
        "ok": True,
        **write_opencode_plugin_bridge(
            output_path,
            packet["runtime_hook_installation"],
            packet["runtime_gate_protocols"],
            session_id=session_id,
        ),
    }
    return require_valid_public_surface("opencode_plugin_bridge", bridge)


def aitp_v5_write_claude_code_hook_settings(base: str, *, session_id: str, output_path: str) -> dict:
    ws = _ws(base)
    packet = require_valid_public_surface("adapter_packet", build_adapter_packet(ws, session_id, runtime="claude_code"))
    settings = {"ok": True, **write_claude_code_hook_settings(
        output_path, packet["runtime_hook_installation"], workspace_base=str(ws.base), session_id=session_id)}
    return require_valid_public_surface("claude_code_hook_settings", settings)


def aitp_v5_evaluate_adapter_pre_tool_event(
    base: str, *, bridge_payload: dict, platform_event: dict,
) -> dict:
    return require_valid_public_surface(
        "pre_tool_policy_decision",
        evaluate_platform_pre_tool_event(_ws(base), bridge_payload, platform_event),
    )


def aitp_v5_install_claude_code_hook_settings(base: str, *, session_id: str, settings_path: str) -> dict:
    ws = _ws(base)
    packet = require_valid_public_surface("adapter_packet", build_adapter_packet(ws, session_id, runtime="claude_code"))
    installed = {"ok": True, **install_claude_code_hook_settings(
        settings_path, packet["runtime_hook_installation"], workspace_base=str(ws.base), session_id=session_id)}
    return require_valid_public_surface("claude_code_hook_installation", installed)


def aitp_v5_get_adapter_protocol_registry() -> dict:
    return {"ok": True, "adapter_protocol_registry": require_valid_public_surface("adapter_protocol_registry", adapter_protocol_registry())}


def aitp_v5_get_runtime_bridge_target_manifest() -> dict:
    """Return MCP-first host bridge targets with CLI fallback templates."""

    return {
        "ok": True,
        "runtime_bridge_target_manifest": require_valid_public_surface(
            "runtime_bridge_target_manifest",
            runtime_bridge_target_manifest(),
        ),
    }


def aitp_v5_audit_runtime_mcp_bridge_acceptance(
    *,
    live_manifest: dict | None = None,
    live_tool_names: list | dict | None = None,
) -> dict:
    """Compare live host MCP bridge exposure with the canonical manifest."""

    return {
        "ok": True,
        "runtime_mcp_bridge_acceptance": require_valid_public_surface(
            "runtime_mcp_bridge_acceptance",
            audit_runtime_mcp_bridge_acceptance(
                live_manifest=live_manifest,
                live_tool_names=live_tool_names,
            ),
        ),
    }


def aitp_v5_get_runtime_payload_profiles() -> dict:
    """Return host-event to AITP typed-write payload profiles."""

    return {
        "ok": True,
        "runtime_payload_profiles": require_valid_public_surface(
            "runtime_payload_profiles",
            runtime_payload_profiles(),
        ),
    }


def aitp_v5_get_curated_rag_corpus(base: str = "") -> dict:
    """Return the curated heuristic RAG corpus catalog."""

    return {
        "ok": True,
        "curated_rag_corpus": require_valid_public_surface(
            "curated_rag_corpus",
            curated_rag_corpus(base or None),
        ),
    }


def aitp_v5_search_curated_rag_corpus(query: str, *, limit: int = 5, base: str = "") -> dict:
    """Return heuristic background chunks from the curated RAG corpus."""

    return {
        "ok": True,
        "curated_rag_search_result": require_valid_public_surface(
            "curated_rag_search_result",
            search_curated_rag_corpus(query, limit=limit, base=base or None),
        ),
    }


def aitp_v5_get_curated_rag_chunk(chunk_id: str, *, base: str = "") -> dict:
    """Return one read-only curated RAG chunk identity/anchor/hash payload."""

    return {
        "ok": True,
        "curated_rag_chunk": require_valid_public_surface(
            "curated_rag_chunk",
            read_curated_rag_chunk(chunk_id, base=base or None),
        ),
    }


def aitp_v5_draft_curated_rag_promotion(
    chunk_id: str,
    *,
    base: str = "",
    topic_id: str = "",
    claim_id: str = "",
    connector_id: str = "curated_rag",
    promotion_intent: str = "claim_support_review",
) -> dict:
    """Return a read-only promotion draft for a curated RAG chunk."""

    return {
        "ok": True,
        "curated_rag_promotion_draft": require_valid_public_surface(
            "curated_rag_promotion_draft",
            draft_curated_rag_promotion(
                chunk_id,
                base=base or None,
                topic_id=topic_id,
                claim_id=claim_id,
                connector_id=connector_id,
                promotion_intent=promotion_intent,
            ),
        ),
    }


def aitp_v5_ingest_curated_rag_corpus(
    base: str,
    *,
    paths: list[str],
    corpus_id: str = "",
    tags: list[str] | None = None,
    domain_hints: list[str] | None = None,
    topic_hints: list[str] | None = None,
    language: str = "en",
    priority: str = "medium",
    chunk_token_limit: int = 220,
    title_prefix: str = "",
    asset_type: str = "",
    rebuild_index: bool = True,
) -> dict:
    """Create or refresh a file-backed curated RAG manifest/index."""

    return require_valid_public_surface(
        "curated_rag_ingest_result",
        ingest_curated_rag_corpus(
            _ws(base),
            paths=paths,
            corpus_id=corpus_id,
            tags=tags,
            domain_hints=domain_hints,
            topic_hints=topic_hints,
            language=language,
            priority=priority,
            chunk_token_limit=chunk_token_limit,
            title_prefix=title_prefix,
            asset_type=asset_type,
            rebuild_index=rebuild_index,
        ),
    )


def aitp_v5_audit_record_gate_coverage() -> dict:
    return {
        "ok": True,
        "record_gate_coverage_audit": require_valid_public_surface(
            "record_gate_coverage_audit",
            record_gate_coverage_audit(),
        ),
    }


def aitp_v5_audit_hook_installation(
    base: str,
    *,
    runtime: str,
    settings_path: str = "",
    plugin_path: str = "",
    output_path: str = "",
) -> dict:
    return {
        "ok": True,
        **require_valid_public_surface(
            "runtime_hook_installation_audit",
            audit_hook_installation(
                _ws(base),
                runtime=runtime,
                settings_path=settings_path,
                plugin_path=plugin_path,
                output_path=output_path,
            ),
        ),
    }


def aitp_v5_discover_hook_install_paths(base: str) -> dict:
    return {
        "ok": True,
        **require_valid_public_surface("runtime_hook_installation_paths", discover_hook_install_paths(_ws(base))),
    }


def aitp_v5_report_hook_smoke_coverage() -> dict:
    return {
        "ok": True,
        **require_valid_public_surface(
            "runtime_hook_smoke_coverage",
            runtime_hook_smoke_coverage_report(),
        ),
    }


def aitp_v5_audit_final_engineering_readiness(base: str, *, migration_dir: str = "") -> dict:
    return {
        "ok": True,
        **require_valid_public_surface(
            "final_engineering_readiness_audit",
            audit_final_engineering_readiness(_ws(base), migration_dir=migration_dir or None),
        ),
    }


def aitp_v5_describe_public_surfaces() -> dict:
    return {"ok": True, "public_surfaces": describe_public_surfaces()}


def aitp_v5_evaluate_pre_tool_policy(
    base: str, *, session_id: str, action: str, claim_id: str = "",
    evidence_refs: list[str] | None = None, code_state_ids: list[str] | None = None,
    validation_contract_ids: list[str] | None = None,
    tool_run_ids: list[str] | None = None, validation_result_ids: list[str] | None = None,
    known_failure_modes: list[str] | None = None,
    recipe_id: str = "", executor_id: str = "",
    source_kind: str = "", source_ref: str = "", orientation_only: bool = False,
    risk_level: str = "guided", human_checkpoint_id: str = "",
    failure_mode_review_checkpoint_id: str = "", failure_mode_review_result_id: str = "",
) -> dict:
    return require_valid_public_surface("pre_tool_policy_decision", evaluate_context_pre_tool_policy(
        _ws(base), session_id=session_id, action=action, claim_id=claim_id,
        evidence_refs=evidence_refs, code_state_ids=code_state_ids,
        validation_contract_ids=validation_contract_ids,
        tool_run_ids=tool_run_ids, validation_result_ids=validation_result_ids,
        known_failure_modes=known_failure_modes,
        recipe_id=recipe_id, executor_id=executor_id,
        source_kind=source_kind, source_ref=source_ref, orientation_only=orientation_only,
        risk_level=risk_level, human_checkpoint_id=human_checkpoint_id,
        failure_mode_review_checkpoint_id=failure_mode_review_checkpoint_id, failure_mode_review_result_id=failure_mode_review_result_id))


def aitp_v5_record_physics_object(
    base: str, *, topic_id: str, object_type: str, name: str, definition: str,
    notation: str = "", assumptions: list[str] | None = None, source_refs: list[str] | None = None,
    metadata: dict | None = None, linked_records: dict | None = None, claim_id: str = "",
    status: str = "active",
) -> dict:
    links = dict(linked_records or {})
    if claim_id:
        links.setdefault("claim_id", claim_id)
    obj = record_physics_object(_ws(base), topic_id=topic_id, object_type=object_type,
        name=name, definition=definition, notation=notation, assumptions=assumptions,
        source_refs=source_refs, metadata=metadata, linked_records=links, status=status)
    return require_valid_public_surface("physics_object_record", {"ok": True, **asdict(obj)})


def aitp_v5_record_object_relation(
    base: str, *, topic_id: str, relation_type: str, subject_id: str, object_id: str,
    statement: str, claim_id: str = "", assumptions: list[str] | None = None,
    failure_modes: list[str] | None = None, source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None, metadata: dict | None = None, status: str = "hypothesis",
) -> dict:
    rel = record_object_relation(_ws(base), topic_id=topic_id, relation_type=relation_type,
        subject_id=subject_id, object_id=object_id, statement=statement, claim_id=claim_id,
        assumptions=assumptions, failure_modes=failure_modes, source_refs=source_refs,
        evidence_refs=evidence_refs, metadata=metadata, status=status)
    return require_valid_public_surface("object_relation_record", {"ok": True, **asdict(rel)})


def aitp_v5_record_authority(
    base: str,
    *,
    topic_id: str,
    authority_type: str,
    authority_statement: str,
    work_package: str = "",
    claim_id: str = "",
    scope: dict | None = None,
    generator_set: str = "",
    closure_envelope: str = "",
    evidence_refs: list[str] | None = None,
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    linked_records: dict | None = None,
    limitations: list[str] | None = None,
    status: str = "research_authority_not_trust_promotion",
) -> dict:
    """Record a convention/sector/dataset/code authority without claim-trust authority."""

    record = record_authority(
        _ws(base),
        topic_id=topic_id,
        authority_type=authority_type,
        authority_statement=authority_statement,
        work_package=work_package,
        claim_id=claim_id,
        scope=scope,
        generator_set=generator_set,
        closure_envelope=closure_envelope,
        evidence_refs=evidence_refs,
        source_refs=source_refs,
        artifact_ids=artifact_ids,
        linked_records=linked_records,
        limitations=limitations,
        status=status,
    )
    return require_valid_public_surface("authority_record", authority_record_payload(record))


def aitp_v5_list_authorities(
    base: str,
    *,
    topic_id: str,
    authority_type: str = "",
    work_package: str = "",
    include_inactive: bool = False,
) -> dict:
    """Return a read-only topic authority registry view."""

    return require_valid_public_surface(
        "authority_registry",
        authority_registry_payload(
            _ws(base),
            topic_id=topic_id,
            authority_type=authority_type,
            work_package=work_package,
            include_inactive=include_inactive,
        ),
    )


def aitp_v5_record_sensemaking_report(
    base: str, *, topic_id: str, claim_id: str, title: str, summary: str,
    object_ids: list[str] | None = None, relation_ids: list[str] | None = None,
    evidence_refs: list[str] | None = None, open_questions: list[str] | None = None,
    next_actions: list[str] | None = None,
) -> dict:
    report = record_sensemaking_report(_ws(base), topic_id=topic_id, claim_id=claim_id,
        title=title, summary=summary, object_ids=object_ids, relation_ids=relation_ids,
        evidence_refs=evidence_refs, open_questions=open_questions, next_actions=next_actions)
    return require_valid_public_surface("sensemaking_report_record", {"ok": True, **asdict(report)})


def aitp_v5_ingest_subagent_result(
    base: str, *, topic_id: str, packet: dict, result_payload: dict,
) -> dict:
    result = ingest_subagent_result(
        _ws(base),
        packet,
        topic_id=topic_id,
        result_payload=result_payload,
    )
    payload = result.to_payload()
    payload["evidence"] = require_valid_public_surface("evidence_record", {"ok": True, **payload["evidence"]})
    payload["proposal"] = require_valid_public_surface("sensemaking_report_record", {"ok": True, **payload["proposal"]})
    return {"ok": True, **payload}


def aitp_v5_create_validation_contract(
    base: str, *, topic_id: str, claim_id: str,
    required_checks: list[str] | None = None, failure_modes: list[str] | None = None,
    required_evidence_outputs: list[str] | None = None,
    tool_recipe_ids: list[str] | None = None, executor_ids: list[str] | None = None,
    validator_role: str = "adversarial_reviewer",
) -> dict:
    contract = create_validation_contract(_ws(base), topic_id=topic_id, claim_id=claim_id,
        required_checks=required_checks, failure_modes=failure_modes,
        required_evidence_outputs=required_evidence_outputs,
        tool_recipe_ids=tool_recipe_ids, executor_ids=executor_ids,
        validator_role=validator_role)
    return require_valid_public_surface("validation_contract_record", {"ok": True, **asdict(contract)})


def aitp_v5_record_validation_result(
    base: str, *, topic_id: str, claim_id: str, contract_id: str, tool_run_id: str,
    status: str, checked_outputs: list[str] | None = None, summary: str = "",
    evidence_refs: list[str] | None = None, artifact_ids: list[str] | None = None,
    covered_failure_modes: list[str] | None = None,
    failure_modes_observed: list[str] | None = None,
) -> dict:
    result = record_validation_result(_ws(base), topic_id=topic_id, claim_id=claim_id,
        contract_id=contract_id, tool_run_id=tool_run_id, status=status,
        checked_outputs=checked_outputs, summary=summary, evidence_refs=evidence_refs,
        artifact_ids=artifact_ids, covered_failure_modes=covered_failure_modes,
        failure_modes_observed=failure_modes_observed)
    return require_valid_public_surface("validation_result_record", {"ok": True, **asdict(result)})


def aitp_v5_request_human_checkpoint(
    base: str, *, topic_id: str, claim_id: str, reason: str, requested_by: str,
    options: list[str] | None = None,
) -> dict:
    chk = request_human_checkpoint(_ws(base), topic_id=topic_id, claim_id=claim_id,
        reason=reason, requested_by=requested_by, options=options)
    return require_valid_public_surface("human_checkpoint_record", {"ok": True, **asdict(chk)})


def aitp_v5_decide_human_checkpoint(
    base: str, *, checkpoint_id: str, decision: str, rationale: str, decided_by: str,
) -> dict:
    dec = decide_human_checkpoint(_ws(base), checkpoint_id=checkpoint_id,
        decision=decision, rationale=rationale, decided_by=decided_by)
    return require_valid_public_surface("human_checkpoint_record", {"ok": True, **asdict(dec)})


def aitp_v5_preview_quiet_checkpoint_batch(
    base: str,
    *,
    session_id: str,
    claim_id: str = "",
    run_id: str = "",
    summary: str,
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
) -> dict:
    """Preview a research-burst checkpoint batch without writing records."""

    return require_valid_public_surface(
        "quiet_checkpoint_preview",
        preview_quiet_checkpoint_batch(
            _ws(base),
            session_id,
            claim_id=claim_id,
            run_id=run_id,
            summary=summary,
            inputs=inputs,
            outputs=outputs,
            changed_files=changed_files,
            generated_artifacts=generated_artifacts,
            validation_commands=validation_commands,
            durable_observations=durable_observations,
            claim_boundary=claim_boundary,
            next_blockers=next_blockers,
            artifact_specs=artifact_specs,
            source_specs=source_specs,
            tool_run_specs=tool_run_specs,
            sensemaking_summary=sensemaking_summary,
            source_refs=source_refs,
        ),
    )


def aitp_v5_apply_quiet_checkpoint_batch(
    base: str,
    *,
    session_id: str,
    claim_id: str = "",
    run_id: str = "",
    summary: str,
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
) -> dict:
    """Apply a research-burst checkpoint batch without updating claim trust."""

    return require_valid_public_surface(
        "quiet_checkpoint_batch",
        apply_quiet_checkpoint_batch(
            _ws(base),
            session_id,
            claim_id=claim_id,
            run_id=run_id,
            summary=summary,
            inputs=inputs,
            outputs=outputs,
            changed_files=changed_files,
            generated_artifacts=generated_artifacts,
            validation_commands=validation_commands,
            durable_observations=durable_observations,
            claim_boundary=claim_boundary,
            next_blockers=next_blockers,
            artifact_specs=artifact_specs,
            source_specs=source_specs,
            tool_run_specs=tool_run_specs,
            sensemaking_summary=sensemaking_summary,
            source_refs=source_refs,
        ),
    )


def aitp_v5_create_promotion_packet(
    base: str, *, topic_id: str, claim_id: str, proposed_memory_kind: str = "scoped_claim",
    scope: str = "", evidence_refs: list[str] | None = None, non_claims: list[str] | None = None,
    known_failure_modes: list[str] | None = None, validation_result_ids: list[str] | None = None,
    failure_mode_review_checkpoint_id: str = "", failure_mode_review_result_id: str = "",
) -> dict:
    pkt = create_promotion_packet(_ws(base), topic_id=topic_id, claim_id=claim_id,
        proposed_memory_kind=proposed_memory_kind, scope=scope, evidence_refs=evidence_refs,
        validation_result_ids=validation_result_ids, non_claims=non_claims,
        known_failure_modes=known_failure_modes, failure_mode_review_checkpoint_id=failure_mode_review_checkpoint_id, failure_mode_review_result_id=failure_mode_review_result_id)
    return require_valid_public_surface("promotion_packet_record", {"ok": True, **asdict(pkt)})


def aitp_v5_apply_promotion_packet(
    base: str, *, packet_id: str, checkpoint_id: str,
) -> dict:
    entry = apply_promotion_packet(_ws(base), packet_id=packet_id, checkpoint_id=checkpoint_id)
    return require_valid_public_surface("memory_entry_record", {"ok": True, **asdict(entry)})


def aitp_v5_preflight_trust_update(
    base: str, *, action: str, session_id: str, topic_id: str, claim_id: str,
    requested_state: str = "", source_kind: str = "", source_ref: str = "",
    evidence_refs: list[str] | None = None, code_state_ids: list[str] | None = None,
    rationale: str = "", request_id: str = "", preflight_token: str = "",
) -> dict:
    return {"ok": True, **require_valid_public_surface("trust_update_preflight",
        preflight_trust_update(_ws(base), _trust_request(locals())))}


def aitp_v5_apply_trust_update(
    base: str, *, action: str, session_id: str, topic_id: str, claim_id: str,
    requested_state: str = "", source_kind: str = "", source_ref: str = "",
    evidence_refs: list[str] | None = None, code_state_ids: list[str] | None = None,
    rationale: str = "", request_id: str = "", preflight_token: str = "",
) -> dict:
    return {"ok": True, **require_valid_public_surface("trust_update_apply",
        apply_trust_update(_ws(base), _trust_request(locals())))}


def aitp_v5_get_trust_update_record(base: str, *, update_id: str) -> dict:
    record = get_trust_update_record(_ws(base), update_id)
    return require_valid_public_surface("trust_update_record", {"ok": True, **asdict(record)})


def _trust_request(ns: dict) -> TrustUpdateRequest:
    rid = ns.get("request_id") or f"trust-request-{ns['session_id']}-{ns['claim_id']}-{ns['action']}"
    return TrustUpdateRequest(request_id=rid, action=ns["action"], session_id=ns["session_id"],
        topic_id=ns["topic_id"], claim_id=ns["claim_id"], requested_state=ns.get("requested_state", ""),
        source_kind=ns.get("source_kind", ""), source_ref=ns.get("source_ref", ""),
        evidence_refs=ns.get("evidence_refs") or [], code_state_ids=ns.get("code_state_ids") or [],
        rationale=ns.get("rationale", ""), preflight_token=ns.get("preflight_token", ""))


def _linked_code_states(ws, claim_id: str) -> list[CodeStateRecord]:
    states = list_records(ws.registry_dir("code_states"), CodeStateRecord)
    return [s for s in states if _record_links_to_claim(s.linked_records, claim_id)]


def _record_links_to_claim(linked_records: dict, claim_id: str) -> bool:
    for value in linked_records.values():
        if value == claim_id or (isinstance(value, list) and claim_id in value):
            return True
    return False
