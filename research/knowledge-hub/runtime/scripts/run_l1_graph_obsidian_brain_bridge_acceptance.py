#!/usr/bin/env python
"""Isolated acceptance for explicit concept-graph mirroring into the theoretical-physics brain."""

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
                "human_request": "Mirror the graph export into the external brain.",
                "decision_surface": {
                    "selected_action_id": "action:demo-topic:graph-brain-bridge",
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
                "action_id": "action:demo-topic:graph-brain-bridge",
                "status": "pending",
                "action_type": "inspect_resume_state",
                "summary": "Mirror the graph export into the external brain.",
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
                }
            ],
            "edges": [],
            "hyperedges": [],
            "communities": [
                {
                    "community_id": "community-topological-order",
                    "label": "Topological order cluster",
                    "node_ids": ["concept:topological-order"],
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


def seed_brain_backend_card(kernel_root: Path, brain_root: Path) -> None:
    backends_root = kernel_root / "canonical" / "backends"
    backends_root.mkdir(parents=True, exist_ok=True)
    write_json(
        backends_root / "theoretical-physics-brain.json",
        {
            "backend_id": "backend:theoretical-physics-brain",
            "title": "Theoretical Physics Brain",
            "backend_type": "human_note_library",
            "status": "active",
            "root_paths": [str(brain_root)],
        },
    )
    (backends_root / "backend_index.jsonl").write_text(
        json.dumps(
            {
                "backend_id": "backend:theoretical-physics-brain",
                "title": "Theoretical Physics Brain",
                "backend_type": "human_note_library",
                "status": "active",
                "card_path": "canonical/backends/theoretical-physics-brain.json",
            },
            ensure_ascii=True,
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
        else Path(tempfile.mkdtemp(prefix="aitp-l1-graph-obsidian-brain-bridge-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    brain_root = work_root / "brain"
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    (kernel_root / "intake").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(package_root / "intake" / "L1_VAULT_PROTOCOL.md", kernel_root / "intake" / "L1_VAULT_PROTOCOL.md")
    seed_demo_runtime(kernel_root)
    seed_demo_source_layer(kernel_root)
    seed_brain_backend_card(kernel_root, brain_root)

    status_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", "demo-topic", "--json"],
    )
    del status_payload

    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    from knowledge_hub.aitp_service import AITPService

    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)
    payload = service.sync_l1_graph_export_to_theoretical_physics_brain(
        topic_slug="demo-topic",
        updated_by="brain-bridge-acceptance",
    )

    target_root = brain_root / "90 AITP Imports" / "concept-graphs" / "demo-topic"
    receipt_path = kernel_root / "topics" / "demo-topic" / "L1" / "vault" / "wiki" / "concept-graph" / "theoretical_physics_brain_sync.receipt.json"
    ensure_exists(target_root / "index.md")
    ensure_exists(target_root / "topological-order-cluster" / "topological-order.md")
    ensure_exists(receipt_path)
    check(payload["target_root"] == str(target_root), "Expected bridge payload to report the mirrored target root.")
    check(payload["summary"]["mirrored_file_count"] >= 4, "Expected the bridge to mirror the concept-graph export files.")

    result = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "mirrored_file_count": payload["summary"]["mirrored_file_count"],
        },
        "artifacts": {
            "target_root": str(target_root),
            "receipt_path": str(receipt_path),
        },
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
