"""Adapter-packet contracts for AITP v5 runtime surfaces."""

from __future__ import annotations

from typing import Any

from brain.v5.adapter_protocols import (
    adapter_protocol_fields,
    adapter_protocol_payload_fingerprint,
    adapter_protocol_registry,
    mandatory_gate_protocols,
    mandatory_kernel_entrypoints,
    mandatory_record_protocols,
    mandatory_trust_mutations,
    mandatory_trust_update_protocol,
    supported_runtimes,
)
from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_bool_value,
    _require_level,
    _require_list,
    _require_mapping,
    _require_nonempty_str,
    _validate_summary_orientation,
    validate_execution_brief,
)
from brain.v5.public_surfaces import describe_public_surfaces


_ADAPTER_REQUIRED_KEYS = (
    "kind",
    "runtime",
    "session_id",
    "topic_id",
    "truth_sources",
    "orientation_surfaces",
    "summary_orientation",
    "execution_brief",
    "trusted_focus",
    "adapter_contract",
    "public_surface_audit",
    "runtime_entrypoints",
    "adapter_protocol_registry",
    "trust_changing_actions",
    "requires_kernel_call_before",
    "required_kernel_entrypoints",
    "trust_mutation_entrypoints",
    "runtime_trust_update_protocol",
    "runtime_record_protocols",
    "runtime_gate_protocols",
    "runtime_rules",
)


