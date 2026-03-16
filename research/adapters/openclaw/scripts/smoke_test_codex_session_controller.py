#!/usr/bin/env python3
"""Run a live Codex tmux-session smoke test for the OpenClaw adapter."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from codex_session_controller import (
    DEFAULT_TIMEOUT_SECONDS,
    read_tail,
    refresh_session_metadata,
    start_codex_exec_session,
    wait_for_session,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-seconds", type=int, default=min(DEFAULT_TIMEOUT_SECONDS, 240))
    parser.add_argument("--keep-tempdir", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    keep_tempdir = bool(args.keep_tempdir)
    temp_root = Path(tempfile.mkdtemp(prefix="codex-session-smoke-"))
    try:
        session_dir = temp_root / "session"
        prompt_path = session_dir / "prompt.md"
        metadata_path = session_dir / "codex_session.json"
        events_path = session_dir / "events.jsonl"
        stderr_path = session_dir / "stderr.txt"
        last_message_path = session_dir / "last.md"
        target_path = temp_root / "smoke.txt"

        prompt = (
            "Create a file named `smoke.txt` in the current directory containing exactly "
            "the text `OK` followed by a newline. Do not modify any other file. "
            "In your final response, state only `done`."
        )
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt + "\n", encoding="utf-8")

        started = start_codex_exec_session(
            metadata_path=metadata_path,
            workspace_root=temp_root,
            prompt_path=prompt_path,
            prompt_text=prompt,
            events_path=events_path,
            stderr_path=stderr_path,
            last_message_path=last_message_path,
            updated_by="smoke-test",
            topic_slug="codex-session-smoke",
            run_id="manual-smoke",
            task_id="write-ok-file",
            allow_web_search=False,
            result_writeback_path=target_path,
        )

        status_after_start = refresh_session_metadata(metadata_path)
        if status_after_start["status"] not in {"running", "completed"}:
            raise SystemExit(
                f"Unexpected session status immediately after start: {status_after_start['status']}"
            )

        finished = wait_for_session(metadata_path, timeout_seconds=args.timeout_seconds)
        if finished.get("exit_code") != 0:
            raise SystemExit(f"Smoke Codex session failed: exit_code={finished.get('exit_code')}")
        if not target_path.exists():
            raise SystemExit(f"Smoke test did not produce target file: {target_path}")

        target_text = target_path.read_text(encoding="utf-8")
        if target_text != "OK\n":
            raise SystemExit(f"Unexpected smoke file contents: {target_text!r}")

        last_message = last_message_path.read_text(encoding="utf-8").strip() if last_message_path.exists() else ""
        if last_message != "done":
            raise SystemExit(f"Unexpected Codex final message: {last_message!r}")

        events_tail = read_tail(events_path, limit=2000)
        if "done" not in events_tail:
            raise SystemExit("Smoke events tail did not include final 'done' message")

        summary = {
            "status": "pass",
            "temp_root": str(temp_root),
            "metadata_path": str(metadata_path),
            "events_path": str(events_path),
            "stderr_path": str(stderr_path),
            "last_message_path": str(last_message_path),
            "target_path": str(target_path),
            "session_id": started.get("session_id"),
            "tmux_session_name": started.get("tmux_session_name"),
            "exit_code": finished.get("exit_code"),
            "last_message": last_message,
        }
        print(json.dumps(summary, ensure_ascii=True, indent=2))
        return 0
    finally:
        if keep_tempdir:
            print(json.dumps({"kept_temp_root": str(temp_root)}, ensure_ascii=True))
        else:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
