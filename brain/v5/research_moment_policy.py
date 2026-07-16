"""Pure deterministic policy for host-neutral research moments."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any, Mapping

from brain.v5.paths import WorkspacePaths
from brain.v5.research_moment_contracts import (
    RECURSIVE_AITP_ORIGINS,
    ResearchEvent,
    ResearchMomentDecision,
    decision_fingerprint,
    normalize_decision,
    normalize_research_event,
)
from brain.v5.research_moment_validation import (
    claim_id,
    default_action,
    families_for_refs,
    is_knowledge_discovery,
    is_unchanged_poll,
    payload_refs,
    requested_action,
    required_payload_text,
    stale_pins,
    unique_refs,
    unreadable_refs,
    validated_capture_arguments,
    validated_discovery_spec,
    validated_semantic_payload,
    workspace_identity,
)


_PROCESS_CAPTURE_OPERATIONS = {
    "SourceAcquired": "capture_source_asset_auto",
    "CodeStateChanged": "capture_code_state_auto",
    "ToolRunCompleted": "capture_tool_run_auto",
    "ArtifactProduced": "attach_artifact_auto",
}
_PROCESS_TARGET_FAMILIES = {
    "capture_source_asset_auto": ("source_assets",),
    "capture_code_state_auto": ("code_states",),
    "capture_tool_run_auto": ("tool_runs",),
    "attach_artifact_auto": ("artifacts",),
}
_HIGH_AUTHORITY_ACTIONS = frozenset(
    {
        "accept_baseline",
        "apply_skill_install",
        "install_skill",
        "promote_claim_trust",
        "rebind_active_claim",
        "submit_expensive_hpc_run",
        "update_claim_trust",
    }
)


def decide_research_moment(
    ws: WorkspacePaths,
    event: ResearchEvent,
) -> ResearchMomentDecision:
    """Return exactly one deterministic decision and perform no write."""

    event = normalize_research_event(event)
    if event.recursion_origin in RECURSIVE_AITP_ORIGINS:
        return _decision(
            ws,
            event,
            outcome="ignore",
            reason_codes=("recursive_aitp_output",),
            application_operation="",
            declared_effect="read_only",
        )
    if is_unchanged_poll(event):
        return _decision(
            ws,
            event,
            outcome="ignore",
            reason_codes=("unchanged_status_poll",),
            application_operation="",
            declared_effect="read_only",
        )

    base_refs = unique_refs(
        f"session:{event.session_id}",
        f"topic:{event.topic_id}",
        *event.subject_refs,
    )
    try:
        prerequisites = payload_refs(event.objective_payload.get("prerequisite_refs", ()))
        semantic_sources = payload_refs(event.semantic_payload.get("source_refs", ()))
    except (TypeError, ValueError):
        return _invalid_payload_decision(
            ws,
            event,
            reason_code="invalid_typed_ref_payload",
            minimum_refs=base_refs,
        )
    required_refs = unique_refs(
        *base_refs,
        *prerequisites,
        *semantic_sources,
    )
    missing = unreadable_refs(ws, required_refs)
    try:
        stale = stale_pins(ws, event.objective_payload.get("pinned_prerequisites", ()))
        stale.extend(payload_refs(event.objective_payload.get("stale_refs", ())))
    except (TypeError, ValueError):
        return _invalid_payload_decision(
            ws,
            event,
            reason_code="invalid_pinned_prerequisite",
            minimum_refs=required_refs,
        )
    if missing or stale:
        return _decision(
            ws,
            event,
            outcome="block_until_prerequisites",
            reason_codes=tuple(
                [
                    *(f"missing_ref:{ref}" for ref in missing),
                    *(f"stale_ref:{ref}" for ref in sorted(set(stale))),
                ]
            ),
            minimum_refs=unique_refs(*required_refs, *missing, *stale),
            blocked_action=requested_action(event) or default_action(event),
            application_operation="",
            declared_effect="read_only",
            verification_steps=("resolve every missing or stale exact record before retry",),
        )
    if event.objective_payload and event.semantic_payload:
        return _decision(
            ws,
            event,
            outcome="block_until_prerequisites",
            reason_codes=("mixed_objective_and_semantic_event",),
            minimum_refs=required_refs,
            blocked_action=default_action(event),
            application_operation="",
            declared_effect="read_only",
            verification_steps=("emit separate atomic objective and semantic events",),
        )

    if event.event_type == "SessionCloseout":
        try:
            milestone_id = required_payload_text(event.objective_payload, "milestone_id")
        except ValueError:
            return _invalid_payload_decision(
                ws,
                event,
                reason_code="closeout_milestone_missing",
                minimum_refs=required_refs,
            )
        return _decision(
            ws,
            event,
            outcome="coalesce_for_review",
            reason_codes=("session_closeout_review_boundary",),
            target_families=("recording_candidate_batches",),
            minimum_refs=required_refs,
            application_operation="recording_batch",
            application_payload={"milestone_id": milestone_id},
            declared_effect="kernel_write",
            verification_steps=("review the coalesced candidate batch before canonical promotion",),
        )

    action = requested_action(event)
    if event.event_type in {"MajorConclusionPending", "ExpensiveRunPending"} or (
        action in _HIGH_AUTHORITY_ACTIONS
    ):
        if event.event_type == "ExpensiveRunPending" and not prerequisites:
            return _decision(
                ws,
                event,
                outcome="block_until_prerequisites",
                reason_codes=("expensive_action_prerequisites_not_declared",),
                minimum_refs=required_refs,
                blocked_action=action or "expensive_run",
                application_operation="",
                declared_effect="read_only",
                verification_steps=("declare exact prerequisite_refs before requesting approval",),
            )
        checkpoint_action = action or (
            "review_major_conclusion"
            if event.event_type == "MajorConclusionPending"
            else "review_expensive_run"
        )
        target_claim = claim_id(event)
        options = event.objective_payload.get("options") or ("approve", "revise", "reject")
        if not target_claim or not isinstance(options, (list, tuple)) or not all(
            isinstance(item, str) and item.strip() for item in options
        ):
            return _invalid_payload_decision(
                ws,
                event,
                reason_code="checkpoint_payload_incomplete",
                minimum_refs=required_refs,
                blocked_action=checkpoint_action,
            )
        return _decision(
            ws,
            event,
            outcome="require_checkpoint",
            reason_codes=("human_authority_required",),
            target_families=("checkpoints",),
            minimum_refs=required_refs,
            required_checkpoint_action=checkpoint_action,
            application_operation="request_human_checkpoint",
            application_payload={
                "claim_id": target_claim,
                "reason": str(
                    event.objective_payload.get("reason")
                    or f"Human review required before {checkpoint_action}."
                ),
                "options": list(options),
            },
            declared_effect="kernel_write",
            verification_steps=("bind the operator decision to the checkpoint receipt",),
        )

    if is_knowledge_discovery(event):
        try:
            discovery_spec = validated_discovery_spec(
                event.objective_payload.get("discovery_spec")
            )
            discovery_stale = stale_pins(
                ws,
                (
                    discovery_spec["gap_ref"],
                    discovery_spec["prior_audit_ref"],
                ),
            )
        except (TypeError, ValueError):
            return _invalid_payload_decision(
                ws,
                event,
                reason_code="invalid_discovery_prerequisites",
                minimum_refs=required_refs,
            )
        if discovery_stale:
            return _decision(
                ws,
                event,
                outcome="block_until_prerequisites",
                reason_codes=tuple(f"stale_ref:{ref}" for ref in discovery_stale),
                minimum_refs=unique_refs(*required_refs, *discovery_stale),
                blocked_action="bounded_literature_discovery",
                application_operation="",
                declared_effect="read_only",
                verification_steps=("refresh the persisted gap and recall audit pins",),
            )
        if event.objective_payload.get("external_read_approved") is not True:
            target_claim = claim_id(event)
            if not target_claim:
                return _invalid_payload_decision(
                    ws,
                    event,
                    reason_code="discovery_claim_not_resolved",
                    minimum_refs=required_refs,
                )
            return _decision(
                ws,
                event,
                outcome="require_checkpoint",
                reason_codes=("external_read_requires_approval",),
                target_families=("checkpoints",),
                minimum_refs=required_refs,
                required_checkpoint_action="approve_bounded_literature_discovery",
                application_operation="request_human_checkpoint",
                application_payload={
                    "claim_id": target_claim,
                    "reason": "Approve bounded read-only literature discovery.",
                    "options": ["approve", "revise", "reject"],
                },
                declared_effect="kernel_write",
            )
        return _decision(
            ws,
            event,
            outcome="auto_capture_process",
            reason_codes=("persisted_knowledge_gap_discovery_handoff",),
            target_families=("proof_obligations", "recall_audits"),
            minimum_refs=required_refs,
            application_operation="knowledge_build_discovery_request",
            application_payload={"discovery_spec": discovery_spec},
            declared_effect="read_only",
            verification_steps=(
                "normalize connector coverage before any source acquisition",
                "keep snippets and unacquired candidates outside grounded knowledge",
            ),
        )

    if event.semantic_payload:
        try:
            semantic = validated_semantic_payload(
                event,
                semantic_sources or event.subject_refs,
            )
        except (TypeError, ValueError):
            return _invalid_payload_decision(
                ws,
                event,
                reason_code="invalid_semantic_candidate",
                minimum_refs=required_refs,
            )
        return _decision(
            ws,
            event,
            outcome="stage_semantic_candidate",
            reason_codes=("semantic_signal_requires_review",),
            target_families=("recording_candidate_batches",),
            minimum_refs=required_refs,
            application_operation="codex_recording_step",
            application_payload={"candidate": semantic},
            declared_effect="runtime_write",
            verification_steps=("coalesce and review the candidate at a milestone",),
            expires_at=str(semantic["expires_at"]),
        )

    if event.event_type in _PROCESS_CAPTURE_OPERATIONS:
        requested_operation = str(
            event.objective_payload.get("capture_operation") or "verify_existing"
        ).strip()
        expected_operation = _PROCESS_CAPTURE_OPERATIONS[event.event_type]
        if requested_operation == "verify_existing":
            if not event.subject_refs:
                return _decision(
                    ws,
                    event,
                    outcome="block_until_prerequisites",
                    reason_codes=("objective_event_has_no_exact_subject_ref",),
                    minimum_refs=required_refs,
                    blocked_action="verify_existing_process_record",
                    application_operation="",
                    declared_effect="read_only",
                )
            return _verify_existing_decision(ws, event, required_refs)
        if requested_operation != expected_operation:
            return _decision(
                ws,
                event,
                outcome="block_until_prerequisites",
                reason_codes=("capture_operation_not_allowed_for_event",),
                minimum_refs=required_refs,
                blocked_action=requested_operation or "unknown_capture_operation",
                application_operation="",
                declared_effect="read_only",
            )
        try:
            arguments = validated_capture_arguments(event, requested_operation)
        except (TypeError, ValueError):
            return _invalid_payload_decision(
                ws,
                event,
                reason_code="invalid_capture_arguments",
                minimum_refs=required_refs,
                blocked_action=requested_operation,
            )
        return _decision(
            ws,
            event,
            outcome="auto_capture_process",
            reason_codes=("exact_objective_process_capture",),
            target_families=_PROCESS_TARGET_FAMILIES[requested_operation],
            minimum_refs=required_refs,
            application_operation=requested_operation,
            application_payload={"arguments": arguments},
            declared_effect="kernel_write",
            verification_steps=("read back the deterministic typed process record",),
        )

    if (
        str(event.objective_payload.get("capture_operation") or "").strip()
        == "verify_existing"
        and event.subject_refs
    ):
        return _verify_existing_decision(ws, event, required_refs)

    return _decision(
        ws,
        event,
        outcome="ignore",
        reason_codes=("no_durable_research_moment",),
        minimum_refs=required_refs,
        application_operation="",
        declared_effect="read_only",
    )


def _verify_existing_decision(
    ws: WorkspacePaths,
    event: ResearchEvent,
    required_refs: tuple[str, ...],
) -> ResearchMomentDecision:
    return _decision(
        ws,
        event,
        outcome="auto_capture_process",
        reason_codes=("exact_process_record_already_exists",),
        target_families=families_for_refs(event.subject_refs),
        minimum_refs=required_refs,
        application_operation="exact_record_expansion",
        application_payload={"record_refs": list(event.subject_refs)},
        declared_effect="read_only",
        verification_steps=("read every exact process ref through RecordRepository",),
    )


def _invalid_payload_decision(
    ws: WorkspacePaths,
    event: ResearchEvent,
    *,
    reason_code: str,
    minimum_refs: tuple[str, ...],
    blocked_action: str = "",
) -> ResearchMomentDecision:
    return _decision(
        ws,
        event,
        outcome="block_until_prerequisites",
        reason_codes=(reason_code,),
        minimum_refs=minimum_refs,
        blocked_action=blocked_action or default_action(event),
        application_operation="",
        declared_effect="read_only",
        verification_steps=("repair the structured event payload before retry",),
    )


def _decision(
    ws: WorkspacePaths,
    event: ResearchEvent,
    *,
    outcome: str,
    reason_codes: tuple[str, ...],
    application_operation: str,
    declared_effect: str,
    target_families: tuple[str, ...] = (),
    minimum_refs: tuple[str, ...] = (),
    verification_steps: tuple[str, ...] = (),
    required_checkpoint_action: str = "",
    blocked_action: str = "",
    application_payload: Mapping[str, Any] | None = None,
    expires_at: str = "",
) -> ResearchMomentDecision:
    expiry = expires_at or (
        datetime.fromisoformat(event.occurred_at) + timedelta(days=1)
    ).isoformat()
    payload = dict(application_payload or {})
    normalized = normalize_decision(
        ResearchMomentDecision(
            decision_id="pending-research-moment-decision",
            event=event,
            outcome=outcome,
            reason_codes=reason_codes,
            target_families=target_families,
            minimum_refs=minimum_refs,
            dedup_key="0" * 64,
            expires_at=expiry,
            verification_steps=verification_steps,
            required_checkpoint_action=required_checkpoint_action,
            blocked_action=blocked_action,
            application_operation=application_operation,
            application_payload=payload,
            declared_effect=declared_effect,
            trust_effect="none",
            can_update_claim_trust=False,
        )
    )
    digest = decision_fingerprint(
        workspace_identity(ws),
        normalized.event,
        outcome=normalized.outcome,
        reason_codes=normalized.reason_codes,
        target_families=normalized.target_families,
        minimum_refs=normalized.minimum_refs,
        expires_at=normalized.expires_at,
        verification_steps=normalized.verification_steps,
        required_checkpoint_action=normalized.required_checkpoint_action,
        blocked_action=normalized.blocked_action,
        application_operation=normalized.application_operation,
        application_payload=normalized.application_payload,
        declared_effect=normalized.declared_effect,
    )
    return replace(
        normalized,
        decision_id=f"research-moment-decision:{digest}",
        dedup_key=digest,
    )
