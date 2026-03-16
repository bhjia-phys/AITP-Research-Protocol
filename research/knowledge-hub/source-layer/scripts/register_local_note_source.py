#!/usr/bin/env python3
"""Register a local note into Layer 0 and create a Layer 1 intake projection."""

from __future__ import annotations

import argparse
import json
import re
import textwrap
from datetime import datetime
from pathlib import Path


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "local-note"


def short_summary(text: str, limit: int = 260) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3].rstrip() + "..."


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


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


def ensure_topic_json(path: Path, topic_slug: str, status: str, created_at: str) -> None:
    if not path.exists():
        write_json(
            path,
            {
                "topic_slug": topic_slug,
                "title": topic_slug.replace("-", " ").title(),
                "status": status,
                "created_at": created_at,
            },
        )


def ensure_intake_status(path: Path, created_at: str) -> None:
    if not path.exists():
        write_json(
            path,
            {"stage": "L1_active", "next_stage": "L1", "last_updated": created_at},
        )


def build_projection_snapshot(
    topic_slug: str,
    source_id: str,
    layer0_source_json: str,
    layer0_snapshot: str,
    acquired_at: str,
) -> str:
    return textwrap.dedent(
        f"""\
        # Layer 1 source projection

        Topic: `{topic_slug}`
        Source id: `{source_id}`
        Projection created: `{acquired_at}`

        Layer 0 source of truth:
        - `{layer0_source_json}`

        Layer 0 snapshot:
        - `{layer0_snapshot}`
        """
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--path", required=True, help="Absolute or repo-local path to the local note.")
    parser.add_argument("--title", help="Optional title override.")
    parser.add_argument("--registered-by", default="codex")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    note_path = Path(args.path).expanduser().resolve()
    if not note_path.exists():
        raise SystemExit(f"Local note not found: {note_path}")

    title = args.title or note_path.stem.replace("-", " ").replace("_", " ")
    topic_slug = args.topic_slug
    acquired_at = now_iso()

    knowledge_root = Path(__file__).resolve().parents[2]
    source_slug = f"local-note-{slugify(title)}"
    source_id = f"local_note:{slugify(title)}"

    layer0_topic_root = knowledge_root / "source-layer" / "topics" / topic_slug
    layer0_source_root = layer0_topic_root / "sources" / source_slug
    layer0_source_root.mkdir(parents=True, exist_ok=True)

    preview = note_path.read_text(encoding="utf-8", errors="replace")
    payload = {
        "source_id": source_id,
        "source_type": "local_note",
        "title": title,
        "topic_slug": topic_slug,
        "provenance": {
            "origin": "local note",
            "absolute_path": str(note_path),
        },
        "locator": {
            "local_path": layer0_source_root.relative_to(knowledge_root).as_posix() + "/source.json",
            "snapshot_path": layer0_source_root.relative_to(knowledge_root).as_posix() + "/snapshot.md",
        },
        "acquired_at": acquired_at,
        "registered_by": args.registered_by,
        "summary": short_summary(preview),
    }

    ensure_topic_json(layer0_topic_root / "topic.json", topic_slug, "source_active", acquired_at)
    write_json(layer0_source_root / "source.json", payload)
    (layer0_source_root / "snapshot.md").write_text(
        textwrap.dedent(
            f"""\
            # {title}

            Source id: `{source_id}`
            Topic: `{topic_slug}`

            ## Local note
            - Path: `{note_path}`

            ## Preview
            {short_summary(preview, limit=1200)}
            """
        ),
        encoding="utf-8",
    )

    topic_index_path = layer0_topic_root / "source_index.jsonl"
    write_jsonl(
        topic_index_path,
        append_unique(load_jsonl(topic_index_path), payload, ("source_id",)),
    )

    global_index_path = knowledge_root / "source-layer" / "global_index.jsonl"
    write_jsonl(
        global_index_path,
        append_unique(
            load_jsonl(global_index_path),
            {
                "source_id": source_id,
                "topic_slug": topic_slug,
                "source_type": payload["source_type"],
                "title": payload["title"],
                "local_path": payload["locator"]["local_path"],
                "acquired_at": acquired_at,
            },
            ("source_id", "topic_slug"),
        ),
    )

    intake_topic_root = knowledge_root / "intake" / "topics" / topic_slug
    intake_projection_root = intake_topic_root / "sources" / source_slug
    intake_projection_root.mkdir(parents=True, exist_ok=True)
    ensure_topic_json(intake_topic_root / "topic.json", topic_slug, "intake_active", acquired_at)
    ensure_intake_status(intake_topic_root / "status.json", acquired_at)
    write_json(intake_projection_root / "source.json", payload)
    (intake_projection_root / "snapshot.md").write_text(
        build_projection_snapshot(
            topic_slug=topic_slug,
            source_id=source_id,
            layer0_source_json=payload["locator"]["local_path"],
            layer0_snapshot=payload["locator"]["snapshot_path"],
            acquired_at=acquired_at,
        ),
        encoding="utf-8",
    )
    intake_index_path = intake_topic_root / "source_index.jsonl"
    write_jsonl(
        intake_index_path,
        append_unique(load_jsonl(intake_index_path), payload, ("source_id",)),
    )

    status_payload = load_json(intake_topic_root / "status.json")
    if status_payload is not None:
        status_payload["last_updated"] = acquired_at
        write_json(intake_topic_root / "status.json", status_payload)

    print(f"Registered local note source {source_id}")
    print(f"- layer0 source.json: {knowledge_root / payload['locator']['local_path']}")
    print(f"- intake projection: {intake_projection_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
