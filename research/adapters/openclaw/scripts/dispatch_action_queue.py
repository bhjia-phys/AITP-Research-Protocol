#!/usr/bin/env python3
"""Dispatch reviewed, allowlisted AITP runtime actions for one topic."""

from __future__ import annotations

import argparse
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
    relative_to_research,
    resolve_topic_slug,
    topic_runtime_root,
    trim_text,
    write_jsonl,
)

RECEIPTS_FILENAME = "action_receipts.jsonl"
NEXT_ACTION_DECISION_FILENAME = "next_action_decision.json"
RUNTIME_CONTROLLER_ACTIONS = {
    "apply_candidate_split_contract",
    "reactivate_deferred_candidate",
    "spawn_followup_subtopics",
    "reintegrate_followup_subtopic",
    "assess_topic_completion",
    "prepare_lean_bridge",
    "auto_promote_candidate",
}


def normalize_handler(handler: str | None) -> str | None:
    if not handler:
        return None
    alias = Path(handler).name if "/" in handler or "\\" in handler else handler
    return {
        "discover_external_skills": "discover_external_skills",
        "discover_external_skills.py": "discover_external_skills",
        "sync_topic_state": "sync_topic_state",
        "sync_topic_state.py": "sync_topic_state",
        "audit_topic_conformance": "audit_topic_conformance",
        "audit_topic_conformance.py": "audit_topic_conformance",
        "advance_closed_loop": "advance_closed_loop",
        "advance_closed_loop.py": "advance_closed_loop",
        "dispatch_execution_task": "dispatch_execution_task",
        "dispatch_execution_task.py": "dispatch_execution_task",
        "run_literature_followup": "run_literature_followup",
        "run_literature_followup.py": "run_literature_followup",
    }.get(alias)


def normalize_dispatch_target(handler: str | None, action_type: str | None) -> str | None:
    handler_key = normalize_handler(handler)
    if handler_key:
        return handler_key
    normalized_action_type = str(action_type or "").strip()
    if normalized_action_type in RUNTIME_CONTROLLER_ACTIONS:
        return normalized_action_type
    return None


def build_discover_command(topic_slug: str, updated_by: str, handler_args: dict) -> list[str]:
    queries = handler_args.get("queries") or handler_args.get("query") or []
    if isinstance(queries, str):
        queries = [queries]
    queries = [query for query in queries if query]
    if not queries:
        raise SystemExit("discover_external_skills requires handler_args.queries")

    command = [
        *python_command(),
        str(ADAPTER_ROOT / "scripts" / "discover_external_skills.py"),
        "--topic-slug",
        topic_slug,
        "--updated-by",
        updated_by,
    ]
    for query in queries:
        command.extend(["--query", query])
    return command


def build_sync_command(topic_slug: str, updated_by: str, handler_args: dict) -> list[str]:
    command = [
        *python_command(),
        str(KNOWLEDGE_ROOT / "runtime" / "scripts" / "sync_topic_state.py"),
        "--topic-slug",
        topic_slug,
        "--updated-by",
        updated_by,
    ]
    if handler_args.get("run_id"):
        command.extend(["--run-id", str(handler_args["run_id"])])
    if handler_args.get("control_note"):
        command.extend(["--control-note", str(handler_args["control_note"])])
    return command


def build_conformance_command(topic_slug: str, updated_by: str, handler_args: dict) -> list[str]:
    phase = str(handler_args.get("phase") or "entry")
    return [
        *python_command(),
        str(KNOWLEDGE_ROOT / "runtime" / "scripts" / "audit_topic_conformance.py"),
        "--topic-slug",
        topic_slug,
        "--phase",
        phase,
        "--updated-by",
        updated_by,
    ]


def build_advance_closed_loop_command(topic_slug: str, updated_by: str, handler_args: dict) -> list[str]:
    step = str(handler_args.get("step") or "auto")
    command = [
        *python_command(),
        str(KNOWLEDGE_ROOT / "runtime" / "scripts" / "advance_closed_loop.py"),
        "--topic-slug",
        topic_slug,
        "--step",
        step,
        "--updated-by",
        updated_by,
    ]
    if handler_args.get("run_id"):
        command.extend(["--run-id", str(handler_args["run_id"])])
    return command


