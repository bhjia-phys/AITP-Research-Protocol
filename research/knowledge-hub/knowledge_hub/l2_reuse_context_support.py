from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .l2_compiler import materialize_obsidian_l2_mirror
from .l2_graph import consult_canonical_l2
from .topic_truth_root_support import compatibility_projection_path


_IDEA_UNIT_TYPES = {
    "concept",
    "physical_picture",
    "claim_card",
    "validation_pattern",
    "warning_note",
    "negative_result",
    "bridge",
}

_PLAN_UNIT_TYPES = _IDEA_UNIT_TYPES | {
    "method",
    "workflow",
    "derivation_object",
    "proof_fragment",
    "example_card",
    "topic_skill_projection",
}
_REUSE_CONTEXT_PROFILE_DEFAULTS = {
    "idea_reuse_context": {
        "retrieval_profile": "l3_idea_reuse_quick",
        "fallback_unit_types": _IDEA_UNIT_TYPES,
        "fallback_max_primary_hits": 4,
    },
    "plan_reuse_context": {
        "retrieval_profile": "l3_plan_reuse_standard",
        "fallback_unit_types": _PLAN_UNIT_TYPES,
        "fallback_max_primary_hits": 6,
    },
}


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    compatibility = compatibility_projection_path(path)
    if compatibility is not None and compatibility != path:
        compatibility.parent.mkdir(parents=True, exist_ok=True)
        compatibility.write_text(rendered, encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    compatibility = compatibility_projection_path(path)
    if compatibility is not None and compatibility != path:
        compatibility.parent.mkdir(parents=True, exist_ok=True)
        compatibility.write_text(text, encoding="utf-8")


def _reuse_context_paths(service: Any, *, topic_slug: str, context_name: str) -> dict[str, Path]:
    runtime_root = service._runtime_root(topic_slug)
    return {
        "json": runtime_root / f"{context_name}.json",
        "note": runtime_root / f"{context_name}.md",
    }


def _profile_shelf_path(service: Any, *, retrieval_profile: str) -> str:
    profile_path = service.kernel_root / "canonical" / "compiled" / "obsidian_l2" / "profiles" / f"{retrieval_profile}.md"
    if not profile_path.exists():
        materialize_obsidian_l2_mirror(service.kernel_root)
    return service._relativize(profile_path)


def _normalize_canonical_hit(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("id") or row.get("unit_id") or ""),
        "title": str(row.get("title") or ""),
        "summary": str(row.get("summary") or ""),
        "unit_type": str(row.get("unit_type") or row.get("object_type") or ""),
        "path": str(row.get("path") or ""),
        "authority_level": "canonical",
        "topic_link_refs": _topic_link_refs(row),
    }


def _normalize_staged_hit(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("entry_id") or row.get("id") or ""),
        "title": str(row.get("title") or ""),
        "summary": str(row.get("summary") or ""),
        "unit_type": str(row.get("candidate_unit_type") or row.get("entry_kind") or ""),
        "path": str(row.get("path") or ""),
        "authority_level": "non_authoritative_staging",
        "topic_slug": str(row.get("topic_slug") or ""),
    }


def _topic_link_refs(row: dict[str, Any]) -> dict[str, list[str]]:
    provenance = dict(row.get("provenance") or {})
    return {
        "origin_topic_refs": [str(item).strip() for item in (row.get("origin_topic_refs") or provenance.get("origin_topic_refs") or []) if str(item).strip()],
        "validation_receipts": [str(item).strip() for item in (row.get("validation_receipts") or provenance.get("validation_receipts") or provenance.get("l4_checks") or []) if str(item).strip()],
        "reuse_receipts": [str(item).strip() for item in (row.get("reuse_receipts") or provenance.get("reuse_receipts") or provenance.get("l3_runs") or []) if str(item).strip()],
        "related_consultation_refs": [str(item).strip() for item in (row.get("related_consultation_refs") or provenance.get("related_consultation_refs") or []) if str(item).strip()],
    }


