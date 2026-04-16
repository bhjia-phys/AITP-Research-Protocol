#!/usr/bin/env python3
"""Manage Codex background sessions for OpenClaw using tmux."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from _aitp_runtime_common import append_jsonl, now_iso, quote_command, read_json, trim_text, write_json

RECEIPTS_FILENAME = "codex_session_receipts.jsonl"
DEFAULT_TIMEOUT_SECONDS = 7200
DEFAULT_POLL_INTERVAL_SECONDS = 2.0


def ensure_dependencies() -> None:
    if shutil.which("tmux") is None:
        raise SystemExit("Missing required dependency: tmux")
    if shutil.which("codex") is None:
        raise SystemExit("Missing required dependency: codex")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_parent(path)
    path.write_text(text, encoding="utf-8")


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def sanitize_token(text: str, limit: int = 24) -> str:
    token = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    token = re.sub(r"-{2,}", "-", token)
    return (token or "session")[:limit]


def default_tmux_session_name(topic_slug: str | None, task_id: str | None, session_kind: str) -> str:
    timestamp = now_iso().replace(":", "").replace("+", "_").replace("-", "")
    parts = [
        "codex",
        sanitize_token(session_kind, limit=12),
        sanitize_token(topic_slug or "topic"),
        sanitize_token(task_id or "task"),
        sanitize_token(timestamp, limit=24),
    ]
    return "-".join(part for part in parts if part)


def default_exit_code_path(metadata_path: Path) -> Path:
    return metadata_path.with_name("codex_session.exit_code.txt")


def default_completed_at_path(metadata_path: Path) -> Path:
    return metadata_path.with_name("codex_session.completed_at.txt")


def default_receipts_path(metadata_path: Path) -> Path:
    return metadata_path.with_name(RECEIPTS_FILENAME)


def monitor_commands(metadata_path: Path) -> dict[str, str]:
    script_path = Path(__file__).resolve()
    quoted_metadata = shlex.quote(str(metadata_path))
    base = f"python3 {shlex.quote(str(script_path))}"
    return {
        "status": f"{base} status --metadata-path {quoted_metadata}",
        "log": f"{base} log --metadata-path {quoted_metadata}",
        "submit_yes": f"{base} submit --metadata-path {quoted_metadata} --text y",
        "kill": f"{base} kill --metadata-path {quoted_metadata}",
        "wait": f"{base} wait --metadata-path {quoted_metadata}",
    }


def tmux_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["tmux", *args], check=False, capture_output=True, text=True, stdin=subprocess.DEVNULL)


def tmux_session_alive(session_name: str) -> bool:
    return tmux_command(["has-session", "-t", session_name]).returncode == 0


def read_exit_code(path: Path) -> int | None:
    text = read_text(path)
    if text is None:
        return None
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return int(stripped)
    except ValueError:
        return None


def read_tail(path: Path, limit: int) -> str:
    text = read_text(path)
    if text is None:
        return ""
    return trim_text(text[-limit:], limit=limit)


def read_completed_at(path: Path) -> str | None:
    text = read_text(path)
    if text is None:
        return None
    stripped = text.strip()
    return stripped or None


def normalize_reasoning_profile(reasoning_profile: str | None) -> str | None:
    if not reasoning_profile:
        return None
    token = str(reasoning_profile).strip().lower().replace("-", "_")
    aliases = {
        "xhigh": "high",
        "very_high": "high",
        "max": "high",
        "default": None,
        "standard": None,
    }
    normalized = aliases.get(token, token)
    if normalized in {None, "off", "none"}:
        return None
    if normalized not in {"minimal", "low", "medium", "high"}:
        return None
    return normalized


def build_codex_exec_command(
    *,
    workspace_root: Path,
    prompt_text: str,
    last_message_path: Path,
    allow_web_search: bool = False,
    reasoning_profile: str | None = None,
) -> list[str]:
    command = [
        "codex",
        "exec",
        "--cd",
        str(workspace_root),
        "--dangerously-bypass-approvals-and-sandbox",
        "--output-last-message",
        str(last_message_path),
        "--json",
    ]
    normalized_reasoning = normalize_reasoning_profile(reasoning_profile)
    if normalized_reasoning:
        command.extend(["-c", f'model_reasoning_effort="{normalized_reasoning}"'])
    if allow_web_search:
        command.append("--search")
    command.append(prompt_text)
    return command


def build_codex_resume_command(
    *,
    workspace_root: Path,
    resume_target: str | None,
    prompt_text: str | None,
    allow_web_search: bool = False,
) -> list[str]:
    command = [
        "codex",
        "resume",
        "--cd",
        str(workspace_root),
        "--dangerously-bypass-approvals-and-sandbox",
    ]
    if allow_web_search:
        command.append("--search")
    if resume_target:
        command.append(resume_target)
    else:
        command.append("--last")
    if prompt_text:
        command.append(prompt_text)
    return command


def build_tmux_shell_command(
    *,
    command: list[str],
    stderr_path: Path,
    exit_code_path: Path,
    completed_at_path: Path,
) -> str:
    inner = (
        f"{quote_command(command)}"
        f" 2> {shlex.quote(str(stderr_path))}; "
        "rc=$?; "
        f"printf '%s\\n' \"$rc\" > {shlex.quote(str(exit_code_path))}; "
        f"printf '%s\\n' \"$(date -Iseconds)\" > {shlex.quote(str(completed_at_path))}; "
        "exit \"$rc\""
    )
    return f"bash --noprofile --norc -lc {shlex.quote(inner)}"


def append_receipt(metadata: dict, action: str, **extra: object) -> None:
    receipts_path = Path(str(metadata["receipts_path"]))
    append_jsonl(
        receipts_path,
        {
            "recorded_at": now_iso(),
            "action": action,
            "session_id": metadata.get("session_id"),
            "tmux_session_name": metadata.get("tmux_session_name"),
            "status": metadata.get("status"),
            "exit_code": metadata.get("exit_code"),
            **extra,
        },
    )


def refresh_session_metadata(metadata_path: Path) -> dict:
    payload = read_json(metadata_path)
    if payload is None:
        raise SystemExit(f"Missing metadata file: {metadata_path}")

    session_name = str(payload.get("tmux_session_name") or "").strip()
    if not session_name:
        raise SystemExit(f"Metadata file is missing tmux_session_name: {metadata_path}")

    exit_code_path = Path(str(payload["exit_code_path"]))
    completed_at_path = Path(str(payload["completed_at_path"]))
    result_writeback_path = str(payload.get("result_writeback_path") or "").strip()
    events_path = Path(str(payload["events_path"]))
    stderr_path = Path(str(payload["stderr_path"]))
    last_message_path = str(payload.get("last_message_path") or "").strip()

    tmux_alive = tmux_session_alive(session_name)
    exit_code = read_exit_code(exit_code_path)
    completed_at = read_completed_at(completed_at_path)
    prior_status = str(payload.get("status") or "").strip()

    if prior_status == "killed" and not tmux_alive:
        status = "killed"
    elif exit_code == 0:
        status = "completed"
    elif exit_code is not None:
        status = "failed"
    elif tmux_alive:
        status = "running"
    else:
        status = "unknown"

    payload.update(
        {
            "status": status,
            "updated_at": now_iso(),
            "tmux_session_alive": tmux_alive,
            "exit_code": exit_code,
            "completed_at": completed_at,
            "events_bytes": events_path.stat().st_size if events_path.exists() else 0,
            "stderr_bytes": stderr_path.stat().st_size if stderr_path.exists() else 0,
            "last_message_present": bool(last_message_path) and Path(last_message_path).exists(),
            "result_present": bool(result_writeback_path) and Path(result_writeback_path).exists(),
        }
    )
    write_json(metadata_path, payload)
    return payload


def start_session_for_command(
    *,
    command: list[str],
    metadata_path: Path,
    workspace_root: Path,
    events_path: Path,
    stderr_path: Path,
    session_kind: str,
    updated_by: str,
    topic_slug: str | None = None,
    run_id: str | None = None,
    task_id: str | None = None,
    prompt_path: Path | None = None,
    last_message_path: Path | None = None,
    result_writeback_path: Path | None = None,
    session_name: str | None = None,
    receipts_path: Path | None = None,
    extra_metadata: dict | None = None,
) -> dict:
    ensure_dependencies()

    metadata_path = metadata_path.resolve()
    events_path = events_path.resolve()
    stderr_path = stderr_path.resolve()
    workspace_root = workspace_root.resolve()
    ensure_parent(metadata_path)
    ensure_parent(events_path)
    ensure_parent(stderr_path)

    existing = read_json(metadata_path)
    if existing is not None:
        existing_session = str(existing.get("tmux_session_name") or "").strip()
        if existing_session and tmux_session_alive(existing_session):
            raise SystemExit(
                f"Refusing to overwrite active Codex session metadata: {metadata_path}"
            )

    events_path.write_text("", encoding="utf-8")
    stderr_path.write_text("", encoding="utf-8")

    receipts_path = (receipts_path or default_receipts_path(metadata_path)).resolve()
    exit_code_path = default_exit_code_path(metadata_path).resolve()
    completed_at_path = default_completed_at_path(metadata_path).resolve()
    if exit_code_path.exists():
        exit_code_path.unlink()
    if completed_at_path.exists():
        completed_at_path.unlink()

    resolved_session_name = session_name or default_tmux_session_name(topic_slug, task_id, session_kind)
    shell_command = build_tmux_shell_command(
        command=command,
        stderr_path=stderr_path,
        exit_code_path=exit_code_path,
        completed_at_path=completed_at_path,
    )
    created_at = now_iso()
    session_id = f"{session_kind}:{resolved_session_name}"

    metadata = {
        "session_format_version": 1,
        "controller": "openclaw.codex_session_controller",
        "session_kind": session_kind,
        "session_id": session_id,
        "tmux_session_name": resolved_session_name,
        "topic_slug": topic_slug,
        "run_id": run_id,
        "task_id": task_id,
        "status": "starting",
        "created_at": created_at,
        "updated_at": created_at,
        "updated_by": updated_by,
        "workspace_root": str(workspace_root),
        "prompt_path": str(prompt_path.resolve()) if prompt_path else None,
        "last_message_path": str(last_message_path.resolve()) if last_message_path else None,
        "events_path": str(events_path),
        "stderr_path": str(stderr_path),
        "metadata_path": str(metadata_path),
        "receipts_path": str(receipts_path),
        "exit_code_path": str(exit_code_path),
        "completed_at_path": str(completed_at_path),
        "result_writeback_path": str(result_writeback_path.resolve()) if result_writeback_path else None,
        "codex_command": quote_command(command),
        "tmux_shell_command": shell_command,
        "monitor_commands": monitor_commands(metadata_path),
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    start_result = tmux_command(["new-session", "-d", "-s", resolved_session_name, shell_command])
    if start_result.returncode != 0:
        raise SystemExit(
            f"Failed to start tmux session {resolved_session_name}: {trim_text(start_result.stderr)}"
        )

    pipe_command = f"cat >> {shlex.quote(str(events_path))}"
    pipe_result = tmux_command(["pipe-pane", "-o", "-t", resolved_session_name, pipe_command])
    if pipe_result.returncode != 0:
        tmux_command(["kill-session", "-t", resolved_session_name])
        raise SystemExit(
            f"Failed to attach tmux pipe for {resolved_session_name}: {trim_text(pipe_result.stderr)}"
        )

    write_json(metadata_path, metadata)
    refreshed = refresh_session_metadata(metadata_path)
    append_receipt(
        refreshed,
        "started",
        command=refreshed["codex_command"],
        prompt_path=refreshed.get("prompt_path"),
    )
    return refreshed


def start_codex_exec_session(
    *,
    metadata_path: Path,
    workspace_root: Path,
    prompt_path: Path,
    prompt_text: str,
    events_path: Path,
    stderr_path: Path,
    last_message_path: Path,
    updated_by: str,
    topic_slug: str | None = None,
    run_id: str | None = None,
    task_id: str | None = None,
    allow_web_search: bool = False,
    reasoning_profile: str | None = None,
    result_writeback_path: Path | None = None,
    receipts_path: Path | None = None,
    session_name: str | None = None,
) -> dict:
    command = build_codex_exec_command(
        workspace_root=workspace_root,
        prompt_text=prompt_text,
        last_message_path=last_message_path,
        allow_web_search=allow_web_search,
        reasoning_profile=reasoning_profile,
    )
    return start_session_for_command(
        command=command,
        metadata_path=metadata_path,
        workspace_root=workspace_root,
        events_path=events_path,
        stderr_path=stderr_path,
        session_kind="codex_exec",
        updated_by=updated_by,
        topic_slug=topic_slug,
        run_id=run_id,
        task_id=task_id,
        prompt_path=prompt_path,
        last_message_path=last_message_path,
        result_writeback_path=result_writeback_path,
        receipts_path=receipts_path,
        session_name=session_name,
        extra_metadata={"reasoning_profile": normalize_reasoning_profile(reasoning_profile) or reasoning_profile},
    )


def start_codex_resume_session(
    *,
    metadata_path: Path,
    workspace_root: Path,
    events_path: Path,
    stderr_path: Path,
    updated_by: str,
    topic_slug: str | None = None,
    run_id: str | None = None,
    task_id: str | None = None,
    resume_target: str | None = None,
    prompt_text: str | None = None,
    allow_web_search: bool = False,
    receipts_path: Path | None = None,
    session_name: str | None = None,
) -> dict:
    command = build_codex_resume_command(
        workspace_root=workspace_root,
        resume_target=resume_target,
        prompt_text=prompt_text,
        allow_web_search=allow_web_search,
    )
    return start_session_for_command(
        command=command,
        metadata_path=metadata_path,
        workspace_root=workspace_root,
        events_path=events_path,
        stderr_path=stderr_path,
        session_kind="codex_resume",
        updated_by=updated_by,
        topic_slug=topic_slug,
        run_id=run_id,
        task_id=task_id,
        receipts_path=receipts_path,
        session_name=session_name,
        extra_metadata={
            "resume_target": resume_target or "--last",
            "resume_prompt": prompt_text,
        },
    )


def wait_for_session(
    metadata_path: Path,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
) -> dict:
    started = time.monotonic()
    while True:
        payload = refresh_session_metadata(metadata_path)
        if payload["status"] != "running":
            append_receipt(
                payload,
                "wait_completed",
                result_present=payload.get("result_present"),
            )
            return payload
        if timeout_seconds >= 0 and (time.monotonic() - started) > timeout_seconds:
            payload["wait_timeout_at"] = now_iso()
            payload["updated_at"] = payload["wait_timeout_at"]
            write_json(metadata_path, payload)
            append_receipt(payload, "wait_timed_out", timeout_seconds=timeout_seconds)
            raise TimeoutError(
                f"Timed out waiting for Codex session after {timeout_seconds}s: {metadata_path}"
            )
        time.sleep(max(poll_interval_seconds, 0.1))


def submit_to_session(metadata_path: Path, text: str, press_enter: bool = True) -> dict:
    payload = refresh_session_metadata(metadata_path)
    session_name = str(payload["tmux_session_name"])
    if payload["status"] != "running":
        raise SystemExit(f"Cannot submit to non-running session: {payload['status']}")

    send_result = tmux_command(["send-keys", "-t", session_name, "-l", text])
    if send_result.returncode != 0:
        raise SystemExit(
            f"Failed to submit text to tmux session {session_name}: {trim_text(send_result.stderr)}"
        )
    if press_enter:
        enter_result = tmux_command(["send-keys", "-t", session_name, "Enter"])
        if enter_result.returncode != 0:
            raise SystemExit(
                f"Failed to submit Enter to tmux session {session_name}: {trim_text(enter_result.stderr)}"
            )

    payload = refresh_session_metadata(metadata_path)
    append_receipt(payload, "submitted_input", submitted_text_preview=trim_text(text, limit=80))
    return payload


def kill_session(metadata_path: Path) -> dict:
    payload = refresh_session_metadata(metadata_path)
    session_name = str(payload["tmux_session_name"])
    if tmux_session_alive(session_name):
        kill_result = tmux_command(["kill-session", "-t", session_name])
        if kill_result.returncode != 0:
            raise SystemExit(
                f"Failed to kill tmux session {session_name}: {trim_text(kill_result.stderr)}"
            )
    payload = refresh_session_metadata(metadata_path)
    payload["status"] = "killed"
    payload["killed_at"] = now_iso()
    payload["updated_at"] = payload["killed_at"]
    write_json(metadata_path, payload)
    append_receipt(payload, "killed")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Start a Codex exec session in tmux.")
    start_parser.add_argument("--metadata-path", required=True)
    start_parser.add_argument("--workspace-root", required=True)
    start_parser.add_argument("--prompt-file", required=True)
    start_parser.add_argument("--events-path", required=True)
    start_parser.add_argument("--stderr-path", required=True)
    start_parser.add_argument("--last-message-path", required=True)
    start_parser.add_argument("--result-writeback-path")
    start_parser.add_argument("--topic-slug")
    start_parser.add_argument("--run-id")
    start_parser.add_argument("--task-id")
    start_parser.add_argument("--updated-by", default="openclaw")
    start_parser.add_argument("--session-name")
    start_parser.add_argument("--receipts-path")
    start_parser.add_argument("--search", action="store_true")
    start_parser.add_argument("--reasoning-profile")

    resume_parser = subparsers.add_parser("resume", help="Start a Codex resume session in tmux.")
    resume_parser.add_argument("--metadata-path", required=True)
    resume_parser.add_argument("--workspace-root", required=True)
    resume_parser.add_argument("--events-path", required=True)
    resume_parser.add_argument("--stderr-path", required=True)
    resume_parser.add_argument("--topic-slug")
    resume_parser.add_argument("--run-id")
    resume_parser.add_argument("--task-id")
    resume_parser.add_argument("--updated-by", default="openclaw")
    resume_parser.add_argument("--session-name")
    resume_parser.add_argument("--receipts-path")
    resume_parser.add_argument("--resume-target")
    resume_parser.add_argument("--prompt")
    resume_parser.add_argument("--search", action="store_true")

    status_parser = subparsers.add_parser("status", help="Refresh and print session status.")
    status_parser.add_argument("--metadata-path", required=True)

    log_parser = subparsers.add_parser("log", help="Print a tail view of the session log.")
    log_parser.add_argument("--metadata-path", required=True)
    log_parser.add_argument("--limit", type=int, default=2000)

    submit_parser = subparsers.add_parser("submit", help="Submit text to a running tmux session.")
    submit_parser.add_argument("--metadata-path", required=True)
    submit_parser.add_argument("--text", required=True)
    submit_parser.add_argument("--no-enter", action="store_true")

    kill_parser = subparsers.add_parser("kill", help="Kill the tmux session and update metadata.")
    kill_parser.add_argument("--metadata-path", required=True)

    wait_parser = subparsers.add_parser("wait", help="Wait for the session to finish.")
    wait_parser.add_argument("--metadata-path", required=True)
    wait_parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    wait_parser.add_argument("--poll-interval-seconds", type=float, default=DEFAULT_POLL_INTERVAL_SECONDS)
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "start":
        prompt_path = Path(args.prompt_file).resolve()
        prompt_text = prompt_path.read_text(encoding="utf-8")
        payload = start_codex_exec_session(
            metadata_path=Path(args.metadata_path),
            workspace_root=Path(args.workspace_root),
            prompt_path=prompt_path,
            prompt_text=prompt_text,
            events_path=Path(args.events_path),
            stderr_path=Path(args.stderr_path),
            last_message_path=Path(args.last_message_path),
            updated_by=args.updated_by,
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            task_id=args.task_id,
            allow_web_search=bool(args.search),
            reasoning_profile=args.reasoning_profile,
            result_writeback_path=Path(args.result_writeback_path) if args.result_writeback_path else None,
            receipts_path=Path(args.receipts_path) if args.receipts_path else None,
            session_name=args.session_name,
        )
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    metadata_path = Path(args.metadata_path).resolve()

    if args.command == "resume":
        payload = start_codex_resume_session(
            metadata_path=metadata_path,
            workspace_root=Path(args.workspace_root),
            events_path=Path(args.events_path),
            stderr_path=Path(args.stderr_path),
            updated_by=args.updated_by,
            topic_slug=args.topic_slug,
            run_id=args.run_id,
            task_id=args.task_id,
            resume_target=args.resume_target,
            prompt_text=args.prompt,
            allow_web_search=bool(args.search),
            receipts_path=Path(args.receipts_path) if args.receipts_path else None,
            session_name=args.session_name,
        )
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    if args.command == "status":
        print(json.dumps(refresh_session_metadata(metadata_path), ensure_ascii=True, indent=2))
        return 0

    if args.command == "log":
        payload = refresh_session_metadata(metadata_path)
        events_text = read_tail(Path(str(payload["events_path"])), limit=max(args.limit, 1))
        if events_text:
            print(events_text)
            return 0
        if payload.get("tmux_session_alive"):
            pane = tmux_command(["capture-pane", "-p", "-t", str(payload["tmux_session_name"]), "-S", "-"])
            if pane.returncode == 0 and pane.stdout:
                print(trim_text(pane.stdout, limit=max(args.limit, 1)))
                return 0
        return 0

    if args.command == "submit":
        print(
            json.dumps(
                submit_to_session(metadata_path, args.text, press_enter=not args.no_enter),
                ensure_ascii=True,
                indent=2,
            )
        )
        return 0

    if args.command == "kill":
        print(json.dumps(kill_session(metadata_path), ensure_ascii=True, indent=2))
        return 0

    if args.command == "wait":
        try:
            payload = wait_for_session(
                metadata_path,
                timeout_seconds=args.timeout_seconds,
                poll_interval_seconds=args.poll_interval_seconds,
            )
        except TimeoutError as exc:
            print(str(exc))
            return 124
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
