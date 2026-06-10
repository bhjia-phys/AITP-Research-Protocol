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


_RISK_LEVELS = {"fluid", "guided", "rigorous", "adversarial"}
def validate_execution_brief(payload: dict[str, Any], *, path: str = "brief") -> ContractResult:
    """Validate the public execution-brief payload."""

    from brain.v5.brief_contracts import validate_execution_brief as _validate_execution_brief
    return _validate_execution_brief(payload, path=path)


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


def validate_runtime_bridge_target_manifest(
    payload: dict[str, Any],
    *,
    path: str = "runtime_bridge_target_manifest",
) -> ContractResult:
    from brain.v5.runtime_bridge_target_contracts import (
        validate_runtime_bridge_target_manifest as _validate,
    )
    return _validate(payload, path=path)


def require_valid_runtime_bridge_target_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.runtime_bridge_target_contracts import (
        require_valid_runtime_bridge_target_manifest as _require,
    )
    return _require(payload)


def validate_record_ref_lookup(
    payload: dict[str, Any],
    *,
    path: str = "record_ref_lookup",
) -> ContractResult:
    from brain.v5.record_ref_contracts import validate_record_ref_lookup as _validate
    return _validate(payload, path=path)


def require_valid_record_ref_lookup(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_ref_contracts import require_valid_record_ref_lookup as _require
    return _require(payload)


def validate_curated_rag_corpus(
    payload: dict[str, Any],
    *,
    path: str = "curated_rag_corpus",
) -> ContractResult:
    from brain.v5.curated_rag_contracts import validate_curated_rag_corpus as _validate
    return _validate(payload, path=path)


def require_valid_curated_rag_corpus(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.curated_rag_contracts import require_valid_curated_rag_corpus as _require
    return _require(payload)


def validate_curated_rag_search_result(
    payload: dict[str, Any],
    *,
    path: str = "curated_rag_search_result",
) -> ContractResult:
    from brain.v5.curated_rag_contracts import validate_curated_rag_search_result as _validate
    return _validate(payload, path=path)


def require_valid_curated_rag_search_result(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.curated_rag_contracts import require_valid_curated_rag_search_result as _require
    return _require(payload)


def validate_curated_rag_ingest_result(
    payload: dict[str, Any],
    *,
    path: str = "curated_rag_ingest_result",
) -> ContractResult:
    from brain.v5.curated_rag_contracts import validate_curated_rag_ingest_result as _validate
    return _validate(payload, path=path)


def require_valid_curated_rag_ingest_result(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.curated_rag_contracts import require_valid_curated_rag_ingest_result as _require
    return _require(payload)


def validate_curated_rag_promotion_draft(
    payload: dict[str, Any],
    *,
    path: str = "curated_rag_promotion_draft",
) -> ContractResult:
    from brain.v5.curated_rag_contracts import validate_curated_rag_promotion_draft as _validate
    return _validate(payload, path=path)


def require_valid_curated_rag_promotion_draft(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.curated_rag_contracts import require_valid_curated_rag_promotion_draft as _require
    return _require(payload)


def validate_literature_comparison_draft(
    payload: dict[str, Any],
    *,
    path: str = "literature_comparison_draft",
) -> ContractResult:
    from brain.v5.literature_comparison_draft_contracts import (
        validate_literature_comparison_draft as _validate,
    )
    return _validate(payload, path=path)


def require_valid_literature_comparison_draft(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.literature_comparison_draft_contracts import (
        require_valid_literature_comparison_draft as _require,
    )
    return _require(payload)


def validate_record_gate_coverage_audit(payload: dict[str, Any], *, path: str = "record_gate_coverage_audit") -> ContractResult:
    from brain.v5.record_gate_audit_contracts import validate_record_gate_coverage_audit as _validate
    return _validate(payload, path=path)

def require_valid_record_gate_coverage_audit(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_gate_audit_contracts import require_valid_record_gate_coverage_audit as _require
    return _require(payload)

def validate_runtime_hook_installation_audit(payload: dict[str, Any], *, path: str = "runtime_hook_installation_audit") -> ContractResult:
    from brain.v5.hook_install_contracts import validate_runtime_hook_installation_audit as _validate
    return _validate(payload, path=path)

def require_valid_runtime_hook_installation_audit(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.hook_install_contracts import require_valid_runtime_hook_installation_audit as _require
    return _require(payload)

def validate_runtime_hook_installation_paths(payload: dict[str, Any], *, path: str = "runtime_hook_installation_paths") -> ContractResult:
    from brain.v5.hook_install_contracts import validate_runtime_hook_installation_paths as _validate
    return _validate(payload, path=path)

def require_valid_runtime_hook_installation_paths(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.hook_install_contracts import require_valid_runtime_hook_installation_paths as _require
    return _require(payload)

def validate_runtime_hook_smoke_coverage(payload: dict[str, Any], *, path: str = "runtime_hook_smoke_coverage") -> ContractResult:
    from brain.v5.hook_install_contracts import validate_runtime_hook_smoke_coverage as _validate
    return _validate(payload, path=path)

def require_valid_runtime_hook_smoke_coverage(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.hook_install_contracts import require_valid_runtime_hook_smoke_coverage as _require
    return _require(payload)

def validate_codex_hook_bridge(payload: dict[str, Any], *, path: str = "codex_hook_bridge") -> ContractResult:
    from brain.v5.hook_protocol_contracts import validate_codex_hook_bridge as _validate_codex_hook_bridge
    return _validate_codex_hook_bridge(payload, path=path)


def require_valid_codex_hook_bridge(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.hook_protocol_contracts import require_valid_codex_hook_bridge as _require_valid_codex_hook_bridge
    return _require_valid_codex_hook_bridge(payload)


def validate_summary_orientation(payload: dict[str, Any], *, path: str = "summary_orientation") -> ContractResult:
    from brain.v5.summary_contracts import validate_summary_orientation as _validate; return _validate(payload, path=path)


def require_valid_summary_orientation(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.summary_contracts import require_valid_summary_orientation as _require; return _require(payload)


def validate_session_summary_bundle(payload: dict[str, Any], *, path: str = "session_summary_bundle") -> ContractResult:
    from brain.v5.summary_contracts import validate_session_summary_bundle as _validate; return _validate(payload, path=path)


def require_valid_session_summary_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.summary_contracts import require_valid_session_summary_bundle as _require; return _require(payload)


def validate_workspace_summary_bundle(payload: dict[str, Any], *, path: str = "workspace_summary_bundle") -> ContractResult:
    from brain.v5.summary_contracts import validate_workspace_summary_bundle as _validate; return _validate(payload, path=path)


def require_valid_workspace_summary_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.summary_contracts import require_valid_workspace_summary_bundle as _require; return _require(payload)

def validate_workspace_replay_packet(payload: dict[str, Any], *, path: str = "workspace_replay_packet") -> ContractResult:
    from brain.v5.replay_contracts import validate_workspace_replay_packet as _validate; return _validate(payload, path=path)

def require_valid_workspace_replay_packet(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.replay_contracts import require_valid_workspace_replay_packet as _require; return _require(payload)

def validate_source_reconstruction_audit(payload: dict[str, Any], *, path: str = "source_reconstruction_audit") -> ContractResult:
    from brain.v5.source_reconstruction_contracts import validate_source_reconstruction_audit as _validate; return _validate(payload, path=path)

def require_valid_source_reconstruction_audit(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.source_reconstruction_contracts import require_valid_source_reconstruction_audit as _require; return _require(payload)


def validate_process_graph_slice(payload: dict[str, Any], *, path: str = "process_graph_slice") -> ContractResult:
    from brain.v5.process_graph_contracts import validate_process_graph_slice as _validate
    return _validate(payload, path=path)


def require_valid_process_graph_slice(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.process_graph_contracts import require_valid_process_graph_slice as _require
    return _require(payload)


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


def validate_trust_update_record(payload: dict[str, Any], *, path: str = "trust_update_record") -> ContractResult:
    from brain.v5.record_contracts import validate_trust_update_record as _validate
    return _validate(payload, path=path)


def require_valid_trust_update_record(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_contracts import require_valid_trust_update_record as _require
    return _require(payload)


def validate_claim_trust_audit(payload: dict[str, Any], *, path: str = "claim_trust_audit") -> ContractResult:
    from brain.v5.trust_audit_contracts import validate_claim_trust_audit as _validate
    return _validate(payload, path=path)


def require_valid_claim_trust_audit(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.trust_audit_contracts import require_valid_claim_trust_audit as _require
    return _require(payload)


def validate_artifact_record(payload: dict[str, Any], *, path: str = "artifact_record") -> ContractResult:
    from brain.v5.record_contracts import validate_artifact_record as _validate
    return _validate(payload, path=path)


def require_valid_artifact_record(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.record_contracts import require_valid_artifact_record as _require
    return _require(payload)


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
