#!/usr/bin/env python3
"""Enrich a registered arXiv source with DeepXiv-style progressive-reading metadata.

Design patterns in this file are adapted from DeepXiv SDK (MIT), but the
implementation here is AITP-native and offline-testable.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def short_summary(text: str, limit: int = 240) -> str:
    collapsed = " ".join(str(text or "").split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3].rstrip() + "..."


def _normalize_keywords(values: list[Any] | None) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        keyword = str(value or "").strip()
        if keyword and keyword.lower() not in seen:
            seen.add(keyword.lower())
            deduped.append(keyword)
    return deduped


def _token_keywords(*texts: str, limit: int = 8) -> list[str]:
    counts: dict[str, int] = {}
    display: dict[str, str] = {}
    for text in texts:
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", str(text or "")):
            lowered = token.lower()
            if lowered in _STOPWORDS:
                continue
            counts[lowered] = counts.get(lowered, 0) + 1
            display.setdefault(lowered, token)
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [display[key] for key, _count in ordered[:limit]]


def _section_rows_from_snapshot(snapshot_text: str, summary: str) -> list[dict[str, Any]]:
    headings = re.findall(r"^##\s+(.+?)\s*$", snapshot_text, flags=re.MULTILINE)
    sections: list[dict[str, Any]] = []
    for idx, heading in enumerate(headings):
        sections.append(
            {
                "name": heading.strip(),
                "idx": idx,
                "tldr": short_summary(summary, limit=120),
                "token_count": max(len(summary.split()), 1),
            }
        )
    if sections:
        return sections
    return [
        {
            "name": "Abstract",
            "idx": 0,
            "tldr": short_summary(summary, limit=120),
            "token_count": max(len(summary.split()), 1),
        }
    ]


def _normalize_sections(values: list[Any] | None, summary: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, value in enumerate(values or []):
        if not isinstance(value, dict):
            continue
        name = str(value.get("name") or value.get("section") or "").strip()
        if not name:
            continue
        rows.append(
            {
                "name": name,
                "idx": int(value.get("idx", idx)),
                "tldr": short_summary(str(value.get("tldr") or summary), limit=160),
                "token_count": int(value.get("token_count") or max(len(str(value.get("tldr") or summary).split()), 1)),
            }
        )
    return rows


def _heuristic_enrichment(source_payload: dict[str, Any], snapshot_text: str) -> dict[str, Any]:
    title = str(source_payload.get("title") or "").strip()
    summary = str(source_payload.get("summary") or "").strip()
    return {
        "provider": "heuristic_fallback",
        "tldr": short_summary(summary or title, limit=220),
        "keywords": _token_keywords(title, summary),
        "github_url": "",
        "sections": _section_rows_from_snapshot(snapshot_text, summary or title),
    }


def _normalize_override(source_payload: dict[str, Any], override: dict[str, Any], snapshot_text: str) -> dict[str, Any]:
    body = dict(override.get("paper") or override)
    title = str(source_payload.get("title") or "").strip()
    summary = str(source_payload.get("summary") or title).strip()
    sections = _normalize_sections(body.get("sections"), summary)
    if not sections:
        sections = _section_rows_from_snapshot(snapshot_text, summary)
    return {
        "provider": str(body.get("provider") or "override_json"),
        "tldr": short_summary(str(body.get("tldr") or summary), limit=220),
        "keywords": _normalize_keywords(body.get("keywords")) or _token_keywords(title, summary),
        "github_url": str(body.get("github_url") or "").strip(),
        "sections": sections,
    }


def _locate_source_json(
    *,
    knowledge_root: Path,
    topic_slug: str,
    source_json: str | None,
    source_id: str | None,
    arxiv_id: str | None,
) -> Path:
    if str(source_json or "").strip():
        path = Path(str(source_json)).expanduser()
        if not path.is_absolute():
            path = knowledge_root / path
        resolved = path.resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Source JSON does not exist: {resolved}")
        return resolved

    topic_root = knowledge_root / "topics" / topic_slug / "L0"
    rows = load_jsonl(topic_root / "source_index.jsonl")
    for row in rows:
        if str(source_id or "").strip() and str(row.get("source_id") or "").strip() == str(source_id).strip():
            local_path = str((row.get("locator") or {}).get("local_path") or row.get("local_path") or "").strip()
            if local_path:
                return (knowledge_root / local_path).resolve()
        if str(arxiv_id or "").strip():
            provenance = row.get("provenance") or {}
            if str(provenance.get("arxiv_id") or "").strip() == str(arxiv_id).strip():
                local_path = str((row.get("locator") or {}).get("local_path") or row.get("local_path") or "").strip()
                if local_path:
                    return (knowledge_root / local_path).resolve()

    candidate_paths = list((topic_root / "sources").glob("*/source.json"))
    if len(candidate_paths) == 1 and not str(source_id or "").strip() and not str(arxiv_id or "").strip():
        return candidate_paths[0].resolve()
    raise FileNotFoundError("Unable to resolve a unique registered source. Provide --source-id, --arxiv-id, or --source-json.")


def enrich_registered_source(
    *,
    knowledge_root: Path,
    topic_slug: str,
    source_id: str | None = None,
    arxiv_id: str | None = None,
    source_json: str | None = None,
    enriched_by: str = "codex",
    enrichment_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_knowledge_root = knowledge_root.expanduser().resolve()
    resolved_topic_slug = str(topic_slug or "").strip()
    if not resolved_topic_slug:
        raise ValueError("topic_slug is required")

    source_json_path = _locate_source_json(
        knowledge_root=resolved_knowledge_root,
        topic_slug=resolved_topic_slug,
        source_json=source_json,
        source_id=source_id,
        arxiv_id=arxiv_id,
    )
    source_payload = load_json(source_json_path)
    if source_payload is None:
        raise FileNotFoundError(f"Registered source payload missing: {source_json_path}")
    snapshot_path = source_json_path.with_name("snapshot.md")
    snapshot_text = snapshot_path.read_text(encoding="utf-8") if snapshot_path.exists() else ""

    enrichment = (
        _normalize_override(source_payload, enrichment_override or {}, snapshot_text)
        if enrichment_override is not None
        else _heuristic_enrichment(source_payload, snapshot_text)
    )

    provenance = dict(source_payload.get("provenance") or {})
    provenance.update(
        {
            "deepxiv_provider": enrichment["provider"],
            "deepxiv_tldr": enrichment["tldr"],
            "deepxiv_keywords": enrichment["keywords"],
            "deepxiv_sections": enrichment["sections"],
            "deepxiv_github_url": enrichment["github_url"],
            "deepxiv_enriched_at": now_iso(),
        }
    )
    source_payload["provenance"] = provenance
    write_json(source_json_path, source_payload)

    intake_projection_json = (
        resolved_knowledge_root
        / "topics"
        / resolved_topic_slug
        / "L1"
        / "sources"
        / source_json_path.parent.name
        / "source.json"
    )
    if intake_projection_json.exists():
        write_json(intake_projection_json, source_payload)

    receipt_path = source_json_path.with_name("deepxiv_enrichment.json")
    receipt_payload = {
        "status": "enriched",
        "topic_slug": resolved_topic_slug,
        "source_id": str(source_payload.get("source_id") or source_id or ""),
        "source_json_path": source_json_path.relative_to(resolved_knowledge_root).as_posix(),
        "provider": enrichment["provider"],
        "enriched_at": provenance["deepxiv_enriched_at"],
        "enriched_by": enriched_by,
        "tldr": enrichment["tldr"],
        "keywords": enrichment["keywords"],
        "section_count": len(enrichment["sections"]),
        "github_url": enrichment["github_url"],
    }
    write_json(receipt_path, receipt_payload)

    return {
        "status": "enriched",
        "topic_slug": resolved_topic_slug,
        "source_id": str(source_payload.get("source_id") or source_id or ""),
        "provider": enrichment["provider"],
        "source_json_path": str(source_json_path),
        "intake_projection_json_path": str(intake_projection_json) if intake_projection_json.exists() else "",
        "receipt_path": str(receipt_path),
        "section_count": len(enrichment["sections"]),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-root")
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--source-id")
    parser.add_argument("--arxiv-id")
    parser.add_argument("--source-json")
    parser.add_argument("--enriched-by", default="codex")
    parser.add_argument("--enrichment-json")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    knowledge_root = (
        Path(args.knowledge_root).expanduser().resolve()
        if args.knowledge_root
        else Path(__file__).resolve().parents[2]
    )
    enrichment_override = None
    if args.enrichment_json:
        enrichment_path = Path(args.enrichment_json).expanduser().resolve()
        enrichment_override = load_json(enrichment_path)
        if enrichment_override is None:
            raise FileNotFoundError(f"Enrichment JSON does not exist: {enrichment_path}")

    result = enrich_registered_source(
        knowledge_root=knowledge_root,
        topic_slug=args.topic_slug,
        source_id=args.source_id,
        arxiv_id=args.arxiv_id,
        source_json=args.source_json,
        enriched_by=args.enriched_by,
        enrichment_override=enrichment_override,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
