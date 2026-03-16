#!/usr/bin/env python3
"""Smoke-test research-mode task materialization and ingest outputs."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from closed_loop_v1 import ingest_execution_result, materialize_execution_task


MODE_CASES = (
    ("first_principles", "numerical", "Run a bounded GW/QSGW-style numerical baseline check."),
    ("toy_model", "numerical", "Run a spin-chain toy-model validation in a fixed symmetry sector."),
    ("formal_derivation", "formal", "Write a bounded derivation note with explicit assumptions."),
)


def write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def ensure_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_source_execution_task(knowledge_root: Path, topic_slug: str, run_id: str, mode: str, surface: str) -> str:
    task_path = (
        knowledge_root
        / "validation"
        / "topics"
        / topic_slug
        / "runs"
        / run_id
        / "execution-tasks"
        / f"{mode}-source-task.json"
    )
    write_json(
        task_path,
        {
            "task_id": f"{mode}-source-task",
            "validation_note": f"obsidian-markdown/11 L4 Validation/active/{topic_slug}-{mode}.md",
            "candidate_id": f"candidate:{topic_slug}-{mode}",
            "research_mode": mode,
            "surface": surface,
            "status": "planned",
            "input_artifacts": [
                f"feedback/topics/{topic_slug}/runs/{run_id}/next_actions.md"
            ],
            "planned_outputs": [
                f"validation/topics/{topic_slug}/runs/{run_id}/results/{mode}-summary.md"
            ],
            "pass_conditions": [
                f"The {mode} smoke execution writes a durable result artifact."
            ],
            "failure_signals": [
                "The declared result artifact is missing."
            ],
            "assigned_runtime": "codex",
            "executor_kind": "codex_cli",
            "result_artifacts": [],
            "summary": f"Source execution-task record for {mode}.",
        },
    )
    return task_path.relative_to(knowledge_root).as_posix()


def prepare_topic_shell(knowledge_root: Path, topic_slug: str, run_id: str, mode: str, surface: str, objective: str) -> dict:
    runtime_root = knowledge_root / "runtime" / "topics" / topic_slug
    runtime_root.mkdir(parents=True, exist_ok=True)
    feedback_root = knowledge_root / "feedback" / "topics" / topic_slug / "runs" / run_id
    feedback_root.mkdir(parents=True, exist_ok=True)
    ensure_file(feedback_root / "next_actions.md", "1. Example next action.\n")
    ensure_file(feedback_root / "status.json", "{}\n")

    source_task_ref = build_source_execution_task(knowledge_root, topic_slug, run_id, mode, surface)
    write_json(
        runtime_root / "selected_validation_route.json",
        {
            "route_id": f"route:{topic_slug}:{mode}",
            "route_type": surface,
            "objective": objective,
            "run_id": run_id,
            "input_artifacts": [f"feedback/topics/{topic_slug}/runs/{run_id}/next_actions.md"],
            "expected_outputs": [
                f"validation/topics/{topic_slug}/runs/{run_id}/results/{mode}-summary.md"
            ],
            "success_criterion": [
                f"The {mode} smoke task returns a truthful result payload."
            ],
            "failure_signals": [
                "The declared result artifact is missing."
            ],
            "needs_human_confirm": False,
            "allow_web_search": False,
            "assigned_runtime": "codex",
            "executor_kind": "codex_cli",
            "reasoning_profile": "high" if mode != "toy_model" else "medium",
            "research_mode": mode,
            "source_execution_task_path": source_task_ref,
        },
    )
    return {
        "topic_slug": topic_slug,
        "latest_run_id": run_id,
        "research_mode": mode,
        "pointers": {
            "feedback_status_path": f"feedback/topics/{topic_slug}/runs/{run_id}/status.json",
            "next_actions_path": f"feedback/topics/{topic_slug}/runs/{run_id}/next_actions.md",
        },
    }


def run_case(knowledge_root: Path, mode: str, surface: str, objective: str) -> dict:
    topic_slug = f"smoke-{mode.replace('_', '-')}"
    run_id = f"2026-03-16-{mode}"
    topic_state = prepare_topic_shell(knowledge_root, topic_slug, run_id, mode, surface, objective)

    task_payload = materialize_execution_task(knowledge_root, topic_state, updated_by="smoke-test")
    result_artifact = knowledge_root / task_payload["planned_outputs"][0]
    ensure_file(result_artifact, f"# {mode} result\n\nSmoke artifact.\n")

    write_json(
        knowledge_root / task_payload["result_writeback_path"],
        {
            "result_id": f"result:{mode}:smoke",
            "task_id": task_payload["task_id"],
            "status": "success",
            "research_mode": mode,
            "executor_kind": task_payload["executor_kind"],
            "reasoning_profile": task_payload["reasoning_profile"],
            "artifacts": [task_payload["planned_outputs"][0]],
            "metrics": {"artifact_count": 1},
            "logs": [],
            "produced_by": "smoke-test",
            "created_at": "2026-03-16T00:00:00+08:00",
            "what_was_attempted": objective,
            "what_actually_ran": f"Executed the {mode} smoke path.",
            "summary": f"{mode} smoke execution completed.",
            "limitations": ["Smoke test only; does not certify scientific correctness."],
            "non_conclusions": ["This is a protocol smoke test, not a scientific validation claim."],
            "failure_signals_triggered": [],
            "trajectory_events": [
                {
                    "event_type": "executor_report",
                    "status": "success",
                    "message": f"Completed the {mode} smoke run.",
                    "recorded_at": "2026-03-16T00:00:00+08:00",
                    "artifacts": [task_payload["planned_outputs"][0]],
                }
            ],
            "recommended_decision": "keep",
            "decision_reason": "Smoke artifact exists and the contract was satisfied.",
            "needs_literature_followup": False,
        },
    )

    ingest_payload = ingest_execution_result(knowledge_root, topic_state, updated_by="smoke-test")
    manifest = ingest_payload["manifest"]
    trajectory_path = knowledge_root / manifest["trajectory_log_path"]
    failure_path = knowledge_root / manifest["failure_classification_path"]

    assert task_payload["research_mode"] == mode
    assert manifest["research_mode"] == mode
    assert trajectory_path.exists(), f"Missing trajectory log for {mode}"
    assert failure_path.exists(), f"Missing failure classification for {mode}"

    return {
        "topic_slug": topic_slug,
        "research_mode": mode,
        "task_id": task_payload["task_id"],
        "executor_kind": task_payload["executor_kind"],
        "reasoning_profile": task_payload["reasoning_profile"],
        "result_status": manifest["status"],
        "trajectory_log_path": manifest["trajectory_log_path"],
        "failure_classification_path": manifest["failure_classification_path"],
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="aitp-research-mode-smoke-") as tmpdir:
        knowledge_root = Path(tmpdir)
        cases = [run_case(knowledge_root, mode, surface, objective) for mode, surface, objective in MODE_CASES]
    print(json.dumps({"cases": cases}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
