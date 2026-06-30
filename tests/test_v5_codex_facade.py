from __future__ import annotations

from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys


def _seed_workspace(tmp_path: Path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "codex-facade-topic", context_id="codex-context", title="Codex facade topic")
    claim = create_claim(
        ws,
        topic_id="codex-facade-topic",
        statement="Compact Codex context should expand only when the research step needs it.",
        evidence_profile="protocol_engineering",
        confidence_state="hypothesis",
        active_uncertainty="facade must not expose trust apply as a default action",
    )
    bind_session(
        ws,
        "codex-session",
        topic_id="codex-facade-topic",
        context_id="codex-context",
        active_claim=claim.claim_id,
    )
    return ws, claim


def _read_content_length_message(stream: BytesIO) -> dict:
    header = b""
    while not (header.endswith(b"\r\n\r\n") or header.endswith(b"\n\n")):
        chunk = stream.read(1)
        assert chunk, f"unexpected EOF while reading MCP header: {header!r}"
        header += chunk
    length = None
    for line in header.decode("utf-8").replace("\r\n", "\n").split("\n"):
        if line.lower().startswith("content-length:"):
            length = int(line.split(":", 1)[1].strip())
            break
    assert length is not None
    return json.loads(stream.read(length).decode("utf-8"))


def test_codex_facade_tools_are_compact_progressive_and_trust_safe(tmp_path):
    from brain.v5.mcp_tools import (
        aitp_v5_codex_closeout,
        aitp_v5_codex_enter,
        aitp_v5_codex_expand,
        aitp_v5_codex_literature_step,
        aitp_v5_codex_recording_step,
        aitp_v5_codex_tool_catalog,
    )
    from brain.v5.models import ReferenceLocationRecord, TrustUpdateRecord
    from brain.v5.store import list_records

    ws, claim = _seed_workspace(tmp_path)

    catalog = aitp_v5_codex_tool_catalog(profile="entry")
    assert catalog["kind"] == "codex_mcp_surface_catalog"
    assert catalog["default_mcp_surface"] == "codex"
    assert "aitp_v5_apply_trust_update" in catalog["hidden_in_codex_surface"]

    entered = aitp_v5_codex_enter(
        str(ws.base),
        session_id="codex-session",
        request_summary="continue the topic and maybe draft a note",
    )
    assert entered["kind"] == "codex_entry_context"
    assert entered["active_session_ready"] is True
    assert entered["process_mode"] == "writing"
    assert entered["context_pack"]["kind"] == "aitp_context_pack"
    assert entered["can_update_claim_trust"] is False

    outline = aitp_v5_codex_expand(str(ws.base), session_id="codex-session", expansion="note_outline")
    assert outline["kind"] == "codex_context_expansion"
    assert outline["surface"]["kind"] == "note_outline"
    assert outline["can_update_kernel_state"] is False

    recording = aitp_v5_codex_recording_step(
        str(ws.base),
        session_id="codex-session",
        event_type="source_touched",
        summary="Found a paper section that may be reused in the note.",
        claim_id=claim.claim_id,
        slot="reference_location",
    )
    assert recording["kind"] == "codex_recording_step"
    assert recording["classification"]["decision"] in {"navigate", "defer", "checkpoint"}
    assert recording["slot_expansion"]["recommended_write_tool"] == "aitp_v5_record_reference_location"
    assert recording["write_executed"] is False
    assert recording["can_update_claim_trust"] is False

    suggested = aitp_v5_codex_literature_step(
        str(ws.base),
        session_id="codex-session",
        uri="https://arxiv.org/abs/2604.14695",
        label="Related long-range spin-chain paper",
        external_id="arXiv:2604.14695",
        short_summary="Potential related work; claim relation still needs review.",
        detected_relevance="related work",
    )
    assert suggested["action"] == "suggest"
    assert suggested["surface"]["kind"] == "literature_intake_suggestion"
    assert suggested["can_update_kernel_state"] is False

    recorded = aitp_v5_codex_literature_step(
        str(ws.base),
        session_id="codex-session",
        action="record_reference",
        uri="https://arxiv.org/abs/2604.14695",
        label="Related long-range spin-chain paper",
        external_id="arXiv:2604.14695",
        short_summary="Reference only; no evidence yet.",
        detected_relevance="related work",
    )
    references = list_records(ws.registry_dir("reference_locations"), ReferenceLocationRecord)
    trust_updates = list_records(ws.registry_dir("trust_updates"), TrustUpdateRecord)
    assert recorded["kernel_state_change"] == "reference_location_record_only"
    assert recorded["can_update_claim_trust"] is False
    assert len(references) == 1
    assert trust_updates == []

    closeout = aitp_v5_codex_closeout(
        str(ws.base),
        session_id="codex-session",
        summary="Session ended after planning compact Codex facade behavior.",
    )
    assert closeout["kind"] == "codex_closeout"
    assert closeout["mode"] == "preview"
    assert closeout["write_executed"] is False
    assert closeout["can_update_claim_trust"] is False


