#!/usr/bin/env python
"""Isolated acceptance for the bounded hypothesis route transition-resumption surface."""

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
    route_mode: str,
    checkpoint_trigger: bool,
) -> None:
    next_action_note = f"topics/{topic_slug}/runtime/next_action_decision.md"
    if route_mode == "current_weak":
        action_summary = (
            "Stay on the weak-coupling route for the current bounded step while keeping the "
            "symmetry-breaking route visible."
        )
        question = "Is any route transition resumption currently applicable?"
        observables = ["No route transition resumption is required."]
        resume_reason = "Hold the current weak-coupling route while the intended handoff remains unresolved."
        seed_recorded_receipt = False
    else:
        action_summary = "Yield to the symmetry-breaking route now that the bounded handoff has been enacted."
        if checkpoint_trigger:
            action_summary = (
                "A contradiction remains unresolved, so yield to the symmetry-breaking route only after"
                " explicit operator adjudication."
            )
        question = "Has bounded transition follow-through actually been resumed yet?"
        observables = ["Route transition resumption should stay explicit on the active topic surface."]
        resume_reason = "Activated hypothesis:symmetry-breaking from the deferred buffer after the bounded handoff."
        seed_recorded_receipt = True

    competing_hypotheses: list[dict[str, Any]] = []
    if route_mode == "current_weak":
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
        competing_hypotheses.append(
            {
                "hypothesis_id": "hypothesis:symmetry-breaking",
                "label": "Symmetry-breaking route",
                "status": "active",
                "summary": "The symmetry-breaking route is the bounded handoff target.",
                "route_kind": "deferred_buffer",
                "route_target_summary": "Park the symmetry-breaking route in the deferred buffer until bounded reactivation conditions are met.",
                "route_target_ref": f"topics/{topic_slug}/runtime/deferred_candidates.json",
                "evidence_refs": ["paper:demo-source-b"],
                "exclusion_notes": [],
            }
        )
    elif route_mode == "deferred_target":
        competing_hypotheses.append(
            {
                "hypothesis_id": "hypothesis:symmetry-breaking",
                "label": "Symmetry-breaking route",
                "status": "leading",
                "summary": "The symmetry-breaking route is the bounded handoff target.",
                "route_kind": "deferred_buffer",
                "route_target_summary": "Park the symmetry-breaking route in the deferred buffer until bounded reactivation conditions are met.",
                "route_target_ref": f"topics/{topic_slug}/runtime/deferred_candidates.json",
                "evidence_refs": ["paper:demo-source-b"],
                "exclusion_notes": [],
            }
        )
    else:
        competing_hypotheses.append(
            {
                "hypothesis_id": "hypothesis:symmetry-breaking",
                "label": "Symmetry-breaking route",
                "status": "active",
                "summary": "The symmetry-breaking route is already the resumed local route.",
                "route_kind": "current_topic",
                "route_target_summary": "Keep the symmetry-breaking route on the current topic branch.",
                "route_target_ref": f"topics/{topic_slug}/runtime/action_queue.jsonl",
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
            "summary": "The active topic should surface route transition resumption explicitly.",
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
            "human_request": "Show the bounded route transition resumption.",
            "decision_surface": {
                "selected_action_id": f"action:{topic_slug}:route-transition-resumption",
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
                "action_id": f"action:{topic_slug}:route-transition-resumption",
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
            "scope": ["Keep route transition resumption bounded to explicit follow-through and route-state artifacts."],
            "assumptions": ["Only durable runtime artifacts count as progress."],
            "non_goals": ["Do not auto-resume or auto-dispatch route state in this slice."],
            "context_intake": ["Human request: surface the bounded route transition resumption."],
            "source_basis_refs": ["paper:demo-source"],
            "interpretation_focus": ["Keep transition resumption explicit without mutating runtime state."],
            "open_ambiguities": ["The bounded route handoff may still need explicit durable re-entry after follow-through."],
            "competing_hypotheses": competing_hypotheses,
            "formalism_and_notation": ["Stay with the bounded demo notation."],
            "observables": observables,
            "target_claims": ["candidate:demo-claim"],
            "deliverables": ["Keep route transition resumption durable on the active topic surface."],
            "acceptance_tests": ["Runtime status and replay expose route transition resumption directly."],
            "forbidden_proxies": ["Do not infer route transition resumption from prose-only notes."],
            "uncertainty_markers": ["The bounded route handoff may still need explicit durable re-entry after follow-through."],
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
    if seed_recorded_receipt:
        target_ref = (
            f"topics/{topic_slug}/runtime/action_queue.jsonl"
            if route_mode == "current_target"
            else f"topics/{topic_slug}/runtime/deferred_candidates.json"
        )
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


def mark_checkpoint_answered(*, package_root: Path, kernel_root: Path, repo_root: Path, topic_slug: str) -> None:
    status_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", topic_slug, "--json"],
    )
    checkpoint = status_payload["operator_checkpoint"]
    check(checkpoint["status"] == "requested", f"Expected {topic_slug} to materialize a requested checkpoint first.")
    checkpoint_path = kernel_root / "topics" / topic_slug / "runtime" / "operator_checkpoint.active.json"
    payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    payload["status"] = "answered"
    payload["active"] = False
    payload["answer"] = "Proceed with bounded route resumption."
    payload["answered_at"] = "2026-04-12T00:05:00+00:00"
    payload["answered_by"] = "test"
    payload["updated_at"] = "2026-04-12T00:05:00+00:00"
    payload["updated_by"] = "test"
    checkpoint_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-hypothesis-route-transition-resumption-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)

    topics = [
        ("demo-topic-no-resumption", "current_weak", False, "none"),
        ("demo-topic-resumption-waiting", "deferred_target", False, "waiting_followthrough"),
        ("demo-topic-resumption-pending", "deferred_target", True, "pending"),
        ("demo-topic-resumption-resumed", "current_target", False, "resumed"),
    ]
    artifacts: dict[str, dict[str, str]] = {}
    checks: dict[str, dict[str, Any]] = {}
    for topic_slug, route_mode, checkpoint_trigger, expected_status in topics:
        seed_demo_runtime(
            kernel_root,
            topic_slug=topic_slug,
            route_mode=route_mode,
            checkpoint_trigger=checkpoint_trigger,
        )
        if topic_slug == "demo-topic-resumption-pending":
            mark_checkpoint_answered(
                package_root=package_root,
                kernel_root=kernel_root,
                repo_root=repo_root,
                topic_slug=topic_slug,
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

        resumption = status_payload["active_research_contract"]["route_transition_resumption"]
        replay_bundle = replay_payload["payload"]
        runtime_protocol_text = runtime_protocol_note.read_text(encoding="utf-8")
        replay_text = replay_md.read_text(encoding="utf-8")

        check(resumption["resumption_status"] == expected_status, f"Expected {topic_slug} to expose `{expected_status}`.")
        check(
            replay_bundle["route_transition_resumption"]["resumption_status"] == expected_status,
            f"Expected replay to expose `{expected_status}` for {topic_slug}.",
        )
        check(
            replay_bundle["current_position"]["route_transition_resumption_status"] == expected_status,
            f"Expected replay current position to expose `{expected_status}` for {topic_slug}.",
        )
        check(
            replay_bundle["conclusions"]["route_transition_resumption_status"] == expected_status,
            f"Expected replay conclusions to expose `{expected_status}` for {topic_slug}.",
        )
        check("## Route transition resumption" in runtime_protocol_text, f"Expected runtime protocol to include the route transition resumption for {topic_slug}.")
        check("## Route Transition Resumption" in replay_text, f"Expected replay markdown to include the route transition resumption for {topic_slug}.")

        if expected_status == "none":
            check(resumption["resumption_kind"] == "none", "Expected the no-resumption topic to keep kind none.")
        elif expected_status == "waiting_followthrough":
            check(resumption["resumption_kind"] == "followthrough_held", "Expected the waiting topic to expose followthrough_held.")
        elif expected_status == "pending":
            check(resumption["resumption_kind"] == "ready_not_resumed", "Expected the pending topic to expose ready_not_resumed.")
            check(resumption["followthrough_status"] == "ready", "Expected the pending topic to show ready follow-through.")
        else:
            check(resumption["resumption_kind"] == "target_route_active", "Expected the resumed topic to expose target_route_active.")
            check(resumption["active_route_alignment"] == "target_active", "Expected the resumed topic to keep target_active alignment.")

        candidate_ledger = kernel_root / "topics" / topic_slug / "L3" / "runs" / "run-001" / "candidate_ledger.jsonl"
        reactivated_rows = [
            row
            for row in read_jsonl(candidate_ledger)
            if str(row.get("candidate_id") or "").strip() == "candidate:demo-symmetry-reactivated"
            or str(row.get("reactivated_from") or "").strip()
        ]
        check(
            not reactivated_rows,
            f"Expected the bounded transition-resumption slice not to materialize a reactivated deferred candidate for {topic_slug}.",
        )

        artifacts[topic_slug] = {
            "runtime_protocol_note": str(runtime_protocol_note),
            "replay_json": str(replay_json),
            "replay_markdown": str(replay_md),
            "transition_history_note": str(transition_history_note),
            "candidate_ledger": str(candidate_ledger),
        }
        checks[topic_slug] = {
            "resumption_status": resumption["resumption_status"],
            "resumption_kind": resumption["resumption_kind"],
            "active_route_alignment": resumption["active_route_alignment"],
            "resumption_ref": resumption["resumption_ref"],
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
