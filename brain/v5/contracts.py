"""Lightweight payload contracts for AITP v5 interfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from brain.v5.adapter_protocols import (
    adapter_protocol_fields,
    adapter_protocol_registry,
    mandatory_gate_protocols,
    mandatory_kernel_entrypoints,
    mandatory_record_protocols,
    mandatory_trust_mutations,
    mandatory_trust_update_protocol,
    supported_runtimes,
)


@dataclass
class ContractIssue:
    path: str
    message: str


@dataclass
class ContractResult:
    issues: list[ContractIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def add(self, path: str, message: str) -> None:
        self.issues.append(ContractIssue(path=path, message=message))

    def extend(self, other: "ContractResult") -> None:
        self.issues.extend(other.issues)


class ContractError(ValueError):
    """Raised when a v5 payload violates a required contract."""

    def __init__(self, result: ContractResult):
        self.result = result
        summary = "; ".join(f"{issue.path}: {issue.message}" for issue in result.issues)
        super().__init__(summary or "contract validation failed")


_BRIEF_REQUIRED_KEYS = (
    "session",
    "current_focus",
    "flow_profile",
    "risk_assessment",
    "action_budget",
    "known_context",
    "mandatory_reflection",
    "next_action_candidates",
    "forbidden_now",
    "human_checkpoint",
)
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
_SUMMARY_ORIENTATION_REQUIRED_KEYS = (
    "kind",
    "session_id",
    "summary_dir",
    "files",
    "truth_source",
    "orientation_only",
    "can_update_kernel_state",
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
    "truth_source",
    "summary_inputs_trusted",
)

_RISK_LEVELS = {"fluid", "guided", "rigorous", "adversarial"}
_MAX_QUESTIONS_BY_LEVEL = {
    "fluid": 1,
    "guided": 3,
    "rigorous": 3,
    "adversarial": 3,
}


def validate_execution_brief(payload: dict[str, Any], *, path: str = "brief") -> ContractResult:
    """Validate the public execution-brief payload."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    for key in _BRIEF_REQUIRED_KEYS:
        if key not in payload:
            result.add(key, "missing required execution brief key")

    if "session" in payload:
        _require_mapping(payload["session"], f"{path}.session", result)
        if isinstance(payload["session"], dict):
            _require_nonempty_str(payload["session"], "session_id", f"{path}.session", result)
            _require_nonempty_str(payload["session"], "topic_id", f"{path}.session", result)
            _require_nonempty_str(payload["session"], "context_id", f"{path}.session", result)

    if "flow_profile" in payload:
        _validate_flow_profile(payload["flow_profile"], f"{path}.flow_profile", result)

    if "risk_assessment" in payload:
        result.extend(validate_risk_assessment(payload["risk_assessment"], path=f"{path}.risk_assessment"))

    if "action_budget" in payload:
        result.extend(validate_action_budget(payload["action_budget"], path=f"{path}.action_budget"))

    if isinstance(payload.get("risk_assessment"), dict) and isinstance(payload.get("action_budget"), dict):
        risk_level = payload["risk_assessment"].get("level")
        budget_level = payload["action_budget"].get("level")
        if risk_level != budget_level:
            result.add(
                f"{path}.action_budget.level",
                f"must match risk_assessment.level ({risk_level!r}), got {budget_level!r}",
            )

    if "mandatory_reflection" in payload:
        _require_list(payload["mandatory_reflection"], f"{path}.mandatory_reflection", result)
        budget = payload.get("action_budget")
        if isinstance(budget, dict) and isinstance(payload["mandatory_reflection"], list):
            max_questions = budget.get("max_questions")
            if isinstance(max_questions, int) and len(payload["mandatory_reflection"]) > max_questions:
                result.add(
                    f"{path}.mandatory_reflection",
                    "contains more questions than action_budget.max_questions",
                )

    if "human_checkpoint" in payload:
        _require_mapping(payload["human_checkpoint"], f"{path}.human_checkpoint", result)
        if isinstance(payload["human_checkpoint"], dict) and not isinstance(payload["human_checkpoint"].get("needed"), bool):
            result.add(f"{path}.human_checkpoint.needed", "must be a boolean")

    for key in ("next_action_candidates", "forbidden_now"):
        if key in payload:
            _require_list(payload[key], f"{path}.{key}", result)

    return result


