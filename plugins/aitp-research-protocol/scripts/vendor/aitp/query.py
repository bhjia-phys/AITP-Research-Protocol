"""Read-only Entry projections for dense AITP stores."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from .md import AITPError, parse_markdown
from .records import ENTRY_ID_RE, ENTRY_KINDS, _canonical_entries, _validate_workstreams, validate_entry
from .workspace import load_store, resolve_root

_KIND_ORDER = (
    "observation", "result", "failure", "decision", "source", "code_change",
    "run", "closeout",
)
LEGACY_MARKER = "> legacy-derived: recovery orientation only — not re-validated"


def _stored_time(raw: Any) -> datetime | None:
    if not isinstance(raw, str):
        return None
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse_since(value: str) -> datetime:
    parsed = _stored_time(value)
    if parsed is None:
        raise AITPError("invalid_since", f"invalid --since value: {value}")
    return parsed


def _sort_key(raw: Any, entry_id: Any) -> tuple[int, Any, str]:
    parsed = _stored_time(raw)
    return (0, parsed, str(entry_id)) if parsed else (1, str(raw), str(entry_id))


def _descending_key(raw: Any, entry_id: Any) -> tuple[int, Any, str]:
    key = _sort_key(raw, entry_id)
    return (1 - key[0], key[1], key[2])


def _truncate(text: str, limit: int = 110) -> str:
    text = " ".join(text.split()).strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def _is_legacy_derived(body: str) -> bool:
    return bool(body.splitlines()) and body.splitlines()[0] == LEGACY_MARKER


def _in_scope(frontmatter: dict[str, Any], workstream: str | None) -> bool:
    if workstream is None:
        return True
    return workstream in frontmatter.get("workstreams", [])


def _warning(root: Path, path: Path, code: str, message: str) -> dict[str, str]:
    return {"code": code, "path": str(path.relative_to(root)), "message": message}


def _scan_records(
    root: Path,
    paths: list[Path],
    validate: Callable[..., None],
    label: str,
    *,
    topic_id: str | None = None,
) -> tuple[list[tuple[dict[str, Any], str, Path]], list[dict[str, str]]]:
    items: list[tuple[dict[str, Any], str, Path]] = []
    warnings: list[dict[str, str]] = []
    seen: set[str] = set()
    for path in paths:
        try:
            frontmatter, body, _ = parse_markdown(path)
            validate(root, frontmatter, body, validate_evidence=False, topic_id=topic_id)
            record_id = frontmatter["id"]
            if record_id in seen:
                raise AITPError("duplicate_id", f"duplicate {label} ID: {record_id}")
            seen.add(record_id)
            items.append((frontmatter, body, path))
        except AITPError as exc:
            warnings.append(_warning(root, path, exc.code, str(exc)))
        except Exception as exc:
            warnings.append(_warning(root, path, "invalid_schema", f"{path}: {exc}"))
    return items, warnings


def _scan_entries(
    root: Path,
    preferred: Path | None = None,
    *,
    topic_id: str | None = None,
) -> tuple[list[tuple[dict[str, Any], str, Path]], list[dict[str, str]]]:
    paths = sorted(_canonical_entries(root), key=lambda item: item.name)
    if preferred in paths:
        paths.remove(preferred)
        paths.insert(0, preferred)
    return _scan_records(root, paths, validate_entry, "Entry", topic_id=topic_id)


def _superseded_ids(items: list[tuple[dict[str, Any], str, Path]]) -> set[str]:
    ids = {frontmatter["id"] for frontmatter, _, _ in items}
    return {target for frontmatter, _, _ in items
            for target in frontmatter["supersedes"] if target in ids}


def _projection(
    root: Path, item: tuple[dict[str, Any], str, Path],
    superseded: set[str], details: bool = False,
) -> dict[str, Any]:
    frontmatter, body, path = item
    if details:
        return {
            "id": frontmatter["id"], "kind": frontmatter["kind"], "summary": frontmatter["summary"],
            "limitations": frontmatter["limitations"], "authority": frontmatter["authority"], "created_at": frontmatter["created_at"],
            "refs": frontmatter["refs"], "source": str(path.relative_to(root)), "legacy_derived": _is_legacy_derived(body),
        }
    return {
        "id": frontmatter["id"], "kind": frontmatter["kind"], "status": "superseded" if frontmatter["id"] in superseded else "active",
        "created_at": frontmatter["created_at"], "authority": frontmatter["authority"], "summary": frontmatter["summary"],
        "legacy_derived": _is_legacy_derived(body), "source": str(path.relative_to(root)),
    }


def _validate_scope(workstream: Any) -> None:
    if workstream is None:
        return
    if not isinstance(workstream, str):
        raise AITPError("invalid_workstreams", "invalid workstreams: exactly one slug required")
    _validate_workstreams([workstream])


def list_workspace(
    cwd: str | Path, *, kind: str | None = None, since: str | None = None, workstream: str | None = None
) -> dict[str, Any]:
    root = resolve_root(cwd)
    topic_id = load_store(root)["topic_id"]
    if kind is not None:
        kind = kind.replace("-", "_")
        if kind not in ENTRY_KINDS:
            allowed = ", ".join(_KIND_ORDER)
            raise AITPError(
                "invalid_kind",
                f"unsupported Entry kind: {kind} (allowed: {allowed})",
            )
    _validate_scope(workstream)
    boundary = _parse_since(since) if since is not None else None
    items, warnings = _scan_entries(root, topic_id=topic_id)
    superseded = _superseded_ids(items)
    selected: list[tuple[dict[str, Any], str, Path]] = []
    for item in items:
        frontmatter, _, path = item
        raw = frontmatter.get("created_at", "")
        parsed = _stored_time(raw)
        if parsed is None:
            warnings.append(_warning(root, path, "invalid_timestamp", f"unparseable created_at: {raw}"))
            if boundary is not None:
                continue
        if kind is not None and frontmatter["kind"] != kind:
            continue
        if not _in_scope(frontmatter, workstream):
            continue
        if boundary is None or parsed >= boundary:
            selected.append(item)
    selected.sort(key=lambda item: _descending_key(item[0].get("created_at", ""), item[0]["id"]), reverse=True)
    entries = [_projection(root, item, superseded) for item in selected]
    payload = {"schema": "aitp/list-0.1", "root": str(root), "count": len(entries),
               "entries": entries, "warnings": warnings}
    if workstream is not None:
        payload["schema"] = "aitp/list-0.2"
        payload["workstream"] = workstream
    return payload


def show_entry(cwd: str | Path, entry_id: str) -> dict[str, Any]:
    if not ENTRY_ID_RE.fullmatch(entry_id):
        raise AITPError("invalid_id", "invalid Entry ID")
    root = resolve_root(cwd)
    topic_id = load_store(root)["topic_id"]
    target = root / ".aitp" / "topic" / "entries" / f"{entry_id}.md"
    items, warnings = _scan_entries(root, target, topic_id=topic_id)
    source = str(target.relative_to(root))
    failure = next((item for item in warnings if item["path"] == source), None)
    if failure and target.is_file():
        try:
            text = target.read_text(encoding="utf-8")
        except OSError as exc:
            raise AITPError("unreadable_record", f"cannot read Entry file: {target}: {exc}") from exc
        return {"schema": "aitp/show-0.1", "root": str(root), "id": entry_id,
                "status": "malformed", "source": source, "legacy_derived": False,
                "frontmatter": None, "body": text, "warning": failure}
    if failure:
        raise AITPError(failure["code"], failure["message"])
    if not target.is_file():
        raise AITPError("entry_not_found", f"no Entry with id {entry_id}")
    selected = next((item for item in items if item[2] == target), None)
    if selected is None:
        raise AITPError("entry_not_found", f"no Entry with id {entry_id}")
    if selected[0]["id"] != entry_id:
        raise AITPError("invalid_id", "Entry ID does not match canonical path")
    superseded = _superseded_ids(items)
    frontmatter, body, path = selected
    return {"schema": "aitp/show-0.1", "root": str(root), "id": entry_id,
            "status": "superseded" if entry_id in superseded else "active",
            "source": str(path.relative_to(root)), "legacy_derived": _is_legacy_derived(body),
            "frontmatter": frontmatter, "body": body}
