"""Shared validation entrypoints for public AITP v5 surfaces."""

from __future__ import annotations

from typing import Any, Callable

_PUBLIC_SURFACE_NAMES = (
    "adapter_packet",
    "adapter_protocol_registry",
    "claude_code_hook_installation",
    "claude_code_hook_settings",
    "codex_hook_bridge",
    "codex_hook_installation",
    "code_state_record",
    "evidence_record",
    "execution_brief",
    "human_checkpoint_record",
    "hook_trace_event_record",
    "knowledge_connector_catalog",
    "legacy_migration_result",
    "memory_entry_record",
    "object_relation_record",
    "opencode_hook_installation",
    "opencode_plugin_bridge",
    "physics_object_record",
    "pre_tool_policy_decision",
    "promotion_packet_record",
    "record_gate_coverage_audit",
    "reference_location_record",
    "sensemaking_report_record",
    "session_summary_bundle",
    "summary_orientation",
    "tool_executor_catalog",
    "tool_recipe_record",
    "tool_run_record",
    "trust_update_apply",
    "trust_update_preflight",
    "validation_contract_record",
    "validation_result_record",
)
_PUBLIC_SURFACE_VALIDATOR_REF = "brain.v5.public_surfaces.require_valid_public_surface"
_PUBLIC_SURFACE_PURPOSES = {
    "adapter_packet": "runtime adapter packet carrying brief, summary orientation, and trust protocol metadata",
    "adapter_protocol_registry": "auditable registry metadata for adapter protocol fields and validator surfaces",
    "claude_code_hook_installation": "contracted safe merge of AITP hooks into Claude Code settings without treating settings as truth",
    "claude_code_hook_settings": "contracted Claude Code hook settings generated from runtime hook installation metadata",
    "codex_hook_bridge": "contracted Codex hook bridge generated from runtime hook installation metadata",
    "codex_hook_installation": "contracted Codex stdin-runner hook installation fixture generated from runtime metadata",
    "code_state_record": "contracted code-state provenance record for code-dependent physics results",
    "evidence_record": "contracted evidence write result linked to a claim and required outputs",
    "execution_brief": "typed kernel brief for current focus, risk, evidence coverage, and next actions",
    "human_checkpoint_record": "contracted human checkpoint requiring explicit options and a decision from the declared option set",
    "hook_trace_event_record": "contracted persisted hook trace-event record that cannot update claim trust",
    "knowledge_connector_catalog": "contracted catalog of knowledge connectors for notes, literature, and learning memory",
    "legacy_migration_result": "contracted explicit migration result from legacy topic files into v5 typed records",
    "memory_entry_record": "contracted L2 memory entry created only from evidence-backed promotion packets with human approval",
    "object_relation_record": "contracted object-relation record linking physics objects with typed relations, failure modes, and assumptions",
    "opencode_hook_installation": "contracted OpenCode stdin-runner hook installation fixture generated from runtime metadata",
    "opencode_plugin_bridge": "contracted OpenCode plugin bridge generated from runtime hook installation metadata",
    "physics_object_record": "contracted physics-object record for theoretical objects, systems, operators, sectors, and definitions",
    "pre_tool_policy_decision": "contracted pre-tool policy decision derived from typed kernel records, not summaries",
    "promotion_packet_record": "contracted promotion packet requiring explicit evidence refs, known failure modes, and scope before L2 memory promotion",
    "record_gate_coverage_audit": "contracted audit that every runtime record protocol has a conscious runtime gate decision",
    "reference_location_record": "contracted orientation-only pointer to an external paper, note, or knowledge item",
    "sensemaking_report_record": "contracted local sense-making report — orientation-only, never a validation gate",
    "session_summary_bundle": "orientation-only summary files regenerated from typed kernel records",
    "summary_orientation": "read-only summary view with explicit truth-source protections",
    "tool_executor_catalog": "contracted catalog of safe built-in tool executors and input schemas",
    "tool_recipe_record": "contracted reusable tool recipe record with inputs, outputs, and invariants",
    "tool_run_record": "contracted tool-run provenance record linked to claims, code states, and artifacts",
    "trust_update_apply": "contracted result of a trust-changing mutation after preflight",
    "trust_update_preflight": "contracted preflight gate for trust-changing actions",
    "validation_contract_record": "contracted validation contract requiring explicit checks, failure modes, and evidence outputs before a claim can be validated",
    "validation_result_record": "contracted validation result linking a tool run to a validation contract and checked outputs",
}


def public_surface_names() -> tuple[str, ...]:
    """Return the names of public payload surfaces with contract gates."""

    return _PUBLIC_SURFACE_NAMES


