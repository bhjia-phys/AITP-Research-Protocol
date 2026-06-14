"""Coverage audit for full legacy-to-v5 migration runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from brain.v5.paths import WorkspacePaths


def audit_legacy_migration_coverage(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Audit file/reference coverage for a completed legacy migration run.

    This proves accounting coverage only. It intentionally does not claim that
    the physics meaning of every legacy note was understood correctly.
    """

    run_dir = _resolve_migration_dir(ws, migration_dir)
    summary = _read_json(run_dir / "migration_summary.json")
    verification = _read_json(run_dir / "verification_report.json")
    totals = summary.get("totals") if isinstance(summary.get("totals"), dict) else {}
    topics = [_topic_coverage(topic) for topic in summary.get("topics", []) if isinstance(topic, dict)]

    file_preservation = _file_preservation(summary, verification)
    archive_reference_coverage = _archive_reference_coverage(summary, verification)
    markdown_readability = _markdown_readability(verification)
    gap_topics = [topic for topic in topics if topic["coverage_status"] != "accounted_needs_review"]
    all_accounted = (
        file_preservation["ok"]
        and archive_reference_coverage["ok"]
        and markdown_readability["ok"]
        and not gap_topics
    )

    return {
        "kind": "legacy_migration_coverage_audit",
        "run_id": str(summary.get("run_id") or verification.get("run_id") or run_dir.name),
        "migration_dir": str(run_dir),
        "workspace": str(summary.get("workspace") or ws.base),
        "legacy_root": str(summary.get("legacy_root") or ""),
        "v5_root": str(summary.get("v5_root") or ws.root),
        "topic_count": int(totals.get("topic_count") or len(topics)),
        "legacy_file_count": int(totals.get("legacy_file_count") or file_preservation["pre_count"]),
        "file_preservation": file_preservation,
        "archive_reference_coverage": archive_reference_coverage,
        "markdown_readability": markdown_readability,
        "topics": topics,
        "gap_topic_count": len(gap_topics),
        "gap_topics": [topic["topic"] for topic in gap_topics],
        "coverage_status": "accounted_needs_review" if all_accounted else "coverage_gaps",
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "semantic_review_reason": (
            "Migration manifests can prove file accounting and reference preservation; "
            "they cannot prove that every legacy physics claim was semantically interpreted correctly."
        ),
        "truth_source": "migration_manifests_and_v5_registry_refs",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _resolve_migration_dir(ws: WorkspacePaths, migration_dir: str | Path | None) -> Path:
    if migration_dir:
        return _canonical_migration_dir(ws, Path(migration_dir))
    latest = _latest_canonical_legacy_run(ws)
    if latest is None:
        raise FileNotFoundError("no legacy-v5-lossless migration run found")
    return latest


def _canonical_migration_dir(ws: WorkspacePaths, migration_dir: Path) -> Path:
    if migration_dir.is_absolute() and _same_path_or_missing(migration_dir.parent.parent, ws.root):
        return migration_dir
    if migration_dir.is_absolute() and _looks_like_noncanonical_aitp_migration(migration_dir):
        latest = _latest_canonical_legacy_run(ws)
        if latest is not None:
            return latest
    if migration_dir.is_absolute() and migration_dir.exists():
        latest = _latest_legacy_run_under(migration_dir)
        if latest is not None:
            return latest
    name = migration_dir.name
    if name:
        canonical = ws.root / "migrations" / name
        if _is_migration_run_dir(canonical):
            return canonical
        latest = _latest_legacy_run_under(canonical)
        if latest is not None:
            return latest
        if not migration_dir.is_absolute() and len(migration_dir.parts) == 1 and name.startswith("legacy-v5-lossless-"):
            latest = _latest_canonical_legacy_run(ws)
            if latest is not None:
                return latest
    if not migration_dir.is_absolute():
        under_root = ws.root / migration_dir
        if _is_migration_run_dir(under_root):
            return under_root
        latest = _latest_legacy_run_under(under_root)
        if latest is not None:
            return latest
        if migration_dir.parts[:2] == (".aitp", "migrations") and name:
            canonical = ws.root / "migrations" / name
            if _is_migration_run_dir(canonical):
                return canonical
            latest = _latest_legacy_run_under(canonical)
            if latest is not None:
                return latest
            latest = _latest_canonical_legacy_run(ws)
            if latest is not None:
                return latest
    if _looks_like_noncanonical_aitp_migration(migration_dir):
        latest = _latest_canonical_legacy_run(ws)
        if latest is not None:
            return latest
    return migration_dir


def _latest_canonical_legacy_run(ws: WorkspacePaths) -> Path | None:
    return _latest_legacy_run_under(ws.root / "migrations")


def _latest_legacy_run_under(root: Path) -> Path | None:
    if not root.exists() or not root.is_dir():
        return None
    if _is_migration_run_dir(root):
        return root
    candidates = [
        path
        for path in root.glob("legacy-v5-lossless-*")
        if _is_migration_run_dir(path)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime_ns)


def _is_migration_run_dir(path: Path) -> bool:
    return path.is_dir() and (path / "migration_summary.json").exists()


def _looks_like_noncanonical_aitp_migration(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    return ".aitp" in parts and "migrations" in parts


def _same_path_or_missing(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return left.absolute() == right.absolute()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _file_preservation(summary: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    totals = summary.get("totals") if isinstance(summary.get("totals"), dict) else {}
    manifest = verification.get("manifest_check") if isinstance(verification.get("manifest_check"), dict) else {}
    pre_count = int(manifest.get("pre_count") or totals.get("legacy_file_count") or 0)
    post_count = int(manifest.get("post_count") or totals.get("post_legacy_file_count") or 0)
    missing = int(manifest.get("missing") or 0)
    extra = int(manifest.get("extra") or 0)
    changed = int(manifest.get("changed") or totals.get("legacy_manifest_change_count") or 0)
    ok = bool(verification.get("file_accounting_ok") is True) and missing == 0 and extra == 0 and changed == 0
    return {
        "ok": ok,
        "pre_count": pre_count,
        "post_count": post_count,
        "missing": missing,
        "extra": extra,
        "changed": changed,
        "legacy_manifest_hash_stable": bool(totals.get("legacy_manifest_hash_stable") is True),
    }


def _archive_reference_coverage(summary: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    totals = summary.get("totals") if isinstance(summary.get("totals"), dict) else {}
    check = (
        verification.get("archive_reference_check")
        if isinstance(verification.get("archive_reference_check"), dict)
        else {}
    )
    expected = int(check.get("archive_records_expected") or totals.get("archive_reference_count") or 0)
    checked = int(check.get("archive_records_checked") or 0)
    registry_count = int(check.get("registry_archive_reference_count") or 0)
    problem_count = int(check.get("problem_count") or totals.get("missing_archive_record_files") or 0)
    return {
        "ok": checked == expected and registry_count == expected and problem_count == 0,
        "expected": expected,
        "checked": checked,
        "registry_count": registry_count,
        "problem_count": problem_count,
    }


def _markdown_readability(verification: dict[str, Any]) -> dict[str, Any]:
    check = (
        verification.get("markdown_readability_check")
        if isinstance(verification.get("markdown_readability_check"), dict)
        else {}
    )
    problem_count = int(check.get("problem_count") or 0)
    return {
        "ok": problem_count == 0,
        "checked": int(check.get("markdown_files_checked") or 0),
        "problem_count": problem_count,
    }


def _topic_coverage(topic: dict[str, Any]) -> dict[str, Any]:
    file_count = int(topic.get("file_count") or 0)
    accounted = int(topic.get("accounted_file_count") or 0)
    missing_expected = [str(item) for item in topic.get("missing_expected_paths", []) if str(item)]
    status = str(topic.get("status") or "")
    unaccounted = max(file_count - accounted, 0)
    coverage_status = "accounted_needs_review" if status == "ok" and unaccounted == 0 else "coverage_gaps"
    written = topic.get("written_records") if isinstance(topic.get("written_records"), dict) else {}
    return {
        "topic": str(topic.get("topic") or ""),
        "status": status,
        "coverage_status": coverage_status,
        "file_count": file_count,
        "accounted_file_count": accounted,
        "unaccounted_file_count": unaccounted,
        "structured_file_count": int(topic.get("structured_file_count") or 0),
        "archive_reference_count": int(topic.get("archive_reference_count") or 0),
        "audit_mapped_file_count": int(topic.get("audit_mapped_file_count") or 0),
        "missing_expected_paths": missing_expected,
        "legacy_shape": "canonical_topic" if topic.get("can_write_v5_records") is True else "noncanonical_seed",
        "active_claim_id": str(topic.get("active_claim_id") or ""),
        "written_records": {str(key): int(value or 0) for key, value in written.items()},
        "preserved_source_refs": int(topic.get("preserved_source_refs") or 0),
        "audit_error": str(topic.get("audit_error") or ""),
        "semantic_review_required": True,
    }
