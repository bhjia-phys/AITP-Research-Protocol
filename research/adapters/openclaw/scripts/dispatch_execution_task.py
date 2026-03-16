#!/usr/bin/env python3
"""Dispatch one minimal closed-loop execution task through Codex."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from codex_session_controller import (
    build_codex_exec_command,
    kill_session,
    start_codex_exec_session,
    wait_for_session,
)
from _aitp_runtime_common import (
    KNOWLEDGE_ROOT,
    RESEARCH_ROOT,
    append_jsonl,
    now_iso,
    quote_command,
    read_json,
    relative_to_research,
    resolve_topic_slug,
    topic_runtime_root,
)

RECEIPTS_FILENAME = "execution_handoff_receipts.jsonl"
WORKSPACE_ROOT = RESEARCH_ROOT.parent
RECOVERY_HINTS = ("fixture", "smoke", "control-path", "control path", "non-scientific", "demo")
DEFAULT_SESSION_TIMEOUT_SECONDS = 7200
DEFAULT_SESSION_POLL_INTERVAL_SECONDS = 2.0
SUPPORTED_CODEX_EXECUTORS = {"codex", "codex_cli", "openai_codex"}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def normalized_executor_kind(task_payload: dict) -> str:
    raw = str(task_payload.get("executor_kind") or task_payload.get("assigned_runtime") or "codex").strip().lower()
    return raw.replace("-", "_")


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return relative_to_research(path)


def resolve_workspace_root(task_payload: dict) -> Path:
    where_to_run = str(task_payload.get("where_to_run") or "").strip()
    if where_to_run == RESEARCH_ROOT.name:
        return WORKSPACE_ROOT
    return WORKSPACE_ROOT


def relative_to_knowledge(path: Path) -> str:
    try:
        return path.relative_to(KNOWLEDGE_ROOT).as_posix()
    except ValueError:
        return relative_to_research(path)


def parse_iso_datetime(raw_value: object) -> datetime | None:
    text = str(raw_value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def gather_result_artifacts(
    *,
    task_payload: dict,
    result_writeback_path: Path,
    execution_notes_dir: Path,
) -> tuple[list[str], list[str]]:
    validation_run_root = result_writeback_path.parent
    results_dir = validation_run_root / "results"
    allowed_inputs = {
        str(ref).strip()
        for ref in (task_payload.get("allowed_input_artifacts") or task_payload.get("input_artifacts") or [])
        if str(ref).strip()
    }
    planned_outputs = {
        str(ref).strip()
        for ref in (task_payload.get("planned_outputs") or [])
        if str(ref).strip()
    }
    materialized_at = parse_iso_datetime(task_payload.get("materialized_at"))
    result_artifacts: list[str] = []
    if results_dir.exists():
        for path in sorted(results_dir.iterdir()):
            if not path.is_file():
                continue
            relpath = relative_to_knowledge(path)
            if relpath in allowed_inputs:
                continue
            if path.name in {"result_manifest.json"}:
                continue
            if relpath in planned_outputs:
                result_artifacts.append(relpath)
                continue
            if materialized_at is None:
                continue
            modified_at = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
            if modified_at >= materialized_at:
                result_artifacts.append(relpath)

    logs: list[str] = []
    for path in (
        execution_notes_dir / "codex_exec_events.jsonl",
        execution_notes_dir / "codex_exec.stderr.txt",
        execution_notes_dir / "codex_last_message.md",
        execution_notes_dir / "codex_session.json",
        execution_notes_dir / "codex_session_receipts.jsonl",
    ):
        if path.exists():
            logs.append(relative_to_knowledge(path))
    return result_artifacts, logs


def extract_last_agent_message(events_path: Path) -> str | None:
    if not events_path.exists():
        return None
    last_text = None
    for raw_line in events_path.read_text(encoding="utf-8").splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            payload = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        item = payload.get("item") or {}
        if payload.get("type") == "item.completed" and item.get("type") == "agent_message":
            text = str(item.get("text") or "").strip()
            if text:
                last_text = text
    return last_text


def infer_fixture_backed(task_payload: dict) -> bool:
    task_text = " ".join(
        [
            str(task_payload.get("summary") or ""),
            str(task_payload.get("human_summary") or ""),
            " ".join(str(item) for item in (task_payload.get("pass_conditions") or [])),
            " ".join(str(item) for item in (task_payload.get("failure_signals") or [])),
        ]
    ).lower()
    return any(hint in task_text for hint in RECOVERY_HINTS)


def attempt_result_recovery(
    *,
    task_payload: dict,
    result_writeback_path: Path,
    execution_notes_dir: Path,
    last_message_path: Path,
    events_path: Path,
) -> dict | None:
    if result_writeback_path.exists():
        return read_json(result_writeback_path)

    result_artifacts, logs = gather_result_artifacts(
        task_payload=task_payload,
        result_writeback_path=result_writeback_path,
        execution_notes_dir=execution_notes_dir,
    )
    if not result_artifacts:
        return None

    if not last_message_path.exists():
        recovered_last_message = extract_last_agent_message(events_path)
        if recovered_last_message:
            write_text(last_message_path, recovered_last_message.rstrip() + "\n")
            logs = gather_result_artifacts(
                task_payload=task_payload,
                result_writeback_path=result_writeback_path,
                execution_notes_dir=execution_notes_dir,
            )[1]

    fixture_backed = infer_fixture_backed(task_payload)
    produced_by = "openclaw-adapter:dispatch_execution_task"
    recovered_payload = {
        "result_id": (
            f"recovered-result:{task_payload.get('task_id') or 'task'}:{now_iso().replace(':', '-').replace('+', '_')}"
        ),
        "task_id": task_payload.get("task_id"),
        "status": "partial",
        "artifacts": result_artifacts,
        "metrics": {
            "artifact_count": len(result_artifacts),
            "log_count": len(logs),
        },
        "logs": logs,
        "produced_by": produced_by,
        "created_at": now_iso(),
        "what_was_attempted": task_payload.get("human_summary") or task_payload.get("summary"),
        "what_actually_ran": (
            "The Codex execution lane produced durable result artifacts, but it did not write the required "
            "`returned_execution_result.json`. The OpenClaw adapter recovered this partial result from the "
            "recorded artifacts instead of claiming a clean executor-authored success."
        ),
        "summary": (
            "Recovered a bounded partial execution result from durable artifacts so the closed-loop runtime can "
            "ingest an honest writeback instead of stalling on a missing return JSON."
        ),
        "limitations": [
            "The external executor omitted the required returned execution result JSON.",
            "This payload was reconstructed by the adapter from durable artifacts and execution notes.",
        ],
        "non_conclusions": [
            "This recovered writeback is not by itself a validated scientific conclusion.",
            "Any route keep/promote decision still requires inspecting the produced artifacts directly.",
        ],
        "notes": "Adapter-authored recovery payload generated because durable artifacts existed without the required return JSON.",
        "research_mode": task_payload.get("research_mode"),
        "executor_kind": task_payload.get("executor_kind") or task_payload.get("assigned_runtime"),
        "reasoning_profile": task_payload.get("reasoning_profile"),
        "fixture_backed": fixture_backed,
        "non_scientific": fixture_backed,
        "recommended_decision": "defer",
        "decision_reason": (
            "Defer scientific adjudication because the executor produced artifacts but missed the formal return "
            "contract, so the runtime should preserve the evidence and continue with bounded follow-up only."
        ),
        "needs_literature_followup": fixture_backed,
    }
    write_json(result_writeback_path, recovered_payload)
    return recovered_payload


def build_prompt(
    *,
    topic_slug: str,
    run_id: str | None,
    task_payload: dict,
    task_json_path: Path,
    task_md_path: Path,
    agent_brief_path: Path,
    result_template_path: Path,
    result_writeback_path: Path,
    workspace_root: Path,
) -> str:
    allowed_inputs = task_payload.get("allowed_input_artifacts") or task_payload.get("input_artifacts") or []
    planned_outputs = task_payload.get("planned_outputs") or []
    pass_conditions = task_payload.get("pass_conditions") or []
    failure_signals = task_payload.get("failure_signals") or []

    lines = [
        "You are the external execution lane for one AITP minimal closed-loop task.",
        "",
        f"Workspace root: `{relative_to_root(workspace_root, workspace_root) or '.'}`",
        f"Topic slug: `{topic_slug}`",
        f"Run id: `{run_id or '(missing)'}`",
        f"Task id: `{task_payload.get('task_id') or '(missing)'}`",
        f"Route id: `{task_payload.get('route_id') or '(missing)'}`",
        f"Research mode: `{task_payload.get('research_mode') or '(missing)'}`",
        f"Assigned runtime: `{task_payload.get('assigned_runtime') or 'codex'}`",
        f"Executor kind: `{task_payload.get('executor_kind') or task_payload.get('assigned_runtime') or 'codex'}`",
        f"Reasoning profile: `{task_payload.get('reasoning_profile') or '(missing)'}`",
        f"Surface: `{task_payload.get('surface') or '(missing)'}`",
        f"Allow web search: `{str(bool(task_payload.get('allow_web_search'))).lower()}`",
        "",
        "Read these files first:",
        f"- `{relative_to_root(workspace_root / 'AGENTS.md', workspace_root)}`",
        f"- `{relative_to_root(task_json_path, workspace_root)}`",
        f"- `{relative_to_root(task_md_path, workspace_root)}`",
        f"- `{relative_to_root(agent_brief_path, workspace_root)}`",
        f"- `{relative_to_root(result_template_path, workspace_root)}`",
        "",
        "Execution contract:",
        f"- Main objective: {task_payload.get('human_summary') or task_payload.get('summary') or '(missing)'}",
        f"- Write the returned result JSON to `{relative_to_root(result_writeback_path, workspace_root)}`.",
        "- The returned result must follow the template fields and remain honest about what actually ran.",
        "- If you create output artifacts, ensure those files exist and list them in the returned result JSON.",
        "- If you cannot honestly complete a real experiment, still write a truthful `partial` or `failed` result instead of leaving the return artifact missing.",
        "- Do not overclaim scientific conclusions. Put hard limits in `limitations` and `non_conclusions`.",
        "- If the result is inconclusive, contradictory, or needs baseline context, include bounded `literature_followup_queries`.",
        "",
        "Allowed input artifacts:",
    ]
    if allowed_inputs:
        for artifact in allowed_inputs:
            lines.append(f"- `{artifact}`")
    else:
        lines.append("- `(none declared)`")

    lines.extend(["", "Expected outputs:"])
    if planned_outputs:
        for artifact in planned_outputs:
            lines.append(f"- `{artifact}`")
    else:
        lines.append("- `(none declared)`")

    lines.extend(
        [
            "",
            "Artifact path convention:",
            "- Open files from the workspace root; knowledge-hub artifacts live on disk under `research/knowledge-hub/...`.",
            "- In `returned_execution_result.json`, preserve artifact refs in canonical knowledge-hub-relative form exactly as declared in this task, for example `validation/...` or `feedback/...`.",
            "- Do not rewrite artifact refs with a `research/knowledge-hub/` prefix inside the returned result JSON.",
        ]
    )

    lines.extend(["", "Pass conditions:"])
    if pass_conditions:
        for condition in pass_conditions:
            lines.append(f"- {condition}")
    else:
        lines.append("- `(none declared)`")

    lines.extend(["", "Failure signals:"])
    if failure_signals:
        for signal in failure_signals:
            lines.append(f"- {signal}")
    else:
        lines.append("- `(none declared)`")

    lines.extend(["", "Reproducibility requirements:"])
    reproducibility_requirements = task_payload.get("reproducibility_requirements") or []
    if reproducibility_requirements:
        for item in reproducibility_requirements:
            lines.append(f"- {item}")
    else:
        lines.append("- `(none declared)`")

    lines.extend(["", "Human-readable notes required:"])
    required_human_notes = task_payload.get("required_human_notes") or []
    if required_human_notes:
        for item in required_human_notes:
            lines.append(f"- {item}")
    else:
        lines.append("- `(none declared)`")

    lines.extend(
        [
            "",
            "Return a concise final report with these exact sections:",
            "## Goal",
            "## Scope",
            "## Changed files",
            "## What I did",
            "## Verification",
            "## Not verified",
            "## Risks / assumptions / open questions",
            "## Next steps",
        ]
    )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-slug")
    parser.add_argument("--run-id")
    parser.add_argument("--updated-by", default="openclaw")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    topic_slug = resolve_topic_slug(args.topic_slug)
    runtime_root = topic_runtime_root(topic_slug)
    task_json_path = runtime_root / "execution_task.json"
    task_md_path = runtime_root / "execution_task.md"
    agent_brief_path = runtime_root / "agent_brief.md"
    task_payload = read_json(task_json_path)
    if task_payload is None:
        raise SystemExit(f"Missing execution task: {task_json_path}")

    executor_kind = normalized_executor_kind(task_payload)
    if executor_kind not in SUPPORTED_CODEX_EXECUTORS:
        raise SystemExit(
            "dispatch_execution_task currently supports executor_kind in "
            f"{sorted(SUPPORTED_CODEX_EXECUTORS)}; got {executor_kind}"
        )
    if not bool(task_payload.get("auto_dispatch_allowed")):
        raise SystemExit("Execution task does not allow automatic dispatch")

    run_id = args.run_id or task_payload.get("run_id")
    result_writeback_ref = task_payload.get("result_writeback_path")
    if not result_writeback_ref:
        raise SystemExit("Execution task is missing result_writeback_path")
    result_writeback_path = KNOWLEDGE_ROOT / str(result_writeback_ref)
    if result_writeback_path.exists():
        raise SystemExit(f"Returned result already exists: {result_writeback_path}")

    result_template_ref = task_payload.get("result_template_path")
    if not result_template_ref:
        raise SystemExit("Execution task is missing result_template_path")
    result_template_path = KNOWLEDGE_ROOT / str(result_template_ref)

    execution_notes_ref = task_payload.get("execution_notes_dir")
    execution_notes_dir = (
        KNOWLEDGE_ROOT / str(execution_notes_ref)
        if execution_notes_ref
        else result_writeback_path.parent / "execution_notes"
    )
    execution_notes_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = execution_notes_dir / "codex_handoff_prompt.md"
    events_path = execution_notes_dir / "codex_exec_events.jsonl"
    stderr_path = execution_notes_dir / "codex_exec.stderr.txt"
    last_message_path = execution_notes_dir / "codex_last_message.md"
    session_metadata_path = execution_notes_dir / "codex_session.json"
    session_receipts_path = execution_notes_dir / "codex_session_receipts.jsonl"
    workspace_root = resolve_workspace_root(task_payload)

    prompt = build_prompt(
        topic_slug=topic_slug,
        run_id=str(run_id) if run_id else None,
        task_payload=task_payload,
        task_json_path=task_json_path,
        task_md_path=task_md_path,
        agent_brief_path=agent_brief_path,
        result_template_path=result_template_path,
        result_writeback_path=result_writeback_path,
        workspace_root=workspace_root,
    )
    write_text(prompt_path, prompt)
    command = build_codex_exec_command(
        workspace_root=workspace_root,
        prompt_text=prompt,
        last_message_path=last_message_path,
        allow_web_search=bool(task_payload.get("allow_web_search")),
        reasoning_profile=str(task_payload.get("reasoning_profile") or "") or None,
    )

    receipt = {
        "handoff_id": f"execution-handoff:{topic_slug}:{task_payload.get('task_id')}:{now_iso()}",
        "topic_slug": topic_slug,
        "run_id": run_id,
        "task_id": task_payload.get("task_id"),
        "route_id": task_payload.get("route_id"),
        "updated_at": now_iso(),
        "updated_by": args.updated_by,
        "research_mode": task_payload.get("research_mode"),
        "executor_kind": task_payload.get("executor_kind") or task_payload.get("assigned_runtime"),
        "reasoning_profile": task_payload.get("reasoning_profile"),
        "command": quote_command(command),
        "workspace_root": relative_to_root(workspace_root, workspace_root) or ".",
        "prompt_path": relative_to_root(prompt_path, workspace_root),
        "events_path": relative_to_root(events_path, workspace_root),
        "stderr_path": relative_to_root(stderr_path, workspace_root),
        "last_message_path": relative_to_root(last_message_path, workspace_root),
        "codex_session_path": relative_to_root(session_metadata_path, workspace_root),
        "codex_session_receipts_path": relative_to_root(session_receipts_path, workspace_root),
        "result_writeback_path": relative_to_root(result_writeback_path, workspace_root),
        "dispatch_mode": "tmux_codex_exec_session",
    }

    if args.dry_run:
        print(json.dumps({**receipt, "dry_run": True}, ensure_ascii=True, indent=2))
        return 0

    recovered_before_dispatch = attempt_result_recovery(
        task_payload=task_payload,
        result_writeback_path=result_writeback_path,
        execution_notes_dir=execution_notes_dir,
        last_message_path=last_message_path,
        events_path=events_path,
    )
    if recovered_before_dispatch is not None:
        receipt["command_executed"] = False
        receipt["exit_code"] = 0
        receipt["result_present"] = True
        receipt["result_recovered"] = True
        receipt["status"] = "completed"
        append_jsonl(runtime_root / RECEIPTS_FILENAME, receipt)
        print(json.dumps(receipt, ensure_ascii=True))
        return 0

    session_state = start_codex_exec_session(
        metadata_path=session_metadata_path,
        workspace_root=workspace_root,
        prompt_path=prompt_path,
        prompt_text=prompt,
        events_path=events_path,
        stderr_path=stderr_path,
        last_message_path=last_message_path,
        updated_by=args.updated_by,
        topic_slug=topic_slug,
        run_id=str(run_id) if run_id else None,
        task_id=str(task_payload.get("task_id") or "") or None,
        allow_web_search=bool(task_payload.get("allow_web_search")),
        reasoning_profile=str(task_payload.get("reasoning_profile") or "") or None,
        result_writeback_path=result_writeback_path,
        receipts_path=session_receipts_path,
    )
    receipt["session_id"] = session_state.get("session_id")
    receipt["tmux_session_name"] = session_state.get("tmux_session_name")

    timeout_seconds = int(
        task_payload.get("codex_session_timeout_seconds") or DEFAULT_SESSION_TIMEOUT_SECONDS
    )
    poll_interval_seconds = float(
        task_payload.get("codex_session_poll_interval_seconds")
        or DEFAULT_SESSION_POLL_INTERVAL_SECONDS
    )
    try:
        session_state = wait_for_session(
            session_metadata_path,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
    except TimeoutError as exc:
        result_payload = read_json(result_writeback_path)
        if result_payload is None:
            result_payload = attempt_result_recovery(
                task_payload=task_payload,
                result_writeback_path=result_writeback_path,
                execution_notes_dir=execution_notes_dir,
                last_message_path=last_message_path,
                events_path=events_path,
            )
        if result_payload is not None:
            session_kill_error = None
            try:
                session_state = kill_session(session_metadata_path)
            except SystemExit as kill_exc:
                session_kill_error = str(kill_exc)
                session_state = read_json(session_metadata_path) or {}
            receipt["command_executed"] = True
            receipt["exit_code"] = session_state.get("exit_code")
            receipt["result_present"] = True
            receipt["result_recovered"] = (
                str((result_payload or {}).get("produced_by") or "")
                == "openclaw-adapter:dispatch_execution_task"
            )
            receipt["status"] = "completed"
            receipt["timed_out"] = True
            receipt["timeout_message"] = str(exc)
            receipt["session_killed_after_result"] = True
            if session_kill_error:
                receipt["session_kill_error"] = session_kill_error
            append_jsonl(runtime_root / RECEIPTS_FILENAME, receipt)
            print(json.dumps(receipt, ensure_ascii=True))
            return 0
        receipt["command_executed"] = True
        receipt["exit_code"] = None
        receipt["result_present"] = result_writeback_path.exists()
        receipt["result_recovered"] = False
        receipt["status"] = "failed"
        receipt["timed_out"] = True
        append_jsonl(runtime_root / RECEIPTS_FILENAME, receipt)
        raise SystemExit(str(exc))

    result_payload = read_json(result_writeback_path)
    completed_returncode = session_state.get("exit_code")
    if completed_returncode == 0 and result_payload is None:
        result_payload = attempt_result_recovery(
            task_payload=task_payload,
            result_writeback_path=result_writeback_path,
            execution_notes_dir=execution_notes_dir,
            last_message_path=last_message_path,
            events_path=events_path,
        )
    receipt["exit_code"] = completed_returncode
    receipt["command_executed"] = True
    receipt["result_present"] = result_payload is not None
    receipt["result_recovered"] = (
        bool(result_payload)
        and str((result_payload or {}).get("produced_by") or "") == "openclaw-adapter:dispatch_execution_task"
    )
    receipt["status"] = "completed" if completed_returncode == 0 and result_payload is not None else "failed"
    append_jsonl(runtime_root / RECEIPTS_FILENAME, receipt)

    if completed_returncode != 0:
        raise SystemExit(f"Codex execution failed for {topic_slug}: exit_code={completed_returncode}")
    if result_payload is None:
        raise SystemExit(f"Codex finished without writing {result_writeback_path}")

    print(json.dumps(receipt, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
