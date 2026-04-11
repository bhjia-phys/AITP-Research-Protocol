from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def prune_compat_surfaces(
    service: Any,
    *,
    topic_slug: str,
    updated_by: str,
) -> dict[str, Any]:
    runtime_root = service._runtime_root(topic_slug)
    topic_state_path = runtime_root / "topic_state.json"
    if not topic_state_path.exists():
        raise FileNotFoundError(f"Runtime state missing for topic {topic_slug}")

    primary_rows = [
        {
            "surface": "topic_dashboard",
            "path": service._relativize(runtime_root / "topic_dashboard.md"),
            "exists": (runtime_root / "topic_dashboard.md").exists(),
        },
        {
            "surface": "runtime_protocol",
            "path": service._relativize(runtime_root / "runtime_protocol.generated.md"),
            "exists": (runtime_root / "runtime_protocol.generated.md").exists(),
        },
    ]
    blocking_rows = [
        {"surface": row["surface"], "path": row["path"], "reason": "primary_surface_missing"}
        for row in primary_rows
        if not row["exists"]
    ]
    if blocking_rows:
        return {
            "status": "blocked_missing_primary_surfaces",
            "topic_slug": topic_slug,
            "updated_by": updated_by,
            "removed_surfaces": [],
            "skipped_surfaces": [],
            "blocking_surfaces": blocking_rows,
        }

    candidates = [
        ("agent_brief", runtime_root / "agent_brief.md"),
        ("operator_console", runtime_root / "operator_console.md"),
    ]

    current_topic_json = service._current_topic_memory_paths()["json"]
    current_topic_note = service._current_topic_memory_paths()["note"]
    current_payload = _read_json(current_topic_json) or {}
    if str(current_payload.get("topic_slug") or "").strip() == topic_slug:
        candidates.append(("current_topic_note", current_topic_note))

    removed_rows: list[dict[str, str]] = []
    skipped_rows: list[dict[str, str]] = []
    for surface, path in candidates:
        if path.exists():
            path.unlink()
            removed_rows.append({"surface": surface, "path": service._relativize(path)})
        else:
            skipped_rows.append({"surface": surface, "path": service._relativize(path), "reason": "missing"})

    return {
        "status": "pruned" if removed_rows else "no_compat_surfaces_present",
        "topic_slug": topic_slug,
        "updated_by": updated_by,
        "removed_surfaces": removed_rows,
        "skipped_surfaces": skipped_rows,
        "blocking_surfaces": [],
        "primary_surfaces": [
            {"surface": row["surface"], "path": row["path"]}
            for row in primary_rows
        ],
    }
