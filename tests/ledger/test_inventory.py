from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from aitp.core import AITPError, build_inventory, init_workspace


def make_store(tmp_path: Path) -> Path:
    root = tmp_path / "store"
    root.mkdir()
    result = init_workspace(root, "nio", "Magnetic NiO")
    assert result["status"] == "initialized"
    return root


def make_tree(tmp_path: Path) -> Path:
    tree = tmp_path / "legacy"
    (tree / "theory").mkdir(parents=True)
    (tree / "theory" / "notes.md").write_text("note a\n", encoding="utf-8")
    (tree / "data").mkdir()
    (tree / "data" / "run.dat").write_text("1.0\n2.0\n", encoding="utf-8")
    (tree / "README.md").write_text("# Legacy\n", encoding="utf-8")
    return tree


def read_manifest(root: Path, name: str) -> dict:
    path = root / ".aitp" / "local" / "legacy" / f"{name}-inventory.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_inventory_scans_and_hashes_skipping_store(tmp_path: Path) -> None:
    root = make_store(tmp_path)
    payload = build_inventory(root, root, "corpus")
    assert payload["status"] == "ok"
    assert payload["name"] == "corpus"
    assert (root / ".aitp" / "local" / "legacy" / "corpus-inventory.json").is_file()

    manifest = read_manifest(root, "corpus")
    assert manifest["schema"] == "aitp/legacy-inventory-0.1"
    assert manifest["name"] == "corpus"
    assert manifest["root"] == str(root.resolve())
    assert payload["manifest"] == ".aitp/local/legacy/corpus-inventory.json"
    assert payload["files"] == len(manifest["files"])
    assert payload["bytes"] == sum(item["bytes"] for item in manifest["files"])

    by_path = {item["path"]: item for item in manifest["files"]}
    assert ".aitp/STORE.toml" not in by_path
    assert ".aitp/topic/TOPIC.md" not in by_path
    assert ".aitp/local/config.toml" not in by_path
    assert "README.md" in by_path
    assert "theory/README.md" in by_path
    for relative, item in by_path.items():
        full = root / relative
        assert full.is_file()
        assert item["sha256"] == hashlib.sha256(full.read_bytes()).hexdigest()
        assert item["bytes"] == full.stat().st_size


def test_inventory_skips_git_directories_at_any_depth(tmp_path: Path) -> None:
    root = make_store(tmp_path)
    tree = make_tree(tmp_path)
    (tree / ".git").mkdir()
    (tree / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (tree / "nested" / ".git").mkdir(parents=True)
    (tree / "nested" / ".git" / "config").write_text("[core]\n", encoding="utf-8")
    (tree / "worktree").mkdir()
    (tree / "worktree" / ".git").write_text("gitdir: /elsewhere\n", encoding="utf-8")

    build_inventory(root, tree, "corpus")
    paths = [item["path"] for item in read_manifest(root, "corpus")["files"]]
    assert ".git/HEAD" not in paths
    assert "nested/.git/config" not in paths
    assert "worktree/.git" not in paths
    assert "README.md" in paths
    assert "data/run.dat" in paths


def test_inventory_records_symlinks_without_hashing(tmp_path: Path) -> None:
    root = make_store(tmp_path)
    tree = make_tree(tmp_path)
    (tree / "data" / "link.dat").symlink_to("run.dat")
    (tree / "linked-dir").symlink_to("data", target_is_directory=True)

    build_inventory(root, tree, "corpus")
    by_path = {item["path"]: item for item in read_manifest(root, "corpus")["files"]}
    assert by_path["data/link.dat"] == {
        "path": "data/link.dat",
        "type": "symlink",
    }
    assert by_path["linked-dir"] == {"path": "linked-dir", "type": "symlink"}
    assert "linked-dir/run.dat" not in by_path
    assert all("sha256" not in item for item in by_path.values() if item["path"].startswith(("data/link.dat", "linked-dir")))


def test_inventory_overwrites_same_name(tmp_path: Path) -> None:
    root = make_store(tmp_path)
    tree = make_tree(tmp_path)
    build_inventory(root, tree, "corpus")
    first = read_manifest(root, "corpus")
    (tree / "extra.txt").write_text("more\n", encoding="utf-8")

    build_inventory(root, tree, "corpus")
    second = read_manifest(root, "corpus")
    paths = [item["path"] for item in second["files"]]
    assert "extra.txt" in paths
    assert len(first["files"]) + 1 == len(second["files"])
    legacy_dir = root / ".aitp" / "local" / "legacy"
    assert sorted(path.name for path in legacy_dir.iterdir()) == [
        "corpus-inventory.json"
    ]


def test_inventory_requires_store(tmp_path: Path) -> None:
    tree = make_tree(tmp_path)
    with pytest.raises(AITPError) as error:
        build_inventory(tmp_path, tree, "corpus")
    assert error.value.code == "not_initialized"


def test_inventory_manifest_matches_sha256sum(tmp_path: Path) -> None:
    root = make_store(tmp_path)
    tree = make_tree(tmp_path)
    build_inventory(root, tree, "corpus")
    by_path = {
        item["path"]: item
        for item in read_manifest(root, "corpus")["files"]
        if "sha256" in item
    }
    for relative in ["README.md", "data/run.dat"]:
        path = tree / relative
        result = subprocess.run(
            ["sha256sum", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
        assert by_path[relative]["sha256"] == result.stdout.split()[0]
