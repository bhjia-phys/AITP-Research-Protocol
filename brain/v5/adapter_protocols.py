"""Shared runtime adapter protocol registry for AITP v5."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


_SUPPORTED_RUNTIMES = ("codex", "claude_code", "opencode")
_TRUST_CHANGING_ACTIONS = [
    "record_evidence",
    "record_tool_run",
    "change_claim_confidence",
    "validate_claim",
    "promote_to_l2",
]
_KERNEL_ENTRYPOINTS = [
    "aitp_v5_get_execution_brief",
    "aitp_v5_preflight_trust_update",
    "aitp_v5_apply_trust_update",
    "aitp_v5_record_evidence",
    "aitp_v5_record_tool_run",
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
}
_RUNTIME_RECORD_PROTOCOLS = {
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
        "accepted_link_fields": ["code_state_ids", "artifact_ids", "source_refs"],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
}
_RUNTIME_GATE_PROTOCOLS = {
    "validate_claim": {
        "preflight": "aitp_v5_preflight_trust_update",
        "sequence": [
            "refresh_execution_brief",
            "preflight_trust_update",
            "record_validation_evidence",
            "refresh_execution_brief",
            "write_session_summary",
        ],
        "required_typed_refs": ["topic_id", "claim_id", "evidence_refs"],
        "allowed_state_sources": ["typed_evidence_records", "typed_validation_records"],
        "human_checkpoint_required": False,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
    "promote_to_l2": {
        "preflight": "aitp_v5_preflight_trust_update",
        "sequence": [
            "refresh_execution_brief",
            "preflight_trust_update",
            "human_checkpoint",
            "promote_to_l2",
        ],
        "required_typed_refs": ["topic_id", "claim_id", "evidence_refs", "validation_result_ref"],
        "allowed_state_sources": ["typed_evidence_records", "typed_validation_records", "human_checkpoint"],
        "human_checkpoint_required": True,
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
    },
}


def supported_runtimes() -> tuple[str, ...]:
    """Return runtime ids supported by the public adapter packet."""

    return _SUPPORTED_RUNTIMES


def mandatory_kernel_entrypoints() -> set[str]:
    """Return kernel entrypoints every adapter packet must expose."""

    return set(_MANDATORY_KERNEL_ENTRYPOINTS)


def mandatory_trust_mutations() -> dict[str, Any]:
    """Return mandatory trust mutation entrypoint mappings."""

    return deepcopy(_TRUST_MUTATION_ENTRYPOINTS)


def mandatory_trust_update_protocol() -> dict[str, Any]:
    """Return mandatory trust-update runtime protocols."""

    return deepcopy(_RUNTIME_TRUST_UPDATE_PROTOCOL)


def mandatory_record_protocols() -> dict[str, Any]:
    """Return mandatory typed-record runtime protocols."""

    return deepcopy(_RUNTIME_RECORD_PROTOCOLS)


def mandatory_gate_protocols() -> dict[str, Any]:
    """Return mandatory validation and promotion runtime protocols."""

    return deepcopy(_RUNTIME_GATE_PROTOCOLS)


def build_adapter_protocols() -> dict[str, Any]:
    """Build the protocol fields shared by all runtime adapter packets."""

    return {
        "trust_changing_actions": deepcopy(_TRUST_CHANGING_ACTIONS),
        "requires_kernel_call_before": deepcopy(_TRUST_CHANGING_ACTIONS),
        "required_kernel_entrypoints": deepcopy(_KERNEL_ENTRYPOINTS),
        "trust_mutation_entrypoints": deepcopy(_TRUST_MUTATION_ENTRYPOINTS),
        "runtime_trust_update_protocol": deepcopy(_RUNTIME_TRUST_UPDATE_PROTOCOL),
        "runtime_record_protocols": deepcopy(_RUNTIME_RECORD_PROTOCOLS),
        "runtime_gate_protocols": deepcopy(_RUNTIME_GATE_PROTOCOLS),
    }
