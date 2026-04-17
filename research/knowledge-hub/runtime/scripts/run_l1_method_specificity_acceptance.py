#!/usr/bin/env python
"""Isolated acceptance for the bounded L1 method-specificity surface."""

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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n",
        encoding="utf-8",
    )


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
    (runtime_root / "interaction_state.json").write_text(
        json.dumps(
            {
                "human_request": "Inspect the method-specificity surface before continuing.",
                "decision_surface": {
                    "selected_action_id": "action:demo-topic:read",
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
                "action_id": "action:demo-topic:read",
                "status": "pending",
                "action_type": "inspect_resume_state",
                "summary": "Inspect the source-backed method specificity before proceeding.",
                "auto_runnable": False,
                "queue_source": "heuristic",
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )


def seed_demo_source_layer(kernel_root: Path) -> None:
    topic_root = kernel_root / "topics" / "demo-topic" / "L0"
    write_jsonl(
        topic_root / "source_index.jsonl",
        [
            {
                "source_id": "thesis:formal-route",
                "source_type": "thesis",
                "title": "Bounded closure derivation",
                "summary": (
                    "We derive a bounded closure theorem in the weak coupling limit and "
                    "state the first proof obligation explicitly."
                ),
                "provenance": {
                    "absolute_path": str(kernel_root / "inputs" / "bounded-closure.tex"),
                },
            },
            {
                "source_id": "paper:benchmark-route",
                "source_type": "paper",
                "title": "Exact benchmark workflow",
                "summary": (
                    "We benchmark the route with exact diagonalization and a small-system "
                    "numerical simulation before broader extrapolation."
                ),
                "provenance": {
                    "abs_url": "https://example.org/benchmark",
                },
            },
        ],
    )
    snapshot_root = topic_root / "sources" / "thesis-formal-route"
    snapshot_root.mkdir(parents=True, exist_ok=True)
    (snapshot_root / "snapshot.md").write_text(
        "# Snapshot\n\n"
        "## Preview\n"
        "We derive a bounded closure theorem in the weak coupling limit and state the first proof obligation explicitly.\n",
        encoding="utf-8",
    )


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-l1-method-specificity-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    seed_demo_runtime(kernel_root)
    seed_demo_source_layer(kernel_root)

    status_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", "demo-topic", "--json"],
    )

    method_rows = (
        (status_payload.get("active_research_contract") or {})
        .get("l1_source_intake", {})
        .get("method_specificity_rows", [])
    )
    research_contract_note = kernel_root / "topics" / "demo-topic" / "runtime" / "research_question.contract.md"
    runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"])
    ensure_exists(research_contract_note)
    ensure_exists(runtime_protocol_note)

    check(len(method_rows) == 2, "Expected two method-specificity rows.")
    families = {row.get("method_family") for row in method_rows}
    check("formal_derivation" in families, "Expected formal_derivation method family.")
    check("numerical_benchmark" in families, "Expected numerical_benchmark method family.")
    check(
        any(row.get("specificity_tier") == "high" for row in method_rows),
        "Expected at least one high-specificity row.",
    )
    check(
        "## Method specificity" in research_contract_note.read_text(encoding="utf-8"),
        "Expected method-specificity section in research_question.contract.md.",
    )
    check(
        "## Method specificity" in runtime_protocol_note.read_text(encoding="utf-8"),
        "Expected method-specificity section in runtime protocol note.",
    )

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "method_specificity_row_count": len(method_rows),
            "method_families": sorted(families),
            "high_specificity_count": sum(1 for row in method_rows if row.get("specificity_tier") == "high"),
        },
        "artifacts": {
            "research_question_contract_note": str(research_contract_note),
            "runtime_protocol_note": str(runtime_protocol_note),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
