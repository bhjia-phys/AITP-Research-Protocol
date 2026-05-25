from __future__ import annotations

import json
import sys
from pathlib import Path


def test_runtime_host_readiness_runs_process_without_trusting_summaries(tmp_path):
    from brain.v5.host_readiness import audit_runtime_host_readiness
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)

    payload = audit_runtime_host_readiness(
        ws,
        runtime="codex",
        command=sys.executable,
        version_args=["--version"],
        check_installation=False,
    )
    validated = require_valid_public_surface("runtime_host_readiness_audit", payload)

    assert validated["process"]["ok"] is True
    assert validated["installation_audit"]["status"] == "skipped"
    assert validated["summary_inputs_trusted"] is False
    assert validated["orientation_only"] is True
    assert validated["can_update_kernel_state"] is False
    assert validated["can_update_claim_trust"] is False
    assert validated["status"] == "process_ready"


def test_runtime_host_readiness_cli_and_mcp(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_audit_runtime_host_readiness

    assert main([
        "--base",
        str(tmp_path),
        "adapter",
        "host-readiness",
        "codex",
        "--command",
        sys.executable,
        "--arg=--version",
        "--skip-install-audit",
    ]) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_audit_runtime_host_readiness(
        str(tmp_path),
        runtime="codex",
        command=sys.executable,
        version_args=["--version"],
        check_installation=False,
    )

    assert cli_payload["kind"] == "runtime_host_readiness_audit"
    assert mcp_payload["kind"] == "runtime_host_readiness_audit"
    assert cli_payload["process"]["ok"] is True
    assert mcp_payload["process"]["ok"] is True


def test_runtime_host_lifecycle_probe_detects_trace_delta_and_hook_output(tmp_path):
    from brain.v5.host_readiness import audit_runtime_host_lifecycle
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.trace import TraceEvent, append_trace_event, hook_trace_event_path
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    script = tmp_path / "emit_hook_signal.py"
    script.write_text(
        "\n".join(
            [
                "import json",
                "import sys",
                "from pathlib import Path",
                "trace_path = Path(sys.argv[1])",
                "trace_path.parent.mkdir(parents=True, exist_ok=True)",
                "event = {",
                "  'event_id': 'event-probe',",
                "  'session_id': 's1',",
                "  'topic_id': 'fqhe',",
                "  'event_type': 'tool_run_recorded',",
                "  'risk_level': 'guided',",
                "  'claim_id': 'claim-fqhe',",
                "  'payload': {},",
                "  'timestamp': '',",
                "  'kind': 'trace_event',",
                "}",
                "with trace_path.open('a', encoding='utf-8') as handle:",
                "    handle.write(json.dumps(event, sort_keys=True) + '\\n')",
                "print(json.dumps({'aitp': {'kind': 'hook_trace_event_record'}}))",
            ]
        ),
        encoding="utf-8",
    )
    trace_path = hook_trace_event_path(ws)
    append_trace_event(
        trace_path,
        TraceEvent(
            event_id="event-before",
            session_id="s0",
            topic_id="fqhe",
            event_type="tool_run_recorded",
            risk_level="guided",
        ),
    )

    payload = audit_runtime_host_lifecycle(
        ws,
        runtime="claude_code",
        command=sys.executable,
        args=[str(script), str(trace_path)],
        timeout_seconds=10,
    )

    validated = require_valid_public_surface("runtime_host_lifecycle_audit", payload)
    assert validated["status"] == "lifecycle_observed"
    assert validated["process"]["ok"] is True
    assert validated["trace"]["before_count"] == 1
    assert validated["trace"]["after_count"] == 2
    assert validated["trace"]["delta_count"] == 1
    assert validated["hook_output"]["observed"] is True
    assert validated["summary_inputs_trusted"] is False
    assert validated["can_update_kernel_state"] is False
    assert validated["can_update_claim_trust"] is False


def test_runtime_host_lifecycle_probe_cli_and_mcp(tmp_path, capsys):
    from brain.v5.cli import main
    from brain.v5.mcp_tools import aitp_v5_audit_runtime_host_lifecycle

    script = tmp_path / "no_hook.py"
    script.write_text("print('no lifecycle event')\n", encoding="utf-8")

    assert main(
        [
            "--base",
            str(tmp_path),
            "adapter",
            "host-lifecycle",
            "codex",
            "--command",
            sys.executable,
            "--arg",
            str(script),
            "--timeout",
            "10",
        ]
    ) == 0
    cli_payload = json.loads(capsys.readouterr().out)
    mcp_payload = aitp_v5_audit_runtime_host_lifecycle(
        str(tmp_path),
        runtime="codex",
        command=sys.executable,
        args=[str(script)],
        timeout_seconds=10,
    )

    assert cli_payload["kind"] == "runtime_host_lifecycle_audit"
    assert mcp_payload["kind"] == "runtime_host_lifecycle_audit"
    assert cli_payload["status"] == "process_ready_no_lifecycle_event_observed"
    assert mcp_payload["status"] == "process_ready_no_lifecycle_event_observed"
    assert Path(cli_payload["trace"]["path"]).name == "hook_trace_events.jsonl"
