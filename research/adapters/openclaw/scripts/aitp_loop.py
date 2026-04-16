#!/usr/bin/env python3
"""Single-entry OpenClaw-side AITP loop surface."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

from _aitp_runtime_common import (
    ADAPTER_ROOT,
    KNOWLEDGE_ROOT,
    append_jsonl,
    now_iso,
    python_command,
    quote_command,
    read_json,
    read_jsonl,
    select_active_topic,
    topic_runtime_root,
    write_json,
)

LOOP_STATE_FILENAME = "loop_state.json"
LOOP_HISTORY_FILENAME = "loop_history.jsonl"
NEXT_ACTION_DECISION_FILENAME = "next_action_decision.json"


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "aitp-topic"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-slug")
    parser.add_argument("--topic")
    parser.add_argument("--statement")
    parser.add_argument("--run-id")
    parser.add_argument("--control-note")
    parser.add_argument("--research-mode")
    parser.add_argument("--human-request")
    parser.add_argument("--updated-by", default="openclaw")
    parser.add_argument("--skill-query", action="append", default=[])
    parser.add_argument("--arxiv-id", action="append", default=[])
    parser.add_argument("--local-note-path", action="append", default=[])
    parser.add_argument("--max-steps", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def resolve_requested_topic(args: argparse.Namespace) -> tuple[str, str]:
    if args.topic_slug:
        return args.topic_slug, "explicit --topic-slug"
    if args.topic:
        return slugify(args.topic), "derived from --topic"

    selected = select_active_topic()
    return str(selected["topic_slug"]), str(selected["selection_reason"])


def build_orchestrate_command(args: argparse.Namespace, topic_slug: str) -> list[str]:
    command = [
        *python_command(),
        str(KNOWLEDGE_ROOT / "runtime" / "scripts" / "orchestrate_topic.py"),
        "--updated-by",
        args.updated_by,
    ]
    if args.topic and not args.topic_slug:
        command.extend(["--topic", args.topic])
    else:
        command.extend(["--topic-slug", topic_slug])
    if args.statement:
        command.extend(["--statement", args.statement])
    if args.run_id:
        command.extend(["--run-id", args.run_id])
    if args.control_note:
        command.extend(["--control-note", args.control_note])
    if args.research_mode:
        command.extend(["--research-mode", args.research_mode])
    if args.human_request:
        command.extend(["--human-request", args.human_request])
    for arxiv_id in args.arxiv_id:
        command.extend(["--arxiv-id", arxiv_id])
    for local_note_path in args.local_note_path:
        command.extend(["--local-note-path", local_note_path])
    for query in args.skill_query:
        command.extend(["--skill-query", query])
    return command


def build_dispatch_command(topic_slug: str, updated_by: str, max_steps: int) -> list[str]:
    return [
        *python_command(),
        str(ADAPTER_ROOT / "scripts" / "dispatch_action_queue.py"),
        "--topic-slug",
        topic_slug,
        "--updated-by",
        updated_by,
        "--max-actions",
        str(max(max_steps, 0)),
    ]


def build_exit_audit_command(topic_slug: str, updated_by: str) -> list[str]:
    return [
        *python_command(),
        str(KNOWLEDGE_ROOT / "runtime" / "scripts" / "audit_topic_conformance.py"),
        "--topic-slug",
        topic_slug,
        "--phase",
        "exit",
        "--updated-by",
        updated_by,
    ]


def load_next_action_decision(runtime_root: Path) -> dict:
    return read_json(runtime_root / NEXT_ACTION_DECISION_FILENAME) or {}


def decision_selected_action(decision: dict) -> dict:
    return decision.get("selected_action") or {}


def decision_allows_auto_dispatch(decision: dict) -> bool:
    selected_action = decision_selected_action(decision)
    return bool(decision.get("auto_dispatch_allowed")) and bool(selected_action.get("action_id"))


def new_action_receipts(before_rows: list[dict], after_rows: list[dict]) -> list[str]:
    seen_receipts = {str(row.get("receipt_id") or "") for row in before_rows}
    action_ids: list[str] = []
    for row in after_rows:
        receipt_id = str(row.get("receipt_id") or "")
        if not receipt_id or receipt_id in seen_receipts or receipt_id.endswith(":refresh"):
            continue
        action_id = str(row.get("action_id") or "").strip()
        if action_id and action_id not in action_ids:
            action_ids.append(action_id)
    return action_ids


def capability_status(runtime_root: Path) -> str:
    payload = read_json(runtime_root / "capability_registry.json") or {}
    return str(payload.get("overall_status") or "unknown")


def trust_status(topic_slug: str, run_id: str | None) -> str:
    if not run_id:
        return "unknown"
    payload = read_json(
        KNOWLEDGE_ROOT / "validation" / "topics" / topic_slug / "runs" / run_id / "trust_audit.json"
    ) or {}
    return str(payload.get("overall_status") or "unknown")


def main() -> int:
    args = build_parser().parse_args()
    topic_slug, selection_reason = resolve_requested_topic(args)

    orchestrate_command = build_orchestrate_command(args, topic_slug)
    dispatch_command = build_dispatch_command(topic_slug, args.updated_by, args.max_steps)
    exit_audit_command = build_exit_audit_command(topic_slug, args.updated_by)

    if args.dry_run:
        print(f"Resolved topic_slug={topic_slug}")
        print(f"selection_reason={selection_reason}")
        print(f"orchestrate_command={quote_command(orchestrate_command)}")
        print(
            f"decision_artifact=runtime/topics/{topic_slug}/{NEXT_ACTION_DECISION_FILENAME}"
        )
        if args.max_steps > 0:
            print(f"dispatch_command={quote_command(dispatch_command)}")
        print(f"exit_audit_command={quote_command(exit_audit_command)}")
        return 0

    subprocess.run(orchestrate_command, check=True, stdin=subprocess.DEVNULL)

    runtime_root = topic_runtime_root(topic_slug)
    entry_decision = load_next_action_decision(runtime_root)
    entry_conformance = str(
        ((read_json(runtime_root / "conformance_state.json") or {}).get("overall_status") or "unknown")
    )
    receipts_before = read_jsonl(runtime_root / "action_receipts.jsonl")

    dispatch_exit_code = 0
    if args.max_steps > 0 and decision_allows_auto_dispatch(entry_decision):
        dispatch_completed = subprocess.run(dispatch_command, check=False, stdin=subprocess.DEVNULL)
        dispatch_exit_code = dispatch_completed.returncode

    exit_completed = subprocess.run(exit_audit_command, check=False, stdin=subprocess.DEVNULL)
    exit_decision = load_next_action_decision(runtime_root)
    selected_action = decision_selected_action(exit_decision)
    exit_conformance = str(
        ((read_json(runtime_root / "conformance_state.json") or {}).get("overall_status") or "unknown")
    )
    receipts_after = read_jsonl(runtime_root / "action_receipts.jsonl")
    executed_actions = new_action_receipts(receipts_before, receipts_after)

    topic_state = read_json(runtime_root / "topic_state.json") or {}
    queue_rows = read_jsonl(runtime_root / "action_queue.jsonl")
    pending_rows = [row for row in queue_rows if row.get("status") == "pending"]
    run_id = str(topic_state.get("latest_run_id") or args.run_id or "") or None
    human_request = (
        args.human_request
        or args.statement
        or str(topic_state.get("summary") or "")
        or f"Resume {topic_slug}."
    )

    loop_entry = {
        "topic_slug": topic_slug,
        "run_id": run_id,
        "updated_at": now_iso(),
        "updated_by": args.updated_by,
        "human_request": human_request,
        "max_auto_steps": max(args.max_steps, 0),
        "bootstrap_runtime_root": str(runtime_root),
        "entry_conformance": entry_conformance,
        "exit_conformance": exit_conformance,
        "capability_status": capability_status(runtime_root),
        "trust_status": trust_status(topic_slug, run_id),
        "research_mode": topic_state.get("research_mode"),
        "active_executor_kind": topic_state.get("active_executor_kind"),
        "decision_source": exit_decision.get("decision_source"),
        "decision_mode": exit_decision.get("decision_mode"),
        "decision_basis": exit_decision.get("decision_basis"),
        "decision_reason": exit_decision.get("reason"),
        "selected_action_id": selected_action.get("action_id"),
        "selected_action_type": selected_action.get("action_type"),
        "selected_action_auto_runnable": bool(selected_action.get("auto_runnable")),
        "auto_actions_executed": executed_actions,
        "remaining_pending_actions": len(pending_rows),
        "topic_selection_reason": selection_reason,
    }
    write_json(runtime_root / LOOP_STATE_FILENAME, loop_entry)
    append_jsonl(runtime_root / LOOP_HISTORY_FILENAME, loop_entry)

    print(f"AITP loop complete for {topic_slug}")
    print(f"- runtime_root: {runtime_root}")
    print(f"- run_id: {run_id or '(none)'}")
    print(f"- auto_actions_executed: {len(executed_actions)}")
    print(f"- remaining_pending_actions: {len(pending_rows)}")
    print(f"- entry_conformance: {entry_conformance}")
    print(f"- exit_conformance: {exit_conformance}")

    if dispatch_exit_code != 0:
        return dispatch_exit_code
    return exit_completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
