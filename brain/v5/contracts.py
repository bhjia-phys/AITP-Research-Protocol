"""Lightweight payload contracts for AITP v5 interfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from brain.v5.runtime_entrypoints import runtime_entrypoints, validate_runtime_entrypoints

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
_RISK_LEVELS = {"fluid", "guided", "rigorous", "adversarial"}
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
    from brain.v5.adapter_contracts import validate_adapter_packet as _validate_adapter_packet
    return _validate_adapter_packet(payload, path=path)


def require_valid_adapter_packet(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.adapter_contracts import require_valid_adapter_packet as _require_valid_adapter_packet
    return _require_valid_adapter_packet(payload)


def validate_adapter_protocol_registry(payload: dict[str, Any], *, path: str = "adapter_protocol_registry") -> ContractResult:
    from brain.v5.adapter_contracts import validate_adapter_protocol_registry as _validate_adapter_protocol_registry
    return _validate_adapter_protocol_registry(payload, path=path)


def require_valid_adapter_protocol_registry(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.adapter_contracts import require_valid_adapter_protocol_registry as _require_valid_adapter_protocol_registry
    return _require_valid_adapter_protocol_registry(payload)


def validate_record_gate_coverage_audit(payload: dict[str, Any], *, path: str = "record_gate_coverage_audit") -> ContractResult:
    from brain.v5.record_gate_audit_contracts import validate_record_gate_coverage_audit as _validate
    return _validate(payload, path=path)

def require_valid_record_gate_coverage_audit(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_gate_audit_contracts import require_valid_record_gate_coverage_audit as _require
    return _require(payload)

def validate_codex_hook_bridge(payload: dict[str, Any], *, path: str = "codex_hook_bridge") -> ContractResult:
    from brain.v5.hook_protocol_contracts import validate_codex_hook_bridge as _validate_codex_hook_bridge
    return _validate_codex_hook_bridge(payload, path=path)


def require_valid_codex_hook_bridge(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.hook_protocol_contracts import require_valid_codex_hook_bridge as _require_valid_codex_hook_bridge
    return _require_valid_codex_hook_bridge(payload)


def validate_summary_orientation(payload: dict[str, Any], *, path: str = "summary_orientation") -> ContractResult:
    """Validate a public orientation-only summary view."""

    from brain.v5.summary_contracts import validate_summary_orientation as _validate_summary_orientation

    return _validate_summary_orientation(payload, path=path)


def require_valid_summary_orientation(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a summary orientation payload or raise a contract error."""

    from brain.v5.summary_contracts import require_valid_summary_orientation as _require_valid_summary_orientation

    return _require_valid_summary_orientation(payload)


def validate_session_summary_bundle(payload: dict[str, Any], *, path: str = "session_summary_bundle") -> ContractResult:
    """Validate a public session-summary write result."""

    from brain.v5.summary_contracts import validate_session_summary_bundle as _validate_session_summary_bundle

    return _validate_session_summary_bundle(payload, path=path)


def require_valid_session_summary_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a session-summary bundle payload or raise a contract error."""

    from brain.v5.summary_contracts import (
        require_valid_session_summary_bundle as _require_valid_session_summary_bundle,
    )

    return _require_valid_session_summary_bundle(payload)


def validate_trust_update_preflight(payload: dict[str, Any], *, path: str = "trust_preflight") -> ContractResult:
    """Validate a public trust-update preflight payload."""

    from brain.v5.trust_contracts import validate_trust_update_preflight as _validate_trust_update_preflight

    return _validate_trust_update_preflight(payload, path=path)


def require_valid_trust_update_preflight(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a trust-update preflight payload or raise a contract error."""

    from brain.v5.trust_contracts import require_valid_trust_update_preflight as _require_valid_trust_update_preflight

    return _require_valid_trust_update_preflight(payload)


