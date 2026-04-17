#!/usr/bin/env python
"""Isolated acceptance for the bounded Layer 0 source catalog surface."""

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


def seed_demo_source_layer(kernel_root: Path) -> None:
    write_jsonl(
        kernel_root / "topics" / "demo-topic" / "L0" / "source_index.jsonl",
        [
            {
                "source_id": "paper:shared-a",
                "source_type": "paper",
                "title": "Shared paper",
                "summary": "Shared source summary.",
                "canonical_source_id": "source_identity:doi:10-1000-shared-paper",
                "references": ["doi:10-1000-neighbor-paper"],
                "provenance": {"abs_url": "https://example.org/demo"},
            }
        ],
    )
    write_jsonl(
        kernel_root / "topics" / "sibling-topic" / "L0" / "source_index.jsonl",
        [
            {
                "source_id": "paper:shared-b",
                "source_type": "paper",
                "title": "Shared paper mirror",
                "summary": "Same source reused in another topic.",
                "canonical_source_id": "source_identity:doi:10-1000-shared-paper",
                "references": [],
                "provenance": {"abs_url": "https://example.org/sibling"},
            }
        ],
    )
    write_jsonl(
        kernel_root / "topics" / "neighbor-topic" / "L0" / "source_index.jsonl",
        [
            {
                "source_id": "paper:neighbor",
                "source_type": "paper",
                "title": "Neighbor paper",
                "summary": "Neighbor source summary.",
                "canonical_source_id": "source_identity:doi:10-1000-neighbor-paper",
                "references": ["doi:10-1000-shared-paper"],
                "provenance": {"abs_url": "https://example.org/neighbor"},
            }
        ],
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
                "human_request": "Inspect source reuse and source fidelity.",
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
                "summary": "Inspect source catalog and fidelity surfaces.",
                "auto_runnable": False,
                "queue_source": "heuristic",
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )


def write_demo_bibtex(kernel_root: Path) -> Path:
    bib_path = kernel_root / "imports" / "demo-import.bib"
    bib_path.parent.mkdir(parents=True, exist_ok=True)
    bib_path.write_text(
        "\n".join(
            [
                "@article{new-paper,",
                "  title = {New imported paper},",
                "  author = {Chen Ning Yang and Emmy Noether},",
                "  year = {1942},",
                "  doi = {10.1000/new-imported-paper},",
                "  url = {https://doi.org/10.1000/new-imported-paper},",
                "  abstract = {Imported from BibTeX.}",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return bib_path


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-source-catalog-acceptance-")).resolve()
    )
    kernel_root = work_root / "kernel"
    shutil.copytree(package_root / "schemas", kernel_root / "schemas", dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "schemas", kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    seed_demo_source_layer(kernel_root)
    seed_demo_runtime(kernel_root)
    bib_path = write_demo_bibtex(kernel_root)

    catalog_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["compile-source-catalog", "--json"],
    )
    trace_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["trace-source-citations", "--canonical-source-id", "source_identity:doi:10-1000-shared-paper", "--json"],
    )
    family_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["compile-source-family", "--source-type", "paper", "--json"],
    )
    export_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "export-source-bibtex",
            "--canonical-source-id",
            "source_identity:doi:10-1000-shared-paper",
            "--include-neighbors",
            "--json",
        ],
    )
    import_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=[
            "import-bibtex-sources",
            "--topic-slug",
            "demo-topic",
            "--bibtex-path",
            str(bib_path),
            "--json",
        ],
    )
    status_payload = run_cli_json(
        package_root=package_root,
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", "demo-topic", "--json"],
    )

    catalog_json = Path(catalog_payload["json_path"])
    catalog_md = Path(catalog_payload["markdown_path"])
    trace_json = Path(trace_payload["json_path"])
    trace_md = Path(trace_payload["markdown_path"])
    family_json = Path(family_payload["json_path"])
    family_md = Path(family_payload["markdown_path"])
    export_json = Path(export_payload["json_path"])
    export_md = Path(export_payload["markdown_path"])
    export_bib = Path(export_payload["bibtex_path"])
    import_json = Path(import_payload["json_path"])
    import_md = Path(import_payload["markdown_path"])
    imported_source_index = Path(import_payload["source_index_path"])
    for path in (
        catalog_json,
        catalog_md,
        trace_json,
        trace_md,
        family_json,
        family_md,
        export_json,
        export_md,
        export_bib,
        import_json,
        import_md,
        imported_source_index,
    ):
        ensure_exists(path)

    check(catalog_payload["payload"]["summary"]["multi_topic_source_count"] == 1, "Expected one cross-topic reused source.")
    check(trace_payload["payload"]["summary"]["outgoing_link_count"] == 1, "Expected one outgoing citation link.")
    check(trace_payload["payload"]["summary"]["incoming_link_count"] == 1, "Expected one incoming citation link.")
    check(family_payload["payload"]["summary"]["multi_topic_source_count"] == 1, "Expected one multi-topic paper source.")
    check(export_payload["payload"]["summary"]["entry_count"] == 2, "Expected BibTeX export to include seed plus one neighbor.")
    check(import_payload["payload"]["summary"]["imported_entry_count"] == 1, "Expected one imported BibTeX source row.")
    check(
        status_payload["source_intelligence"]["fidelity_summary"]["strongest_tier"] == "peer_reviewed",
        "Expected peer-reviewed fidelity to appear in runtime status.",
    )

    payload = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "catalog_multi_topic_source_count": catalog_payload["payload"]["summary"]["multi_topic_source_count"],
            "trace_outgoing_link_count": trace_payload["payload"]["summary"]["outgoing_link_count"],
            "trace_incoming_link_count": trace_payload["payload"]["summary"]["incoming_link_count"],
            "family_multi_topic_source_count": family_payload["payload"]["summary"]["multi_topic_source_count"],
            "bibtex_export_entry_count": export_payload["payload"]["summary"]["entry_count"],
            "bibtex_imported_entry_count": import_payload["payload"]["summary"]["imported_entry_count"],
            "status_strongest_fidelity": status_payload["source_intelligence"]["fidelity_summary"]["strongest_tier"],
        },
        "artifacts": {
            "catalog_json": str(catalog_json),
            "catalog_markdown": str(catalog_md),
            "trace_json": str(trace_json),
            "trace_markdown": str(trace_md),
            "family_json": str(family_json),
            "family_markdown": str(family_md),
            "bibtex_export_json": str(export_json),
            "bibtex_export_markdown": str(export_md),
            "bibtex_export_bib": str(export_bib),
            "bibtex_import_json": str(import_json),
            "bibtex_import_markdown": str(import_md),
            "imported_source_index": str(imported_source_index),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
