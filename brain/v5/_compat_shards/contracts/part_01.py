# Compatibility shard 1 for contracts.
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

def validate_claim_relation_map(payload: dict[str, Any], *, path: str = "claim_relation_map") -> ContractResult:
    from brain.v5.claim_relation_map_contracts import validate_claim_relation_map as _validate
    return _validate(payload, path=path)

def require_valid_claim_relation_map(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.claim_relation_map_contracts import require_valid_claim_relation_map as _require
    return _require(payload)

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

def validate_runtime_mcp_bridge_acceptance(
    payload: dict[str, Any],
    *,
    path: str = "runtime_mcp_bridge_acceptance",
) -> ContractResult:
    from brain.v5.runtime_mcp_bridge_acceptance_contracts import (
        validate_runtime_mcp_bridge_acceptance as _validate,
    )
    return _validate(payload, path=path)

def require_valid_runtime_mcp_bridge_acceptance(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.runtime_mcp_bridge_acceptance_contracts import (
        require_valid_runtime_mcp_bridge_acceptance as _require,
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

def validate_literature_extraction_report(
    payload: dict[str, Any],
    *,
    path: str = "literature_extraction_report",
) -> ContractResult:
    from brain.v5.literature_extraction_report_contracts import (
        validate_literature_extraction_report as _validate,
    )
    return _validate(payload, path=path)

def require_valid_literature_extraction_report(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.literature_extraction_report_contracts import (
        require_valid_literature_extraction_report as _require,
    )
    return _require(payload)

def validate_literature_corpus_extraction_artifact(
    payload: dict[str, Any],
    *,
    path: str = "literature_corpus_extraction_artifact",
) -> ContractResult:
    from brain.v5.literature_corpus_extraction_artifact_contracts import (
        validate_literature_corpus_extraction_artifact as _validate,
    )
    return _validate(payload, path=path)

def require_valid_literature_corpus_extraction_artifact(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.literature_corpus_extraction_artifact_contracts import (
        require_valid_literature_corpus_extraction_artifact as _require,
    )
    return _require(payload)

def validate_literature_source_extraction_candidates(
    payload: dict[str, Any],
    *,
    path: str = "literature_source_extraction_candidates",
) -> ContractResult:
    from brain.v5.literature_source_extraction_contracts import (
        validate_literature_source_extraction_candidates as _validate,
    )
    return _validate(payload, path=path)

def require_valid_literature_source_extraction_candidates(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.literature_source_extraction_contracts import (
        require_valid_literature_source_extraction_candidates as _require,
    )
    return _require(payload)

def validate_literature_reading_route(
    payload: dict[str, Any],
    *,
    path: str = "literature_reading_route",
) -> ContractResult:
    from brain.v5.literature_reading_route_contracts import (
        validate_literature_reading_route as _validate,
    )
    return _validate(payload, path=path)

def require_valid_literature_reading_route(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.literature_reading_route_contracts import (
        require_valid_literature_reading_route as _require,
    )
    return _require(payload)

def validate_context_profile_template_catalog(
    payload: dict[str, Any],
    *,
    path: str = "context_profile_template_catalog",
) -> ContractResult:
    from brain.v5.context_profile_template_contracts import (
        validate_context_profile_template_catalog as _validate,
    )
    return _validate(payload, path=path)

def require_valid_context_profile_template_catalog(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.context_profile_template_contracts import (
        require_valid_context_profile_template_catalog as _require,
    )
    return _require(payload)

def validate_context_profile_draft(
    payload: dict[str, Any],
    *,
    path: str = "context_profile_draft",
) -> ContractResult:
    from brain.v5.context_profile_draft_contracts import (
        validate_context_profile_draft as _validate,
    )
    return _validate(payload, path=path)

def require_valid_context_profile_draft(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.context_profile_draft_contracts import (
        require_valid_context_profile_draft as _require,
    )
    return _require(payload)

def validate_literature_source_set_readiness(
    payload: dict[str, Any],
    *,
    path: str = "literature_source_set_readiness",
) -> ContractResult:
    from brain.v5.literature_source_set_readiness_contracts import (
        validate_literature_source_set_readiness as _validate,
    )
    return _validate(payload, path=path)

def require_valid_literature_source_set_readiness(payload: dict[str, Any]) -> dict[str, Any]:
    from brain.v5.literature_source_set_readiness_contracts import (
        require_valid_literature_source_set_readiness as _require,
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

def validate_lifecycle_event_record(payload: dict[str, Any], *, path: str = "lifecycle_event_record") -> ContractResult:
    """Validate a public lifecycle-event-record payload."""

    from brain.v5.record_contracts import validate_lifecycle_event_record as _validate_lifecycle_event_record

    return _validate_lifecycle_event_record(payload, path=path)

def require_valid_lifecycle_event_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a lifecycle-event-record payload or raise a contract error."""

    from brain.v5.record_contracts import require_valid_lifecycle_event_record as _require_valid_lifecycle_event_record

    return _require_valid_lifecycle_event_record(payload)

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
