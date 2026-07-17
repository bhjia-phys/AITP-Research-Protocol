from __future__ import annotations

from pathlib import Path

import pytest


def _opencode_installation():
    from brain.v5.adapter_protocols import build_adapter_protocols
    from brain.v5.hook_install_templates import build_runtime_hook_installation

    protocols = build_adapter_protocols()["runtime_hook_protocols"]
    return build_runtime_hook_installation("opencode", protocols)


def _seed_session(tmp_path):
    from brain.v5.workspace import bind_session, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    bind_session(
        ws,
        "s1",
        topic_id="librpa-gw",
        context_id="gw-methods",
        runtime="opencode",
    )
    return ws


def _stale_plugin_text(workspace_base: Path, *, marker: bool = True) -> str:
    prefix = "// AITP_V5_OPENCODE_PLUGIN\n" if marker else ""
    return prefix + f"""
// tool.execute.before aitp_v5_adapter_event_runner.py pre-tool --bridge-path {workspace_base}
// tool.execute.after aitp_v5_adapter_event_runner.py post-tool {workspace_base}
const gateway = fs.readFileSync(GATEWAY_SKILL, 'utf8')
export const plugin = {{
  'experimental.chat.system.transform': async (_input, output) => {{
    output.system.push('Below is the full content of your using-aitp skill')
  }},
}}
"""


def test_repository_opencode_template_registers_skills_without_full_context_injection():
    path = Path("deploy/templates/opencode/aitp-plugin.js")
    text = path.read_text(encoding="utf-8")

    assert "AITP 1.0.0 v5 adapter" in text
    assert "aitp_v5_get_execution_brief" in text
    assert "aitp_v5_build_workspace_recovery_audit" in text
    assert "experimental.chat.system.transform" not in text
    assert "full content of your using-aitp skill" not in text
    assert "Runtime skill content (auto-injected)" not in text
    assert "readFileSync(GATEWAY_SKILL" not in text


def test_legacy_injection_detector_builds_content_bound_review_plan(tmp_path):
    from brain.v5.legacy_injection_quarantine import (
        build_legacy_injection_replacement_plan,
        detect_legacy_injection_conflicts,
    )

    plugin_path = tmp_path / ".opencode" / "plugins" / "aitp-v5.js"
    plugin_path.parent.mkdir(parents=True)
    plugin_path.write_text(_stale_plugin_text(tmp_path), encoding="utf-8")

    conflicts = detect_legacy_injection_conflicts(plugin_path.read_text(encoding="utf-8"))
    plan = build_legacy_injection_replacement_plan(plugin_path, runtime="opencode")

    assert conflicts == (
        "full_skill_system_injection",
        "gateway_skill_file_injection",
    )
    assert plan["kind"] == "reviewed_host_install_replacement_plan"
    assert plan["runtime"] == "opencode"
    assert plan["target_path"] == str(plugin_path.resolve())
    assert plan["conflicts"] == list(conflicts)
    assert plan["plan_id"].startswith("host-install-plan-")
    assert len(plan["current_content_sha256"]) == 64
    assert plan["operation"] == "replace_legacy_injection_with_bounded_host_configuration"
    assert plan["automatic_apply"] is False
    assert plan["human_review_required"] is True
    assert plan["can_update_kernel_state"] is False
    assert plan["can_update_claim_trust"] is False
    assert detect_legacy_injection_conflicts(
        "const gateway = fs.readFileSync(GATEWAY_SKILL, 'utf8')"
    ) == ()


def test_detector_covers_complete_memory_and_legacy_stage_guidance_injection():
    from brain.v5.legacy_injection_quarantine import detect_legacy_injection_conflicts

    conflicts = detect_legacy_injection_conflicts(
        "experimental.chat.system.transform readFileSync('MEMORY.md') L0-L4"
    )

    assert conflicts == (
        "complete_memory_body_injection",
        "legacy_stage_guidance_injection",
    )


