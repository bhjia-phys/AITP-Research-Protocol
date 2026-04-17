#!/usr/bin/env python
"""Isolated acceptance for collaborator-profile, research-trajectory, and mode-learning continuity surfaces."""

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


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n", encoding="utf-8")


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def seed_demo_runtime(kernel_root: Path) -> None:
    runtime_root = kernel_root / "runtime"
    topic_root = runtime_root / "topics" / "demo-topic"
    sibling_root = runtime_root / "topics" / "operator-algebra-notes"
    topic_root.mkdir(parents=True, exist_ok=True)
    sibling_root.mkdir(parents=True, exist_ok=True)
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
        sibling_root / "topic_state.json",
        {
            "topic_slug": "operator-algebra-notes",
            "latest_run_id": "run-000",
            "resume_stage": "L1",
        },
    )
    write_json(
        topic_root / "interaction_state.json",
        {
            "human_request": "Continue this topic and keep the benchmark-first route bounded.",
            "decision_surface": {
                "decision_mode": "continue_unfinished",
                "decision_source": "heuristic",
                "decision_contract_status": "missing",
                "control_note_path": None,
                "selected_action_id": "action:demo-topic:bench",
            },
        },
    )
    write_jsonl(
        topic_root / "action_queue.jsonl",
        [
            {
                "action_id": "action:demo-topic:bench",
                "status": "pending",
                "action_type": "benchmark_review",
                "summary": "Run the benchmark-first bounded route before broad theory detours.",
                "auto_runnable": False,
                "queue_source": "heuristic",
            }
        ],
    )
    write_jsonl(
        runtime_root / "topic_index.jsonl",
        [
            {"topic_slug": "operator-algebra-notes", "updated_at": "2026-04-10T08:00:00+08:00"},
            {"topic_slug": "demo-topic", "updated_at": "2026-04-11T08:00:00+08:00"},
        ],
    )
    write_jsonl(
        runtime_root / "collaborator_memory.jsonl",
        [
            {
                "memory_id": "collab-pref-demo",
                "recorded_at": "2026-04-11T09:00:00+08:00",
                "memory_kind": "preference",
                "summary": "Prefer benchmark-first routes before broad theorem detours.",
                "topic_slug": "demo-topic",
                "run_id": "run-001",
                "tags": ["code-method"],
                "related_topic_slugs": ["demo-topic"],
                "updated_by": "human",
            },
            {
                "memory_id": "collab-traj-demo",
                "recorded_at": "2026-04-11T09:05:00+08:00",
                "memory_kind": "trajectory",
                "summary": "The latest session kept the benchmark-first route active and bounded.",
                "topic_slug": "demo-topic",
                "run_id": "run-001",
                "tags": ["continuity"],
                "related_topic_slugs": ["demo-topic", "operator-algebra-notes"],
                "updated_by": "human",
            },
        ],
    )
    (runtime_root / "collaborator_memory.md").write_text("# Collaborator memory\n", encoding="utf-8")


def seed_strategy_memory(kernel_root: Path) -> None:
    write_jsonl(
        kernel_root / "topics" / "demo-topic" / "L3" / "runs" / "run-001" / "strategy_memory.jsonl",
        [
            {
                "strategy_id": "strategy:demo-helpful",
                "timestamp": "2026-04-11T09:10:00+08:00",
                "topic_slug": "demo-topic",
                "run_id": "run-001",
                "strategy_type": "resource_plan",
                "summary": "Prefer the benchmark-first route when the bounded task is still measurement-heavy.",
                "outcome": "helpful",
                "confidence": 0.88,
                "lane": "code_method",
                "reuse_conditions": ["benchmark-first", "measurement-heavy"],
                "do_not_apply_when": [],
                "input_context": {},
                "evidence_refs": [],
            },
            {
                "strategy_id": "strategy:demo-harmful",
                "timestamp": "2026-04-11T09:11:00+08:00",
                "topic_slug": "demo-topic",
                "run_id": "run-000",
                "strategy_type": "scope_control",
                "summary": "Avoid switching into theorem-first derivation before the benchmark baseline stabilizes.",
                "outcome": "harmful",
                "confidence": 0.77,
                "lane": "formal_theory",
                "reuse_conditions": [],
                "do_not_apply_when": ["benchmark baseline is still unstable"],
                "input_context": {},
                "evidence_refs": [],
            },
        ],
    )


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-collaborator-continuity-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    for name in ("closed_loop_policies.json", "research_mode_profiles.json"):
        target = kernel_root / "runtime" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package_root / "runtime" / name, target)
    seed_demo_runtime(kernel_root)
    seed_strategy_memory(kernel_root)

    focus_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "focus-topic",
            "--topic-slug",
            "demo-topic",
            "--updated-by",
            "continuity-acceptance",
            "--human-request",
            "continue this topic",
            "--json",
        ],
    )
    status_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", "demo-topic", "--json"],
    )
    current_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["current-topic", "--json"],
    )
    session_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["session-start", "--json", "继续这个 topic，保持 benchmark-first route"],
    )

    for key in ("collaborator_profile", "research_trajectory", "mode_learning"):
        artifact = status_payload[key]
        check(artifact["status"] == "available", f"{key} should be available")
        ensure_exists(kernel_root / artifact["path"])
        ensure_exists(kernel_root / artifact["note_path"])

    check(status_payload["mode_learning"]["preferred_lane"] == "code_method", "mode learning should favor code_method")
    check("benchmark-first route" in status_payload["mode_learning"]["summary"], "mode learning summary should mention benchmark-first route")
    current_topic = current_payload["current_topic"]
    check(current_topic["collaborator_profile_status"] == "available", "current-topic should surface collaborator profile")
    check(current_topic["research_trajectory_status"] == "available", "current-topic should surface research trajectory")
    check(current_topic["mode_learning_status"] == "available", "current-topic should surface mode learning")

    session_contract = json.loads(Path(session_payload["session_start_contract_path"]).read_text(encoding="utf-8"))
    artifacts = session_contract["artifacts"]
    for key in ("collaborator_profile_note_path", "research_trajectory_note_path", "mode_learning_note_path"):
        check(key in artifacts, f"session-start artifacts should contain {key}")
        ensure_exists(kernel_root / artifacts[key])
    check(any(str(row.get("path") or "").endswith("mode_learning.active.md") for row in session_contract["must_read_now"]), "session-start must_read_now should surface mode learning")

    payload = {
        "work_root": str(work_root),
        "focus": focus_payload,
        "status": {
            "collaborator_profile": status_payload["collaborator_profile"],
            "research_trajectory": status_payload["research_trajectory"],
            "mode_learning": status_payload["mode_learning"],
        },
        "current_topic": current_topic,
        "session_start_contract_path": session_payload["session_start_contract_path"],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(
            "collaborator continuity acceptance passed\n"
            f"work_root: {work_root}\n"
            f"session_start_contract: {session_payload['session_start_contract_path']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
