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
