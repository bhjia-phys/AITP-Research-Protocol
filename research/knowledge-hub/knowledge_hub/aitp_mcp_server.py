from __future__ import annotations

import json
import os
import traceback
from pathlib import Path
from typing import Any, Callable

from mcp.server.fastmcp import FastMCP

from .aitp_mcp_profiles import (
    build_profile_tool_manifest,
    normalize_mcp_profile,
    profile_instructions,
    server_name_for_mcp_profile,
    tool_allowed_in_profile,
)
from .aitp_service import AITPService
from .decision_point_handler import list_pending_decision_points, resolve_decision_point

service = AITPService()
ACTIVE_MCP_PROFILE = normalize_mcp_profile(os.environ.get("AITP_MCP_PROFILE"))
AITP_MCP_TOOL_ACCESS: dict[str, str] = {}
AITP_MCP_TOOL_FUNCTIONS: list[Callable[..., str]] = []


def aitp_tool(*, access: str) -> Callable[[Callable[..., str]], Callable[..., str]]:
    normalized_access = str(access).strip().lower()
    if normalized_access not in {"read", "write"}:
        raise ValueError(f"Unsupported MCP tool access mode: {access}")

    def decorator(func: Callable[..., str]) -> Callable[..., str]:
        AITP_MCP_TOOL_ACCESS[func.__name__] = normalized_access
        AITP_MCP_TOOL_FUNCTIONS.append(func)
        return func

    return decorator


def build_mcp_server(profile: str | None = None) -> FastMCP:
    resolved_profile = normalize_mcp_profile(profile)
    server = FastMCP(
        server_name_for_mcp_profile(resolved_profile),
        instructions=profile_instructions(resolved_profile),
    )
    for func in AITP_MCP_TOOL_FUNCTIONS:
        access = AITP_MCP_TOOL_ACCESS[func.__name__]
        if tool_allowed_in_profile(func.__name__, access, resolved_profile):
            server.add_tool(func)
    return server


def _tool_manifest(profile: str | None = None) -> dict[str, Any]:
    return build_profile_tool_manifest(profile, AITP_MCP_TOOL_ACCESS)


def _ok(**payload: object) -> str:
    return json.dumps({"status": "success", **payload}, ensure_ascii=False, indent=2)


def _err(message: str) -> str:
    return json.dumps(
        {
            "status": "error",
            "error": message,
            "traceback": traceback.format_exc(),
        },
        ensure_ascii=False,
        indent=2,
    )


def _compact_topic_state(topic_state: dict[str, Any] | None) -> dict[str, Any]:
    payload = topic_state or {}
    explainability = payload.get("status_explainability") or {}
    return {
        "resume_stage": payload.get("resume_stage"),
        "last_materialized_stage": payload.get("last_materialized_stage"),
        "research_mode": payload.get("research_mode"),
        "load_profile": payload.get("load_profile"),
        "summary": payload.get("summary") or explainability.get("current_status_summary"),
    }


def _compact_current_topic_memory(current_topic_memory: dict[str, Any] | None) -> dict[str, Any]:
    payload = current_topic_memory or {}
    return {
        "topic_slug": payload.get("topic_slug"),
        "summary": payload.get("summary"),
        "current_topic_path": payload.get("current_topic_path") or payload.get("current_topic_memory_path"),
        "current_topic_note_path": payload.get("current_topic_note_path"),
    }


