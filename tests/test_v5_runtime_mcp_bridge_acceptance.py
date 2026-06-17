from __future__ import annotations

import json


def _tool_names(manifest):
    return sorted(
        {
            target["mcp_tool"]
            for target in manifest["targets"]
        }
        | {"aitp_v5_get_runtime_bridge_target_manifest"}
    )


def test_runtime_mcp_bridge_acceptance_expected_contract_only():
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.runtime_mcp_bridge_acceptance import audit_runtime_mcp_bridge_acceptance

    payload = audit_runtime_mcp_bridge_acceptance()
    validated = require_valid_public_surface("runtime_mcp_bridge_acceptance", payload)

    assert validated["status"] == "expected_contract_only"
    assert validated["expected"]["target_count"] == 35
    assert validated["live"]["manifest_provided"] is False
    assert validated["live"]["tools_provided"] is False
    assert validated["comparison"]["manifest_checked"] is False
    assert validated["comparison"]["tools_checked"] is False
    assert validated["comparison"]["missing_operations"] == []
    assert validated["comparison"]["missing_mcp_tools"] == []
    assert validated["comparison"]["recording_navigator_tools_missing"] == []
    assert validated["next_actions"] == ["call_live_mcp_manifest_and_tools_list_then_rerun_acceptance"]
    assert validated["summary_inputs_trusted"] is False
    assert validated["can_update_kernel_state"] is False
    assert validated["can_update_claim_trust"] is False


def test_runtime_mcp_bridge_acceptance_accepts_current_manifest_and_tools():
    from brain.v5.runtime_bridge_targets import runtime_bridge_target_manifest
    from brain.v5.runtime_mcp_bridge_acceptance import audit_runtime_mcp_bridge_acceptance

    manifest = runtime_bridge_target_manifest()
    payload = audit_runtime_mcp_bridge_acceptance(
        live_manifest={"ok": True, "runtime_bridge_target_manifest": manifest},
        live_tool_names=[{"name": name} for name in _tool_names(manifest)],
    )

    assert payload["status"] == "accepted"
    assert payload["comparison"]["target_count_matches"] is True
    assert payload["comparison"]["missing_operations"] == []
    assert payload["comparison"]["missing_mcp_tools"] == []
    assert payload["comparison"]["recording_navigator_tools_missing"] == []
    assert payload["next_actions"] == ["host_mcp_bridge_exposure_accepted"]


def test_runtime_mcp_bridge_acceptance_flags_stale_recording_navigator_exposure():
    from brain.v5.runtime_bridge_targets import runtime_bridge_target_manifest
    from brain.v5.runtime_mcp_bridge_acceptance import audit_runtime_mcp_bridge_acceptance

    manifest = runtime_bridge_target_manifest()
    stale_targets = [
        target
        for target in manifest["targets"]
        if target["operation"] not in {
            "readWorkspaceRecordingAudit",
            "classifyRecordingCandidate",
            "readRecordingNavigationState",
            "expandRecordingSlot",
            "verifyRecordingEffect",
        }
    ]
    stale_manifest = {
        **manifest,
        "target_count": len(stale_targets),
        "targets": stale_targets,
    }
    stale_tool_names = [
        name
        for name in _tool_names(manifest)
        if name
        not in {
            "aitp_v5_build_workspace_recording_audit",
            "aitp_v5_classify_recording_candidate",
            "aitp_v5_get_recording_navigation_state",
            "aitp_v5_expand_recording_slot",
            "aitp_v5_verify_recording_effect",
        }
    ]

    payload = audit_runtime_mcp_bridge_acceptance(
        live_manifest=stale_manifest,
        live_tool_names=stale_tool_names,
    )

    assert payload["status"] == "stale_or_incomplete"
    assert payload["live"]["target_count"] == 30
    assert payload["comparison"]["target_count_matches"] is False
    assert payload["comparison"]["missing_operations"] == [
        "classifyRecordingCandidate",
        "expandRecordingSlot",
        "readRecordingNavigationState",
        "readWorkspaceRecordingAudit",
        "verifyRecordingEffect",
    ]
    assert payload["comparison"]["recording_navigator_tools_missing"] == [
        "aitp_v5_build_workspace_recording_audit",
        "aitp_v5_classify_recording_candidate",
        "aitp_v5_get_recording_navigation_state",
        "aitp_v5_expand_recording_slot",
        "aitp_v5_verify_recording_effect",
    ]
    assert "restart_or_refresh_host_mcp_session" in payload["next_actions"]
    assert "verify_host_reimported_latest_native_mcp_server" in payload["next_actions"]


def test_runtime_mcp_bridge_acceptance_cli_and_mcp(capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_audit_runtime_mcp_bridge_acceptance
    from brain.v5.runtime_bridge_targets import runtime_bridge_target_manifest

    manifest = runtime_bridge_target_manifest()
    tools = {"tools": [{"name": name} for name in _tool_names(manifest)]}

    assert main(
        [
            "adapter",
            "bridge-acceptance",
            "--live-manifest-json",
            json.dumps({"runtime_bridge_target_manifest": manifest}),
            "--live-tools-json",
            json.dumps(tools),
        ]
    ) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_audit_runtime_mcp_bridge_acceptance(
        live_manifest={"runtime_bridge_target_manifest": manifest},
        live_tool_names=tools,
    )

    assert cli_payload["runtime_mcp_bridge_acceptance"]["status"] == "accepted"
    assert mcp_payload["runtime_mcp_bridge_acceptance"]["status"] == "accepted"
