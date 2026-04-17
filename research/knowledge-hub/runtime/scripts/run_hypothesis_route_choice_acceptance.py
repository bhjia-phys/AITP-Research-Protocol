#!/usr/bin/env python
"""Isolated acceptance for the bounded hypothesis route choice surface."""

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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


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
            "summary": "The active topic should show whether the current route stays local or yields to the handoff candidate.",
            "pointers": {
                "next_action_decision_note_path": "topics/demo-topic/runtime/next_action_decision.md"
            },
        },
    )
    (runtime_root / "next_action_decision.md").write_text(
        "# Next action\n\nStay on the weak-coupling route for the current bounded step.\n",
        encoding="utf-8",
    )
    write_json(
        runtime_root / "interaction_state.json",
        {
            "human_request": "Show whether the current local route should stay local or yield to the parked handoff candidate.",
            "decision_surface": {
                "selected_action_id": "action:demo-topic:route-choice",
                "decision_source": "heuristic",
                "next_action_decision_note_path": "topics/demo-topic/runtime/next_action_decision.md",
            },
            "action_queue_surface": {
                "queue_source": "heuristic"
            },
        },
    )
    write_jsonl(
        runtime_root / "action_queue.jsonl",
        [
            {
                "action_id": "action:demo-topic:route-choice",
                "status": "pending",
                "action_type": "manual_followup",
                "summary": "Stay on the weak-coupling route for the current bounded step while keeping the parked handoff candidate visible.",
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
            "question": "Should the current local route stay local or yield to the primary handoff candidate?",
            "scope": [
                "Keep route choice bounded to explicit route activation, re-entry, and handoff artifacts.",
                "Do not mutate runtime state in this slice.",
            ],
            "assumptions": [
                "Only durable runtime artifacts count as progress.",
            ],
            "non_goals": [
                "Do not auto-reactivate or auto-reintegrate parked routes.",
            ],
            "context_intake": [
                "Human request: surface stay-local versus yield choice.",
            ],
            "source_basis_refs": ["paper:demo-source"],
            "interpretation_focus": ["Keep route choice explicit without mutating runtime state."],
            "open_ambiguities": [
                "The current bounded step may still favor the local route even when a parked route is ready.",
            ],
            "competing_hypotheses": [
                {
                    "hypothesis_id": "hypothesis:weak-coupling",
                    "label": "Weak-coupling route",
                    "status": "leading",
                    "summary": "The weak-coupling route remains the active local branch.",
                    "route_kind": "current_topic",
                    "route_target_summary": "Keep the weak-coupling route on the current topic branch.",
                    "route_target_ref": "topics/demo-topic/runtime/action_queue.jsonl",
                    "evidence_refs": ["paper:demo-source"],
                    "exclusion_notes": [],
                },
                {
                    "hypothesis_id": "hypothesis:symmetry-breaking",
                    "label": "Symmetry-breaking route",
                    "status": "active",
                    "summary": "The symmetry-breaking route is parked until the cited comparison source lands.",
                    "route_kind": "deferred_buffer",
                    "route_target_summary": "Park the symmetry-breaking route in the deferred buffer until bounded reactivation conditions are met.",
                    "route_target_ref": "topics/demo-topic/runtime/deferred_candidates.json",
                    "evidence_refs": ["paper:demo-source-b"],
                    "exclusion_notes": [],
                },
                {
                    "hypothesis_id": "hypothesis:prior-work",
                    "label": "Prior-work route",
                    "status": "watch",
                    "summary": "The prior-work route is parked until the child route returns bounded evidence.",
                    "route_kind": "followup_subtopic",
                    "route_target_summary": "Route the prior-work distinction into a bounded follow-up subtopic.",
                    "route_target_ref": "topics/demo-topic/runtime/followup_subtopics.jsonl",
                    "evidence_refs": ["note:demo-prior-work-gap"],
                    "exclusion_notes": [],
                },
            ],
            "formalism_and_notation": ["Stay with the bounded demo notation."],
            "observables": ["Stay-local versus yield-to-handoff choice."],
            "target_claims": ["candidate:demo-claim"],
            "deliverables": ["Keep route choice durable on the active topic surface."],
            "acceptance_tests": ["Runtime status and replay expose route choice directly."],
            "forbidden_proxies": ["Do not infer route choice from prose-only notes."],
            "uncertainty_markers": ["The current bounded step may still favor the local route."],
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
                    "entry_id": "deferred:demo-symmetry",
                    "source_candidate_id": "candidate:demo-symmetry",
                    "title": "Symmetry-breaking route",
                    "summary": "Park the symmetry-breaking route until the cited comparison source lands.",
                    "reason": "Current evidence is still too thin for parent-topic reintegration.",
                    "status": "buffered",
                    "reactivation_conditions": {
                        "source_ids_any": ["paper:demo-source-b"]
                    },
                    "reactivation_candidate": {
                        "candidate_id": "candidate:demo-symmetry-reactivated",
                        "summary": "Reactivated symmetry-breaking candidate."
                    },
                }
            ],
        },
    )
    write_jsonl(
        kernel_root / "topics" / "demo-topic" / "L0" / "source_index.jsonl",
        [
            {
                "source_id": "paper:demo-source-b",
                "title": "Demo Source B",
                "summary": "The cited comparison source required for the symmetry-breaking route is now present.",
            }
        ],
    )
    child_packet_path = (
        kernel_root / "topics" / "demo-topic--followup--prior-work" / "runtime"
        / "followup_return_packet.json"
    )
    write_jsonl(
        runtime_root / "followup_subtopics.jsonl",
        [
            {
                "child_topic_slug": "demo-topic--followup--prior-work",
                "parent_topic_slug": "demo-topic",
                "status": "spawned",
                "query": "Recover the missing prior-work distinction on a bounded child route.",
                "return_packet_path": str(child_packet_path),
            }
        ],
    )
    write_json(
        child_packet_path,
        {
            "return_packet_version": 1,
            "child_topic_slug": "demo-topic--followup--prior-work",
            "parent_topic_slug": "demo-topic",
            "parent_run_id": "run-001",
            "receipt_id": "receipt:demo-prior-work",
            "query": "Recover the missing prior-work distinction on a bounded child route.",
            "parent_gap_ids": ["open_gap:prior-work"],
            "parent_followup_task_ids": ["followup_source_task:prior-work"],
            "reentry_targets": ["definition:demo-prior-work"],
            "supporting_regression_question_ids": ["regression_question:prior-work"],
            "source_id": "paper:demo-prior-work",
            "arxiv_id": "1234.56789",
            "expected_return_route": "L0->L1->L3->L4->L2",
            "acceptable_return_shapes": ["recovered_units", "resolved_gap_update", "still_unresolved_packet"],
            "required_output_artifacts": ["candidate_ledger_or_recovered_units"],
            "unresolved_return_statuses": ["pending_reentry", "returned_with_gap", "returned_unresolved"],
            "return_status": "recovered_units",
            "accepted_return_shape": "recovered_units",
            "return_summary": "Recovered the missing prior-work distinction and the parent topic can now reconsider the parked route.",
            "return_artifact_paths": [
                "topics/demo-topic/L3/runs/run-001/candidate_ledger.jsonl"
            ],
            "reintegration_requirements": {
                "must_write_back_parent_gaps": True,
                "must_update_reentry_targets": True,
                "must_not_patch_parent_directly": True,
                "requires_child_topic_summary": True,
            },
            "updated_at": "2026-04-12T00:00:00+00:00",
            "updated_by": "test",
        },
    )


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-hypothesis-route-choice-acceptance-")).resolve()
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
    parent_reintegration = runtime_root / "followup_reintegration.jsonl"
    feedback_ledger = kernel_root / "topics" / "demo-topic" / "L3" / "runs" / "run-001" / "candidate_ledger.jsonl"
    reintegration_rows = read_jsonl(parent_reintegration)
    feedback_rows = read_jsonl(feedback_ledger)
    reactivated_rows = [
        row
        for row in feedback_rows
        if str(row.get("candidate_id") or "").strip() == "candidate:demo-symmetry-reactivated"
        or str(row.get("reactivated_from") or "").strip()
    ]
    for path in (runtime_protocol_note, replay_json, replay_md, deferred_buffer, followup_rows):
        ensure_exists(path)

    active_research = status_payload["active_research_contract"]
    route_choice = active_research["route_choice"]
    replay_bundle = replay_payload["payload"]
    replay_route_choice = replay_bundle["route_choice"]
    runtime_protocol_text = runtime_protocol_note.read_text(encoding="utf-8")
    replay_text = replay_md.read_text(encoding="utf-8")

    check(route_choice["choice_status"] == "stay_local", "Expected the bounded choice to remain on the current local route.")
    check(route_choice["active_local_hypothesis_id"] == "hypothesis:weak-coupling", "Expected the weak-coupling route to remain the active local hypothesis.")
    check(route_choice["primary_handoff_candidate_id"] == "hypothesis:symmetry-breaking", "Expected the symmetry-breaking route to remain the primary handoff candidate.")
    check(route_choice["stay_local_option"]["hypothesis_id"] == "hypothesis:weak-coupling", "Expected the stay-local option to point at the active local hypothesis.")
    check(route_choice["yield_to_handoff_option"]["hypothesis_id"] == "hypothesis:symmetry-breaking", "Expected the yield option to point at the handoff candidate.")
    check("remains the next parked-route handoff candidate" in route_choice["choice_summary"], "Expected the choice summary to explain the handoff candidate while staying local.")
    check(replay_route_choice["choice_status"] == "stay_local", "Expected replay to surface the stay-local choice.")
    check(replay_bundle["conclusions"]["route_choice_status"] == "stay_local", "Expected replay conclusions to surface the route-choice status.")
    check("## Route choice" in runtime_protocol_text, "Expected the runtime protocol note to include the route choice section.")
    check("Choice status: `stay_local`" in runtime_protocol_text, "Expected the runtime protocol note to show the choice status.")
    check("## Route Choice" in replay_text, "Expected the replay bundle note to include the route choice section.")
    check("Yield to handoff" in replay_text, "Expected the replay bundle note to show the yield option.")
    check(not reintegration_rows, "Expected the bounded slice to avoid writing a reintegration receipt.")
    check(not reactivated_rows, "Expected the bounded slice to avoid materializing a reactivated deferred candidate.")

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "choice_status": route_choice["choice_status"],
            "active_local_hypothesis_id": route_choice["active_local_hypothesis_id"],
            "primary_handoff_candidate_id": route_choice["primary_handoff_candidate_id"],
            "auto_reintegrated_parent": bool(reintegration_rows),
            "auto_reactivated_candidate": bool(reactivated_rows),
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