def public_surface_validator_ref() -> str:
    """Return the stable import path for validating public payload surfaces."""

    return _PUBLIC_SURFACE_VALIDATOR_REF


def describe_public_surfaces() -> dict[str, Any]:
    """Return an auditable description of public surface contract coverage."""

    return {
        "kind": "public_surface_contracts",
        "validator": public_surface_validator_ref(),
        "surface_names": list(public_surface_names()),
        "surfaces": [
            {
                "name": name,
                "validator": public_surface_validator_ref(),
                "purpose": _PUBLIC_SURFACE_PURPOSES[name],
            }
            for name in public_surface_names()
        ],
        "truth_source": "contract_registry",
        "summary_inputs_trusted": False,
    }


def require_valid_public_surface(surface_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a public payload by stable surface name."""

    validator = _validators().get(surface_name)
    if validator is None:
        raise ValueError(f"unknown public surface: {surface_name}")
    return validator(payload)


def _validators() -> dict[str, Callable[[dict[str, Any]], dict[str, Any]]]:
    from brain.v5.contracts import (
        require_valid_adapter_packet,
        require_valid_adapter_protocol_registry,
        require_valid_codex_hook_bridge,
        require_valid_code_state_record,
        require_valid_evidence_record,
        require_valid_execution_brief,
        require_valid_human_checkpoint_record,
        require_valid_knowledge_connector_catalog,
        require_valid_memory_entry_record,
        require_valid_object_relation_record,
        require_valid_physics_object_record,
        require_valid_promotion_packet_record,
        require_valid_record_gate_coverage_audit,
        require_valid_reference_location_record,
        require_valid_sensemaking_report_record,
        require_valid_session_summary_bundle,
        require_valid_summary_orientation,
        require_valid_tool_executor_catalog,
        require_valid_tool_recipe_record,
        require_valid_tool_run_record,
        require_valid_trust_update_apply,
        require_valid_trust_update_preflight,
        require_valid_validation_contract_record,
        require_valid_validation_result_record,
    )
    from brain.v5.legacy_contracts import require_valid_legacy_migration_result
    from brain.v5.hook_protocol_contracts import (
        require_valid_claude_code_hook_installation,
        require_valid_claude_code_hook_settings,
        require_valid_hook_trace_event_record,
        require_valid_opencode_plugin_bridge,
        require_valid_pre_tool_policy_decision,
    )
    from brain.v5.hook_install_contracts import (
        require_valid_codex_hook_installation,
        require_valid_opencode_hook_installation,
    )

    return {
        "adapter_packet": require_valid_adapter_packet,
        "adapter_protocol_registry": require_valid_adapter_protocol_registry,
        "claude_code_hook_installation": require_valid_claude_code_hook_installation,
        "claude_code_hook_settings": require_valid_claude_code_hook_settings,
        "codex_hook_bridge": require_valid_codex_hook_bridge,
        "codex_hook_installation": require_valid_codex_hook_installation,
        "code_state_record": require_valid_code_state_record,
        "evidence_record": require_valid_evidence_record,
        "execution_brief": require_valid_execution_brief,
        "human_checkpoint_record": require_valid_human_checkpoint_record,
        "hook_trace_event_record": require_valid_hook_trace_event_record,
        "knowledge_connector_catalog": require_valid_knowledge_connector_catalog,
        "legacy_migration_result": require_valid_legacy_migration_result,
        "memory_entry_record": require_valid_memory_entry_record,
        "object_relation_record": require_valid_object_relation_record,
        "opencode_hook_installation": require_valid_opencode_hook_installation,
        "opencode_plugin_bridge": require_valid_opencode_plugin_bridge,
        "physics_object_record": require_valid_physics_object_record,
        "pre_tool_policy_decision": require_valid_pre_tool_policy_decision,
        "promotion_packet_record": require_valid_promotion_packet_record,
        "record_gate_coverage_audit": require_valid_record_gate_coverage_audit,
        "reference_location_record": require_valid_reference_location_record,
        "sensemaking_report_record": require_valid_sensemaking_report_record,
        "session_summary_bundle": require_valid_session_summary_bundle,
        "summary_orientation": require_valid_summary_orientation,
        "tool_executor_catalog": require_valid_tool_executor_catalog,
        "tool_recipe_record": require_valid_tool_recipe_record,
        "tool_run_record": require_valid_tool_run_record,
        "trust_update_apply": require_valid_trust_update_apply,
        "trust_update_preflight": require_valid_trust_update_preflight,
        "validation_contract_record": require_valid_validation_contract_record,
        "validation_result_record": require_valid_validation_result_record,
    }
