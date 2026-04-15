from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import jsonschema

from .bundle_support import materialized_default_user_kernel_root
from .topic_truth_root_support import compatibility_projection_path, runtime_root


def _kernel_root(kernel_root: Path | None = None) -> Path:
    if kernel_root is not None:
        return kernel_root
    candidate = Path(__file__).resolve().parents[1]
    if (candidate / "runtime" / "scripts" / "orchestrate_topic.py").exists():
        return candidate
    return materialized_default_user_kernel_root()


def _runtime_topic_root(topic_slug: str, kernel_root: Path | None = None) -> Path:
    return runtime_root(_kernel_root(kernel_root), topic_slug)


def _schema_path(schema_name: str, kernel_root: Path | None = None) -> Path:
    return _kernel_root(kernel_root) / "schemas" / f"{schema_name}.schema.json"


def _read_json(path: Path) -> dict[str, Any]:
    target = path
    if not target.exists():
        compatibility_path = compatibility_projection_path(path)
        if compatibility_path is None or not compatibility_path.exists():
            raise FileNotFoundError(path)
        target = compatibility_path
    return json.loads(target.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(rendered, encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    target = path
    if not target.exists():
        compatibility_path = compatibility_projection_path(path)
        if compatibility_path is None or not compatibility_path.exists():
            return []
        target = compatibility_path
    rows: list[dict[str, Any]] = []
    for raw_line in target.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    rendered = "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(rendered, encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(text, encoding="utf-8")


def _markdown_truth_note(*, artifact_kind: str, title: str, payload: dict[str, Any]) -> str:
    topic_slug = str(payload.get("topic_slug") or "").strip() or "(missing)"
    updated_at = str(payload.get("updated_at") or "").strip() or "(unknown)"
    updated_by = str(payload.get("updated_by") or "").strip() or "(unknown)"
    summary = str(
        payload.get("summary")
        or payload.get("next_action_summary")
        or payload.get("question")
        or payload.get("title")
        or ""
    ).strip()
    lines = [
        "---",
        f"topic_slug: {topic_slug}",
        f"artifact_kind: {artifact_kind}",
        f"updated_at: {updated_at}",
        f"updated_by: {updated_by}",
        "---",
        "",
        f"# {title}",
        "",
    ]
    if summary:
        lines.extend(["## Summary", "", summary, ""])
    lines.extend(
        [
            "## Structured Fields",
            "",
            "```json",
            json.dumps(payload, ensure_ascii=True, indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


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


def _transition_history_paths(topic_slug: str, kernel_root: Path | None = None) -> dict[str, Path]:
    root = _runtime_topic_root(topic_slug, kernel_root)
    return {
        "log": root / "transition_history.jsonl",
        "json": root / "transition_history.json",
        "note": root / "transition_history.md",
    }


def _layer_rank(layer: str) -> int:
    normalized = str(layer or "").strip().upper()
    if normalized == "L2_AUTO":
        return 2
    match = re.match(r"^L(?P<rank>\d+)$", normalized)
    if match:
        return int(match.group("rank"))
    return -1


def _transition_kind(from_layer: str, to_layer: str) -> str:
    from_rank = _layer_rank(from_layer)
    to_rank = _layer_rank(to_layer)
    if from_rank >= 0 and to_rank >= 0:
        if to_rank > from_rank:
            return "forward_transition"
        if to_rank < from_rank:
            return "backedge_transition"
    return "boundary_hold"


def _normalize_transition_row(payload: dict[str, Any]) -> dict[str, Any]:
    from_layer = str(payload.get("from_layer") or "").strip() or "unknown"
    to_layer = str(payload.get("to_layer") or "").strip() or from_layer
    transition_kind = str(payload.get("transition_kind") or "").strip() or _transition_kind(from_layer, to_layer)
    evidence_refs = [
        str(item).strip()
        for item in (payload.get("evidence_refs") or [])
        if str(item).strip()
    ]
    transition_id = str(payload.get("transition_id") or "").strip()
    if not transition_id:
        transition_id = (
            f"transition:{_slugify(payload.get('topic_slug') or '')}:"
            f"{_slugify(payload.get('event_kind') or '')}:"
            f"{_slugify(payload.get('run_id') or '')}:"
            f"{_slugify(from_layer)}-to-{_slugify(to_layer)}:"
            f"{_slugify(payload.get('reason') or '')}"
        )
    return {
        "transition_id": transition_id,
        "topic_slug": str(payload.get("topic_slug") or "").strip(),
        "run_id": str(payload.get("run_id") or "").strip(),
        "event_kind": str(payload.get("event_kind") or "").strip() or "runtime_transition",
        "from_layer": from_layer,
        "to_layer": to_layer,
        "transition_kind": transition_kind,
        "reason": str(payload.get("reason") or "").strip() or "No transition reason was recorded.",
        "evidence_refs": evidence_refs,
        "candidate_id": str(payload.get("candidate_id") or "").strip(),
        "recorded_at": str(payload.get("recorded_at") or "").strip(),
        "recorded_by": str(payload.get("recorded_by") or "").strip() or "aitp",
    }


def _transition_history_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    transition_count = len(rows)
    forward_rows = [row for row in rows if row.get("transition_kind") == "forward_transition"]
    backtrack_rows = [row for row in rows if row.get("transition_kind") == "backedge_transition"]
    hold_rows = [row for row in rows if row.get("transition_kind") == "boundary_hold"]
    latest_transition = rows[-1] if rows else {}
    latest_demotion = backtrack_rows[-1] if backtrack_rows else {}
    return {
        "status": "recorded" if rows else "empty",
        "transition_count": transition_count,
        "forward_count": len(forward_rows),
        "backtrack_count": len(backtrack_rows),
        "hold_count": len(hold_rows),
        "demotion_count": len(backtrack_rows),
        "latest_transition": latest_transition,
        "latest_demotion": latest_demotion,
        "rows": rows,
    }


def _render_transition_history_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Transition history",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Transition count: `{payload.get('transition_count') or 0}`",
        f"- Forward count: `{payload.get('forward_count') or 0}`",
        f"- Backtrack count: `{payload.get('backtrack_count') or 0}`",
        f"- Hold count: `{payload.get('hold_count') or 0}`",
        "",
        "## Latest transition",
        "",
    ]
    latest_transition = payload.get("latest_transition") or {}
    if latest_transition:
        lines.extend(
            [
                f"- Event: `{latest_transition.get('event_kind') or '(missing)'}`",
                f"- From: `{latest_transition.get('from_layer') or '(missing)'}`",
                f"- To: `{latest_transition.get('to_layer') or '(missing)'}`",
                f"- Kind: `{latest_transition.get('transition_kind') or '(missing)'}`",
                f"- Reason: {latest_transition.get('reason') or '(missing)'}",
                f"- Recorded at: `{latest_transition.get('recorded_at') or '(missing)'}`",
            ]
        )
    else:
        lines.append("- (none)")
    lines.extend(["", "## Demotion / backtrack history", ""])
    latest_demotion = payload.get("latest_demotion") or {}
    if latest_demotion:
        lines.append(
            f"- Latest demotion: `{latest_demotion.get('from_layer') or '(missing)'}` -> `{latest_demotion.get('to_layer') or '(missing)'}` because {latest_demotion.get('reason') or '(missing)'}"
        )
    else:
        lines.append("- (none)")
    lines.extend(["", "## Transition rows", ""])
    for row in payload.get("rows") or []:
        lines.append(
            f"- `{row.get('event_kind') or '(missing)'}` `{row.get('from_layer') or '(missing)'}` -> `{row.get('to_layer') or '(missing)'}` ({row.get('transition_kind') or '(missing)'})"
        )
        lines.append(f"  reason: {row.get('reason') or '(missing)'}")
        lines.append(f"  evidence: `{', '.join(row.get('evidence_refs') or []) or '(none)'}`")
    if not payload.get("rows"):
        lines.append("- (none)")
    return "\n".join(lines) + "\n"


def load_transition_history(
    topic_slug: str,
    *,
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    paths = _transition_history_paths(topic_slug, kernel_root)
    payload = _read_json(paths["json"]) if paths["json"].exists() else None
    if isinstance(payload, dict):
        return payload
    return {
        "topic_slug": topic_slug,
        "status": "empty",
        "transition_count": 0,
        "forward_count": 0,
        "backtrack_count": 0,
        "hold_count": 0,
        "demotion_count": 0,
        "latest_transition": {},
        "latest_demotion": {},
        "rows": [],
        "log_path": str(paths["log"]),
        "path": str(paths["json"]),
        "note_path": str(paths["note"]),
    }


def append_transition_history(
    topic_slug: str,
    payload: dict[str, Any],
    *,
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    normalized = _normalize_transition_row({**payload, "topic_slug": topic_slug})
    paths = _transition_history_paths(topic_slug, kernel_root)
    rows = _read_jsonl(paths["log"])
    if not any(str(row.get("transition_id") or "") == normalized["transition_id"] for row in rows):
        rows.append(normalized)
        _write_jsonl(paths["log"], rows)
    summary = {
        "topic_slug": topic_slug,
        **_transition_history_summary(rows),
        "log_path": str(paths["log"]),
        "path": str(paths["json"]),
        "note_path": str(paths["note"]),
    }
    _write_json(paths["json"], summary)
    _write_text(paths["note"], _render_transition_history_markdown(summary))
    return {
        "transition_history": summary,
        "log_path": str(paths["log"]),
        "path": str(paths["json"]),
        "note_path": str(paths["note"]),
    }


def write_topic_synopsis(
    topic_slug: str,
    payload: dict[str, Any],
    *,
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    _validate("topic-synopsis", payload, kernel_root)
    path = _runtime_topic_root(topic_slug, kernel_root) / "topic_synopsis.json"
    _write_json(path, payload)
    _write_text(
        path.with_suffix(".md"),
        _markdown_truth_note(
            artifact_kind="topic_synopsis",
            title="Topic Synopsis",
            payload=payload,
        ),
    )
    return {"topic_synopsis": payload, "path": str(path)}


def write_pending_decisions_projection(
    topic_slug: str,
    payload: dict[str, Any],
    *,
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    path = _runtime_topic_root(topic_slug, kernel_root) / "pending_decisions.json"
    _write_json(path, payload)
    _write_text(
        path.with_suffix(".md"),
        _markdown_truth_note(
            artifact_kind="pending_decisions",
            title="Pending Decisions",
            payload=payload,
        ),
    )
    return {"pending_decisions": payload, "path": str(path)}


def write_promotion_readiness_projection(
    topic_slug: str,
    payload: dict[str, Any],
    *,
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    path = _runtime_topic_root(topic_slug, kernel_root) / "promotion_readiness.json"
    _write_json(path, payload)
    _write_text(
        path.with_suffix(".md"),
        _markdown_truth_note(
            artifact_kind="promotion_readiness",
            title="Promotion Readiness",
            payload=payload,
        ),
    )
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
