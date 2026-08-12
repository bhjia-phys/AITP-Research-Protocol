"""Write-lock staleness and liveness tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from aitp.core import AITPError
from aitp.workspace import _lock_owner_alive, store_lock


def _lock_path(root: Path) -> Path:
    path = root / ".aitp" / "local" / "locks" / "write.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def test_stale_lock_from_dead_owner_is_broken(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    lock = _lock_path(root)
    lock.write_text("999999999", encoding="utf-8")

    assert _lock_owner_alive(lock) is False
    with store_lock(root):
        assert lock.read_text(encoding="utf-8").strip() == str(os.getpid())
    assert not lock.exists()


def test_legacy_pidless_lock_is_stale(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    lock = _lock_path(root)
    lock.write_text("", encoding="utf-8")

    assert _lock_owner_alive(lock) is False
    with store_lock(root):
        pass
    assert not lock.exists()


def test_live_lock_still_blocks(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    lock = _lock_path(root)
    lock.write_text(str(os.getpid()), encoding="utf-8")

    assert _lock_owner_alive(lock) is True
    with pytest.raises(AITPError) as excinfo:
        with store_lock(root):
            pass
    assert excinfo.value.code == "store_busy"
    assert lock.exists()  # a live lock is never broken
