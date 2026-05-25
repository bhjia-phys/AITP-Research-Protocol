"""Runtime entrypoint catalog data and CLI sample arguments."""
from __future__ import annotations

from typing import Any

RUNTIME_ENTRYPOINTS: dict[str, dict[str, Any]] = {
    "public_surfaces": {
        "cli": "aitp-v5 adapter public-surfaces",
        "mcp": "aitp_v5_describe_public_surfaces",
        "surface": "public_surface_contracts",
    },
    "adapter_registry": {
        "cli": "aitp-v5 adapter registry",
        "mcp": "aitp_v5_get_adapter_protocol_registry",
        "surface": "adapter_protocol_registry",
    },
    "record_gate_coverage_audit": {
        "cli": "aitp-v5 adapter record-gate-audit",
        "mcp": "aitp_v5_audit_record_gate_coverage",
        "surface": "record_gate_coverage_audit",
    },
    "runtime_hook_installation_audit": {
        "cli": "aitp-v5 adapter install-audit <runtime> <args>",
        "mcp": "aitp_v5_audit_hook_installation",
        "surface": "runtime_hook_installation_audit",
    },
    "runtime_host_lifecycle_audit": {"cli": "aitp-v5 adapter host-lifecycle <runtime>", "mcp": "aitp_v5_audit_runtime_host_lifecycle", "surface": "runtime_host_lifecycle_audit"},
    "runtime_host_readiness_audit": {"cli": "aitp-v5 adapter host-readiness <runtime>", "mcp": "aitp_v5_audit_runtime_host_readiness", "surface": "runtime_host_readiness_audit"},
    "runtime_hook_installation_paths": {
        "cli": "aitp-v5 adapter install-paths",
        "mcp": "aitp_v5_discover_hook_install_paths",
        "surface": "runtime_hook_installation_paths",
    },
    "runtime_hook_smoke_coverage": {"cli": "aitp-v5 adapter smoke-coverage", "mcp": "aitp_v5_report_hook_smoke_coverage", "surface": "runtime_hook_smoke_coverage"},
    "adapter_packet": {
        "cli": "aitp-v5 adapter packet <runtime> <session-id>",
        "mcp": "aitp_v5_get_adapter_packet",
        "surface": "adapter_packet",
    },
    "codex_hook_bridge": {"cli": "aitp-v5 adapter hook-bridge codex <session-id> <args>", "mcp": "aitp_v5_write_codex_hook_bridge", "surface": "codex_hook_bridge"},
    "codex_hook_installation": {"cli": "aitp-v5 adapter install-hooks codex <session-id> <args>", "mcp": "aitp_v5_install_codex_hook_fixture", "surface": "codex_hook_installation"},
    "opencode_plugin_bridge": {"cli": "aitp-v5 adapter hook-bridge opencode <session-id> <args>", "mcp": "aitp_v5_write_opencode_plugin_bridge", "surface": "opencode_plugin_bridge"},
    "opencode_hook_installation": {"cli": "aitp-v5 adapter install-hooks opencode <session-id> <args>", "mcp": "aitp_v5_install_opencode_hook_fixture", "surface": "opencode_hook_installation"},
    "claude_code_hook_settings": {"cli": "aitp-v5 adapter hook-settings claude-code <session-id> <args>", "mcp": "aitp_v5_write_claude_code_hook_settings", "surface": "claude_code_hook_settings"},
    "claude_code_hook_installation": {"cli": "aitp-v5 adapter install-hooks claude-code <session-id> <args>", "mcp": "aitp_v5_install_claude_code_hook_settings", "surface": "claude_code_hook_installation"},
    "kimi_code_hook_config": {"cli": "aitp-v5 adapter hook-settings kimi-code <session-id> <args>", "mcp": "aitp_v5_write_kimi_code_hook_config", "surface": "kimi_code_hook_config"},
    "kimi_code_hook_installation": {"cli": "aitp-v5 adapter install-hooks kimi-code <session-id> <args>", "mcp": "aitp_v5_install_kimi_code_hook_config", "surface": "kimi_code_hook_installation"},
    "adapter_pre_tool_event": {
        "cli": "aitp-v5 adapter pre-tool-event <runtime> <session-id> <args>",
        "mcp": "aitp_v5_evaluate_adapter_pre_tool_event",
        "surface": "pre_tool_policy_decision",
    },
    "execution_brief": {
        "cli": "aitp-v5 brief <session-id>",
        "mcp": "aitp_v5_get_execution_brief",
        "surface": "execution_brief",
    },
    "interaction_recording_preview": {"cli": "aitp-v5 interaction preview <session-id>", "mcp": "aitp_v5_preview_interaction_recording", "surface": "interaction_recording_preview"},
    "record_code_state": {
        "cli": "aitp-v5 code state record <args>",
        "mcp": "aitp_v5_record_code_state",
        "surface": "code_state_record",
    },
    "record_evidence": {
        "cli": "aitp-v5 evidence record <args>",
        "mcp": "aitp_v5_record_evidence",
        "surface": "evidence_record",
    },
    "register_tool_recipe": {
        "cli": "aitp-v5 tool recipe register <args>",
        "mcp": "aitp_v5_register_tool_recipe",
        "surface": "tool_recipe_record",
    },
    "record_tool_run": {
        "cli": "aitp-v5 tool run record <args>",
        "mcp": "aitp_v5_record_tool_run",
        "surface": "tool_run_record",
    },
    "execute_tool": {
        "cli": "aitp-v5 tool execute <args>",
        "mcp": "aitp_v5_execute_tool",
        "surface": "tool_run_record",
    },
    "list_tool_executors": {
        "cli": "aitp-v5 tool executors",
        "mcp": "aitp_v5_list_tool_executors",
        "surface": "tool_executor_catalog",
    },
    "list_knowledge_connectors": {
        "cli": "aitp-v5 knowledge connectors",
        "mcp": "aitp_v5_list_knowledge_connectors",
        "surface": "knowledge_connector_catalog",
    },
    "source_reconstruction_audit": {
        "cli": "aitp-v5 source reconstruction-audit <args>",
        "mcp": "aitp_v5_audit_source_reconstruction",
        "surface": "source_reconstruction_audit",
    },
    "persist_hook_trace_event": {
        "cli": "aitp-v5 trace hook-event persist <args>",
        "mcp": "aitp_v5_persist_hook_trace_event",
        "surface": "hook_trace_event_record",
    },
    "record_reference_location": {
        "cli": "aitp-v5 reference location record <args>",
        "mcp": "aitp_v5_record_reference_location",
        "surface": "reference_location_record",
    },
    "migrate_legacy_topic": {
        "cli": "aitp-v5 legacy migrate <args>",
        "mcp": "aitp_v5_migrate_legacy_topic_to_v5",
        "surface": "legacy_migration_result",
    },
    "legacy_migration_coverage_audit": {
        "cli": "aitp-v5 legacy migration-audit <args>",
        "mcp": "aitp_v5_audit_legacy_migration_coverage",
        "surface": "legacy_migration_coverage_audit",
    },
    "legacy_semantic_review_queue": {
        "cli": "aitp-v5 legacy semantic-review-queue <args>",
        "mcp": "aitp_v5_build_legacy_semantic_review_queue",
        "surface": "legacy_semantic_review_queue",
    },
    "record_legacy_semantic_review_result": {
        "cli": "aitp-v5 legacy semantic-review-result <args>",
        "mcp": "aitp_v5_record_legacy_semantic_review_result",
        "surface": "legacy_semantic_review_result_record",
    },
    "summary_orientation": {
        "cli": "aitp-v5 summary orientation <session-id>",
        "mcp": "aitp_v5_read_summary_orientation",
        "surface": "summary_orientation",
    },
    "session_summary": {
        "cli": "aitp-v5 summary session <session-id>",
        "mcp": "aitp_v5_write_session_summary",
        "surface": "session_summary_bundle",
    },
    "workspace_summary": {"cli": "aitp-v5 summary workspace", "mcp": "aitp_v5_write_workspace_summary", "surface": "workspace_summary_bundle"},
    "workspace_replay": {"cli": "aitp-v5 summary replay", "mcp": "aitp_v5_write_workspace_replay_packet", "surface": "workspace_replay_packet"},
    "workspace_refresh": {"cli": "aitp-v5 summary refresh", "mcp": "aitp_v5_refresh_workspace_views", "surface": "workspace_refresh_bundle"},
    "trust_preflight": {
        "cli": "aitp-v5 trust preflight <args>",
        "mcp": "aitp_v5_preflight_trust_update",
        "surface": "trust_update_preflight",
    },
    "trust_apply": {
        "cli": "aitp-v5 trust apply <args>",
        "mcp": "aitp_v5_apply_trust_update",
        "surface": "trust_update_apply",
    },
    "get_trust_update_record": {
        "cli": "aitp-v5 trust update-record <args>",
        "mcp": "aitp_v5_get_trust_update_record",
        "surface": "trust_update_record",
    },
    "audit_claim_trust": {
        "cli": "aitp-v5 trust audit <args>",
        "mcp": "aitp_v5_audit_claim_trust",
        "surface": "claim_trust_audit",
    },
    "pre_tool_policy": {
        "cli": "aitp-v5 policy pre-tool <args>",
        "mcp": "aitp_v5_evaluate_pre_tool_policy",
        "surface": "pre_tool_policy_decision",
    },
    "record_physics_object": {
        "cli": "aitp-v5 object record <args>",
        "mcp": "aitp_v5_record_physics_object",
        "surface": "physics_object_record",
    },
    "record_object_relation": {
        "cli": "aitp-v5 relation record <args>",
        "mcp": "aitp_v5_record_object_relation",
        "surface": "object_relation_record",
    },
    "record_sensemaking_report": {
        "cli": "aitp-v5 sensemaking report <args>",
        "mcp": "aitp_v5_record_sensemaking_report",
        "surface": "sensemaking_report_record",
    },
    "ingest_subagent_result": {
        "cli": "aitp-v5 subagent ingest-result <args>",
        "mcp": "aitp_v5_ingest_subagent_result",
        "surface": "sensemaking_report_record",
    },
    "create_validation_contract": {
        "cli": "aitp-v5 validation contract create <args>",
        "mcp": "aitp_v5_create_validation_contract",
        "surface": "validation_contract_record",
    },
    "record_validation_result": {
        "cli": "aitp-v5 validation result record <args>",
        "mcp": "aitp_v5_record_validation_result",
        "surface": "validation_result_record",
    },
    "request_human_checkpoint": {
        "cli": "aitp-v5 checkpoint request <args>",
        "mcp": "aitp_v5_request_human_checkpoint",
        "surface": "human_checkpoint_record",
    },
    "decide_human_checkpoint": {
        "cli": "aitp-v5 checkpoint decide <args>",
        "mcp": "aitp_v5_decide_human_checkpoint",
        "surface": "human_checkpoint_record",
    },
    "create_promotion_packet": {
        "cli": "aitp-v5 promotion packet create <args>",
        "mcp": "aitp_v5_create_promotion_packet",
        "surface": "promotion_packet_record",
    },
    "apply_promotion_packet": {
        "cli": "aitp-v5 promotion packet apply <args>",
        "mcp": "aitp_v5_apply_promotion_packet",
        "surface": "memory_entry_record",
    },
    "audit_l2_memory_context": {"cli": "aitp-v5 memory audit <args>", "mcp": "aitp_v5_audit_l2_memory_context", "surface": "l2_memory_audit"},
    "l2_obsidian_view": {"cli": "aitp-v5 memory obsidian-view", "mcp": "aitp_v5_write_l2_obsidian_view", "surface": "l2_obsidian_view_bundle"},
    "audit_failure_mode_coverage": {"cli": "aitp-v5 memory failure-modes <args>", "mcp": "aitp_v5_audit_failure_mode_coverage", "surface": "failure_mode_audit"},
    "build_failure_mode_review_packet": {"cli": "aitp-v5 memory failure-mode-review <args>", "mcp": "aitp_v5_build_failure_mode_review_packet", "surface": "failure_mode_review_packet"},
    "request_failure_mode_review_checkpoint": {"cli": "aitp-v5 memory request-failure-mode-review <args>", "mcp": "aitp_v5_request_failure_mode_review_checkpoint", "surface": "human_checkpoint_record"},
    "record_failure_mode_review_result": {"cli": "aitp-v5 memory failure-mode-review-result <args>", "mcp": "aitp_v5_record_failure_mode_review_result", "surface": "failure_mode_review_result_record"},
}


