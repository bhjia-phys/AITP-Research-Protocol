from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _seed_session(tmp_path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw-methods", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The modified self-energy kernel preserves the Si GW benchmark invariant.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="formula-code translation may be wrong",
    )
    bind_session(
        ws,
        "s1",
        topic_id="librpa-gw",
        context_id="gw-methods",
        runtime="codex",
        active_claim=claim.claim_id,
    )
    return claim


def _write_codex_bridge(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_write_codex_hook_bridge

    return aitp_v5_write_codex_hook_bridge(
        str(tmp_path),
        session_id="s1",
        output_path=str(tmp_path / "codex" / "AITP_V5_HOOK_BRIDGE.md"),
    )


def _run_fixture_hook(hook, event):
    argv = list(hook["argv"])
    argv[0] = sys.executable
    return subprocess.run(
        argv,
        cwd=hook["cwd"],
        input=json.dumps(event),
        capture_output=True,
        encoding="utf-8",
        check=False,
    )


def _codex_native_command(installation, event_name):
    event_hooks = installation["hooks"]["hooks"][event_name]
    for event_hook in event_hooks:
        for hook in event_hook["hooks"]:
            if hook["type"] == "command":
                return hook["command"]
    raise AssertionError(f"missing Codex native command for {event_name}")


def _run_codex_native_command(command, event, cwd):
    return subprocess.run(
        command,
        cwd=cwd,
        input=json.dumps(event),
        capture_output=True,
        encoding="utf-8",
        shell=True,
        check=False,
    )


def _run_node_script(script_path, *args):
    return subprocess.run(
        ["node", str(script_path), *[str(arg) for arg in args]],
        capture_output=True,
        encoding="utf-8",
        check=False,
    )


def test_adapter_event_runner_reads_stdin_and_uses_bridge_sidecar(tmp_path):
    claim = _seed_session(tmp_path)
    bridge = _write_codex_bridge(tmp_path)
    script = Path(__file__).resolve().parents[1] / "hooks" / "aitp_v5_adapter_event_runner.py"

    event = {
        "tool_name": "mcp__aitp__aitp_v5_record_evidence",
        "tool_input": {
            "topic_id": "librpa-gw",
            "claim_id": claim.claim_id,
            "source_kind": "findings",
            "orientation_only": True,
        },
    }
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "pre-tool",
            "--base",
            str(tmp_path),
            "--runtime",
            "codex",
            "--session-id",
            "s1",
            "--bridge-path",
            bridge["payload_path"],
        ],
        input=json.dumps(event),
        capture_output=True,
        encoding="utf-8",
        check=False,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 2
    assert payload["ok"] is True
    assert payload["kind"] == "hook_decision"
    assert payload["action"] == "record_evidence"
    assert payload["block"] is True
    assert payload["runtime_event"]["runtime"] == "codex"
    assert payload["runtime_event"]["platform_event"] == "codex_pre_tool"
    assert payload["runtime_event"]["tool_name"] == "mcp__aitp__aitp_v5_record_evidence"
    assert payload["policy_reasons"][0]["policy_id"] == "no_summary_surface_as_truth_source"


