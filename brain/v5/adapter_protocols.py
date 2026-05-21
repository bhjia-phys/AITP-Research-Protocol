"""Shared runtime adapter protocol registry for AITP v5."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from brain.v5.gate_protocols import mandatory_gate_protocols
from brain.v5.public_surfaces import public_surface_names, public_surface_validator_ref


_FINGERPRINT_ALGORITHM = "sha256-canonical-json-v1"
_SUPPORTED_RUNTIMES = ("codex", "claude_code", "opencode")
_PROTOCOL_FIELDS = [
    "trust_changing_actions",
    "requires_kernel_call_before",
    "required_kernel_entrypoints",
    "trust_mutation_entrypoints",
    "runtime_trust_update_protocol",
    "runtime_record_protocols",
    "runtime_gate_protocols",
    "runtime_hook_protocols",
]
_REGISTRY_METADATA = {
    "kind": "adapter_protocol_registry",
    "source_module": "brain.v5.adapter_protocols",
    "protocol_version": 1,
    "summary_inputs_trusted": False,
}
_TRUST_CHANGING_ACTIONS = [
    "record_code_state",
    "record_evidence",
    "record_tool_run",
    "execute_tool",
    "register_tool_recipe",
    "record_reference_location",
    "record_physics_object",
    "record_object_relation",
    "record_sensemaking_report",
    "ingest_subagent_result",
    "create_validation_contract",
    "request_human_checkpoint",
    "decide_human_checkpoint",
    "create_promotion_packet",
    "apply_promotion_packet",
    "change_claim_confidence",
    "validate_claim",
    "promote_to_l2",
]
_KERNEL_ENTRYPOINTS = [
    "aitp_v5_get_execution_brief",
    "aitp_v5_evaluate_pre_tool_policy",
    "aitp_v5_preflight_trust_update",
    "aitp_v5_apply_trust_update",
    "aitp_v5_record_code_state",
    "aitp_v5_record_evidence",
    "aitp_v5_record_tool_run",
    "aitp_v5_execute_tool",
    "aitp_v5_register_tool_recipe",
    "aitp_v5_record_reference_location",
    "aitp_v5_record_physics_object",
    "aitp_v5_record_object_relation",
    "aitp_v5_record_sensemaking_report",
    "aitp_v5_ingest_subagent_result",
    "aitp_v5_create_validation_contract",
    "aitp_v5_request_human_checkpoint",
    "aitp_v5_decide_human_checkpoint",
    "aitp_v5_create_promotion_packet",
    "aitp_v5_apply_promotion_packet",
    "aitp_v5_assess_risk",
    "aitp_v5_write_session_summary",
]
_MANDATORY_KERNEL_ENTRYPOINTS = {
    "aitp_v5_get_execution_brief",
    "aitp_v5_preflight_trust_update",
    "aitp_v5_apply_trust_update",
}
_TRUST_MUTATION_ENTRYPOINTS = {
    "change_claim_confidence": {
        "preflight": "aitp_v5_preflight_trust_update",
        "apply": "aitp_v5_apply_trust_update",
    },
}
_TRUST_UPDATE_SEQUENCE = [
    "refresh_execution_brief",
    "preflight_trust_update",
    "apply_trust_update",
    "refresh_execution_brief",
    "write_session_summary",
]
_RUNTIME_TRUST_UPDATE_PROTOCOL = {
    "change_claim_confidence": {
        "sequence": list(_TRUST_UPDATE_SEQUENCE),
        "preflight": "aitp_v5_preflight_trust_update",
        "apply": "aitp_v5_apply_trust_update",
        "refresh": ["aitp_v5_get_execution_brief", "aitp_v5_write_session_summary"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
}
_RECORD_SEQUENCE_BY_ACTION = {
    "record_code_state": [
        "refresh_execution_brief",
        "record_code_state",
        "refresh_execution_brief",
        "write_session_summary",
    ],
    "record_evidence": [
        "refresh_execution_brief",
        "record_evidence",
        "refresh_execution_brief",
        "write_session_summary",
    ],
    "record_tool_run": [
        "refresh_execution_brief",
        "record_tool_run",
        "refresh_execution_brief",
        "write_session_summary",
    ],
    "execute_tool": [
        "refresh_execution_brief",
        "execute_tool",
        "refresh_execution_brief",
        "write_session_summary",
    ],
    "register_tool_recipe": [
        "register_tool_recipe",
    ],
    "record_reference_location": [
        "refresh_execution_brief",
        "record_reference_location",
        "refresh_execution_brief",
        "write_session_summary",
    ],
    "record_physics_object": [
        "refresh_execution_brief",
        "record_physics_object",
        "refresh_execution_brief",
        "write_session_summary",
    ],
    "record_object_relation": [
        "refresh_execution_brief",
        "record_object_relation",
        "refresh_execution_brief",
        "write_session_summary",
    ],
    "record_sensemaking_report": [
        "refresh_execution_brief",
        "record_sensemaking_report",
        "refresh_execution_brief",
        "write_session_summary",
    ],
    "ingest_subagent_result": [
        "refresh_execution_brief",
        "ingest_subagent_result",
        "refresh_execution_brief",
        "write_session_summary",
    ],
    "create_validation_contract": [
        "refresh_execution_brief",
        "create_validation_contract",
        "refresh_execution_brief",
        "write_session_summary",
    ],
    "request_human_checkpoint": [
        "refresh_execution_brief",
        "request_human_checkpoint",
        "refresh_execution_brief",
        "write_session_summary",
    ],
    "decide_human_checkpoint": [
        "refresh_execution_brief",
        "decide_human_checkpoint",
        "refresh_execution_brief",
        "write_session_summary",
    ],
    "create_promotion_packet": [
        "refresh_execution_brief",
        "create_promotion_packet",
        "refresh_execution_brief",
        "write_session_summary",
    ],
    "apply_promotion_packet": [
        "refresh_execution_brief",
        "apply_promotion_packet",
        "refresh_execution_brief",
        "write_session_summary",
    ],
}
_RUNTIME_RECORD_PROTOCOLS = {
    "record_code_state": {
        "entrypoint": "aitp_v5_record_code_state",
        "sequence": list(_RECORD_SEQUENCE_BY_ACTION["record_code_state"]),
        "required_typed_refs": ["repo_id", "upstream_commit", "local_branch"],
        "accepted_link_fields": ["linked_records"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
    "record_evidence": {
        "entrypoint": "aitp_v5_record_evidence",
        "sequence": list(_RECORD_SEQUENCE_BY_ACTION["record_evidence"]),
        "required_typed_refs": ["topic_id", "claim_id"],
        "accepted_link_fields": ["source_refs", "tool_run_ids", "artifact_ids"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
    "record_tool_run": {
        "entrypoint": "aitp_v5_record_tool_run",
        "sequence": list(_RECORD_SEQUENCE_BY_ACTION["record_tool_run"]),
        "required_typed_refs": ["topic_id", "claim_id", "recipe_id"],
        "accepted_link_fields": ["code_state_ids", "validation_contract_ids", "artifact_ids", "source_refs"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
    "execute_tool": {
        "entrypoint": "aitp_v5_execute_tool",
        "sequence": list(_RECORD_SEQUENCE_BY_ACTION["execute_tool"]),
        "required_typed_refs": ["topic_id", "claim_id", "recipe_id", "executor_id"],
        "accepted_link_fields": ["code_state_ids", "validation_contract_ids", "artifact_ids", "source_refs"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
    "register_tool_recipe": {
        "entrypoint": "aitp_v5_register_tool_recipe",
        "sequence": list(_RECORD_SEQUENCE_BY_ACTION["register_tool_recipe"]),
        "required_typed_refs": ["recipe_id", "tool_family", "tool_name"],
        "accepted_link_fields": ["required_inputs", "expected_outputs", "invariants"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
    "record_reference_location": {
        "entrypoint": "aitp_v5_record_reference_location",
        "sequence": list(_RECORD_SEQUENCE_BY_ACTION["record_reference_location"]),
        "required_typed_refs": ["topic_id", "connector_id", "uri"],
        "accepted_link_fields": ["claim_id", "source_ref", "external_id", "linked_records"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
    "record_physics_object": {
        "entrypoint": "aitp_v5_record_physics_object",
        "sequence": list(_RECORD_SEQUENCE_BY_ACTION["record_physics_object"]),
        "required_typed_refs": ["topic_id", "object_type", "name", "definition"],
        "accepted_link_fields": ["source_refs", "linked_records"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
    "record_object_relation": {
        "entrypoint": "aitp_v5_record_object_relation",
        "sequence": list(_RECORD_SEQUENCE_BY_ACTION["record_object_relation"]),
        "required_typed_refs": ["topic_id", "relation_type", "subject_id", "object_id", "statement"],
        "accepted_link_fields": ["claim_id", "source_refs", "evidence_refs"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
    "record_sensemaking_report": {
        "entrypoint": "aitp_v5_record_sensemaking_report",
        "sequence": list(_RECORD_SEQUENCE_BY_ACTION["record_sensemaking_report"]),
        "required_typed_refs": ["topic_id", "claim_id", "title", "summary"],
        "accepted_link_fields": ["object_ids", "relation_ids", "evidence_refs"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
    "ingest_subagent_result": {
        "entrypoint": "aitp_v5_ingest_subagent_result",
        "sequence": list(_RECORD_SEQUENCE_BY_ACTION["ingest_subagent_result"]),
        "required_typed_refs": ["topic_id", "claim_id", "packet_id"],
        "accepted_link_fields": ["evidence_refs", "code_state_refs", "proposed_next_actions"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
    "create_validation_contract": {
        "entrypoint": "aitp_v5_create_validation_contract",
        "sequence": list(_RECORD_SEQUENCE_BY_ACTION["create_validation_contract"]),
        "required_typed_refs": ["topic_id", "claim_id", "required_checks", "failure_modes"],
        "accepted_link_fields": ["required_evidence_outputs", "validator_role"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
    "request_human_checkpoint": {
        "entrypoint": "aitp_v5_request_human_checkpoint",
        "sequence": list(_RECORD_SEQUENCE_BY_ACTION["request_human_checkpoint"]),
        "required_typed_refs": ["topic_id", "claim_id", "reason", "requested_by"],
        "accepted_link_fields": ["options", "decision", "decided_by"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
    "decide_human_checkpoint": {
        "entrypoint": "aitp_v5_decide_human_checkpoint",
        "sequence": list(_RECORD_SEQUENCE_BY_ACTION["decide_human_checkpoint"]),
        "required_typed_refs": ["checkpoint_id", "decision", "rationale", "decided_by"],
        "accepted_link_fields": [],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
    "create_promotion_packet": {
        "entrypoint": "aitp_v5_create_promotion_packet",
        "sequence": list(_RECORD_SEQUENCE_BY_ACTION["create_promotion_packet"]),
        "required_typed_refs": ["topic_id", "claim_id", "proposed_memory_kind", "scope"],
        "accepted_link_fields": ["evidence_refs", "non_claims", "known_failure_modes"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
    "apply_promotion_packet": {
        "entrypoint": "aitp_v5_apply_promotion_packet",
        "sequence": list(_RECORD_SEQUENCE_BY_ACTION["apply_promotion_packet"]),
        "required_typed_refs": ["packet_id", "checkpoint_id"],
        "accepted_link_fields": ["source_claim_id", "source_topic_id", "evidence_refs"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
}
_RUNTIME_HOOK_PROTOCOLS = {
    "pre_commit": {
        "lifecycle_event": "pre_commit",
        "command": ["python", "hooks/aitp_v5_hook.py", "pre-commit"],
        "required_inputs": ["changed_files", "test_refs", "evolution_note"],
        "output_kind": "hook_decision",
        "may_block": True,
        "block_exit_code": 2,
        "state_mutation": "none",
        "summary_inputs_trusted": False,
    },
    "pre_tool": {
        "lifecycle_event": "pre_tool",
        "command": ["python", "hooks/aitp_v5_hook.py", "pre-tool"],
        "required_inputs": ["action", "risk_level", "policy_json"],
        "output_kind": "hook_decision",
        "may_block": True,
        "block_exit_code": 2,
        "state_mutation": "none",
        "summary_inputs_trusted": False,
    },
    "post_tool": {
        "lifecycle_event": "post_tool",
        "command": ["python", "hooks/aitp_v5_hook.py", "post-tool"],
        "required_inputs": ["session_id", "topic_id", "claim_id", "risk_level", "tool_name", "evidence_status"],
        "output_kind": "hook_trace_event",
        "may_block": False,
        "block_exit_code": 0,
        "state_mutation": "trace_event_output_only",
        "summary_inputs_trusted": False,
    },
}


def supported_runtimes() -> tuple[str, ...]:
    """Return runtime ids supported by the public adapter packet."""

    return _SUPPORTED_RUNTIMES


def mandatory_kernel_entrypoints() -> set[str]:
    """Return kernel entrypoints every adapter packet must expose."""

    return set(_MANDATORY_KERNEL_ENTRYPOINTS)


def adapter_protocol_fields() -> tuple[str, ...]:
    """Return protocol field names governed by the adapter protocol registry."""

    return tuple(_PROTOCOL_FIELDS)


def adapter_protocol_fingerprint() -> str:
    """Return a stable fingerprint for the registry-governed protocol payload."""

    return adapter_protocol_payload_fingerprint(_build_protocol_payload())


def adapter_protocol_payload_fingerprint(protocol_payload: dict[str, Any]) -> str:
    """Return a stable fingerprint for a registry-governed protocol payload."""

    canonical_payload = json.dumps(
        protocol_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def adapter_protocol_registry() -> dict[str, Any]:
    """Return metadata describing the shared protocol registry."""

    return {
        **deepcopy(_REGISTRY_METADATA),
        "protocol_fields": list(adapter_protocol_fields()),
        "protocol_fingerprint_inputs": list(adapter_protocol_fields()),
        "protocol_fingerprint": adapter_protocol_fingerprint(),
        "protocol_fingerprint_algorithm": _FINGERPRINT_ALGORITHM,
        "public_surface_contracts": list(public_surface_names()),
        "public_surface_validator": public_surface_validator_ref(),
    }


def mandatory_trust_mutations() -> dict[str, Any]:
    """Return mandatory trust mutation entrypoint mappings."""

    return deepcopy(_TRUST_MUTATION_ENTRYPOINTS)


def mandatory_trust_update_protocol() -> dict[str, Any]:
    """Return mandatory trust-update runtime protocols."""

    return deepcopy(_RUNTIME_TRUST_UPDATE_PROTOCOL)


def mandatory_record_protocols() -> dict[str, Any]:
    """Return mandatory typed-record runtime protocols."""

    return deepcopy(_RUNTIME_RECORD_PROTOCOLS)


def record_gate_coverage_audit() -> dict[str, Any]:
    """Return an audit showing whether typed record protocols have gate coverage."""

    record_actions = set(_RUNTIME_RECORD_PROTOCOLS)
    gate_actions = set(mandatory_gate_protocols())
    return {
        "kind": "record_gate_coverage_audit",
        "record_protocols": sorted(record_actions),
        "gate_protocols": sorted(gate_actions),
        "gated_record_protocols": sorted(record_actions & gate_actions),
        "ungated_record_protocols": sorted(record_actions - gate_actions),
        "extra_gate_protocols": sorted(gate_actions - record_actions),
        "truth_source": "adapter_protocol_registry",
        "summary_inputs_trusted": False,
    }


def mandatory_hook_protocols() -> dict[str, Any]:
    """Return mandatory lifecycle hook protocols for runtime adapters."""

    return deepcopy(_RUNTIME_HOOK_PROTOCOLS)


def build_adapter_protocols() -> dict[str, Any]:
    """Build the protocol fields shared by all runtime adapter packets."""

    return {
        "adapter_protocol_registry": adapter_protocol_registry(),
        **_build_protocol_payload(),
    }


def _build_protocol_payload() -> dict[str, Any]:
    return {
        "trust_changing_actions": deepcopy(_TRUST_CHANGING_ACTIONS),
        "requires_kernel_call_before": deepcopy(_TRUST_CHANGING_ACTIONS),
        "required_kernel_entrypoints": deepcopy(_KERNEL_ENTRYPOINTS),
        "trust_mutation_entrypoints": deepcopy(_TRUST_MUTATION_ENTRYPOINTS),
        "runtime_trust_update_protocol": deepcopy(_RUNTIME_TRUST_UPDATE_PROTOCOL),
        "runtime_record_protocols": deepcopy(_RUNTIME_RECORD_PROTOCOLS),
        "runtime_gate_protocols": mandatory_gate_protocols(),
        "runtime_hook_protocols": deepcopy(_RUNTIME_HOOK_PROTOCOLS),
    }