def sample_args_for_template(template: str) -> list[str]:
    from brain.v5.runtime_entrypoint_samples import adapter_sample_args

    adapter_args = adapter_sample_args(template)
    if adapter_args is not None:
        return adapter_args
    if template.startswith("trust update-record"):
        return [
            "trust-update-sample",
        ]
    if template.startswith("trust audit"):
        return [
            "--claim",
            "claim-fqhe",
        ]
    if template.startswith("trust "):
        return [
            "change_claim_confidence",
            "--session",
            "s1",
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
        ]
    if template.startswith("policy pre-tool"):
        return [
            "validate_claim",
            "--session",
            "s1",
            "--claim",
            "claim-fqhe",
            "--source-kind",
            "typed_records",
        ]
    if template.startswith("memory failure-mode-review-result"):
        return ["--claim", "claim-fqhe", "--checkpoint", "checkpoint-fqhe", "--status", "passed", "--reviewed-mode", "sector misassignment", "--basis-ref", "literature:fqhe", "--summary", "Review basis."]
    if template.startswith(("memory audit", "memory failure-modes", "memory failure-mode-review", "memory request-failure-mode-review")):
        return ["--claim", "claim-fqhe"]
    if template.startswith("source reconstruction-audit"):
        return ["--claim", "claim-fqhe"]
    if template.startswith("code state record"):
        return [
            "--repo-id",
            "librpa",
            "--upstream-remote",
            "origin",
            "--upstream-branch",
            "master",
            "--upstream-commit",
            "abc123",
            "--local-branch",
            "topic/gw",
            "--worktree-path",
            "D:/worktrees/librpa/gw",
        ]
    if template.startswith("evidence record"):
        return [
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
            "--type",
            "toy_numeric",
            "--status",
            "supports",
            "--summary",
            "Finite-size check.",
        ]
    if template.startswith("tool recipe register"):
        return [
            "recipe-ed",
            "--family",
            "numerical",
            "--name",
            "exact-diagonalization",
            "--purpose",
            "Run an ED check.",
        ]
    if template.startswith("tool run record"):
        return [
            "--recipe",
            "recipe-ed",
            "--family",
            "numerical",
            "--name",
            "exact-diagonalization",
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
        ]
    if template.startswith("tool execute"):
        return [
            "scalar_tolerance_check",
            "--recipe",
            "recipe-ed",
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
            "--inputs-json",
            '{"observed":1,"expected":1,"tolerance":0}',
        ]
    if template.startswith("reference location record"):
        return [
            "--topic",
            "fqhe",
            "--connector",
            "local_pdf",
            "--type",
            "paper_pdf",
            "--uri",
            "file:///papers/fqhe.pdf",
            "--label",
            "FQHE paper PDF",
        ]
    if template.startswith("trace hook-event persist"):
        return [
            "--payload-json",
            '{"kind":"hook_trace_event","hook_name":"post_tool","event":{"event_id":"event-1","session_id":"s1","topic_id":"fqhe","event_type":"tool_run_recorded","risk_level":"guided","payload":{},"kind":"trace_event"},"exit_code":0,"summary_inputs_trusted":false}',
        ]
    if template.startswith("legacy migrate"):
        return [
            "D:/aitp/legacy-topic",
            "--context",
            "legacy-context",
            "--session",
            "s1",
        ]
    if template.startswith("legacy migration-audit"):
        return [
            "--migration-dir",
            "D:/aitp/.aitp/migrations/legacy-v5-lossless-run",
        ]
    if template.startswith("legacy semantic-review-queue"):
        return [
            "--migration-dir",
            "D:/aitp/.aitp/migrations/legacy-v5-lossless-run",
        ]
    if template.startswith("legacy semantic-review-result"):
        return [
            "--migration-dir",
            "D:/aitp/.aitp/migrations/legacy-v5-lossless-run",
            "--topic",
            "fqhe",
            "--status",
            "inconclusive",
            "--legacy-ref",
            "legacy-topic:state.md",
            "--summary",
            "Semantic review sample.",
        ]
    if template.startswith("object record"):
        return [
            "--topic",
            "fqhe",
            "--type",
            "hilbert_sector",
            "--name",
            "N=8 sector",
            "--definition",
            "Finite-size Hilbert sector.",
        ]
    if template.startswith("relation record"):
        return [
            "--topic",
            "fqhe",
            "--type",
            "diagnoses",
            "--subject",
            "object-a",
            "--object",
            "object-b",
            "--statement",
            "A diagnoses B.",
        ]
    if template.startswith("sensemaking report"):
        return [
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
            "--title",
            "Sanity check",
            "--summary",
            "Counting holds for N=8.",
        ]
    if template.startswith("subagent ingest-result"):
        return [
            "--topic",
            "fqhe",
            "--packet-json",
            '{"packet_id":"packet-critic","packet_type":"CriticPacket","claim_id":"claim-fqhe","claim_statement":"Claim"}',
            "--result-json",
            '{"summary":"Critique result."}',
        ]
    if template.startswith("validation contract create"):
        return [
            "--topic",
            "gw",
            "--claim",
            "claim-gw",
            "--required-check",
            "code_state_present",
            "--failure-mode",
            "dirty worktree",
            "--required-output",
            "evidence_or_provenance",
        ]
    if template.startswith("validation result record"):
        return [
            "--topic",
            "gw",
            "--claim",
            "claim-gw",
            "--contract",
            "validation-contract-gw",
            "--tool-run",
            "tool-run-gw",
            "--status",
            "inconclusive",
            "--checked-output",
            "evidence_or_provenance",
            "--summary",
            "Validation result sample.",
        ]
    if template.startswith("checkpoint request"):
        return [
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
            "--reason",
            "Promotion requires judgment",
            "--requested-by",
            "risk_policy",
            "--option",
            "approve",
        ]
    if template.startswith("checkpoint decide"):
        return [
            "checkpoint-test",
            "--decision",
            "approve",
            "--rationale",
            "Looks good",
            "--decided-by",
            "human",
        ]
    if template.startswith("promotion packet create"):
        return [
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
            "--proposed-kind",
            "scoped_claim",
            "--scope",
            "N<=10 ED",
            "--evidence-ref",
            "evidence-1",
            "--validation-result-id",
            "validation-result-1",
            "--failure-mode",
            "misassignment",
        ]
    if template.startswith("promotion packet apply"):
        return [
            "packet-fqhe",
            "--checkpoint",
            "checkpoint-fqhe",
        ]
    return []
