#!/usr/bin/env python
"""Isolated acceptance for the quick-exploration entrypoint and promotion path."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
KERNEL_ROOT = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--json", action="store_true")
    return parser


def run_cli_json(*, package_root: Path, kernel_root: Path, repo_root: Path, args: list[str]) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "knowledge_hub.aitp_cli",
        "--kernel-root",
        str(kernel_root),
        "--repo-root",
        str(repo_root),
        *args,
    ]
    completed = subprocess.run(
        command,
        cwd=package_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")
    return json.loads(completed.stdout)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def seed_current_topic(kernel_root: Path) -> None:
    runtime_root = kernel_root / "runtime"
    topic_root = runtime_root / "topics" / "demo-topic"
    topic_root.mkdir(parents=True, exist_ok=True)
    write_json(
        topic_root / "topic_state.json",
        {
            "topic_slug": "demo-topic",
            "latest_run_id": "run-001",
            "resume_stage": "L3",
            "last_materialized_stage": "L3",
            "research_mode": "exploratory_general",
        },
    )
    write_json(
        runtime_root / "current_topic.json",
        {
            "topic_slug": "demo-topic",
            "current_topic_note_path": "runtime/current_topic.md",
            "summary": "Continue the bounded benchmark lane.",
        },
    )
    (runtime_root / "current_topic.md").write_text("# Current topic\n", encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-quick-exploration-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    for name in ("closed_loop_policies.json", "research_mode_profiles.json"):
        target = kernel_root / "runtime" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package_root / "runtime" / name, target)
    seed_current_topic(kernel_root)

    explore_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["explore", "--json", "Sketch a speculative benchmark-first branch before opening a full topic loop."],
    )
    promotion_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "promote-exploration",
            "--exploration-id",
            explore_payload["exploration_id"],
            "--current-topic",
            "--json",
        ],
    )

    ensure_exists(Path(explore_payload["exploration_session_path"]))
    ensure_exists(Path(explore_payload["exploration_session_note_path"]))
    check(explore_payload["topic_bootstrap_skipped"], "quick exploration should skip full topic bootstrap")
    check(explore_payload["artifact_footprint"]["quick_exploration_artifact_count"] == 2, "quick exploration should stay on a two-file carrier")
    check(explore_payload["artifact_footprint"]["status"] == "lighter_than_full_topic", "artifact footprint should be marked lighter than full topic")

    ensure_exists(Path(promotion_payload["promotion_request_path"]))
    ensure_exists(Path(promotion_payload["promotion_request_note_path"]))
    ensure_exists(Path(promotion_payload["promoted_session"]["session_start_contract_path"]))
    check(promotion_payload["target_mode"] == "current_topic", "promotion should target current topic in this acceptance")
    check(promotion_payload["promoted_session"]["routing"]["route"] == "explicit_current_topic", "promotion should use explicit current-topic session-start routing")

    payload = {
        "work_root": str(work_root),
        "explore": explore_payload,
        "promotion": promotion_payload,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(
            "quick exploration acceptance passed\n"
            f"work_root: {work_root}\n"
            f"promotion_request: {promotion_payload['promotion_request_path']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