def _filter_hits(rows: list[dict[str, Any]], *, allowed_unit_types: set[str], limit: int) -> list[dict[str, Any]]:
    filtered = [
        row
        for row in rows
        if str(row.get("unit_type") or row.get("object_type") or "").strip() in allowed_unit_types
    ]
    if filtered:
        return filtered[:limit]
    return rows[:limit]


def _render_context_hit_section(
    title: str,
    rows: list[dict[str, Any]],
    *,
    predicate,
) -> list[str]:  # type: ignore[no-untyped-def]
    matched = [row for row in rows if predicate(row)]
    lines = [f"## {title}", ""]
    for row in matched:
        lines.append(
            f"- `{row.get('id') or '(missing)'}` type=`{row.get('unit_type') or '(missing)'}` authority=`{row.get('authority_level') or '(missing)'}`"
        )
    if not matched:
        lines.append("- `(none)`")
    lines.append("")
    return lines


def _render_reuse_context_markdown(payload: dict[str, Any]) -> str:
    canonical_hits = list(payload.get("canonical_hits") or [])
    lines = [
        f"# {payload.get('context_name', 'Reuse Context').replace('_', ' ').title()}",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Read depth: `{payload.get('read_depth') or '(missing)'}`",
        f"- Retrieval profile: `{payload.get('retrieval_profile') or '(missing)'}`",
        f"- Profile shelf: `{payload.get('profile_shelf_path') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Query text: `{payload.get('query_text') or '(missing)'}`",
        "",
    ]
    lines.extend(
        _render_context_hit_section(
            "Core Hits",
            canonical_hits,
            predicate=lambda row: str(row.get("unit_type") or "") not in {"warning_note", "workflow", "topic_skill_projection"}
            and not ((row.get("topic_link_refs") or {}).get("reuse_receipts") or []),
        )
    )
    lines.extend(
        _render_context_hit_section(
            "Warnings",
            canonical_hits,
            predicate=lambda row: str(row.get("unit_type") or "") == "warning_note",
        )
    )
    lines.extend(
        _render_context_hit_section(
            "Workflows",
            canonical_hits,
            predicate=lambda row: str(row.get("unit_type") or "") == "workflow",
        )
    )
    lines.extend(
        _render_context_hit_section(
            "Topic Skill Projections",
            canonical_hits,
            predicate=lambda row: str(row.get("unit_type") or "") == "topic_skill_projection",
        )
    )
    lines.extend(
        _render_context_hit_section(
            "Recently Reused Units",
            canonical_hits,
            predicate=lambda row: bool(((row.get("topic_link_refs") or {}).get("reuse_receipts") or [])),
        )
    )
    lines.extend(["## Staged Hints", ""])
    for row in payload.get("staged_hits") or []:
        lines.append(
            f"- `{row.get('id') or '(missing)'}` type=`{row.get('unit_type') or '(missing)'}` authority=`{row.get('authority_level') or '(missing)'}`"
        )
    if not (payload.get("staged_hits") or []):
        lines.append("- `(none)`")
    lines.extend(["", "## Supporting Refs", ""])
    for item in payload.get("supporting_refs") or []:
        lines.append(f"- `{item}`")
    if not (payload.get("supporting_refs") or []):
        lines.append("- `(none)`")
    lines.append("")
    return "\n".join(lines)


def _query_text(
    *,
    selected_pending_action: dict[str, Any] | None,
    research_contract: dict[str, Any],
    validation_contract: dict[str, Any],
    topic_skill_projection: dict[str, Any],
) -> str:
    parts = [
        str((selected_pending_action or {}).get("summary") or "").strip(),
        str(research_contract.get("question") or "").strip(),
        str(validation_contract.get("verification_focus") or "").strip(),
        str(topic_skill_projection.get("summary") or "").strip(),
    ]
    return " ".join(item for item in parts if item)


