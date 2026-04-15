from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


def consultation_projection_path(
    kernel_root: Path,
    *,
    topic_slug: str,
    stage: str,
    run_id: str | None,
) -> Path | None:
    if not run_id:
        return None
    if stage == "L1":
        return kernel_root / "topics" / topic_slug / "L1" / "l2_consultation_log.jsonl"
    if stage == "L3":
        return kernel_root / "topics" / topic_slug / "L3" / "runs" / run_id / "l2_consultation_log.jsonl"
    return kernel_root / "topics" / topic_slug / "L4" / "runs" / run_id / "l2_consultation_log.jsonl"


def build_l2_consultation_record(
    *,
    kernel_root: Path,
    topic_slug: str,
    stage: str,
    run_id: str | None,
    query_text: str,
    retrieval_profile: str,
    dashboard_path: Path,
    context_id: str,
    payload: dict[str, Any],
    relativize: Callable[[Path], str],
) -> dict[str, Any]:
    projection_path = consultation_projection_path(
        kernel_root,
        topic_slug=topic_slug,
        stage=stage,
        run_id=run_id,
    )
    primary_hits = list(payload.get("primary_hits", []))
    expanded_hits = list(payload.get("expanded_hits", []))
    traversal_summary = dict(payload.get("traversal_summary") or {})
    return {
        "record_args": {
            "context_ref": {
                "id": context_id,
                "layer": stage,
                "object_type": "consultation_query",
                "path": relativize(dashboard_path),
                "title": f"L2 consultation query for {topic_slug}",
                "summary": query_text,
            },
            "requested_unit_types": requested_unit_types_for_profile(kernel_root, retrieval_profile),
            "retrieved_refs": [hit_to_object_ref(row) for row in [*primary_hits, *expanded_hits]],
            "result_summary": (
                f"Retrieved {len(primary_hits)} primary hits and "
                f"{len(expanded_hits)} expanded hits "
                f"(max depth reached={int(traversal_summary.get('max_depth_reached') or 0)})."
            ),
            "effect_on_work": (
                f"Recorded canonical L2 consultation context for {stage} work on `{topic_slug}` "
                "so later review can inspect the exact retrieval basis."
            ),
            "outcome": "candidate_narrowed" if primary_hits or expanded_hits else "no_change",
            "projection_paths": [
                relativize(dashboard_path),
                *([relativize(projection_path)] if projection_path is not None else []),
            ],
        },
        "retrieval_summary": traversal_summary,
        "traversal_paths": payload.get("traversal_paths", []),
    }


def hit_to_object_ref(row: dict[str, Any]) -> dict[str, str]:
    object_id = str(row.get("id") or row.get("unit_id") or "")
    object_type = str(row.get("unit_type") or row.get("object_type") or "l2_unit")
    return {
        "id": object_id,
        "layer": "L2",
        "object_type": object_type,
        "path": str(row.get("path") or ""),
        "title": str(row.get("title") or object_id),
        "summary": str(row.get("summary") or f"Retrieved {object_type} {object_id} from canonical L2 memory."),
    }


def requested_unit_types_for_profile(kernel_root: Path, retrieval_profile: str) -> list[str]:
    profiles_path = kernel_root / "canonical" / "retrieval_profiles.json"
    if not profiles_path.exists():
        return []
    payload = json.loads(profiles_path.read_text(encoding="utf-8"))
    preferred_types = ((payload.get("profiles") or {}).get(retrieval_profile) or {}).get("preferred_unit_types") or []
    requested_types: list[str] = []
    seen: set[str] = set()
    for unit_type in preferred_types:
        normalized = str(unit_type or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        requested_types.append(normalized)
    return requested_types
