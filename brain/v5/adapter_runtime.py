"""Runtime helpers that consume generated AITP v5 adapter bridge payloads."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from brain.v5.pretool_policy import evaluate_context_pre_tool_policy


def evaluate_bridge_lifecycle_event(
    ws,
    bridge_payload: dict[str, Any],
    event: dict[str, Any],
) -> dict[str, Any]:
    """Map a runtime lifecycle event through generated bridge gate protocols."""

    if event.get("lifecycle_event") != "pre_tool":
        raise ValueError("only pre_tool lifecycle events can produce gate policy decisions")
    if not _bridge_declares_pre_tool(bridge_payload):
        raise ValueError("bridge payload does not declare a pre_tool lifecycle call")
    action = str(event.get("action", ""))
    payload = evaluate_bridge_gate_pre_tool_policy(
        ws,
        bridge_payload,
        session_id=str(event.get("session_id", "")),
        action=action,
        claim_id=str(event.get("claim_id", "")),
        evidence_refs=_clean_list(event.get("evidence_refs")),
        code_state_ids=_clean_list(event.get("code_state_ids")),
        source_kind=str(event.get("source_kind", "typed_records")),
        source_ref=str(event.get("source_ref", "")),
        orientation_only=bool(event.get("orientation_only", False)),
        risk_level=str(event.get("risk_level", "guided")),
    )
    payload["runtime_event"] = {
        "lifecycle_event": "pre_tool",
        "action": action,
        "source_kind": str(event.get("source_kind", "typed_records")),
    }
    return payload


def evaluate_bridge_gate_pre_tool_policy(
    ws,
    bridge_payload: dict[str, Any],
    *,
    session_id: str,
    action: str,
    claim_id: str = "",
    evidence_refs: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    source_kind: str = "typed_records",
    source_ref: str = "",
    orientation_only: bool = False,
    risk_level: str = "guided",
) -> dict[str, Any]:
    """Evaluate the shared pre-tool policy using gate metadata from a bridge."""

    gate_protocol = _bridge_gate_protocol(bridge_payload, action)
    if gate_protocol.get("pre_tool_policy") != "aitp_v5_evaluate_pre_tool_policy":
        raise ValueError("bridge gate protocol must use aitp_v5_evaluate_pre_tool_policy")
    if "evaluate_pre_tool_policy" not in gate_protocol.get("sequence", []):
        raise ValueError("bridge gate protocol must sequence evaluate_pre_tool_policy")

    payload = evaluate_context_pre_tool_policy(
        ws,
        session_id=session_id,
        action=action,
        claim_id=claim_id,
        evidence_refs=evidence_refs,
        code_state_ids=code_state_ids,
        source_kind=source_kind,
        source_ref=source_ref,
        orientation_only=orientation_only,
        risk_level=risk_level,
    )
    payload["runtime_gate_protocol"] = {
        "source_protocol_field": "runtime_gate_protocols",
        "action": action,
        **deepcopy(gate_protocol),
    }
    return payload


def _bridge_declares_pre_tool(bridge_payload: dict[str, Any]) -> bool:
    if bridge_payload.get("kind") == "codex_hook_bridge":
        return any(call.get("hook_name") == "pre_tool" for call in bridge_payload.get("guard_calls", []))
    if bridge_payload.get("kind") == "opencode_plugin_bridge":
        calls = bridge_payload.get("plugin_bridge", {}).get("lifecycle_calls", [])
        return any(call.get("lifecycle_event") == "pre_tool" for call in calls)
    return False


def _bridge_gate_protocol(bridge_payload: dict[str, Any], action: str) -> dict[str, Any]:
    if bridge_payload.get("kind") == "codex_hook_bridge":
        gate_protocols = bridge_payload.get("gate_protocols", {})
    elif bridge_payload.get("kind") == "opencode_plugin_bridge":
        gate_protocols = bridge_payload.get("plugin_bridge", {}).get("gate_protocols", {})
    else:
        raise ValueError("unsupported bridge payload kind")
    if gate_protocols.get("source_protocol_field") != "runtime_gate_protocols":
        raise ValueError("bridge gate protocols must come from runtime_gate_protocols")
    protocol = gate_protocols.get(action)
    if not isinstance(protocol, dict):
        raise ValueError(f"bridge gate protocol missing action: {action}")
    return protocol


def _clean_list(values: Any) -> list[str]:
    if not values:
        return []
    if not isinstance(values, list):
        raise ValueError("event list fields must be lists")
    return [str(value) for value in values if str(value)]
