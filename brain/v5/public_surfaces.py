"""Shared validation entrypoints for public AITP v5 surfaces."""

from __future__ import annotations

from typing import Any, Callable

_PUBLIC_SURFACE_NAMES = (
    "adapter_packet",
    "adapter_protocol_registry",
    "claim_trust_audit",
    "claude_code_hook_installation",
    "claude_code_hook_settings",
    "codex_hook_bridge",
    "codex_hook_installation",
    "code_state_record",
    "evidence_record",
    "execution_brief",
    "failure_mode_audit",
    "failure_mode_review_packet",
    "failure_mode_review_result_record",
    "final_engineering_readiness_audit",
    "human_checkpoint_record",
    "hook_trace_event_record",
    "interaction_recording_preview",
    "kimi_code_hook_config",
    "kimi_code_hook_installation",
    "knowledge_connector_catalog",
    "l2_obsidian_view_bundle",
    "l2_memory_audit",
    "legacy_l2_graph_manifest",
    "legacy_migration_coverage_audit",
    "legacy_migration_result",
    "legacy_semantic_review_manifest",
    "legacy_semantic_review_packet",
    "legacy_semantic_repair_apply",
    "legacy_semantic_repair_plan",
    "legacy_semantic_review_result_record",
    "legacy_semantic_review_queue",
    "memory_entry_record",
    "object_relation_record",
    "opencode_hook_installation",
    "opencode_plugin_bridge",
    "physics_object_record",
    "pre_tool_policy_decision",
    "promotion_packet_record",
    "record_gate_coverage_audit",
    "reference_location_record",
    "runtime_hook_installation_audit",
    "runtime_host_lifecycle_audit",
    "runtime_host_readiness_audit",
    "runtime_hook_installation_paths",
    "runtime_hook_smoke_coverage",
    "sensemaking_report_record",
    "session_summary_bundle",
    "source_reconstruction_audit",
    "source_reconstruction_manifest",
    "summary_orientation",
    "tool_executor_catalog",
    "tool_recipe_record",
    "tool_run_record",
    "trust_update_record",
    "trust_update_apply",
    "trust_update_preflight",
    "validation_contract_record",
    "validation_result_record",
    "workspace_summary_bundle",
    "workspace_replay_packet",
    "workspace_refresh_bundle",
)
_PUBLIC_SURFACE_VALIDATOR_REF = "brain.v5.public_surfaces.require_valid_public_surface"
_PUBLIC_SURFACE_PURPOSES = {
    "adapter_packet": "runtime adapter packet carrying brief, summary orientation, and trust protocol metadata",
    "adapter_protocol_registry": "auditable registry metadata for adapter protocol fields and validator surfaces",
    "claim_trust_audit": "read-only typed-record audit of whether a claim confidence state has evidence, validation, memory, and code provenance support",
    "claude_code_hook_installation": "contracted safe merge of AITP hooks into Claude Code settings without treating settings as truth",
    "claude_code_hook_settings": "contracted Claude Code hook settings generated from runtime hook installation metadata",
    "codex_hook_bridge": "contracted Codex hook bridge generated from runtime hook installation metadata",
    "codex_hook_installation": "contracted Codex stdin-runner hook installation fixture generated from runtime metadata",
    "code_state_record": "contracted code-state provenance record for code-dependent physics results",
    "evidence_record": "contracted evidence write result linked to a claim and required outputs",
    "execution_brief": "typed kernel brief for current focus, risk, evidence coverage, and next actions",
    "failure_mode_audit": "read-only typed-record audit of claim, validation, and promotion failure-mode coverage",
    "failure_mode_review_packet": "read-only physics adequacy review questions for recorded failure modes",
    "failure_mode_review_result_record": "contracted typed record preserving the evidence/tool/literature basis behind an approved failure-mode review",
    "final_engineering_readiness_audit": "orientation-only final-gap audit separating AITP v5 kernel capability from remaining host and legacy semantic-review backlog",
    "human_checkpoint_record": "contracted human checkpoint requiring explicit options and a decision from the declared option set",
    "hook_trace_event_record": "contracted persisted hook trace-event record that cannot update claim trust",
    "interaction_recording_preview": "read-only preview of natural conversation recording boundaries, lightweight mode, and heavier triggers",
    "kimi_code_hook_config": "contracted Kimi Code TOML hook config generated from runtime hook installation metadata",
    "kimi_code_hook_installation": "contracted safe merge of AITP hooks into Kimi Code TOML config without treating config as truth",
    "knowledge_connector_catalog": "contracted catalog of knowledge connectors for notes, literature, and learning memory",
    "l2_obsidian_view_bundle": "orientation-only Obsidian Markdown view over typed L2 memory entries",
    "l2_memory_audit": "read-only typed-record audit of L2 memory provenance for one claim",
    "legacy_l2_graph_manifest": "read-only manifest for planning legacy global L2 graph/index migration into typed L2 memory and Obsidian views",
    "legacy_migration_coverage_audit": "read-only audit of legacy migration file accounting, archive references, and per-topic coverage without claiming semantic proof",
    "legacy_migration_result": "contracted explicit migration result from legacy topic files into v5 typed records",
    "legacy_semantic_review_manifest": "orientation-only batch manifest listing per-topic semantic review packets, statuses, and result-record commands",
    "legacy_semantic_review_packet": "orientation-only per-topic packet collecting migrated legacy refs, typed records, and checklist for actual semantic review",
    "legacy_semantic_repair_apply": "guarded content repair application derived from typed legacy semantic review results without changing claim trust",
    "legacy_semantic_repair_plan": "read-only repair plan derived from typed legacy semantic review results without applying claim trust or kernel-state mutations",
    "legacy_semantic_review_result_record": "contracted per-topic legacy migration semantic review result with explicit review basis and no claim-trust mutation authority",
    "legacy_semantic_review_queue": "orientation-only per-topic semantic review queue for completed legacy migrations, linking accounting coverage to typed source reconstruction gaps without claiming semantic proof",
    "memory_entry_record": "contracted L2 memory entry created only from evidence-backed promotion packets with human approval",
    "object_relation_record": "contracted object-relation record linking physics objects with typed relations, failure modes, and assumptions",
    "opencode_hook_installation": "contracted OpenCode stdin-runner hook installation fixture generated from runtime metadata",
    "opencode_plugin_bridge": "contracted OpenCode plugin bridge generated from runtime hook installation metadata",
    "physics_object_record": "contracted physics-object record for theoretical objects, systems, operators, sectors, and definitions",
    "pre_tool_policy_decision": "contracted pre-tool policy decision derived from typed kernel records, not summaries",
    "promotion_packet_record": "contracted promotion packet requiring explicit evidence refs, known failure modes, and scope before L2 memory promotion",
    "record_gate_coverage_audit": "contracted audit that every runtime record protocol has a conscious runtime gate decision",
    "reference_location_record": "contracted orientation-only pointer to an external paper, note, or knowledge item",
    "runtime_hook_installation_audit": "read-only audit of installed runtime hook files; runtime metadata only, never kernel truth",
    "runtime_host_lifecycle_audit": "dynamic read-only probe that runs a host command and checks stdout/stderr plus hook trace deltas for lifecycle-event evidence",
    "runtime_host_readiness_audit": "dynamic read-only audit that launches the local host command and checks installed hook files without updating kernel truth",
    "runtime_hook_installation_paths": "read-only discovery of workspace-local hook install targets for Codex, Claude Code, Kimi Code, and OpenCode",
    "runtime_hook_smoke_coverage": "read-only report of which generated runtime hook paths have test-backed smoke coverage",
    "sensemaking_report_record": "contracted local sense-making report — orientation-only, never a validation gate",
    "session_summary_bundle": "orientation-only summary files regenerated from typed kernel records",
    "source_reconstruction_audit": "read-only typed-record audit of whether a claim has definition, scope, source, dependency, reconstruction, and failure-condition coverage",
    "source_reconstruction_manifest": "read-only backlog manifest batching source reconstruction gaps and next actions across active claims",
    "summary_orientation": "read-only summary view with explicit truth-source protections",
    "tool_executor_catalog": "contracted catalog of safe built-in tool executors and input schemas",
    "tool_recipe_record": "contracted reusable tool recipe record with inputs, outputs, and invariants",
    "tool_run_record": "contracted tool-run provenance record linked to claims, code states, and artifacts",
    "trust_update_record": "contracted durable history record for a trust-update apply attempt",
    "trust_update_apply": "contracted result of a trust-changing mutation after preflight",
    "trust_update_preflight": "contracted preflight gate for trust-changing actions",
    "validation_contract_record": "contracted validation contract requiring explicit checks, failure modes, and evidence outputs before a claim can be validated",
    "validation_result_record": "contracted validation result linking a tool run to a validation contract and checked outputs",
    "workspace_summary_bundle": "orientation-only workspace summary regenerated from typed sessions, active claims, memory entries, and validation links",
    "workspace_replay_packet": "orientation-only multi-session replay packet listing resume attention, source reconstruction gaps, evidence gaps, and next actions from typed records",
    "workspace_refresh_bundle": "orientation-only host startup bundle that refreshes workspace summary, replay packet, and L2 Obsidian views from typed records",
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
        require_valid_claim_trust_audit,
        require_valid_codex_hook_bridge,
        require_valid_code_state_record,
        require_valid_evidence_record,
        require_valid_execution_brief,
        require_valid_failure_mode_audit,
        require_valid_failure_mode_review_packet,
        require_valid_failure_mode_review_result_record,
        require_valid_final_engineering_readiness_audit,
        require_valid_human_checkpoint_record,
        require_valid_knowledge_connector_catalog,
        require_valid_l2_memory_audit,
        require_valid_memory_entry_record,
        require_valid_object_relation_record,
        require_valid_physics_object_record,
        require_valid_promotion_packet_record,
        require_valid_record_gate_coverage_audit,
        require_valid_reference_location_record,
        require_valid_runtime_hook_installation_audit,
        require_valid_runtime_hook_installation_paths,
        require_valid_runtime_hook_smoke_coverage,
        require_valid_sensemaking_report_record,
        require_valid_session_summary_bundle,
        require_valid_source_reconstruction_audit,
        require_valid_summary_orientation,
        require_valid_tool_executor_catalog,
        require_valid_tool_recipe_record,
        require_valid_tool_run_record,
        require_valid_trust_update_record,
        require_valid_trust_update_apply,
        require_valid_trust_update_preflight,
        require_valid_validation_contract_record,
        require_valid_validation_result_record,
        require_valid_workspace_summary_bundle,
        require_valid_workspace_replay_packet,
    )
    from brain.v5.legacy_contracts import require_valid_legacy_migration_result
    from brain.v5.legacy_l2_graph_contracts import require_valid_legacy_l2_graph_manifest
    from brain.v5.legacy_migration_audit_contracts import require_valid_legacy_migration_coverage_audit
    from brain.v5.source_reconstruction_contracts import require_valid_source_reconstruction_manifest
    from brain.v5.legacy_semantic_review_contracts import (
        require_valid_legacy_semantic_review_manifest,
        require_valid_legacy_semantic_review_packet,
        require_valid_legacy_semantic_repair_apply,
        require_valid_legacy_semantic_repair_plan,
        require_valid_legacy_semantic_review_queue,
        require_valid_legacy_semantic_review_result_record,
    )
    from brain.v5.host_readiness_contracts import require_valid_runtime_host_readiness_audit
    from brain.v5.host_lifecycle_contracts import require_valid_runtime_host_lifecycle_audit
    from brain.v5.interaction_preview_contracts import require_valid_interaction_recording_preview
    from brain.v5.obsidian_view_contracts import require_valid_l2_obsidian_view_bundle
    from brain.v5.workspace_refresh_contracts import require_valid_workspace_refresh_bundle
    from brain.v5.hook_protocol_contracts import (
        require_valid_claude_code_hook_installation,
        require_valid_claude_code_hook_settings,
        require_valid_hook_trace_event_record,
        require_valid_opencode_plugin_bridge,
        require_valid_pre_tool_policy_decision,
    )
    from brain.v5.hook_kimi_contracts import (
        require_valid_kimi_code_hook_config,
        require_valid_kimi_code_hook_installation,
    )
    from brain.v5.hook_install_contracts import (
        require_valid_codex_hook_installation,
        require_valid_opencode_hook_installation,
    )

    return {
        "adapter_packet": require_valid_adapter_packet,
        "adapter_protocol_registry": require_valid_adapter_protocol_registry,
        "claim_trust_audit": require_valid_claim_trust_audit,
        "claude_code_hook_installation": require_valid_claude_code_hook_installation,
        "claude_code_hook_settings": require_valid_claude_code_hook_settings,
        "codex_hook_bridge": require_valid_codex_hook_bridge,
        "codex_hook_installation": require_valid_codex_hook_installation,
        "code_state_record": require_valid_code_state_record,
        "evidence_record": require_valid_evidence_record,
        "execution_brief": require_valid_execution_brief,
        "failure_mode_audit": require_valid_failure_mode_audit,
        "failure_mode_review_packet": require_valid_failure_mode_review_packet,
        "failure_mode_review_result_record": require_valid_failure_mode_review_result_record,
        "final_engineering_readiness_audit": require_valid_final_engineering_readiness_audit,
        "human_checkpoint_record": require_valid_human_checkpoint_record,
        "hook_trace_event_record": require_valid_hook_trace_event_record,
        "interaction_recording_preview": require_valid_interaction_recording_preview,
        "kimi_code_hook_config": require_valid_kimi_code_hook_config,
        "kimi_code_hook_installation": require_valid_kimi_code_hook_installation,
        "knowledge_connector_catalog": require_valid_knowledge_connector_catalog,
        "l2_obsidian_view_bundle": require_valid_l2_obsidian_view_bundle,
        "l2_memory_audit": require_valid_l2_memory_audit,
        "legacy_l2_graph_manifest": require_valid_legacy_l2_graph_manifest,
        "legacy_migration_coverage_audit": require_valid_legacy_migration_coverage_audit,
        "legacy_migration_result": require_valid_legacy_migration_result,
        "legacy_semantic_review_manifest": require_valid_legacy_semantic_review_manifest,
        "legacy_semantic_review_packet": require_valid_legacy_semantic_review_packet,
        "legacy_semantic_repair_apply": require_valid_legacy_semantic_repair_apply,
        "legacy_semantic_repair_plan": require_valid_legacy_semantic_repair_plan,
        "legacy_semantic_review_result_record": require_valid_legacy_semantic_review_result_record,
        "legacy_semantic_review_queue": require_valid_legacy_semantic_review_queue,
        "memory_entry_record": require_valid_memory_entry_record,
        "object_relation_record": require_valid_object_relation_record,
        "opencode_hook_installation": require_valid_opencode_hook_installation,
        "opencode_plugin_bridge": require_valid_opencode_plugin_bridge,
        "physics_object_record": require_valid_physics_object_record,
        "pre_tool_policy_decision": require_valid_pre_tool_policy_decision,
        "promotion_packet_record": require_valid_promotion_packet_record,
        "record_gate_coverage_audit": require_valid_record_gate_coverage_audit,
        "reference_location_record": require_valid_reference_location_record,
        "runtime_hook_installation_audit": require_valid_runtime_hook_installation_audit,
        "runtime_host_lifecycle_audit": require_valid_runtime_host_lifecycle_audit,
        "runtime_host_readiness_audit": require_valid_runtime_host_readiness_audit,
        "runtime_hook_installation_paths": require_valid_runtime_hook_installation_paths,
        "runtime_hook_smoke_coverage": require_valid_runtime_hook_smoke_coverage,
        "sensemaking_report_record": require_valid_sensemaking_report_record,
        "session_summary_bundle": require_valid_session_summary_bundle,
        "source_reconstruction_audit": require_valid_source_reconstruction_audit,
        "source_reconstruction_manifest": require_valid_source_reconstruction_manifest,
        "summary_orientation": require_valid_summary_orientation,
        "tool_executor_catalog": require_valid_tool_executor_catalog,
        "tool_recipe_record": require_valid_tool_recipe_record,
        "tool_run_record": require_valid_tool_run_record,
        "trust_update_record": require_valid_trust_update_record,
        "trust_update_apply": require_valid_trust_update_apply,
        "trust_update_preflight": require_valid_trust_update_preflight,
        "validation_contract_record": require_valid_validation_contract_record,
        "validation_result_record": require_valid_validation_result_record,
        "workspace_summary_bundle": require_valid_workspace_summary_bundle,
        "workspace_replay_packet": require_valid_workspace_replay_packet,
        "workspace_refresh_bundle": require_valid_workspace_refresh_bundle,
    }
