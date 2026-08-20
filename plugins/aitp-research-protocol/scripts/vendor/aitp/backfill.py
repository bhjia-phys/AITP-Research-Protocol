"""Reviewed explicit workstream backfill (`aitp backfill workstreams`, M1e)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .md import AITPError, atomic_write, parse_markdown
from .notes import NOTE_ID_RE
from .records import ENTRY_ID_RE, WORKSTREAM_RE
from .workspace import resolve_root


def _json_error(message: str) -> AITPError:
    return AITPError("invalid_backfill_mapping", message)


def _load_mapping(root: Path, mapping: str | Path) -> tuple[Path, str, dict[str, list[tuple[str, str]]]]:
    candidate = Path(mapping)
    path = candidate if candidate.is_absolute() else (root / candidate)
    try:
        path = path.resolve()
        path.relative_to(root)
    except ValueError as exc:
        raise _json_error(f"mapping must be inside the workspace: {mapping}") from exc
    if not path.is_file():
        raise _json_error(f"mapping file does not exist: {mapping}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _json_error(f"mapping file is unreadable: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != "aitp/backfill-workstreams-0.1":
        raise _json_error("mapping must use schema aitp/backfill-workstreams-0.1")
    result: dict[str, list[tuple[str, str]]] = {"entries": [], "notes": []}
    seen: set[str] = set()
    for section, id_re, label in (("entries", ENTRY_ID_RE, "Entry"), ("notes", NOTE_ID_RE, "Note")):
        values = data.get(section)
        if not isinstance(values, dict):
            raise _json_error(f"{section} must be a map")
        for slug, ids in values.items():
            if not isinstance(slug, str) or not WORKSTREAM_RE.fullmatch(slug):
                raise _json_error(f"invalid workstream slug: {slug!r}")
            if not isinstance(ids, list) or not ids:
                raise _json_error(f"{section}.{slug} must be a non-empty list of {label} IDs")
            for record_id in ids:
                if not isinstance(record_id, str) or not id_re.fullmatch(record_id):
                    raise _json_error(f"invalid {label} ID: {record_id!r}")
                if record_id in seen:
                    raise _json_error(f"duplicate record ID in mapping: {record_id}")
                seen.add(record_id)
                result[section].append((slug, record_id))
    return path, str(path.relative_to(root)), result


def _decision_anchors(root: Path, decision: str, mapping_path: Path, mapping_rel: str) -> None:
    decision_path = root / ".aitp" / "topic" / "entries" / f"{decision}.md"
    if not decision_path.is_file():
        raise AITPError("missing_backfill_decision", f"decision Entry does not exist: {decision}")
    try:
        frontmatter, _, _ = parse_markdown(decision_path)
    except AITPError as exc:
        raise AITPError("invalid_backfill_decision", f"decision Entry is unreadable: {exc}") from exc
    if frontmatter.get("kind") != "decision" or frontmatter.get("authority") != "human":
        raise AITPError("invalid_backfill_decision", "backfill decision must be a human decision Entry")
    digest = hashlib.sha256(mapping_path.read_bytes()).hexdigest()
    for ref in frontmatter.get("refs", []):
        if not isinstance(ref, dict) or ref.get("target") != mapping_rel:
            continue
        pin = ref.get("at", "")
        if pin.startswith("sha256:") and pin[7:].lower() == digest:
            return
    raise AITPError(
        "backfill_anchor_missing",
        f"decision {decision} must pin the mapping file with sha256:<digest>",
    )


def _record_path(root: Path, section: str, record_id: str) -> Path:
    folder = "entries" if section == "entries" else "notes"
    return root / ".aitp" / "topic" / folder / f"{record_id}.md"


def _merge_workstreams(frontmatter: dict[str, Any], slugs: list[str]) -> list[str]:
    existing = frontmatter.get("workstreams")
    if existing is None:
        existing = []
    if not isinstance(existing, list) or not all(isinstance(item, str) for item in existing):
        raise AITPError("invalid_backfill_record", "existing workstreams field is invalid")
    merged = list(existing)
    for slug in slugs:
        if slug not in merged:
            merged.append(slug)
    return merged


def _set_workstreams_block(text: str, slugs: list[str]) -> str:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0] != "---\n":
        raise AITPError("invalid_backfill_record", "record has no YAML frontmatter")
    close = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if close is None:
        raise AITPError("invalid_backfill_record", "record has an unclosed YAML frontmatter")
    block = "workstreams:\n" + "".join(f"  - {slug}\n" for slug in slugs)
    key = next((i for i in range(1, close) if lines[i].lstrip().startswith("workstreams:")), None)
    if key is None:
        lines.insert(close, block)
    else:
        end = key + 1
        while end < close and (lines[end].lstrip().startswith("- ") or lines[end].strip() == ""):
            end += 1
        lines[key:end] = [block]
    return "".join(lines)


def backfill_workspace(
    cwd: str | Path, *, mapping: str, decision: str, apply: bool
) -> dict[str, Any]:
    root = resolve_root(cwd)
    mapping_path, mapping_rel, mapping_data = _load_mapping(root, mapping)
    _decision_anchors(root, decision, mapping_path, mapping_rel)
    changed: list[dict[str, Any]] = []
    unchanged: list[str] = []
    for section, items in mapping_data.items():
        for slug, record_id in items:
            path = _record_path(root, section, record_id)
            try:
                frontmatter, body, text = parse_markdown(path)
            except AITPError as exc:
                raise _json_error(f"cannot read {path.relative_to(root)}: {exc}") from exc
            merged = _merge_workstreams(frontmatter, [slug])
            if merged == frontmatter.get("workstreams"):
                unchanged.append(record_id)
                continue
            new_text = _set_workstreams_block(text, merged)
            # Validate the edited text with the real parser before writing.
            temp_path = path.with_name(f".{path.name}.backfill-check")
            atomic_write(temp_path, new_text)
            try:
                new_frontmatter, new_body, _ = parse_markdown(temp_path)
            finally:
                temp_path.unlink()
            if new_frontmatter.get("workstreams") != merged or new_body != body:
                raise _json_error(f"backfill would change non-workstream content: {record_id}")
            changed.append({"path": str(path.relative_to(root)), "workstreams": merged})
            if apply:
                atomic_write(path, new_text)
    return {
        "schema": "aitp/backfill-0.1",
        "status": "applied" if apply else "dry_run",
        "mapping": mapping_rel,
        "decision": decision,
        "changed": changed,
        "unchanged": unchanged,
    }
