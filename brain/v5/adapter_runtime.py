"""Runtime helpers that consume generated AITP v5 adapter bridge payloads."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from brain.v5.pretool_policy import evaluate_context_pre_tool_policy


_AITP_TOOL_ACTIONS = {
    "aitp_v5_record_code_state": "record_code_state",
    "aitp_v5_record_evidence": "record_evidence",
    "aitp_v5_record_tool_run": "record_tool_run",
    "aitp_v5_execute_tool": "execute_tool",
    "aitp_v5_register_tool_recipe": "register_tool_recipe",
    "aitp_v5_record_reference_location": "record_reference_location",
    "aitp_v5_record_physics_object": "record_physics_object",
    "aitp_v5_record_object_relation": "record_object_relation",
    "aitp_v5_record_sensemaking_report": "record_sensemaking_report",
    "aitp_v5_ingest_subagent_result": "ingest_subagent_result",
    "aitp_v5_create_validation_contract": "create_validation_contract",
    "aitp_v5_request_human_checkpoint": "request_human_checkpoint",
    "aitp_v5_decide_human_checkpoint": "decide_human_checkpoint",
    "aitp_v5_create_promotion_packet": "create_promotion_packet",
    "aitp_v5_apply_promotion_packet": "apply_promotion_packet",
}


def evaluate_platform_pre_tool_event(
    ws,
    bridge_payload: dict[str, Any],
    platform_event: dict[str, Any],
) -> dict[str, Any]:
    """Normalize Codex/OpenCode-style pre-tool events through the bridge policy path."""

    event = _platform_pre_tool_event(bridge_payload, platform_event)
    payload = evaluate_bridge_lifecycle_event(ws, bridge_payload, event)
    payload["runtime_event"].update(
        {
            "runtime": event["runtime"],
            "platform_event": event["platform_event"],
            "tool_name": event["tool_name"],
        }
    )
    return payload


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
        validation_contract_ids=_clean_list(event.get("validation_contract_ids")),
        source_kind=str(event.get("source_kind", "typed_records")),
        source_ref=str(event.get("source_ref", "")),
        orientation_only=bool(event.get("orientation_only", False)),
        risk_level=str(event.get("risk_level", "guided")),
        human_checkpoint_id=str(event.get("human_checkpoint_id", "")),
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
    validation_contract_ids: list[str] | None = None,
    source_kind: str = "typed_records",
    source_ref: str = "",
    orientation_only: bool = False,
    risk_level: str = "guided",
    human_checkpoint_id: str = "",
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
        validation_contract_ids=validation_contract_ids,
        source_kind=source_kind,
        source_ref=source_ref,
        orientation_only=orientation_only,
        risk_level=risk_level,
        human_checkpoint_id=human_checkpoint_id,
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


def _platform_pre_tool_event(bridge_payload: dict[str, Any], platform_event: dict[str, Any]) -> dict[str, Any]:
    runtime = _bridge_runtime(bridge_payload)
    if str(platform_event.get("runtime", runtime)).strip().lower() != runtime:
        raise ValueError("platform event runtime does not match bridge payload")
    if runtime == "codex":
        if str(platform_event.get("hook_name") or platform_event.get("lifecycle_event")) != "pre_tool":
            raise ValueError("Codex platform event must be a pre_tool event")
        tool_name = str(platform_event.get("tool_name") or "")
        tool_input = platform_event.get("tool_input") if isinstance(platform_event.get("tool_input"), dict) else {}
    elif runtime == "opencode":
        if str(platform_event.get("lifecycle_event") or platform_event.get("hook_name")) != "pre_tool":
            raise ValueError("OpenCode platform event must be a pre_tool event")
        tool = platform_event.get("tool") if isinstance(platform_event.get("tool"), dict) else {}
        tool_name = str(tool.get("name") or platform_event.get("tool_name") or "")
        raw_input = tool.get("input") if isinstance(tool.get("input"), dict) else platform_event.get("tool_input")
        tool_input = raw_input if isinstance(raw_input, dict) else {}
    else:
        raise ValueError("unsupported bridge payload kind")
    action = str(platform_event.get("action") or tool_input.get("action") or _action_from_tool_name(tool_name))
    if not action:
        raise ValueError("platform pre_tool event must provide or imply an AITP action")
    return {
        "runtime": runtime,
        "platform_event": f"{runtime}_pre_tool",
        "lifecycle_event": "pre_tool",
        "session_id": str(platform_event.get("session_id") or tool_input.get("session_id") or ""),
        "action": action,
        "claim_id": _claim_id_from_tool_input(tool_input),
        "evidence_refs": _input_list(tool_input, "evidence_refs"),
        "code_state_ids": _input_list(tool_input, "code_state_ids"),
        "validation_contract_ids": _input_list(tool_input, "validation_contract_ids"),
        "source_kind": str(tool_input.get("source_kind") or platform_event.get("source_kind") or "typed_records"),
        "source_ref": str(tool_input.get("source_ref") or platform_event.get("source_ref") or ""),
        "orientation_only": bool(tool_input.get("orientation_only") is True or platform_event.get("orientation_only") is True),
        "risk_level": str(platform_event.get("risk_level") or tool_input.get("risk_level") or "guided"),
        "human_checkpoint_id": str(
            tool_input.get("human_checkpoint_id")
            or tool_input.get("human_checkpoint")
            or tool_input.get("checkpoint_id")
            or platform_event.get("human_checkpoint_id")
            or platform_event.get("human_checkpoint")
            or platform_event.get("checkpoint_id")
            or ""
        ),
        "tool_name": tool_name,
    }


def _bridge_runtime(bridge_payload: dict[str, Any]) -> str:
    if bridge_payload.get("kind") == "codex_hook_bridge":
        return "codex"
    if bridge_payload.get("kind") == "opencode_plugin_bridge":
        return "opencode"
    raise ValueError("unsupported bridge payload kind")


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


def _action_from_tool_name(tool_name: str) -> str:
    lowered = tool_name.lower()
    for entrypoint, action in _AITP_TOOL_ACTIONS.items():
        if entrypoint in lowered:
            return action
    return ""


def _input_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    singular = payload.get(key.removesuffix("s"))
    if singular:
        return [str(singular)]
    return []


def _claim_id_from_tool_input(tool_input: dict[str, Any]) -> str:
    if tool_input.get("claim_id") or tool_input.get("claim"):
        return str(tool_input.get("claim_id") or tool_input.get("claim"))
    packet = tool_input.get("packet")
    if isinstance(packet, dict) and packet.get("claim_id"):
        return str(packet["claim_id"])
    return ""


def _clean_list(values: Any) -> list[str]:
    if not values:
        return []
    if not isinstance(values, list):
        raise ValueError("event list fields must be lists")
    return [str(value) for value in values if str(value)]
