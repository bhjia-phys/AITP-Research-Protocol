from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


VALID_STAGING_STATUSES = {"staged", "reviewed", "dismissed"}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def slugify(text: str) -> str:
    lowered = str(text or "").lower()
    allowed = "".join(ch if ch.isalnum() else "-" for ch in lowered)
    while "--" in allowed:
        allowed = allowed.replace("--", "-")
    return allowed.strip("-") or "staging"


def _canonical_root(kernel_root: Path) -> Path:
    return kernel_root / "canonical"


def _staging_root(kernel_root: Path) -> Path:
    return _canonical_root(kernel_root) / "staging"


def _entries_root(kernel_root: Path) -> Path:
    return _staging_root(kernel_root) / "entries"


def _entry_digest(topic_slug: str, entry_kind: str, title: str) -> str:
    raw = f"{topic_slug}|{entry_kind}|{title}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:8]


def _entry_id(topic_slug: str, entry_kind: str, title: str) -> str:
    return f"staging:{slugify(topic_slug)}-{slugify(entry_kind)}-{_entry_digest(topic_slug, entry_kind, title)}"


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _render_entry_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# L2 Staging Entry",
        "",
        f"- Entry id: `{payload.get('entry_id') or '(missing)'}`",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Entry kind: `{payload.get('entry_kind') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Authoritative: `{payload.get('authoritative')}`",
        f"- Title: {payload.get('title') or '(missing)'}",
        "",
        "## Summary",
        "",
        payload.get("summary") or "(missing)",
        "",
        "## Source Artifacts",
        "",
    ]
    source_artifacts = payload.get("source_artifact_paths") or []
    if source_artifacts:
        for item in source_artifacts:
            lines.append(f"- `{item}`")
    else:
        lines.append("- `(none)`")
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "This entry is provisional and non-authoritative. It must not be treated as canonical `L2` memory unless it later passes the proper promotion path.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def load_staging_entries(kernel_root: Path) -> list[dict[str, Any]]:
    root = _entries_root(kernel_root)
    if not root.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        payload = read_json(path)
        if isinstance(payload, dict):
            row = dict(payload)
            row.setdefault("path", _rel(path, kernel_root))
            row.setdefault("entry_kind", str(row.get("candidate_unit_type") or "unknown"))
            row.setdefault(
                "authoritative",
                bool(row.get("authoritative")) if "authoritative" in row else str(row.get("trust_surface") or "") != "staging",
            )
            rows.append(row)
    return rows


def _staging_index_rows(kernel_root: Path, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in entries:
        title = str(entry.get("title") or "").strip()
        summary = str(entry.get("summary") or "").strip()
        entry_kind = str(entry.get("entry_kind") or "unknown").strip()
        topic_slug = str(entry.get("topic_slug") or "").strip()
        failure_kind = str(entry.get("failure_kind") or "").strip()
        source_artifact_paths = [
            str(item).strip()
            for item in (entry.get("source_artifact_paths") or [])
            if str(item).strip()
        ]
        rows.append(
            {
                "entry_id": str(entry.get("entry_id") or ""),
                "topic_slug": topic_slug,
                "entry_kind": entry_kind,
                "candidate_unit_type": str(entry.get("candidate_unit_type") or entry_kind),
                "title": title,
                "summary": summary,
                "trust_surface": str(entry.get("trust_surface") or "staging"),
                "status": str(entry.get("status") or ""),
                "authoritative": bool(entry.get("authoritative")),
                "path": str(entry.get("path") or ""),
                "note_path": str(entry.get("note_path") or ""),
                "failure_kind": failure_kind,
                "source_artifact_paths": source_artifact_paths,
                "tags": [str(item).strip() for item in (entry.get("tags") or []) if str(item).strip()],
                "source_refs": [str(item).strip() for item in (entry.get("source_refs") or []) if str(item).strip()],
                "provenance": dict(entry.get("provenance") or {}),
                "search_terms": " ".join(
                    [
                        title,
                        summary,
                        entry_kind,
                        " ".join(str(item).strip() for item in (entry.get("tags") or []) if str(item).strip()),
                        " ".join(str(item).strip() for item in (entry.get("source_refs") or []) if str(item).strip()),
                        failure_kind,
                        str(entry.get("notes") or "").strip(),
                        str((entry.get("provenance") or {}).get("source_id") or ""),
                        str((entry.get("provenance") or {}).get("source_title") or ""),
                        str((entry.get("provenance") or {}).get("source_slug") or ""),
                        " ".join(source_artifact_paths),
                    ]
                ),
                "created_at": str(entry.get("created_at") or ""),
                "updated_at": str(entry.get("updated_at") or ""),
            }
        )
    rows.sort(key=lambda row: str(row.get("entry_id") or ""))
    return rows


def build_workspace_staging_manifest(kernel_root: Path) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    entries = load_staging_entries(kernel_root)

    counts_by_status: dict[str, int] = {status: 0 for status in sorted(VALID_STAGING_STATUSES)}
    counts_by_kind: dict[str, int] = {}
    counts_by_topic: dict[str, int] = {}
    for entry in entries:
        status = str(entry.get("status") or "staged")
        counts_by_status[status] = counts_by_status.get(status, 0) + 1
        entry_kind = str(entry.get("entry_kind") or "unknown")
        counts_by_kind[entry_kind] = counts_by_kind.get(entry_kind, 0) + 1
        topic_slug = str(entry.get("topic_slug") or "unknown")
        counts_by_topic[topic_slug] = counts_by_topic.get(topic_slug, 0) + 1

    summary = {
        "total_entries": len(entries),
        "counts_by_status": dict(sorted(counts_by_status.items())),
        "counts_by_kind": dict(sorted(counts_by_kind.items())),
        "counts_by_topic": dict(sorted(counts_by_topic.items())),
    }

    return {
        "kind": "l2_workspace_staging_manifest",
        "manifest_version": 1,
        "generated_at": now_iso(),
        "source_contract_path": "canonical/L2_STAGING_PROTOCOL.md",
        "summary": summary,
        "entries": [
            {
                "entry_id": str(entry.get("entry_id") or ""),
                "topic_slug": str(entry.get("topic_slug") or ""),
                "entry_kind": str(entry.get("entry_kind") or ""),
                "status": str(entry.get("status") or ""),
                "title": str(entry.get("title") or ""),
                "path": str(entry.get("path") or ""),
                "authoritative": bool(entry.get("authoritative")),
            }
            for entry in entries
        ],
    }


def render_workspace_staging_manifest_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Workspace Staging Manifest",
        "",
        f"- Generated at: `{payload.get('generated_at') or '(missing)'}`",
        f"- Source contract: `{payload.get('source_contract_path') or '(missing)'}`",
        f"- Total entries: `{summary.get('total_entries', 0)}`",
        "",
        "## Counts By Status",
        "",
    ]
    for status, count in (summary.get("counts_by_status") or {}).items():
        lines.append(f"- `{status}`: `{count}`")
    lines.extend(["", "## Counts By Kind", ""])
    if summary.get("counts_by_kind"):
        for kind, count in (summary.get("counts_by_kind") or {}).items():
            lines.append(f"- `{kind}`: `{count}`")
    else:
        lines.append("- `(none)`")
    lines.extend(["", "## Entries", ""])
    entries = payload.get("entries") or []
    if not entries:
        lines.append("- `(none)`")
    else:
        for entry in entries:
            lines.append(
                f"- `{entry.get('entry_id')}` topic=`{entry.get('topic_slug')}` kind=`{entry.get('entry_kind')}` status=`{entry.get('status')}` path=`{entry.get('path')}`"
            )
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "Everything listed here is non-authoritative staging content. Canonical `L2` promotion still requires the normal review path.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def materialize_workspace_staging_manifest(kernel_root: Path) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    staging_root = _staging_root(kernel_root)
    entries = load_staging_entries(kernel_root)
    payload = build_workspace_staging_manifest(kernel_root)
    json_path = staging_root / "workspace_staging_manifest.json"
    md_path = staging_root / "workspace_staging_manifest.md"
    index_path = staging_root / "staging_index.jsonl"
    write_json(json_path, payload)
    write_text(md_path, render_workspace_staging_manifest_markdown(payload))
    write_jsonl(index_path, _staging_index_rows(kernel_root, entries))
    return {
        "payload": payload,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
        "index_path": str(index_path),
    }


def stage_provisional_l2_entry(
    kernel_root: Path,
    *,
    topic_slug: str,
    entry_kind: str,
    title: str,
    summary: str,
    source_artifact_paths: list[str] | None = None,
    notes: str | None = None,
    staged_by: str = "aitp-cli",
) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    entry_kind = str(entry_kind or "").strip()
    title = str(title or "").strip()
    summary = str(summary or "").strip()
    if not topic_slug or not entry_kind or not title or not summary:
        raise ValueError("topic_slug, entry_kind, title, and summary are required")

    entry_id = _entry_id(topic_slug, entry_kind, title)
    entry_json_path = _entries_root(kernel_root) / f"{entry_id.split(':', 1)[1]}.json"
    entry_md_path = _entries_root(kernel_root) / f"{entry_id.split(':', 1)[1]}.md"

    payload = {
        "entry_id": entry_id,
        "topic_slug": topic_slug,
        "entry_kind": entry_kind,
        "title": title,
        "summary": summary,
        "status": "staged",
        "authoritative": False,
        "source_artifact_paths": [str(item).strip() for item in (source_artifact_paths or []) if str(item).strip()],
        "notes": str(notes or "").strip(),
        "created_at": now_iso(),
        "created_by": staged_by,
        "updated_at": now_iso(),
        "updated_by": staged_by,
        "path": _rel(entry_json_path, kernel_root),
        "note_path": _rel(entry_md_path, kernel_root),
    }

    write_json(entry_json_path, payload)
    write_text(entry_md_path, _render_entry_markdown(payload))
    manifest = materialize_workspace_staging_manifest(kernel_root)
    return {
        "entry": payload,
        "entry_json_path": str(entry_json_path),
        "entry_markdown_path": str(entry_md_path),
        "manifest": manifest["payload"],
        "manifest_json_path": manifest["json_path"],
        "manifest_markdown_path": manifest["markdown_path"],
    }


def stage_negative_result_entry(
    kernel_root: Path,
    *,
    title: str,
    summary: str,
    failure_kind: str,
    staged_by: str = "aitp-cli",
) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    normalized_title = str(title or "").strip()
    normalized_summary = str(summary or "").strip()
    normalized_failure_kind = str(failure_kind or "").strip()
    if not normalized_title or not normalized_summary or not normalized_failure_kind:
        raise ValueError("title, summary, and failure_kind are required")

    slug = slugify(normalized_title)
    entry_id = f"staging:{slug}"
    entry_json_path = _entries_root(kernel_root) / f"staging--{slug}.json"
    entry_md_path = _entries_root(kernel_root) / f"staging--{slug}.md"
    recorded_at = now_iso()

    payload = {
        "entry_id": entry_id,
        "topic_slug": "global",
        "entry_kind": "negative_result",
        "title": normalized_title,
        "summary": normalized_summary,
        "failure_kind": normalized_failure_kind,
        "status": "staged",
        "authoritative": False,
        "source_artifact_paths": [],
        "notes": f"Failure kind: {normalized_failure_kind}",
        "created_at": recorded_at,
        "created_by": staged_by,
        "updated_at": recorded_at,
        "updated_by": staged_by,
        "path": _rel(entry_json_path, kernel_root),
        "note_path": _rel(entry_md_path, kernel_root),
    }

    write_json(entry_json_path, payload)
    write_text(entry_md_path, _render_entry_markdown(payload))
    manifest = materialize_workspace_staging_manifest(kernel_root)
    return {
        "entry": payload,
        "entry_json_path": str(entry_json_path),
        "entry_markdown_path": str(entry_md_path),
        "manifest": manifest["payload"],
        "manifest_json_path": manifest["json_path"],
        "manifest_markdown_path": manifest["markdown_path"],
    }