def test_install_audit_reports_legacy_injection_conflict_and_review_plan(tmp_path):
    from brain.v5.hook_install_audit import audit_hook_installation
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    plugin_path = tmp_path / ".opencode" / "plugins" / "aitp-v5.js"
    plugin_path.parent.mkdir(parents=True)
    plugin_path.write_text(_stale_plugin_text(tmp_path), encoding="utf-8")

    payload = audit_hook_installation(
        ws,
        runtime="opencode",
        plugin_path=str(plugin_path),
    )
    validated = require_valid_public_surface("runtime_hook_installation_audit", payload)

    assert validated["status"] == "conflict"
    assert validated["automatic_replacement_allowed"] is False
    finding = validated["findings"][0]
    assert finding["observed"] == [
        "tool.execute.before pre-tool runner",
        "tool.execute.after post-tool runner",
    ]
    assert finding["legacy_injection_conflicts"] == [
        "full_skill_system_injection",
        "gateway_skill_file_injection",
    ]
    assert finding["replacement_plan"]["human_review_required"] is True
    assert finding["replacement_plan"]["automatic_apply"] is False
    assert finding["replacement_plan"]["plan_id"] in validated["required_actions"][0]


def test_opencode_installer_requires_exact_review_plan_before_replacing_legacy_injection(
    tmp_path,
):
    from brain.v5.hook_opencode_install import install_opencode_plugin_file
    from brain.v5.legacy_injection_quarantine import build_legacy_injection_replacement_plan

    plugin_path = tmp_path / ".opencode" / "plugins" / "aitp-v5.js"
    plugin_path.parent.mkdir(parents=True)
    plugin_path.write_text(_stale_plugin_text(tmp_path), encoding="utf-8")
    bridge_path = tmp_path / ".opencode" / "AITP_V5_PLUGIN_BRIDGE.md"

    with pytest.raises(ValueError, match="reviewed host-install replacement plan"):
        install_opencode_plugin_file(
            plugin_path,
            _opencode_installation(),
            workspace_base=str(tmp_path),
            session_id="s1",
        )
    assert not bridge_path.exists()
    assert "experimental.chat.system.transform" in plugin_path.read_text(encoding="utf-8")

    plan = build_legacy_injection_replacement_plan(plugin_path, runtime="opencode")
    result = install_opencode_plugin_file(
        plugin_path,
        _opencode_installation(),
        workspace_base=str(tmp_path),
        session_id="s1",
        reviewed_replacement_plan_id=plan["plan_id"],
    )

    installed = plugin_path.read_text(encoding="utf-8")
    assert result["changed"] is True
    assert result["reviewed_replacement_plan_id"] == plan["plan_id"]
    assert "experimental.chat.system.transform" not in installed
    assert "tool.execute.before" in installed
    assert "tool.execute.after" in installed
    assert bridge_path.exists()


def test_opencode_installer_rejects_stale_or_wrong_replacement_plan_id(tmp_path):
    from brain.v5.hook_opencode_install import install_opencode_plugin_file

    plugin_path = tmp_path / ".opencode" / "plugins" / "aitp-v5.js"
    plugin_path.parent.mkdir(parents=True)
    plugin_path.write_text(_stale_plugin_text(tmp_path), encoding="utf-8")

    with pytest.raises(ValueError, match="does not match current legacy injection content"):
        install_opencode_plugin_file(
            plugin_path,
            _opencode_installation(),
            workspace_base=str(tmp_path),
            session_id="s1",
            reviewed_replacement_plan_id="host-install-plan-wrong",
        )


def test_full_cli_applies_only_the_exact_reviewed_opencode_replacement_plan(
    tmp_path, capsys
):
    import json

    from brain.v5.cli import main
    from brain.v5.legacy_injection_quarantine import build_legacy_injection_replacement_plan

    _seed_session(tmp_path)
    plugin_path = tmp_path / ".opencode" / "plugins" / "aitp-v5.js"
    plugin_path.parent.mkdir(parents=True)
    plugin_path.write_text(_stale_plugin_text(tmp_path), encoding="utf-8")
    plan = build_legacy_injection_replacement_plan(plugin_path, runtime="opencode")

    assert main(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "install-hooks",
            "opencode",
            "s1",
            "--plugin",
            str(plugin_path),
            "--reviewed-replacement-plan-id",
            plan["plan_id"],
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["ok"] is True
    assert payload["reviewed_replacement_plan_id"] == plan["plan_id"]
    assert "experimental.chat.system.transform" not in plugin_path.read_text(
        encoding="utf-8"
    )