def validate_adapter_packet(payload: dict[str, Any], *, path: str = "adapter") -> ContractResult:
    """Validate the public runtime adapter packet."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    for key in _ADAPTER_REQUIRED_KEYS:
        if key not in payload:
            result.add(f"{path}.{key}", "missing required adapter packet key")

    if payload.get("kind") != "adapter_packet":
        result.add(f"{path}.kind", "must be 'adapter_packet'")

    if payload.get("runtime") not in supported_runtimes():
        result.add(f"{path}.runtime", f"must be one of {sorted(supported_runtimes())}")

    for key in ("session_id", "topic_id"):
        _require_nonempty_str(payload, key, path, result)

    if "truth_sources" in payload:
        _require_list(payload["truth_sources"], f"{path}.truth_sources", result)
        if isinstance(payload["truth_sources"], list):
            required_sources = {"typed_records", "execution_brief"}
            if set(payload["truth_sources"]) != required_sources:
                result.add(
                    f"{path}.truth_sources",
                    "must be exactly ['typed_records', 'execution_brief']",
                )

    if "summary_orientation" in payload:
        _validate_summary_orientation(payload["summary_orientation"], f"{path}.summary_orientation", result)

    if "adapter_contract" in payload:
        _validate_adapter_contract(payload["adapter_contract"], f"{path}.adapter_contract", result)

    if "public_surface_audit" in payload:
        _validate_public_surface_audit(payload["public_surface_audit"], f"{path}.public_surface_audit", result)

    if "runtime_entrypoints" in payload:
        _validate_runtime_entrypoints(payload["runtime_entrypoints"], f"{path}.runtime_entrypoints", result)

    if "adapter_protocol_registry" in payload:
        _validate_adapter_protocol_registry(
            payload["adapter_protocol_registry"],
            f"{path}.adapter_protocol_registry",
            result,
        )
    _validate_adapter_protocol_fields_present(payload, path, result)
    _validate_adapter_protocol_fingerprint(payload, f"{path}.adapter_protocol_registry", result)

    if "execution_brief" in payload:
        result.extend(validate_execution_brief(payload["execution_brief"], path=f"{path}.execution_brief"))

    if "trusted_focus" in payload:
        _validate_trusted_focus(payload["trusted_focus"], f"{path}.trusted_focus", result)

    for key in ("trust_changing_actions", "requires_kernel_call_before", "required_kernel_entrypoints", "runtime_rules"):
        if key in payload:
            _require_list(payload[key], f"{path}.{key}", result)
            if isinstance(payload[key], list) and any(not isinstance(item, str) or not item for item in payload[key]):
                result.add(f"{path}.{key}", "must contain non-empty strings")

    if isinstance(payload.get("required_kernel_entrypoints"), list):
        missing = sorted(mandatory_kernel_entrypoints() - set(payload["required_kernel_entrypoints"]))
        if missing:
            result.add(
                f"{path}.required_kernel_entrypoints",
                f"missing mandatory kernel entrypoints: {missing}",
            )

    if "trust_mutation_entrypoints" in payload:
        _validate_trust_mutation_entrypoints(
            payload["trust_mutation_entrypoints"],
            f"{path}.trust_mutation_entrypoints",
            payload.get("required_kernel_entrypoints"),
            result,
        )

    if "runtime_trust_update_protocol" in payload:
        _validate_runtime_trust_update_protocol(
            payload["runtime_trust_update_protocol"],
            f"{path}.runtime_trust_update_protocol",
            payload.get("required_kernel_entrypoints"),
            result,
        )

    if "runtime_record_protocols" in payload:
        _validate_runtime_record_protocols(
            payload["runtime_record_protocols"],
            f"{path}.runtime_record_protocols",
            payload.get("required_kernel_entrypoints"),
            result,
        )

    if "runtime_gate_protocols" in payload:
        _validate_runtime_gate_protocols(
            payload["runtime_gate_protocols"],
            f"{path}.runtime_gate_protocols",
            payload.get("required_kernel_entrypoints"),
            result,
        )

    if isinstance(payload.get("trust_changing_actions"), list) and isinstance(
        payload.get("requires_kernel_call_before"),
        list,
    ):
        if set(payload["trust_changing_actions"]) != set(payload["requires_kernel_call_before"]):
            result.add(
                f"{path}.requires_kernel_call_before",
                "must match trust_changing_actions",
            )

    return result


def require_valid_adapter_packet(payload: dict[str, Any]) -> dict[str, Any]:
    """Return an adapter packet or raise a contract error."""

    result = validate_adapter_packet(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_adapter_protocol_registry(
    payload: dict[str, Any],
    *,
    path: str = "adapter_protocol_registry",
) -> ContractResult:
    """Validate the public adapter protocol registry payload."""

    result = ContractResult()
    _validate_adapter_protocol_registry(payload, path, result)
    return result


def require_valid_adapter_protocol_registry(payload: dict[str, Any]) -> dict[str, Any]:
    """Return an adapter protocol registry payload or raise a contract error."""

    result = validate_adapter_protocol_registry(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_adapter_contract(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    _require_bool_value(
        payload.get("summary_files_are_truth_source"),
        False,
        f"{path}.summary_files_are_truth_source",
        result,
    )
    _require_bool_value(
        payload.get("summary_files_can_update_kernel_state"),
        False,
        f"{path}.summary_files_can_update_kernel_state",
        result,
    )
    _require_bool_value(
        payload.get("kernel_must_be_called_before_trust_updates"),
        True,
        f"{path}.kernel_must_be_called_before_trust_updates",
        result,
    )
    if payload.get("regenerated_from") != "kernel_state":
        result.add(f"{path}.regenerated_from", "must be 'kernel_state'")


def _validate_public_surface_audit(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return

    if payload != describe_public_surfaces():
        result.add(path, "must match describe_public_surfaces()")


def _validate_runtime_entrypoints(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return

    from brain.v5 import contracts

    if payload != contracts.runtime_entrypoints():
        result.add(path, "must match runtime_entrypoints()")
    for error in contracts.validate_runtime_entrypoints(payload):
        error_path = error.split(":", 1)[0]
        result.add(f"{path}.{error_path}", error)


def _validate_adapter_protocol_registry(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return

    for key, expected_value in adapter_protocol_registry().items():
        if payload.get(key) != expected_value:
            result.add(f"{path}.{key}", f"must be {expected_value!r}")


def _validate_adapter_protocol_fields_present(
    payload: dict[str, Any],
    path: str,
    result: ContractResult,
) -> None:
    for field_name in adapter_protocol_fields():
        if field_name not in payload:
            result.add(
                f"{path}.adapter_protocol_registry.protocol_fields.{field_name}",
                "declared protocol field missing from adapter packet",
            )


def _validate_adapter_protocol_fingerprint(
    payload: dict[str, Any],
    path: str,
    result: ContractResult,
) -> None:
    registry = payload.get("adapter_protocol_registry")
    if not isinstance(registry, dict):
        return
    if any(field_name not in payload for field_name in adapter_protocol_fields()):
        return

    protocol_payload = {field_name: payload[field_name] for field_name in adapter_protocol_fields()}
    actual_fingerprint = adapter_protocol_payload_fingerprint(protocol_payload)
    if registry.get("protocol_fingerprint") != actual_fingerprint:
        result.add(path + ".protocol_fingerprint", "must match the adapter packet protocol payload")


def _validate_trust_mutation_entrypoints(
    payload: Any,
    path: str,
    required_kernel_entrypoints: Any,
    result: ContractResult,
) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return

    entrypoints = set(required_kernel_entrypoints) if isinstance(required_kernel_entrypoints, list) else set()
    for action, required_steps in mandatory_trust_mutations().items():
        action_payload = payload.get(action)
        _require_mapping(action_payload, f"{path}.{action}", result)
        if not isinstance(action_payload, dict):
            continue
        for step, expected_entrypoint in required_steps.items():
            actual_entrypoint = action_payload.get(step)
            if actual_entrypoint != expected_entrypoint:
                result.add(
                    f"{path}.{action}.{step}",
                    f"must be {expected_entrypoint!r}",
                )
            if isinstance(actual_entrypoint, str) and entrypoints and actual_entrypoint not in entrypoints:
                result.add(
                    f"{path}.{action}.{step}",
                    "must reference a declared required kernel entrypoint",
                )


def _validate_runtime_trust_update_protocol(
    payload: Any,
    path: str,
    required_kernel_entrypoints: Any,
    result: ContractResult,
) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return

    entrypoints = set(required_kernel_entrypoints) if isinstance(required_kernel_entrypoints, list) else set()
    for action, expected_protocol in mandatory_trust_update_protocol().items():
        protocol = payload.get(action)
        _require_mapping(protocol, f"{path}.{action}", result)
        if not isinstance(protocol, dict):
            continue

        sequence = protocol.get("sequence")
        _require_list(sequence, f"{path}.{action}.sequence", result)
        if isinstance(sequence, list) and sequence != expected_protocol["sequence"]:
            result.add(f"{path}.{action}.sequence", "must follow refresh->preflight->apply->refresh sequence")

        refresh = protocol.get("refresh")
        _require_list(refresh, f"{path}.{action}.refresh", result)
        if isinstance(refresh, list) and refresh != expected_protocol["refresh"]:
            result.add(f"{path}.{action}.refresh", "must name execution brief and summary refresh entrypoints")

        for key in ("preflight", "apply"):
            expected_entrypoint = expected_protocol[key]
            actual_entrypoint = protocol.get(key)
            if actual_entrypoint != expected_entrypoint:
                result.add(f"{path}.{action}.{key}", f"must be {expected_entrypoint!r}")
            if isinstance(actual_entrypoint, str) and entrypoints and actual_entrypoint not in entrypoints:
                result.add(f"{path}.{action}.{key}", "must reference a declared required kernel entrypoint")

        if isinstance(refresh, list) and entrypoints:
            for index, entrypoint in enumerate(refresh):
                if entrypoint not in entrypoints:
                    result.add(
                        f"{path}.{action}.refresh[{index}]",
                        "must reference a declared required kernel entrypoint",
                    )

        if protocol.get("truth_source") != expected_protocol["truth_source"]:
            result.add(f"{path}.{action}.truth_source", "must be 'typed_records'")
        _require_bool_value(
            protocol.get("summary_inputs_trusted"),
            expected_protocol["summary_inputs_trusted"],
            f"{path}.{action}.summary_inputs_trusted",
            result,
        )


def _validate_runtime_record_protocols(
    payload: Any,
    path: str,
    required_kernel_entrypoints: Any,
    result: ContractResult,
) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return

    entrypoints = set(required_kernel_entrypoints) if isinstance(required_kernel_entrypoints, list) else set()
    for action, expected_protocol in mandatory_record_protocols().items():
        protocol = payload.get(action)
        _require_mapping(protocol, f"{path}.{action}", result)
        if not isinstance(protocol, dict):
            continue

        entrypoint = protocol.get("entrypoint")
        if entrypoint != expected_protocol["entrypoint"]:
            result.add(f"{path}.{action}.entrypoint", f"must be {expected_protocol['entrypoint']!r}")
        if isinstance(entrypoint, str) and entrypoints and entrypoint not in entrypoints:
            result.add(f"{path}.{action}.entrypoint", "must reference a declared required kernel entrypoint")

        for key in ("sequence", "required_typed_refs", "accepted_link_fields"):
            _require_list(protocol.get(key), f"{path}.{action}.{key}", result)
            if isinstance(protocol.get(key), list) and protocol[key] != expected_protocol[key]:
                result.add(f"{path}.{action}.{key}", f"must be {expected_protocol[key]!r}")

        if protocol.get("truth_source") != expected_protocol["truth_source"]:
            result.add(f"{path}.{action}.truth_source", "must be 'typed_records'")
        _require_bool_value(
            protocol.get("summary_inputs_trusted"),
            expected_protocol["summary_inputs_trusted"],
            f"{path}.{action}.summary_inputs_trusted",
            result,
        )


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
        if isinstance(preflight, str) and entrypoints and preflight not in entrypoints:
            result.add(f"{path}.{action}.preflight", "must reference a declared required kernel entrypoint")

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


def _validate_trusted_focus(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("active_claim", "claim_statement", "confidence_state", "evidence_profile", "main_uncertainty"):
        if key not in payload:
            result.add(f"{path}.{key}", "missing trusted focus key")
    _require_level(payload.get("flow_profile"), f"{path}.flow_profile", result)
    _require_level(payload.get("risk_level"), f"{path}.risk_level", result)
