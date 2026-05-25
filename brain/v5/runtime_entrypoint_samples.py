"""Focused sample argv helpers for runtime entrypoint validation."""

from __future__ import annotations


def adapter_sample_args(template: str) -> list[str] | None:
    if template.startswith("adapter hook-bridge"):
        return ["--output", "AITP_V5_HOOK_BRIDGE.md"]
    if template.startswith("adapter hook-settings"):
        return ["--output", ".claude/settings.local.json"]
    if template.startswith("adapter install-hooks kimi-code"):
        return ["--settings", ".kimi/config.toml"]
    if template.startswith("adapter install-hooks codex"):
        return ["--output", ".codex/AITP_V5_HOOKS.json"]
    if template.startswith("adapter install-hooks opencode"):
        return ["--output", ".opencode/AITP_V5_PLUGIN_HOOKS.json"]
    if template.startswith("adapter install-hooks"):
        return ["--settings", ".claude/settings.local.json"]
    if template.startswith("adapter pre-tool-event"):
        return [
            "--bridge-json",
            '{"kind":"codex_hook_bridge","runtime":"codex","source_protocol_field":"runtime_hook_installation","installation_mode":"explicit_guard_calls","native_installer_available":false,"summary_inputs_trusted":false,"can_update_kernel_state":false,"pre_tool_policy_entrypoint":{"cli":"aitp-v5 policy pre-tool <args>","mcp":"aitp_v5_evaluate_pre_tool_policy","surface":"pre_tool_policy_decision","truth_source":"typed_records","summary_inputs_trusted":false,"can_update_kernel_state":false,"can_update_claim_trust":false},"gate_protocols":{"source_protocol_field":"runtime_gate_protocols","record_evidence":{"pre_tool_policy":"aitp_v5_evaluate_pre_tool_policy","preflight":"","sequence":["refresh_execution_brief","evaluate_pre_tool_policy","record_evidence","refresh_execution_brief","write_session_summary"],"required_typed_refs":["topic_id","claim_id"],"allowed_state_sources":["typed_records","typed_evidence_records"],"policy_reasons_field":"policy_reasons","human_checkpoint_required":false,"truth_source":"typed_records","summary_inputs_trusted":false}},"path":"AITP_V5_HOOK_BRIDGE.md","guard_calls":[{"hook_name":"pre_tool"}]}',
            "--event-json",
            '{"runtime":"codex","hook_name":"pre_tool","session_id":"s1","tool_name":"mcp__aitp__aitp_v5_record_evidence","tool_input":{"claim_id":"claim-fqhe","source_kind":"typed_records"}}',
        ]
    if template.startswith("adapter host-lifecycle"):
        return ["--command", "python", "--arg", "--version"]
    return None
