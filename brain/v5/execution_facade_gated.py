"""Host-attested checkpoint operations for the full M2 execution facade."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from brain.v5.bound_execution import BoundToolExecutionRequest, execute_bound_tool_request
from brain.v5.checkpoint_bindings import (
    CheckpointSubjectBinding,
    decide_bound_checkpoint,
    request_bound_checkpoint,
)
from brain.v5.execution_baselines import (
    BaselineAcceptanceRequest,
    accept_execution_baseline,
)
from brain.v5.execution_facade_common import coerce_pin, coerce_pins
from brain.v5.paths import WorkspacePaths
from brain.v5.pretool_policy import evaluate_context_pre_tool_policy
from brain.v5.record_envelope import RecordActor
from brain.v5.scope_revalidation import (
    ScopeRevalidationRequest,
    record_scope_revalidation,
)


_ACTOR = RecordActor(
    actor_type="tool",
    actor_id="execution-gated-facade",
    host="aitp-v5",
)
_EFFECT_POLICY_BY_ACTION = {
    "accept_execution_baseline": "execution_maturity_only",
    "approve_scope_revalidation": "scope_revalidation_only",
    "execute_bound_tool": "execution_records_only",
}


def dispatch_execution_gated(
    ws: WorkspacePaths,
    operation: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if operation == "execution_request_bound_checkpoint":
        return _request_checkpoint(ws, payload)
    if operation == "execution_decide_bound_checkpoint":
        return _decide_checkpoint(ws, payload)
    if operation == "execution_apply_bound_action":
        return _apply_action(ws, payload)
    raise ValueError(f"unsupported gated execution operation: {operation}")


def _request_checkpoint(ws: WorkspacePaths, payload: Mapping[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "")
    effect_policy = str(payload.get("effect_policy") or "")
    topic_id = str(payload.get("topic_id") or "")
    claim_id = str(payload.get("claim_id") or "")
    _require_session_scope(ws, payload, topic_id=topic_id, claim_id=claim_id)
    if action not in _EFFECT_POLICY_BY_ACTION:
        raise ValueError(f"unsupported bound checkpoint action: {action}")
    if effect_policy != _EFFECT_POLICY_BY_ACTION[action]:
        raise ValueError("bound checkpoint effect_policy does not match action")
    pre_tool = _pre_tool(
        ws,
        payload,
        action="request_human_checkpoint",
        claim_id=claim_id,
    )
    requested = request_bound_checkpoint(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        reason=str(payload.get("reason") or ""),
        requested_by=str(payload.get("requested_by") or ""),
        action=action,
        action_payload=_mapping(payload.get("action_payload"), "action_payload"),
        intent_ref=coerce_pin(payload.get("intent_ref"), "intent_ref"),
        subject_refs=coerce_pins(payload.get("subject_refs"), "subject_refs"),
        options=_strings(payload.get("options"), "options"),
        expires_at=str(payload.get("expires_at") or ""),
        replay_policy=str(payload.get("replay_policy") or ""),
        target_scope_refs=_strings(payload.get("target_scope_refs"), "target_scope_refs"),
        effect_policy=effect_policy,
        actor=_ACTOR,
    )
    return {
        "status": requested.write_status,
        "session_id": str(payload.get("session_id") or ""),
        "claim_id": claim_id,
        "checkpoint_id": requested.record.checkpoint_id,
        "request_ref": asdict(requested.request_ref),
        "binding": asdict(requested.binding),
        "pre_tool_decision": pre_tool,
    }


def _decide_checkpoint(ws: WorkspacePaths, payload: Mapping[str, Any]) -> dict[str, Any]:
    request_ref = coerce_pin(payload.get("request_ref"), "request_ref")
    topic_id, claim_id = _checkpoint_scope(ws, request_ref)
    _require_session_scope(ws, payload, topic_id=topic_id, claim_id=claim_id)
    pre_tool = _pre_tool(
        ws,
        payload,
        action="decide_human_checkpoint",
        claim_id=claim_id,
    )
    decided = decide_bound_checkpoint(
        ws,
        request_ref=request_ref,
        expected=_binding(payload.get("binding")),
        decision=str(payload.get("decision") or ""),
        rationale=str(payload.get("rationale") or ""),
        decided_by=str(payload.get("decided_by") or ""),
        approval_receipt=None,
    )
    return {
        "status": "decided",
        "session_id": str(payload.get("session_id") or ""),
        "claim_id": claim_id,
        "request_ref": asdict(decided.request_ref),
        "decision_ref": asdict(decided.decision_ref),
        "binding": asdict(decided.binding),
        "pre_tool_decision": pre_tool,
    }


def _apply_action(ws: WorkspacePaths, payload: Mapping[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "")
    request_ref = coerce_pin(payload.get("request_ref"), "request_ref")
    decision_ref = coerce_pin(payload.get("decision_ref"), "decision_ref")
    binding = _binding(payload.get("binding"))
    action_request = _mapping(payload.get("action_request"), "action_request")
    topic_id, claim_id = _checkpoint_scope(ws, decision_ref)
    _require_session_scope(ws, payload, topic_id=topic_id, claim_id=claim_id)
    pre_tool = _pre_tool(
        ws,
        payload,
        action=action,
        claim_id=claim_id,
        human_checkpoint_id=decision_ref.record_ref.partition(":")[2],
    )
    if action == "execute_bound_tool":
        request = _bound_tool_request(action_request)
        outcome = execute_bound_tool_request(
            ws,
            request,
            binding=binding,
            request_ref=request_ref,
            decision_ref=decision_ref,
            actor=_ACTOR,
        )
        result_refs = [asdict(outcome.tool_run_ref), asdict(outcome.validation_result_ref)]
        application_ref = outcome.application_receipt_ref
        replayed = outcome.replayed
    elif action == "approve_scope_revalidation":
        outcome = record_scope_revalidation(
            ws,
            _scope_revalidation_request(action_request),
            binding=binding,
            checkpoint_request_ref=request_ref,
            checkpoint_decision_ref=decision_ref,
            actor=_ACTOR,
        )
        result_refs = [asdict(outcome.pinned_ref)]
        application_ref = outcome.application_receipt_ref
        replayed = outcome.write_status == "unchanged"
    elif action == "accept_execution_baseline":
        outcome = accept_execution_baseline(
            ws,
            BaselineAcceptanceRequest(
                run_ref=coerce_pin(action_request.get("run_ref"), "run_ref"),
                validation_refs=coerce_pins(
                    action_request.get("validation_refs", []),
                    "validation_refs",
                ),
            ),
            binding=binding,
            checkpoint_request_ref=request_ref,
            checkpoint_decision_ref=decision_ref,
            actor=_ACTOR,
        )
        result_refs = [asdict(outcome.baseline_ref)]
        application_ref = outcome.checkpoint_application_receipt_ref
        replayed = outcome.replayed
    else:
        raise ValueError(f"unsupported bound checkpoint action: {action}")
    return {
        "status": "applied",
        "session_id": str(payload.get("session_id") or ""),
        "claim_id": claim_id,
        "action": action,
        "request_ref": asdict(request_ref),
        "decision_ref": asdict(decision_ref),
        "result_refs": result_refs,
        "application_receipt_ref": asdict(application_ref),
        "replayed": replayed,
        "pre_tool_decision": pre_tool,
    }


def _binding(value: Any) -> CheckpointSubjectBinding:
    data = _mapping(value, "binding")
    return CheckpointSubjectBinding(
        intent=coerce_pin(data.get("intent"), "binding.intent"),
        subjects=coerce_pins(data.get("subjects"), "binding.subjects"),
        action=str(data.get("action") or ""),
        action_payload_hash=str(data.get("action_payload_hash") or ""),
        request_hash=str(data.get("request_hash") or ""),
        target_scope_refs=tuple(_strings(data.get("target_scope_refs"), "binding.target_scope_refs")),
        effect_policy=str(data.get("effect_policy") or ""),
        replay_policy=str(data.get("replay_policy") or ""),
    )


def _bound_tool_request(data: Mapping[str, Any]) -> BoundToolExecutionRequest:
    return BoundToolExecutionRequest(
        executor_id=str(data.get("executor_id") or ""),
        recipe=coerce_pin(data.get("recipe"), "recipe"),
        topic_id=str(data.get("topic_id") or ""),
        claim_id=str(data.get("claim_id") or ""),
        inputs=_mapping(data.get("inputs"), "inputs"),
        argv=tuple(_strings(data.get("argv"), "argv")),
        environment_policy=_mapping(data.get("environment_policy"), "environment_policy"),
        write_policy=str(data.get("write_policy") or ""),
        network_policy=str(data.get("network_policy") or ""),
        timeout_seconds=data.get("timeout_seconds"),
        dependency_refs=coerce_pins(data.get("dependency_refs"), "dependency_refs"),
        revalidation_decision_refs=coerce_pins(
            data.get("revalidation_decision_refs", []),
            "revalidation_decision_refs",
        ),
    )


def _scope_revalidation_request(data: Mapping[str, Any]) -> ScopeRevalidationRequest:
    supersedes = data.get("supersedes_decision")
    return ScopeRevalidationRequest(
        bridge=coerce_pin(data.get("bridge"), "bridge"),
        source_refs=coerce_pins(data.get("source_refs"), "source_refs"),
        source_scope_refs=tuple(_strings(data.get("source_scope_refs"), "source_scope_refs")),
        target_topic_id=str(data.get("target_topic_id") or ""),
        target_claim_id=str(data.get("target_claim_id") or ""),
        target_program_id=str(data.get("target_program_id") or ""),
        target_scope_refs=tuple(_strings(data.get("target_scope_refs"), "target_scope_refs")),
        allowed_operations=tuple(_strings(data.get("allowed_operations"), "allowed_operations")),
        applicability_conditions=tuple(
            _strings(data.get("applicability_conditions"), "applicability_conditions")
        ),
        validation_refs=coerce_pins(data.get("validation_refs"), "validation_refs"),
        evidence_refs=coerce_pins(data.get("evidence_refs", []), "evidence_refs"),
        decision=str(data.get("decision") or ""),
        expires_at=str(data.get("expires_at") or ""),
        supersedes_decision=(
            coerce_pin(supersedes, "supersedes_decision") if supersedes else None
        ),
    )


def _pre_tool(
    ws: WorkspacePaths,
    payload: Mapping[str, Any],
    *,
    action: str,
    claim_id: str,
    human_checkpoint_id: str = "",
) -> dict[str, Any]:
    decision = evaluate_context_pre_tool_policy(
        ws,
        session_id=str(payload.get("session_id") or ""),
        action=action,
        claim_id=claim_id,
        source_kind="typed_records",
        risk_level="guided",
        human_checkpoint_id=human_checkpoint_id,
    )
    if decision.get("block") is True:
        raise ValueError(f"pre-tool policy blocked {action}: {decision.get('message', '')}")
    return decision


def _checkpoint_scope(ws: WorkspacePaths, checkpoint_ref) -> tuple[str, str]:
    from brain.v5.pinned_record_refs import get_record_version

    record = get_record_version(ws, checkpoint_ref).record
    topic_id = str(getattr(record, "topic_id", "") or "")
    claim_id = str(getattr(record, "claim_id", "") or "")
    if not topic_id or not claim_id:
        raise ValueError("bound checkpoint does not identify topic and claim scope")
    return topic_id, claim_id


def _require_session_scope(
    ws: WorkspacePaths,
    payload: Mapping[str, Any],
    *,
    topic_id: str,
    claim_id: str,
) -> None:
    from brain.v5.workspace import get_session_binding

    session_id = str(payload.get("session_id") or "")
    binding = get_session_binding(ws, session_id)
    if binding.topic_id != topic_id or binding.active_claim != claim_id:
        raise ValueError("execution facade session scope does not match checkpoint target")


def _mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _strings(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field_name} must contain non-empty strings")
    return list(value)
