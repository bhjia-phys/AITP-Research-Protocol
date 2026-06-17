from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_legacy_write_helpers_block_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("AITP_LEGACY_ENABLE_WRITES", raising=False)

    import brain.mcp_server as ms

    target = tmp_path / "topics" / "demo-topic" / "state.md"

    assert ms.is_legacy_write_tool("aitp_bootstrap_topic") is True
    assert ms.is_legacy_write_tool("aitp_list_topics") is False

    blocked = ms.aitp_bootstrap_topic(str(tmp_path / "topics"), "demo-topic", "Demo", "Question?")
    assert blocked["ok"] is False
    assert blocked["error"] == "legacy_aitp_writes_disabled"
    assert not target.exists()

    with pytest.raises(RuntimeError, match="Legacy AITP L0-L4 Markdown writes are disabled"):
        ms._write_md(target, {}, "# Demo\n")


def test_legacy_write_helpers_allow_escape_hatch(tmp_path, monkeypatch):
    monkeypatch.setenv("AITP_LEGACY_ENABLE_WRITES", "1")

    import brain.mcp_server as ms

    root = tmp_path / "topics"
    result = ms.aitp_bootstrap_topic(str(root), "demo-topic", "Demo", "Question?")
    assert "Bootstrapped topic" in str(result)
    assert (root / "demo-topic" / "state.md").exists()


def test_native_mcp_rejects_legacy_write_call_by_default(tmp_path):
    script = Path(__file__).resolve().parents[1] / "brain" / "native_mcp.py"
    request = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "aitp_bootstrap_topic", "arguments": {
            "topics_root": str(tmp_path / "topics"),
            "topic_slug": "demo-topic",
            "title": "Demo",
            "question": "Question?",
        }}},
    ]
    payload = b"\n".join(json.dumps(item).encode("utf-8") for item in request) + b"\n"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        input=payload,
        capture_output=True,
        timeout=20,
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    responses = [json.loads(line) for line in lines]
    assert any("error" in item for item in responses)
    error = next(item["error"] for item in responses if item.get("id") == 2)
    assert error["code"] == -32050
    assert "disabled by default" in error["message"]
    assert not (tmp_path / "topics" / "demo-topic").exists()


def test_legacy_read_only_tools_still_work(tmp_path, monkeypatch):
    monkeypatch.delenv("AITP_LEGACY_ENABLE_WRITES", raising=False)

    import brain.mcp_server as ms

    root = tmp_path / "topics" / "demo-topic"
    root.mkdir(parents=True)
    (root / "state.md").write_text(
        "---\n"
        "topic_slug: demo-topic\n"
        "title: Demo\n"
        "status: new\n"
        "stage: L0\n"
        "posture: discover\n"
        "lane: unspecified\n"
        "updated_at: '2026-06-18T00:00:00+08:00'\n"
        "---\n"
        "# Demo\n\nQuestion\n",
        encoding="utf-8",
    )

    topics = ms.aitp_list_topics(str(tmp_path / "topics"))
    assert topics and topics[0]["topic_slug"] == "demo-topic"
    brief = ms.aitp_get_execution_brief(str(tmp_path / "topics"), "demo-topic")
    assert brief["topic_slug"] == "demo-topic"
    assert brief["stage"] == "L0"


def test_bridge_query_is_blocked_as_a_write_tool(tmp_path, monkeypatch):
    monkeypatch.delenv("AITP_LEGACY_ENABLE_WRITES", raising=False)

    import brain.mcp_server as ms

    root = tmp_path / "topics" / "demo-topic"
    root.mkdir(parents=True)
    (root / "state.md").write_text(
        "---\n"
        "topic_slug: demo-topic\n"
        "title: Demo\n"
        "status: new\n"
        "stage: L0\n"
        "posture: discover\n"
        "lane: unspecified\n"
        "updated_at: '2026-06-18T00:00:00+08:00'\n"
        "---\n"
        "# Demo\n\nQuestion\n",
        encoding="utf-8",
    )
    global_l2 = tmp_path / "topics" / ".aitp" / "L2" / "entries"
    global_l2.mkdir(parents=True)
    (global_l2 / "INDEX.md").write_text("# L2 Index\n", encoding="utf-8")

    result = ms.aitp_find_cross_topic_bridges(str(tmp_path / "topics"))
    assert result["ok"] is False
    assert result["error"] == "legacy_aitp_writes_disabled"
    assert "index.md" not in result.get("target", "")
