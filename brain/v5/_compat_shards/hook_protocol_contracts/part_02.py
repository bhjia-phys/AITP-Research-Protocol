# Compatibility shard 2 for hook_protocol_contracts.
from __future__ import annotations

def _validate_gate_protocols(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("source_protocol_field") != "runtime_gate_protocols":
        result.add(f"{path}.source_protocol_field", "must be 'runtime_gate_protocols'")
    for action, expected in mandatory_gate_protocols().items():
        protocol = payload.get(action)
        _require_mapping(protocol, f"{path}.{action}", result)
        if isinstance(protocol, dict) and protocol != expected:
            result.add(f"{path}.{action}", "must match mandatory runtime gate protocol")

def _validate_policy_reason(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("policy_id", "severity", "message"):
        _require_nonempty_str(payload, key, path, result)

def _validate_trace_event_payload(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    if payload.get("kind") != "trace_event":
        result.add(f"{path}.kind", "must be 'trace_event'")
    for key in ("event_id", "session_id", "topic_id", "event_type", "risk_level"):
        _require_nonempty_str(payload, key, path, result)
    _require_mapping(payload.get("payload"), f"{path}.payload", result)