def require_valid_execution_brief(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a brief payload or raise a contract error."""

    result = validate_execution_brief(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


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

    if "adapter_protocol_registry" in payload:
        _validate_adapter_protocol_registry(
            payload["adapter_protocol_registry"],
            f"{path}.adapter_protocol_registry",
            result,
        )
    _validate_adapter_protocol_fields_present(payload, path, result)

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


def validate_summary_orientation(payload: dict[str, Any], *, path: str = "summary_orientation") -> ContractResult:
    """Validate a public orientation-only summary view."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    for key in _SUMMARY_ORIENTATION_REQUIRED_KEYS:
        if key not in payload:
            result.add(f"{path}.{key}", "missing required summary orientation key")

    if payload.get("kind") != "summary_orientation":
        result.add(f"{path}.kind", "must be 'summary_orientation'")
    _require_nonempty_str(payload, "session_id", path, result)
    _require_nonempty_str(payload, "summary_dir", path, result)
    _validate_summary_orientation(payload, path, result)

    files = payload.get("files")
    if isinstance(files, dict):
        for role, file_payload in files.items():
            _validate_summary_orientation_file(file_payload, f"{path}.files.{role}", result)

    return result


def require_valid_summary_orientation(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a summary orientation payload or raise a contract error."""

    result = validate_summary_orientation(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


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


def validate_risk_assessment(payload: dict[str, Any], *, path: str = "risk_assessment") -> ContractResult:
    """Validate a risk assessment payload."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    _require_level(payload.get("level"), f"{path}.level", result)
    if not isinstance(payload.get("score"), int):
        result.add(f"{path}.score", "must be an integer")
    if payload.get("score", 0) < 0:
        result.add(f"{path}.score", "must be non-negative")

    signals = payload.get("signals")
    _require_list(signals, f"{path}.signals", result)
    if isinstance(signals, list):
        for index, signal in enumerate(signals):
            _validate_risk_signal(signal, f"{path}.signals[{index}]", result)

    if "trust_reductions" in payload:
        _require_list(payload["trust_reductions"], f"{path}.trust_reductions", result)

    if "action_budget" in payload:
        result.extend(validate_action_budget(payload["action_budget"], path=f"{path}.action_budget"))
        if isinstance(payload["action_budget"], dict) and payload["action_budget"].get("level") != payload.get("level"):
            result.add(f"{path}.action_budget.level", "must match risk assessment level")

    if not isinstance(payload.get("human_checkpoint_needed"), bool):
        result.add(f"{path}.human_checkpoint_needed", "must be a boolean")
    _require_nonempty_str(payload, "summary", path, result)

    return result


def _validate_summary_orientation(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    _require_bool_value(payload.get("truth_source"), False, f"{path}.truth_source", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)
    _require_bool_value(payload.get("can_update_kernel_state"), False, f"{path}.can_update_kernel_state", result)
    if "files" in payload:
        _require_mapping(payload["files"], f"{path}.files", result)


def _validate_summary_orientation_file(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    _require_nonempty_str(payload, "path", path, result)
    if "frontmatter" in payload:
        _require_mapping(payload["frontmatter"], f"{path}.frontmatter", result)
    if "body" in payload and not isinstance(payload["body"], str):
        result.add(f"{path}.body", "must be a string")
    _require_bool_value(payload.get("truth_source"), False, f"{path}.truth_source", result)
    _require_bool_value(payload.get("orientation_only"), True, f"{path}.orientation_only", result)


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


def validate_action_budget(payload: dict[str, Any], *, path: str = "action_budget") -> ContractResult:
    """Validate an action-budget payload."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if result.issues:
        return result

    level = payload.get("level")
    _require_level(level, f"{path}.level", result)

    max_questions = payload.get("max_questions")
    if not isinstance(max_questions, int):
        result.add(f"{path}.max_questions", "must be an integer")
    elif isinstance(level, str) and level in _MAX_QUESTIONS_BY_LEVEL:
        allowed = _MAX_QUESTIONS_BY_LEVEL[level]
        if max_questions > allowed:
            result.add(f"{path}.max_questions", f"{level} budget max_questions must be <= {allowed}")
        if max_questions < 0:
            result.add(f"{path}.max_questions", "must be non-negative")

    for key in ("required_outputs", "allowed_actions"):
        _require_list(payload.get(key), f"{path}.{key}", result)
        if isinstance(payload.get(key), list) and any(not isinstance(item, str) or not item for item in payload[key]):
            result.add(f"{path}.{key}", "must contain non-empty strings")

    if not isinstance(payload.get("requires_human_checkpoint"), bool):
        result.add(f"{path}.requires_human_checkpoint", "must be a boolean")

    return result


def _validate_flow_profile(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    _require_level(payload.get("profile"), f"{path}.profile", result)
    _require_nonempty_str(payload, "reason", path, result)
    _require_list(payload.get("escalation_triggers"), f"{path}.escalation_triggers", result)
    risk_level = payload.get("risk_level")
    if risk_level:
        _require_level(risk_level, f"{path}.risk_level", result)


def _validate_risk_signal(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("kind", "reason", "evidence_ref", "suggested_action"):
        _require_nonempty_str(payload, key, path, result)
    severity = payload.get("severity")
    if not isinstance(severity, int):
        result.add(f"{path}.severity", "must be an integer")
    elif severity <= 0:
        result.add(f"{path}.severity", "must be positive")


def _validate_policy_reason(payload: Any, path: str, result: ContractResult) -> None:
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return
    for key in ("policy_id", "message", "severity"):
        _require_nonempty_str(payload, key, path, result)


def _require_mapping(value: Any, path: str, result: ContractResult) -> None:
    if not isinstance(value, dict):
        result.add(path, "must be a mapping")


def _require_list(value: Any, path: str, result: ContractResult) -> None:
    if not isinstance(value, list):
        result.add(path, "must be a list")


def _require_nonempty_str(payload: dict[str, Any], key: str, path: str, result: ContractResult) -> None:
    if not isinstance(payload.get(key), str) or not payload.get(key):
        result.add(f"{path}.{key}", "must be a non-empty string")


def _require_bool_value(value: Any, expected: bool, path: str, result: ContractResult) -> None:
    if value is not expected:
        result.add(path, f"must be {expected}")


def _require_level(value: Any, path: str, result: ContractResult) -> None:
    if value not in _RISK_LEVELS:
        result.add(path, f"must be one of {sorted(_RISK_LEVELS)}")
