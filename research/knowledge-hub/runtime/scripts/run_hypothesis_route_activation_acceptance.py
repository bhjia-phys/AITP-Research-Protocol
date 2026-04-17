#!/usr/bin/env python
"""Isolated acceptance for the bounded hypothesis route-activation surface."""

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
            "summary": "The active local route remains bounded while parked route obligations stay explicit.",
        },
    )
    write_json(
        runtime_root / "interaction_state.json",
        {
            "human_request": "Keep the weak-coupling route active and show exactly what the parked routes are waiting on.",
            "decision_surface": {
                "selected_action_id": "action:demo-topic:route-activation",
                "decision_source": "heuristic",
            },
        },
    )
    write_jsonl(
        runtime_root / "action_queue.jsonl",
        [
            {
                "action_id": "action:demo-topic:route-activation",
                "status": "pending",
                "action_type": "manual_followup",
                "summary": "Continue the weak-coupling route on the active topic while keeping parked route obligations explicit.",
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
            "question": "How should the active local route and parked routes stay visible without auto-spawning new work?",
            "scope": [
                "Keep the route activation surface bounded to the current topic family.",
                "Expose parked obligations without auto-spawning or auto-adjudicating branch execution.",
            ],
            "assumptions": [
                "Only durable runtime artifacts count as progress.",
            ],
            "non_goals": [
                "Do not auto-spawn or auto-schedule new branches in this slice.",
            ],
            "context_intake": [
                "Human request: surface active-route action and parked-route obligations directly.",
            ],
            "source_basis_refs": ["paper:demo-source"],
            "interpretation_focus": ["Keep current-route action and parked-route obligations explicit."],
            "open_ambiguities": [
                "The parked routes remain relevant but should not replace the active local route.",
            ],
            "competing_hypotheses": [
                {
                    "hypothesis_id": "hypothesis:weak-coupling",
                    "label": "Weak-coupling route",
                    "status": "leading",
                    "summary": "The weak-coupling route remains the active local branch.",
                    "route_kind": "current_topic",
                    "route_target_summary": "Continue the weak-coupling route on the active topic while keeping parked route obligations explicit.",
                    "route_target_ref": "topics/demo-topic/runtime/action_queue.jsonl",
                    "evidence_refs": ["paper:demo-source"],
                    "exclusion_notes": [],
                },
                {
                    "hypothesis_id": "hypothesis:symmetry-breaking",
                    "label": "Symmetry-breaking route",
                    "status": "active",
                    "summary": "The symmetry-breaking route stays parked in deferred storage.",
                    "route_kind": "deferred_buffer",
                    "route_target_summary": "Park the symmetry-breaking route in the deferred buffer until broader evidence arrives.",
                    "route_target_ref": "topics/demo-topic/runtime/deferred_candidates.json",
                    "evidence_refs": ["note:demo-symmetry-gap"],
                    "exclusion_notes": [],
                },
                {
                    "hypothesis_id": "hypothesis:prior-work",
                    "label": "Prior-work route",
                    "status": "watch",
                    "summary": "The prior-work route stays visible as a bounded follow-up obligation.",
                    "route_kind": "followup_subtopic",
                    "route_target_summary": "Route the prior-work distinction into a bounded follow-up subtopic after the current topic stabilizes.",
                    "route_target_ref": "topics/demo-topic/runtime/followup_subtopics.jsonl",
                    "evidence_refs": ["note:demo-prior-work-gap"],
                    "exclusion_notes": [],
                },
            ],
            "formalism_and_notation": ["Stay with the bounded demo notation."],
            "observables": ["Active local action and parked-route obligations."],
            "target_claims": ["candidate:demo-claim"],
            "deliverables": ["Keep route activation durable on the active topic surface."],
            "acceptance_tests": ["Runtime status and replay expose route activation directly."],
            "forbidden_proxies": ["Do not reconstruct route activation from separate prose-only notes."],
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
                "status": "proposed",
                "query": "Recover the missing prior-work distinction on a bounded child route after the current topic stabilizes.",
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
        else Path(tempfile.mkdtemp(prefix="aitp-hypothesis-route-activation-acceptance-")).resolve()
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
    runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"])
    replay_json = Path(replay_payload["json_path"])
    replay_md = Path(replay_payload["markdown_path"])
    deferred_buffer = runtime_root / "deferred_candidates.json"
    followup_rows = runtime_root / "followup_subtopics.jsonl"
    followup_child_root = runtime_root.parent / "demo-topic--followup--prior-work"
    for path in (runtime_protocol_note, replay_json, replay_md, deferred_buffer, followup_rows):
        ensure_exists(path)

    active_research = status_payload["active_research_contract"]
    route_activation = active_research["route_activation"]
    replay_bundle = replay_payload["payload"]
    replay_route_activation = replay_bundle["route_activation"]
    runtime_protocol_text = runtime_protocol_note.read_text(encoding="utf-8")
    replay_text = replay_md.read_text(encoding="utf-8")

    check(
        route_activation["active_local_hypothesis_id"] == "hypothesis:weak-coupling",
        "Expected the weak-coupling route to remain the active local hypothesis.",
    )
    check(
        "Continue the weak-coupling route" in route_activation["active_local_action_summary"],
        "Expected the active local action summary to stay explicit.",
    )
    check(
        route_activation["active_local_action_ref"].endswith("action_queue.jsonl"),
        "Expected the active local action ref to point to the action queue surface.",
    )
    check(route_activation["parked_route_count"] == 2, "Expected exactly two parked route obligations.")
    check(
        len(route_activation["deferred_obligations"]) == 1,
        "Expected one deferred-buffer obligation.",
    )
    check(
        len(route_activation["followup_obligations"]) == 1,
        "Expected one follow-up obligation.",
    )
    check(
        replay_route_activation["active_local_hypothesis_id"] == "hypothesis:weak-coupling",
        "Expected replay to surface the active local hypothesis id.",
    )
    check(
        replay_bundle["conclusions"]["parked_route_count"] == 2,
        "Expected replay conclusions to surface the parked route count.",
    )
    check(
        "## Route activation" in runtime_protocol_text,
        "Expected the runtime protocol note to include the route-activation section.",
    )
    check(
        "Deferred obligations" in runtime_protocol_text and "Follow-up obligations" in runtime_protocol_text,
        "Expected the runtime protocol note to list both parked-route obligation lanes.",
    )
    check(
        "## Route Activation" in replay_text,
        "Expected the replay bundle note to include the route-activation section.",
    )
    check(
        "Parked route count" in replay_text,
        "Expected the replay bundle note to surface the parked-route summary.",
    )
    check(
        not followup_child_root.exists(),
        "Expected the bounded acceptance slice to avoid auto-spawning a follow-up topic directory.",
    )

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "active_local_hypothesis_id": route_activation["active_local_hypothesis_id"],
            "active_local_action_ref": route_activation["active_local_action_ref"],
            "parked_route_count": route_activation["parked_route_count"],
            "deferred_obligation_count": len(route_activation["deferred_obligations"]),
            "followup_obligation_count": len(route_activation["followup_obligations"]),
            "auto_spawned_followup_topic": followup_child_root.exists(),
        },
        "artifacts": {
            "runtime_protocol_note": str(runtime_protocol_note),
            "replay_json": str(replay_json),
            "replay_markdown": str(replay_md),
            "deferred_buffer": str(deferred_buffer),
            "followup_subtopics": str(followup_rows),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
