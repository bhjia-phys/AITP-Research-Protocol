from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


_KIND_DIRS = {
    "tool": "tools",
    "server": "servers",
    "environment": "environments",
    "workflow": "workflows",
}


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _slugify(text: str) -> str:
    lowered = str(text or "").lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "capability"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def capability_plane_root(kernel_root: Path) -> Path:
    return kernel_root / "runtime" / "capabilities"


def capability_registry_path(kernel_root: Path) -> Path:
    return capability_plane_root(kernel_root) / "registry.json"


def capability_status_root(kernel_root: Path) -> Path:
    return capability_plane_root(kernel_root) / "status"


def _kind_root(kernel_root: Path, capability_kind: str) -> Path:
    normalized = str(capability_kind or "").strip()
    if normalized not in _KIND_DIRS:
        raise ValueError(f"Unsupported capability kind: {capability_kind}")
    return capability_plane_root(kernel_root) / _KIND_DIRS[normalized]


def capability_card_paths(kernel_root: Path, *, capability_kind: str, capability_id: str) -> dict[str, Path]:
    slug = _slugify(str(capability_id or "").split(":", 1)[-1])
    root = _kind_root(kernel_root, capability_kind)
    return {
        "json": root / f"{capability_kind}--{slug}.json",
        "note": root / f"{capability_kind}--{slug}.md",
    }


def _render_capability_markdown(card: dict[str, Any]) -> str:
    properties = dict(card.get("properties") or {})
    lines = [
        "# Runtime Capability Card",
        "",
        f"- Capability kind: `{card.get('capability_kind') or '(missing)'}`",
        f"- Capability id: `{card.get('capability_id') or '(missing)'}`",
        f"- Status: `{card.get('status') or '(missing)'}`",
        f"- Declaration source: `{card.get('declaration_source') or '(missing)'}`",
        f"- Title: {card.get('title') or '(missing)'}",
        "",
        "## Summary",
        "",
        card.get("summary") or "(missing)",
        "",
        "## Declaration text",
        "",
        card.get("declaration_text") or "(missing)",
        "",
        "## Properties",
        "",
    ]
    if properties:
        for key in sorted(properties):
            lines.append(f"- `{key}`: `{properties[key]}`")
    else:
        lines.append("- `(none)`")
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "This card is runtime capability state, not canonical L2 truth.",
            "",
        ]
    )
    return "\n".join(lines)


def load_runtime_capability_cards(kernel_root: Path) -> list[dict[str, Any]]:
    root = capability_plane_root(kernel_root)
    if not root.exists():
        return []
    cards: list[dict[str, Any]] = []
    for capability_kind, dir_name in _KIND_DIRS.items():
        kind_root = root / dir_name
        if not kind_root.exists():
            continue
        for path in sorted(kind_root.glob("*.json")):
            payload = _read_json(path)
            if not isinstance(payload, dict):
                continue
            card = dict(payload)
            card.setdefault("capability_kind", capability_kind)
            card.setdefault("status", "declared")
            card.setdefault("properties", {})
            card.setdefault("path", str(path.relative_to(kernel_root)).replace("\\", "/"))
            note_path = path.with_suffix(".md")
            card.setdefault(
                "note_path",
                str(note_path.relative_to(kernel_root)).replace("\\", "/"),
            )
            cards.append(card)
    cards.sort(key=lambda row: (str(row.get("capability_kind") or ""), str(row.get("capability_id") or "")))
    return cards


def build_runtime_capability_registry(kernel_root: Path) -> dict[str, Any]:
    cards = load_runtime_capability_cards(kernel_root)
    return {
        "kind": "runtime_capability_registry",
        "registry_version": 1,
        "generated_at": _now_iso(),
        "cards": [
            {
                "capability_kind": str(card.get("capability_kind") or ""),
                "capability_id": str(card.get("capability_id") or ""),
                "title": str(card.get("title") or ""),
                "status": str(card.get("status") or ""),
                "path": str(card.get("path") or ""),
                "note_path": str(card.get("note_path") or ""),
            }
            for card in cards
        ],
    }


