"""Host-agnostic policy for research moments in a process graph slice."""

from __future__ import annotations

from typing import Any


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
    trust_boundary_reasons: list[str],
) -> dict[str, Any]:
    """Return read-only policy decisions for recording, exploration, and trust boundaries."""

    decisions: list[dict[str, Any]] = []
    decisions.extend(_recording_decisions(open_obligations))
    decisions.extend(_source_backtrace_decisions(source_backtrace))
    decisions.extend(_relation_brainstorm_decisions(relation_neighborhood))
    decisions.extend(_exploratory_decisions(exploratory_records))
    decisions.extend(_trust_boundary_decisions(source_backtrace, decisions))
    decisions = _dedupe_decisions(decisions)

    return {
        "ok": True,
        "kind": "host_agnostic_moment_policy",
        "session_id": session_id,
        "topic_id": topic_id,
        "claim_id": claim_id,
        "policy_axes": ["recording", "brainstorming", "backtrace", "trust_boundary"],
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


def _recording_decisions(open_obligations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _decision(
            moment="record_or_validate_open_obligation",
            decision_type="recording",
            action_kind="record_evidence_or_validation",
            required_now=True,
            reason="open proof obligation requires typed evidence or validation",
            target_type="proof_obligation",
            target_id=str(obligation["obligation_id"]),
            record_entrypoints=["aitp_v5_record_evidence", "aitp_v5_record_validation_result"],
            required_before_trust_change=[
                "record typed evidence or validation for the open obligation",
                "run aitp_v5_preflight_trust_update",
            ],
        )
        for obligation in open_obligations
    ]


def _source_backtrace_decisions(source_backtrace: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                missing_components=missing,
                record_entrypoints=[
                    "aitp_v5_record_exploratory_record",
                    "aitp_v5_record_reference_location",
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


def _relation_brainstorm_decisions(relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                    exploration_entrypoints=["aitp_v5_record_exploratory_record"],
                )
            )
    return decisions


def _trust_boundary_decisions(source_backtrace: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
    record_entrypoints: list[str] | None = None,
    exploration_entrypoints: list[str] | None = None,
    required_before_trust_change: list[str] | None = None,
    missing_components: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "moment": moment,
        "decision_type": decision_type,
        "action_kind": action_kind,
        "required_now": required_now,
        "reason": reason,
        "target_type": target_type,
        "target_id": target_id,
        "missing_components": missing_components or [],
        "record_entrypoints": record_entrypoints or [],
        "exploration_entrypoints": exploration_entrypoints or [],
        "required_before_trust_change": required_before_trust_change or [],
        "trust_boundary": bool(required_before_trust_change),
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _moment_summary(decision: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "moment": decision["moment"],
        "reason": decision["reason"],
        "target_type": decision["target_type"],
        "target_id": decision["target_id"],
        "decision_type": decision["decision_type"],
        "required_now": decision["required_now"],
        "trust_boundary": decision["trust_boundary"],
    }
    if decision["missing_components"]:
        summary["missing_components"] = list(decision["missing_components"])
    return summary


def _dedupe_decisions(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        key = (item["moment"], item["decision_type"], item["target_type"], item["target_id"])
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
