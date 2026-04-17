#!/usr/bin/env python3
"""Build a physics-adapted concept graph for one registered source.

Design patterns in this file are adapted from Graphify (MIT), but the
implementation here is AITP-native and offline-testable.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema

_NODE_TYPES = {
    "concept",
    "method",
    "finding",
    "theorem",
    "definition",
    "conjecture",
    "regime",
    "approximation",
    "notation_system",
    "proof",
    "equation",
    "observable",
}

_EDGE_RELATIONS = {
    "depends_on",
    "related_to",
    "assumes",
    "valid_in",
    "contradicts",
    "derives",
    "notation_for",
    "generalizes",
    "special_case_of",
    "implies",
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


def slugify(text: str) -> str:
    lowered = str(text or "").strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", lowered)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "concept"


def _schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / "concept-graph.schema.json"


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _normalize_id(value: Any, *, prefix: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{prefix} identifier is required")
    if ":" in text:
        return text
    return f"{prefix}:{slugify(text)}"


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
        local_path = str((row.get("locator") or {}).get("local_path") or row.get("local_path") or "").strip()
        if not local_path:
            continue
        if str(source_id or "").strip() and str(row.get("source_id") or "").strip() == str(source_id).strip():
            return (knowledge_root / local_path).resolve()
        if str(arxiv_id or "").strip() and str((row.get("provenance") or {}).get("arxiv_id") or "").strip() == str(arxiv_id).strip():
            return (knowledge_root / local_path).resolve()

    candidate_paths = list((topic_root / "sources").glob("*/source.json"))
    if len(candidate_paths) == 1 and not str(source_id or "").strip() and not str(arxiv_id or "").strip():
        return candidate_paths[0].resolve()
    raise FileNotFoundError("Unable to resolve a unique registered source for concept-graph construction.")


def _token_nodes(title: str, summary: str, keywords: list[str], evidence_ref: str) -> list[dict[str, Any]]:
    labels = [*keywords]
    if not labels:
        labels = [fragment.strip() for fragment in re.split(r"\band\b|,", title, flags=re.IGNORECASE) if fragment.strip()]
    if not labels:
        labels = [title or summary or "source concept"]
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for label in labels[:6]:
        node_id = f"concept:{slugify(label)}"
        if node_id in seen:
            continue
        seen.add(node_id)
        rows.append(
            {
                "node_id": node_id,
                "label": label,
                "node_type": "concept",
                "confidence_tier": "EXTRACTED",
                "confidence_score": 0.7,
                "evidence_refs": [evidence_ref],
                "notes": "",
            }
        )
    return rows


def _heuristic_graph(*, source_payload: dict[str, Any], source_json_relative_path: str) -> dict[str, Any]:
    title = str(source_payload.get("title") or "").strip()
    summary = str(source_payload.get("summary") or "").strip()
    provenance = source_payload.get("provenance") or {}
    keywords = [str(item) for item in (provenance.get("deepxiv_keywords") or []) if str(item).strip()]
    nodes = _token_nodes(title, summary, keywords, source_json_relative_path)
    edges: list[dict[str, Any]] = []
    if len(nodes) >= 2:
        edges.append(
            {
                "edge_id": f"edge-{slugify(nodes[1]['label'])}-special-case-{slugify(nodes[0]['label'])}",
                "from_id": nodes[1]["node_id"],
                "relation": "special_case_of",
                "to_id": nodes[0]["node_id"],
                "evidence_refs": [source_json_relative_path],
                "notes": "Heuristic fallback edge derived from source title and keywords.",
            }
        )
    communities = [
        {
            "community_id": f"community-{slugify(title or 'source-cluster')}",
            "label": title or "Source cluster",
            "node_ids": [node["node_id"] for node in nodes],
        }
    ]
    return {
        "provider": "heuristic_fallback",
        "nodes": nodes,
        "edges": edges,
        "hyperedges": [],
        "communities": communities,
        "god_nodes": [nodes[0]["node_id"]] if nodes else [],
    }


def _normalize_nodes(values: list[Any], *, evidence_ref: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        label = str(value.get("label") or value.get("title") or "").strip()
        node_type = str(value.get("node_type") or "concept").strip()
        if not label or node_type not in _NODE_TYPES:
            continue
        rows.append(
            {
                "node_id": _normalize_id(value.get("node_id") or label, prefix=node_type),
                "label": label,
                "node_type": node_type,
                "confidence_tier": str(value.get("confidence_tier") or "EXTRACTED"),
                "confidence_score": float(value.get("confidence_score") or 0.7),
                "evidence_refs": [str(item) for item in (value.get("evidence_refs") or [evidence_ref]) if str(item).strip()],
                "notes": str(value.get("notes") or ""),
            }
        )
    return rows


def _normalize_edges(values: list[Any], *, evidence_ref: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        relation = str(value.get("relation") or "").strip()
        if relation not in _EDGE_RELATIONS:
            continue
        rows.append(
            {
                "edge_id": str(value.get("edge_id") or f"edge-{slugify(str(value.get('from_id') or 'from'))}-{relation}-{slugify(str(value.get('to_id') or 'to'))}"),
                "from_id": _normalize_id(value.get("from_id"), prefix="concept"),
                "relation": relation,
                "to_id": _normalize_id(value.get("to_id"), prefix="concept"),
                "evidence_refs": [str(item) for item in (value.get("evidence_refs") or [evidence_ref]) if str(item).strip()],
                "notes": str(value.get("notes") or ""),
            }
        )
    return rows


def _normalize_hyperedges(values: list[Any], *, evidence_ref: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        node_ids = [_normalize_id(item, prefix="concept") for item in (value.get("node_ids") or []) if str(item).strip()]
        if len(node_ids) < 2:
            continue
        rows.append(
            {
                "hyperedge_id": str(value.get("hyperedge_id") or f"hyperedge-{slugify(str(value.get('relation') or 'group'))}"),
                "relation": str(value.get("relation") or "supports"),
                "node_ids": node_ids,
                "evidence_refs": [str(item) for item in (value.get("evidence_refs") or [evidence_ref]) if str(item).strip()],
                "notes": str(value.get("notes") or ""),
            }
        )
    return rows


def _normalize_communities(values: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        label = str(value.get("label") or "").strip()
        node_ids = [_normalize_id(item, prefix="concept") for item in (value.get("node_ids") or []) if str(item).strip()]
        if not label or not node_ids:
            continue
        rows.append(
            {
                "community_id": str(value.get("community_id") or f"community-{slugify(label)}"),
                "label": label,
                "node_ids": node_ids,
            }
        )
    return rows


def _normalized_override(*, override: dict[str, Any], source_json_relative_path: str) -> dict[str, Any]:
    body = dict(override.get("graph") or override)
    return {
        "provider": str(body.get("provider") or "override_json"),
        "nodes": _normalize_nodes(list(body.get("nodes") or []), evidence_ref=source_json_relative_path),
        "edges": _normalize_edges(list(body.get("edges") or []), evidence_ref=source_json_relative_path),
        "hyperedges": _normalize_hyperedges(list(body.get("hyperedges") or []), evidence_ref=source_json_relative_path),
        "communities": _normalize_communities(list(body.get("communities") or [])),
        "god_nodes": [_normalize_id(item, prefix="concept") for item in (body.get("god_nodes") or []) if str(item).strip()],
    }


def build_concept_graph_for_registered_source(
    *,
    knowledge_root: Path,
    topic_slug: str,
    source_id: str | None = None,
    arxiv_id: str | None = None,
    source_json: str | None = None,
    built_by: str = "codex",
    graph_override: dict[str, Any] | None = None,
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
    source_json_relative_path = _relative(source_json_path, resolved_knowledge_root)
    graph_body = (
        _normalized_override(override=graph_override or {}, source_json_relative_path=source_json_relative_path)
        if graph_override is not None
        else _heuristic_graph(source_payload=source_payload, source_json_relative_path=source_json_relative_path)
    )
    graph_payload = {
        "kind": "source_concept_graph",
        "graph_version": 1,
        "topic_slug": resolved_topic_slug,
        "source_id": str(source_payload.get("source_id") or source_id or ""),
        "source_json_path": source_json_relative_path,
        "generated_at": now_iso(),
        "generated_by": built_by,
        "provider": graph_body["provider"],
        "nodes": graph_body["nodes"],
        "edges": graph_body["edges"],
        "hyperedges": graph_body["hyperedges"],
        "communities": graph_body["communities"],
        "god_nodes": graph_body["god_nodes"],
    }
    jsonschema.validate(graph_payload, load_json(_schema_path()))

    concept_graph_path = source_json_path.with_name("concept_graph.json")
    write_json(concept_graph_path, graph_payload)
    concept_graph_relative_path = _relative(concept_graph_path, resolved_knowledge_root)

    source_payload.setdefault("locator", {})
    source_payload["locator"]["concept_graph_path"] = concept_graph_relative_path
    source_payload.setdefault("provenance", {})
    source_payload["provenance"]["concept_graph_provider"] = graph_payload["provider"]
    source_payload["provenance"]["concept_graph_generated_at"] = graph_payload["generated_at"]
    write_json(source_json_path, source_payload)

    intake_projection_json = (
        resolved_knowledge_root / "topics" / resolved_topic_slug / "L1" / "sources" / source_json_path.parent.name / "source.json"
    )
    if intake_projection_json.exists():
        intake_payload = load_json(intake_projection_json) or {}
        intake_payload.setdefault("locator", {})
        intake_payload["locator"]["concept_graph_path"] = concept_graph_relative_path
        intake_payload.setdefault("provenance", {})
        intake_payload["provenance"]["concept_graph_provider"] = graph_payload["provider"]
        intake_payload["provenance"]["concept_graph_generated_at"] = graph_payload["generated_at"]
        write_json(intake_projection_json, intake_payload)

    receipt_path = source_json_path.with_name("concept_graph_receipt.json")
    receipt_payload = {
        "status": "built",
        "topic_slug": resolved_topic_slug,
        "source_id": graph_payload["source_id"],
        "concept_graph_path": concept_graph_relative_path,
        "provider": graph_payload["provider"],
        "generated_at": graph_payload["generated_at"],
        "generated_by": built_by,
        "node_count": len(graph_payload["nodes"]),
        "edge_count": len(graph_payload["edges"]),
        "hyperedge_count": len(graph_payload["hyperedges"]),
        "community_count": len(graph_payload["communities"]),
    }
    write_json(receipt_path, receipt_payload)

    return {
        "status": "built",
        "topic_slug": resolved_topic_slug,
        "source_id": graph_payload["source_id"],
        "provider": graph_payload["provider"],
        "concept_graph_path": str(concept_graph_path),
        "concept_graph_relative_path": concept_graph_relative_path,
        "receipt_path": str(receipt_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-root")
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--source-id")
    parser.add_argument("--arxiv-id")
    parser.add_argument("--source-json")
    parser.add_argument("--built-by", default="codex")
    parser.add_argument("--graph-json")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    knowledge_root = (
        Path(args.knowledge_root).expanduser().resolve()
        if args.knowledge_root
        else Path(__file__).resolve().parents[2]
    )
    graph_override = None
    if args.graph_json:
        graph_path = Path(args.graph_json).expanduser().resolve()
        graph_override = load_json(graph_path)
        if graph_override is None:
            raise FileNotFoundError(f"Graph JSON does not exist: {graph_path}")
    result = build_concept_graph_for_registered_source(
        knowledge_root=knowledge_root,
        topic_slug=args.topic_slug,
        source_id=args.source_id,
        arxiv_id=args.arxiv_id,
        source_json=args.source_json,
        built_by=args.built_by,
        graph_override=graph_override,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
