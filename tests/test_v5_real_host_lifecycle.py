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

    assert matrix.hosts["opencode"].legacy_injection_conflicts == ()
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
            (
                "prompt_submit",
                "aitp_v5_codex_enter",
                "read_only",
                "runtime_receipt_only",
            ),
            ("session_end", "plan_session_closeout", "human_review_required", "plan_only"),
        ),
        "opencode": (
            ("prompt_submit", "begin_research_turn", "read_only", "runtime_receipt_only"),
            ("session_end", "plan_session_closeout", "human_review_required", "plan_only"),
        ),
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


def test_normalized_host_event_uses_stable_identity_and_allowlisted_payload_only():
    from brain.v5.host_lifecycle_facade import normalize_host_lifecycle_event

    event = normalize_host_lifecycle_event(
        "claude_code",
        "SessionStart",
        {
            "event_id": "evt-start-1",
            "host_session_id": "claude-session-1",
            "occurred_at": "2026-07-16T12:00:00Z",
            "topic_id": "librpa-gw",
            "research_relevant": True,
            "context_profile": "startup_orientation",
            "objective_text": "Continue the verified GW workflow.",
            "user_goal": "Recover the exact prior calculation boundary.",
            "subject_refs": ["claim:claim-librpa"],
            "raw_prompt": "must not survive normalization",
            "tool_input": {"secret": "must not survive normalization"},
        },
        session_id="s1",
    )

    assert event.event_id == "evt-start-1"
    assert event.logical_event == "session_start"
    assert event.native_event == "SessionStart"
    assert event.host_session_id == "claude-session-1"
    assert event.session_id == "s1"
    assert event.topic_id == "librpa-gw"
    assert event.automatic is True
    assert event.origin == "host_native"
    assert event.subject_refs == ("claim:claim-librpa",)
    assert event.objective_payload == {
        "context_profile": "startup_orientation",
        "objective_text": "Continue the verified GW workflow.",
        "research_relevant": True,
        "user_goal": "Recover the exact prior calculation boundary.",
    }
    assert event.process_payload == {}
    assert "raw_prompt" not in repr(event)
    assert "secret" not in repr(event)


@pytest.mark.parametrize(
    ("host", "native_event"),
    [
        ("claude_code", "PostToolUse"),
        ("kimi_code", "PostToolUse"),
        ("codex", "PostToolUse"),
        ("opencode", "tool.execute.after"),
    ],
)
def test_automatic_post_tool_normalization_requires_stable_native_event_identity(host, native_event):
    from brain.v5.host_lifecycle_facade import normalize_host_lifecycle_event

    with pytest.raises(ValueError, match="stable event_id"):
        normalize_host_lifecycle_event(
            host,
            native_event,
            {
                "host_session_id": f"{host}-session",
                "tool_name": "pytest",
                "status": "completed",
            },
            session_id="s1",
        )


def test_explicit_first_turn_and_closeout_fallbacks_remain_nonautomatic():
    from brain.v5.host_lifecycle_facade import normalize_host_lifecycle_event

    codex_start = normalize_host_lifecycle_event(
        "codex",
        "aitp_v5_codex_enter",
        {
            "event_id": "evt-codex-enter-1",
            "host_session_id": "codex-session-1",
            "research_relevant": True,
        },
        session_id="s1",
    )
    closeout = normalize_host_lifecycle_event(
        "opencode",
        "plan_session_closeout",
        {
            "event_id": "evt-closeout-1",
            "host_session_id": "opencode-session-1",
        },
        session_id="s1",
    )

    assert (codex_start.logical_event, codex_start.automatic, codex_start.origin) == (
        "prompt_submit",
        False,
        "explicit_fallback",
    )
    assert (closeout.logical_event, closeout.automatic, closeout.origin) == (
        "session_end",
        False,
        "explicit_fallback",
    )


