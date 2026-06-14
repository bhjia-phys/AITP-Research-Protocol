"""Discovery helpers for workspace migration artifacts."""

from __future__ import annotations

from pathlib import Path

from brain.v5.paths import WorkspacePaths


def latest_workspace_migration_plan(ws: WorkspacePaths) -> Path | None:
    """Return the latest saved workspace migration plan, if one exists."""

    return _latest_file(ws, "workspace_migration_plan.json")


def latest_workspace_old_store_manifest(ws: WorkspacePaths) -> Path | None:
    """Return the latest saved old-store manifest, if one exists."""

    return _latest_file(ws, "workspace_old_store_manifest.json")


def latest_workspace_recovery_audit(ws: WorkspacePaths) -> Path | None:
    """Return the latest saved workspace recovery audit, if one exists."""

    return _latest_file(ws, "workspace_recovery_audit.json")


def latest_workspace_file_migration_ledger(ws: WorkspacePaths) -> Path | None:
    """Return the latest saved file-level migration ledger, if one exists."""

    return _latest_file(ws, "workspace_file_migration_ledger.json")


def latest_legacy_accounting_dir(ws: WorkspacePaths) -> Path | None:
    """Return the latest legacy L0-L4 accounting directory, if one exists."""

    migrations = ws.root / "migrations"
    if not migrations.exists():
        return None
    candidates = []
    for manifest in migrations.rglob("file_manifest.json"):
        parent = manifest.parent
        if (parent / "migration_summary.json").exists():
            candidates.append(parent)
    if not candidates:
        return None
    return max(candidates, key=_sort_key)


def _latest_file(ws: WorkspacePaths, filename: str) -> Path | None:
    migrations = ws.root / "migrations"
    if not migrations.exists():
        return None
    candidates = [path for path in migrations.rglob(filename) if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=_sort_key)


def _sort_key(path: Path) -> tuple[float, str]:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0.0
    return (mtime, path.as_posix())
