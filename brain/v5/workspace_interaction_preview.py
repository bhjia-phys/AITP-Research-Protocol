"""Workspace-level preview of natural interaction recording boundaries."""

from __future__ import annotations

from collections import Counter
from typing import Any

from brain.v5.evidence import required_output_coverage
from brain.v5.flow import resolve_flow_profile
from brain.v5.interaction import resolve_interaction_profile
from brain.v5.interaction_preview import _heavier_triggers, _recording_decision
from brain.v5.models import ClaimRecord, CodeStateRecord, EvidenceRecord, SessionBinding
from brain.v5.risk import action_budget_for_level, assess_claim_risk
from brain.v5.store import list_records


def build_workspace_interaction_preview(ws) -> dict[str, Any]:
    """Summarize per-session interaction previews without mutating kernel state."""

    sessions = list_records(ws.root / "runtime" / "sessions", SessionBinding)
    claims = {claim.claim_id: claim for claim in list_records(ws.registry_dir("claims"), ClaimRecord)}
    evidence = _group_by_claim(list_records(ws.registry_dir("evidence"), EvidenceRecord))
    code_states = list_records(ws.registry_dir("code_states"), CodeStateRecord)
    items = [_item_for_session(session, claims, evidence, code_states) for session in sessions]
    mode_counts = Counter(item["recording_mode"] for item in items)
    source_records = {
        "sessions": [item["session_id"] for item in items],
        "topics": _unique(item["topic_id"] for item in items if item["topic_id"]),
        "claims": [item["active_claim"] for item in items if item["active_claim"]],
    }
    return {
        "kind": "workspace_interaction_preview_bundle",
        "session_count": len(items),
        "decision_mode_counts": dict(mode_counts),
        "items": items,
        "preview_refs": [item["source_preview_ref"] for item in items],
        "source_records": source_records,
        "derived_from": "interaction_recording_preview",
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "adapter_rule": "read_for_orientation_then_call_kernel_before_trust_updates",
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _item_for_session(
    session: SessionBinding,
    claims: dict[str, ClaimRecord],
    evidence_by_claim: dict[str, list[EvidenceRecord]],
    code_states: list[CodeStateRecord],
) -> dict[str, Any]:
    claim = claims.get(session.active_claim) if session.active_claim else None
    if claim is None:
        risk_level = "guided"
        flow_profile = "guided"
        action_budget = action_budget_for_level("guided")
        missing_outputs: list[str] = []
        checkpoint_needed = False
    else:
        risk = assess_claim_risk(claim, code_states=_linked_code_states(code_states, claim.claim_id))
        flow = resolve_flow_profile(claim, assessment=risk)
        action_budget = risk.action_budget if risk.action_budget else action_budget_for_level(risk.level)
        coverage = required_output_coverage(
            evidence_by_claim.get(claim.claim_id, []),
            required_outputs=action_budget.required_outputs,
        )
        risk_level = risk.level
        flow_profile = flow.profile
        missing_outputs = list(coverage.missing_outputs)
        checkpoint_needed = bool(action_budget.requires_human_checkpoint)
    interaction = resolve_interaction_profile(
        session.interaction_profile,
        risk_level=action_budget.level,
        max_questions=action_budget.max_questions,
        user_steering=session.interaction_steering,
    )
    decision = _recording_decision(
        active_claim=bool(claim),
        risk_level=risk_level,
        missing_outputs=missing_outputs,
        checkpoint_needed=checkpoint_needed,
    )
    return {
        "session_id": session.session_id,
        "topic_id": session.topic_id,
        "active_claim": claim.claim_id if claim else "",
        "interaction_role": interaction.profile.role,
        "risk_level": risk_level,
        "flow_profile": flow_profile,
        "recording_mode": decision["mode"],
        "can_stay_lightweight": risk_level in {"fluid", "guided"} and not checkpoint_needed,
        "next_kernel_entrypoint": decision["next_kernel_entrypoint"],
        "mandatory_question_count": 0,
        "max_questions": interaction.effective_max_questions,
        "heavier_triggers": _heavier_triggers(risk_level, missing_outputs, checkpoint_needed),
        "source_brief_ref": f"execution_brief:{session.session_id}",
        "source_preview_ref": f"interaction_recording_preview:{session.session_id}",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _group_by_claim(records: list[EvidenceRecord]) -> dict[str, list[EvidenceRecord]]:
    grouped: dict[str, list[EvidenceRecord]] = {}
    for record in records:
        grouped.setdefault(record.claim_id, []).append(record)
    return grouped


def _linked_code_states(code_states: list[CodeStateRecord], claim_id: str) -> list[CodeStateRecord]:
    return [state for state in code_states if _record_links_to_claim(state.linked_records, claim_id)]


def _record_links_to_claim(linked_records: dict, claim_id: str) -> bool:
    for value in linked_records.values():
        if value == claim_id:
            return True
        if isinstance(value, list) and claim_id in value:
            return True
    return False


def _unique(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
