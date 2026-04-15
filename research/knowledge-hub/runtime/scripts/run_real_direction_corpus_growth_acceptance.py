#!/usr/bin/env python
"""Acceptance for the real-direction L2 corpus growth baseline."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
KERNEL_ROOT = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]
TOPIC_SLUG = "measurement-induced-algebraic-transition-and-observer-algebras"

if str(KERNEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KERNEL_ROOT))

from knowledge_hub.aitp_service import AITPService  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--updated-by", default="real-direction-corpus-growth-acceptance")
    parser.add_argument("--json", action="store_true")
    return parser


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _rewrite_source_path(value: str, slug_map: dict[str, str]) -> str:
    rendered = str(value or "")
    for old_slug, new_slug in slug_map.items():
        rendered = rendered.replace(f"/sources/{old_slug}/", f"/sources/{new_slug}/")
        rendered = rendered.replace(f"\\sources\\{old_slug}\\", f"\\sources\\{new_slug}\\")
    return rendered


def _copy_shortened_topic_sources(package_root: Path, kernel_root: Path) -> dict[str, str]:
    source_index_path = package_root / "source-layer" / "topics" / TOPIC_SLUG / "source_index.jsonl"
    copied_sources_root = kernel_root / "source-layer" / "topics" / TOPIC_SLUG / "sources"
    copied_sources_root.mkdir(parents=True, exist_ok=True)

    slug_map: dict[str, str] = {}
    for index, raw_line in enumerate(source_index_path.read_text(encoding="utf-8").splitlines()):
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        old_local_path = str(((payload.get("locator") or {}).get("local_path")) or "")
        old_slug = Path(old_local_path).parent.name if old_local_path else f"source-{index:02d}"
        new_slug = f"s{index:02d}"
        slug_map[old_slug] = new_slug
        destination = copied_sources_root / new_slug / "source.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload["locator"] = payload.get("locator") or {}
        payload["locator"]["local_path"] = str(
            Path("source-layer") / "topics" / TOPIC_SLUG / "sources" / new_slug / "source.json"
        ).replace("\\", "/")
        destination.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return slug_map


def _rewrite_copied_topic_entries(kernel_root: Path, slug_map: dict[str, str]) -> None:
    entries_root = kernel_root / "canonical" / "staging" / "entries"
    for entry_path in sorted(entries_root.glob("*.json")):
        payload = json.loads(entry_path.read_text(encoding="utf-8"))
        if str(payload.get("topic_slug") or "").strip() != TOPIC_SLUG:
            continue
        payload["source_artifact_paths"] = [
            _rewrite_source_path(str(item), slug_map)
            for item in (payload.get("source_artifact_paths") or [])
        ]
        payload["source_refs"] = [
            _rewrite_source_path(str(item), slug_map)
            for item in (payload.get("source_refs") or [])
        ]
        payload["tags"] = [
            _rewrite_source_path(str(item), slug_map)
            for item in (payload.get("tags") or [])
        ]
        provenance = dict(payload.get("provenance") or {})
        source_slug = str(provenance.get("source_slug") or "").strip()
        if source_slug in slug_map:
            provenance["source_slug"] = slug_map[source_slug]
        payload["provenance"] = provenance
        entry_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="real-direction-corpus-growth-")).resolve()
    )
    kernel_root = work_root / "kernel"

    for relative in ("canonical", "knowledge_hub", "schemas"):
        shutil.copytree(package_root / relative, kernel_root / relative, dirs_exist_ok=True)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    runtime_schemas_root = package_root / "runtime" / "schemas"
    if runtime_schemas_root.exists():
        shutil.copytree(runtime_schemas_root, kernel_root / "runtime" / "schemas", dirs_exist_ok=True)

    slug_map = _copy_shortened_topic_sources(package_root, kernel_root)
    _rewrite_copied_topic_entries(kernel_root, slug_map)

    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)
    corpus_payload = service.compile_topic_l2_corpus_baseline(topic_slug=TOPIC_SLUG)

    json_path = Path(str(corpus_payload.get("json_path") or ""))
    markdown_path = Path(str(corpus_payload.get("markdown_path") or ""))
    ensure_exists(json_path)
    ensure_exists(markdown_path)

    payload = corpus_payload.get("payload") or {}
    summary = payload.get("summary") or {}
    relation_kinds = {str(row.get("relation") or "") for row in (payload.get("relation_clusters") or [])}

    check(
        int(summary.get("topic_entry_count") or 0) >= 15,
        "Expected the real direction to have at least 15 topic-local staging entries.",
    )
    check(
        int(summary.get("source_anchor_count") or 0) >= 9,
        "Expected the real direction to preserve at least 9 registered source anchors.",
    )
    check(
        int(summary.get("source_backed_entry_count") or 0) >= 12,
        "Expected most topic-local entries to remain source-backed.",
    )
    check(
        int(summary.get("multi_source_entry_count") or 0) >= 3,
        "Expected the corpus to contain multiple multi-source bridge-style entries.",
    )
    check(
        int(summary.get("derived_edge_count") or 0) >= 20,
        "Expected the corpus baseline to materialize a non-trivial edge set.",
    )
    check(
        int(summary.get("connected_entry_count") or 0) >= 12,
        "Expected the real direction corpus to have substantial connected entry coverage.",
    )
    check(
        int(summary.get("bridge_note_count") or 0) >= 1,
        "Expected at least one bridge note in the real direction corpus.",
    )
    check(
        int(summary.get("warning_note_count") or 0) >= 1,
        "Expected at least one warning note in the real direction corpus.",
    )
    check(
        {"supported_by_source", "shares_source_anchor"}.issubset(relation_kinds),
        "Expected the corpus baseline to include source-support and shared-source relations.",
    )

    result = {
        "status": "success",
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "topic_slug": TOPIC_SLUG,
        "updated_by": args.updated_by,
        "summary": summary,
        "relation_kinds": sorted(relation_kinds),
        "artifacts": {
            "topic_l2_corpus_baseline_json": str(json_path),
            "topic_l2_corpus_baseline_markdown": str(markdown_path),
        },
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

