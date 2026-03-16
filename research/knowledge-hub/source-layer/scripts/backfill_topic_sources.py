#!/usr/bin/env python3
"""Backfill an existing intake topic into the dedicated Layer 0 source substrate."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def append_unique(rows: list[dict], new_row: dict, key_fields: tuple[str, ...]) -> list[dict]:
    filtered = []
    for row in rows:
        if all(row.get(field) == new_row.get(field) for field in key_fields):
            continue
        filtered.append(row)
    filtered.append(new_row)
    return filtered


def layer0_payload_from_source(
    knowledge_root: Path,
    topic_slug: str,
    source_payload: dict,
    layer0_source_root: Path,
) -> dict:
    layer0_rel = layer0_source_root.relative_to(knowledge_root).as_posix()
    bundle = ""
    for candidate in ("source.tar.gz", "source.tar"):
        candidate_path = layer0_source_root / candidate
        if candidate_path.exists():
            bundle = candidate_path.relative_to(knowledge_root).as_posix()
            break
    extract_dir = layer0_source_root / "tex-src"

    updated = dict(source_payload)
    updated["topic_slug"] = topic_slug
    updated["locator"] = {
        **source_payload.get("locator", {}),
        "local_path": f"{layer0_rel}/source.json",
        "snapshot_path": f"{layer0_rel}/snapshot.md",
        "downloaded_source_bundle": bundle,
        "extracted_source_dir": extract_dir.relative_to(knowledge_root).as_posix()
        if extract_dir.exists()
        else "",
    }
    return updated


def build_projection_snapshot(payload: dict, refreshed_at: str) -> str:
    return "\n".join(
        [
            "# Layer 1 source projection",
            "",
            f"Topic: `{payload['topic_slug']}`",
            f"Source id: `{payload['source_id']}`",
            f"Projection refreshed: `{refreshed_at}`",
            "",
            "Layer 0 source of truth:",
            f"- `{payload['locator']['local_path']}`",
            "",
            "Layer 0 snapshot:",
            f"- `{payload['locator']['snapshot_path']}`",
            "",
            "This intake-side snapshot is a projection only.",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--registered-by", default="codex")
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    topic_slug = args.topic_slug
    refreshed_at = now_iso()

    knowledge_root = Path(__file__).resolve().parents[2]
    intake_topic_root = knowledge_root / "intake" / "topics" / topic_slug
    intake_sources_root = intake_topic_root / "sources"
    if not intake_sources_root.exists():
        raise SystemExit(f"No intake sources found for topic {topic_slug}")

    source_layer_topic_root = knowledge_root / "source-layer" / "topics" / topic_slug
    source_layer_topic_root.mkdir(parents=True, exist_ok=True)

    intake_topic_json = intake_topic_root / "topic.json"
    if intake_topic_json.exists():
        topic_payload = load_json(intake_topic_json)
    else:
        topic_payload = {
            "topic_slug": topic_slug,
            "title": topic_slug.replace("-", " ").title(),
            "status": "source_active",
            "created_at": refreshed_at,
        }
    topic_payload["status"] = "source_active"
    write_json(source_layer_topic_root / "topic.json", topic_payload)

    source_rows: list[dict] = []
    global_rows = load_jsonl(knowledge_root / "source-layer" / "global_index.jsonl")

    for source_dir in sorted(path for path in intake_sources_root.iterdir() if path.is_dir()):
        intake_source_json = source_dir / "source.json"
        if not intake_source_json.exists():
            continue
        original_payload = load_json(intake_source_json)
        source_slug = source_dir.name
        layer0_source_root = source_layer_topic_root / "sources" / source_slug
        if not layer0_source_root.exists() or args.force:
            shutil.copytree(source_dir, layer0_source_root, dirs_exist_ok=True)

        layer0_payload = layer0_payload_from_source(
            knowledge_root=knowledge_root,
            topic_slug=topic_slug,
            source_payload=original_payload,
            layer0_source_root=layer0_source_root,
        )
        layer0_payload["registered_by"] = original_payload.get("registered_by", args.registered_by)
        write_json(layer0_source_root / "source.json", layer0_payload)

        source_rows.append(layer0_payload)
        global_rows = append_unique(
            global_rows,
            {
                "source_id": layer0_payload["source_id"],
                "topic_slug": topic_slug,
                "source_type": layer0_payload["source_type"],
                "title": layer0_payload["title"],
                "local_path": layer0_payload["locator"]["local_path"],
                "acquired_at": layer0_payload["acquired_at"],
            },
            ("source_id", "topic_slug"),
        )

        write_json(intake_source_json, layer0_payload)
        (source_dir / "snapshot.md").write_text(
            build_projection_snapshot(layer0_payload, refreshed_at),
            encoding="utf-8",
        )

    write_jsonl(source_layer_topic_root / "source_index.jsonl", source_rows)
    write_jsonl(knowledge_root / "source-layer" / "global_index.jsonl", global_rows)
    write_jsonl(intake_topic_root / "source_index.jsonl", source_rows)

    status_json = intake_topic_root / "status.json"
    if status_json.exists():
        status_payload = load_json(status_json)
        status_payload["last_updated"] = refreshed_at
        write_json(status_json, status_payload)

    print(f"Backfilled Layer 0 sources for topic {topic_slug}")
    print(f"- layer0 topic root: {source_layer_topic_root}")
    print(f"- source count: {len(source_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