def _runtime_protocol_postures(runtime_protocol: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    runtime_protocol_payload = runtime_protocol or {}
    protocol_path = runtime_protocol_payload.get("runtime_protocol_path")
    if not isinstance(protocol_path, str) or not protocol_path:
        return {}, {}
    try:
        payload = json.loads(Path(protocol_path).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}, {}
    return (
        payload.get("human_interaction_posture") or {},
        payload.get("autonomy_posture") or {},
    )


def _compact_bootstrap_result(result: dict[str, Any]) -> dict[str, Any]:
    conformance_state = result.get("conformance_state") or {}
    return {
        "topic_slug": result.get("topic_slug"),
        "runtime_root": result.get("runtime_root"),
        "command": result.get("command"),
        "conformance": {
            "overall_status": conformance_state.get("overall_status"),
        },
        "files": result.get("files") or {},
        "topic_state_summary": _compact_topic_state(result.get("topic_state")),
    }


def _compact_loop_result(result: dict[str, Any]) -> dict[str, Any]:
    loop_state = result.get("loop_state") or {}
    bootstrap = result.get("bootstrap") or {}
    bootstrap_topic_state = bootstrap.get("topic_state") or {}
    explainability = bootstrap_topic_state.get("status_explainability") or {}
    entry_audit = result.get("entry_audit") or {}
    exit_audit = result.get("exit_audit") or {}
    capability_audit = result.get("capability_audit") or {}
    trust_audit = result.get("trust_audit") or {}
    runtime_protocol = result.get("runtime_protocol") or {}
    human_interaction_posture, autonomy_posture = _runtime_protocol_postures(runtime_protocol)
    return {
        "topic_slug": result.get("topic_slug"),
        "run_id": result.get("run_id"),
        "load_profile": result.get("load_profile"),
        "loop_state_path": result.get("loop_state_path"),
        "loop_history_path": result.get("loop_history_path"),
        "runtime_protocol": runtime_protocol,
        "current_topic_memory": _compact_current_topic_memory(result.get("current_topic_memory")),
        "selected_action": explainability.get("next_bounded_action") or {},
        "human_interaction_posture": human_interaction_posture,
        "autonomy_posture": autonomy_posture,
        "audits": {
            "entry_conformance": (entry_audit.get("conformance_state") or {}).get("overall_status"),
            "exit_conformance": (exit_audit.get("conformance_state") or {}).get("overall_status"),
            "capability_status": capability_audit.get("overall_status") or loop_state.get("capability_status"),
            "capability_report_path": capability_audit.get("capability_report_path"),
            "trust_status": trust_audit.get("overall_status") or loop_state.get("trust_status"),
            "trust_audit_path": trust_audit.get("trust_audit_path"),
            "trust_report_path": trust_audit.get("trust_report_path"),
        },
        "auto_actions_executed": loop_state.get("auto_actions_executed"),
        "steering_artifacts": result.get("steering_artifacts") or {},
    }


@aitp_tool(access="read")
def aitp_describe_mcp_profile(profile: str | None = None) -> str:
    """Describe the active or requested AITP MCP profile and whether it is read-only."""
    try:
        manifest = _tool_manifest(profile or ACTIVE_MCP_PROFILE)
        return _ok(
            profile=manifest["profile"],
            server_name=manifest["server_name"],
            read_only=manifest["read_only"],
            allowed_tool_count=len(manifest["allowed_tools"]),
            blocked_tool_count=len(manifest["blocked_tools"]),
        )
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="read")
def aitp_list_tool_manifest(profile: str | None = None) -> str:
    """Show the MCP tool manifest for the active or requested AITP profile."""
    try:
        return _ok(manifest=_tool_manifest(profile or ACTIVE_MCP_PROFILE))
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_bootstrap_topic(
    topic: str | None = None,
    topic_slug: str | None = None,
    statement: str | None = None,
    run_id: str | None = None,
    control_note: str | None = None,
    updated_by: str = "aitp-mcp",
    arxiv_ids: list[str] | None = None,
    local_note_paths: list[str] | None = None,
    skill_queries: list[str] | None = None,
    human_request: str | None = None,
) -> str:
    """Bootstrap or update an AITP topic through the kernel orchestrator."""
    try:
        result = service.orchestrate(
            topic_slug=topic_slug,
            topic=topic,
            statement=statement,
            run_id=run_id,
            control_note=control_note,
            updated_by=updated_by,
            arxiv_ids=arxiv_ids or [],
            local_note_paths=local_note_paths or [],
            skill_queries=skill_queries or [],
            human_request=human_request,
        )
        return _ok(**_compact_bootstrap_result(result))
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_resume_topic(
    topic_slug: str,
    run_id: str | None = None,
    control_note: str | None = None,
    updated_by: str = "aitp-mcp",
    human_request: str | None = None,
    skill_queries: list[str] | None = None,
) -> str:
    """Resume an existing AITP topic."""
    try:
        result = service.orchestrate(
            topic_slug=topic_slug,
            run_id=run_id,
            control_note=control_note,
            updated_by=updated_by,
            human_request=human_request,
            skill_queries=skill_queries or [],
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="read")
def aitp_get_runtime_state(topic_slug: str) -> str:
    """Read the runtime topic_state.json for an AITP topic."""
    try:
        return _ok(topic_state=service.get_runtime_state(topic_slug))
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="read")
def aitp_get_topic_interaction(topic_slug: str, updated_by: str = "aitp-mcp") -> str:
    """Read the active human-interaction packet for a topic, including checkpoint options and pending decision points."""
    try:
        return _ok(**service.topic_interaction(topic_slug=topic_slug, updated_by=updated_by))
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="read")
def aitp_list_pending_decisions(topic_slug: str) -> str:
    """List pending durable decision points for a topic."""
    try:
        return _ok(decision_points=list_pending_decision_points(topic_slug, kernel_root=service.kernel_root))
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_resolve_pending_decision(
    topic_slug: str,
    decision_id: str,
    option: int,
    comment: str | None = None,
    resolved_by: str = "human",
) -> str:
    """Resolve one durable decision point for a topic."""
    try:
        payload = resolve_decision_point(
            topic_slug,
            decision_id,
            option,
            comment=comment,
            resolved_by=resolved_by,
            kernel_root=service.kernel_root,
        )
        return _ok(**payload)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_resolve_operator_checkpoint(
    topic_slug: str,
    option: int,
    comment: str | None = None,
    resolved_by: str = "human",
) -> str:
    """Resolve the active operator checkpoint for a topic after the human chooses an option."""
    try:
        payload = service.resolve_operator_checkpoint(
            topic_slug=topic_slug,
            option_index=option,
            comment=comment,
            resolved_by=resolved_by,
        )
        return _ok(**payload)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_audit_conformance(topic_slug: str, phase: str = "entry", updated_by: str = "aitp-mcp") -> str:
    """Run the AITP conformance audit for a topic."""
    try:
        result = service.audit(topic_slug=topic_slug, phase=phase, updated_by=updated_by)
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_scaffold_baseline(
    topic_slug: str,
    run_id: str,
    title: str,
    reference: str,
    agreement_criterion: str,
    baseline_kind: str = "public_example",
    updated_by: str = "aitp-mcp",
    notes: str | None = None,
) -> str:
    """Create baseline-reproduction placeholder artifacts for an AITP validation run."""
    try:
        result = service.scaffold_baseline(
            topic_slug=topic_slug,
            run_id=run_id,
            title=title,
            reference=reference,
            agreement_criterion=agreement_criterion,
            baseline_kind=baseline_kind,
            updated_by=updated_by,
            notes=notes,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_scaffold_atomic_understanding(
    topic_slug: str,
    run_id: str,
    method_title: str,
    updated_by: str = "aitp-mcp",
    scope_note: str | None = None,
) -> str:
    """Create atomic-understanding placeholder artifacts for a theory method."""
    try:
        result = service.scaffold_atomic_understanding(
            topic_slug=topic_slug,
            run_id=run_id,
            method_title=method_title,
            updated_by=updated_by,
            scope_note=scope_note,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_scaffold_operation(
    topic_slug: str,
    run_id: str | None,
    title: str,
    kind: str,
    updated_by: str = "aitp-mcp",
    summary: str | None = None,
    notes: str | None = None,
    baseline_required: bool | None = None,
    atomic_understanding_required: bool | None = None,
    references: list[str] | None = None,
    source_paths: list[str] | None = None,
) -> str:
    """Register a reusable operation under the trust registry for a validation run."""
    try:
        result = service.scaffold_operation(
            topic_slug=topic_slug,
            run_id=run_id,
            title=title,
            kind=kind,
            updated_by=updated_by,
            summary=summary,
            notes=notes,
            baseline_required=baseline_required,
            atomic_understanding_required=atomic_understanding_required,
            references=references or [],
            source_paths=source_paths or [],
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_update_operation(
    topic_slug: str,
    run_id: str | None,
    operation: str,
    updated_by: str = "aitp-mcp",
    summary: str | None = None,
    notes: str | None = None,
    baseline_status: str | None = None,
    atomic_understanding_status: str | None = None,
    references: list[str] | None = None,
    source_paths: list[str] | None = None,
    artifact_paths: list[str] | None = None,
) -> str:
    """Update operation trust status, references, or result artifacts."""
    try:
        result = service.update_operation(
            topic_slug=topic_slug,
            run_id=run_id,
            operation=operation,
            updated_by=updated_by,
            summary=summary,
            notes=notes,
            baseline_status=baseline_status,
            atomic_understanding_status=atomic_understanding_status,
            references=references or [],
            source_paths=source_paths or [],
            artifact_paths=artifact_paths or [],
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_audit_operation_trust(
    topic_slug: str,
    run_id: str | None = None,
    updated_by: str = "aitp-mcp",
) -> str:
    """Audit whether tracked operations are baseline- and understanding-ready for reuse."""
    try:
        result = service.audit_operation_trust(
            topic_slug=topic_slug,
            run_id=run_id,
            updated_by=updated_by,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_audit_capability(
    topic_slug: str,
    updated_by: str = "aitp-mcp",
) -> str:
    """Audit runtime/operator capability state for an AITP topic."""
    try:
        result = service.capability_audit(
            topic_slug=topic_slug,
            updated_by=updated_by,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_audit_theory_coverage(
    topic_slug: str,
    candidate_id: str,
    run_id: str | None = None,
    updated_by: str = "aitp-mcp",
    source_sections: list[str] | None = None,
    covered_sections: list[str] | None = None,
    equation_labels: list[str] | None = None,
    notation_bindings: list[dict[str, str]] | None = None,
    derivation_nodes: list[str] | None = None,
    agent_votes: list[dict[str, str]] | None = None,
    consensus_status: str = "unanimous",
    critical_unit_recall: float = 1.0,
    missing_anchor_count: int = 0,
    skeptic_major_gap_count: int = 0,
    supporting_regression_question_ids: list[str] | None = None,
    supporting_oracle_ids: list[str] | None = None,
    supporting_regression_run_ids: list[str] | None = None,
    promotion_blockers: list[str] | None = None,
    split_required: bool | None = None,
    cited_recovery_required: bool | None = None,
    followup_gap_ids: list[str] | None = None,
    topic_completion_status: str | None = None,
    notes: str | None = None,
) -> str:
    """Record theory coverage, notation, derivation, and consensus artifacts for a candidate."""
    try:
        result = service.audit_theory_coverage(
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            run_id=run_id,
            updated_by=updated_by,
            source_sections=source_sections or [],
            covered_sections=covered_sections or [],
            equation_labels=equation_labels or [],
            notation_bindings=notation_bindings or [],
            derivation_nodes=derivation_nodes or [],
            agent_votes=agent_votes or [],
            consensus_status=consensus_status,
            critical_unit_recall=critical_unit_recall,
            missing_anchor_count=missing_anchor_count,
            skeptic_major_gap_count=skeptic_major_gap_count,
            supporting_regression_question_ids=supporting_regression_question_ids or [],
            supporting_oracle_ids=supporting_oracle_ids or [],
            supporting_regression_run_ids=supporting_regression_run_ids or [],
            promotion_blockers=promotion_blockers or [],
            split_required=split_required,
            cited_recovery_required=cited_recovery_required,
            followup_gap_ids=followup_gap_ids or [],
            topic_completion_status=topic_completion_status,
            notes=notes,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_audit_formal_theory(
    topic_slug: str,
    candidate_id: str,
    run_id: str | None = None,
    updated_by: str = "aitp-mcp",
    formal_theory_role: str = "trusted_target",
    statement_graph_role: str = "target_statement",
    definition_trust_tier: str | None = None,
    target_statement_id: str | None = None,
    statement_graph_parents: list[str] | None = None,
    statement_graph_children: list[str] | None = None,
    informal_statement: str | None = None,
    formal_target: str | None = None,
    faithfulness_status: str = "pending",
    faithfulness_strategy: str | None = None,
    faithfulness_notes: str | None = None,
    comparator_audit_status: str = "pending",
    comparator_risks: list[str] | None = None,
    nearby_variants: list[dict[str, str]] | None = None,
    comparator_notes: str | None = None,
    provenance_kind: str = "generated_from_scratch",
    attribution_requirements: list[str] | None = None,
    provenance_sources: list[str] | None = None,
    provenance_notes: str | None = None,
    prerequisite_closure_status: str = "pending",
    lean_prerequisite_ids: list[str] | None = None,
    supporting_obligation_ids: list[str] | None = None,
    formalization_blockers: list[str] | None = None,
    prerequisite_notes: str | None = None,
) -> str:
    """Record durable formal-theory trust-boundary and prerequisite-closure audits for a candidate."""
    try:
        result = service.audit_formal_theory(
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            run_id=run_id,
            updated_by=updated_by,
            formal_theory_role=formal_theory_role,
            statement_graph_role=statement_graph_role,
            definition_trust_tier=definition_trust_tier,
            target_statement_id=target_statement_id,
            statement_graph_parents=statement_graph_parents or [],
            statement_graph_children=statement_graph_children or [],
            informal_statement=informal_statement,
            formal_target=formal_target,
            faithfulness_status=faithfulness_status,
            faithfulness_strategy=faithfulness_strategy,
            faithfulness_notes=faithfulness_notes,
            comparator_audit_status=comparator_audit_status,
            comparator_risks=comparator_risks or [],
            nearby_variants=nearby_variants or [],
            comparator_notes=comparator_notes,
            provenance_kind=provenance_kind,
            attribution_requirements=attribution_requirements or [],
            provenance_sources=provenance_sources or [],
            provenance_notes=provenance_notes,
            prerequisite_closure_status=prerequisite_closure_status,
            lean_prerequisite_ids=lean_prerequisite_ids or [],
            supporting_obligation_ids=supporting_obligation_ids or [],
            formalization_blockers=formalization_blockers or [],
            prerequisite_notes=prerequisite_notes,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_complete_topic(
    topic_slug: str,
    run_id: str | None = None,
    updated_by: str = "aitp-mcp",
) -> str:
    """Assess topic-completion status against regression support and follow-up debt."""
    try:
        result = service.assess_topic_completion(
            topic_slug=topic_slug,
            run_id=run_id,
            updated_by=updated_by,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_update_followup_return(
    topic_slug: str,
    return_status: str,
    run_id: str | None = None,
    accepted_return_shape: str | None = None,
    return_summary: str | None = None,
    child_topic_summary: str | None = None,
    return_artifact_paths: list[str] | None = None,
    updated_by: str = "aitp-mcp",
) -> str:
    """Update a child-topic follow-up return packet before parent reintegration."""
    try:
        result = service.update_followup_return_packet(
            topic_slug=topic_slug,
            run_id=run_id,
            return_status=return_status,
            accepted_return_shape=accepted_return_shape,
            return_summary=return_summary,
            child_topic_summary=child_topic_summary,
            return_artifact_paths=return_artifact_paths or [],
            updated_by=updated_by,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_reintegrate_followup(
    topic_slug: str,
    child_topic_slug: str,
    run_id: str | None = None,
    updated_by: str = "aitp-mcp",
) -> str:
    """Reintegrate a child follow-up topic back into its parent topic."""
    try:
        result = service.reintegrate_followup_subtopic(
            topic_slug=topic_slug,
            child_topic_slug=child_topic_slug,
            run_id=run_id,
            updated_by=updated_by,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_prepare_lean_bridge(
    topic_slug: str,
    run_id: str | None = None,
    candidate_id: str | None = None,
    updated_by: str = "aitp-mcp",
) -> str:
    """Materialize Lean-ready bridge packets for a topic or bounded candidate."""
    try:
        result = service.prepare_lean_bridge(
            topic_slug=topic_slug,
            run_id=run_id,
            candidate_id=candidate_id,
            updated_by=updated_by,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_request_promotion(
    topic_slug: str,
    candidate_id: str,
    run_id: str | None = None,
    route: str = "L3->L4->L2",
    backend_id: str | None = None,
    target_backend_root: str | None = None,
    updated_by: str = "aitp-mcp",
    notes: str | None = None,
) -> str:
    """Create a durable human-approval request before Layer 2 promotion."""
    try:
        result = service.request_promotion(
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            run_id=run_id,
            route=route,
            backend_id=backend_id,
            target_backend_root=target_backend_root,
            requested_by=updated_by,
            notes=notes,
        )
        payload = dict(result)
        payload["gate_status"] = payload.pop("status", None)
        return _ok(**payload)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_approve_promotion(
    topic_slug: str,
    candidate_id: str,
    run_id: str | None = None,
    updated_by: str = "aitp-mcp",
    notes: str | None = None,
) -> str:
    """Approve a pending Layer 2 promotion request."""
    try:
        result = service.approve_promotion(
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            run_id=run_id,
            approved_by=updated_by,
            notes=notes,
        )
        payload = dict(result)
        payload["gate_status"] = payload.pop("status", None)
        return _ok(**payload)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_reject_promotion(
    topic_slug: str,
    candidate_id: str,
    run_id: str | None = None,
    updated_by: str = "aitp-mcp",
    notes: str | None = None,
) -> str:
    """Reject a pending Layer 2 promotion request."""
    try:
        result = service.reject_promotion(
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            run_id=run_id,
            rejected_by=updated_by,
            notes=notes,
        )
        payload = dict(result)
        payload["gate_status"] = payload.pop("status", None)
        return _ok(**payload)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_promote_candidate(
    topic_slug: str,
    candidate_id: str,
    run_id: str | None = None,
    backend_id: str | None = None,
    target_backend_root: str | None = None,
    domain: str | None = None,
    subdomain: str | None = None,
    source_id: str | None = None,
    source_section: str | None = None,
    source_section_title: str | None = None,
    updated_by: str = "aitp-mcp",
    notes: str | None = None,
) -> str:
    """Promote an approved candidate into the configured Layer 2 backend."""
    try:
        result = service.promote_candidate(
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            run_id=run_id,
            promoted_by=updated_by,
            backend_id=backend_id,
            target_backend_root=target_backend_root,
            domain=domain,
            subdomain=subdomain,
            source_id=source_id,
            source_section=source_section,
            source_section_title=source_section_title,
            notes=notes,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_auto_promote_candidate(
    topic_slug: str,
    candidate_id: str,
    run_id: str | None = None,
    backend_id: str | None = None,
    target_backend_root: str | None = None,
    domain: str | None = None,
    subdomain: str | None = None,
    source_id: str | None = None,
    source_section: str | None = None,
    source_section_title: str | None = None,
    updated_by: str = "aitp-mcp",
    notes: str | None = None,
) -> str:
    """Auto-promote a theory candidate into L2_auto after coverage and consensus gates pass."""
    try:
        result = service.auto_promote_candidate(
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            run_id=run_id,
            promoted_by=updated_by,
            backend_id=backend_id,
            target_backend_root=target_backend_root,
            domain=domain,
            subdomain=subdomain,
            source_id=source_id,
            source_section=source_section,
            source_section_title=source_section_title,
            notes=notes,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_run_topic_loop(
    topic_slug: str | None = None,
    topic: str | None = None,
    statement: str | None = None,
    run_id: str | None = None,
    control_note: str | None = None,
    updated_by: str = "aitp-mcp",
    human_request: str | None = None,
    skill_queries: list[str] | None = None,
    max_auto_steps: int = 4,
) -> str:
    """Run the safe AITP auto-continue loop, including capability and trust audits."""
    try:
        result = service.run_topic_loop(
            topic_slug=topic_slug,
            topic=topic,
            statement=statement,
            run_id=run_id,
            control_note=control_note,
            updated_by=updated_by,
            human_request=human_request,
            skill_queries=skill_queries or [],
            max_auto_steps=max_auto_steps,
        )
        return _ok(**_compact_loop_result(result))
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@aitp_tool(access="write")
def aitp_install_agent_wrapper(
    agent: str,
    scope: str = "user",
    target_root: str | None = None,
    force: bool = True,
    install_mcp: bool = True,
    mcp_profile: str = "full",
) -> str:
    """Install AITP wrapper files for Codex, OpenClaw, or OpenCode."""
    try:
        result = service.install_agent(
            agent=agent,
            scope=scope,
            target_root=target_root,
            force=force,
            install_mcp=install_mcp,
            mcp_profile=mcp_profile,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


mcp = build_mcp_server(ACTIVE_MCP_PROFILE)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
