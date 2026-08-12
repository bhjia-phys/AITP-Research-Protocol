from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from aitp import workspace
from aitp.core import AITPError, adopt_workspace, enter_workspace


def populated(tmp_path: Path) -> Path:
    root = tmp_path / "research"
    (root / "theory" / "notes").mkdir(parents=True)
    (root / "theory" / "notes" / "a.md").write_text("note a\n", encoding="utf-8")
    (root / "data" / "run-1").mkdir(parents=True)
    (root / "data" / "run-1" / "out.dat").write_text("1.0\n2.0\n", encoding="utf-8")
    (root / "README.md").write_text("# My research\n", encoding="utf-8")
    (root / ".git").mkdir(parents=True)
    (root / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (root / "deep" / "a" / "b").mkdir(parents=True)
    (root / "deep" / "a" / "b" / "file.txt").write_text("deep\n", encoding="utf-8")
    return root


def test_adopt_populated_tree_untouched(tmp_path: Path) -> None:
    root = populated(tmp_path)

    def tree_hash() -> dict[str, str]:
        return {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*"))
            if path.is_file() and ".aitp" not in path.parts
        }

    before = tree_hash()
    result = adopt_workspace(root, "legacy", "Legacy research")
    assert result["status"] == "initialized"
    assert result["mode"] == "adopt"
    assert tree_hash() == before


def test_adopt_creates_exact_store(tmp_path: Path) -> None:
    root = tmp_path / "research"
    root.mkdir()
    (root / "notes.md").write_text("keep\n", encoding="utf-8")
    result = adopt_workspace(root, "legacy", "Legacy research")

    assert sorted(result["created_files"]) == [
        ".aitp/.gitignore",
        ".aitp/STORE.toml",
        ".aitp/local/config.toml",
        ".aitp/topic/TOPIC.md",
    ]
    for path in result["created_files"]:
        assert (root / path).is_file()
    for directory in [
        ".aitp/topic/entries",
        ".aitp/topic/notes",
        ".aitp/local/drafts",
        ".aitp/local/locks",
    ]:
        assert (root / directory).is_dir()
    for absent in [
        "README.md",
        ".gitignore",
        "theory",
        "software",
        "calculations",
        "data",
        "figures",
        "references",
        "manuscripts",
    ]:
        assert not (root / absent).exists()


def test_adopt_refuses_existing_store(tmp_path: Path) -> None:
    root = populated(tmp_path)
    adopt_workspace(root, "legacy", "Legacy research")
    with pytest.raises(AITPError) as error:
        adopt_workspace(root, "legacy", "Legacy research")
    assert error.value.code == "already_initialized"


def test_adopt_dry_run_writes_nothing(tmp_path: Path) -> None:
    root = populated(tmp_path)
    result = adopt_workspace(root, "legacy", "Legacy research", dry_run=True)
    assert result["status"] == "dry_run"
    assert result["mode"] == "adopt"
    assert not (root / ".aitp").exists()


def test_adopt_rollback_on_conflict(tmp_path: Path, monkeypatch) -> None:
    root = populated(tmp_path)
    calls = {"count": 0}
    original = workspace.atomic_write

    def failing_write(path: Path, text: str) -> None:
        calls["count"] += 1
        if calls["count"] >= 2:
            raise OSError("simulated write failure")
        return original(path, text)

    monkeypatch.setattr(workspace, "atomic_write", failing_write)
    with pytest.raises(OSError, match="simulated"):
        adopt_workspace(root, "legacy", "Legacy research")
    assert not (root / ".aitp").exists()
    assert (root / "theory" / "notes" / "a.md").read_text(encoding="utf-8") == (
        "note a\n"
    )


def test_adopt_then_enter(tmp_path: Path) -> None:
    root = populated(tmp_path)
    adopt_workspace(root, "legacy", "Legacy research")
    brief = enter_workspace(root)
    assert brief["memory_status"] == "not_established"
    assert brief["topic"]["id"] == "legacy"
    assert brief["recent_entries"] == []
    assert brief["counts"]["active"] == 0