def test_begin_research_turn_requires_existing_binding_and_never_selects_a_topic(tmp_path, monkeypatch):
    from brain.v5.host_lifecycle_facade import begin_research_turn, normalize_host_lifecycle_event
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    event = normalize_host_lifecycle_event(
        "codex",
        "aitp_v5_codex_enter",
        {
            "event_id": "evt-unbound-1",
            "host_session_id": "codex-session-1",
            "topic_id": "librpa-gw",
            "research_relevant": True,
        },
        session_id="missing-session",
    )

    def fail_prepare(*args, **kwargs):
        raise AssertionError("unbound lifecycle event must not compile context")

    monkeypatch.setattr("brain.v5.host_lifecycle_dispatch.prepare_context_injection", fail_prepare)
    result = begin_research_turn(ws, event)

    assert result.status == "unbound_session"
    assert result.operation == "orientation_required"
    assert result.topic_id == ""
    assert result.reason_codes == ("session_binding_not_found",)
    assert result.receipt_id == ""
    assert result.canonical_write is False
    assert not ws.session_path("missing-session").exists()


def test_begin_research_turn_uses_bound_topic_and_ephemeral_delivery(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from brain.v5.host_lifecycle_facade import begin_research_turn, normalize_host_lifecycle_event
    from brain.v5.workspace import get_session_binding

    ws, _ = _seed_session(tmp_path)
    delivered = []
    captured = {}

    def prepare(ws_arg, request, *, deliver=None):
        captured["workspace"] = ws_arg
        captured["request"] = request
        if deliver is not None:
            deliver("bounded context body")
        return SimpleNamespace(receipt_id="ctx-receipt-1", injection_status="injected")

    monkeypatch.setattr("brain.v5.host_lifecycle_dispatch.prepare_context_injection", prepare)
    event = normalize_host_lifecycle_event(
        "claude_code",
        "SessionStart",
        {
            "event_id": "evt-bound-1",
            "host_session_id": "claude-session-1",
            "topic_id": "librpa-gw",
            "research_relevant": True,
            "context_profile": "startup_orientation",
            "objective_text": "Continue the verified GW workflow.",
        },
        session_id="s1",
    )
    before = get_session_binding(ws, "s1")

    result = begin_research_turn(ws, event, deliver_context=delivered.append)
    after = get_session_binding(ws, "s1")

    request = captured["request"]
    assert captured["workspace"] == ws
    assert request.event_id == "evt-bound-1"
    assert request.event_type == "SessionStart"
    assert request.host == "claude_code"
    assert request.host_session_id == "claude-session-1"
    assert request.session_id == "s1"
    assert request.topic_id == "librpa-gw"
    assert request.context_profile == "startup_orientation"
    assert request.host_supports_session_start is True
    assert delivered == ["bounded context body"]
    assert result.status == "context_injected"
    assert result.receipt_id == "ctx-receipt-1"
    assert "bounded context body" not in repr(result)
    assert before == after


def test_begin_research_turn_rejects_topic_mismatch_without_rebinding(tmp_path, monkeypatch):
    from brain.v5.host_lifecycle_facade import begin_research_turn, normalize_host_lifecycle_event
    from brain.v5.workspace import get_session_binding

    ws, _ = _seed_session(tmp_path)
    event = normalize_host_lifecycle_event(
        "claude_code",
        "SessionStart",
        {
            "event_id": "evt-topic-mismatch-1",
            "host_session_id": "claude-session-1",
            "topic_id": "another-topic",
            "research_relevant": True,
        },
        session_id="s1",
    )

    def fail_prepare(*args, **kwargs):
        raise AssertionError("mismatched topic must not compile context")

    monkeypatch.setattr("brain.v5.host_lifecycle_dispatch.prepare_context_injection", fail_prepare)
    result = begin_research_turn(ws, event)

    assert result.status == "binding_mismatch"
    assert result.reason_codes == ("event_topic_does_not_match_session_binding",)
    assert get_session_binding(ws, "s1").topic_id == "librpa-gw"


def test_codex_first_turn_prepares_real_bounded_receipt_without_canonical_change(tmp_path):
    from brain.v5.host_lifecycle_facade import begin_research_turn, normalize_host_lifecycle_event
    from brain.v5.query_index import current_canonical_watermark

    ws, _ = _seed_session(tmp_path)
    event = normalize_host_lifecycle_event(
        "codex",
        "aitp_v5_codex_enter",
        {
            "event_id": "evt-codex-real-enter-1",
            "host_session_id": "codex-real-session-1",
            "research_relevant": True,
            "objective_text": "Recover the exact LibRPA GW boundary.",
            "raw_host_payload": "do-not-persist-host-secret",
        },
        session_id="s1",
    )
    before = current_canonical_watermark(ws)

    result = begin_research_turn(ws, event)

    assert result.status == "context_prepared"
    assert result.receipt_status == "prepared"
    assert result.receipt_id.startswith("context-injection-")
    assert result.runtime_write is True
    assert result.canonical_write is False
    assert current_canonical_watermark(ws) == before
    runtime_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ws.root / "runtime").rglob("*")
        if path.is_file()
    )
    assert "do-not-persist-host-secret" not in runtime_text


