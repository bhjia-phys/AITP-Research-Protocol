from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


PROFILE_MEMORY_KINDS = ("preference", "working_style", "trajectory", "coordination")


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def collaborator_profile_paths(runtime_root: Path) -> dict[str, Path]:
    return {
        "json": runtime_root / "collaborator_profile.active.json",
        "note": runtime_root / "collaborator_profile.active.md",
    }


def empty_collaborator_profile(*, topic_slug: str, updated_by: str) -> dict[str, Any]:
    return {
        "artifact_kind": "collaborator_profile",
        "topic_slug": topic_slug,
        "status": "absent",
        "preference_count": 0,
        "working_style_count": 0,
        "trajectory_count": 0,
        "coordination_count": 0,
        "preference_summaries": [],
        "working_style_summaries": [],
        "trajectory_summaries": [],
        "coordination_summaries": [],
        "preferred_tags": [],
        "related_topic_slugs": [],
        "memory_ids": [],
        "summary": "No collaborator profile is currently recorded for this topic.",
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }


def load_collaborator_profile(
    runtime_root: Path,
    *,
    topic_slug: str,
    updated_by: str = "aitp-service",
) -> dict[str, Any] | None:
    json_path = collaborator_profile_paths(runtime_root)["json"]
    if not json_path.exists():
        return None
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    payload = {
        **empty_collaborator_profile(topic_slug=topic_slug, updated_by=updated_by),
        **payload,
    }
    payload["topic_slug"] = str(payload.get("topic_slug") or topic_slug)
    return payload


def derive_collaborator_profile(
    self,
    *,
    topic_slug: str,
    updated_by: str,
) -> dict[str, Any]:
    rows = [
        row
        for row in self._load_collaborator_memory_rows()
        if self._collaborator_memory_matches_topic(row, topic_slug)
    ]
    profile_rows = [
        row
        for row in rows
        if str(row.get("memory_kind") or "").strip() in PROFILE_MEMORY_KINDS
    ]
    grouped = {
        kind: [row for row in profile_rows if str(row.get("memory_kind") or "").strip() == kind]
        for kind in PROFILE_MEMORY_KINDS
    }
    preferred_tags = self._dedupe_strings(
        [tag for row in profile_rows for tag in (row.get("tags") or [])]
    )
    related_topics = self._dedupe_strings(
        [slug for row in profile_rows for slug in (row.get("related_topic_slugs") or [])]
    )
    preference_summaries = self._dedupe_strings(
        [str(row.get("summary") or "").strip() for row in grouped["preference"]]
    )
    working_style_summaries = self._dedupe_strings(
        [str(row.get("summary") or "").strip() for row in grouped["working_style"]]
    )
    trajectory_summaries = self._dedupe_strings(
        [str(row.get("summary") or "").strip() for row in grouped["trajectory"]]
    )
    coordination_summaries = self._dedupe_strings(
        [str(row.get("summary") or "").strip() for row in grouped["coordination"]]
    )
    status = "available" if profile_rows else "absent"
    if profile_rows:
        summary = (
            f"{len(grouped['preference'])} preference, {len(grouped['working_style'])} working-style, "
            f"{len(grouped['trajectory'])} trajectory, and {len(grouped['coordination'])} coordination "
            f"signal(s) are recorded for `{topic_slug}`."
        )
        if preference_summaries:
            summary += f" Latest preference: {preference_summaries[0]}"
    else:
        summary = "No collaborator profile is currently recorded for this topic."
    updated_at = (
        str(profile_rows[0].get("recorded_at") or "").strip()
        if profile_rows
        else _now_iso()
    )
    return {
        "artifact_kind": "collaborator_profile",
        "topic_slug": topic_slug,
        "status": status,
        "preference_count": len(grouped["preference"]),
        "working_style_count": len(grouped["working_style"]),
        "trajectory_count": len(grouped["trajectory"]),
        "coordination_count": len(grouped["coordination"]),
        "preference_summaries": preference_summaries,
        "working_style_summaries": working_style_summaries,
        "trajectory_summaries": trajectory_summaries,
        "coordination_summaries": coordination_summaries,
        "preferred_tags": preferred_tags,
        "related_topic_slugs": related_topics,
        "memory_ids": self._dedupe_strings(
            [str(row.get("memory_id") or "").strip() for row in profile_rows]
        ),
        "summary": summary,
        "updated_at": updated_at,
        "updated_by": updated_by,
    }


