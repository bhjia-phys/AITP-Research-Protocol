#!/usr/bin/env python
"""Isolated acceptance for Obsidian-compatible concept-graph export from the L1 vault."""

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
                "human_request": "Inspect the Obsidian graph export before continuing.",
                "decision_surface": {
                    "selected_action_id": "action:demo-topic:graph-export",
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
                "action_id": "action:demo-topic:graph-export",
                "status": "pending",
                "action_type": "inspect_resume_state",
                "summary": "Inspect the Obsidian graph export before continuing.",
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
    source_slug = "paper-topological-order-and-anyon-condensation-2401-00001"
    source_dir = topic_root / "sources" / source_slug
    source_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        source_dir / "concept_graph.json",
        {
            "kind": "source_concept_graph",
            "graph_version": 1,
            "topic_slug": "demo-topic",
            "source_id": "paper:topological-order-and-anyon-condensation-2401-00001",
            "source_json_path": f"topics/demo-topic/L0/sources/{source_slug}/source.json",
            "generated_at": "2026-04-13T00:00:00+08:00",
            "generated_by": "test",
            "provider": "override_json",
            "nodes": [
                {
                    "node_id": "concept:topological-order",
                    "label": "Topological order",
                    "node_type": "concept",
                    "confidence_tier": "EXTRACTED",
                    "confidence_score": 0.95,
                    "evidence_refs": [],
                    "notes": "",
                },
                {
                    "node_id": "concept:anyon-condensation",
                    "label": "Anyon condensation",
                    "node_type": "concept",
                    "confidence_tier": "EXTRACTED",
                    "confidence_score": 0.93,
                    "evidence_refs": [],
                    "notes": "",
                },
            ],
            "edges": [
                {
                    "edge_id": "edge:topological-order-special-case",
                    "from_id": "concept:anyon-condensation",
                    "relation": "special_case_of",
                    "to_id": "concept:topological-order",
                }
            ],
            "hyperedges": [
                {
                    "hyperedge_id": "hyperedge:condensation-route",
                    "relation": "supports",
                    "node_ids": ["concept:topological-order", "concept:anyon-condensation"],
                }
            ],
            "communities": [
                {
                    "community_id": "community-topological-order",
                    "label": "Topological order cluster",
                    "node_ids": ["concept:topological-order", "concept:anyon-condensation"],
                }
            ],
            "god_nodes": ["concept:topological-order"],
        },
    )
    write_jsonl(
        topic_root / "source_index.jsonl",
        [
            {
                "source_id": "paper:topological-order-and-anyon-condensation-2401-00001",
                "source_type": "paper",
                "title": "Topological Order and Anyon Condensation",
                "summary": "Topological order supports the bounded condensation route.",
                "locator": {
                    "local_path": f"topics/demo-topic/L0/sources/{source_slug}/source.json",
                    "concept_graph_path": f"topics/demo-topic/L0/sources/{source_slug}/concept_graph.json",
                },
                "provenance": {
                    "abs_url": "https://example.org/topological-order",
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
        else Path(tempfile.mkdtemp(prefix="aitp-l1-graph-obsidian-export-acceptance-")).resolve()
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
    index_path = graph_root / "index.md"
    community_index = graph_root / "topological-order-cluster" / "index.md"
    topological_note = graph_root / "topological-order-cluster" / "topological-order.md"
    anyon_note = graph_root / "topological-order-cluster" / "anyon-condensation.md"
    for path in (manifest_path, index_path, community_index, topological_note, anyon_note):
        ensure_exists(path)

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    index_text = index_path.read_text(encoding="utf-8")
    community_text = community_index.read_text(encoding="utf-8")
    topological_text = topological_note.read_text(encoding="utf-8")
    anyon_text = anyon_note.read_text(encoding="utf-8")

    check(manifest_payload["summary"]["node_note_count"] == 2, "Expected two exported node notes.")
    check(manifest_payload["summary"]["community_folder_count"] == 1, "Expected one exported community folder.")
    check(manifest_payload["summary"]["community_page_count"] == 1, "Expected one exported community overview page.")
    check("[[concept-graph/topological-order-cluster/topological-order|Topological order]]" in index_text, "Expected index.md to link to the topological-order note.")
    check("[[concept-graph/topological-order-cluster/anyon-condensation|Anyon condensation]]" in index_text, "Expected index.md to link to the anyon-condensation note.")
    check("[[concept-graph/topological-order-cluster/topological-order|Topological order]]" in community_text, "Expected community index to link to the topological-order note.")
    check("[[concept-graph/topological-order-cluster/anyon-condensation|Anyon condensation]]" in community_text, "Expected community index to link to the anyon-condensation note.")
    check("Topological order supports the bounded condensation route." in topological_text, "Expected node note to include the source summary excerpt.")
    check("https://example.org/topological-order" in anyon_text, "Expected node note to include the source locator.")
    check("This node `special_case_of` [[concept-graph/topological-order-cluster/topological-order|Topological order]]" in anyon_text, "Expected outgoing relation wording to be directional and explicit.")
    check("[[concept-graph/topological-order-cluster/anyon-condensation|Anyon condensation]] `special_case_of` this node" in topological_text, "Expected incoming relation wording to be directional and explicit.")
    check("This node participates in `supports` with [[concept-graph/topological-order-cluster/topological-order|Topological order]]" in anyon_text, "Expected hyperedge wording to be directional and explicit.")
    check(
        "concept-graph/index.md" in json.dumps(((status_payload.get("active_research_contract") or {}).get("l1_vault") or {})),
        "Expected the L1 vault payload to expose the concept-graph index path.",
    )

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "node_note_count": manifest_payload["summary"]["node_note_count"],
            "community_folder_count": manifest_payload["summary"]["community_folder_count"],
        },
        "artifacts": {
            "manifest_json": str(manifest_path),
            "index_note": str(index_path),
            "community_index_note": str(community_index),
            "topological_note": str(topological_note),
            "anyon_note": str(anyon_note),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