def _supporting_refs(
    service: Any,
    *,
    topic_slug: str,
    latest_run_id: str | None,
    topic_skill_projection: dict[str, Any],
) -> list[str]:
    refs = []
    note_path = str(topic_skill_projection.get("note_path") or "").strip()
    if note_path:
        refs.append(note_path)
    if latest_run_id:
        consultation_log = service._feedback_run_root(topic_slug, latest_run_id) / "l2_consultation_log.jsonl"
        if consultation_log.exists():
            refs.append(service._relativize(consultation_log))
    return refs


def _canonical_index_rows(service: Any) -> dict[str, dict[str, Any]]:
    index_path = service.kernel_root / "canonical" / "index.jsonl"
    rows: dict[str, dict[str, Any]] = {}
    if not index_path.exists():
        return rows
    for raw_line in index_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        row = json.loads(line)
        unit_id = str(row.get("id") or row.get("unit_id") or "").strip()
        if unit_id:
            rows[unit_id] = row
    return rows


def _projection_seed_rows(
    service: Any,
    *,
    topic_skill_projection: dict[str, Any],
    allowed_unit_types: set[str],
    limit: int,
) -> list[dict[str, Any]]:
    index_rows = _canonical_index_rows(service)
    seed_ids = [
        str(topic_skill_projection.get("intended_l2_target") or "").strip(),
        str(topic_skill_projection.get("id") or "").strip(),
    ]
    queue: list[tuple[str, int]] = [(unit_id, 0) for unit_id in seed_ids if unit_id]
    visited: set[str] = set()
    seeded_rows: list[dict[str, Any]] = []
    added_ids: set[str] = set()
    while queue and len(seeded_rows) < limit:
        unit_id, depth = queue.pop(0)
        if unit_id in visited:
            continue
        visited.add(unit_id)
        row = index_rows.get(unit_id)
        if row is None:
            continue
        unit_type = str(row.get("unit_type") or row.get("object_type") or "").strip()
        if unit_type in allowed_unit_types and unit_id not in added_ids:
            seeded_rows.append(row)
            added_ids.add(unit_id)
        if depth >= 2:
            continue
        for neighbor_id in [
            str(item).strip()
            for item in list(row.get("dependencies") or []) + list(row.get("related_units") or [])
            if str(item).strip()
        ]:
            if neighbor_id not in visited:
                queue.append((neighbor_id, depth + 1))
    return seeded_rows


