#!/usr/bin/env python
"""Isolated acceptance for mode-aware DeepXiv progressive reading in L1 distillation."""

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
    (runtime_root / "session_start.contract.json").write_text(
        json.dumps({"updated_at": "test-seed"}, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (runtime_root / "interaction_state.json").write_text(
        json.dumps(
            {
                "human_request": "Inspect the verify-mode progressive reading surface before continuing.",
                "decision_surface": {
                    "selected_action_id": "action:demo-topic:progressive",
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
                "action_id": "action:demo-topic:progressive",
                "status": "pending",
                "action_type": "inspect_resume_state",
                "summary": "Inspect the DeepXiv progressive-reading intake before proceeding.",
                "auto_runnable": False,
                "queue_source": "heuristic",
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_root / "runtime_protocol.generated.json").write_text(
        json.dumps(
            {
                "runtime_mode": "verify",
                "active_submode": "literature",
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_root / "runtime_protocol.generated.md").write_text("# Runtime protocol\n", encoding="utf-8")


def seed_demo_source_layer(kernel_root: Path) -> None:
    topic_root = kernel_root / "topics" / "demo-topic" / "L0"
    write_jsonl(
        topic_root / "source_index.jsonl",
        [
            {
                "source_id": "paper:bounded-closure-2401-00004",
                "source_type": "paper",
                "title": "Bounded Closure Route",
                "summary": "Summary fallback should stay deferred because it only mentions strong coupling.",
                "provenance": {
                    "abs_url": "https://example.org/bounded-closure-progressive",
                    "deepxiv_tldr": "This paper studies the bounded closure route.",
                    "deepxiv_sections": [
                        {
                            "name": "Introduction",
                            "idx": 0,
                            "tldr": "The introduction frames the theorem-facing route.",
                            "token_count": 120,
                        },
                        {
                            "name": "Setup",
                            "idx": 1,
                            "tldr": "We assume the closure remains valid in the weak coupling limit.",
                            "token_count": 160,
                        },
                        {
                            "name": "Results",
                            "idx": 4,
                            "tldr": "At zero temperature, the proof closes the first bounded theorem route.",
                            "token_count": 180,
                        },
                    ],
                },
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
        else Path(tempfile.mkdtemp(prefix="aitp-l1-progressive-reading-acceptance-")).resolve()
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
    reading_depth_rows = l1_source_intake.get("reading_depth_rows", [])
    regime_rows = l1_source_intake.get("regime_rows", [])
    method_specificity_rows = l1_source_intake.get("method_specificity_rows", [])

    research_contract_note = kernel_root / "topics" / "demo-topic" / "runtime" / "research_question.contract.md"
    runtime_protocol_note = kernel_root / "topics" / "demo-topic" / "runtime" / "runtime_protocol.generated.md"
    wiki_source_intake_note = kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "source-intake.md"
    for path in (
        research_contract_note,
        runtime_protocol_note,
        wiki_source_intake_note,
    ):
        ensure_exists(path)

    reading_depth_by_source = {
        str(row.get("source_id") or ""): {
            "reading_depth": str(row.get("reading_depth") or ""),
            "basis": str(row.get("basis") or ""),
        }
        for row in reading_depth_rows
    }
    regime_dump = json.dumps(regime_rows, ensure_ascii=True)
    method_dump = json.dumps(method_specificity_rows, ensure_ascii=True)
    check(
        reading_depth_by_source.get("paper:bounded-closure-2401-00004", {}).get("reading_depth") == "skim",
        "Expected verify-mode progressive reading to register as skim depth.",
    )
    check(
        reading_depth_by_source.get("paper:bounded-closure-2401-00004", {}).get("basis") == "deepxiv_sections",
        "Expected verify-mode progressive reading to report the deepxiv_sections basis.",
    )
    check("weak coupling" in regime_dump, "Expected head sections to contribute the weak-coupling regime.")
    check("zero temperature" in regime_dump, "Expected verify-mode relevant sections to contribute zero temperature.")
    check("strong coupling" not in regime_dump, "Expected summary fallback to stay deferred in verify mode.")
    check("formal_derivation" in method_dump, "Expected verify-mode progressive reading to preserve method specificity.")

    research_text = research_contract_note.read_text(encoding="utf-8")
    protocol_text = runtime_protocol_note.read_text(encoding="utf-8")
    wiki_text = wiki_source_intake_note.read_text(encoding="utf-8")
    check("## Reading-depth limits" in research_text, "Expected reading-depth limits section in research_question.contract.md.")
    check("deepxiv_sections" in protocol_text, "Expected runtime protocol note to expose the progressive-reading basis.")
    check("## Reading depth" in wiki_text, "Expected reading depth section in the L1 vault wiki source-intake page.")

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "reading_depths": reading_depth_by_source,
            "regime_row_count": len(regime_rows),
            "method_specificity_row_count": len(method_specificity_rows),
        },
        "artifacts": {
            "research_question_contract_note": str(research_contract_note),
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
