# Compatibility shard 2 for adapter_contracts.
from __future__ import annotations

def _validate_runtime_gate_protocols(
    payload: Any,
    path: str,
    required_kernel_entrypoints: Any,
    result: ContractResult,
) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return

    entrypoints = set(required_kernel_entrypoints) if isinstance(required_kernel_entrypoints, list) else set()
    for action, expected_protocol in mandatory_gate_protocols().items():
        protocol = payload.get(action)
        _require_mapping(protocol, f"{path}.{action}", result)
        if not isinstance(protocol, dict):
            continue

        preflight = protocol.get("preflight")
        if preflight != expected_protocol["preflight"]:
            result.add(f"{path}.{action}.preflight", f"must be {expected_protocol['preflight']!r}")
        if isinstance(preflight, str) and preflight and entrypoints and preflight not in entrypoints:
            result.add(f"{path}.{action}.preflight", "must reference a declared required kernel entrypoint")
        pre_tool_policy = protocol.get("pre_tool_policy")
        if pre_tool_policy != expected_protocol["pre_tool_policy"]:
            result.add(f"{path}.{action}.pre_tool_policy", f"must be {expected_protocol['pre_tool_policy']!r}")
        if isinstance(pre_tool_policy, str) and entrypoints and pre_tool_policy not in entrypoints:
            result.add(f"{path}.{action}.pre_tool_policy", "must reference a declared required kernel entrypoint")
        if protocol.get("policy_reasons_field") != expected_protocol["policy_reasons_field"]:
            result.add(
                f"{path}.{action}.policy_reasons_field",
                f"must be {expected_protocol['policy_reasons_field']!r}",
            )

        for key in ("sequence", "required_typed_refs", "allowed_state_sources"):
            _require_list(protocol.get(key), f"{path}.{action}.{key}", result)
            if isinstance(protocol.get(key), list) and protocol[key] != expected_protocol[key]:
                result.add(f"{path}.{action}.{key}", f"must be {expected_protocol[key]!r}")

        _require_bool_value(
            protocol.get("human_checkpoint_required"),
            expected_protocol["human_checkpoint_required"],
            f"{path}.{action}.human_checkpoint_required",
            result,
        )
        if protocol.get("truth_source") != expected_protocol["truth_source"]:
            result.add(f"{path}.{action}.truth_source", "must be 'typed_records'")
        _require_bool_value(
            protocol.get("summary_inputs_trusted"),
            expected_protocol["summary_inputs_trusted"],
            f"{path}.{action}.summary_inputs_trusted",
            result,
        )

def _validate_runtime_recording_trigger_protocol(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    expected = mandatory_recording_trigger_protocol()
    if payload != expected:
        result.add(path, "must match mandatory_recording_trigger_protocol()")

    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    _require_bool_value(payload.get("can_update_claim_trust"), False, f"{path}.can_update_claim_trust", result)
    _require_list(payload.get("trigger_moments"), f"{path}.trigger_moments", result)
    _require_list(payload.get("minimal_sequence"), f"{path}.minimal_sequence", result)
    _require_mapping(payload.get("write_boundary"), f"{path}.write_boundary", result)
    boundary = payload.get("write_boundary")
    if isinstance(boundary, dict):
        if boundary.get("trust_apply_exposed_to_host") is not False:
            result.add(f"{path}.write_boundary.trust_apply_exposed_to_host", "must be false")

def _validate_trusted_focus(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("active_claim", "claim_statement", "confidence_state", "evidence_profile", "main_uncertainty"):
        if key not in payload:
            result.add(f"{path}.{key}", "missing trusted focus key")
    _require_level(payload.get("flow_profile"), f"{path}.flow_profile", result)
    _require_level(payload.get("risk_level"), f"{path}.risk_level", result)
