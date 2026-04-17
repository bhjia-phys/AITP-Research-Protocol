#!/usr/bin/env python
"""Isolated acceptance for the bounded L1 assumption and reading-depth surface."""

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
                "human_request": "Inspect the source-backed assumptions and reading-depth limits before continuing.",
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
                "summary": "Inspect the source-backed assumptions, reading depth, and conflict surface before proceeding.",
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
                "source_id": "thesis:weak-coupling-note",
                "source_type": "thesis",
                "title": "Weak-coupling derivation note",
                "summary": (
                    "We derive a bounded closure relation and track the first proof obligation."
                ),
                "provenance": {
                    "absolute_path": str(kernel_root / "inputs" / "weak-coupling-note.tex"),
                },
            },
            {
                "source_id": "paper:strong-coupling-abstract",
                "source_type": "paper",
                "title": "Strong-coupling abstract",
                "summary": (
                    "Under the assumption that strong coupling remains dominant at finite temperature, "
                    "we benchmark the route before wider interpretation."
                ),
                "provenance": {
                    "abs_url": "https://example.org/strong-coupling-abstract",
                },
            },
        ],
    )
    snapshot_root = topic_root / "sources" / "thesis-weak-coupling-note"
    snapshot_root.mkdir(parents=True, exist_ok=True)
    (snapshot_root / "snapshot.md").write_text(
        "# Snapshot\n\n"
        "## Preview\n"
        "We assume weak coupling and zero temperature while deriving the bounded closure relation.\n",
        encoding="utf-8",
    )


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-l1-assumption-depth-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    (kernel_root / "intake").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(package_root / "intake" / "L1_VAULT_PROTOCOL.md", kernel_root / "intake" / "L1_VAULT_PROTOCOL.md")
    seed_demo_runtime(kernel_root)
    seed_demo_source_layer(kernel_root)

    status_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", "demo-topic", "--json"],
    )

    l1_source_intake = (
        (status_payload.get("active_research_contract") or {})
        .get("l1_source_intake", {})
    )
    assumption_rows = l1_source_intake.get("assumption_rows", [])
    reading_depth_rows = l1_source_intake.get("reading_depth_rows", [])
    contradiction_candidates = l1_source_intake.get("contradiction_candidates", [])

    research_contract_note = kernel_root / "topics" / "demo-topic" / "runtime" / "research_question.contract.md"
    topic_dashboard_note = kernel_root / "topics" / "demo-topic" / "runtime" / "topic_dashboard.md"
    runtime_protocol_note = Path(status_payload["runtime_protocol_note_path"])
    wiki_source_intake_note = kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "source-intake.md"
    for path in (
        research_contract_note,
        topic_dashboard_note,
        runtime_protocol_note,
        wiki_source_intake_note,
    ):
        ensure_exists(path)

    reading_depth_by_source = {
        str(row.get("source_id") or ""): str(row.get("reading_depth") or "")
        for row in reading_depth_rows
    }
    check(len(assumption_rows) >= 2, "Expected at least two source-backed assumption rows.")
    check(
        reading_depth_by_source.get("thesis:weak-coupling-note") == "full_read",
        "Expected the snapshot-backed thesis source to register as full_read.",
    )
    check(
        reading_depth_by_source.get("paper:strong-coupling-abstract") == "abstract_only",
        "Expected the metadata-only paper source to register as abstract_only.",
    )
    check(contradiction_candidates, "Expected at least one contradiction candidate.")
    first_contradiction = contradiction_candidates[0]
    check(
        str(first_contradiction.get("comparison_basis") or "") == "regime_rows",
        "Expected contradiction rows to expose the comparison basis.",
    )
    check(
        str(first_contradiction.get("source_basis_type") or "") == "regime",
        "Expected contradiction rows to expose the source-side basis type.",
    )
    check(
        str(first_contradiction.get("against_basis_type") or "") == "regime",
        "Expected contradiction rows to expose the compared-side basis type.",
    )
    check(
        "strong coupling" in str(first_contradiction.get("source_basis_summary") or ""),
        "Expected contradiction rows to keep the source-side basis summary explicit.",
    )
    check(
        "weak coupling" in str(first_contradiction.get("against_basis_summary") or ""),
        "Expected contradiction rows to keep the compared-side basis summary explicit.",
    )

    research_text = research_contract_note.read_text(encoding="utf-8")
    dashboard_text = topic_dashboard_note.read_text(encoding="utf-8")
    protocol_text = runtime_protocol_note.read_text(encoding="utf-8")
    wiki_text = wiki_source_intake_note.read_text(encoding="utf-8")

    check("## Source-backed assumptions" in research_text, "Expected assumptions section in research_question.contract.md.")
    check("## Reading-depth limits" in research_text, "Expected reading-depth limits section in research_question.contract.md.")
    check("## Contradiction candidates" in research_text, "Expected contradiction section in research_question.contract.md.")
    check("## L1 intake honesty" in dashboard_text, "Expected dashboard to expose the L1 intake honesty section.")
    check("### Reading-depth limits" in dashboard_text, "Expected dashboard to keep reading-depth limits explicit.")
    check("### Contradiction candidates" in dashboard_text, "Expected dashboard to keep contradiction candidates explicit.")
    check("## Source-backed assumptions" in protocol_text, "Expected assumptions section in runtime protocol note.")
    check("## Reading-depth limits" in protocol_text, "Expected reading-depth limits section in runtime protocol note.")
    check("## Contradiction candidates" in protocol_text, "Expected contradiction section in runtime protocol note.")
    check("## Assumptions" in wiki_text, "Expected assumptions section in L1 vault wiki source-intake page.")
    check("## Reading depth" in wiki_text, "Expected reading-depth section in L1 vault wiki source-intake page.")

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "assumption_row_count": len(assumption_rows),
            "reading_depths": reading_depth_by_source,
            "contradiction_candidate_count": len(contradiction_candidates),
        },
        "artifacts": {
            "research_question_contract_note": str(research_contract_note),
            "topic_dashboard_note": str(topic_dashboard_note),
            "runtime_protocol_note": str(runtime_protocol_note),
            "wiki_source_intake_note": str(wiki_source_intake_note),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