def validate_trust_update_apply(payload: dict[str, Any], *, path: str = "trust_apply") -> ContractResult:
    """Validate a public trust-update apply payload."""

    from brain.v5.trust_contracts import validate_trust_update_apply as _validate_trust_update_apply

    return _validate_trust_update_apply(payload, path=path)


def require_valid_trust_update_apply(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a trust-update apply payload or raise a contract error."""

    from brain.v5.trust_contracts import require_valid_trust_update_apply as _require_valid_trust_update_apply

    return _require_valid_trust_update_apply(payload)


def validate_evidence_record(payload: dict[str, Any], *, path: str = "evidence_record") -> ContractResult:
    """Validate a public evidence-record write payload."""

    from brain.v5.record_contracts import validate_evidence_record as _validate_evidence_record

    return _validate_evidence_record(payload, path=path)


def require_valid_evidence_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return an evidence-record write payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_evidence_record as _require_valid_evidence_record

    return _require_valid_evidence_record(payload)


def validate_tool_run_record(payload: dict[str, Any], *, path: str = "tool_run_record") -> ContractResult:
    """Validate a public tool-run-record write payload."""

    from brain.v5.record_contracts import validate_tool_run_record as _validate_tool_run_record

    return _validate_tool_run_record(payload, path=path)


def require_valid_tool_run_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a tool-run-record write payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_tool_run_record as _require_valid_tool_run_record

    return _require_valid_tool_run_record(payload)


def validate_code_state_record(payload: dict[str, Any], *, path: str = "code_state_record") -> ContractResult:
    """Validate a public code-state-record write payload."""

    from brain.v5.record_contracts import validate_code_state_record as _validate_code_state_record

    return _validate_code_state_record(payload, path=path)


def require_valid_code_state_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a code-state-record write payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_code_state_record as _require_valid_code_state_record

    return _require_valid_code_state_record(payload)


def validate_tool_recipe_record(payload: dict[str, Any], *, path: str = "tool_recipe_record") -> ContractResult:
    """Validate a public tool-recipe-record write payload."""

    from brain.v5.record_contracts import validate_tool_recipe_record as _validate_tool_recipe_record

    return _validate_tool_recipe_record(payload, path=path)


def require_valid_tool_recipe_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a tool-recipe-record write payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_tool_recipe_record as _require_valid_tool_recipe_record

    return _require_valid_tool_recipe_record(payload)


def validate_reference_location_record(
    payload: dict[str, Any],
    *,
    path: str = "reference_location_record",
) -> ContractResult:
    """Validate a public reference-location-record write payload."""

    from brain.v5.record_contracts import validate_reference_location_record as _validate_reference_location_record

    return _validate_reference_location_record(payload, path=path)


def require_valid_reference_location_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a reference-location-record write payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_reference_location_record as _require_valid_reference_location_record

    return _require_valid_reference_location_record(payload)


def validate_physics_object_record(payload: dict[str, Any], *, path: str = "physics_object_record") -> ContractResult:
    """Validate a public physics-object-record write payload."""

    from brain.v5.record_contracts import validate_physics_object_record as _validate_physics_object_record

    return _validate_physics_object_record(payload, path=path)


def require_valid_physics_object_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a physics-object-record write payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_physics_object_record as _require_valid_physics_object_record

    return _require_valid_physics_object_record(payload)


def validate_object_relation_record(payload: dict[str, Any], *, path: str = "object_relation_record") -> ContractResult:
    """Validate a public object-relation-record write payload."""

    from brain.v5.record_contracts import validate_object_relation_record as _validate_object_relation_record

    return _validate_object_relation_record(payload, path=path)


def require_valid_object_relation_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return an object-relation-record write payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_object_relation_record as _require_valid_object_relation_record

    return _require_valid_object_relation_record(payload)


def validate_sensemaking_report_record(payload: dict[str, Any], *, path: str = "sensemaking_report_record") -> ContractResult:
    """Validate a public sensemaking-report-record write payload."""

    from brain.v5.record_contracts import validate_sensemaking_report_record as _validate_sensemaking_report_record

    return _validate_sensemaking_report_record(payload, path=path)


def require_valid_sensemaking_report_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a sensemaking-report-record write payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_sensemaking_report_record as _require_valid_sensemaking_report_record

    return _require_valid_sensemaking_report_record(payload)


def validate_validation_contract_record(payload: dict[str, Any], *, path: str = "validation_contract_record") -> ContractResult:
    """Validate a public validation-contract-record write payload."""

    from brain.v5.record_contracts import validate_validation_contract_record as _validate_validation_contract_record

    return _validate_validation_contract_record(payload, path=path)


def require_valid_validation_contract_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a validation-contract-record write payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_validation_contract_record as _require_valid_validation_contract_record

    return _require_valid_validation_contract_record(payload)


def validate_human_checkpoint_record(payload: dict[str, Any], *, path: str = "human_checkpoint_record") -> ContractResult:
    """Validate a public human-checkpoint-record write payload."""

    from brain.v5.record_contracts import validate_human_checkpoint_record as _validate_human_checkpoint_record

    return _validate_human_checkpoint_record(payload, path=path)


def require_valid_human_checkpoint_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a human-checkpoint-record write payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_human_checkpoint_record as _require_valid_human_checkpoint_record

    return _require_valid_human_checkpoint_record(payload)


def validate_promotion_packet_record(payload: dict[str, Any], *, path: str = "promotion_packet_record") -> ContractResult:
    from brain.v5.record_contracts import validate_promotion_packet_record as _validate
    return _validate(payload, path=path)


def require_valid_promotion_packet_record(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_contracts import require_valid_promotion_packet_record as _require
    return _require(payload)


def validate_memory_entry_record(payload: dict[str, Any], *, path: str = "memory_entry_record") -> ContractResult:
    from brain.v5.record_contracts import validate_memory_entry_record as _validate
    return _validate(payload, path=path)


def require_valid_memory_entry_record(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_contracts import require_valid_memory_entry_record as _require
    return _require(payload)


def validate_tool_executor_catalog(payload: dict[str, Any], *, path: str = "tool_executor_catalog") -> ContractResult:
    """Validate a public safe tool-executor catalog payload."""

    from brain.v5.tool_executor_contracts import validate_tool_executor_catalog as _validate_tool_executor_catalog

    return _validate_tool_executor_catalog(payload, path=path)


def require_valid_tool_executor_catalog(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a safe tool-executor catalog payload or raise a contract error."""

    from brain.v5.tool_executor_contracts import require_valid_tool_executor_catalog as _require_valid_tool_executor_catalog

    return _require_valid_tool_executor_catalog(payload)


def validate_knowledge_connector_catalog(
    payload: dict[str, Any],
    *,
    path: str = "knowledge_connector_catalog",
) -> ContractResult:
    """Validate a public knowledge-connector catalog payload."""

    from brain.v5.knowledge_connector_contracts import (
        validate_knowledge_connector_catalog as _validate_knowledge_connector_catalog,
    )

    return _validate_knowledge_connector_catalog(payload, path=path)


def require_valid_knowledge_connector_catalog(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a knowledge-connector catalog payload or raise a contract error."""

    from brain.v5.knowledge_connector_contracts import (
        require_valid_knowledge_connector_catalog as _require_valid_knowledge_connector_catalog,
    )

    return _require_valid_knowledge_connector_catalog(payload)


def validate_risk_assessment(payload: dict[str, Any], *, path: str = "risk_assessment") -> ContractResult:
    """Validate a risk assessment payload."""

    from brain.v5.risk_contracts import validate_risk_assessment as _validate_risk_assessment

    return _validate_risk_assessment(payload, path=path)


def validate_action_budget(payload: dict[str, Any], *, path: str = "action_budget") -> ContractResult:
    """Validate an action-budget payload."""

    from brain.v5.risk_contracts import validate_action_budget as _validate_action_budget

    return _validate_action_budget(payload, path=path)


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
