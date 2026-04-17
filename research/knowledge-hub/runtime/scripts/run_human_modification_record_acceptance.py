#!/usr/bin/env python
"""Isolated acceptance for the bounded promotion-gate human modification record."""

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
                "resume_stage": "L4",
                "last_materialized_stage": "L4",
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
                "human_request": "Review the modified approval record before promotion writeback.",
                "decision_surface": {
                    "selected_action_id": "action:demo-topic:promotion-review",
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
                "action_id": "action:demo-topic:promotion-review",
                "status": "pending",
                "action_type": "inspect_resume_state",
                "summary": "Inspect the approval record and decide whether the modified L2 candidate is ready for writeback.",
                "auto_runnable": False,
                "queue_source": "heuristic",
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
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
                "title": "Demo theorem candidate",
                "summary": "A bounded theorem candidate ready for human L2 approval.",
                "topic_slug": "demo-topic",
                "run_id": "run-001",
                "origin_refs": [],
                "question": "Can the bounded theorem be approved for L2?",
                "assumptions": ["The submitted candidate still needs a narrower regime statement."],
                "proposed_validation_route": "analytical",
                "intended_l2_targets": ["theorem:demo-approved-result"],
                "status": "ready_for_validation",
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
        else Path(tempfile.mkdtemp(prefix="aitp-human-modification-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    seed_demo_runtime(kernel_root)
    seed_demo_candidate(kernel_root)

    requested = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["request-promotion", "--topic-slug", "demo-topic", "--candidate-id", "candidate:demo-candidate", "--json"],
    )
    approved = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "approve-promotion",
            "--topic-slug",
            "demo-topic",
            "--candidate-id",
            "candidate:demo-candidate",
            "--human-modification",
            "statement=Narrowed to weak coupling only:The submitted candidate overstated the valid regime.",
            "--human-modification",
            "summary=Clarified that the result remains bounded:The original summary implied stronger closure than the evidence supports.",
            "--json",
        ],
    )
    replay = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["replay-topic", "--topic-slug", "demo-topic", "--json"],
    )

    runtime_root = kernel_root / "topics" / "demo-topic" / "runtime"
    gate_json = runtime_root / "promotion_gate.json"
    gate_note = runtime_root / "promotion_gate.md"
    replay_json = Path(replay["json_path"])
    replay_md = Path(replay["markdown_path"])
    for path in (gate_json, gate_note, replay_json, replay_md):
        ensure_exists(path)

    gate_payload = json.loads(gate_json.read_text(encoding="utf-8"))
    replay_payload = replay["payload"]

    check(requested["status"] == "pending_human_approval", "Expected request-promotion to create a pending human gate.")
    check(approved["status"] == "approved", "Expected approve-promotion to approve the pending gate.")
    check(gate_payload["approval_change_kind"] == "approved_with_modifications", "Expected the gate to record a modified approval.")
    check(len(gate_payload["human_modifications"]) == 2, "Expected two recorded human modifications.")
    check(gate_payload["human_modifications"][0]["field"] == "statement", "Expected the first modification to target the statement.")
    check("## Human modifications" in gate_note.read_text(encoding="utf-8"), "Expected promotion gate note to render human modifications.")
    check(replay_payload["current_position"]["approval_change_kind"] == "approved_with_modifications", "Expected replay to surface the modified approval kind.")
    check(replay_payload["conclusions"]["human_modification_count"] == 2, "Expected replay to surface the human modification count.")
    check(any(step.get("label") == "Promotion gate" for step in replay_payload["reading_path"]), "Expected replay reading path to include promotion gate.")

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "approval_change_kind": gate_payload["approval_change_kind"],
            "human_modification_count": len(gate_payload["human_modifications"]),
            "modified_fields": [row["field"] for row in gate_payload["human_modifications"]],
        },
        "artifacts": {
            "promotion_gate_json": str(gate_json),
            "promotion_gate_note": str(gate_note),
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
