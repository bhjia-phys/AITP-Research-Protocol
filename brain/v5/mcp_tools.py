"""Thin MCP-facing wrappers around the AITP v5 kernel."""

from __future__ import annotations

from dataclasses import asdict
from importlib import import_module
from pathlib import Path

from brain.v5.adapter_protocols import adapter_protocol_registry, record_gate_coverage_audit
from brain.v5.adapter_runtime import evaluate_platform_pre_tool_event
from brain.v5.adapters import build_adapter_packet
from brain.v5.brief import build_execution_brief
from brain.v5.code import capture_code_state_from_git, record_code_state
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
from brain.v5.mcp_kimi_hooks import aitp_v5_install_kimi_code_hook_config, aitp_v5_write_kimi_code_hook_config
from brain.v5.mcp_legacy import aitp_v5_apply_legacy_semantic_repair, aitp_v5_apply_legacy_source_reconstruction_repair, aitp_v5_audit_legacy_migration_coverage, aitp_v5_build_legacy_executable_evidence_packet, aitp_v5_build_legacy_human_checkpoint_packet, aitp_v5_build_legacy_l2_graph_manifest, aitp_v5_build_legacy_l2_typed_migration_packet, aitp_v5_build_legacy_runtime_log_marker_audit, aitp_v5_build_legacy_semantic_needs_revision_basis_packet, aitp_v5_build_legacy_semantic_needs_revision_basis_queue, aitp_v5_build_legacy_semantic_repair_manifest, aitp_v5_build_legacy_semantic_repair_plan, aitp_v5_build_legacy_semantic_review_manifest, aitp_v5_build_legacy_semantic_review_packet, aitp_v5_build_legacy_semantic_review_queue, aitp_v5_build_legacy_semantic_review_worklist, aitp_v5_build_legacy_source_metadata_repair_packet, aitp_v5_build_legacy_source_reconstruction_manifest, aitp_v5_build_legacy_source_reconstruction_plan, aitp_v5_build_legacy_source_reconstruction_review_packet, aitp_v5_build_legacy_topic_question_backfill_packet, aitp_v5_list_curated_legacy_topics, aitp_v5_migrate_curated_legacy_topic_to_v5, aitp_v5_migrate_legacy_topic_to_v5, aitp_v5_record_legacy_semantic_review_result, aitp_v5_write_legacy_human_checkpoint_obsidian_view, aitp_v5_write_legacy_l2_obsidian_view, aitp_v5_write_legacy_semantic_needs_revision_basis_obsidian_view, aitp_v5_write_legacy_semantic_review_obsidian_view, aitp_v5_write_legacy_source_reconstruction_obsidian_view
from brain.v5.hook_smoke_coverage import runtime_hook_smoke_coverage_report
from brain.v5.knowledge_connectors import describe_knowledge_connectors
from brain.v5.models import CodeStateRecord, TrustUpdateRequest
from brain.v5.pretool_policy import evaluate_context_pre_tool_policy
from brain.v5.public_surfaces import describe_public_surfaces, require_valid_public_surface
from brain.v5.physics_objects import record_object_relation, record_physics_object
from brain.v5.process_graph import build_process_graph_slice
from brain.v5.references import record_reference_location
from brain.v5.routes import record_research_route, research_route_payload
from brain.v5.runtime_bridge_targets import runtime_bridge_target_manifest
from brain.v5.runtime_payload_profiles import runtime_payload_profiles
from brain.v5.sensemaking import record_sensemaking_report
from brain.v5.source_assets import capture_source_asset_from_local_path, register_source_asset, source_asset_payload
from brain.v5.validation import create_validation_contract, record_validation_result
from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
from brain.v5.memory import apply_promotion_packet, create_promotion_packet
from brain.v5.mcp_evidence import aitp_v5_record_evidence
from brain.v5.mcp_host_readiness import aitp_v5_audit_priority_host_production_loops, aitp_v5_audit_runtime_host_lifecycle, aitp_v5_audit_runtime_host_readiness
from brain.v5.mcp_hook_install import aitp_v5_install_codex_hook_fixture, aitp_v5_install_opencode_hook_fixture
from brain.v5.mcp_interaction import aitp_v5_build_interaction_recording_worklist, aitp_v5_build_workspace_interaction_preview, aitp_v5_preview_interaction_recording
from brain.v5.mcp_lane_exemplars import aitp_v5_build_lane_exemplar_manifest, aitp_v5_record_lane_exemplar
from brain.v5.mcp_literature import aitp_v5_record_literature_candidate, aitp_v5_suggest_literature_intake
from brain.v5.mcp_memory import aitp_v5_audit_failure_mode_coverage, aitp_v5_audit_l2_memory_context, aitp_v5_build_failure_mode_review_packet, aitp_v5_record_failure_mode_review_result, aitp_v5_request_failure_mode_review_checkpoint, aitp_v5_write_l2_obsidian_view
from brain.v5.mcp_operator_checkpoint import aitp_v5_answer_operator_checkpoint, aitp_v5_request_operator_checkpoint
from brain.v5.mcp_output_stability import aitp_v5_build_vnext_readiness_manifest, aitp_v5_record_final_output_profile
from brain.v5.mcp_qsgw_cockpit import aitp_v5_write_qsgw_cockpit_surfaces, aitp_v5_write_qsgw_cockpit_surfaces_compact
from brain.v5.mcp_research_cockpit import aitp_v5_write_research_cockpit_surfaces, aitp_v5_write_research_cockpit_surfaces_compact
from brain.v5.mcp_research_state import aitp_v5_attach_artifact, aitp_v5_attach_artifact_auto, aitp_v5_classify_research_event, aitp_v5_create_proof_obligation, aitp_v5_record_bounded_numerical_evidence, aitp_v5_register_source, aitp_v5_update_claim_status, aitp_v5_update_proof_obligation
from brain.v5.mcp_research_intent import aitp_v5_materialize_steering_redirect, aitp_v5_record_research_intent_packet
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


def _ws(base: str):
    return init_workspace(Path(base))


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
    session = bind_session(_ws(base), session_id, topic_id=topic_id, context_id=context_id,
        active_claim=active_claim, interaction_profile=interaction_profile,
        interaction_steering=interaction_steering)
    return {"ok": True, **asdict(session)}


def aitp_v5_get_execution_brief(base: str, *, session_id: str) -> dict:
    return require_valid_public_surface("execution_brief", build_execution_brief(_ws(base), session_id))


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


def aitp_v5_get_runtime_payload_profiles() -> dict:
    """Return host-event to AITP typed-write payload profiles."""

    return {
        "ok": True,
        "runtime_payload_profiles": require_valid_public_surface(
            "runtime_payload_profiles",
            runtime_payload_profiles(),
        ),
    }


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
    metadata: dict | None = None, linked_records: dict | None = None, status: str = "active",
) -> dict:
    obj = record_physics_object(_ws(base), topic_id=topic_id, object_type=object_type,
        name=name, definition=definition, notation=notation, assumptions=assumptions,
        source_refs=source_refs, metadata=metadata, linked_records=linked_records, status=status)
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