def _merge_canonical_rows(
    primary_rows: list[dict[str, Any]],
    seeded_rows: list[dict[str, Any]],
    *,
    limit: int,
    allowed_unit_types: set[str],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in primary_rows + seeded_rows:
        unit_id = str(row.get("id") or row.get("unit_id") or "").strip()
        unit_type = str(row.get("unit_type") or row.get("object_type") or "").strip()
        if not unit_id or unit_id in seen or unit_type not in allowed_unit_types:
            continue
        seen.add(unit_id)
        merged.append(row)
        if len(merged) >= limit:
            break
    return merged


def _reuse_profile_settings(
    service: Any,
    *,
    context_name: str,
) -> tuple[str, set[str], int]:
    defaults = _REUSE_CONTEXT_PROFILE_DEFAULTS[context_name]
    desired_profile = str(defaults["retrieval_profile"])
    profiles = ((json.loads((service.kernel_root / "canonical" / "retrieval_profiles.json").read_text(encoding="utf-8"))).get("profiles") or {}) if (service.kernel_root / "canonical" / "retrieval_profiles.json").exists() else {}
    profile = dict(profiles.get(desired_profile) or {})
    if not profile:
        return (
            "l3_candidate_formation",
            set(defaults["fallback_unit_types"]),
            int(defaults["fallback_max_primary_hits"]),
        )
    preferred_unit_types = {
        str(item).strip()
        for item in (profile.get("preferred_unit_types") or [])
        if str(item).strip()
    } or set(defaults["fallback_unit_types"])
    return (
        desired_profile,
        preferred_unit_types,
        int(profile.get("max_primary_hits") or defaults["fallback_max_primary_hits"]),
    )


def _materialize_single_context(
    service: Any,
    *,
    topic_slug: str,
    context_name: str,
    read_depth: str,
    updated_by: str,
    selected_pending_action: dict[str, Any] | None,
    research_contract: dict[str, Any],
    validation_contract: dict[str, Any],
    topic_skill_projection: dict[str, Any],
    latest_run_id: str | None,
) -> dict[str, Any]:
    retrieval_profile, allowed_unit_types, max_primary_hits = _reuse_profile_settings(
        service,
        context_name=context_name,
    )
    query_text = _query_text(
        selected_pending_action=selected_pending_action,
        research_contract=research_contract,
        validation_contract=validation_contract,
        topic_skill_projection=topic_skill_projection,
    )
    try:
        consult_payload = consult_canonical_l2(
            service.kernel_root,
            query_text=query_text,
            retrieval_profile=retrieval_profile,
            max_primary_hits=max_primary_hits,
            include_staging=True,
            topic_slug=topic_slug,
        )
    except ValueError:
        consult_payload = {
            "primary_hits": [],
            "expanded_hits": [],
            "staged_hits": [],
        }
    canonical_rows = [
        _normalize_canonical_hit(row)
        for row in _merge_canonical_rows(
            _filter_hits(
                list(consult_payload.get("primary_hits") or []) + list(consult_payload.get("expanded_hits") or []),
                allowed_unit_types=allowed_unit_types,
                limit=max_primary_hits,
            ),
            _projection_seed_rows(
                service,
                topic_skill_projection=topic_skill_projection,
                allowed_unit_types=allowed_unit_types,
                limit=max_primary_hits,
            ),
            limit=max_primary_hits,
            allowed_unit_types=allowed_unit_types,
        )
    ]
    staged_rows = [
        _normalize_staged_hit(row)
        for row in list(consult_payload.get("staged_hits") or [])[:max_primary_hits]
    ]
    payload = {
        "context_version": 1,
        "context_name": context_name,
        "topic_slug": topic_slug,
        "read_depth": read_depth,
        "retrieval_profile": retrieval_profile,
        "profile_shelf_path": _profile_shelf_path(service, retrieval_profile=retrieval_profile),
        "status": "ready" if canonical_rows or staged_rows else "empty",
        "query_text": query_text,
        "canonical_hits": canonical_rows,
        "staged_hits": staged_rows,
        "supporting_refs": _supporting_refs(
            service,
            topic_slug=topic_slug,
            latest_run_id=latest_run_id,
            topic_skill_projection=topic_skill_projection,
        ),
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    paths = _reuse_context_paths(service, topic_slug=topic_slug, context_name=context_name)
    _write_json(paths["json"], payload)
    _write_text(paths["note"], _render_reuse_context_markdown(payload) + "\n")
    return {
        **payload,
        "path": service._relativize(paths["json"]),
        "note_path": service._relativize(paths["note"]),
    }


def materialize_reuse_contexts(
    service: Any,
    *,
    topic_slug: str,
    updated_by: str,
    selected_pending_action: dict[str, Any] | None,
    research_contract: dict[str, Any],
    validation_contract: dict[str, Any],
    topic_skill_projection: dict[str, Any],
    latest_run_id: str | None,
) -> dict[str, dict[str, Any]]:
    idea = _materialize_single_context(
        service,
        topic_slug=topic_slug,
        context_name="idea_reuse_context",
        read_depth="quick",
        updated_by=updated_by,
        selected_pending_action=selected_pending_action,
        research_contract=research_contract,
        validation_contract=validation_contract,
        topic_skill_projection=topic_skill_projection,
        latest_run_id=latest_run_id,
    )
    plan = _materialize_single_context(
        service,
        topic_slug=topic_slug,
        context_name="plan_reuse_context",
        read_depth="standard",
        updated_by=updated_by,
        selected_pending_action=selected_pending_action,
        research_contract=research_contract,
        validation_contract=validation_contract,
        topic_skill_projection=topic_skill_projection,
        latest_run_id=latest_run_id,
    )
    return {
        "idea": idea,
        "plan": plan,
    }
