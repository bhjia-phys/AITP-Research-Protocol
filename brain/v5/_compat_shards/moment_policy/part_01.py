# Compatibility shard 1 for moment_policy.
from __future__ import annotations

from typing import Any

from brain.v5.payload_hints import with_draft_schema

_ACTIVE_STATUSES = {"open", "active"}

def build_host_agnostic_moment_policy(
    *,
    session_id: str,
    topic_id: str,
    claim_id: str,
    open_obligations: list[dict[str, Any]],
    source_backtrace: list[dict[str, Any]],
    relation_neighborhood: list[dict[str, Any]],
    exploratory_records: list[dict[str, Any]],
    route_state: dict[str, Any] | None = None,
    trust_boundary_reasons: list[str],
) -> dict[str, Any]:
    """Return read-only policy decisions for recording, exploration, and trust boundaries."""

    decisions: list[dict[str, Any]] = []
    decisions.extend(_recording_decisions(open_obligations, session_id=session_id))
    decisions.extend(_source_backtrace_decisions(source_backtrace, session_id=session_id))
    decisions.extend(_relation_brainstorm_decisions(relation_neighborhood, session_id=session_id))
    decisions.extend(_exploratory_decisions(exploratory_records))
    decisions.extend(_route_decisions(route_state or {}))
    decisions.extend(_trust_boundary_decisions(source_backtrace, decisions, topic_id=topic_id, session_id=session_id))
    decisions = _dedupe_decisions(decisions)

    return {
        "ok": True,
        "kind": "host_agnostic_moment_policy",
        "session_id": session_id,
        "topic_id": topic_id,
        "claim_id": claim_id,
        "policy_axes": ["recording", "brainstorming", "backtrace", "route", "trust_boundary"],
        "decisions": decisions,
        "recommended_moments": [_moment_summary(item) for item in decisions],
        "trust_boundary_reasons": list(trust_boundary_reasons),
        "adapter_rule": "hosts may read this policy for orientation, then call typed kernel entrypoints before trust changes",
        "derived_from": "process_graph_slice",
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }

