#!/usr/bin/env python
"""Isolated acceptance for the bounded competing-hypotheses runtime surface."""

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
    write_json(
        runtime_root / "topic_state.json",
        {
            "topic_slug": "demo-topic",
            "latest_run_id": "run-001",
            "resume_stage": "L3",
            "last_materialized_stage": "L3",
            "research_mode": "formal_derivation",
            "summary": "Two bounded explanations are still competing on the active topic.",
        },
    )
    write_json(
        runtime_root / "interaction_state.json",
        {
            "human_request": "Keep the current competing hypotheses explicit while we compare bounded explanations.",
            "decision_surface": {
                "selected_action_id": "action:demo-topic:compare-hypotheses",
                "decision_source": "heuristic",
            },
        },
    )
    write_jsonl(
        runtime_root / "action_queue.jsonl",
        [
            {
                "action_id": "action:demo-topic:compare-hypotheses",
                "status": "pending",
                "action_type": "manual_followup",
                "summary": "Compare the bounded weak-coupling and symmetry-breaking explanations without collapsing them into one route yet.",
                "auto_runnable": False,
                "queue_source": "heuristic",
            }
        ],
    )
    write_json(
        runtime_root / "research_question.contract.json",
        {
            "contract_version": 1,
            "question_id": "research_question:demo-topic",
            "title": "Demo Topic",
            "topic_slug": "demo-topic",
            "status": "active",
            "template_mode": "formal_theory",
            "research_mode": "formal_derivation",
            "question": "Which bounded explanation currently best accounts for the demo phenomenon?",
            "scope": [
                "Keep the question bounded to the current demo topic.",
                "Track multiple plausible explanations without forcing an early collapse.",
            ],
            "assumptions": [
                "Only durable runtime artifacts count as progress.",
            ],
            "non_goals": [
                "Do not claim whole-topic closure from one bounded comparison.",
            ],
            "context_intake": [
                "Human request: keep the competing explanations explicit while the bounded review continues.",
            ],
            "source_basis_refs": ["paper:demo-source"],
            "interpretation_focus": [
                "Compare the weak-coupling and symmetry-breaking routes explicitly.",
            ],
            "open_ambiguities": [
                "The current evidence does not yet collapse the weak-coupling and symmetry-breaking routes into one answer.",
            ],
            "competing_hypotheses": [
                {
                    "hypothesis_id": "hypothesis:weak-coupling",
                    "label": "Weak-coupling route",
                    "status": "leading",
                    "summary": "The current bounded evidence favors the weak-coupling explanation.",
                    "evidence_refs": [
                        "paper:demo-source",
                        "note:demo-weak-coupling-check",
                    ],
                    "exclusion_notes": [],
                },
                {
                    "hypothesis_id": "hypothesis:symmetry-breaking",
                    "label": "Symmetry-breaking route",
                    "status": "active",
                    "summary": "A symmetry-breaking explanation remains plausible enough to stay live on the active topic.",
                    "evidence_refs": [
                        "note:demo-symmetry-gap",
                    ],
                    "exclusion_notes": [],
                },
                {
                    "hypothesis_id": "hypothesis:strong-closure",
                    "label": "Immediate strong-closure route",
                    "status": "excluded",
                    "summary": "The stronger closure claim is currently ruled out on the bounded evidence we have.",
                    "evidence_refs": [],
                    "exclusion_notes": [
                        "The bounded validation note contradicts the stronger closure claim.",
                    ],
                },
            ],
            "formalism_and_notation": [
                "Stay within the current bounded demo notation.",
            ],
            "observables": [
                "Hypothesis status, evidence refs, and exclusion notes.",
            ],
            "target_claims": ["candidate:demo-claim"],
            "deliverables": [
                "Keep the current hypothesis competition durable on the active question surface.",
            ],
            "acceptance_tests": [
                "Runtime status and replay surface the competing hypotheses explicitly.",
            ],
            "forbidden_proxies": [
                "Do not silently flatten the question back into one prose-only answer.",
            ],
            "uncertainty_markers": [
                "The active topic still has more than one live explanation.",
            ],
            "target_layers": ["L1", "L3", "L4", "L2"],
        },
    )
    write_json(
        runtime_root / "deferred_candidates.json",
        {
            "buffer_version": 1,
            "topic_slug": "demo-topic",
            "updated_at": "2026-04-12T00:00:00+00:00",
            "updated_by": "test",
            "entries": [
                {
                    "entry_id": "buffer:demo-wide-route",
                    "candidate_id": "candidate:demo-wide-route",
                    "status": "buffered",
                    "summary": "A wider route stays parked until the bounded comparison resolves.",
                    "reactivation_triggers": ["Need broader evidence before reactivation."],
                }
            ],
        },
    )
    write_jsonl(
        runtime_root / "followup_subtopics.jsonl",
        [
            {
                "child_topic_slug": "demo-topic--followup--prior-work",
                "parent_topic_slug": "demo-topic",
                "status": "spawned",
                "query": "Recover one missing prior-work distinction before collapsing the active question.",
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
        else Path(tempfile.mkdtemp(prefix="aitp-competing-hypotheses-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    seed_demo_runtime(kernel_root)

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
    research_note = runtime_root / "research_question.contract.md"
    runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"])
    replay_json = Path(replay_payload["json_path"])
    replay_md = Path(replay_payload["markdown_path"])
    deferred_buffer = runtime_root / "deferred_candidates.json"
    for path in (research_note, runtime_protocol_note, replay_json, replay_md):
        ensure_exists(path)

    active_research = status_payload["active_research_contract"]
    replay_bundle = replay_payload["payload"]
    research_text = research_note.read_text(encoding="utf-8")
    runtime_protocol_text = runtime_protocol_note.read_text(encoding="utf-8")

    check(active_research["competing_hypothesis_count"] == 3, "Expected three competing hypotheses on the active research contract.")
    check(active_research["leading_hypothesis_id"] == "hypothesis:weak-coupling", "Expected the weak-coupling route to remain the leading hypothesis.")
    check(len(active_research["competing_hypotheses"]) == 3, "Expected the active research contract to expose all competing hypotheses.")
    check(deferred_buffer.exists(), "Expected the deferred candidate buffer to remain present.")
    check(status_payload["topic_completion"]["followup_subtopic_count"] == 1, "Expected the follow-up subtopic surface to remain visible.")
    check("## Competing hypotheses" in research_text, "Expected research_question.contract.md to include a competing-hypotheses section.")
    check("Weak-coupling route" in research_text, "Expected the question note to name the leading hypothesis.")
    check("## Competing hypotheses" in runtime_protocol_text, "Expected the runtime protocol note to surface competing hypotheses.")
    check(replay_bundle["conclusions"]["competing_hypothesis_count"] == 3, "Expected replay to surface the competing-hypothesis count.")
    check(replay_bundle["conclusions"]["excluded_competing_hypothesis_count"] == 1, "Expected replay to surface the excluded hypothesis count.")
    check(
        replay_bundle["current_position"]["leading_competing_hypothesis_id"] == "hypothesis:weak-coupling",
        "Expected replay to surface the leading competing hypothesis id.",
    )
    check(
        any(step.get("label") == "Question contract" for step in replay_bundle["reading_path"]),
        "Expected replay reading path to include the question contract.",
    )

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "competing_hypothesis_count": active_research["competing_hypothesis_count"],
            "leading_hypothesis_id": active_research["leading_hypothesis_id"],
            "deferred_buffer_present": deferred_buffer.exists(),
            "followup_subtopic_count": status_payload["topic_completion"]["followup_subtopic_count"],
            "excluded_competing_hypothesis_count": replay_bundle["conclusions"]["excluded_competing_hypothesis_count"],
        },
        "artifacts": {
            "research_question_note": str(research_note),
            "runtime_protocol_note": str(runtime_protocol_note),
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
