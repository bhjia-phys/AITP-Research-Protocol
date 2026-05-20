"""Trust-update contracts for AITP v5 trust-changing surfaces."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import (
    ContractError,
    ContractResult,
    _require_bool_value,
    _require_list,
    _require_mapping,
    _require_nonempty_str,
)


_TRUST_PREFLIGHT_REQUIRED_KEYS = (
    "kind",
    "request",
    "request_id",
    "action",
    "session_id",
    "topic_id",
    "claim_id",
    "allowed",
    "mutation_allowed_after_preflight",
    "policy_reasons",
    "required_actions",
    "evidence_refs",
    "code_state_ids",
    "preflight_token",
    "preflight_proof",
    "truth_source",
    "summary_inputs_trusted",
    "can_update_kernel_state",
)
_TRUST_APPLY_REQUIRED_KEYS = (
    "kind",
    "request",
    "request_id",
    "action",
    "session_id",
    "topic_id",
    "claim_id",
    "applied",
    "previous_state",
    "new_state",
    "required_actions",
    "preflight",
    "preflight_token",
    "truth_source",
    "summary_inputs_trusted",
)


def validate_trust_update_preflight(payload: dict[str, Any], *, path: str = "trust_preflight") -> ContractResult:
    """Validate a public trust-update preflight payload."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    for key in _TRUST_PREFLIGHT_REQUIRED_KEYS:
        if key not in payload:
            result.add(f"{path}.{key}", "missing required trust preflight key")

    if payload.get("kind") != "trust_update_preflight":
        result.add(f"{path}.kind", "must be 'trust_update_preflight'")

    for key in ("request_id", "action", "session_id", "topic_id", "claim_id"):
        _require_nonempty_str(payload, key, path, result)

    _require_mapping(payload.get("request"), f"{path}.request", result)
    for key in ("allowed", "mutation_allowed_after_preflight"):
        if not isinstance(payload.get(key), bool):
            result.add(f"{path}.{key}", "must be a boolean")
    if isinstance(payload.get("allowed"), bool) and isinstance(payload.get("mutation_allowed_after_preflight"), bool):
        if payload["mutation_allowed_after_preflight"] is not payload["allowed"]:
            result.add(f"{path}.mutation_allowed_after_preflight", "must match allowed")

    _require_list(payload.get("policy_reasons"), f"{path}.policy_reasons", result)
    if isinstance(payload.get("policy_reasons"), list):
        for index, reason in enumerate(payload["policy_reasons"]):
            _validate_policy_reason(reason, f"{path}.policy_reasons[{index}]", result)

    for key in ("required_actions", "evidence_refs", "code_state_ids"):
        _require_list(payload.get(key), f"{path}.{key}", result)
        if isinstance(payload.get(key), list) and any(not isinstance(item, str) or not item for item in payload[key]):
            result.add(f"{path}.{key}", "must contain non-empty strings")
    _require_nonempty_str(payload, "preflight_token", path, result)
    _validate_preflight_proof(payload.get("preflight_proof"), f"{path}.preflight_proof", result, payload)

    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)

    return result


def require_valid_trust_update_preflight(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a trust-update preflight payload or raise a contract error."""

    result = validate_trust_update_preflight(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_trust_update_apply(payload: dict[str, Any], *, path: str = "trust_apply") -> ContractResult:
    """Validate a public trust-update apply payload."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    for key in _TRUST_APPLY_REQUIRED_KEYS:
        if key not in payload:
            result.add(f"{path}.{key}", "missing required trust apply key")

    if payload.get("kind") != "trust_update_apply":
        result.add(f"{path}.kind", "must be 'trust_update_apply'")
    for key in ("request_id", "action", "session_id", "topic_id", "claim_id", "previous_state", "new_state"):
        _require_nonempty_str(payload, key, path, result)

    _require_mapping(payload.get("request"), f"{path}.request", result)
    if not isinstance(payload.get("applied"), bool):
        result.add(f"{path}.applied", "must be a boolean")
    if "preflight_token" in payload and not isinstance(payload.get("preflight_token"), str):
        result.add(f"{path}.preflight_token", "must be a string")

    _require_list(payload.get("required_actions"), f"{path}.required_actions", result)
    if isinstance(payload.get("required_actions"), list):
        if any(not isinstance(item, str) or not item for item in payload["required_actions"]):
            result.add(f"{path}.required_actions", "must contain non-empty strings")
        if payload.get("applied") is True and payload["required_actions"]:
            result.add(f"{path}.required_actions", "must be empty when applied is true")

    preflight = payload.get("preflight")
    if isinstance(preflight, dict):
        result.extend(validate_trust_update_preflight(preflight, path=f"{path}.preflight"))
        if payload.get("applied") is True and preflight.get("allowed") is not True:
            result.add(f"{path}.preflight.allowed", "must be true when applied is true")
        if payload.get("applied") is True:
            token = payload.get("preflight_token")
            if not token:
                result.add(f"{path}.preflight_token", "must be present when applied is true")
            if token and token != preflight.get("preflight_token"):
                result.add(f"{path}.preflight_token", "must match preflight.preflight_token when applied is true")
    else:
        _require_mapping(preflight, f"{path}.preflight", result)

    if payload.get("truth_source") != "typed_records":
        result.add(f"{path}.truth_source", "must be 'typed_records'")
    _require_bool_value(payload.get("summary_inputs_trusted"), False, f"{path}.summary_inputs_trusted", result)

    return result


def require_valid_trust_update_apply(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a trust-update apply payload or raise a contract error."""

    result = validate_trust_update_apply(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_policy_reason(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("policy_id", "message", "severity"):
        _require_nonempty_str(payload, key, path, result)


def _validate_preflight_proof(
    proof: Any,
    path: str,
    result: ContractResult,
    parent_payload: dict[str, Any],
) -> None:
    _require_mapping(proof, path, result)
    if not isinstance(proof, dict):
        return
    for key in ("token", "request_id", "request_digest", "policy_digest", "source"):
        _require_nonempty_str(proof, key, path, result)
    if proof.get("token") != parent_payload.get("preflight_token"):
        result.add(f"{path}.token", "must match preflight_token")
    if proof.get("request_id") != parent_payload.get("request_id"):
        result.add(f"{path}.request_id", "must match request_id")
    if proof.get("source") != "trust_update_preflight":
        result.add(f"{path}.source", "must be 'trust_update_preflight'")
