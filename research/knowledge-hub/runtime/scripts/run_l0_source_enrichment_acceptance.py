#!/usr/bin/env python
"""Isolated acceptance for the bounded Layer 0 registration -> enrichment bridge."""

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


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    del repo_root
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-l0-source-enrichment-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    (kernel_root / "topics" / "demo-topic" / "L0").mkdir(parents=True, exist_ok=True)
    (kernel_root / "topics" / "demo-topic" / "L1").mkdir(parents=True, exist_ok=True)

    metadata_path = work_root / "fixtures" / "metadata.json"
    enrichment_path = work_root / "fixtures" / "deepxiv-enrichment.json"
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
            "source_url": "https://arxiv.org/e-print/2401.00001v2",
        },
    )
    write_json(
        enrichment_path,
        {
            "paper": {
                "tldr": "A bounded TLDR for topological order and anyon condensation.",
                "keywords": ["topological order", "anyon condensation", "operator algebra"],
                "github_url": "https://github.com/example/topological-order",
                "sections": [
                    {
                        "name": "Introduction",
                        "idx": 0,
                        "tldr": "Introduces the route.",
                        "token_count": 180,
                    },
                    {
                        "name": "Condensation mechanism",
                        "idx": 1,
                        "tldr": "Defines the condensation mechanism.",
                        "token_count": 320,
                    },
                ],
            }
        },
    )

    registration = run_script_json(
        script_path=package_root / "source-layer" / "scripts" / "register_arxiv_source.py",
        package_root=package_root,
        args=[
            "--knowledge-root",
            str(kernel_root),
            "--topic-slug",
            "demo-topic",
            "--arxiv-id",
            "2401.00001v2",
            "--metadata-json",
            str(metadata_path),
            "--json",
            "--registered-by",
            "acceptance-test",
        ],
    )
    enrichment = run_script_json(
        script_path=package_root / "source-layer" / "scripts" / "enrich_with_deepxiv.py",
        package_root=package_root,
        args=[
            "--knowledge-root",
            str(kernel_root),
            "--topic-slug",
            "demo-topic",
            "--source-id",
            registration["source_id"],
            "--enrichment-json",
            str(enrichment_path),
            "--json",
            "--enriched-by",
            "acceptance-test",
        ],
    )

    source_json_path = Path(registration["layer0_source_json"])
    source_payload = json.loads(source_json_path.read_text(encoding="utf-8"))
    intake_source_json = Path(registration["intake_projection_root"]) / "source.json"
    intake_payload = json.loads(intake_source_json.read_text(encoding="utf-8"))
    receipt_path = Path(enrichment["receipt_path"])

    for path in (source_json_path, intake_source_json, receipt_path):
        ensure_exists(path)

    check(enrichment["status"] == "enriched", "Expected enrichment script to report enriched status.")
    check(
        source_payload["provenance"]["deepxiv_tldr"] == "A bounded TLDR for topological order and anyon condensation.",
        "Expected layer0 source provenance to include deepxiv_tldr.",
    )
    check(
        intake_payload["provenance"]["deepxiv_keywords"] == ["topological order", "anyon condensation", "operator algebra"],
        "Expected intake projection to mirror deepxiv keywords.",
    )
    check(
        source_payload["provenance"]["deepxiv_sections"][1]["name"] == "Condensation mechanism",
        "Expected enriched section structure to persist to layer0 provenance.",
    )
    check(
        source_payload["provenance"]["deepxiv_github_url"] == "https://github.com/example/topological-order",
        "Expected provenance to keep the DeepXiv-style github URL.",
    )

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "source_id": registration["source_id"],
            "deepxiv_provider": source_payload["provenance"]["deepxiv_provider"],
            "section_count": len(source_payload["provenance"]["deepxiv_sections"]),
        },
        "artifacts": {
            "layer0_source_json": str(source_json_path),
            "intake_source_json": str(intake_source_json),
            "enrichment_receipt": str(receipt_path),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
