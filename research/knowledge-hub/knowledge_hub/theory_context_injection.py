from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


THEORY_CONTEXT_SESSION_TTL_SECONDS = 3600


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _now() -> datetime:
    return datetime.now().astimezone()


def _slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "aitp-topic"


def _parse_datetime(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _dedupe_strings(values: list[str] | None) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        normalized = str(value or "").strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return deduped


def _resolve_artifact_path(service: Any, path_value: str | None) -> Path | None:
    text = str(path_value or "").strip()
    if not text:
        return None
    path = Path(text)
    if path.is_absolute():
        return path
    return (service.kernel_root / path).resolve()


def _relativize(service: Any, path: Path | None) -> str:
    if path is None:
        return ""
    return service._relativize(path)


def _theory_target_paths(service: Any, *, topic_slug: str) -> list[str]:
    paths: list[str] = []
    for candidate in (
        service._validation_review_bundle_paths(topic_slug)["note"],
        service._statement_compilation_active_paths(topic_slug)["note"],
        service._lean_bridge_active_paths(topic_slug)["note"],
        service._topic_skill_projection_paths(topic_slug)["note"],
    ):
        if candidate.exists():
            paths.append(_relativize(service, candidate))
    return _dedupe_strings(paths)


def _theory_context_is_active(
    *,
    lane: str,
    validation_review_bundle: dict[str, Any],
    statement_compilation: dict[str, Any],
    lean_bridge: dict[str, Any],
    topic_skill_projection: dict[str, Any],
    selected_pending_action: dict[str, Any] | None,
) -> bool:
    if lane == "formal_theory":
        return True
    if str(validation_review_bundle.get("primary_review_kind") or "").strip() == "formal_theory_review":
        return True
    if str(validation_review_bundle.get("validation_mode") or "").strip() == "formal":
        return True
    if str(statement_compilation.get("status") or "").strip() not in {"", "idle"}:
        return True
    if str(lean_bridge.get("status") or "").strip() not in {"", "idle"}:
        return True
    action_summary = str((selected_pending_action or {}).get("summary") or "")
    return bool(re.search(r"(theorem|proof|formal|lean|lemma|notation|derivation)", action_summary, flags=re.IGNORECASE))


def _render_fragment_note(
    *,
    fragment_id: str,
    kind: str,
    topic_slug: str,
    candidate_id: str | None,
    summary: str,
    source_paths: list[str],
    target_paths: list[str],
    detail_lines: list[str],
) -> str:
    lines = [
        "# Theory context fragment",
        "",
        f"- Fragment id: `{fragment_id}`",
        f"- Kind: `{kind}`",
        f"- Topic slug: `{topic_slug}`",
        f"- Candidate id: `{candidate_id or '(none)'}`",
        "",
        summary,
        "",
        "## Target paths",
        "",
    ]
    for item in target_paths or ["(none)"]:
        lines.append(f"- `{item}`" if item != "(none)" else "- (none)")
    lines.extend(["", "## Source paths", ""])
    for item in source_paths or ["(none)"]:
        lines.append(f"- `{item}`" if item != "(none)" else "- (none)")
    if detail_lines:
        lines.extend(["", "## Details", ""])
        lines.extend(detail_lines)
    return "\n".join(lines) + "\n"


def _build_notation_fragment(
    service: Any,
    *,
    topic_slug: str,
    candidate_id: str,
    notation_table_path: Path,
    target_paths: list[str],
) -> dict[str, Any] | None:
    notation_payload = _read_json(notation_table_path) or {}
    bindings = [
        {
            "symbol": str(row.get("symbol") or "").strip(),
            "meaning": str(row.get("meaning") or "").strip(),
        }
        for row in notation_payload.get("bindings") or []
        if str(row.get("symbol") or "").strip() and str(row.get("meaning") or "").strip()
    ]
    if not bindings:
        return None

    binding_preview = "; ".join(f"{row['symbol']} = {row['meaning']}" for row in bindings[:4])
    fragment_id = f"theory-context:notation:{_slugify(topic_slug)}:{_slugify(candidate_id)}"
    fragment_root = service._runtime_root(topic_slug) / "context_fragments"
    note_path = fragment_root / f"{_slugify(fragment_id)}.md"
    json_path = fragment_root / f"{_slugify(fragment_id)}.json"
    source_paths = [_relativize(service, notation_table_path)]
    payload = {
        "fragment_id": fragment_id,
        "kind": "notation_bindings",
        "summary": f"Notation bindings for the bounded theorem packet: {binding_preview}.",
        "path": _relativize(service, note_path),
        "json_path": _relativize(service, json_path),
        "source_paths": source_paths,
        "target_paths": target_paths,
        "binding_count": len(bindings),
    }
    _write_json(json_path, {**payload, "bindings": bindings})
    _write_text(
        note_path,
        _render_fragment_note(
            fragment_id=fragment_id,
            kind="notation_bindings",
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            summary=payload["summary"],
            source_paths=source_paths,
            target_paths=target_paths,
            detail_lines=[f"- `{row['symbol']}` -> `{row['meaning']}`" for row in bindings],
        ),
    )
    return payload


def _build_prerequisite_fragment(
    service: Any,
    *,
    topic_slug: str,
    candidate_id: str,
    formal_theory_review_path: Path,
    prerequisite_closure_review_path: Path,
    target_paths: list[str],
) -> dict[str, Any] | None:
    formal_payload = _read_json(formal_theory_review_path) or {}
    prerequisite_payload = _read_json(prerequisite_closure_review_path) or {}
    prerequisite_status = str(
        formal_payload.get("prerequisite_closure_status")
        or prerequisite_payload.get("status")
        or "unknown"
    ).strip()
    lean_prerequisites = _dedupe_strings(
        list(formal_payload.get("lean_prerequisite_ids") or [])
        + list(prerequisite_payload.get("lean_prerequisite_ids") or [])
    )
    blockers = _dedupe_strings(
        list(formal_payload.get("formalization_blockers") or [])
        + list(prerequisite_payload.get("blocking_reasons") or [])
    )
    notes = _dedupe_strings(
        [
            str(formal_payload.get("prerequisite_notes") or "").strip(),
            str(prerequisite_payload.get("notes") or "").strip(),
        ]
    )
    if not (prerequisite_status or lean_prerequisites or blockers or notes):
        return None

    fragment_id = f"theory-context:prerequisite:{_slugify(topic_slug)}:{_slugify(candidate_id)}"
    fragment_root = service._runtime_root(topic_slug) / "context_fragments"
    note_path = fragment_root / f"{_slugify(fragment_id)}.md"
    json_path = fragment_root / f"{_slugify(fragment_id)}.json"
    source_paths = _dedupe_strings(
        [
            _relativize(service, formal_theory_review_path) if formal_theory_review_path.exists() else "",
            _relativize(service, prerequisite_closure_review_path) if prerequisite_closure_review_path.exists() else "",
        ]
    )
    summary = f"Prerequisite closure status for the bounded theorem packet: `{prerequisite_status or 'unknown'}`."
    if lean_prerequisites:
        summary += f" Prerequisites: {', '.join(lean_prerequisites[:4])}."
    if blockers:
        summary += f" Blockers: {blockers[0]}."
    payload = {
        "fragment_id": fragment_id,
        "kind": "prerequisite_closure",
        "summary": summary,
        "path": _relativize(service, note_path),
        "json_path": _relativize(service, json_path),
        "source_paths": source_paths,
        "target_paths": target_paths,
        "prerequisite_status": prerequisite_status,
        "prerequisite_count": len(lean_prerequisites),
    }
    _write_json(
        json_path,
        {
            **payload,
            "lean_prerequisite_ids": lean_prerequisites,
            "blocking_reasons": blockers,
            "notes": notes,
        },
    )
    detail_lines = [
        f"- Status: `{prerequisite_status or 'unknown'}`",
        f"- Lean prerequisites: `{', '.join(lean_prerequisites) or '(none)'}`",
        f"- Blocking reasons: `{'; '.join(blockers) or '(none)'}`",
    ]
    if notes:
        detail_lines.append(f"- Notes: `{notes[0]}`")
    _write_text(
        note_path,
        _render_fragment_note(
            fragment_id=fragment_id,
            kind="prerequisite_closure",
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            summary=summary,
            source_paths=source_paths,
            target_paths=target_paths,
            detail_lines=detail_lines,
        ),
    )
    return payload


def _build_l2_fragment(
    service: Any,
    *,
    topic_slug: str,
    topic_skill_projection: dict[str, Any],
    target_paths: list[str],
) -> dict[str, Any] | None:
    if str(topic_skill_projection.get("status") or "").strip() != "available":
        return None
    projection_note_path = str(topic_skill_projection.get("note_path") or "").strip()
    projection_json_path = str(topic_skill_projection.get("path") or "").strip()
    if not projection_note_path and not projection_json_path:
        return None

    fragment_id = f"theory-context:l2:{_slugify(topic_slug)}"
    fragment_root = service._runtime_root(topic_slug) / "context_fragments"
    note_path = fragment_root / f"{_slugify(fragment_id)}.md"
    json_path = fragment_root / f"{_slugify(fragment_id)}.json"
    source_paths = _dedupe_strings([projection_json_path, projection_note_path])
    required_first_routes = _dedupe_strings(list(topic_skill_projection.get("required_first_routes") or []))
    summary = (
        f"Relevant reusable L2 unit is pinned through `{topic_skill_projection.get('intended_l2_target') or topic_skill_projection.get('id') or 'topic_skill_projection'}`. "
        f"{str(topic_skill_projection.get('summary') or '').strip()}"
    ).strip()
    payload = {
        "fragment_id": fragment_id,
        "kind": "relevant_l2_units",
        "summary": summary,
        "path": _relativize(service, note_path),
        "json_path": _relativize(service, json_path),
        "source_paths": source_paths,
        "target_paths": target_paths,
        "unit_count": 1,
    }
    _write_json(
        json_path,
        {
            **payload,
            "intended_l2_target": str(topic_skill_projection.get("intended_l2_target") or ""),
            "required_first_reads": _dedupe_strings(list(topic_skill_projection.get("required_first_reads") or [])),
            "required_first_routes": required_first_routes,
        },
    )
    _write_text(
        note_path,
        _render_fragment_note(
            fragment_id=fragment_id,
            kind="relevant_l2_units",
            topic_slug=topic_slug,
            candidate_id=str(topic_skill_projection.get("candidate_id") or "").strip() or None,
            summary=summary,
            source_paths=source_paths,
            target_paths=target_paths,
            detail_lines=[
                f"- Intended L2 target: `{topic_skill_projection.get('intended_l2_target') or '(missing)'}`",
                f"- Required first reads: `{', '.join(topic_skill_projection.get('required_first_reads') or []) or '(none)'}`",
                f"- Required first routes: `{'; '.join(required_first_routes) or '(none)'}`",
            ],
        ),
    )
    return payload


def build_theory_context_injection(
    service: Any,
    *,
    topic_slug: str,
    latest_run_id: str | None,
    lane: str,
    validation_review_bundle: dict[str, Any],
    statement_compilation: dict[str, Any],
    lean_bridge: dict[str, Any],
    topic_skill_projection: dict[str, Any],
    selected_pending_action: dict[str, Any] | None,
    candidate_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    runtime_root = service._runtime_root(topic_slug)
    session_state_path = runtime_root / "theory_context_injection.session.json"
    target_paths = _theory_target_paths(service, topic_slug=topic_slug)
    active = _theory_context_is_active(
        lane=lane,
        validation_review_bundle=validation_review_bundle,
        statement_compilation=statement_compilation,
        lean_bridge=lean_bridge,
        topic_skill_projection=topic_skill_projection,
        selected_pending_action=selected_pending_action,
    )
    if not active or not target_paths or not latest_run_id:
        return {
            "status": "inactive",
            "session_ttl_seconds": THEORY_CONTEXT_SESSION_TTL_SECONDS,
            "session_state_path": _relativize(service, session_state_path),
            "active_target_paths": target_paths,
            "fragments": [],
        }

    fragments: list[dict[str, Any]] = []
    candidate_context = service._formal_theory_projection_candidate_context(
        topic_slug=topic_slug,
        run_id=latest_run_id,
        candidate_rows=candidate_rows,
    )
    if candidate_context:
        candidate_id = str(candidate_context.get("candidate_id") or "").strip() or "candidate"
        packet_paths = service._theory_packet_paths(topic_slug, latest_run_id, candidate_id)
        notation_fragment = _build_notation_fragment(
            service,
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            notation_table_path=packet_paths["notation_table"],
            target_paths=target_paths,
        )
        if notation_fragment:
            fragments.append(notation_fragment)
        prerequisite_fragment = _build_prerequisite_fragment(
            service,
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            formal_theory_review_path=packet_paths["formal_theory_review"],
            prerequisite_closure_review_path=packet_paths["prerequisite_closure_review"],
            target_paths=target_paths,
        )
        if prerequisite_fragment:
            fragments.append(prerequisite_fragment)

    l2_fragment = _build_l2_fragment(
        service,
        topic_slug=topic_slug,
        topic_skill_projection=topic_skill_projection,
        target_paths=target_paths,
    )
    if l2_fragment:
        fragments.append(l2_fragment)

    return {
        "status": "active" if fragments else "inactive",
        "session_ttl_seconds": THEORY_CONTEXT_SESSION_TTL_SECONDS,
        "session_state_path": _relativize(service, session_state_path),
        "active_target_paths": target_paths,
        "fragments": fragments,
    }


def apply_theory_context_session_dedup(
    service: Any,
    *,
    topic_slug: str,
    payload: dict[str, Any] | None,
    updated_by: str,
) -> dict[str, Any]:
    base_payload = dict(payload or {})
    ttl_seconds = int(base_payload.get("session_ttl_seconds") or THEORY_CONTEXT_SESSION_TTL_SECONDS)
    session_state_path = _resolve_artifact_path(service, str(base_payload.get("session_state_path") or "")) or (
        service._runtime_root(topic_slug) / "theory_context_injection.session.json"
    )
    fragments = [dict(row) for row in base_payload.get("fragments") or [] if isinstance(row, dict)]
    if str(base_payload.get("status") or "").strip() != "active" or not fragments:
        return {
            **base_payload,
            "session_state_path": _relativize(service, session_state_path),
            "injected_now_paths": [],
            "suppressed_paths": [],
        }

    now = _now()
    session_state = _read_json(session_state_path) or {}
    prior_fragments = session_state.get("fragments") or {}
    resolved_fragments: list[dict[str, Any]] = []
    persisted_fragments: dict[str, Any] = {}
    injected_now_paths: list[str] = []
    suppressed_paths: list[str] = []

    for fragment in fragments:
        fragment_id = str(fragment.get("fragment_id") or "").strip()
        if not fragment_id:
            continue
        previous = prior_fragments.get(fragment_id) if isinstance(prior_fragments, dict) else None
        previous_until = _parse_datetime((previous or {}).get("dedup_until"))
        if previous_until is not None and previous_until > now:
            delivery_status = "suppressed_recently_injected"
            dedup_until = previous_until.isoformat(timespec="seconds")
            suppressed_paths.append(str(fragment.get("path") or "").strip())
            delivery_count = int((previous or {}).get("delivery_count") or 0)
            last_injected_at = str((previous or {}).get("last_injected_at") or "")
        else:
            delivery_status = "inject_now"
            dedup_until = (now + timedelta(seconds=ttl_seconds)).isoformat(timespec="seconds")
            injected_now_paths.append(str(fragment.get("path") or "").strip())
            delivery_count = int((previous or {}).get("delivery_count") or 0) + 1
            last_injected_at = now.isoformat(timespec="seconds")
        persisted_fragments[fragment_id] = {
            "fragment_id": fragment_id,
            "last_injected_at": last_injected_at,
            "dedup_until": dedup_until,
            "delivery_count": delivery_count,
        }
        resolved_fragments.append(
            {
                **fragment,
                "delivery_status": delivery_status,
                "dedup_until": dedup_until,
            }
        )

    _write_json(
        session_state_path,
        {
            "topic_slug": topic_slug,
            "updated_at": now.isoformat(timespec="seconds"),
            "updated_by": updated_by,
            "session_ttl_seconds": ttl_seconds,
            "fragments": persisted_fragments,
        },
    )
    return {
        **base_payload,
        "session_state_path": _relativize(service, session_state_path),
        "updated_at": now.isoformat(timespec="seconds"),
        "updated_by": updated_by,
        "fragments": resolved_fragments,
        "injected_now_paths": _dedupe_strings(injected_now_paths),
        "suppressed_paths": _dedupe_strings(suppressed_paths),
    }