def build_execution_handoff_command(topic_slug: str, updated_by: str, handler_args: dict) -> list[str]:
    command = [
        *python_command(),
        str(ADAPTER_ROOT / "scripts" / "dispatch_execution_task.py"),
        "--topic-slug",
        topic_slug,
        "--updated-by",
        updated_by,
    ]
    if handler_args.get("run_id"):
        command.extend(["--run-id", str(handler_args["run_id"])])
    return command


def build_literature_followup_command(topic_slug: str, updated_by: str, handler_args: dict) -> list[str]:
    query = str(handler_args.get("query") or "").strip()
    run_id = str(handler_args.get("run_id") or "").strip()
    if not query:
        raise SystemExit("run_literature_followup requires handler_args.query")
    if not run_id:
        raise SystemExit("run_literature_followup requires handler_args.run_id")

    command = [
        *python_command(),
        str(KNOWLEDGE_ROOT / "runtime" / "scripts" / "run_literature_followup.py"),
        "--topic-slug",
        topic_slug,
        "--run-id",
        run_id,
        "--query",
        query,
        "--updated-by",
        updated_by,
    ]
    if handler_args.get("priority"):
        command.extend(["--priority", str(handler_args["priority"])])
    if handler_args.get("target_source_type"):
        command.extend(["--target-source-type", str(handler_args["target_source_type"])])
    if handler_args.get("max_results"):
        command.extend(["--max-results", str(handler_args["max_results"])])
    return command


def build_runtime_controller_command(
    topic_slug: str,
    updated_by: str,
    action_type: str,
    handler_args: dict,
) -> list[str]:
    command = [
        *python_command(),
        str(ADAPTER_ROOT / "scripts" / "dispatch_runtime_controller_action.py"),
        "--topic-slug",
        topic_slug,
        "--action-type",
        action_type,
        "--updated-by",
        updated_by,
    ]
    option_map = (
        ("run_id", "--run-id"),
        ("entry_id", "--entry-id"),
        ("query", "--query"),
        ("receipt_id", "--receipt-id"),
        ("child_topic_slug", "--child-topic-slug"),
        ("candidate_id", "--candidate-id"),
        ("backend_id", "--backend-id"),
        ("target_backend_root", "--target-backend-root"),
        ("domain", "--domain"),
        ("subdomain", "--subdomain"),
        ("source_id", "--source-id"),
        ("source_section", "--source-section"),
        ("source_section_title", "--source-section-title"),
        ("notes", "--notes"),
    )
    for key, flag in option_map:
        value = handler_args.get(key)
        if value is not None and str(value).strip():
            command.extend([flag, str(value)])
    return command


def build_apply_split_command(topic_slug: str, updated_by: str, handler_args: dict) -> list[str]:
    return build_runtime_controller_command(
        topic_slug,
        updated_by,
        "apply_candidate_split_contract",
        handler_args,
    )


def build_reactivate_deferred_command(topic_slug: str, updated_by: str, handler_args: dict) -> list[str]:
    return build_runtime_controller_command(
        topic_slug,
        updated_by,
        "reactivate_deferred_candidate",
        handler_args,
    )


def build_spawn_followup_command(topic_slug: str, updated_by: str, handler_args: dict) -> list[str]:
    return build_runtime_controller_command(
        topic_slug,
        updated_by,
        "spawn_followup_subtopics",
        handler_args,
    )


def build_reintegrate_followup_command(topic_slug: str, updated_by: str, handler_args: dict) -> list[str]:
    return build_runtime_controller_command(
        topic_slug,
        updated_by,
        "reintegrate_followup_subtopic",
        handler_args,
    )


def build_topic_completion_command(topic_slug: str, updated_by: str, handler_args: dict) -> list[str]:
    return build_runtime_controller_command(
        topic_slug,
        updated_by,
        "assess_topic_completion",
        handler_args,
    )


def build_lean_bridge_command(topic_slug: str, updated_by: str, handler_args: dict) -> list[str]:
    return build_runtime_controller_command(
        topic_slug,
        updated_by,
        "prepare_lean_bridge",
        handler_args,
    )


def build_auto_promote_command(topic_slug: str, updated_by: str, handler_args: dict) -> list[str]:
    return build_runtime_controller_command(
        topic_slug,
        updated_by,
        "auto_promote_candidate",
        handler_args,
    )


