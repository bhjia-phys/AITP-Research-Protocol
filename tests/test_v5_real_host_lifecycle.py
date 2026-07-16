from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


def _seed_session(tmp_path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="Generated lifecycle hooks preserve the observed host boundary.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="host lifecycle behavior is characterization-only",
    )
    bind_session(
        ws,
        "s1",
        topic_id="librpa-gw",
        context_id="gw-methods",
        runtime="codex",
        active_claim=claim.claim_id,
    )
    return ws, claim


def _runtime_installation(runtime: str) -> dict:
    from brain.v5.adapter_protocols import build_adapter_protocols
    from brain.v5.hook_install_templates import build_runtime_hook_installation

    protocols = build_adapter_protocols()["runtime_hook_protocols"]
    return build_runtime_hook_installation(runtime, protocols)


def _install_real_host_owners(tmp_path) -> dict[str, dict]:
    from brain.v5.hook_codex_install import install_codex_hooks_json
    from brain.v5.hook_install_templates import install_claude_code_hook_settings
    from brain.v5.hook_kimi_install import install_kimi_code_hook_config
    from brain.v5.hook_opencode_install import install_opencode_plugin_file

    return {
        "claude_code": install_claude_code_hook_settings(
            tmp_path / ".claude" / "settings.local.json",
            _runtime_installation("claude_code"),
            workspace_base=str(tmp_path),
            session_id="s1",
        ),
        "kimi_code": install_kimi_code_hook_config(
            tmp_path / ".kimi" / "config.toml",
            _runtime_installation("kimi_code"),
            workspace_base=str(tmp_path),
            session_id="s1",
        ),
        "codex": install_codex_hooks_json(
            tmp_path / ".codex" / "hooks.json",
            _runtime_installation("codex"),
            workspace_base=str(tmp_path),
            session_id="s1",
        ),
        "opencode": install_opencode_plugin_file(
            tmp_path / ".opencode" / "plugins" / "aitp-v5.js",
            _runtime_installation("opencode"),
            workspace_base=str(tmp_path),
            session_id="s1",
        ),
    }


def _owner_event(payload: dict, event_name: str) -> dict:
    for event in payload["events"]:
        if event["hook_event_name"] == event_name:
            return event
    raise AssertionError(f"missing generated owner event {event_name!r}")


def _codex_command(payload: dict, event_name: str) -> str:
    event = payload["hooks"]["hooks"][event_name][0]
    return event["hooks"][0]["command"]


def _run_generated_command(command: str, event: dict, cwd: Path):
    return subprocess.run(
        command,
        cwd=cwd,
        input=json.dumps(event),
        capture_output=True,
        encoding="utf-8",
        shell=True,
        check=False,
    )


def test_matrix_characterizes_generated_events_from_current_owner_apis(tmp_path):
    from brain.v5.host_lifecycle_facade import host_lifecycle_capability_matrix

    _seed_session(tmp_path)
    owners = _install_real_host_owners(tmp_path)
    matrix = host_lifecycle_capability_matrix()

    claude_events = [
        (event["protocol_hook"], event["hook_event_name"], event["matcher"])
        for event in owners["claude_code"]["events"]
    ]
    kimi_events = [
        (event["protocol_hook"], event["hook_event_name"], event["matcher"])
        for event in owners["kimi_code"]["events"]
    ]
    codex_events = list(owners["codex"]["hooks"]["hooks"])
    opencode_plugin = owners["opencode"]["plugin"]

    assert claude_events == [
        ("session_start", "SessionStart", "startup|resume"),
        ("pre_tool", "PreToolUse", "*"),
        ("post_tool", "PostToolUse", "*"),
    ]
    assert kimi_events == claude_events
    assert codex_events == ["PreToolUse", "PostToolUse"]
    assert opencode_plugin["lifecycle_events"] == ["tool.execute.before", "tool.execute.after"]
    assert opencode_plugin["pre_tool"]["lifecycle_event"] == "pre_tool"
    assert opencode_plugin["post_tool"]["lifecycle_event"] == "post_tool"

    assert [
        (event.logical_event, event.native_event)
        for event in matrix.hosts["claude_code"].automatic_events
    ] == [(logical, native) for logical, native, _ in claude_events]
    assert [
        (event.logical_event, event.native_event)
        for event in matrix.hosts["kimi_code"].automatic_events
    ] == [(logical, native) for logical, native, _ in kimi_events]
    assert [
        (event.logical_event, event.native_event)
        for event in matrix.hosts["codex"].automatic_events
    ] == [("pre_tool", "PreToolUse"), ("post_tool", "PostToolUse")]
    assert [
        (event.logical_event, event.native_event)
        for event in matrix.hosts["opencode"].automatic_events
    ] == [("pre_tool", "tool.execute.before"), ("post_tool", "tool.execute.after")]

    assert matrix.hosts["opencode"].legacy_injection_conflicts == (
        "experimental.chat.system.transform: stale full-skill injection; not a lifecycle start capability",
    )
    assert all("session_end" not in {event.logical_event for event in host.automatic_events} for host in matrix.hosts.values())


