#!/usr/bin/env python
"""Isolated acceptance for the bounded runtime transition and demotion history surface."""

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


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


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
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def seed_demo_runtime(kernel_root: Path) -> None:
    runtime_root = kernel_root / "topics" / "demo-topic" / "runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    (runtime_root / "topic_state.json").write_text(
        json.dumps(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "run-001",
                "resume_stage": "L3",
                "last_materialized_stage": "L4",
                "resume_reason": "Validation contradiction returned the topic to L3 for another bounded pass.",
                "research_mode": "formal_derivation",
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_root / "interaction_state.json").write_text(
        json.dumps(
            {
                "human_request": "Inspect the transition history before deciding whether to retry promotion.",
                "decision_surface": {
                    "selected_action_id": "action:demo-topic:transition-audit",
                    "decision_source": "heuristic",
                },
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_root / "action_queue.jsonl").write_text(
        json.dumps(
            {
                "action_id": "action:demo-topic:transition-audit",
                "status": "pending",
                "action_type": "inspect_resume_state",
                "summary": "Inspect the transition history and decide whether the topic should retry promotion or continue bounded L3 work.",
                "auto_runnable": False,
                "queue_source": "heuristic",
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )


def seed_demo_source_layer(kernel_root: Path) -> None:
    topic_root = kernel_root / "topics" / "demo-topic" / "L0"
    topic_root.mkdir(parents=True, exist_ok=True)
    write_jsonl(
        topic_root / "source_index.jsonl",
        [
            {
                "source_id": "paper:demo-source",
                "source_type": "paper",
                "title": "Demo promoted route source",
                "summary": "A bounded source for the promotion-and-backtrack replay lane.",
                "provenance": {"abs_url": "https://example.org/demo-transition-source"},
            }
        ],
    )


def seed_demo_candidate(kernel_root: Path) -> None:
    feedback_root = kernel_root / "topics" / "demo-topic" / "L3" / "runs" / "run-001"
    feedback_root.mkdir(parents=True, exist_ok=True)
    write_jsonl(
        feedback_root / "candidate_ledger.jsonl",
        [
            {
                "candidate_id": "candidate:demo-candidate",
                "candidate_type": "theorem_card",
                "title": "Demo promoted route",
                "summary": "A bounded theorem candidate that will be rejected back to L3 after contradiction review.",
                "topic_slug": "demo-topic",
                "run_id": "run-001",
                "origin_refs": [{"id": "paper:demo-source", "layer": "L0", "object_type": "source"}],
                "question": "Does the bounded route survive the contradiction review?",
                "assumptions": ["Bounded contradiction review remains unresolved."],
                "proposed_validation_route": "analytical",
                "intended_l2_targets": ["theorem:demo-transition-result"],
                "status": "ready_for_validation",
                "supporting_regression_question_ids": ["regression_question:demo-transition"],
                "supporting_oracle_ids": ["question_oracle:demo-transition"],
                "supporting_regression_run_ids": ["regression_run:demo-transition"],
            }
        ],
    )


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-transition-history-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    seed_demo_runtime(kernel_root)
    seed_demo_source_layer(kernel_root)
    seed_demo_candidate(kernel_root)

    requested = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "request-promotion",
            "--topic-slug",
            "demo-topic",
            "--candidate-id",
            "candidate:demo-candidate",
            "--json",
        ],
    )
    rejected = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "reject-promotion",
            "--topic-slug",
            "demo-topic",
            "--candidate-id",
            "candidate:demo-candidate",
            "--notes",
            "Validation contradiction returned the candidate to L3.",
            "--json",
        ],
    )
    status_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", "demo-topic", "--json"],
    )
    replay_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["replay-topic", "--topic-slug", "demo-topic", "--json"],
    )

    runtime_root = kernel_root / "topics" / "demo-topic" / "runtime"
    transition_log = runtime_root / "transition_history.jsonl"
    transition_json = runtime_root / "transition_history.json"
    transition_note = runtime_root / "transition_history.md"
    topic_dashboard = runtime_root / "topic_dashboard.md"
    runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"])
    replay_json = Path(replay_payload["json_path"])
    replay_md = Path(replay_payload["markdown_path"])
    for path in (
        transition_log,
        transition_json,
        transition_note,
        topic_dashboard,
        runtime_protocol_note,
        replay_json,
        replay_md,
    ):
        ensure_exists(path)

    transition_payload = json.loads(transition_json.read_text(encoding="utf-8"))
    replay_bundle = replay_payload["payload"]
    transition_rows = transition_payload["rows"]

    check(requested["status"] == "pending_human_approval", "Expected request-promotion to write a pending human gate.")
    check(rejected["status"] == "rejected", "Expected reject-promotion to reject the pending gate.")
    check(transition_payload["transition_count"] >= 2, "Expected at least two transition rows (rejection + runtime resume).")
    check(transition_payload["backtrack_count"] >= 1, "Expected at least one backtrack transition.")
    check(transition_payload["demotion_count"] >= 1, "Expected at least one demotion transition.")
    check(any(row.get("event_kind") == "promotion_rejected" for row in transition_rows), "Expected a promotion_rejected transition row.")
    check(any(row.get("event_kind") == "runtime_resume_state" for row in transition_rows), "Expected a runtime_resume_state transition row.")
    check(
        any(row.get("to_layer") == "L3" and row.get("transition_kind") == "backedge_transition" for row in transition_rows),
        "Expected a backedge transition into L3.",
    )
    check(
        replay_bundle["current_position"]["latest_demotion_reason"]
        == str((transition_payload.get("latest_demotion") or {}).get("reason") or ""),
        "Expected replay bundle to surface the latest demotion reason.",
    )
    check(
        replay_bundle["conclusions"]["demotion_count"] >= 1,
        "Expected replay bundle to surface the demotion count.",
    )
    check(
        any(step.get("label") == "Transition history" for step in replay_bundle["reading_path"]),
        "Expected replay bundle to include transition history in the reading path.",
    )
    check("## Transition history" in runtime_protocol_note.read_text(encoding="utf-8"), "Expected runtime protocol note to mention transition history.")

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "transition_count": transition_payload["transition_count"],
            "backtrack_count": transition_payload["backtrack_count"],
            "demotion_count": transition_payload["demotion_count"],
            "event_kinds": [str(row.get("event_kind") or "") for row in transition_rows],
        },
        "artifacts": {
            "transition_log": str(transition_log),
            "transition_json": str(transition_json),
            "transition_note": str(transition_note),
            "runtime_protocol_note": str(runtime_protocol_note),
            "topic_dashboard": str(topic_dashboard),
            "replay_json": str(replay_json),
            "replay_markdown": str(replay_md),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