ALLOWLIST = {
    "discover_external_skills": build_discover_command,
    "sync_topic_state": build_sync_command,
    "audit_topic_conformance": build_conformance_command,
    "advance_closed_loop": build_advance_closed_loop_command,
    "dispatch_execution_task": build_execution_handoff_command,
    "run_literature_followup": build_literature_followup_command,
    "apply_candidate_split_contract": build_apply_split_command,
    "reactivate_deferred_candidate": build_reactivate_deferred_command,
    "spawn_followup_subtopics": build_spawn_followup_command,
    "reintegrate_followup_subtopic": build_reintegrate_followup_command,
    "assess_topic_completion": build_topic_completion_command,
    "prepare_lean_bridge": build_lean_bridge_command,
    "auto_promote_candidate": build_auto_promote_command,
}

POST_REFRESH_HANDLERS = {
    "advance_closed_loop",
    "dispatch_execution_task",
    "run_literature_followup",
    "apply_candidate_split_contract",
    "reactivate_deferred_candidate",
    "spawn_followup_subtopics",
    "reintegrate_followup_subtopic",
    "assess_topic_completion",
    "prepare_lean_bridge",
    "auto_promote_candidate",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-slug")
    parser.add_argument("--action-id")
    parser.add_argument("--max-actions", type=int, default=1)
    parser.add_argument("--updated-by", default="openclaw")
    parser.add_argument("--continue-on-failure", action="store_true")
    return parser


def eligible_action(row: dict, requested_action_id: str | None) -> bool:
    if requested_action_id and row.get("action_id") != requested_action_id:
        return False
    return row.get("status") == "pending" and bool(row.get("auto_runnable"))


def load_decision_selected_action(topic_slug: str) -> dict:
    decision_path = topic_runtime_root(topic_slug) / NEXT_ACTION_DECISION_FILENAME
    payload = read_json(decision_path) or {}
    selected = payload.get("selected_action") or {}
    return {
        "decision_path": decision_path,
        "decision_mode": str(payload.get("decision_mode") or "").strip() or None,
        "reason": str(payload.get("reason") or "").strip() or None,
        "action_id": str(selected.get("action_id") or "").strip() or None,
        "auto_dispatch_allowed": bool(payload.get("auto_dispatch_allowed")),
    }


def build_orchestrate_refresh_command(topic_slug: str, updated_by: str, handler_args: dict) -> list[str]:
    command = [
        *python_command(),
        str(KNOWLEDGE_ROOT / "runtime" / "scripts" / "orchestrate_topic.py"),
        "--topic-slug",
        topic_slug,
        "--updated-by",
        updated_by,
    ]
    if handler_args.get("run_id"):
        command.extend(["--run-id", str(handler_args["run_id"])])
    if handler_args.get("control_note"):
        command.extend(["--control-note", str(handler_args["control_note"])])
    return command


def dispatch_one(
    queue_rows: list[dict],
    index: int,
    topic_slug: str,
    updated_by: str,
    receipts_path: Path,
) -> tuple[dict, int]:
    row = dict(queue_rows[index])
    dispatch_key = normalize_dispatch_target(row.get("handler"), row.get("action_type"))
    if dispatch_key not in ALLOWLIST:
        raise SystemExit(
            f"Action {row.get('action_id')} is not allowlisted for auto-dispatch: {row.get('handler')}"
        )

    started_at = now_iso()
    dispatch_count = int(row.get("dispatch_count", 0)) + 1
    running_row = {
        **row,
        "status": "running",
        "handler_key": dispatch_key,
        "dispatch_count": dispatch_count,
        "last_dispatched_at": started_at,
        "last_dispatched_by": updated_by,
        "started_at": started_at,
    }
    queue_rows[index] = running_row

    queue_path = topic_runtime_root(topic_slug) / "action_queue.jsonl"
    write_jsonl(queue_path, queue_rows)

    command = ALLOWLIST[dispatch_key](topic_slug, updated_by, running_row.get("handler_args") or {})
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )
    refresh_command = None
    refresh_completed = None
    if completed.returncode == 0 and dispatch_key in POST_REFRESH_HANDLERS:
        refresh_command = build_orchestrate_refresh_command(
            topic_slug,
            updated_by,
            running_row.get("handler_args") or {},
        )
    finished_at = now_iso()

    receipt = {
        "receipt_id": f"receipt:{running_row['action_id']}:{finished_at}",
        "action_id": running_row["action_id"],
        "topic_slug": topic_slug,
        "updated_at": finished_at,
        "updated_by": updated_by,
        "status": "completed" if completed.returncode == 0 else "failed",
        "handler": running_row.get("handler"),
        "handler_key": dispatch_key,
        "command": quote_command(command),
        "started_at": started_at,
        "finished_at": finished_at,
        "exit_code": completed.returncode,
        "stdout_tail": trim_text(completed.stdout),
        "stderr_tail": trim_text(completed.stderr),
    }
    append_jsonl(receipts_path, receipt)

    final_row = {
        **running_row,
        "status": receipt["status"],
        "finished_at": finished_at,
        "last_receipt_path": relative_to_research(receipts_path),
        "last_exit_code": completed.returncode,
    }
    if completed.returncode == 0:
        final_row.pop("last_error", None)
    else:
        final_row["last_error"] = trim_text(completed.stderr or completed.stdout)

    queue_rows[index] = final_row
    write_jsonl(queue_path, queue_rows)

    if refresh_command is not None:
        refresh_completed = subprocess.run(
            refresh_command,
            check=False,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
        )
        receipt["post_refresh_command"] = quote_command(refresh_command)
        receipt["post_refresh_exit_code"] = refresh_completed.returncode
        receipt["post_refresh_stdout_tail"] = trim_text(refresh_completed.stdout)
        receipt["post_refresh_stderr_tail"] = trim_text(refresh_completed.stderr)
        append_jsonl(receipts_path, {**receipt, "receipt_id": receipt["receipt_id"] + ":refresh"})

    return receipt, completed.returncode


