#!/usr/bin/env python
"""Isolated acceptance for the analytical-review and research-judgment runtime surfaces."""

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
            "human_request": "Continue the derivation route and keep the judgment surface honest.",
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
                "summary": "Check sign conventions before combining the derivation branches.",
                "auto_runnable": False,
                "queue_source": "heuristic",
            }
        ],
    )
    write_jsonl(
        kernel_root / "runtime" / "collaborator_memory.jsonl",
        [
            {
                "memory_id": "collab-stuckness-demo",
                "recorded_at": "2026-04-11T10:00:00+08:00",
                "memory_kind": "stuckness",
                "summary": "The derivation keeps stalling at the sign-convention merge point.",
                "topic_slug": "demo-topic",
                "run_id": "run-001",
                "tags": ["formal-theory"],
                "related_topic_slugs": ["demo-topic"],
                "updated_by": "human",
            },
            {
                "memory_id": "collab-surprise-demo",
                "recorded_at": "2026-04-11T10:05:00+08:00",
                "memory_kind": "surprise",
                "summary": "The weak-coupling route unexpectedly preserved the target symmetry.",
                "topic_slug": "demo-topic",
                "run_id": "run-001",
                "tags": ["analytical"],
                "related_topic_slugs": ["demo-topic"],
                "updated_by": "human",
            },
        ],
    )
    (kernel_root / "runtime" / "collaborator_memory.md").write_text(
        "# Collaborator memory\n",
        encoding="utf-8",
    )


def seed_demo_validation(kernel_root: Path) -> None:
    write_jsonl(
        kernel_root / "topics" / "demo-topic" / "L3" / "runs" / "run-001" / "candidate_ledger.jsonl",
        [
            {
                "candidate_id": "candidate:demo-candidate",
                "candidate_type": "concept",
                "title": "Demo Analytical Concept",
                "summary": "A bounded concept for analytical judgment acceptance.",
                "topic_slug": "demo-topic",
                "run_id": "run-001",
                "origin_refs": [],
                "question": "Does the analytical route stay source-backed and judgment-aware?",
                "assumptions": ["Weak-coupling regime only."],
                "proposed_validation_route": "analytical",
                "intended_l2_targets": ["concept:demo-analytical-concept"],
                "status": "ready_for_validation",
            }
        ],
    )
    write_jsonl(
        kernel_root / "topics" / "demo-topic" / "L3" / "runs" / "run-001" / "strategy_memory.jsonl",
        [
            {
                "strategy_id": "strategy:demo-proof",
                "timestamp": "2026-04-11T09:00:00+08:00",
                "topic_slug": "demo-topic",
                "run_id": "run-001",
                "strategy_type": "verification_guardrail",
                "summary": "Check sign conventions before combining derivation branches.",
                "outcome": "helpful",
                "confidence": 0.81,
                "lane": "formal_theory",
                "reuse_conditions": ["combining derivation branches", "sign conventions"],
                "do_not_apply_when": [],
                "input_context": {},
                "evidence_refs": [],
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
                "summary": "Demo summary for analytical judgment acceptance.",
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
        else Path(tempfile.mkdtemp(prefix="aitp-analytical-judgment-acceptance-")).resolve()
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

    analytical_review_path = Path(analytical_review_payload["paths"]["analytical_review"])
    review_bundle_path = kernel_root / str(status_payload["validation_review_bundle"]["path"])
    review_bundle_note_path = kernel_root / str(status_payload["validation_review_bundle"]["note_path"])
    research_judgment_path = kernel_root / str(status_payload["research_judgment"]["path"])
    research_judgment_note_path = kernel_root / str(status_payload["research_judgment"]["note_path"])
    runtime_protocol_path = Path(verify_payload["runtime_protocol"]["runtime_protocol_path"])
    for path in (
        analytical_review_path,
        review_bundle_path,
        review_bundle_note_path,
        research_judgment_path,
        research_judgment_note_path,
        runtime_protocol_path,
    ):
        ensure_exists(path)

    check(analytical_review_payload["overall_status"] == "ready", "Expected analytical-review to pass.")
    check(
        verify_payload["validation_contract"]["validation_mode"] == "analytical",
        "Expected verify --mode analytical to materialize analytical validation.",
    )
    check(
        status_payload["validation_review_bundle"]["primary_review_kind"] == "analytical_review",
        "Expected analytical review to become the primary review bundle surface.",
    )
    check(
        status_payload["research_judgment"]["status"] == "signals_active",
        "Expected research judgment to report active signals.",
    )
    check(
        status_payload["research_judgment"]["stuckness"]["status"] == "active",
        "Expected a durable stuckness signal in status output.",
    )
    check(
        status_payload["research_judgment"]["surprise"]["status"] == "active",
        "Expected a durable surprise signal in status output.",
    )
    check(
        status_payload["topic_synopsis"]["runtime_focus"]["momentum_status"] == "queued",
        "Expected runtime focus to expose queued momentum for the bounded route.",
    )
    check(
        any(str(row.get("path") or "").endswith("research_judgment.active.md") for row in status_payload["must_read_now"]),
        "Expected the judgment note to become a must-read surface when signals are active.",
    )

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "analytical_review_status": analytical_review_payload["overall_status"],
            "validation_mode": verify_payload["validation_contract"]["validation_mode"],
            "primary_review_kind": status_payload["validation_review_bundle"]["primary_review_kind"],
            "research_judgment_status": status_payload["research_judgment"]["status"],
            "momentum_status": status_payload["topic_synopsis"]["runtime_focus"]["momentum_status"],
            "stuckness_status": status_payload["research_judgment"]["stuckness"]["status"],
            "surprise_status": status_payload["research_judgment"]["surprise"]["status"],
        },
        "artifacts": {
            "analytical_review_path": str(analytical_review_path),
            "validation_review_bundle_path": str(review_bundle_path),
            "validation_review_bundle_note_path": str(review_bundle_note_path),
            "research_judgment_path": str(research_judgment_path),
            "research_judgment_note_path": str(research_judgment_note_path),
            "runtime_protocol_path": str(runtime_protocol_path),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
