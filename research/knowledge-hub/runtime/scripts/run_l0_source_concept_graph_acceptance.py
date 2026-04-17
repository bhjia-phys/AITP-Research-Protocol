#!/usr/bin/env python
"""Isolated acceptance for the bounded Layer 0 register -> concept-graph bridge."""

from __future__ import annotations

import argparse
import json
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def run_script_json(*, script_path: Path, package_root: Path, args: list[str]) -> dict[str, Any]:
    command = [sys.executable, str(script_path), *args]
    completed = subprocess.run(command, cwd=package_root, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")
    return json.loads(completed.stdout)


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    del repo_root
    work_root = Path(args.work_root).expanduser().resolve() if args.work_root else Path(tempfile.mkdtemp(prefix="aitp-l0-source-concept-graph-acceptance-")).resolve()
    kernel_root = work_root / "kernel"
    (kernel_root / "topics" / "demo-topic" / "L0").mkdir(parents=True, exist_ok=True)
    (kernel_root / "topics" / "demo-topic" / "L1").mkdir(parents=True, exist_ok=True)

    metadata_path = work_root / "fixtures" / "metadata.json"
    enrichment_path = work_root / "fixtures" / "deepxiv-enrichment.json"
    graph_path = work_root / "fixtures" / "concept-graph.json"
    write_json(
        metadata_path,
        {
            "arxiv_id": "2401.00001v2",
            "title": "Topological Order and Anyon Condensation",
            "summary": "A direct match for topological order and anyon condensation discovery.",
            "published": "2024-01-03T00:00:00Z",
            "updated": "2024-01-05T00:00:00Z",
            "authors": ["Primary Author", "Secondary Author"],
            "identifier": "https://arxiv.org/abs/2401.00001v2",
            "abs_url": "https://arxiv.org/abs/2401.00001v2",
            "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
            "source_url": "https://arxiv.org/e-print/2401.00001v2"
        }
    )
    write_json(
        enrichment_path,
        {
            "paper": {
                "tldr": "A bounded TLDR for topological order and anyon condensation.",
                "keywords": ["topological order", "anyon condensation", "operator algebra"],
                "sections": [
                    {"name": "Introduction", "idx": 0, "tldr": "Intro", "token_count": 180},
                    {"name": "Condensation mechanism", "idx": 1, "tldr": "Mechanism", "token_count": 320}
                ]
            }
        }
    )
    write_json(
        graph_path,
        {
            "nodes": [
                {"node_id": "concept:topological-order", "label": "Topological order", "node_type": "concept", "confidence_tier": "EXTRACTED", "confidence_score": 0.95},
                {"node_id": "concept:anyon-condensation", "label": "Anyon condensation", "node_type": "concept", "confidence_tier": "EXTRACTED", "confidence_score": 0.93}
            ],
            "edges": [
                {"edge_id": "edge-topological-order-special-case-anyon-condensation", "from_id": "concept:anyon-condensation", "relation": "special_case_of", "to_id": "concept:topological-order", "evidence_refs": ["topics/demo-topic/L0/sources/paper-topological-order-and-anyon-condensation-2401-00001/source.json"], "notes": "offline fixture"}
            ],
            "hyperedges": [
                {"hyperedge_id": "hyperedge-condensation-route", "relation": "supports", "node_ids": ["concept:topological-order", "concept:anyon-condensation"], "evidence_refs": ["topics/demo-topic/L0/sources/paper-topological-order-and-anyon-condensation-2401-00001/source.json"], "notes": "offline fixture"}
            ],
            "communities": [
                {"community_id": "community-topological-order", "label": "Topological order cluster", "node_ids": ["concept:topological-order", "concept:anyon-condensation"]}
            ],
            "god_nodes": ["concept:topological-order"]
        }
    )

    registration = run_script_json(
        script_path=package_root / "source-layer" / "scripts" / "register_arxiv_source.py",
        package_root=package_root,
        args=[
            "--knowledge-root", str(kernel_root),
            "--topic-slug", "demo-topic",
            "--arxiv-id", "2401.00001v2",
            "--metadata-json", str(metadata_path),
            "--enrichment-json", str(enrichment_path),
            "--graph-json", str(graph_path),
            "--json",
            "--registered-by", "acceptance-test"
        ],
    )

    source_json_path = Path(registration["layer0_source_json"])
    intake_source_json = Path(registration["intake_projection_root"]) / "source.json"
    graph_json_path = Path(registration["concept_graph_path"])
    graph_receipt_path = Path(registration["graph_receipt_path"])
    for path in (source_json_path, intake_source_json, graph_json_path, graph_receipt_path):
        ensure_exists(path)

    source_payload = json.loads(source_json_path.read_text(encoding="utf-8"))
    intake_payload = json.loads(intake_source_json.read_text(encoding="utf-8"))
    graph_payload = json.loads(graph_json_path.read_text(encoding="utf-8"))

    check(registration["graph_build_status"] == "built", "Expected integrated graph build to report built status.")
    check(source_payload["locator"]["concept_graph_path"], "Expected source locator to include concept_graph_path.")
    check(intake_payload["locator"]["concept_graph_path"] == source_payload["locator"]["concept_graph_path"], "Expected intake projection to mirror concept_graph_path.")
    check(graph_payload["god_nodes"] == ["concept:topological-order"], "Expected concept graph payload to keep the god_nodes list.")
    check(graph_payload["edges"][0]["relation"] == "special_case_of", "Expected concept graph to persist the offline edge relation.")

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "source_id": registration["source_id"],
            "graph_build_status": registration["graph_build_status"],
            "node_count": len(graph_payload["nodes"]),
            "edge_count": len(graph_payload["edges"])
        },
        "artifacts": {
            "layer0_source_json": str(source_json_path),
            "intake_source_json": str(intake_source_json),
            "concept_graph_json": str(graph_json_path),
            "graph_receipt": str(graph_receipt_path)
        }
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