def test_dispatch_keeps_pre_post_and_closeout_at_their_declared_boundaries(tmp_path, monkeypatch):
    from brain.v5.host_lifecycle_facade import (
        closeout_session,
        dispatch_host_lifecycle_event,
        normalize_host_lifecycle_event,
    )

    ws, _ = _seed_session(tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("bounded host dispatch crossed a forbidden writer boundary")

    monkeypatch.setattr("brain.v5.lifecycle_facade.apply_session_closeout", forbidden)
    monkeypatch.setattr("brain.v5.lifecycle_facade.plan_session_closeout", forbidden)
    monkeypatch.setattr("brain.v5.research_moment_application.apply_research_moment_decision", forbidden)

    pre = normalize_host_lifecycle_event(
        "codex",
        "PreToolUse",
        {"event_id": "evt-pre-1", "host_session_id": "codex-session-1", "tool_name": "pytest"},
        session_id="s1",
    )
    post = normalize_host_lifecycle_event(
        "codex",
        "PostToolUse",
        {
            "event_id": "evt-post-1",
            "host_session_id": "codex-session-1",
            "tool_name": "pytest",
            "status": "completed",
        },
        session_id="s1",
    )
    closeout = normalize_host_lifecycle_event(
        "codex",
        "plan_session_closeout",
        {"event_id": "evt-closeout-2", "host_session_id": "codex-session-1"},
        session_id="s1",
    )

    pre_result = dispatch_host_lifecycle_event(ws, pre)
    post_result = dispatch_host_lifecycle_event(ws, post)
    closeout_result = closeout_session(ws, closeout)

    assert (pre_result.status, pre_result.operation, pre_result.canonical_write) == (
        "policy_only",
        "delegate_existing_pre_tool_policy",
        False,
    )
    assert (post_result.status, post_result.operation, post_result.canonical_write) == (
        "trace_only",
        "delegate_existing_post_tool_trace",
        False,
    )
    assert (closeout_result.status, closeout_result.operation, closeout_result.canonical_write) == (
        "plan_only",
        "plan_session_closeout",
        False,
    )
    assert closeout_result.reason_codes == ("human_review_required", "automatic_closeout_unsupported")


def test_host_lifecycle_operation_allowlist_excludes_high_authority_writers():
    from brain.v5.host_lifecycle_facade import (
        authorize_host_lifecycle_operation,
        host_lifecycle_operation_allowlist,
        normalize_host_lifecycle_event,
    )

    allowlist = host_lifecycle_operation_allowlist()
    assert allowlist["session_start"] == {"prepare_context_injection": "runtime_write"}
    assert allowlist["prompt_submit"] == {"prepare_context_injection": "runtime_write"}
    assert allowlist["pre_tool"] == {
        "delegate_existing_pre_tool_policy": "read_only"
    }
    assert allowlist["session_end"] == {"plan_session_closeout": "read_only"}
    assert allowlist["post_tool"] == {
        "append_hook_trace_event": "runtime_write",
        "delegate_existing_post_tool_trace": "read_only",
        "dispatch_validated_research_moment": "policy_bounded_write",
    }
    with pytest.raises(TypeError):
        allowlist["post_tool"]["record_evidence"] = "canonical_write"

    event = normalize_host_lifecycle_event(
        "codex",
        "PostToolUse",
        {
            "event_id": "evt-allowlist-1",
            "host_session_id": "codex-session-1",
            "tool_name": "pytest",
            "status": "completed",
        },
        session_id="s1",
    )
    assert (
        authorize_host_lifecycle_operation(
            event, "delegate_existing_post_tool_trace"
        )
        == "read_only"
    )
    for forbidden in (
        "accept_execution_baseline",
        "apply_promotion_packet",
        "apply_project_skill",
        "apply_session_closeout",
        "apply_skill_install_plan",
        "apply_trust_update",
        "attach_artifact_auto",
        "bind_session",
        "capture_code_state_auto",
        "capture_source_asset_auto",
        "capture_tool_run_auto",
        "confirm_active_claim_rebind",
        "record_evidence",
        "stage_semantic_candidate",
    ):
        with pytest.raises(PermissionError, match="not allowed"):
            authorize_host_lifecycle_operation(event, forbidden)


def test_all_normalized_host_paths_pass_high_authority_writer_sentinels(
    tmp_path, monkeypatch
):
    from brain.v5.host_lifecycle_facade import (
        dispatch_host_lifecycle_event,
        normalize_host_lifecycle_event,
    )
    from brain.v5.query_index import current_canonical_watermark

    ws, _ = _seed_session(tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("host lifecycle invoked a high-authority writer")

    for target in (
        "brain.v5.evidence.record_evidence",
        "brain.v5.trust_updates.apply_trust_update",
        "brain.v5.memory.apply_promotion_packet",
        "brain.v5.skill_candidates.apply_project_skill",
        "brain.v5.skill_install_transactions.apply_skill_install_plan",
        "brain.v5.execution_baselines.accept_execution_baseline",
        "brain.v5.active_claim_focus.confirm_active_claim_rebind",
        "brain.v5.workspace.bind_session",
        "brain.v5.lifecycle_facade.apply_session_closeout",
    ):
        monkeypatch.setattr(target, forbidden)

    native_paths = (
        ("claude_code", "SessionStart"),
        ("claude_code", "PreToolUse"),
        ("claude_code", "PostToolUse"),
        ("kimi_code", "SessionStart"),
        ("kimi_code", "PreToolUse"),
        ("kimi_code", "PostToolUse"),
        ("codex", "PreToolUse"),
        ("codex", "PostToolUse"),
        ("codex", "aitp_v5_codex_enter"),
        ("opencode", "tool.execute.before"),
        ("opencode", "tool.execute.after"),
        ("opencode", "begin_research_turn"),
        ("opencode", "plan_session_closeout"),
    )
    before = current_canonical_watermark(ws)
    results = []
    for number, (host, native_event) in enumerate(native_paths, start=1):
        event = normalize_host_lifecycle_event(
            host,
            native_event,
            {
                "event_id": f"evt-sentinel-{number}",
                "host_session_id": f"{host}-sentinel-session",
                "research_relevant": True,
                "tool_name": "pytest",
                "status": "completed",
            },
            session_id="s1",
        )
        results.append(dispatch_host_lifecycle_event(ws, event))

    assert {result.status for result in results} == {
        "context_prepared",
        "plan_only",
        "policy_only",
        "trace_only",
    }
    assert all(result.canonical_write is False for result in results)
    assert current_canonical_watermark(ws) == before