def main() -> int:
    args = build_parser().parse_args()
    topic_slug = resolve_topic_slug(args.topic_slug)
    queue_path = topic_runtime_root(topic_slug) / "action_queue.jsonl"
    receipts_path = topic_runtime_root(topic_slug) / RECEIPTS_FILENAME
    printed_skipped: set[str] = set()
    dispatched = 0
    while dispatched < max(args.max_actions, 0):
        requested_action_id = args.action_id
        if requested_action_id is None:
            decision_selected = load_decision_selected_action(topic_slug)
            requested_action_id = decision_selected["action_id"]
            if not requested_action_id or not decision_selected["auto_dispatch_allowed"]:
                if dispatched == 0:
                    print(f"No auto-dispatchable decision-selected action for {topic_slug}")
                    print(
                        f"- decision_mode: {decision_selected['decision_mode'] or '(missing)'}"
                    )
                    print(f"- reason: {decision_selected['reason'] or '(missing)'}")
                    print(
                        f"- decision_path: {relative_to_research(decision_selected['decision_path'])}"
                    )
                break

        queue_rows = read_jsonl(queue_path)
        dispatch_index = None
        skipped: list[str] = []
        for index, row in enumerate(queue_rows):
            if not eligible_action(row, requested_action_id):
                continue
            dispatch_key = normalize_dispatch_target(row.get("handler"), row.get("action_type"))
            if dispatch_key in ALLOWLIST:
                dispatch_index = index
                break
            skipped.append(row.get("action_id") or f"index:{index}")

        fresh_skipped = [action_id for action_id in skipped if action_id not in printed_skipped]
        if fresh_skipped:
            print("Skipped non-allowlisted auto actions:")
            for action_id in fresh_skipped:
                printed_skipped.add(action_id)
                print(f"- {action_id}")

        if dispatch_index is None:
            if requested_action_id and dispatched == 0 and not skipped:
                if args.action_id:
                    raise SystemExit(f"No pending auto-runnable action matches {args.action_id!r}")
                print(
                    f"Decision-selected action is not currently pending and auto-runnable: {requested_action_id!r}"
                )
            break

        receipt, exit_code = dispatch_one(
            queue_rows=queue_rows,
            index=dispatch_index,
            topic_slug=topic_slug,
            updated_by=args.updated_by,
            receipts_path=receipts_path,
        )
        dispatched += 1
        print(
            f"Dispatched {receipt['action_id']} status={receipt['status']} receipts={relative_to_research(receipts_path)}"
        )
        if exit_code != 0 and not args.continue_on_failure:
            return exit_code
        if args.action_id:
            break

    if dispatched == 0:
        print(f"No allowlisted auto-runnable actions for {topic_slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
