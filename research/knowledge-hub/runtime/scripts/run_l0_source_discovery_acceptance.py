#!/usr/bin/env python
"""Isolated acceptance for the bounded Layer 0 discovery -> registration bridge."""

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


def run_discovery_json(
    *,
    package_root: Path,
    kernel_root: Path,
    args: list[str],
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(package_root / "source-layer" / "scripts" / "discover_and_register.py"),
        "--knowledge-root",
        str(kernel_root),
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


def seed_search_results(path: Path) -> None:
    write_json(
        path,
        {
            "provider": "offline-fixture",
            "results": [
                {
                    "arxiv_id": "2401.00002v1",
                    "title": "Unrelated Numerical Note",
                    "summary": "A bounded but irrelevant numerical note for ranking contrast.",
                    "published": "2024-01-04T00:00:00Z",
                    "updated": "2024-01-04T00:00:00Z",
                    "authors": ["Auxiliary Author"],
                    "identifier": "https://arxiv.org/abs/2401.00002v1",
                    "abs_url": "https://arxiv.org/abs/2401.00002v1",
                    "pdf_url": "https://arxiv.org/pdf/2401.00002.pdf",
                    "source_url": "https://arxiv.org/e-print/2401.00002v1",
                    "score": 0.31,
                },
                {
                    "arxiv_id": "2401.00001v2",
                    "title": "Topological Order and Anyon Condensation",
                    "summary": "A discovery candidate directly aligned with topological order, anyon condensation, and operator-algebra source intake.",
                    "published": "2024-01-03T00:00:00Z",
                    "updated": "2024-01-05T00:00:00Z",
                    "authors": ["Primary Author", "Secondary Author"],
                    "identifier": "https://arxiv.org/abs/2401.00001v2",
                    "abs_url": "https://arxiv.org/abs/2401.00001v2",
                    "pdf_url": "https://arxiv.org/pdf/2401.00001.pdf",
                    "source_url": "https://arxiv.org/e-print/2401.00001v2",
                    "score": 0.92,
                },
            ],
        },
    )


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    del repo_root  # Kept for parity with the other acceptance scripts.
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-l0-source-discovery-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    (kernel_root / "topics" / "demo-topic" / "L0").mkdir(parents=True, exist_ok=True)
    (kernel_root / "topics" / "demo-topic" / "L1").mkdir(parents=True, exist_ok=True)

    search_results_path = work_root / "fixtures" / "deepxiv-search-results.json"
    enrichment_json_path = work_root / "fixtures" / "deepxiv-enrichment.json"
    graph_json_path = work_root / "fixtures" / "concept-graph.json"
    seed_search_results(search_results_path)
    write_json(
        enrichment_json_path,
        {
            "paper": {
                "tldr": "A bounded TLDR for topological order and anyon condensation.",
                "keywords": ["topological order", "anyon condensation", "operator algebra"],
                "sections": [
                    {"name": "Introduction", "idx": 0, "tldr": "Intro", "token_count": 180},
                    {"name": "Condensation mechanism", "idx": 1, "tldr": "Mechanism", "token_count": 320},
                ],
                "github_url": "https://github.com/example/topological-order",
            }
        },
    )
    write_json(
        graph_json_path,
        {
            "nodes": [
                {"node_id": "concept:topological-order", "label": "Topological order", "node_type": "concept", "confidence_tier": "EXTRACTED", "confidence_score": 0.95},
                {"node_id": "concept:anyon-condensation", "label": "Anyon condensation", "node_type": "concept", "confidence_tier": "EXTRACTED", "confidence_score": 0.93}
            ],
            "edges": [
                {"edge_id": "edge-topological-order-special-case-anyon-condensation", "from_id": "concept:anyon-condensation", "relation": "special_case_of", "to_id": "concept:topological-order", "evidence_refs": ["topics/demo-topic/L0/sources/paper-topological-order-and-anyon-condensation-2401-00001/source.json"], "notes": "offline fixture"}
            ],
            "hyperedges": [],
            "communities": [
                {"community_id": "community-topological-order", "label": "Topological order cluster", "node_ids": ["concept:topological-order", "concept:anyon-condensation"]}
            ],
            "god_nodes": ["concept:topological-order"]
        },
    )

    payload = run_discovery_json(
        package_root=package_root,
        kernel_root=kernel_root,
        args=[
            "--topic-slug",
            "demo-topic",
            "--query",
            "topological order anyon condensation",
            "--provider",
            "search_results_json",
            "--search-results-json",
            str(search_results_path),
            "--enrichment-json",
            str(enrichment_json_path),
            "--graph-json",
            str(graph_json_path),
            "--json",
            "--registered-by",
            "acceptance-test",
        ],
    )

    discovery_root = Path(payload["discovery_root"])
    query_path = Path(payload["query_path"])
    search_results_json = Path(payload["search_results_path"])
    candidate_evaluation_path = Path(payload["candidate_evaluation_path"])
    registration_receipt_path = Path(payload["registration_receipt_path"])
    enrichment_receipt_path = Path(payload["enrichment_receipt_path"])
    concept_graph_path = Path(payload["concept_graph_path"])
    graph_receipt_path = Path(payload["graph_receipt_path"])
    summary_path = Path(payload["summary_path"])
    layer0_source_json = Path(payload["layer0_source_json"])
    layer0_snapshot = Path(payload["layer0_snapshot"])
    intake_projection_root = Path(payload["intake_projection_root"])
    topic_index_path = kernel_root / "topics" / "demo-topic" / "L0" / "source_index.jsonl"
    global_index_path = kernel_root / "source-layer" / "global_index.jsonl"

    for path in (
        discovery_root,
        query_path,
        search_results_json,
        candidate_evaluation_path,
        registration_receipt_path,
        enrichment_receipt_path,
        concept_graph_path,
        graph_receipt_path,
        summary_path,
        layer0_source_json,
        layer0_snapshot,
        intake_projection_root,
        topic_index_path,
        global_index_path,
    ):
        ensure_exists(path)

    query_payload = json.loads(query_path.read_text(encoding="utf-8"))
    evaluation_payload = json.loads(candidate_evaluation_path.read_text(encoding="utf-8"))
    registration_payload = json.loads(registration_receipt_path.read_text(encoding="utf-8"))
    enrichment_payload = json.loads(enrichment_receipt_path.read_text(encoding="utf-8"))
    graph_payload = json.loads(concept_graph_path.read_text(encoding="utf-8"))
    layer0_payload = json.loads(layer0_source_json.read_text(encoding="utf-8"))
    intake_payload = json.loads((intake_projection_root / "source.json").read_text(encoding="utf-8"))

    check(payload["status"] == "registered", "Expected discovery bridge to report registered status.")
    check(payload["selected_provider"] == "search_results_json", "Expected the offline JSON provider to be selected.")
    check(payload["selected_candidate"]["arxiv_id"] == "2401.00001v2", "Expected the aligned candidate to win evaluation.")
    check(query_payload["status"] == "registered", "Expected query receipt to close as registered.")
    check(any(row["status"] == "viable" for row in evaluation_payload["evaluations"]), "Expected at least one viable candidate.")
    check(registration_payload["status"] == "registered", "Expected registration receipt to be written.")
    check(enrichment_payload["status"] == "enriched", "Expected enrichment receipt to be written.")
    check(payload["graph_build_status"] == "built", "Expected graph build to complete.")
    check(layer0_payload["provenance"]["arxiv_id"] == "2401.00001v2", "Expected Layer 0 source to keep the selected arXiv id.")
    check(layer0_payload["title"] == "Topological Order and Anyon Condensation", "Expected Layer 0 title to come from the selected candidate metadata.")
    check(layer0_payload["provenance"]["deepxiv_tldr"] == "A bounded TLDR for topological order and anyon condensation.", "Expected integrated enrichment to update layer0 provenance.")
    check(layer0_payload["locator"]["concept_graph_path"] == payload["concept_graph_relative_path"], "Expected layer0 locator to include concept_graph_path.")
    check(intake_payload["provenance"]["arxiv_id"] == "2401.00001v2", "Expected intake projection to mirror the registered source.")
    check(intake_payload["provenance"]["deepxiv_keywords"] == ["topological order", "anyon condensation", "operator algebra"], "Expected intake projection to mirror the enrichment keywords.")
    check(intake_payload["locator"]["concept_graph_path"] == payload["concept_graph_relative_path"], "Expected intake projection to mirror concept_graph_path.")
    check(graph_payload["god_nodes"] == ["concept:topological-order"], "Expected integrated concept graph to persist god_nodes.")
    check("search_results_json" in summary_path.read_text(encoding="utf-8"), "Expected summary note to keep the provider chain explicit.")

    result = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "selected_provider": payload["selected_provider"],
            "selected_arxiv_id": payload["selected_candidate"]["arxiv_id"],
            "viable_candidate_count": sum(
                1 for row in evaluation_payload["evaluations"] if row["status"] == "viable"
            ),
            "topic_index_path": str(topic_index_path),
            "global_index_path": str(global_index_path),
            "enrichment_receipt_path": str(enrichment_receipt_path),
            "graph_receipt_path": str(graph_receipt_path),
        },
        "artifacts": {
            "discovery_root": str(discovery_root),
            "query_receipt": str(query_path),
            "search_results": str(search_results_json),
            "candidate_evaluation": str(candidate_evaluation_path),
            "registration_receipt": str(registration_receipt_path),
            "enrichment_receipt": str(enrichment_receipt_path),
            "concept_graph_json": str(concept_graph_path),
            "graph_receipt": str(graph_receipt_path),
            "discovery_summary": str(summary_path),
            "layer0_source_json": str(layer0_source_json),
            "layer0_snapshot": str(layer0_snapshot),
            "intake_projection_root": str(intake_projection_root),
        },
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
