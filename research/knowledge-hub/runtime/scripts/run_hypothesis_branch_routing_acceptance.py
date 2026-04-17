#!/usr/bin/env python
"""Isolated acceptance for the bounded hypothesis branch-routing runtime surface."""

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
            "summary": "One hypothesis stays local while neighboring routes are parked explicitly.",
            "pointers": {
                "innovation_direction_path": "topics/demo-topic/runtime/innovation_direction.md",
                "innovation_decisions_path": "topics/demo-topic/runtime/innovation_decisions.jsonl",
            },
        },
    )
    write_json(
        runtime_root / "interaction_state.json",
        {
            "human_request": "Keep the weak-coupling route local, park one route, and branch one route outward.",
            "decision_surface": {
                "selected_action_id": "action:demo-topic:route-hypotheses",
                "decision_source": "heuristic",
            },
        },
    )
    write_jsonl(
        runtime_root / "action_queue.jsonl",
        [
            {
                "action_id": "action:demo-topic:route-hypotheses",
                "status": "pending",
                "action_type": "manual_followup",
                "summary": "Review the current hypothesis routing and keep the weak-coupling route on the active topic.",
                "auto_runnable": False,
                "queue_source": "heuristic",
            }
        ],
    )
    (runtime_root / "innovation_direction.md").write_text(
        "# Innovation direction\n\nKeep the weak-coupling route on the active topic.\n",
        encoding="utf-8",
    )
    write_jsonl(
        runtime_root / "innovation_decisions.jsonl",
        [
            {
                "decision": "continue",
                "summary": "Keep the weak-coupling route on the active topic and route neighboring hypotheses explicitly.",
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
            "question": "Which bounded route should remain local, which should park, and which should branch?",
            "scope": [
                "Keep the routing decision bounded to the current topic family.",
                "Do not auto-spawn or auto-adjudicate branch execution in this slice.",
            ],
            "assumptions": [
                "Only durable runtime artifacts count as progress.",
            ],
            "non_goals": [
                "Do not auto-spawn or auto-adjudicate branches.",
            ],
            "context_intake": [
                "Human request: keep branch intent explicit per hypothesis.",
            ],
            "source_basis_refs": ["paper:demo-source"],
            "interpretation_focus": ["Route each live hypothesis explicitly."],
            "open_ambiguities": [
                "Only one route should stay local on the active branch.",
            ],
            "competing_hypotheses": [
                {
                    "hypothesis_id": "hypothesis:weak-coupling",
                    "label": "Weak-coupling route",
                    "status": "leading",
                    "summary": "The weak-coupling explanation remains the active local route.",
                    "route_kind": "current_topic",
                    "route_target_summary": "Keep the weak-coupling route on the current topic branch under the current steering note.",
                    "route_target_ref": "topics/demo-topic/runtime/innovation_direction.md",
                    "evidence_refs": ["paper:demo-source", "note:demo-weak-coupling-check"],
                    "exclusion_notes": [],
                },
                {
                    "hypothesis_id": "hypothesis:symmetry-breaking",
                    "label": "Symmetry-breaking route",
                    "status": "active",
                    "summary": "The symmetry-breaking route should stay parked until broader evidence arrives.",
                    "route_kind": "deferred_buffer",
                    "route_target_summary": "Park the symmetry-breaking route in the deferred buffer until bounded reactivation conditions are met.",
                    "route_target_ref": "topics/demo-topic/runtime/deferred_candidates.json",
                    "evidence_refs": ["note:demo-symmetry-gap"],
                    "exclusion_notes": [],
                },
                {
                    "hypothesis_id": "hypothesis:prior-work",
                    "label": "Prior-work distinction route",
                    "status": "watch",
                    "summary": "A prior-work distinction should stay live on a separate follow-up branch.",
                    "route_kind": "followup_subtopic",
                    "route_target_summary": "Route the prior-work distinction into a bounded follow-up subtopic rather than widening the current topic.",
                    "route_target_ref": "topics/demo-topic/runtime/followup_subtopics.jsonl",
                    "evidence_refs": ["note:demo-prior-work-gap"],
                    "exclusion_notes": [],
                },
                {
                    "hypothesis_id": "hypothesis:strong-closure",
                    "label": "Immediate strong-closure route",
                    "status": "excluded",
                    "summary": "The stronger closure claim is currently ruled out.",
                    "route_kind": "excluded",
                    "route_target_summary": "Keep the stronger closure route excluded with no active branch.",
                    "route_target_ref": "",
                    "evidence_refs": [],
                    "exclusion_notes": ["Contradicted by the bounded validation note."],
                },
            ],
            "formalism_and_notation": ["Stay with the bounded demo notation."],
            "observables": ["Hypothesis route kind and target summary."],
            "target_claims": ["candidate:demo-claim"],
            "deliverables": ["Keep branch intent durable on the active topic surface."],
            "acceptance_tests": ["Runtime status and replay expose the route of each live hypothesis."],
            "forbidden_proxies": ["Do not infer branch routing from prose-only context."],
            "uncertainty_markers": ["Only one route should stay local on the active branch."],
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
                    "entry_id": "buffer:demo-symmetry",
                    "candidate_id": "candidate:demo-symmetry",
                    "status": "buffered",
                    "summary": "The symmetry-breaking route stays parked until broader evidence arrives.",
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
                "query": "Recover the missing prior-work distinction on a bounded child route.",
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
        else Path(tempfile.mkdtemp(prefix="aitp-hypothesis-branch-routing-acceptance-")).resolve()
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
    for path in (
        research_note,
        runtime_protocol_note,
        replay_json,
        replay_md,
        runtime_root / "innovation_direction.md",
        runtime_root / "deferred_candidates.json",
        runtime_root / "followup_subtopics.jsonl",
    ):
        ensure_exists(path)

    active_research = status_payload["active_research_contract"]
    replay_bundle = replay_payload["payload"]
    research_text = research_note.read_text(encoding="utf-8")
    runtime_protocol_text = runtime_protocol_note.read_text(encoding="utf-8")

    check(active_research["active_branch_hypothesis_id"] == "hypothesis:weak-coupling", "Expected the weak-coupling route to remain the active branch hypothesis.")
    check(active_research["deferred_branch_hypothesis_ids"] == ["hypothesis:symmetry-breaking"], "Expected the symmetry-breaking route to stay parked in the deferred buffer.")
    check(active_research["followup_branch_hypothesis_ids"] == ["hypothesis:prior-work"], "Expected the prior-work route to target a follow-up subtopic.")
    check(replay_bundle["current_position"]["active_branch_hypothesis_id"] == "hypothesis:weak-coupling", "Expected replay to surface the active branch hypothesis id.")
    check(replay_bundle["conclusions"]["deferred_branch_hypothesis_count"] == 1, "Expected replay to surface the deferred branch count.")
    check(replay_bundle["conclusions"]["followup_branch_hypothesis_count"] == 1, "Expected replay to surface the follow-up branch count.")
    check(status_payload["topic_completion"]["followup_subtopic_count"] == 1, "Expected the follow-up subtopic surface to remain visible.")
    check("route=`current_topic`" in research_text, "Expected the question note to show the current-topic route.")
    check("route=`deferred_buffer`" in research_text, "Expected the question note to show the deferred-buffer route.")
    check("route=`followup_subtopic`" in research_text, "Expected the question note to show the follow-up-subtopic route.")
    check("innovation_direction.md" in research_text, "Expected the question note to keep the steering target ref visible.")
    check("Active branch hypothesis" in runtime_protocol_text, "Expected the runtime protocol note to summarize the active branch hypothesis.")
    check("Deferred branch hypotheses" in runtime_protocol_text, "Expected the runtime protocol note to summarize deferred branch hypotheses.")

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "active_branch_hypothesis_id": active_research["active_branch_hypothesis_id"],
            "deferred_branch_hypothesis_ids": active_research["deferred_branch_hypothesis_ids"],
            "followup_branch_hypothesis_ids": active_research["followup_branch_hypothesis_ids"],
            "followup_subtopic_count": status_payload["topic_completion"]["followup_subtopic_count"],
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
