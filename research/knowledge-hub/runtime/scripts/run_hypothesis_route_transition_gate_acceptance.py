#!/usr/bin/env python
"""Isolated acceptance for the bounded hypothesis route transition-gate surface."""

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


def seed_demo_runtime(
    kernel_root: Path,
    *,
    topic_slug: str,
    include_current_topic: bool,
    request_checkpoint: bool,
) -> None:
    next_action_note = f"topics/{topic_slug}/runtime/next_action_decision.md"
    if include_current_topic:
        action_type = "manual_followup"
        action_summary = (
            "Stay on the weak-coupling route for the current bounded step while keeping the "
            "symmetry-breaking route visible."
        )
        question = "Should the current local route stay local or yield to the primary handoff candidate?"
        observables = ["Stay-local versus yield-to-handoff transition gate."]
    elif request_checkpoint:
        action_type = "select_validation_route"
        action_summary = "Choose the validation route before yielding to the symmetry-breaking handoff candidate."
        question = "Which validation route should be confirmed before yielding to the primary handoff candidate?"
        observables = ["Checkpoint-gated yield-to-handoff transition."]
    else:
        action_type = "manual_followup"
        action_summary = "Yield to the symmetry-breaking route now that no active local route remains."
        question = "Should the runtime yield directly to the primary handoff candidate now that the local route is absent?"
        observables = ["Direct yield-to-handoff transition gate."]

    competing_hypotheses: list[dict[str, Any]] = []
    if include_current_topic:
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
        symmetry_status = "active"
    else:
        symmetry_status = "leading"
    competing_hypotheses.append(
        {
            "hypothesis_id": "hypothesis:symmetry-breaking",
            "label": "Symmetry-breaking route",
            "status": symmetry_status,
            "summary": "The symmetry-breaking route is parked until the cited comparison source lands.",
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
            "summary": "The active topic should surface whether yielding is blocked, available, or checkpoint-gated.",
            "pointers": {
                "next_action_decision_note_path": next_action_note
            },
        },
    )
    (kernel_root / next_action_note).parent.mkdir(parents=True, exist_ok=True)
    (kernel_root / next_action_note).write_text(
        "# Next action\n\n" + action_summary + "\n",
        encoding="utf-8",
    )
    write_json(
        runtime_root / "interaction_state.json",
        {
            "human_request": "Show the bounded route transition gate.",
            "decision_surface": {
                "selected_action_id": f"action:{topic_slug}:route-transition-gate",
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
                "action_id": f"action:{topic_slug}:route-transition-gate",
                "status": "pending",
                "action_type": action_type,
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
            "scope": ["Keep route transition gating bounded to explicit route choice and checkpoint artifacts."],
            "assumptions": ["Only durable runtime artifacts count as progress."],
            "non_goals": ["Do not auto-reactivate, auto-reintegrate, or auto-mutate route state."],
            "context_intake": ["Human request: surface the bounded route transition gate."],
            "source_basis_refs": ["paper:demo-source"],
            "interpretation_focus": ["Keep transition-gate visibility explicit without mutating runtime state."],
            "open_ambiguities": ["The active gate may be blocked, available, or checkpoint-gated."],
            "competing_hypotheses": competing_hypotheses,
            "formalism_and_notation": ["Stay with the bounded demo notation."],
            "observables": observables,
            "target_claims": ["candidate:demo-claim"],
            "deliverables": ["Keep route transition gating durable on the active topic surface."],
            "acceptance_tests": ["Runtime status and replay expose route transition gating directly."],
            "forbidden_proxies": ["Do not infer route transition gating from prose-only notes."],
            "uncertainty_markers": ["The bounded route may still require an explicit checkpoint or remain blocked."],
            "target_layers": ["L1", "L3", "L4", "L2"],
        },
    )
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


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-hypothesis-route-transition-gate-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)

    topics = [
        ("demo-topic-blocked", True, False, "blocked"),
        ("demo-topic-available", False, False, "available"),
        ("demo-topic-checkpoint", False, True, "checkpoint_required"),
    ]
    artifacts: dict[str, dict[str, str]] = {}
    checks: dict[str, dict[str, Any]] = {}
    for topic_slug, include_current_topic, request_checkpoint, expected_status in topics:
        seed_demo_runtime(
            kernel_root,
            topic_slug=topic_slug,
            include_current_topic=include_current_topic,
            request_checkpoint=request_checkpoint,
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
        operator_checkpoint_note = kernel_root / "topics" / topic_slug / "runtime" / "operator_checkpoint.active.md"
        for path in (runtime_protocol_note, replay_json, replay_md, operator_checkpoint_note):
            ensure_exists(path)

        route_choice = status_payload["active_research_contract"]["route_choice"]
        route_gate = status_payload["active_research_contract"]["route_transition_gate"]
        replay_bundle = replay_payload["payload"]
        runtime_protocol_text = runtime_protocol_note.read_text(encoding="utf-8")
        replay_text = replay_md.read_text(encoding="utf-8")

        check(route_gate["transition_status"] == expected_status, f"Expected {topic_slug} to expose `{expected_status}`.")
        check(
            replay_bundle["route_transition_gate"]["transition_status"] == expected_status,
            f"Expected replay to expose `{expected_status}` for {topic_slug}.",
        )
        check(
            replay_bundle["current_position"]["route_transition_gate_status"] == expected_status,
            f"Expected replay current position to expose `{expected_status}` for {topic_slug}.",
        )
        check(
            replay_bundle["conclusions"]["route_transition_gate_status"] == expected_status,
            f"Expected replay conclusions to expose `{expected_status}` for {topic_slug}.",
        )
        check("## Route transition gate" in runtime_protocol_text, f"Expected runtime protocol to include the route transition gate for {topic_slug}.")
        check("## Route Transition Gate" in replay_text, f"Expected replay markdown to include the route transition gate for {topic_slug}.")

        if expected_status == "blocked":
            check(route_choice["choice_status"] == "stay_local", "Expected the blocked topic to stay local.")
            check(route_gate["gate_kind"] == "current_route_choice", "Expected the blocked topic to point at the current route-choice artifact.")
            check("next_action_decision.md" in route_gate["gate_artifact_ref"], "Expected the blocked gate to point at the route-choice note.")
        elif expected_status == "available":
            check(route_choice["choice_status"] == "yield_to_handoff", "Expected the available topic to yield to handoff.")
            check(route_gate["gate_kind"] == "handoff_candidate_ready", "Expected the available topic to point at the ready handoff lane.")
            check("deferred_candidates.json" in route_gate["transition_target_ref"], "Expected the available gate to point at the deferred-buffer artifact.")
        else:
            check(status_payload["operator_checkpoint"]["status"] == "requested", "Expected the checkpoint topic to materialize a requested checkpoint.")
            check(route_choice["choice_status"] == "yield_to_handoff", "Expected the checkpoint topic to keep the yield choice visible.")
            check(route_gate["gate_kind"] == "operator_checkpoint", "Expected the checkpoint topic to point at the operator checkpoint.")
            check("operator_checkpoint.active.md" in route_gate["gate_artifact_ref"], "Expected the checkpoint gate to point at the operator checkpoint note.")

        check(
            not read_jsonl(kernel_root / "topics" / topic_slug / "runtime" / "followup_reintegration.jsonl"),
            f"Expected {topic_slug} not to materialize a follow-up reintegration receipt.",
        )
        candidate_ledger = kernel_root / "topics" / topic_slug / "L3" / "runs" / "run-001" / "candidate_ledger.jsonl"
        reactivated_rows = [
            row
            for row in read_jsonl(candidate_ledger)
            if str(row.get("candidate_id") or "").strip() == "candidate:demo-symmetry-reactivated"
            or str(row.get("reactivated_from") or "").strip()
        ]
        check(
            not reactivated_rows,
            f"Expected the bounded transition-gate slice not to materialize a reactivated deferred candidate for {topic_slug}.",
        )

        artifacts[topic_slug] = {
            "runtime_protocol_note": str(runtime_protocol_note),
            "replay_json": str(replay_json),
            "replay_markdown": str(replay_md),
            "operator_checkpoint_note": str(operator_checkpoint_note),
            "candidate_ledger": str(candidate_ledger),
        }
        checks[topic_slug] = {
            "choice_status": route_choice["choice_status"],
            "transition_status": route_gate["transition_status"],
            "gate_kind": route_gate["gate_kind"],
            "checkpoint_status": route_gate["checkpoint_status"],
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