def _materialize_runtime_capability_registry(kernel_root: Path) -> dict[str, Any]:
    payload = build_runtime_capability_registry(kernel_root)
    path = capability_registry_path(kernel_root)
    _write_json(path, payload)
    return {
        "payload": payload,
        "path": str(path),
    }


def write_runtime_capability_card(
    kernel_root: Path,
    *,
    capability_kind: str,
    capability_id: str,
    title: str,
    summary: str,
    declaration_source: str,
    properties: dict[str, Any] | None = None,
    declaration_text: str | None = None,
    updated_by: str = "aitp-cli",
) -> dict[str, Any]:
    normalized_kind = str(capability_kind or "").strip()
    normalized_id = str(capability_id or "").strip()
    normalized_title = str(title or "").strip()
    normalized_summary = str(summary or "").strip()
    normalized_source = str(declaration_source or "").strip()
    if not normalized_kind or not normalized_id or not normalized_title or not normalized_summary:
        raise ValueError("capability_kind, capability_id, title, and summary are required")
    paths = capability_card_paths(
        kernel_root,
        capability_kind=normalized_kind,
        capability_id=normalized_id,
    )
    card = {
        "capability_kind": normalized_kind,
        "capability_id": normalized_id,
        "title": normalized_title,
        "summary": normalized_summary,
        "declaration_source": normalized_source or "human_text",
        "declaration_text": str(declaration_text or normalized_summary).strip(),
        "status": "declared",
        "properties": dict(properties or {}),
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "path": str(paths["json"].relative_to(kernel_root)).replace("\\", "/"),
        "note_path": str(paths["note"].relative_to(kernel_root)).replace("\\", "/"),
    }
    _write_json(paths["json"], card)
    _write_text(paths["note"], _render_capability_markdown(card))
    registry = _materialize_runtime_capability_registry(kernel_root)
    return {
        "card": card,
        "json_path": str(paths["json"]),
        "markdown_path": str(paths["note"]),
        "registry_path": registry["path"],
        "registry": registry["payload"],
    }


def record_runtime_capability_declaration(
    kernel_root: Path,
    *,
    capability_kind: str,
    declaration_text: str,
    capability_id: str,
    title: str,
    updated_by: str = "aitp-cli",
) -> dict[str, Any]:
    normalized_text = str(declaration_text or "").strip()
    if not normalized_text:
        raise ValueError("declaration_text is required")
    summary = normalized_text.split(".", 1)[0].strip() or normalized_text
    return write_runtime_capability_card(
        kernel_root,
        capability_kind=capability_kind,
        capability_id=capability_id,
        title=title,
        summary=summary,
        declaration_source="natural_language",
        declaration_text=normalized_text,
        properties={},
        updated_by=updated_by,
    )


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", str(text or "").lower()))


def _score_capability_card(
    card: dict[str, Any],
    *,
    query_terms: set[str],
    lane_terms: set[str],
) -> tuple[float, list[str]]:
    searchable = " ".join(
        [
            str(card.get("title") or ""),
            str(card.get("summary") or ""),
            str(card.get("declaration_text") or ""),
            json.dumps(card.get("properties") or {}, ensure_ascii=True),
        ]
    )
    terms = _tokenize(searchable)
    overlap = sorted(query_terms & terms)
    score = float(len(overlap))
    allowed = {
        str(item).strip().lower()
        for item in ((card.get("properties") or {}).get("allowed_workloads") or [])
        if str(item).strip()
    }
    if allowed & lane_terms:
        score += 3.0
    return score, overlap


def _resource_context_paths(service: Any, *, topic_slug: str) -> dict[str, Path]:
    runtime_root = service._runtime_root(topic_slug)
    return {
        "json": runtime_root / "execution_resource_context.json",
        "note": runtime_root / "execution_resource_context.md",
    }


