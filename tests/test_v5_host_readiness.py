from __future__ import annotations

import json
import sys


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
