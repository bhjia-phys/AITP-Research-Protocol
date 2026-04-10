from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import jsonschema


def _kernel_root(kernel_root: Path | None = None) -> Path:
    return kernel_root or Path(__file__).resolve().parents[1]


def _runtime_topic_root(topic_slug: str, kernel_root: Path | None = None) -> Path:
    return _kernel_root(kernel_root) / "runtime" / "topics" / topic_slug


def _schema_path(schema_name: str, kernel_root: Path | None = None) -> Path:
    return _kernel_root(kernel_root) / "schemas" / f"{schema_name}.schema.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _validate(schema_name: str, payload: dict[str, Any], kernel_root: Path | None = None) -> None:
    schema = _read_json(_schema_path(schema_name, kernel_root))
    jsonschema.validate(instance=payload, schema=schema)


def _slugify(value: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", str(value).lower())
    return "-".join(tokens) or "item"


def _packet_type_for_candidate_type(candidate_type: str) -> str:
    normalized = str(candidate_type or "").strip().lower()
    if normalized in {
        "theorem_card",
        "claim_card",
        "proof_fragment",
        "derivation_step",
        "derivation_object",
        "equivalence_map",
        "equation_card",
    }:
        return "theorem"
    if normalized in {"method", "workflow"}:
        return "method"
    if normalized == "topic_skill_projection":
        return "code_method"
    if normalized == "validation_pattern":
        return "regression_status"
    return "concept"


def write_topic_synopsis(
    topic_slug: str,
    payload: dict[str, Any],
    *,
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    _validate("topic-synopsis", payload, kernel_root)
    path = _runtime_topic_root(topic_slug, kernel_root) / "topic_synopsis.json"
    _write_json(path, payload)
    return {"topic_synopsis": payload, "path": str(path)}


def write_pending_decisions_projection(
    topic_slug: str,
    payload: dict[str, Any],
    *,
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    path = _runtime_topic_root(topic_slug, kernel_root) / "pending_decisions.json"
    _write_json(path, payload)
    return {"pending_decisions": payload, "path": str(path)}


def write_promotion_readiness_projection(
    topic_slug: str,
    payload: dict[str, Any],
    *,
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    path = _runtime_topic_root(topic_slug, kernel_root) / "promotion_readiness.json"
    _write_json(path, payload)
    return {"promotion_readiness": payload, "path": str(path)}


def write_topic_skill_projection(
    topic_slug: str,
    payload: dict[str, Any],
    *,
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    _validate("topic-skill-projection", payload, kernel_root)
    path = _runtime_topic_root(topic_slug, kernel_root) / "topic_skill_projection.active.json"
    _write_json(path, payload)
    return {"topic_skill_projection": payload, "path": str(path)}


def write_knowledge_packets(
    topic_slug: str,
    packets: list[dict[str, Any]],
    *,
    kernel_root: Path | None = None,
) -> list[dict[str, Any]]:
    packet_root = _runtime_topic_root(topic_slug, kernel_root) / "knowledge_packets"
    packet_root.mkdir(parents=True, exist_ok=True)
    written: list[dict[str, Any]] = []
    for payload in packets:
        _validate("knowledge-packet", payload, kernel_root)
        path = packet_root / f"{str(payload['id']).replace(':', '__')}.json"
        _write_json(path, payload)
        written.append({"knowledge_packet": payload, "path": str(path)})
    return written


def build_knowledge_packets_from_candidates(
    topic_slug: str,
    candidate_rows: list[dict[str, Any]],
    *,
    lane: str,
    updated_at: str,
    updated_by: str,
    kernel_root: Path | None = None,
) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for row in candidate_rows:
        candidate_id = str(row.get("candidate_id") or "").strip()
        title = str(row.get("title") or "").strip()
        summary = str(row.get("summary") or "").strip()
        if not candidate_id or not title or not summary:
            continue
        supporting_refs = [candidate_id]
        for origin_ref in row.get("origin_refs") or []:
            if isinstance(origin_ref, dict):
                object_ref = str(origin_ref.get("object_ref") or origin_ref.get("id") or "").strip()
                if object_ref:
                    supporting_refs.append(object_ref)
        packets.append(
            {
                "id": f"packet:{_slugify(candidate_id)}",
                "topic_slug": topic_slug,
                "packet_type": _packet_type_for_candidate_type(str(row.get("candidate_type") or "")),
                "source_ref": candidate_id,
                "candidate_type": str(row.get("candidate_type") or ""),
                "title": title,
                "summary": summary,
                "status": str(row.get("status") or "draft"),
                "lane": lane,
                "supporting_refs": list(dict.fromkeys(supporting_refs)),
                "target_l2_refs": [str(item).strip() for item in (row.get("intended_l2_targets") or []) if str(item).strip()],
                "updated_at": updated_at,
                "updated_by": updated_by,
            }
        )
    return write_knowledge_packets(topic_slug, packets, kernel_root=kernel_root)


def write_promotion_trace(
    topic_slug: str,
    payload: dict[str, Any],
    *,
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    _validate("promotion-trace", payload, kernel_root)
    path = _runtime_topic_root(topic_slug, kernel_root) / "promotion_trace.latest.json"
    _write_json(path, payload)
    return {"promotion_trace": payload, "path": str(path)}