def _render_execution_resource_context_markdown(payload: dict[str, Any]) -> str:
    recommended_server = payload.get("recommended_server") or {}
    recommended_environment = payload.get("recommended_environment") or {}
    lines = [
        "# Execution Resource Context",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Read depth: `{payload.get('read_depth') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Query text: `{payload.get('query_text') or '(missing)'}`",
        "",
        "## Recommended resources",
        "",
        f"- Server: `{recommended_server.get('capability_id') or '(none)'}`",
        f"- Environment: `{recommended_environment.get('capability_id') or '(none)'}`",
        f"- Tools: `{', '.join(payload.get('recommended_tool_ids') or []) or '(none)'}`",
        "",
        "## Relevant cards",
        "",
    ]
    for row in payload.get("relevant_cards") or []:
        lines.append(
            f"- `{row.get('capability_id') or '(missing)'}` kind=`{row.get('capability_kind') or '(missing)'}` score=`{row.get('score')}`"
        )
    if not (payload.get("relevant_cards") or []):
        lines.append("- `(none)`")
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "Use explicit capability ids in plans instead of free-form resource guesses.",
            "",
        ]
    )
    return "\n".join(lines)


def materialize_execution_resource_context(
    service: Any,
    *,
    topic_slug: str,
    updated_by: str,
    selected_pending_action: dict[str, Any] | None,
    research_contract: dict[str, Any],
    validation_contract: dict[str, Any],
    topic_skill_projection: dict[str, Any],
) -> dict[str, Any]:
    cards = load_runtime_capability_cards(service.kernel_root)
    lane_terms = {
        str(research_contract.get("template_mode") or "").strip().lower(),
        str(research_contract.get("research_mode") or "").strip().lower(),
        str(topic_skill_projection.get("lane") or "").strip().lower(),
    }
    query_text = " ".join(
        item
        for item in [
            str((selected_pending_action or {}).get("summary") or "").strip(),
            str(research_contract.get("question") or "").strip(),
            str(validation_contract.get("verification_focus") or "").strip(),
            str(topic_skill_projection.get("summary") or "").strip(),
        ]
        if item
    )
    query_terms = _tokenize(query_text)
    scored_rows: list[dict[str, Any]] = []
    for card in cards:
        score, overlap = _score_capability_card(
            card,
            query_terms=query_terms,
            lane_terms=lane_terms,
        )
        scored_rows.append(
            {
                **card,
                "score": round(score, 3),
                "matched_terms": overlap,
            }
        )
    scored_rows.sort(
        key=lambda row: (-float(row.get("score") or 0.0), str(row.get("capability_id") or "")),
    )
    relevant_cards = scored_rows[:8]

    def _first_kind(kind: str) -> dict[str, Any]:
        for row in scored_rows:
            if str(row.get("capability_kind") or "") == kind:
                return row
        return {}

    recommended_server = _first_kind("server")
    recommended_environment = _first_kind("environment")
    recommended_tools = [
        row for row in scored_rows if str(row.get("capability_kind") or "") == "tool"
    ][:4]

    payload = {
        "context_version": 1,
        "context_name": "execution_resource_context",
        "topic_slug": topic_slug,
        "read_depth": "standard",
        "status": "ready" if cards else "empty",
        "query_text": query_text,
        "recommended_server": recommended_server,
        "recommended_environment": recommended_environment,
        "recommended_tool_ids": [
            str(row.get("capability_id") or "")
            for row in recommended_tools
            if str(row.get("capability_id") or "").strip()
        ],
        "relevant_cards": relevant_cards,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    paths = _resource_context_paths(service, topic_slug=topic_slug)
    _write_json(paths["json"], payload)
    _write_text(paths["note"], _render_execution_resource_context_markdown(payload) + "\n")
    return {
        **payload,
        "path": service._relativize(paths["json"]),
        "note_path": service._relativize(paths["note"]),
    }
