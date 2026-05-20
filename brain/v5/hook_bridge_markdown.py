"""Markdown renderers for generated AITP v5 hook bridges."""

from __future__ import annotations

from typing import Any


def codex_bridge_markdown(bridge: dict[str, Any]) -> str:
    lines = [
        "# AITP v5 Codex Hook Bridge",
        "",
        "Generated from `runtime_hook_installation`.",
        "",
        "- truth_source: false",
        "- summary_inputs_trusted=false",
        "- can_update_kernel_state=false",
        "",
        *_shared_pre_tool_policy_lines(),
        *_adapter_pre_tool_event_lines(
            runner=bridge["pre_tool_event_runner"],
            entrypoint=bridge["pre_tool_event_entrypoint"],
        ),
        *_gate_protocol_lines(bridge["gate_protocols"]),
        "## Guard Calls",
        "",
    ]
    for guard_call in bridge["guard_calls"]:
        lines.extend(
            [
                f"### {guard_call['hook_name']}",
                "",
                f"- when: {guard_call['when']}",
                f"- output_kind: `{guard_call['output_kind']}`",
                f"- may_block: `{str(guard_call['may_block']).lower()}`",
                f"- state_mutation: `{guard_call['state_mutation']}`",
                "",
                "```powershell",
                guard_call["command"],
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def opencode_bridge_markdown(bridge: dict[str, Any]) -> str:
    plugin_bridge = bridge["plugin_bridge"]
    lines = [
        "# AITP v5 OpenCode Plugin Bridge",
        "",
        "Generated from `runtime_hook_installation`.",
        "",
        "- truth_source: false",
        "- summary_inputs_trusted=false",
        "- can_update_kernel_state=false",
        "- can_update_claim_trust=false",
        "",
        *_shared_pre_tool_policy_lines(),
        *_adapter_pre_tool_event_lines(
            runner=plugin_bridge["pre_tool_event_runner"],
            entrypoint=plugin_bridge["pre_tool_event_entrypoint"],
        ),
        *_gate_protocol_lines(plugin_bridge["gate_protocols"]),
        "## Lifecycle Calls",
        "",
    ]
    for call in plugin_bridge["lifecycle_calls"]:
        lines.extend(
            [
                f"### {call['hook_name']}",
                "",
                f"- lifecycle_event: `{call['lifecycle_event']}`",
                f"- output_kind: `{call['output_kind']}`",
                f"- may_block: `{str(call['may_block']).lower()}`",
                f"- state_mutation: `{call['state_mutation']}`",
                "",
                "```powershell",
                call["command"],
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Persistence",
            "",
            "Persist post-tool trace events through `aitp_v5_persist_hook_trace_event` only.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _shared_pre_tool_policy_lines() -> list[str]:
    return [
        "## Shared Context Pre-Tool Policy",
        "",
        "Use `aitp-v5 policy pre-tool <args>` before trust-changing actions that depend on typed claim, evidence, source, or code-state context.",
        "",
        "- surface: `pre_tool_policy_decision`",
        "- mcp: `aitp_v5_evaluate_pre_tool_policy`",
        "- truth_source: `typed_records`",
        "- can_update_kernel_state=false",
        "- can_update_claim_trust=false",
        "- required inputs: `session_id`, `action`, `claim_id`, `risk_level`",
        "- optional inputs include: `evidence_refs`, `code_state_ids`, `source_kind`, `source_ref`, `orientation_only`, `human_checkpoint_id`",
        "",
    ]


def _adapter_pre_tool_event_lines(*, runner: dict[str, Any], entrypoint: dict[str, Any]) -> list[str]:
    return [
        "## Adapter Pre-Tool Event",
        "",
        "Use the generated sidecar runner to normalize live platform events through the shared policy path.",
        "",
        f"- bridge_payload_source: `{runner['bridge_payload_source']}`",
        f"- mcp: `{entrypoint['mcp']}`",
        f"- surface: `{entrypoint['surface']}`",
        "- platform event optional tool inputs include: `claim_id`, `evidence_refs`, `code_state_ids`, `source_kind`, `source_ref`, `orientation_only`, `risk_level`, `human_checkpoint_id`",
        "",
        "```powershell",
        _command_string(runner["argv"]),
        "```",
        "",
        "Host hooks that provide the platform event on stdin can call:",
        "",
        "```powershell",
        _command_string(runner["stdin_runner"]["argv"]),
        "```",
        "",
    ]


def _gate_protocol_lines(gate_protocols: dict[str, Any]) -> list[str]:
    lines = ["## Gate Protocols", ""]
    for action in _gate_protocol_actions(gate_protocols):
        protocol = gate_protocols.get(action, {})
        lines.extend(
            [
                f"### {action}",
                "",
                "Generated from `runtime_gate_protocols` in the adapter packet.",
                "",
                f"- pre_tool_policy: `{protocol.get('pre_tool_policy', '')}`",
                f"- policy_reasons_field: `{protocol.get('policy_reasons_field', '')}`",
                f"- sequence: `{', '.join(protocol.get('sequence', []))}`",
                "",
            ]
        )
    return lines


def _gate_protocol_actions(gate_protocols: dict[str, Any]) -> list[str]:
    return [action for action in gate_protocols if action != "source_protocol_field"]


def _command_string(command: list[str]) -> str:
    return " ".join(command)
