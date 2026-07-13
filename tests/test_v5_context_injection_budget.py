from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


_ROOT = Path(__file__).resolve().parents[1]


def _write_legacy_topic(root: Path, topic_id: str, *, title: str, question: str, memory_marker: str):
    topic = root / topic_id
    topic.mkdir(parents=True)
    (topic / "state.md").write_text(
        "---\n"
        f'title: "{title}"\n'
        "stage: L3\n"
        "lane: theory\n"
        "---\n\n"
        "## Research Question\n"
        f"{question}\n",
        encoding="utf-8",
    )
    (topic / "MEMORY.md").write_text(
        f"# {memory_marker}\n\n" + (f"{memory_marker} private body " * 1200),
        encoding="utf-8",
    )


def _run_router(topics_root: Path, message: str):
    env = dict(os.environ)
    env["AITP_TOPICS_ROOT"] = str(topics_root)
    return subprocess.run(
        [sys.executable, str(_ROOT / "deploy" / "hooks" / "aitp-keyword-router.py")],
        input=json.dumps({"user_message": message}, ensure_ascii=False),
        text=True,
        capture_output=True,
        encoding="utf-8",
        env=env,
        check=False,
    )


def test_router_injects_bounded_topic_hints_without_memory_bodies(tmp_path):
    topics_root = tmp_path / "research" / "aitp-topics"
    topics_root.mkdir(parents=True)
    _write_legacy_topic(
        topics_root,
        "quantum-gravity-insight",
        title="量子引力与黑洞信息",
        question="如何控制 replica wormhole 的解析延拓边界？",
        memory_marker="QG_PRIVATE_MEMORY_MARKER",
    )
    _write_legacy_topic(
        topics_root,
        "librpa-qsgw-workflow",
        title="LibRPA QSGW workflow",
        question="How should the head and wing workflow be resumed?",
        memory_marker="LIBRPA_PRIVATE_MEMORY_MARKER",
    )

    result = _run_router(topics_root, "继续量子引力课题，检查 replica wormhole 推导边界")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert "quantum-gravity-insight" in context
    assert "量子引力与黑洞信息" in context
    assert "librpa-qsgw-workflow" not in context
    assert "QG_PRIVATE_MEMORY_MARKER" not in context
    assert "LIBRPA_PRIVATE_MEMORY_MARKER" not in context
    assert "aitp_v5_codex_autoroute" in context
    assert "aitp_v5_codex_enter" in context
    assert len(context.encode("utf-8")) <= 4096


def test_topic_status_and_startup_refresh_share_compact_context_boundary(tmp_path, monkeypatch):
    from brain.v5 import workspace_refresh
    from brain.v5.topic_status import write_topic_status_surfaces
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace
    from brain.v5.workspace_refresh import refresh_workspace_startup_views

    ws = init_workspace(tmp_path / "workspace")
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum gravity")
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="Replica continuation is controlled only in the recorded finite-n scope.",
        evidence_profile="semi_formal_theory",
        confidence_state="conditional",
        active_uncertainty="No uniform continuation bound is recorded.",
    )
    bind_session(
        ws,
        "session-qg",
        topic_id="qg",
        context_id="formal-theory",
        active_claim=claim.claim_id,
    )

    topic_status = write_topic_status_surfaces(ws, session_id="session-qg")

    def fail_heavy_topic_status(*_args, **_kwargs):
        raise AssertionError("startup called the full topic-status writer")

    monkeypatch.setattr(workspace_refresh, "write_topic_status_surfaces", fail_heavy_topic_status)
    startup = refresh_workspace_startup_views(ws, session_id="session-qg")

    assert topic_status["compact_context"] == startup["compact_context"]
    assert startup["compact_context"] == startup["topic_status_bundles"][0]["compact_context"]
    assert startup["compact_context"]["fingerprint"]
    coverage = startup["compact_context"]["retrieval_coverage"]
    assert coverage["scope_state_fresh"] is True
    assert coverage["scope_content_verified"] is False
    assert coverage["exhaustive"] is False
    assert coverage["can_claim_no_result"] is False
    assert startup["compact_context"]["orientation_only"] is True
    assert startup["compact_context"]["can_update_kernel_state"] is False
    assert startup["compact_context"]["can_update_claim_trust"] is False
