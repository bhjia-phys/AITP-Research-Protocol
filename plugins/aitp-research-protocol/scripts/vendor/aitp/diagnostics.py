"""Read-only store diagnostics (`aitp check`): no-flag whole-store `aitp/check-report-0.1` (M1b-R1); single-occurrence `--workstream` scoped `aitp/check-report-0.2` (M1d)."""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Any

from .md import AITPError, _section_content, parse_markdown
from .notes import validate_note
from .query import _in_scope, _scan_records, _stored_time, _validate_scope
from .records import (
    _canonical_entries,
    _validate_relations,
    _verify_refs,
    validate_entry,
)
from .workspace import load_store, resolve_root

GOAL_PLACEHOLDER = "Not established yet"


def _finding(level: str, code: str, relative: str, message: str) -> dict[str, str]:
    return {"level": level, "code": code, "path": relative, "message": message}


def _policy_matches(target: str, patterns: list[str] | None) -> bool:
    if not patterns:
        return False
    for pattern in patterns:
        if pattern.endswith("/**"):
            prefix = pattern[:-3].rstrip("/")
            if target == prefix or target.startswith(prefix + "/"):
                return True
        elif fnmatch.fnmatchcase(target, pattern):
            return True
    return False


def _validate_policy_paths(values: Any, label: str) -> list[str]:
    if not isinstance(values, list):
        raise ValueError(f"{label} must be a list")
    paths: list[str] = []
    for item in values:
        if not isinstance(item, dict) or not isinstance(item.get("paths"), list):
            raise ValueError(f"{label} items must be maps with a paths list")
        for path in item["paths"]:
            if not isinstance(path, str) or not path.strip():
                raise ValueError(f"{label} paths must be non-empty strings")
            if path.startswith("/") or any(part == ".." for part in path.split("/")):
                raise ValueError(f"{label} path must be workspace-relative: {path}")
            paths.append(path)
    return paths


def _load_check_policy(root: Path) -> tuple[list[str] | None, list[str] | None, list[dict[str, str]]]:
    policy_path = root / ".aitp" / "local" / "check-policy.json"
    if not policy_path.is_file():
        return None, None, []
    relative = str(policy_path.relative_to(root))
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, None, [_finding("error", "invalid_check_policy", relative, f"unreadable check policy: {exc}")]
    if not isinstance(policy, dict) or policy.get("schema") != "aitp/check-policy-0.1":
        return None, None, [_finding("error", "invalid_check_policy", relative, "check policy must use schema aitp/check-policy-0.1")]
    try:
        mutable = _validate_policy_paths(policy.get("mutable"), "mutable")
        immutable = _validate_policy_paths(policy.get("immutable"), "immutable")
    except (TypeError, ValueError) as exc:
        return None, None, [_finding("error", "invalid_check_policy", relative, str(exc))]
    return mutable, immutable, []


def _grade_records(root: Path, items: list[tuple[dict[str, Any], str, Path]], refs_key: str, label: str,
                   *, relations: bool, require_refs: bool, findings: list[dict[str, str]],
                   entry_map: dict[str, tuple[dict[str, Any], Path]] | None = None,
                   policy: tuple[list[str] | None, list[str] | None] | None = None) -> None:
    for frontmatter, _, path in items:
        relative = str(path.relative_to(root))
        if _stored_time(frontmatter.get("created_at")) is None:
            findings.append(_finding("warning", "invalid_timestamp", relative, f"unparseable created_at: {frontmatter.get('created_at')}"))
        if relations:
            relation_failed = False
            for field in ("resolves", "supersedes"):
                try:
                    _validate_relations(root, frontmatter, field, frontmatter["id"], entry_map)
                except AITPError as exc:
                    findings.append(_finding("error", exc.code, relative, str(exc))); relation_failed = True
                except Exception as exc:
                    findings.append(_finding("error", "invalid_schema", relative, f"{path}: {exc}")); relation_failed = True
            if relation_failed: continue
        refs = frontmatter[refs_key]
        if require_refs and not refs:
            findings.append(_finding("error", "missing_refs", relative, f"{label} requires nonempty {refs_key}"))
        elif refs:
            mutable, immutable = (None, None) if policy is None else policy
            for ref in refs:
                try:
                    graded = _verify_refs(root, [ref])
                except Exception as exc:
                    findings.append(_finding("error", "invalid_schema", relative, f"{path}: {exc}"))
                    continue
                for code, message, grade in graded:
                    target = ref.get("target", "") if isinstance(ref, dict) else ""
                    if grade == "error" and code == "hash_mismatch" and _policy_matches(target, mutable):
                        code, grade = "historical_pin_drift", "warning"
                        message = message.replace("sha256 mismatch:", "sha256 historical drift:", 1)
                    elif grade == "error" and code == "missing_ref" and _policy_matches(target, mutable):
                        code, grade = "historical_ref_missing", "warning"
                    findings.append(_finding(grade, code, relative, message))