def render_collaborator_profile_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Collaborator profile",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Preference count: `{payload.get('preference_count') or 0}`",
        f"- Working-style count: `{payload.get('working_style_count') or 0}`",
        f"- Trajectory count: `{payload.get('trajectory_count') or 0}`",
        f"- Coordination count: `{payload.get('coordination_count') or 0}`",
        f"- Preferred tags: `{', '.join(payload.get('preferred_tags') or []) or '(none)'}`",
        f"- Related topics: `{', '.join(payload.get('related_topic_slugs') or []) or '(none)'}`",
        "",
        payload.get("summary") or "(missing)",
    ]
    for header, key in (
        ("Preference summaries", "preference_summaries"),
        ("Working-style summaries", "working_style_summaries"),
        ("Trajectory summaries", "trajectory_summaries"),
        ("Coordination summaries", "coordination_summaries"),
    ):
        lines.extend(["", f"## {header}", ""])
        for row in payload.get(key) or ["(none)"]:
            lines.append(f"- {row}")
    return "\n".join(lines) + "\n"


def materialize_collaborator_profile_surface(
    self,
    *,
    runtime_root: Path,
    topic_slug: str,
    updated_by: str,
) -> tuple[dict[str, Path], dict[str, Any]]:
    paths = collaborator_profile_paths(runtime_root)
    payload = derive_collaborator_profile(self, topic_slug=topic_slug, updated_by=updated_by)
    payload = {
        **payload,
        "path": self._relativize(paths["json"]),
        "note_path": self._relativize(paths["note"]),
    }
    _write_json(paths["json"], payload)
    paths["note"].write_text(render_collaborator_profile_markdown(payload), encoding="utf-8")
    return paths, payload


def normalize_collaborator_profile_for_bundle(
    self,
    *,
    shell_surfaces: dict[str, Any],
    runtime_root: Path,
    topic_slug: str,
    updated_by: str,
) -> dict[str, Any]:
    profile = dict(shell_surfaces.get("collaborator_profile") or {})
    if not profile:
        profile = empty_collaborator_profile(topic_slug=topic_slug, updated_by=updated_by)
    paths = collaborator_profile_paths(runtime_root)
    if not str(profile.get("path") or "").strip():
        profile["path"] = self._relativize(paths["json"])
    if not str(profile.get("note_path") or "").strip():
        profile["note_path"] = self._relativize(paths["note"])
    return profile


def collaborator_profile_must_read_entry(profile: dict[str, Any]) -> dict[str, str] | None:
    if str(profile.get("status") or "") != "available":
        return None
    note_path = str(profile.get("note_path") or "").strip()
    if not note_path:
        return None
    return {
        "path": note_path,
        "reason": "Topic-scoped collaborator profile is available. Read it before repeating an old route preference or working-style mismatch.",
    }


def append_collaborator_profile_markdown(lines: list[str], profile: dict[str, Any]) -> None:
    lines.extend(
        [
            "## Collaborator profile",
            "",
            f"- Status: `{profile.get('status') or '(missing)'}`",
            f"- Preference count: `{profile.get('preference_count') or 0}`",
            f"- Working-style count: `{profile.get('working_style_count') or 0}`",
            f"- Trajectory count: `{profile.get('trajectory_count') or 0}`",
            f"- Coordination count: `{profile.get('coordination_count') or 0}`",
            f"- Note path: `{profile.get('note_path') or '(missing)'}`",
            "",
            f"{profile.get('summary') or '(missing)'}",
            "",
        ]
    )
