#!/usr/bin/env python3
"""Heartbeat bridge that advances exactly one AITP loop step."""

from __future__ import annotations

import argparse
import subprocess

from _aitp_runtime_common import (
    ADAPTER_ROOT,
    HEARTBEAT_HISTORY_PATH,
    HEARTBEAT_STATE_PATH,
    STOP_PATH,
    append_jsonl,
    now_iso,
    quote_command,
    read_json,
    relative_to_research,
    select_active_topic,
    topic_runtime_root,
    trim_text,
    write_json,
)

HEARTBEAT_STATE_VERSION = 1


def heartbeat_id() -> str:
    return f"heartbeat:{now_iso().replace(':', '-').replace('+', '_')}"


def loop_artifact_refs(topic_slug: str) -> dict:
    runtime_root = topic_runtime_root(topic_slug)
    loop_state_path = runtime_root / "loop_state.json"
    loop_history_path = runtime_root / "loop_history.jsonl"
    return {
        "topic_runtime_root": relative_to_research(runtime_root),
        "loop_state_path": relative_to_research(loop_state_path) if loop_state_path.exists() else None,
        "loop_history_path": relative_to_research(loop_history_path) if loop_history_path.exists() else None,
    }


def write_heartbeat(payload: dict, *, append_history: bool) -> None:
    write_json(HEARTBEAT_STATE_PATH, payload)
    if append_history:
        append_jsonl(HEARTBEAT_HISTORY_PATH, payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-slug")
    parser.add_argument("--run-id")
    parser.add_argument("--control-note")
    parser.add_argument("--research-mode")
    parser.add_argument("--human-request")
    parser.add_argument("--updated-by", default="openclaw-heartbeat")
    parser.add_argument("--skill-query", action="append", default=[])
    parser.add_argument("--max-steps", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    beat_id = heartbeat_id()
    if STOP_PATH.exists():
        stopped_payload = {
            "heartbeat_state_version": HEARTBEAT_STATE_VERSION,
            "heartbeat_id": beat_id,
            "updated_at": now_iso(),
            "updated_by": args.updated_by,
            "status": "stopped",
            "selection_reason": "STOP file present; heartbeat did not dispatch a loop tick.",
            "requested_topic_slug": args.topic_slug,
            "topic_slug": args.topic_slug,
            "max_steps": max(args.max_steps, 0),
            "stop_path": relative_to_research(STOP_PATH),
            "command_executed": False,
            "command": None,
        }
        write_heartbeat(stopped_payload, append_history=True)
        print("HEARTBEAT_OK stopped")
        return 0

    selection_reason = "explicit --topic-slug"
    topic_slug = args.topic_slug
    if not topic_slug:
        selected = select_active_topic()
        topic_slug = str(selected["topic_slug"])
        selection_reason = str(selected["selection_reason"])

    command = [
        "python3",
        str(ADAPTER_ROOT / "scripts" / "aitp_loop.py"),
        "--topic-slug",
        topic_slug,
        "--updated-by",
        args.updated_by,
        "--max-steps",
        str(max(args.max_steps, 0)),
    ]
    if args.run_id:
        command.extend(["--run-id", args.run_id])
    if args.control_note:
        command.extend(["--control-note", args.control_note])
    if args.research_mode:
        command.extend(["--research-mode", args.research_mode])
    if args.human_request:
        command.extend(["--human-request", args.human_request])
    for query in args.skill_query:
        command.extend(["--skill-query", query])

    if args.dry_run:
        print(f"topic_slug={topic_slug}")
        print(f"selection_reason={selection_reason}")
        print(f"loop_command={quote_command(command)}")
        print(f"heartbeat_state_path={relative_to_research(HEARTBEAT_STATE_PATH)}")
        print(f"heartbeat_history_path={relative_to_research(HEARTBEAT_HISTORY_PATH)}")
        return 0

    started_payload = {
        "heartbeat_state_version": HEARTBEAT_STATE_VERSION,
        "heartbeat_id": beat_id,
        "updated_at": now_iso(),
        "updated_by": args.updated_by,
        "status": "running",
        "requested_topic_slug": args.topic_slug,
        "topic_slug": topic_slug,
        "selection_reason": selection_reason,
        "max_steps": max(args.max_steps, 0),
        "run_id": args.run_id,
        "control_note": args.control_note,
        "research_mode": args.research_mode,
        "human_request": args.human_request,
        "skill_queries": list(args.skill_query),
        "command_executed": False,
        "command": quote_command(command),
        **loop_artifact_refs(topic_slug),
    }
    write_heartbeat(started_payload, append_history=False)

    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )
    loop_state = read_json(topic_runtime_root(topic_slug) / "loop_state.json") or {}
    final_payload = {
        **started_payload,
        "updated_at": now_iso(),
        "status": "completed" if completed.returncode == 0 else "failed",
        "command_executed": True,
        "exit_code": completed.returncode,
        "stdout_tail": trim_text(completed.stdout, limit=1200),
        "stderr_tail": trim_text(completed.stderr, limit=1200),
        **loop_artifact_refs(topic_slug),
        "loop_summary": {
            "run_id": loop_state.get("run_id"),
            "entry_conformance": loop_state.get("entry_conformance"),
            "exit_conformance": loop_state.get("exit_conformance"),
            "capability_status": loop_state.get("capability_status"),
            "trust_status": loop_state.get("trust_status"),
            "selected_action_id": loop_state.get("selected_action_id"),
            "selected_action_type": loop_state.get("selected_action_type"),
            "auto_actions_executed": loop_state.get("auto_actions_executed"),
            "remaining_pending_actions": loop_state.get("remaining_pending_actions"),
        },
    }
    write_heartbeat(final_payload, append_history=True)

    if completed.returncode != 0:
        raise SystemExit(
            f"Heartbeat loop failed for {topic_slug}: exit_code={completed.returncode}\n"
            f"{trim_text(completed.stderr or completed.stdout, limit=1200)}"
        )

    print(f"HEARTBEAT_OK topic={topic_slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