def test_codex_install_fixture_runner_executes_from_declared_cwd(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_install_codex_hook_fixture

    claim = _seed_session(tmp_path)
    fixture_path = tmp_path / ".codex" / "AITP_V5_HOOKS.json"
    installation = aitp_v5_install_codex_hook_fixture(
        str(tmp_path),
        session_id="s1",
        output_path=str(fixture_path),
    )
    hook = installation["fixture"]["hooks"]["pre_tool"]

    result = _run_fixture_hook(
        hook,
        {
            "tool_name": "mcp__aitp__aitp_v5_record_evidence",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "source_kind": "findings",
                "orientation_only": True,
            },
        },
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 2
    assert payload["ok"] is True
    assert payload["runtime_event"]["runtime"] == "codex"
    assert payload["policy_reasons"][0]["policy_id"] == "no_summary_surface_as_truth_source"


def test_opencode_install_fixture_runner_executes_from_declared_cwd(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_install_opencode_hook_fixture

    claim = _seed_session(tmp_path)
    fixture_path = tmp_path / ".opencode" / "AITP_V5_PLUGIN_HOOKS.json"
    installation = aitp_v5_install_opencode_hook_fixture(
        str(tmp_path),
        session_id="s1",
        output_path=str(fixture_path),
    )
    hook = installation["fixture"]["plugin_hooks"]["pre_tool"]

    result = _run_fixture_hook(
        hook,
        {
            "tool_name": "mcp__aitp__aitp_v5_record_evidence",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "source_kind": "findings",
                "orientation_only": True,
            },
        },
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 2
    assert payload["ok"] is True
    assert payload["runtime_event"]["runtime"] == "opencode"
    assert payload["policy_reasons"][0]["policy_id"] == "no_summary_surface_as_truth_source"


def test_opencode_local_plugin_runner_argv_is_cwd_independent(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_install_opencode_hook_fixture

    _seed_session(tmp_path)
    plugin_path = tmp_path / ".opencode" / "plugins" / "aitp-v5.js"
    installation = aitp_v5_install_opencode_hook_fixture(
        str(tmp_path),
        session_id="s1",
        plugin_path=str(plugin_path),
    )

    for hook_name in ("pre_tool", "post_tool"):
        argv = installation["plugin"][hook_name]["argv"]
        assert argv[0] == sys.executable
        assert Path(argv[1]).is_absolute()
        assert Path(argv[1]).name == "aitp_v5_adapter_event_runner.py"


def test_opencode_local_plugin_lifecycle_smoke_executes_generated_plugin(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_install_opencode_hook_fixture
    from brain.v5.trace import read_trace_events

    claim = _seed_session(tmp_path)
    plugin_path = tmp_path / ".opencode" / "plugins" / "aitp-v5.js"
    installation = aitp_v5_install_opencode_hook_fixture(
        str(tmp_path),
        session_id="s1",
        plugin_path=str(plugin_path),
    )
    assert installation["plugin"]["pre_tool"]["argv"][0] == sys.executable

    (tmp_path / "package.json").write_text('{"type":"module"}\n', encoding="utf-8")
    driver = tmp_path / "opencode-plugin-smoke.mjs"
    driver.write_text(
        """
import { pathToFileURL } from "node:url"

const pluginPath = process.argv[2]
const mod = await import(pathToFileURL(pluginPath).href)
const hooks = await mod.AITPV5Plugin()

let beforeBlocked = false
let beforeMessage = ""
try {
  await hooks["tool.execute.before"]({
    tool: {
      name: "mcp__aitp__aitp_v5_record_evidence",
      input: {
        topic_id: "librpa-gw",
        claim_id: process.argv[3],
        source_kind: "findings",
        orientation_only: true
      }
    }
  }, {})
} catch (error) {
  beforeBlocked = true
  beforeMessage = error.message
}

await hooks["tool.execute.after"]({
  tool: { name: "pytest" },
  args: {},
}, {
  status: "supports",
})

console.log(JSON.stringify({ beforeBlocked, beforeMessage }))
""".lstrip(),
        encoding="utf-8",
    )

    result = _run_node_script(driver, plugin_path, claim.claim_id)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["beforeBlocked"] is True
    assert payload["beforeMessage"]

    events = read_trace_events(tmp_path / ".aitp" / "runtime" / "hook_trace_events.jsonl")
    assert len(events) == 1
    assert events[0].session_id == "s1"
    assert events[0].topic_id == "librpa-gw"
    assert events[0].claim_id == claim.claim_id
    assert events[0].payload["tool_name"] == "pytest"


def test_codex_native_hooks_json_pre_tool_command_executes_from_workspace_cwd(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_install_codex_hook_fixture

    claim = _seed_session(tmp_path)
    hooks_path = tmp_path / ".codex" / "hooks.json"
    installation = aitp_v5_install_codex_hook_fixture(
        str(tmp_path),
        session_id="s1",
        hooks_path=str(hooks_path),
    )
    command = _codex_native_command(installation, "PreToolUse")

    result = _run_codex_native_command(
        command,
        {
            "tool_name": "mcp__aitp__aitp_v5_record_evidence",
            "tool_input": {
                "topic_id": "librpa-gw",
                "claim_id": claim.claim_id,
                "source_kind": "findings",
                "orientation_only": True,
            },
        },
        cwd=tmp_path,
    )

    assert result.stdout, result.stderr
    payload = json.loads(result.stdout)
    assert result.returncode == 2
    assert payload["ok"] is True
    assert payload["runtime_event"]["runtime"] == "codex"
    assert payload["policy_reasons"][0]["policy_id"] == "no_summary_surface_as_truth_source"


def test_codex_native_hooks_json_post_tool_command_executes_from_workspace_cwd(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_install_codex_hook_fixture
    from brain.v5.trace import read_trace_events

    claim = _seed_session(tmp_path)
    hooks_path = tmp_path / ".codex" / "hooks.json"
    installation = aitp_v5_install_codex_hook_fixture(
        str(tmp_path),
        session_id="s1",
        hooks_path=str(hooks_path),
    )
    command = _codex_native_command(installation, "PostToolUse")

    result = _run_codex_native_command(
        command,
        {
            "tool_name": "pytest",
            "evidence_status": "supports",
            "risk_level": "guided",
        },
        cwd=tmp_path,
    )

    assert result.stdout, result.stderr
    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["ok"] is True
    assert payload["kind"] == "hook_trace_event_record"

    events = read_trace_events(payload["trace_path"])
    assert len(events) == 1
    assert events[0].session_id == "s1"
    assert events[0].topic_id == "librpa-gw"
    assert events[0].claim_id == claim.claim_id
    assert events[0].payload["tool_name"] == "pytest"
    assert events[0].payload["evidence_status"] == "supports"


def test_codex_install_fixture_post_tool_runner_persists_trace_event(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_install_codex_hook_fixture
    from brain.v5.trace import read_trace_events

    claim = _seed_session(tmp_path)
    fixture_path = tmp_path / ".codex" / "AITP_V5_HOOKS.json"
    installation = aitp_v5_install_codex_hook_fixture(
        str(tmp_path),
        session_id="s1",
        output_path=str(fixture_path),
    )
    hook = installation["fixture"]["hooks"]["post_tool"]

    result = _run_fixture_hook(
        hook,
        {
            "tool_name": "pytest",
            "evidence_status": "supports",
            "risk_level": "guided",
        },
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["ok"] is True
    assert payload["kind"] == "hook_trace_event_record"
    assert payload["source_hook"] == "post_tool"
    assert payload["summary_inputs_trusted"] is False
    assert payload["can_update_claim_trust"] is False
    assert payload["trace_path"].replace("\\", "/").endswith(".aitp/runtime/hook_trace_events.jsonl")

    events = read_trace_events(payload["trace_path"])
    assert len(events) == 1
    assert events[0].session_id == "s1"
    assert events[0].topic_id == "librpa-gw"
    assert events[0].claim_id == claim.claim_id
    assert events[0].payload["tool_name"] == "pytest"
    assert events[0].payload["evidence_status"] == "supports"


def test_opencode_install_fixture_post_tool_runner_persists_trace_event(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_install_opencode_hook_fixture
    from brain.v5.trace import read_trace_events

    claim = _seed_session(tmp_path)
    fixture_path = tmp_path / ".opencode" / "AITP_V5_PLUGIN_HOOKS.json"
    installation = aitp_v5_install_opencode_hook_fixture(
        str(tmp_path),
        session_id="s1",
        output_path=str(fixture_path),
    )
    hook = installation["fixture"]["plugin_hooks"]["post_tool"]

    result = _run_fixture_hook(
        hook,
        {
            "tool": {"name": "pytest"},
            "status": "supports",
            "risk_level": "guided",
        },
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["ok"] is True
    assert payload["kind"] == "hook_trace_event_record"
    assert payload["source_hook"] == "post_tool"

    events = read_trace_events(payload["trace_path"])
    assert len(events) == 1
    assert events[0].session_id == "s1"
    assert events[0].topic_id == "librpa-gw"
    assert events[0].claim_id == claim.claim_id
    assert events[0].payload["tool_name"] == "pytest"
    assert events[0].payload["evidence_status"] == "supports"