def check_workspace(cwd: str | Path, *, workstream: str | None = None) -> dict[str, Any]:
    root = resolve_root(cwd)
    topic_id = load_store(root)["topic_id"]
    _validate_scope(workstream)
    mutable_policy, immutable_policy, policy_findings = _load_check_policy(root)
    policy = (mutable_policy, immutable_policy)
    findings: list[dict[str, str]] = [*policy_findings]
    entry_paths = sorted(_canonical_entries(root), key=lambda item: item.name)
    entries, entry_warnings = _scan_records(root, entry_paths, validate_entry, "Entry", topic_id=topic_id)
    findings.extend(_finding("error", item["code"], item["path"], item["message"]) for item in entry_warnings)
    entry_map = {fm["id"]: (fm, path) for fm, _, path in entries if isinstance(fm.get("id"), str)}
    _grade_records(root, entries, "refs", "Entry", relations=True, require_refs=False,
                   findings=findings, entry_map=entry_map, policy=policy)
    notes_dir = root / ".aitp" / "topic" / "notes"
    note_paths = sorted(notes_dir.glob("note-*.md"), key=lambda item: item.name)
    notes, note_warnings = _scan_records(root, note_paths, validate_note, "Note", topic_id=topic_id)
    findings.extend(_finding("error", item["code"], item["path"], item["message"]) for item in note_warnings)
    _grade_records(root, notes, "basis_refs", "Note", relations=False, require_refs=True, findings=findings, policy=policy)
    topic_path = root / ".aitp" / "topic" / "TOPIC.md"
    relative = str(topic_path.relative_to(root))
    try:
        _, topic_body, _ = parse_markdown(topic_path)
        goal = _section_content(topic_body, "Research Goal").strip()
        if not goal or goal == GOAL_PLACEHOLDER:
            findings.append(_finding("warning", "empty_topic_goal", relative, "Research Goal is not established"))
    except AITPError as exc:
        findings.append(_finding("error", exc.code, relative, str(exc)))
    except Exception as exc:
        findings.append(_finding("error", "invalid_schema", relative, f"{topic_path}: {exc}"))
    findings.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    errors = sum(1 for item in findings if item["level"] == "error")
    warnings = len(findings) - errors
    if workstream is not None:
        scoped_paths = {str(path.relative_to(root)) for fm, _, path in entries + notes if _in_scope(fm, workstream)}
        scoped = [item for item in findings if item["path"] in scoped_paths]
        scoped_errors = sum(1 for item in scoped if item["level"] == "error")
        scoped_warnings = len(scoped) - scoped_errors
        by_code: dict[str, dict[str, int]] = {}
        for item in scoped:
            by_code.setdefault(item["code"], {"errors": 0, "warnings": 0})[item["level"] + "s"] += 1
        return {"schema": "aitp/check-report-0.2", "status": "clean" if not scoped else "findings", "root": str(root),
                "counts": {"entries": sum(1 for fm, _, _ in entries if _in_scope(fm, workstream)),
                           "notes": sum(1 for fm, _, _ in notes if _in_scope(fm, workstream)),
                           "errors": scoped_errors, "warnings": scoped_warnings,
                           "by_code": dict(sorted(by_code.items())),
                           "outside_scope": {"errors": errors - scoped_errors, "warnings": warnings - scoped_warnings}},
                "findings": scoped, "workstream": workstream}
    return {"schema": "aitp/check-report-0.1", "status": "clean" if not findings else "findings",
            "root": str(root),
            "counts": {"entries": len(entry_paths), "notes": len(note_paths),
                       "errors": errors, "warnings": warnings},
            "findings": findings}