def test_generated_owner_behavior_matches_output_trace_failure_and_timeout_contracts(tmp_path):
    from brain.v5.host_lifecycle_facade import host_lifecycle_capability
    from brain.v5.trace import read_trace_events

    _, claim = _seed_session(tmp_path)
    owners = _install_real_host_owners(tmp_path)

    claude_start = _run_generated_command(
        _owner_event(owners["claude_code"], "SessionStart")["command"],
        {"source": "startup"},
        tmp_path,
    )
    assert claude_start.returncode == 0, claude_start.stderr
    assert json.loads(claude_start.stdout)["suppressOutput"] is True

    kimi_post = _run_generated_command(
        _owner_event(owners["kimi_code"], "PostToolUse")["command"],
        {"tool": {"name": "pytest"}, "result": {"status": "completed", "exit_code": 0}},
        tmp_path,
    )
    assert kimi_post.returncode == 0, kimi_post.stderr
    assert json.loads(kimi_post.stdout)["aitp"]["kind"] == "hook_trace_event_record"

    codex_pre = _run_generated_command(
        _codex_command(owners["codex"], "PreToolUse"),
        {
            "tool_name": "mcp__aitp__aitp_v5_record_evidence",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "source_kind": "findings",
                "orientation_only": True,
            },
        },
        tmp_path,
    )
    assert codex_pre.returncode == 2, codex_pre.stderr
    assert json.loads(codex_pre.stdout)["runtime_event"]["runtime"] == "codex"

    codex_post = _run_generated_command(
        _codex_command(owners["codex"], "PostToolUse"),
        {"tool_name": "pytest", "evidence_status": "supports", "risk_level": "guided"},
        tmp_path,
    )
    assert codex_post.returncode == 0, codex_post.stderr
    assert json.loads(codex_post.stdout)["kind"] == "hook_trace_event_record"

    opencode = owners["opencode"]["plugin"]
    assert opencode["pre_tool"]["output_kind"] == "pre_tool_policy_decision"
    assert opencode["pre_tool"]["may_block"] is True
    assert opencode["post_tool"]["output_kind"] == "hook_trace_event_record"
    assert opencode["post_tool"]["may_block"] is False
    assert "timeout" not in opencode["pre_tool"]
    assert "timeout" not in opencode["post_tool"]

    (tmp_path / "package.json").write_text('{"type":"module"}\n', encoding="utf-8")
    driver = tmp_path / "opencode-lifecycle.mjs"
    driver.write_text(
        """
import { pathToFileURL } from "node:url"

const mod = await import(pathToFileURL(process.argv[2]).href)
const hooks = await mod.AITPV5Plugin()
let preToolBlocked = false
try {
  await hooks["tool.execute.before"]({
    tool: {
      name: "mcp__aitp__aitp_v5_record_evidence",
      input: { topic_id: "librpa-gw", claim_id: process.argv[3], source_kind: "findings", orientation_only: true }
    }
  }, {})
} catch (_) {
  preToolBlocked = true
}
const cycle = {}
cycle.self = cycle
let postToolSuppressed = true
try {
  await hooks["tool.execute.after"]({ tool: { name: "pytest" }, args: cycle }, {})
} catch (_) {
  postToolSuppressed = false
}
console.log(JSON.stringify({ preToolBlocked, postToolSuppressed }))
""".lstrip(),
        encoding="utf-8",
    )
    opencode_result = subprocess.run(
        ["node", str(driver), owners["opencode"]["plugin_path"], claim.claim_id],
        capture_output=True,
        encoding="utf-8",
        check=False,
    )
    assert opencode_result.returncode == 0, opencode_result.stderr
    assert json.loads(opencode_result.stdout) == {"preToolBlocked": True, "postToolSuppressed": True}

    trace_events = read_trace_events(tmp_path / ".aitp" / "runtime" / "hook_trace_events.jsonl")
    assert [event.payload["tool_name"] for event in trace_events] == ["pytest", "pytest"]

    claude = host_lifecycle_capability("claude_code")
    kimi = host_lifecycle_capability("kimi_code")
    codex = host_lifecycle_capability("codex")
    open_code = host_lifecycle_capability("opencode")
    assert claude.event("session_start").output_contract == "suppressed_continue_with_compact_workspace_refresh"
    assert kimi.event("post_tool").trace_contract == "append_hook_trace_event"
    assert codex.event("pre_tool").failure_contract == "hook_failure_propagates_to_host"
    assert open_code.event("pre_tool").failure_contract == "nonzero_or_block_throws_to_host"
    assert open_code.event("post_tool").failure_contract == "failure_is_logged_and_suppressed"
    assert all(
        event.timeout_contract == "no_owner_timeout"
        for host in (claude, kimi, codex, open_code)
        for event in host.automatic_events
    )


