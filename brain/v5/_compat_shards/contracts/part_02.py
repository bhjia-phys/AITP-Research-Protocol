# Compatibility shard 2 for contracts.
from __future__ import annotations

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

def validate_claim_status_record(payload: dict[str, Any], *, path: str = "claim_status_record") -> ContractResult:
    from brain.v5.record_contracts import validate_claim_status_record as _validate
    return _validate(payload, path=path)

def require_valid_claim_status_record(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_contracts import require_valid_claim_status_record as _require
    return _require(payload)

def validate_proof_obligation_record(payload: dict[str, Any], *, path: str = "proof_obligation_record") -> ContractResult:
    from brain.v5.record_contracts import validate_proof_obligation_record as _validate
    return _validate(payload, path=path)

def require_valid_proof_obligation_record(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_contracts import require_valid_proof_obligation_record as _require
    return _require(payload)

def validate_authority_record(payload: dict[str, Any], *, path: str = "authority_record") -> ContractResult:
    from brain.v5.record_contracts import validate_authority_record as _validate
    return _validate(payload, path=path)

def require_valid_authority_record(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_contracts import require_valid_authority_record as _require
    return _require(payload)

def validate_authority_registry(payload: dict[str, Any], *, path: str = "authority_registry") -> ContractResult:
    from brain.v5.record_contracts import validate_authority_registry as _validate
    return _validate(payload, path=path)

def require_valid_authority_registry(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_contracts import require_valid_authority_registry as _require
    return _require(payload)

def validate_note_outline(payload: dict[str, Any], *, path: str = "note_outline") -> ContractResult:
    from brain.v5.note_outline_contracts import validate_note_outline as _validate
    return _validate(payload, path=path)

def require_valid_note_outline(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.note_outline_contracts import require_valid_note_outline as _require
    return _require(payload)

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

def validate_source_asset_record(payload: dict[str, Any], *, path: str = "source_asset_record") -> ContractResult:
    """Validate a public source-asset-record write payload."""

    from brain.v5.record_contracts import validate_source_asset_record as _validate

    return _validate(payload, path=path)

def require_valid_source_asset_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a source-asset-record write payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_source_asset_record as _require

    return _require(payload)

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

def validate_exploratory_record(payload: dict[str, Any], *, path: str = "exploratory_record") -> ContractResult:
    """Validate a public exploratory-record write payload."""

    from brain.v5.record_contracts import validate_exploratory_record as _validate

    return _validate(payload, path=path)

def require_valid_exploratory_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return an exploratory-record write payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_exploratory_record as _require

    return _require(payload)

def validate_research_route_record(payload: dict[str, Any], *, path: str = "research_route_record") -> ContractResult:
    """Validate a public research-route-record write payload."""

    from brain.v5.record_contracts import validate_research_route_record as _validate

    return _validate(payload, path=path)

def require_valid_research_route_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a research-route-record write payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_research_route_record as _require

    return _require(payload)

def validate_research_run_record(payload: dict[str, Any], *, path: str = "research_run_record") -> ContractResult:
    """Validate a public research-run-record write payload."""

    from brain.v5.record_contracts import validate_research_run_record as _validate

    return _validate(payload, path=path)

def require_valid_research_run_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a research-run-record write payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_research_run_record as _require

    return _require(payload)

def validate_research_run_event_record(
    payload: dict[str, Any],
    *,
    path: str = "research_run_event_record",
) -> ContractResult:
    """Validate a public research-run-event-record write payload."""

    from brain.v5.record_contracts import validate_research_run_event_record as _validate

    return _validate(payload, path=path)

def require_valid_research_run_event_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a research-run-event-record write payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_research_run_event_record as _require

    return _require(payload)

def validate_validation_contract_record(payload: dict[str, Any], *, path: str = "validation_contract_record") -> ContractResult:
    from brain.v5.record_contracts import validate_validation_contract_record as _validate_validation_contract_record
    return _validate_validation_contract_record(payload, path=path)

def require_valid_validation_contract_record(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_contracts import require_valid_validation_contract_record as _require_valid_validation_contract_record
    return _require_valid_validation_contract_record(payload)

def validate_validation_result_record(payload: dict[str, Any], *, path: str = "validation_result_record") -> ContractResult:
    from brain.v5.record_contracts import validate_validation_result_record as _validate_validation_result_record
    return _validate_validation_result_record(payload, path=path)

def require_valid_validation_result_record(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_contracts import require_valid_validation_result_record as _require_valid_validation_result_record
    return _require_valid_validation_result_record(payload)

def validate_human_checkpoint_record(payload: dict[str, Any], *, path: str = "human_checkpoint_record") -> ContractResult:
    from brain.v5.record_contracts import validate_human_checkpoint_record as _validate_human_checkpoint_record

    return _validate_human_checkpoint_record(payload, path=path)

def require_valid_human_checkpoint_record(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_contracts import require_valid_human_checkpoint_record as _require_valid_human_checkpoint_record

    return _require_valid_human_checkpoint_record(payload)

def validate_failure_mode_review_result_record(payload: dict[str, Any], *, path: str = "failure_mode_review_result_record") -> ContractResult:
    from brain.v5.record_contracts import validate_failure_mode_review_result_record as _validate; return _validate(payload, path=path)

def require_valid_failure_mode_review_result_record(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_contracts import require_valid_failure_mode_review_result_record as _require; return _require(payload)

def validate_final_engineering_readiness_audit(payload: dict[str, Any], *, path: str = "final_engineering_readiness_audit") -> ContractResult:
    from brain.v5.final_readiness_contracts import validate_final_engineering_readiness_audit as _validate; return _validate(payload, path=path)

def require_valid_final_engineering_readiness_audit(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.final_readiness_contracts import require_valid_final_engineering_readiness_audit as _require; return _require(payload)

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

def validate_l2_memory_audit(payload: dict[str, Any], *, path: str = "l2_memory_audit") -> ContractResult:
    from brain.v5.memory_audit_contracts import validate_l2_memory_audit as _validate; return _validate(payload, path=path)

def require_valid_l2_memory_audit(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.memory_audit_contracts import require_valid_l2_memory_audit as _require; return _require(payload)

def validate_failure_mode_audit(payload: dict[str, Any], *, path: str = "failure_mode_audit") -> ContractResult:
    from brain.v5.failure_mode_audit_contracts import validate_failure_mode_audit as _validate; return _validate(payload, path=path)

def require_valid_failure_mode_audit(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.failure_mode_audit_contracts import require_valid_failure_mode_audit as _require; return _require(payload)

def validate_failure_mode_review_packet(payload: dict[str, Any], *, path: str = "failure_mode_review_packet") -> ContractResult:
    from brain.v5.failure_mode_review_contracts import validate_failure_mode_review_packet as _validate; return _validate(payload, path=path)

def require_valid_failure_mode_review_packet(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.failure_mode_review_contracts import require_valid_failure_mode_review_packet as _require; return _require(payload)

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

def validate_knowledge_connector_binding_registry(
    payload: dict[str, Any],
    *,
    path: str = "knowledge_connector_binding_registry",
) -> ContractResult:
    """Validate a public knowledge-connector binding registry payload."""

    from brain.v5.knowledge_connector_binding_contracts import (
        validate_knowledge_connector_binding_registry as _validate,
    )

    return _validate(payload, path=path)

def require_valid_knowledge_connector_binding_registry(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a knowledge-connector binding registry payload or raise a contract error."""

    from brain.v5.knowledge_connector_binding_contracts import (
        require_valid_knowledge_connector_binding_registry as _require,
    )

    return _require(payload)

def validate_domain_pack_catalog(
    payload: dict[str, Any],
    *,
    path: str = "domain_pack_catalog",
) -> ContractResult:
    """Validate a public domain-pack catalog payload."""

    from brain.v5.domain_pack_contracts import validate_domain_pack_catalog as _validate_domain_pack_catalog

    return _validate_domain_pack_catalog(payload, path=path)

def require_valid_domain_pack_catalog(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a domain-pack catalog payload or raise a contract error."""

    from brain.v5.domain_pack_contracts import require_valid_domain_pack_catalog as _require_valid_domain_pack_catalog

    return _require_valid_domain_pack_catalog(payload)

def validate_domain_skill_shim_manifest(
    payload: dict[str, Any],
    *,
    path: str = "domain_skill_shim_manifest",
) -> ContractResult:
    """Validate a project-scope domain-skill shim manifest."""

    from brain.v5.domain_skill_shim_contracts import validate_domain_skill_shim_manifest as _validate

    return _validate(payload, path=path)

def require_valid_domain_skill_shim_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a domain-skill shim manifest or raise a contract error."""

    from brain.v5.domain_skill_shim_contracts import require_valid_domain_skill_shim_manifest as _require

    return _require(payload)

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
