#!/usr/bin/env python
"""Isolated acceptance for multi-community node navigation in the Obsidian graph export."""

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
    completed = subprocess.run(command, cwd=package_root, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")
    return json.loads(completed.stdout)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n", encoding="utf-8")


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
                "human_request": "Inspect the multi-community graph export before continuing.",
                "decision_surface": {
                    "selected_action_id": "action:demo-topic:graph-export-multi",
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
                "action_id": "action:demo-topic:graph-export-multi",
                "status": "pending",
                "action_type": "inspect_resume_state",
                "summary": "Inspect the multi-community graph export before continuing.",
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
    source_slug = "paper-multi-community-2401-00002"
    source_dir = topic_root / "sources" / source_slug
    source_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        source_dir / "concept_graph.json",
        {
            "kind": "source_concept_graph",
            "graph_version": 1,
            "topic_slug": "demo-topic",
            "source_id": "paper:multi-community-2401-00002",
            "source_json_path": f"topics/demo-topic/L0/sources/{source_slug}/source.json",
            "generated_at": "2026-04-13T00:00:00+08:00",
            "generated_by": "test",
            "provider": "override_json",
            "nodes": [
                {
                    "node_id": "concept:modular-tensor-category",
                    "label": "Modular tensor category",
                    "node_type": "concept",
                    "confidence_tier": "EXTRACTED",
                    "confidence_score": 0.95,
                    "evidence_refs": [],
                    "notes": "",
                }
            ],
            "edges": [],
            "hyperedges": [],
            "communities": [
                {
                    "community_id": "community-category-theory",
                    "label": "Category theory cluster",
                    "node_ids": ["concept:modular-tensor-category"],
                },
                {
                    "community_id": "community-topological-order",
                    "label": "Topological order cluster",
                    "node_ids": ["concept:modular-tensor-category"],
                },
            ],
            "god_nodes": [],
        },
    )
    write_jsonl(
        topic_root / "source_index.jsonl",
        [
            {
                "source_id": "paper:multi-community-2401-00002",
                "source_type": "paper",
                "title": "Multi-community paper",
                "summary": "A node that lives in two graph communities.",
                "locator": {
                    "local_path": f"topics/demo-topic/L0/sources/{source_slug}/source.json",
                    "concept_graph_path": f"topics/demo-topic/L0/sources/{source_slug}/concept_graph.json",
                },
                "provenance": {
                    "abs_url": "https://example.org/multi-community",
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
        else Path(tempfile.mkdtemp(prefix="aitp-l1-graph-obsidian-multicommunity-acceptance-")).resolve()
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

    graph_root = kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "concept-graph"
    manifest_path = graph_root / "manifest.json"
    category_index = graph_root / "category-theory-cluster" / "index.md"
    topological_index = graph_root / "topological-order-cluster" / "index.md"
    primary_note = graph_root / "category-theory-cluster" / "modular-tensor-category.md"
    for path in (manifest_path, category_index, topological_index, primary_note):
        ensure_exists(path)

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    category_text = category_index.read_text(encoding="utf-8")
    topological_text = topological_index.read_text(encoding="utf-8")
    primary_text = primary_note.read_text(encoding="utf-8")

    check(manifest_payload["summary"]["node_note_count"] == 1, "Expected one exported node note.")
    check(manifest_payload["summary"]["community_folder_count"] == 2, "Expected two community folders for the shared node.")
    check(manifest_payload["summary"]["community_page_count"] == 2, "Expected two community overview pages for the shared node.")
    check("[[concept-graph/category-theory-cluster/modular-tensor-category|Modular tensor category]]" in category_text, "Expected the primary community index to link to the shared note.")
    check("[[concept-graph/category-theory-cluster/modular-tensor-category|Modular tensor category]]" in topological_text, "Expected the secondary community index to link to the same shared note.")
    check("Communities: `Category theory cluster, Topological order cluster`" in primary_text, "Expected the shared note to list both community memberships.")
    check(
        "category-theory-cluster/index.md" in json.dumps(((status_payload.get("active_research_contract") or {}).get("l1_vault") or {})),
        "Expected the L1 vault payload to expose the primary community overview path.",
    )
    check(
        "topological-order-cluster/index.md" in json.dumps(((status_payload.get("active_research_contract") or {}).get("l1_vault") or {})),
        "Expected the L1 vault payload to expose the secondary community overview path.",
    )

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "node_note_count": manifest_payload["summary"]["node_note_count"],
            "community_folder_count": manifest_payload["summary"]["community_folder_count"],
            "community_page_count": manifest_payload["summary"]["community_page_count"],
        },
        "artifacts": {
            "manifest_json": str(manifest_path),
            "category_index_note": str(category_index),
            "topological_index_note": str(topological_index),
            "primary_note": str(primary_note),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