def test_fallback_descriptors_bind_unsupported_events_to_nonautomatic_boundaries():
    from brain.v5.host_lifecycle_facade import HostLifecycleFallbackDescriptor, host_lifecycle_capability_matrix

    matrix = host_lifecycle_capability_matrix()
    expected = {
        "claude_code": (("session_end", "plan_session_closeout", "human_review_required", "plan_only"),),
        "kimi_code": (("session_end", "plan_session_closeout", "human_review_required", "plan_only"),),
        "codex": (
            ("prompt_submit", "aitp_v5_codex_enter", "read_only", "read_only"),
            ("session_end", "plan_session_closeout", "human_review_required", "plan_only"),
        ),
        "opencode": (("session_end", "plan_session_closeout", "human_review_required", "plan_only"),),
    }

    for host_name, expected_fallbacks in expected.items():
        fallbacks = matrix.hosts[host_name].fallbacks
        assert all(isinstance(fallback, HostLifecycleFallbackDescriptor) for fallback in fallbacks)
        assert [
            (
                fallback.unsupported_event,
                fallback.operation,
                fallback.review_boundary,
                fallback.application_boundary,
            )
            for fallback in fallbacks
        ] == list(expected_fallbacks)
        assert all(fallback.automatic is False for fallback in fallbacks)
        assert all(fallback.unsupported_event in matrix.hosts[host_name].unsupported_events for fallback in fallbacks)

    assert all(
        fallback.operation != "apply_session_closeout"
        for host in matrix.hosts.values()
        for fallback in host.fallbacks
    )


@pytest.mark.parametrize("host", [None, "", [], {}])
def test_host_lifecycle_capability_rejects_invalid_host_values_with_stable_value_error(host):
    from brain.v5.host_lifecycle_facade import host_lifecycle_capability

    with pytest.raises(ValueError, match=r"^unsupported host: "):
        host_lifecycle_capability(host)