def test_native_mcp_codex_surface_exposes_facade_not_full_kernel(tmp_path):
    script = Path(__file__).resolve().parents[1] / "brain" / "v5" / "native_mcp.py"
    env = {
        **os.environ,
        "AITP_MCP_SURFACE": "codex",
        "AITP_V5_MCP_LOG": str(tmp_path / "mcp.log"),
    }
    input_bytes = b""
    for message in [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]:
        body = json.dumps(message).encode("utf-8")
        input_bytes += f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8") + body

    process = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        input=input_bytes,
        capture_output=True,
        env=env,
        timeout=10,
    )
    assert process.returncode == 0, process.stderr.decode("utf-8", "replace")
    stdout = BytesIO(process.stdout)
    initialized = _read_content_length_message(stdout)
    tools = _read_content_length_message(stdout)["result"]["tools"]
    tool_names = {tool["name"] for tool in tools}

    assert initialized["result"]["serverInfo"]["version"] == "1.0.0"
    assert "aitp_v5_codex_enter" in tool_names
    assert "aitp_v5_codex_expand" in tool_names
    assert "aitp_v5_codex_literature_step" in tool_names
    assert "aitp_v5_preflight_trust_update" in tool_names
    assert "aitp_v5_apply_trust_update" not in tool_names
    assert "aitp_v5_get_execution_brief" not in tool_names
    assert "aitp_v5_get_context_pack" not in tool_names
    assert len(tool_names) < 20


def test_codex_plugin_skills_and_launcher_route_through_facade():
    repo = Path(__file__).resolve().parents[1]
    using = (repo / "plugins" / "aitp-research-protocol" / "skills" / "using-aitp" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    runtime = (repo / "plugins" / "aitp-research-protocol" / "skills" / "aitp-runtime" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    launcher = (repo / "plugins" / "aitp-research-protocol" / "scripts" / "launch_aitp_mcp.py").read_text(
        encoding="utf-8"
    )
    plugin_readme = (repo / "plugins" / "aitp-research-protocol" / "README.md").read_text(encoding="utf-8")

    assert 'os.environ.setdefault("AITP_MCP_SURFACE", "codex")' in launcher
    assert "full `aitp_v5_*` tool surface loads" not in using
    assert "aitp_v5_codex_tool_catalog" in using
    assert "aitp_v5_codex_enter" in using
    assert "AITP_MCP_SURFACE=full" in using
    assert "aitp_v5_codex_expand" in runtime
    assert "aitp_v5_codex_recording_step" in runtime
    assert "aitp_v5_codex_literature_step" in runtime
    assert "aitp_v5_codex_closeout" in runtime
    assert "A paper, web page, local note, or RAG chunk is not evidence" in runtime
    assert "AITP_MCP_SURFACE=codex" in plugin_readme
    assert "AITP_MCP_SURFACE=full" in plugin_readme
