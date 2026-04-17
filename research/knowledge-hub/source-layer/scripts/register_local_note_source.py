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


def normalize_backend_metadata(
    *,
    backend_id: str | None = None,
    backend_root: str | None = None,
    backend_artifact_kind: str | None = None,
    backend_relative_path: str | None = None,
    backend_card_path: str | None = None,
) -> dict | None:
    if not any(
        value is not None and str(value).strip()
        for value in (
            backend_id,
            backend_root,
            backend_artifact_kind,
            backend_relative_path,
            backend_card_path,
        )
    ):
        return None

    missing = [
        name
        for name, value in (
            ("backend_id", backend_id),
            ("backend_root", backend_root),
            ("backend_artifact_kind", backend_artifact_kind),
            ("backend_relative_path", backend_relative_path),
        )
        if value is None or not str(value).strip()
    ]
    if missing:
        raise ValueError(
            "Backend-aware L0 registration requires all of: "
            + ", ".join(missing)
        )

    payload = {
        "backend_id": str(backend_id).strip(),
        "backend_root": str(Path(str(backend_root)).expanduser().resolve()),
        "backend_artifact_kind": str(backend_artifact_kind).strip(),
        "backend_relative_path": str(backend_relative_path).strip().replace("\\", "/"),
    }
    if backend_card_path is not None and str(backend_card_path).strip():
        payload["backend_card_path"] = str(Path(str(backend_card_path)).expanduser().resolve())
    return payload


def build_projection_snapshot(
    topic_slug: str,
    source_id: str,
    layer0_source_json: str,
    layer0_snapshot: str,
    acquired_at: str,
    backend_metadata: dict | None = None,
) -> str:
    backend_lines = ""
    if backend_metadata:
        backend_card_path = backend_metadata.get("backend_card_path")
        backend_lines = textwrap.dedent(
            f"""\

            Backend bridge:
            - backend_id: `{backend_metadata['backend_id']}`
            - backend_root: `{backend_metadata['backend_root']}`
            - backend_artifact_kind: `{backend_metadata['backend_artifact_kind']}`
            - backend_relative_path: `{backend_metadata['backend_relative_path']}`
            - backend_card_path: `{backend_card_path or '(missing)'}`"""
        )
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
        {backend_lines}
        """
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--path", required=True, help="Absolute or repo-local path to the local note.")
    parser.add_argument("--title", help="Optional title override.")
    parser.add_argument("--registered-by", default="codex")
    parser.add_argument("--backend-id")
    parser.add_argument("--backend-root")
    parser.add_argument("--backend-artifact-kind")
    parser.add_argument("--backend-relative-path")
    parser.add_argument("--backend-card-path")
    return parser


def register_local_note_source(
    *,
    knowledge_root: Path,
    topic_slug: str,
    note_path: Path,
    title: str | None = None,
    registered_by: str = "codex",
    backend_id: str | None = None,
    backend_root: str | None = None,
    backend_artifact_kind: str | None = None,
    backend_relative_path: str | None = None,
    backend_card_path: str | None = None,
) -> dict:
    knowledge_root = knowledge_root.expanduser().resolve()
    note_path = note_path.expanduser().resolve()
    if not note_path.exists():
        raise FileNotFoundError(f"Local note not found: {note_path}")

    resolved_title = title or note_path.stem.replace("-", " ").replace("_", " ")
    acquired_at = now_iso()
    backend_metadata = normalize_backend_metadata(
        backend_id=backend_id,
        backend_root=backend_root,
        backend_artifact_kind=backend_artifact_kind,
        backend_relative_path=backend_relative_path,
        backend_card_path=backend_card_path,
    )

    source_slug = f"local-note-{slugify(resolved_title)}"
    source_id = f"local_note:{slugify(resolved_title)}"

    layer0_topic_root = knowledge_root / "topics" / topic_slug / "L0"
    layer0_source_root = layer0_topic_root / "sources" / source_slug
    layer0_source_root.mkdir(parents=True, exist_ok=True)

    preview = note_path.read_text(encoding="utf-8", errors="replace")
    provenance = {
        "origin": "local note",
        "absolute_path": str(note_path),
    }
    locator = {
        "local_path": layer0_source_root.relative_to(knowledge_root).as_posix() + "/source.json",
        "snapshot_path": layer0_source_root.relative_to(knowledge_root).as_posix() + "/snapshot.md",
    }
    if backend_metadata:
        provenance.update(
            {
                "backend_id": backend_metadata["backend_id"],
                "backend_root": backend_metadata["backend_root"],
                "backend_artifact_kind": backend_metadata["backend_artifact_kind"],
            }
        )
        if backend_metadata.get("backend_card_path"):
            provenance["backend_card_path"] = backend_metadata["backend_card_path"]
        locator["backend_relative_path"] = backend_metadata["backend_relative_path"]

    payload = {
        "source_id": source_id,
        "source_type": "local_note",
        "title": resolved_title,
        "topic_slug": topic_slug,
        "provenance": provenance,
        "locator": locator,
        "acquired_at": acquired_at,
        "registered_by": registered_by,
        "summary": short_summary(preview),
    }

    ensure_topic_json(layer0_topic_root / "topic.json", topic_slug, "source_active", acquired_at)
    write_json(layer0_source_root / "source.json", payload)
    backend_snapshot_block = ""
    if backend_metadata:
        backend_snapshot_block = textwrap.dedent(
            f"""\

            ## Backend bridge
            - Backend id: `{backend_metadata['backend_id']}`
            - Backend root: `{backend_metadata['backend_root']}`
            - Backend artifact kind: `{backend_metadata['backend_artifact_kind']}`
            - Backend relative path: `{backend_metadata['backend_relative_path']}`
            - Backend card path: `{backend_metadata.get('backend_card_path') or '(missing)'}`"""
        )
    (layer0_source_root / "snapshot.md").write_text(
        textwrap.dedent(
            f"""\
            # {resolved_title}

            Source id: `{source_id}`
            Topic: `{topic_slug}`

            ## Local note
            - Path: `{note_path}`
            {backend_snapshot_block}

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
                "backend_id": payload["provenance"].get("backend_id"),
                "backend_root": payload["provenance"].get("backend_root"),
                "backend_artifact_kind": payload["provenance"].get("backend_artifact_kind"),
                "backend_card_path": payload["provenance"].get("backend_card_path"),
                "backend_relative_path": payload["locator"].get("backend_relative_path"),
                "acquired_at": acquired_at,
            },
            ("source_id", "topic_slug"),
        ),
    )

    intake_topic_root = knowledge_root / "topics" / topic_slug / "L1"
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
            backend_metadata=backend_metadata,
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

    return {
        "source_id": source_id,
        "payload": payload,
        "layer0_source_json": layer0_source_root / "source.json",
        "layer0_snapshot": layer0_source_root / "snapshot.md",
        "intake_projection_root": intake_projection_root,
    }


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = register_local_note_source(
            knowledge_root=Path(__file__).resolve().parents[2],
            topic_slug=args.topic_slug,
            note_path=Path(args.path),
            title=args.title,
            registered_by=args.registered_by,
            backend_id=args.backend_id,
            backend_root=args.backend_root,
            backend_artifact_kind=args.backend_artifact_kind,
            backend_relative_path=args.backend_relative_path,
            backend_card_path=args.backend_card_path,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Registered local note source {result['source_id']}")
    print(f"- layer0 source.json: {result['layer0_source_json']}")
    print(f"- intake projection: {result['intake_projection_root']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
