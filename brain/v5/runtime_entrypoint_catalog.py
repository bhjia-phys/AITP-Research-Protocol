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
    "adapter_packet": {
        "cli": "aitp-v5 adapter packet <runtime> <session-id>",
        "mcp": "aitp_v5_get_adapter_packet",
        "surface": "adapter_packet",
    },
    "codex_hook_bridge": {
        "cli": "aitp-v5 adapter hook-bridge codex <session-id> <args>",
        "mcp": "aitp_v5_write_codex_hook_bridge",
        "surface": "codex_hook_bridge",
    },
    "codex_hook_installation": {
        "cli": "aitp-v5 adapter install-hooks codex <session-id> <args>",
        "mcp": "aitp_v5_install_codex_hook_fixture",
        "surface": "codex_hook_installation",
    },
    "opencode_plugin_bridge": {
        "cli": "aitp-v5 adapter hook-bridge opencode <session-id> <args>",
        "mcp": "aitp_v5_write_opencode_plugin_bridge",
        "surface": "opencode_plugin_bridge",
    },
    "opencode_hook_installation": {
        "cli": "aitp-v5 adapter install-hooks opencode <session-id> <args>",
        "mcp": "aitp_v5_install_opencode_hook_fixture",
        "surface": "opencode_hook_installation",
    },
    "claude_code_hook_settings": {
        "cli": "aitp-v5 adapter hook-settings claude-code <session-id> <args>",
        "mcp": "aitp_v5_write_claude_code_hook_settings",
        "surface": "claude_code_hook_settings",
    },
    "claude_code_hook_installation": {
        "cli": "aitp-v5 adapter install-hooks claude-code <session-id> <args>",
        "mcp": "aitp_v5_install_claude_code_hook_settings",
        "surface": "claude_code_hook_installation",
    },
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
}


def sample_args_for_template(template: str) -> list[str]:
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
    if template.startswith("adapter hook-bridge"):
        return [
            "--output",
            "AITP_V5_HOOK_BRIDGE.md",
        ]
    if template.startswith("adapter hook-settings"):
        return [
            "--output",
            ".claude/settings.local.json",
        ]
    if template.startswith("adapter install-hooks codex"):
        return [
            "--output",
            ".codex/AITP_V5_HOOKS.json",
        ]
    if template.startswith("adapter install-hooks opencode"):
        return [
            "--output",
            ".opencode/AITP_V5_PLUGIN_HOOKS.json",
        ]
    if template.startswith("adapter install-hooks"):
        return [
            "--settings",
            ".claude/settings.local.json",
        ]
    if template.startswith("adapter pre-tool-event"):
        return [
            "--bridge-json",
            '{"kind":"codex_hook_bridge","runtime":"codex","source_protocol_field":"runtime_hook_installation","installation_mode":"explicit_guard_calls","native_installer_available":false,"summary_inputs_trusted":false,"can_update_kernel_state":false,"pre_tool_policy_entrypoint":{"cli":"aitp-v5 policy pre-tool <args>","mcp":"aitp_v5_evaluate_pre_tool_policy","surface":"pre_tool_policy_decision","truth_source":"typed_records","summary_inputs_trusted":false,"can_update_kernel_state":false,"can_update_claim_trust":false},"gate_protocols":{"source_protocol_field":"runtime_gate_protocols","record_evidence":{"pre_tool_policy":"aitp_v5_evaluate_pre_tool_policy","preflight":"","sequence":["refresh_execution_brief","evaluate_pre_tool_policy","record_evidence","refresh_execution_brief","write_session_summary"],"required_typed_refs":["topic_id","claim_id"],"allowed_state_sources":["typed_records","typed_evidence_records"],"policy_reasons_field":"policy_reasons","human_checkpoint_required":false,"truth_source":"typed_records","summary_inputs_trusted":false}},"path":"AITP_V5_HOOK_BRIDGE.md","guard_calls":[{"hook_name":"pre_tool"}]}',
            "--event-json",
            '{"runtime":"codex","hook_name":"pre_tool","session_id":"s1","tool_name":"mcp__aitp__aitp_v5_record_evidence","tool_input":{"claim_id":"claim-fqhe","source_kind":"typed_records"}}',
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
