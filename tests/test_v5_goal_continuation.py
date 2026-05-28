"""Tests for goal continuation audit packets."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from brain.v5.contracts import ContractError
from brain.v5.goal_continuation import (
    list_goal_continuations,
    read_latest_goal_continuation,
    write_goal_continuation,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def _ws(tmp_path):
    return init_workspace(str(tmp_path))


def test_write_goal_continuation_creates_json_and_md(tmp_path):
    ws = _ws(tmp_path)
    result = write_goal_continuation(
        ws,
        objective="Return compact session-start refresh",
        changed_files=["brain/v5/cli_refresh_progress.py", "hooks/aitp_v5_claude_hook.py"],
        tests_run=["test_v5_adapter_event_runner.py", "test_v5_workspace_refresh.py"],
        tests_passed=True,
        smoke_commands=["aitp-v5 status topic s1 --compact"],
        smoke_passed=True,
        readiness_outcome={"completion_status": "kernel_ready_content_backlog", "blocking_gaps": ["legacy_semantic_review_backlog"], "can_update_claim_trust": False, "can_update_kernel_state": False, "semantic_lossless_proven": False},
        next_actions=["implement goal continuation audit packet", "keep legacy semantic backlog blocking"],
        trust_boundary="Do not update claim trust; do not close human checkpoints; orientation-only",
        blocking_backlog=["legacy_semantic_review_backlog"],
        notes="Full v5 tests: all passed",
        session_id="session-2026-05-28",
        commit_ref="5131515",
    )
    assert result["kind"] == "goal_continuation_packet"
    assert result["orientation_only"] is True
    assert result["can_update_claim_trust"] is False
    assert result["can_update_kernel_state"] is False
    assert result["truth_source"] is False
    assert "json" in result["files"]
    assert "markdown" in result["files"]
    assert "latest_json" in result["files"]
    assert "latest_markdown" in result["files"]

    surface_dir = tmp_path / ".aitp" / "surfaces" / "goal_continuation"
    assert surface_dir.exists()

    json_files = list(surface_dir.glob("goal-continuation-*.json"))
    assert len(json_files) == 1
    packet = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert packet["objective"] == "Return compact session-start refresh"
    assert packet["changed_files"] == ["brain/v5/cli_refresh_progress.py", "hooks/aitp_v5_claude_hook.py"]
    assert packet["verification"]["tests_passed"] is True
    assert packet["verification"]["smoke_passed"] is True
    assert packet["readiness_outcome"]["completion_status"] == "kernel_ready_content_backlog"
    assert packet["readiness_outcome"]["blocking_gaps"] == ["legacy_semantic_review_backlog"]
    assert packet["readiness_outcome"]["can_update_claim_trust"] is False
    assert packet["next_actions"] == ["implement goal continuation audit packet", "keep legacy semantic backlog blocking"]
    assert packet["blocking_backlog"] == ["legacy_semantic_review_backlog"]
    assert packet["commit_ref"] == "5131515"

    md_files = list(surface_dir.glob("goal-continuation-*.md"))
    assert len(md_files) == 1
    md_text = md_files[0].read_text(encoding="utf-8")
    assert "Goal Continuation" in md_text
    assert "Return compact session-start refresh" in md_text
    assert "kernel_ready_content_backlog" in md_text
    assert "legacy_semantic_review_backlog" in md_text

    latest_json = surface_dir / "latest.json"
    latest_md = surface_dir / "latest.md"
    assert latest_json.exists()
    assert latest_md.exists()
    latest_packet = json.loads(latest_json.read_text(encoding="utf-8"))
    assert latest_packet["packet_id"] == packet["packet_id"]

    assert require_valid_public_surface("goal_continuation_packet", result) == result


def test_read_latest_returns_none_when_empty(tmp_path):
    ws = _ws(tmp_path)
    assert read_latest_goal_continuation(ws) is None


def test_list_goal_continuations_empty(tmp_path):
    ws = _ws(tmp_path)
    assert list_goal_continuations(ws) == []


def test_list_goal_continuations_returns_ordered(tmp_path):
    ws = _ws(tmp_path)
    write_goal_continuation(ws, objective="first objective")
    write_goal_continuation(ws, objective="second objective")
    packets = list_goal_continuations(ws)
    assert len(packets) == 2
    assert packets[0]["objective"] == "first objective"
    assert packets[1]["objective"] == "second objective"


def test_latest_overwrites_on_each_write(tmp_path):
    ws = _ws(tmp_path)
    write_goal_continuation(ws, objective="first")
    write_goal_continuation(ws, objective="second")
    latest = read_latest_goal_continuation(ws)
    assert latest is not None
    assert latest["objective"] == "second"


def test_readiness_outcome_none_returns_empty_dict(tmp_path):
    ws = _ws(tmp_path)
    result = write_goal_continuation(ws, objective="no readiness", readiness_outcome=None)
    packet = json.loads(
        list((tmp_path / ".aitp" / "surfaces" / "goal_continuation").glob("goal-continuation-*.json"))[0].read_text()
    )
    assert packet["readiness_outcome"] == {}


def test_goal_cli_write_and_read(tmp_path, capsys):
    ws = _ws(tmp_path)
    base = str(tmp_path)
    readiness = '{"completion_status":"kernel_ready_content_backlog","blocking_gaps":["legacy_semantic_review_backlog"],"can_update_claim_trust":false,"can_update_kernel_state":false,"semantic_lossless_proven":false}'
    subprocess.run(
        [sys.executable, "-m", "brain.v5.cli", "--base", base, "goal", "write",
         "--objective", "Return compact session-start refresh",
         "--changed-files", "brain/v5/cli_refresh_progress.py,hooks/aitp_v5_claude_hook.py",
         "--tests-run", "test_v5_adapter_event_runner.py,test_v5_workspace_refresh.py",
         "--tests-passed", "true",
         "--smoke-commands", "aitp-v5 status topic s1 --compact",
         "--smoke-passed", "true",
         "--readiness-json", readiness,
         "--next-actions", "implement goal continuation,keep legacy blocking",
         "--trust-boundary", "Do not update claim trust",
         "--blocking-backlog", "legacy_semantic_review_backlog",
         "--session-id", "session-2026-05-28",
         "--commit-ref", "5131515"],
        check=True, capture_output=True, text=True,
    )
    result = subprocess.run(
        [sys.executable, "-m", "brain.v5.cli", "--base", base, "goal", "latest"],
        check=True, capture_output=True, text=True,
    )
    latest = json.loads(result.stdout.strip())
    assert latest["objective"] == "Return compact session-start refresh"
    assert latest["commit_ref"] == "5131515"
    assert latest["verification"]["tests_passed"] is True
    assert latest["readiness_outcome"]["completion_status"] == "kernel_ready_content_backlog"

    result = subprocess.run(
        [sys.executable, "-m", "brain.v5.cli", "--base", base, "goal", "list"],
        check=True, capture_output=True, text=True,
    )
    listing = json.loads(result.stdout.strip())
    assert listing["kind"] == "goal_continuation_list"
    assert listing["count"] == 1
    assert len(listing["latest_objectives"]) == 1
    assert require_valid_public_surface("goal_continuation_list", listing) == listing


def test_goal_latest_packet_passes_public_surface_contract(tmp_path):
    ws = _ws(tmp_path)
    write_goal_continuation(
        ws,
        objective="Make continuation packets auditable",
        changed_files=["brain/v5/goal_continuation.py"],
        tests_run=["tests/test_v5_goal_continuation.py"],
        tests_passed=True,
        commit_ref="abc1234",
        commit_range="base..head",
        commits=[
            {
                "hash": "abc1234",
                "subject": "Make continuation packets auditable",
                "files_changed": 3,
                "insertions": 42,
                "deletions": 5,
            }
        ],
        audit_commands=["git show --stat abc1234"],
    )
    latest = read_latest_goal_continuation(ws)
    assert latest is not None
    assert require_valid_public_surface("goal_continuation_packet", latest) == latest
    assert latest["commit_range"] == "base..head"
    assert latest["commits"][0]["hash"] == "abc1234"
    assert latest["audit_commands"] == ["git show --stat abc1234"]


def test_goal_contract_raises_contract_error_not_assertion(tmp_path):
    with pytest.raises(ContractError):
        require_valid_public_surface(
            "goal_continuation_packet",
            {"kind": "goal_continuation_packet", "orientation_only": True},
        )


def test_goal_markdown_renders_bullets_on_separate_lines(tmp_path):
    ws = _ws(tmp_path)
    write_goal_continuation(
        ws,
        objective="Readable audit packet",
        changed_files=["brain/v5/goal_continuation.py", "tests/test_v5_goal_continuation.py"],
        next_actions=[
            "resolve legacy semantic review backlog (18 topics, 16 needs_revision, 2 inconclusive)",
            "respect qsgw operator checkpoint",
        ],
    )
    md_text = (
        tmp_path / ".aitp" / "surfaces" / "goal_continuation" / "latest.md"
    ).read_text(encoding="utf-8")
    assert "- `brain/v5/goal_continuation.py`\n- `tests/test_v5_goal_continuation.py`" in md_text
    assert "topics- 16" not in md_text
    assert "inconclusive)\n- respect qsgw" in md_text


def test_goal_cli_repeated_args_preserve_commas(tmp_path):
    base = str(tmp_path)
    action = "resolve legacy semantic review backlog (18 topics, 16 needs_revision, 2 inconclusive)"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "brain.v5.cli",
            "--base",
            base,
            "goal",
            "write",
            "--objective",
            "Preserve structured audit fields",
            "--changed-file",
            "brain/v5/goal_continuation.py",
            "--test-run",
            "tests/test_v5_goal_continuation.py",
            "--next-action",
            action,
            "--commit-range",
            "base..head",
            "--commits-json",
            '[{"hash":"abc1234","subject":"subject, with comma","files_changed":1}]',
            "--audit-command",
            "git show --stat abc1234",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [sys.executable, "-m", "brain.v5.cli", "--base", base, "goal", "latest"],
        check=True,
        capture_output=True,
        text=True,
    )
    latest = json.loads(result.stdout.strip())
    assert latest["next_actions"] == [action]
    assert latest["commit_range"] == "base..head"
    assert latest["commits"][0]["subject"] == "subject, with comma"
    assert latest["audit_commands"] == ["git show --stat abc1234"]