def _recording_decisions(open_obligations: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [
        _decision(
            moment="record_or_validate_open_obligation",
            decision_type="recording",
            action_kind="record_evidence_or_validation",
            required_now=True,
            reason="open proof obligation requires typed evidence or validation",
            target_type="proof_obligation",
            target_id=str(obligation["obligation_id"]),
            topic_id=str(obligation.get("topic_id") or ""),
            claim_id=str(obligation.get("claim_id") or ""),
            target_record=obligation,
            session_id=session_id,
            record_entrypoints=["aitp_v5_record_evidence", "aitp_v5_record_validation_result"],
            required_before_trust_change=[
                "record typed evidence or validation for the open obligation",
                "run aitp_v5_preflight_trust_update",
            ],
        )
        for obligation in open_obligations
    ]

def _source_backtrace_decisions(source_backtrace: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    decisions = []
    for item in source_backtrace:
        missing = list(item.get("missing_components") or [])
        if not missing:
            continue
        decisions.append(
            _decision(
                moment="backtrace_source_reconstruction",
                decision_type="backtrace",
                action_kind="reconstruct_missing_source_components",
                required_now=True,
                reason="missing source reconstruction components",
                target_type="claim",
                target_id=str(item.get("claim_id") or ""),
                topic_id=str(item.get("topic_id") or ""),
                claim_id=str(item.get("claim_id") or ""),
                target_record=item,
                session_id=session_id,
                missing_components=missing,
                record_entrypoints=[
                    "aitp_v5_record_exploratory_record",
                    "aitp_v5_record_reference_location",
                    "aitp_v5_capture_source_asset_auto",
                    "aitp_v5_register_source_asset",
                ],
                exploration_entrypoints=["aitp_v5_record_exploratory_record"],
                required_before_trust_change=[
                    "backtrace missing source components to typed records",
                    "record evidence only after source and provenance are explicit",
                    "run aitp_v5_preflight_trust_update",
                ],
            )
        )
    return decisions

def _relation_brainstorm_decisions(relations: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    decisions = []
    for relation in relations:
        if str(relation.get("status") or "").strip().lower() != "hypothesis":
            continue
        decisions.append(
            _decision(
                moment="brainstorm_relation_path",
                decision_type="brainstorming",
                action_kind="brainstorm_relation_path_before_validation",
                required_now=False,
                reason="object relation is still a hypothesis",
                target_type="object_relation",
                target_id=str(relation.get("relation_id") or ""),
                topic_id=str(relation.get("topic_id") or ""),
                claim_id=str(relation.get("claim_id") or ""),
                session_id=session_id,
                target_record=relation,
                exploration_entrypoints=["aitp_v5_record_exploratory_record"],
                required_before_trust_change=[
                    "convert relation-path brainstorm into typed evidence or validation",
                    "run aitp_v5_preflight_trust_update",
                ],
            )
        )
    return decisions

def _exploratory_decisions(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions = []
    for record in records:
        status = str(record.get("status") or "")
        if status not in _ACTIVE_STATUSES:
            continue
        record_id = str(record.get("record_id") or "")
        exploration_type = str(record.get("exploration_type") or "")
        if exploration_type == "question_decomposition":
            decisions.append(
                _decision(
                    moment="direction.brainstorm",
                    decision_type="brainstorming",
                    action_kind="steer_next_local_analysis",
                    required_now=False,
                    reason="open question decomposition should steer the next local analysis",
                    target_type="exploratory_record",
                    target_id=record_id,
                    topic_id=str(record.get("topic_id") or ""),
                    claim_id=str(record.get("claim_id") or ""),
                    session_id=str(record.get("session_id") or ""),
                    target_record=record,
                    exploration_entrypoints=["aitp_v5_record_exploratory_record"],
                )
            )
        if exploration_type == "relation_path_brainstorm":
            decisions.append(
                _decision(
                    moment="brainstorm_relation_path",
                    decision_type="brainstorming",
                    action_kind="continue_relation_path_brainstorm",
                    required_now=False,
                    reason="relation path brainstorming is open",
                    target_type="exploratory_record",
                    target_id=record_id,
                    topic_id=str(record.get("topic_id") or ""),
                    claim_id=str(record.get("claim_id") or ""),
                    session_id=str(record.get("session_id") or ""),
                    target_record=record,
                    exploration_entrypoints=["aitp_v5_record_exploratory_record"],
                )
            )
        if exploration_type in {"source_asset", "backtrace_step"}:
            decisions.append(
                _decision(
                    moment="backtrace_source_reconstruction",
                    decision_type="backtrace",
                    action_kind="continue_source_or_backtrace_record",
                    required_now=False,
                    reason="exploratory source/backtrace record is still open",
                    target_type="exploratory_record",
                    target_id=record_id,
                    topic_id=str(record.get("topic_id") or ""),
                    claim_id=str(record.get("claim_id") or ""),
                    session_id=str(record.get("session_id") or ""),
                    target_record=record,
                    exploration_entrypoints=["aitp_v5_record_exploratory_record"],
                )
            )
        if record.get("original_question") and record.get("local_question"):
            decisions.append(
                _decision(
                    moment="audit_original_question_drift",
                    decision_type="brainstorming",
                    action_kind="check_local_question_against_original",
                    required_now=False,
                    reason="exploratory local question must stay tied to the original question",
                    target_type="exploratory_record",
                    target_id=record_id,
                    topic_id=str(record.get("topic_id") or ""),
                    claim_id=str(record.get("claim_id") or ""),
                    session_id=str(record.get("session_id") or ""),
                    target_record=record,
                    exploration_entrypoints=["aitp_v5_record_exploratory_record"],
                )
            )
    return decisions

def _route_decisions(route_state: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = []
    for route in route_state.get("routes") or []:
        if not isinstance(route, dict):
            continue
        status = str(route.get("status") or "")
        route_id = str(route.get("route_id") or "")
        if not route_id:
            continue
        if status in {"live", "selected"}:
            decisions.append(
                _decision(
                    moment="record_route_choice",
                    decision_type="route",
                    action_kind="record_route_choice_rationale",
                    required_now=False,
                    reason="live research route should preserve route-choice rationale",
                    target_type="research_route",
                    target_id=route_id,
                    topic_id=str(route.get("topic_id") or ""),
                    claim_id=str(route.get("claim_id") or ""),
                    session_id=str(route.get("session_id") or ""),
                    target_record=route,
                    record_entrypoints=["aitp_v5_record_research_route"],
                )
            )
        if status in {"blocked", "abandoned"}:
            decisions.append(
                _decision(
                    moment="record_failed_route_lesson",
                    decision_type="route",
                    action_kind="record_failed_route_lesson",
                    required_now=False,
                    reason="blocked or abandoned research route should preserve failure-mode lesson",
                    target_type="research_route",
                    target_id=route_id,
                    topic_id=str(route.get("topic_id") or ""),
                    claim_id=str(route.get("claim_id") or ""),
                    session_id=str(route.get("session_id") or ""),
                    target_record=route,
                    record_entrypoints=["aitp_v5_record_research_route"],
                )
            )
        if route.get("checkpoint_ids") or route.get("pivot_reason"):
            decisions.append(
                _decision(
                    moment="checkpoint_before_route_switch",
                    decision_type="route",
                    action_kind="checkpoint_before_route_switch",
                    required_now=False,
                    reason="route switch or pivot has checkpoint/pivot metadata",
                    target_type="research_route",
                    target_id=route_id,
                    topic_id=str(route.get("topic_id") or ""),
                    claim_id=str(route.get("claim_id") or ""),
                    session_id=str(route.get("session_id") or ""),
                    target_record=route,
                    record_entrypoints=["aitp_v5_record_research_route"],
                    exploration_entrypoints=["aitp_v5_request_human_checkpoint"],
                )
            )
    return decisions

def _trust_boundary_decisions(
    source_backtrace: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    *,
    topic_id: str,
    session_id: str,
) -> list[dict[str, Any]]:
    claim_ids = {str(item.get("claim_id") or "") for item in source_backtrace if item.get("claim_id")}
    risky_targets = [item for item in decisions if item["required_before_trust_change"]]
    if not risky_targets:
        return []
    if not claim_ids:
        claim_ids = {
            str(item["target_id"])
            for item in risky_targets
            if item["target_type"] == "claim" and item.get("target_id")
        }
    return [
        _decision(
            moment="trust_boundary_before_claim_update",
            decision_type="trust_boundary",
            action_kind="block_trust_change_until_policy_prerequisites_are_met",
            required_now=True,
            reason="recording, brainstorming, or backtrace prerequisites exist before any claim-trust update",
            target_type="claim",
            target_id=claim_id,
            topic_id=topic_id,
            claim_id=claim_id,
            session_id=session_id,
            required_before_trust_change=[
                "resolve required recording/backtrace/brainstorm policy decisions",
                "run aitp_v5_preflight_trust_update",
            ],
        )
        for claim_id in sorted(claim_ids)
    ]

def _decision(
    *,
    moment: str,
    decision_type: str,
    action_kind: str,
    required_now: bool,
    reason: str,
    target_type: str,
    target_id: str,
    topic_id: str = "",
    claim_id: str = "",
    session_id: str = "",
    target_record: dict[str, Any] | None = None,
    record_entrypoints: list[str] | None = None,
    exploration_entrypoints: list[str] | None = None,
    required_before_trust_change: list[str] | None = None,
    missing_components: list[str] | None = None,
) -> dict[str, Any]:
    record_points = record_entrypoints or []
    exploration_points = exploration_entrypoints or []
    trust_prerequisites = required_before_trust_change or []
    entrypoints = _entrypoints(record_points, exploration_points, trust_prerequisites)
    lifecycle_contract = _lifecycle_contract(
        decision_type=decision_type,
        action_kind=action_kind,
        required_now=required_now,
        reason=reason,
        target_type=target_type,
        target_id=target_id,
        claim_id=claim_id,
        entrypoints=entrypoints,
        required_before_trust_change=trust_prerequisites,
    )
    return {
        "moment": moment,
        "decision_type": decision_type,
        "action_kind": action_kind,
        "required_now": required_now,
        "reason": reason,
        "target_type": target_type,
        "target_id": target_id,
        "missing_components": missing_components or [],
        "record_entrypoints": record_points,
        "exploration_entrypoints": exploration_points,
        "entrypoints": entrypoints,
        **lifecycle_contract,
        "payload_hints": _payload_hints(
            action_kind=action_kind,
            target_type=target_type,
            target_id=target_id,
            topic_id=topic_id,
            claim_id=claim_id,
            session_id=session_id,
            target_record=target_record or {},
            record_entrypoints=record_points,
            exploration_entrypoints=exploration_points,
            trust_entrypoints=[item for item in entrypoints if item == "aitp_v5_preflight_trust_update"],
        ),
        "required_before_trust_change": trust_prerequisites,
        "trust_boundary": bool(trust_prerequisites),
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }

def _lifecycle_contract(
    *,
    decision_type: str,
    action_kind: str,
    required_now: bool,
    reason: str,
    target_type: str,
    target_id: str,
    claim_id: str,
    entrypoints: list[str],
    required_before_trust_change: list[str],
) -> dict[str, Any]:
    return {
        "lifecycle_phases": _lifecycle_phases(
            decision_type=decision_type,
            action_kind=action_kind,
            required_now=required_now,
            required_before_trust_change=required_before_trust_change,
        ),
        "trigger_conditions": _trigger_conditions(
            decision_type=decision_type,
            action_kind=action_kind,
            required_now=required_now,
            reason=reason,
            required_before_trust_change=required_before_trust_change,
        ),
        "recording_threshold": _recording_threshold(
            decision_type=decision_type,
            required_now=required_now,
            action_kind=action_kind,
        ),
        "trust_boundary_inputs": {
            "target_refs": [f"{target_type}:{target_id}"],
            "claim_id": claim_id or (target_id if target_type == "claim" else ""),
            "entrypoints": list(entrypoints),
            "required_before_trust_change": list(required_before_trust_change),
            "requires_preflight": "aitp_v5_preflight_trust_update" in entrypoints,
            "final_gate_required": decision_type == "trust_boundary" or bool(required_before_trust_change),
        },
        "recommended_host_behavior": _recommended_host_behavior(
            decision_type=decision_type,
            required_now=required_now,
            entrypoints=entrypoints,
            required_before_trust_change=required_before_trust_change,
        ),
    }

def _lifecycle_phases(
    *,
    decision_type: str,
    action_kind: str,
    required_now: bool,
    required_before_trust_change: list[str],
) -> list[str]:
    if decision_type == "trust_boundary":
        return ["pre_action", "pre_final"]
    if required_now or required_before_trust_change:
        return ["pre_turn", "pre_action", "pre_final"]
    if decision_type == "backtrace":
        return ["pre_turn", "pre_action"]
    if decision_type == "route":
        return ["pre_turn", "pre_action"]
    if decision_type == "brainstorming" and "original" in action_kind:
        return ["pre_turn", "pre_action", "pre_final"]
    if decision_type == "brainstorming":
        return ["pre_turn", "pre_action"]
    return ["pre_turn"]
