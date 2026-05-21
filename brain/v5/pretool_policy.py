"""Shared context-aware pre-tool policy decisions for AITP v5."""

from __future__ import annotations

from typing import Any

from brain.v5.hook_adapters import hook_decision_payload
from brain.v5.hooks import decide_pre_tool_use
from brain.v5.models import CodeStateRecord, HumanCheckpointRecord
from brain.v5.policy import PolicyDecision, evaluate_policy
from brain.v5.store import list_records
from brain.v5.workspace import get_claim, get_session_binding


_CONTEXT_ACTIONS = {
    "record_code_state",
    "record_evidence",
    "record_tool_run",
    "execute_tool",
    "record_reference_location",
    "record_physics_object",
    "record_object_relation",
    "record_sensemaking_report",
    "ingest_subagent_result",
    "create_validation_contract",
    "request_human_checkpoint",
    "decide_human_checkpoint",
    "create_promotion_packet",
    "apply_promotion_packet",
    "validate_claim",
    "promote_to_l2",
}


def context_policy_decision(
    ws,
    *,
    session_id: str,
    action: str,
    claim_id: str = "",
    evidence_refs: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    source_kind: str = "",
    source_ref: str = "",
    orientation_only: bool = False,
    risk_level: str = "guided",
    human_checkpoint_id: str = "",
) -> PolicyDecision | None:
    """Evaluate typed-record policy for actions whose correctness depends on claim context."""

    if action not in _CONTEXT_ACTIONS:
        return None
    resolved_claim_id = _resolve_claim_id(ws, session_id, claim_id)
    claim = get_claim(ws, resolved_claim_id)
    approved_checkpoint = _approved_checkpoint_for_claim(ws, claim.claim_id, human_checkpoint_id)
    return evaluate_policy(
        action=action,
        claim=claim,
        code_states=_resolve_code_states(ws, claim.claim_id, _clean_list(code_state_ids)),
        evidence_refs=_clean_list(evidence_refs),
        risk_level=risk_level,
        context={
            "source_kind": source_kind.strip().lower(),
            "source_ref": source_ref,
            "orientation_only": orientation_only,
            "human_checkpoint_id": human_checkpoint_id,
            "human_checkpoint_approved": approved_checkpoint,
        },
    )


def evaluate_context_pre_tool_policy(
    ws,
    *,
    session_id: str,
    action: str,
    claim_id: str = "",
    evidence_refs: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    source_kind: str = "",
    source_ref: str = "",
    orientation_only: bool = False,
    risk_level: str = "guided",
    human_checkpoint_id: str = "",
) -> dict[str, Any]:
    """Return a public hook-decision payload derived only from typed kernel records."""

    resolved_claim_id = _resolve_claim_id(ws, session_id, claim_id)
    policy = context_policy_decision(
        ws,
        session_id=session_id,
        action=action,
        claim_id=resolved_claim_id,
        evidence_refs=evidence_refs,
        code_state_ids=code_state_ids,
        source_kind=source_kind,
        source_ref=source_ref,
        orientation_only=orientation_only,
        risk_level=risk_level,
        human_checkpoint_id=human_checkpoint_id,
    ) or PolicyDecision(allowed=True, action=action)
    decision = decide_pre_tool_use(action=action, risk_level=risk_level, policy_decision=policy)
    payload = {"ok": True, **hook_decision_payload(decision, hook_name="pre_tool")}
    payload.update(
        {
            "action": action,
            "session_id": session_id,
            "claim_id": resolved_claim_id,
            "risk_level": risk_level,
            "human_checkpoint_id": human_checkpoint_id,
            "policy_reasons": [
                {
                    "policy_id": reason.policy_id,
                    "severity": reason.severity,
                    "message": reason.message,
                }
                for reason in policy.reasons
            ],
            "truth_source": "typed_records",
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
        }
    )
    return payload


def _resolve_claim_id(ws, session_id: str, claim_id: str) -> str:
    resolved = claim_id.strip()
    if resolved:
        return resolved
    return get_session_binding(ws, session_id).active_claim


def _resolve_code_states(ws, claim_id: str, requested_ids: list[str]) -> list[CodeStateRecord]:
    states = list_records(ws.registry_dir("code_states"), CodeStateRecord)
    if requested_ids:
        wanted = set(requested_ids)
        return [state for state in states if state.code_state_id in wanted]
    return [state for state in states if _record_links_to_claim(state.linked_records, claim_id)]


def _approved_checkpoint_for_claim(ws, claim_id: str, checkpoint_id: str) -> bool:
    checkpoint_id = checkpoint_id.strip()
    if not checkpoint_id:
        return False
    records = list_records(ws.registry_dir("checkpoints"), HumanCheckpointRecord)
    return any(
        record.checkpoint_id == checkpoint_id
        and record.claim_id == claim_id
        and record.status == "decided"
        and record.decision == "approve"
        for record in records
    )


def _record_links_to_claim(linked_records: dict, claim_id: str) -> bool:
    for value in linked_records.values():
        if value == claim_id or (isinstance(value, list) and claim_id in value):
            return True
    return False


def _clean_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return [str(value) for value in values if str(value)]
