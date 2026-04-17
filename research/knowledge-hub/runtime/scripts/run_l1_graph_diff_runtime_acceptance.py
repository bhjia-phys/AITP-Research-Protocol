#!/usr/bin/env python
"""Isolated acceptance for cross-iteration graph diff runtime surfacing."""

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


def seed_runtime(runtime_root: Path) -> None:
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
                "human_request": "Inspect the graph-analysis runtime surface.",
                "decision_surface": {
                    "selected_action_id": "action:demo-topic:graph-analysis",
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
                "action_id": "action:demo-topic:graph-analysis",
                "status": "pending",
                "action_type": "inspect_resume_state",
                "summary": "Inspect the graph-analysis summary before proceeding.",
                "auto_runnable": False,
                "queue_source": "heuristic",
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )


def write_source_index(source_root: Path, *, paper_graph_path: str, note_graph_path: str | None) -> None:
    rows = [
        json.dumps(
            {
                "source_id": "paper:anyon-condensation-2401-00005",
                "source_type": "paper",
                "title": "Anyon condensation paper",
                "summary": "Anyon condensation summary.",
                "locator": {
                    "concept_graph_path": paper_graph_path,
                },
                "provenance": {
                    "abs_url": "https://example.org/anyon-condensation",
                },
            },
            ensure_ascii=True,
        ),
        json.dumps(
            {
                "source_id": "note:operator-algebra",
                "source_type": "local_note",
                "title": "Operator algebra note",
                "summary": "Operator algebra note summary.",
                "locator": (
                    {"concept_graph_path": note_graph_path}
                    if note_graph_path
                    else {}
                ),
                "provenance": {
                    "deepxiv_tldr": "Operator algebra route summary.",
                },
            },
            ensure_ascii=True,
        ),
    ]
    (source_root / "source_index.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_concept_graph(path: Path, *, source_id: str, source_json_path: str, label: str, node_id: str, generated_at: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "kind": "source_concept_graph",
                "graph_version": 1,
                "topic_slug": "demo-topic",
                "source_id": source_id,
                "source_json_path": source_json_path,
                "generated_at": generated_at,
                "generated_by": "acceptance-test",
                "provider": "override_json",
                "nodes": [
                    {
                        "node_id": node_id,
                        "label": label,
                        "node_type": "concept",
                        "confidence_tier": "EXTRACTED",
                        "confidence_score": 0.95,
                        "evidence_refs": [],
                        "notes": "",
                    }
                ],
                "edges": [],
                "hyperedges": [],
                "communities": [],
                "god_nodes": [node_id],
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
        else Path(tempfile.mkdtemp(prefix="aitp-l1-graph-diff-runtime-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "canonical", kernel_root / "canonical", dirs_exist_ok=True)
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    (kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki").mkdir(parents=True, exist_ok=True)
    (kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "source-intake.md").write_text(
        "# Source Intake\n\nGraph diff runtime acceptance.\n",
        encoding="utf-8",
    )
    runtime_root = kernel_root / "topics" / "demo-topic" / "runtime"
    seed_runtime(runtime_root)

    source_root = kernel_root / "topics" / "demo-topic" / "L0"
    paper_source_slug = "paper-anyon-condensation-2401-00005"
    note_source_slug = "note-operator-algebra"
    paper_graph_path = source_root / "sources" / paper_source_slug / "concept_graph.json"
    note_graph_path = source_root / "sources" / note_source_slug / "concept_graph.json"
    write_concept_graph(
        paper_graph_path,
        source_id="paper:anyon-condensation-2401-00005",
        source_json_path=f"topics/demo-topic/L0/sources/{paper_source_slug}/source.json",
        label="Topological order",
        node_id="concept:topological-order",
        generated_at="2026-04-13T00:00:00+08:00",
    )
    write_source_index(
        source_root,
        paper_graph_path=f"topics/demo-topic/L0/sources/{paper_source_slug}/concept_graph.json",
        note_graph_path=None,
    )

    first_status = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", "demo-topic", "--json"],
    )
    check(first_status["graph_analysis"]["summary"]["connection_count"] == 0, "Expected first graph-analysis pass to have zero cross-source connections.")

    write_concept_graph(
        paper_graph_path,
        source_id="paper:anyon-condensation-2401-00005",
        source_json_path=f"topics/demo-topic/L0/sources/{paper_source_slug}/source.json",
        label="Anyon condensation",
        node_id="concept:anyon-condensation",
        generated_at="2026-04-14T00:00:00+08:00",
    )
    write_concept_graph(
        note_graph_path,
        source_id="note:operator-algebra",
        source_json_path=f"topics/demo-topic/L0/sources/{note_source_slug}/source.json",
        label="Anyon condensation",
        node_id="concept:anyon-condensation-operator",
        generated_at="2026-04-14T00:00:00+08:00",
    )
    write_source_index(
        source_root,
        paper_graph_path=f"topics/demo-topic/L0/sources/{paper_source_slug}/concept_graph.json",
        note_graph_path=f"topics/demo-topic/L0/sources/{note_source_slug}/concept_graph.json",
    )

    second_status = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", "demo-topic", "--json"],
    )

    graph_analysis = second_status["graph_analysis"]
    graph_analysis_json = kernel_root / "topics" / "demo-topic" / "runtime" / "graph_analysis.json"
    graph_analysis_note = kernel_root / "topics" / "demo-topic" / "runtime" / "graph_analysis.md"
    graph_analysis_history = kernel_root / "topics" / "demo-topic" / "runtime" / "graph_analysis_history.jsonl"
    for path in (graph_analysis_json, graph_analysis_note, graph_analysis_history):
        ensure_exists(path)

    check(graph_analysis["summary"]["connection_count"] == 1, "Expected second graph-analysis pass to detect one cross-source connection.")
    check(graph_analysis["summary"]["history_length"] == 2, "Expected graph-analysis history length to increment across passes.")
    check(graph_analysis["diff"]["added"]["node_count"] == 2, "Expected second graph-analysis pass to record two added nodes.")
    check(graph_analysis["diff"]["removed"]["node_count"] == 1, "Expected second graph-analysis pass to record one removed node.")
    check(
        "Anyon condensation" in graph_analysis_note.read_text(encoding="utf-8"),
        "Expected graph_analysis.md to render the updated bridge label.",
    )
    check(
        len([line for line in graph_analysis_history.read_text(encoding="utf-8").splitlines() if line.strip()]) == 2,
        "Expected graph_analysis_history.jsonl to keep two materialization rows.",
    )

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "connection_count": graph_analysis["summary"]["connection_count"],
            "history_length": graph_analysis["summary"]["history_length"],
            "added_node_count": graph_analysis["diff"]["added"]["node_count"],
            "removed_node_count": graph_analysis["diff"]["removed"]["node_count"],
        },
        "artifacts": {
            "graph_analysis_json": str(graph_analysis_json),
            "graph_analysis_note": str(graph_analysis_note),
            "graph_analysis_history": str(graph_analysis_history),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
