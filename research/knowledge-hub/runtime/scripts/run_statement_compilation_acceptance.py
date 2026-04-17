#!/usr/bin/env python
"""Isolated acceptance for the statement-compilation and proof-repair pilot."""

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


def seed_demo_runtime(kernel_root: Path) -> None:
    runtime_root = kernel_root / "topics" / "demo-topic" / "runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    (runtime_root / "topic_state.json").write_text(
        json.dumps(
            {
                "topic_slug": "demo-topic",
                "latest_run_id": "run-001",
                "resume_stage": "L1",
                "research_mode": "formal_derivation",
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_root / "session_start.contract.json").write_text(
        json.dumps({"updated_at": "test-seed"}, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (runtime_root / "interaction_state.json").write_text(
        json.dumps(
            {
                "human_request": "Compile the bounded theorem-facing statement before deeper proof repair.",
                "decision_surface": {
                    "selected_action_id": "action:demo-topic:statement-compilation",
                    "decision_source": "heuristic",
                },
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_root / "action_queue.jsonl").write_text(
        json.dumps(
            {
                "action_id": "action:demo-topic:statement-compilation",
                "status": "pending",
                "action_type": "prepare_lean_bridge",
                "summary": "Compile the theorem-facing statement and inspect the proof-repair plan.",
                "auto_runnable": False,
                "queue_source": "heuristic",
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )


def seed_demo_candidate_and_theory_packets(kernel_root: Path) -> None:
    run_root = kernel_root / "topics" / "demo-topic" / "L3" / "runs" / "run-001"
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "candidate_ledger.jsonl").write_text(
        json.dumps(
            {
                "candidate_id": "candidate:demo-candidate",
                "candidate_type": "theorem_card",
                "title": "Demo theorem packet",
                "summary": "A bounded theorem packet for the statement-compilation pilot.",
                "topic_slug": "demo-topic",
                "run_id": "run-001",
                "origin_refs": [
                    {
                        "id": "paper:demo-source",
                        "layer": "L0",
                        "object_type": "source",
                        "path": "topics/demo-topic/L0/source_index.jsonl",
                        "title": "Demo source",
                        "summary": "Source anchor for theorem packet acceptance.",
                    }
                ],
                "question": "Can the bounded theorem be compiled into a declaration skeleton before proof repair?",
                "assumptions": ["Bounded theorem packet with explicit notation and derivation rows."],
                "proposed_validation_route": "formal-proof",
                "intended_l2_targets": ["theorem:demo-statement-compilation-pilot"],
                "status": "ready_for_validation",
                "supporting_regression_question_ids": ["regression_question:demo-definition"],
                "supporting_oracle_ids": ["question_oracle:demo-definition"],
                "supporting_regression_run_ids": ["regression_run:demo-definition"]
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )

    source_root = kernel_root / "topics" / "demo-topic" / "L0"
    source_root.mkdir(parents=True, exist_ok=True)
    (source_root / "source_index.jsonl").write_text(
        json.dumps(
            {
                "source_id": "paper:demo-source",
                "source_type": "paper",
                "title": "Demo source",
                "summary": "Source-backed theorem-facing route for statement-compilation acceptance.",
                "provenance": {"abs_url": "https://example.org/demo-source"},
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )

    packet_root = kernel_root / "topics" / "demo-topic" / "L4" / "runs" / "run-001" / "theory-packets" / "candidate-demo-candidate"
    packet_root.mkdir(parents=True, exist_ok=True)
    (packet_root / "structure_map.json").write_text(
        json.dumps(
            {
                "status": "captured",
                "sections": [{"section_id": "sec:intro", "status": "present"}],
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (packet_root / "coverage_ledger.json").write_text(
        json.dumps(
            {
                "status": "captured",
                "equation_labels": ["eq:1"],
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (packet_root / "notation_table.json").write_text(
        json.dumps(
            {
                "status": "captured",
                "bindings": [{"symbol": "H", "meaning": "Hamiltonian"}],
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (packet_root / "derivation_graph.json").write_text(
        json.dumps(
            {
                "status": "captured",
                "nodes": [{"id": "def:h"}, {"id": "eq:1"}],
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (packet_root / "regression_gate.json").write_text(
        json.dumps(
            {
                "status": "ready",
                "blocking_reasons": [],
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-statement-compilation-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    seed_demo_runtime(kernel_root)
    seed_demo_candidate_and_theory_packets(kernel_root)

    compilation = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["statement-compilation", "--topic-slug", "demo-topic", "--candidate-id", "candidate:demo-candidate", "--json"],
    )
    lean_bridge = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["lean-bridge", "--topic-slug", "demo-topic", "--candidate-id", "candidate:demo-candidate", "--json"],
    )

    compilation_path = Path(compilation["statement_compilation_path"])
    compilation_note_path = Path(compilation["statement_compilation_note_path"])
    active_payload = json.loads(compilation_path.read_text(encoding="utf-8"))
    packet_path = kernel_root / "topics" / "demo-topic" / "L4" / "runs" / "run-001" / "statement-compilation" / "candidate-demo-candidate" / "statement_compilation.json"
    repair_plan_path = kernel_root / "topics" / "demo-topic" / "L4" / "runs" / "run-001" / "statement-compilation" / "candidate-demo-candidate" / "proof_repair_plan.json"
    lean_packet_path = kernel_root / "topics" / "demo-topic" / "L4" / "runs" / "run-001" / "lean-bridge" / "candidate-demo-candidate" / "lean_ready_packet.json"

    ensure_exists(compilation_path)
    ensure_exists(compilation_note_path)
    ensure_exists(packet_path)
    ensure_exists(repair_plan_path)
    ensure_exists(lean_packet_path)

    packet_payload = json.loads(packet_path.read_text(encoding="utf-8"))
    repair_payload = json.loads(repair_plan_path.read_text(encoding="utf-8"))
    lean_payload = json.loads(lean_packet_path.read_text(encoding="utf-8"))

    check(compilation["status"] == "ready", "Expected statement compilation status to be ready.")
    check(active_payload["packet_count"] == 1, "Expected one active statement-compilation packet.")
    check(packet_payload["primary_statement_kind"] == "theorem", "Expected theorem statement kind for theorem_card.")
    check(any(row.get("assistant") == "lean4" for row in packet_payload["assistant_targets"]), "Expected Lean 4 as one downstream target.")
    check(any(row.get("assistant") == "symbolic_checker" for row in packet_payload["assistant_targets"]), "Expected symbolic_checker as one downstream target.")
    check(repair_payload["status"] == "ready", "Expected proof repair plan to be ready for the bounded captured packet.")
    check(lean_payload["statement_compilation_path"].endswith("statement_compilation.json"), "Expected Lean packet to reference statement compilation.")
    check(lean_payload["proof_repair_plan_path"].endswith("proof_repair_plan.json"), "Expected Lean packet to reference proof repair plan.")

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "statement_compilation_status": compilation["status"],
            "statement_packet_count": active_payload["packet_count"],
            "assistant_targets": [row["assistant"] for row in packet_payload["assistant_targets"]],
            "proof_hole_count": packet_payload["proof_hole_count"],
            "lean_bridge_status": lean_bridge["status"],
        },
        "artifacts": {
            "statement_compilation_active": str(compilation_path),
            "statement_compilation_note": str(compilation_note_path),
            "statement_packet": str(packet_path),
            "proof_repair_plan": str(repair_plan_path),
            "lean_ready_packet": str(lean_packet_path),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
