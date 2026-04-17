#!/usr/bin/env python
"""Isolated acceptance for the analytical cross-check runtime surface."""

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
        },
    )
    write_json(runtime_root / "session_start.contract.json", {"updated_at": "test-seed"})
    write_json(
        runtime_root / "interaction_state.json",
        {
            "human_request": "Continue the analytical route and keep the cross-check surface visible.",
            "decision_surface": {
                "decision_mode": "continue_unfinished",
                "decision_source": "heuristic",
                "decision_contract_status": "missing",
                "control_note_path": None,
                "selected_action_id": "action:demo-topic:proof",
            },
        },
    )
    write_jsonl(
        runtime_root / "action_queue.jsonl",
        [
            {
                "action_id": "action:demo-topic:proof",
                "status": "pending",
                "action_type": "proof_review",
                "summary": "Check the bounded analytical route before deeper execution.",
                "auto_runnable": False,
                "queue_source": "heuristic",
            }
        ],
    )


def seed_demo_validation(kernel_root: Path) -> None:
    write_jsonl(
        kernel_root / "topics" / "demo-topic" / "L3" / "runs" / "run-001" / "candidate_ledger.jsonl",
        [
            {
                "candidate_id": "candidate:demo-candidate",
                "candidate_type": "concept",
                "title": "Demo Analytical Concept",
                "summary": "A bounded concept for analytical cross-check acceptance.",
                "topic_slug": "demo-topic",
                "run_id": "run-001",
                "origin_refs": [],
                "question": "Does the runtime surface keep bounded analytical checks visible?",
                "assumptions": ["Weak-coupling regime only."],
                "proposed_validation_route": "analytical",
                "intended_l2_targets": ["concept:demo-analytical-concept"],
                "status": "ready_for_validation",
            }
        ],
    )
    write_jsonl(
        kernel_root / "topics" / "demo-topic" / "L0" / "source_index.jsonl",
        [
            {
                "source_id": "paper:demo-source",
                "source_type": "paper",
                "title": "Demo source",
                "summary": "Demo summary for analytical cross-check acceptance.",
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
        else Path(tempfile.mkdtemp(prefix="aitp-analytical-cross-check-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    seed_demo_runtime(kernel_root)
    seed_demo_validation(kernel_root)

    analytical_review_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "analytical-review",
            "--topic-slug",
            "demo-topic",
            "--candidate-id",
            "candidate:demo-candidate",
            "--check",
            "limiting_case=weak-coupling:passed:Matches the known free limit.",
            "--check",
            "source_cross_reference=intro-vs-appendix:passed:Cross-referenced source sections agree on the bounded limit.",
            "--source-anchor",
            "paper:demo-source#sec:intro",
            "--assumption",
            "assumption:weak-coupling-regime",
            "--regime-note",
            "Weak-coupling only.",
            "--reading-depth",
            "targeted",
            "--json",
        ],
    )
    verify_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["verify", "--topic-slug", "demo-topic", "--mode", "analytical", "--json"],
    )
    status_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", "demo-topic", "--json"],
    )

    bundle_path = kernel_root / str(status_payload["validation_review_bundle"]["path"])
    bundle_note_path = kernel_root / str(status_payload["validation_review_bundle"]["note_path"])
    runtime_protocol_path = Path(verify_payload["runtime_protocol"]["runtime_protocol_path"])
    runtime_protocol_note_path = Path(verify_payload["runtime_protocol"]["runtime_protocol_note_path"])
    for path in (bundle_path, bundle_note_path, runtime_protocol_path, runtime_protocol_note_path):
        ensure_exists(path)

    bundle_payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    cross_check_surface = status_payload["validation_review_bundle"]["analytical_cross_check_surface"]
    check(analytical_review_payload["overall_status"] == "ready", "Expected analytical-review to pass.")
    check(cross_check_surface["status"] == "ready", "Expected analytical cross-check surface to be ready.")
    check(cross_check_surface["check_rows"][0]["kind"] == "limiting_case", "Expected limiting-case row first.")
    check(
        cross_check_surface["check_rows"][1]["kind"] == "source_cross_reference",
        "Expected source-cross-reference row in status payload.",
    )
    check(
        cross_check_surface["check_rows"][0]["source_anchors"] == ["paper:demo-source#sec:intro"],
        "Expected source anchors on the structured analytical runtime surface.",
    )
    check(
        bundle_payload["analytical_cross_check_surface"]["check_rows"][1]["kind"] == "source_cross_reference",
        "Expected bundle JSON to expose the same analytical cross-check surface.",
    )
    bundle_note = bundle_note_path.read_text(encoding="utf-8")
    runtime_protocol_note = runtime_protocol_note_path.read_text(encoding="utf-8")
    check("## Analytical cross-check surface" in bundle_note, "Expected bundle note to render the analytical cross-check section.")
    check("source_cross_reference" in bundle_note, "Expected bundle note to mention the source-cross-reference row.")
    check("## Analytical cross-check surface" in runtime_protocol_note, "Expected runtime protocol note to render the analytical cross-check section.")
    check("source_cross_reference" in runtime_protocol_note, "Expected runtime protocol note to mention the source-cross-reference row.")

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "analytical_review_status": analytical_review_payload["overall_status"],
            "bundle_status": status_payload["validation_review_bundle"]["status"],
            "cross_check_status": cross_check_surface["status"],
            "primary_review_kind": status_payload["validation_review_bundle"]["primary_review_kind"],
            "check_count": cross_check_surface["check_count"],
        },
        "artifacts": {
            "validation_review_bundle_path": str(bundle_path),
            "validation_review_bundle_note_path": str(bundle_note_path),
            "runtime_protocol_path": str(runtime_protocol_path),
            "runtime_protocol_note_path": str(runtime_protocol_note_path),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
