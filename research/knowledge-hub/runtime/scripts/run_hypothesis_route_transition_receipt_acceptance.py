#!/usr/bin/env python
"""Isolated acceptance for the bounded hypothesis route transition-receipt surface."""

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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def seed_demo_runtime(
    kernel_root: Path,
    *,
    topic_slug: str,
    include_current_topic: bool,
    include_target_route: bool,
    seed_recorded_receipt: bool,
) -> None:
    next_action_note = f"topics/{topic_slug}/runtime/next_action_decision.md"
    if include_current_topic and include_target_route:
        action_summary = (
            "Stay on the weak-coupling route for the current bounded step while keeping the "
            "symmetry-breaking route visible."
        )
        question = "Has the intended handoff from the local route to the symmetry-breaking route been durably recorded?"
        observables = ["Pending route transition receipt."]
        resume_reason = "Hold the current weak-coupling route while the intended handoff remains pending."
    elif include_target_route:
        action_summary = "Yield to the symmetry-breaking route now that the bounded handoff has been enacted."
        question = "Has the intended handoff to the symmetry-breaking route been durably recorded?"
        observables = ["Recorded route transition receipt."]
        resume_reason = "Activated hypothesis:symmetry-breaking from the deferred buffer after the bounded handoff."
    else:
        action_summary = "Stay on the weak-coupling route because no bounded handoff candidate is currently declared."
        question = "Is any route transition receipt currently applicable?"
        observables = ["No route transition receipt is applicable."]
        resume_reason = "No bounded route handoff is currently applicable."

    competing_hypotheses: list[dict[str, Any]] = []
    if include_current_topic or not include_target_route:
        competing_hypotheses.append(
            {
                "hypothesis_id": "hypothesis:weak-coupling",
                "label": "Weak-coupling route",
                "status": "leading",
                "summary": "The weak-coupling route remains the active local branch.",
                "route_kind": "current_topic",
                "route_target_summary": "Keep the weak-coupling route on the current topic branch.",
                "route_target_ref": f"topics/{topic_slug}/runtime/action_queue.jsonl",
                "evidence_refs": ["paper:demo-source"],
                "exclusion_notes": [],
            }
        )
    if include_target_route:
        competing_hypotheses.append(
            {
                "hypothesis_id": "hypothesis:symmetry-breaking",
                "label": "Symmetry-breaking route",
                "status": "active" if include_current_topic else "leading",
                "summary": "The symmetry-breaking route is the bounded handoff target.",
                "route_kind": "deferred_buffer",
                "route_target_summary": "Park the symmetry-breaking route in the deferred buffer until bounded reactivation conditions are met.",
                "route_target_ref": f"topics/{topic_slug}/runtime/deferred_candidates.json",
                "evidence_refs": ["paper:demo-source-b"],
                "exclusion_notes": [],
            }
        )

    runtime_root = kernel_root / "topics" / topic_slug / "runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    write_json(
        runtime_root / "topic_state.json",
        {
            "topic_slug": topic_slug,
            "latest_run_id": "run-001",
            "resume_stage": "L3",
            "last_materialized_stage": "L3",
            "research_mode": "formal_derivation",
            "summary": "The active topic should surface route transition receipt explicitly.",
            "resume_reason": resume_reason,
            "pointers": {
                "next_action_decision_note_path": next_action_note
            },
        },
    )
    write_text(kernel_root / next_action_note, "# Next action\n\n" + action_summary + "\n")
    write_json(
        runtime_root / "interaction_state.json",
        {
            "human_request": "Show the bounded route transition receipt.",
            "decision_surface": {
                "selected_action_id": f"action:{topic_slug}:route-transition-receipt",
                "decision_source": "heuristic",
                "next_action_decision_note_path": next_action_note,
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
                "action_id": f"action:{topic_slug}:route-transition-receipt",
                "status": "pending",
                "action_type": "manual_followup",
                "summary": action_summary,
                "auto_runnable": False,
                "queue_source": "heuristic",
            }
        ],
    )
    write_json(
        runtime_root / "research_question.contract.json",
        {
            "contract_version": 1,
            "question_id": f"research_question:{topic_slug}",
            "title": "Demo Topic",
            "topic_slug": topic_slug,
            "status": "active",
            "template_mode": "formal_theory",
            "research_mode": "formal_derivation",
            "question": question,
            "scope": ["Keep route transition receipt bounded to explicit transition intent and transition-history artifacts."],
            "assumptions": ["Only durable runtime artifacts count as progress."],
            "non_goals": ["Do not auto-reactivate, auto-reintegrate, or auto-mutate route state in this slice."],
            "context_intake": ["Human request: surface the bounded route transition receipt."],
            "source_basis_refs": ["paper:demo-source"],
            "interpretation_focus": ["Keep transition receipt explicit without mutating runtime state."],
            "open_ambiguities": ["The intended handoff may still be pending, recorded, or absent."],
            "competing_hypotheses": competing_hypotheses,
            "formalism_and_notation": ["Stay with the bounded demo notation."],
            "observables": observables,
            "target_claims": ["candidate:demo-claim"],
            "deliverables": ["Keep route transition receipt durable on the active topic surface."],
            "acceptance_tests": ["Runtime status and replay expose route transition receipt directly."],
            "forbidden_proxies": ["Do not infer route transition receipt from prose-only notes."],
            "uncertainty_markers": ["The bounded route handoff may still lack a durable receipt row."],
            "target_layers": ["L1", "L3", "L4", "L2"],
        },
    )
    if include_target_route:
        write_json(
            runtime_root / "deferred_candidates.json",
            {
                "buffer_version": 1,
                "topic_slug": topic_slug,
                "updated_at": "2026-04-12T00:00:00+00:00",
                "updated_by": "test",
                "entries": [
                    {
                        "entry_id": f"deferred:{topic_slug}:symmetry",
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
            kernel_root / "topics" / topic_slug / "L0" / "source_index.jsonl",
            [
                {
                    "source_id": "paper:demo-source-b",
                    "title": "Demo Source B",
                    "summary": "The cited comparison source required for the symmetry-breaking route is now present.",
                }
            ],
        )
    if seed_recorded_receipt:
        target_ref = f"topics/{topic_slug}/runtime/deferred_candidates.json"
        write_json(
            runtime_root / "transition_history.json",
            {
                "topic_slug": topic_slug,
                "status": "recorded",
                "transition_count": 1,
                "forward_count": 0,
                "backtrack_count": 0,
                "hold_count": 1,
                "demotion_count": 0,
                "latest_transition": {
                    "transition_id": f"transition:{topic_slug}:route-handoff",
                    "event_kind": "route_handoff_recorded",
                    "from_layer": "L3",
                    "to_layer": "L3",
                    "transition_kind": "boundary_hold",
                    "reason": "Recorded enactment of hypothesis:symmetry-breaking on the bounded route handoff.",
                    "evidence_refs": [target_ref],
                    "candidate_id": "",
                    "recorded_at": "2026-04-12T00:00:00+00:00",
                    "recorded_by": "test",
                },
                "latest_demotion": {},
                "rows": [
                    {
                        "transition_id": f"transition:{topic_slug}:route-handoff",
                        "event_kind": "route_handoff_recorded",
                        "from_layer": "L3",
                        "to_layer": "L3",
                        "transition_kind": "boundary_hold",
                        "reason": "Recorded enactment of hypothesis:symmetry-breaking on the bounded route handoff.",
                        "evidence_refs": [target_ref],
                        "candidate_id": "",
                        "recorded_at": "2026-04-12T00:00:00+00:00",
                        "recorded_by": "test",
                    }
                ],
                "log_path": f"topics/{topic_slug}/runtime/transition_history.jsonl",
                "path": f"topics/{topic_slug}/runtime/transition_history.json",
                "note_path": f"topics/{topic_slug}/runtime/transition_history.md",
            },
        )
        write_text(
            runtime_root / "transition_history.md",
            "# Transition history\n\nRecorded enactment of hypothesis:symmetry-breaking.\n",
        )


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-hypothesis-route-transition-receipt-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)

    topics = [
        ("demo-topic-pending-receipt", True, True, False, "pending"),
        ("demo-topic-recorded-receipt", False, True, True, "recorded"),
        ("demo-topic-no-receipt", True, False, False, "none"),
    ]
    artifacts: dict[str, dict[str, str]] = {}
    checks: dict[str, dict[str, Any]] = {}
    for topic_slug, include_current_topic, include_target_route, seed_recorded_receipt, expected_status in topics:
        seed_demo_runtime(
            kernel_root,
            topic_slug=topic_slug,
            include_current_topic=include_current_topic,
            include_target_route=include_target_route,
            seed_recorded_receipt=seed_recorded_receipt,
        )
        status_payload = run_cli_json(
            package_root=package_root,
            kernel_root=kernel_root,
            repo_root=repo_root,
            args=["status", "--topic-slug", topic_slug, "--json"],
        )
        replay_payload = run_cli_json(
            package_root=package_root,
            kernel_root=kernel_root,
            repo_root=repo_root,
            args=["replay-topic", "--topic-slug", topic_slug, "--json"],
        )

        runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"])
        replay_json = Path(replay_payload["json_path"])
        replay_md = Path(replay_payload["markdown_path"])
        transition_history_note = kernel_root / "topics" / topic_slug / "runtime" / "transition_history.md"
        for path in (runtime_protocol_note, replay_json, replay_md, transition_history_note):
            ensure_exists(path)

        route_receipt = status_payload["active_research_contract"]["route_transition_receipt"]
        replay_bundle = replay_payload["payload"]
        runtime_protocol_text = runtime_protocol_note.read_text(encoding="utf-8")
        replay_text = replay_md.read_text(encoding="utf-8")

        check(route_receipt["receipt_status"] == expected_status, f"Expected {topic_slug} to expose `{expected_status}`.")
        check(
            replay_bundle["route_transition_receipt"]["receipt_status"] == expected_status,
            f"Expected replay to expose `{expected_status}` for {topic_slug}.",
        )
        check(
            replay_bundle["current_position"]["route_transition_receipt_status"] == expected_status,
            f"Expected replay current position to expose `{expected_status}` for {topic_slug}.",
        )
        check(
            replay_bundle["conclusions"]["route_transition_receipt_status"] == expected_status,
            f"Expected replay conclusions to expose `{expected_status}` for {topic_slug}.",
        )
        check("## Route transition receipt" in runtime_protocol_text, f"Expected runtime protocol to include the route transition receipt for {topic_slug}.")
        check("## Route Transition Receipt" in replay_text, f"Expected replay markdown to include the route transition receipt for {topic_slug}.")

        if expected_status == "pending":
            check(route_receipt["source_hypothesis_id"] == "hypothesis:weak-coupling", "Expected the pending topic to retain the local source route.")
            check(route_receipt["target_hypothesis_id"] == "hypothesis:symmetry-breaking", "Expected the pending topic to point at the handoff target.")
        elif expected_status == "recorded":
            check(route_receipt["target_hypothesis_id"] == "hypothesis:symmetry-breaking", "Expected the recorded topic to point at the handoff target.")
            check(bool(route_receipt["receipt_transition_id"]), "Expected the recorded topic to expose a durable transition id.")
        else:
            check(route_receipt["target_hypothesis_id"] == "", "Expected the none topic to have no handoff target.")

        candidate_ledger = kernel_root / "topics" / topic_slug / "L3" / "runs" / "run-001" / "candidate_ledger.jsonl"
        reactivated_rows = [
            row
            for row in read_jsonl(candidate_ledger)
            if str(row.get("candidate_id") or "").strip() == "candidate:demo-symmetry-reactivated"
            or str(row.get("reactivated_from") or "").strip()
        ]
        check(
            not reactivated_rows,
            f"Expected the bounded transition-receipt slice not to materialize a reactivated deferred candidate for {topic_slug}.",
        )

        artifacts[topic_slug] = {
            "runtime_protocol_note": str(runtime_protocol_note),
            "replay_json": str(replay_json),
            "replay_markdown": str(replay_md),
            "transition_history_note": str(transition_history_note),
            "candidate_ledger": str(candidate_ledger),
        }
        checks[topic_slug] = {
            "receipt_status": route_receipt["receipt_status"],
            "intent_status": route_receipt["intent_status"],
            "source_hypothesis_id": route_receipt["source_hypothesis_id"],
            "target_hypothesis_id": route_receipt["target_hypothesis_id"],
        }

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": checks,
        "artifacts": artifacts,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
