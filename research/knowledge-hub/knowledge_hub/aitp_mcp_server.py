from __future__ import annotations

import json
import traceback

from mcp.server.fastmcp import FastMCP

from .aitp_service import AITPService


mcp = FastMCP(
    "aitp-kernel",
    instructions=(
        "AITP kernel tools for orchestrating topic runs, reading runtime state, "
        "scaffolding trust gates, auditing conformance, and installing agent wrappers."
    ),
)

service = AITPService()


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


@mcp.tool()
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
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@mcp.tool()
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


@mcp.tool()
def aitp_get_runtime_state(topic_slug: str) -> str:
    """Read the runtime topic_state.json for an AITP topic."""
    try:
        return _ok(topic_state=service.get_runtime_state(topic_slug))
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@mcp.tool()
def aitp_audit_conformance(topic_slug: str, phase: str = "entry", updated_by: str = "aitp-mcp") -> str:
    """Run the AITP conformance audit for a topic."""
    try:
        result = service.audit(topic_slug=topic_slug, phase=phase, updated_by=updated_by)
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


@mcp.tool()
def aitp_install_agent_wrapper(
    agent: str,
    scope: str = "user",
    target_root: str | None = None,
    force: bool = True,
    install_mcp: bool = True,
) -> str:
    """Install AITP wrapper files for Codex, OpenClaw, or OpenCode."""
    try:
        result = service.install_agent(
            agent=agent,
            scope=scope,
            target_root=target_root,
            force=force,
            install_mcp=install_mcp,
        )
        return _ok(**result)
    except Exception as exc:  # noqa: BLE001
        return _err(str(exc))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
