"""Runtime adapter packets for AITP v5 agents."""

from __future__ import annotations

from typing import Any

from brain.v5.brief import build_execution_brief
from brain.v5.contracts import require_valid_adapter_packet, require_valid_execution_brief
from brain.v5.paths import WorkspacePaths
from brain.v5.summaries import read_summary_orientation, write_session_summary


_SUPPORTED_RUNTIMES = {"codex", "claude_code", "opencode"}
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


def build_adapter_packet(ws: WorkspacePaths, session_id: str, *, runtime: str = "codex") -> dict[str, Any]:
    """Build the compact packet an external agent should read on entry.

    The packet deliberately separates orientation surfaces from trusted kernel
    state so weaker models get useful context without being invited to trust a
    hand-edited Markdown summary.
    """

    normalized_runtime = _normalize_runtime(runtime)
    summary = write_session_summary(ws, session_id)
    orientation = read_summary_orientation(ws, session_id)
    brief = require_valid_execution_brief(build_execution_brief(ws, session_id))
    focus = brief["current_focus"]

    packet = {
        "kind": "adapter_packet",
        "runtime": normalized_runtime,
        "session_id": session_id,
        "topic_id": brief["session"]["topic_id"],
        "truth_sources": ["typed_records", "execution_brief"],
        "orientation_surfaces": summary.files,
        "summary_orientation": orientation,
        "execution_brief": brief,
        "trusted_focus": {
            "active_claim": focus["active_claim"],
            "claim_statement": focus["claim_statement"],
            "confidence_state": focus["confidence_state"],
            "evidence_profile": focus["evidence_profile"],
            "main_uncertainty": focus["main_uncertainty"],
            "flow_profile": brief["flow_profile"]["profile"],
            "risk_level": brief["risk_assessment"]["level"],
        },
        "adapter_contract": {
            "summary_files_are_truth_source": False,
            "summary_files_can_update_kernel_state": False,
            "kernel_must_be_called_before_trust_updates": True,
            "regenerated_from": "kernel_state",
        },
        "trust_changing_actions": list(_TRUST_CHANGING_ACTIONS),
        "requires_kernel_call_before": list(_TRUST_CHANGING_ACTIONS),
        "required_kernel_entrypoints": list(_KERNEL_ENTRYPOINTS),
        "trust_mutation_entrypoints": {
            action: dict(steps) for action, steps in _TRUST_MUTATION_ENTRYPOINTS.items()
        },
        "runtime_trust_update_protocol": {
            action: {
                **protocol,
                "sequence": list(protocol["sequence"]),
                "refresh": list(protocol["refresh"]),
            }
            for action, protocol in _RUNTIME_TRUST_UPDATE_PROTOCOL.items()
        },
        "runtime_record_protocols": {
            action: {
                **protocol,
                "sequence": list(protocol["sequence"]),
                "required_typed_refs": list(protocol["required_typed_refs"]),
                "accepted_link_fields": list(protocol["accepted_link_fields"]),
            }
            for action, protocol in _RUNTIME_RECORD_PROTOCOLS.items()
        },
        "runtime_rules": _runtime_rules(normalized_runtime),
    }
    return require_valid_adapter_packet(packet)


def _normalize_runtime(runtime: str) -> str:
    value = runtime.strip().lower().replace("-", "_")
    if value in _SUPPORTED_RUNTIMES:
        return value
    return "codex"


def _runtime_rules(runtime: str) -> list[str]:
    common_first = "read_for_orientation_only: task_plan/findings/progress are compact views, not truth sources"
    if runtime == "claude_code":
        return [
            common_first,
            "Use MCP wrappers for execution brief, evidence, tool-run, risk, and summary updates.",
            "Before validation or promotion, re-query the kernel and attach typed evidence references.",
        ]
    if runtime == "opencode":
        return [
            common_first,
            "Use CLI entrypoints for execution brief, summaries, evidence, tool runs, and risk checks.",
            "Do not infer confidence changes from local planning files alone.",
        ]
    return [
        common_first,
        "Use CLI or MCP entrypoints for execution brief, summaries, evidence, tool runs, and risk checks.",
        "Keep worktree/code provenance attached before trusting code-method results.",
    ]
