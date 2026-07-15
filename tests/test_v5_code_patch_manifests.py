from __future__ import annotations

import hashlib
import subprocess

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="patch-manifest-test", host="pytest")


def test_declared_patch_manifest_captures_bytes_but_cannot_claim_repository_coverage(tmp_path):
    from brain.v5.code_patch_manifests import PatchEntryRequest, capture_code_patch_manifest
    from brain.v5.pinned_record_refs import build_frozen_dependency_manifest
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "workspace")
    files = tmp_path / "changed"
    files.mkdir()
    tracked = files / "src.cpp"
    tracked.write_text("int value = 42;\n", encoding="utf-8")
    binary = files / "table.bin"
    binary.write_bytes(b"\x00\x01\x02\xff")
    untracked = files / "submit.slurm"
    untracked.write_text("#!/bin/bash\nsrun librpa\n", encoding="utf-8")
    deleted_before = hashlib.sha256(b"old input\n").hexdigest()

    capture = capture_code_patch_manifest(
        ws,
        repo_id="librpa",
        base_commit="a" * 40,
        entries=[
            PatchEntryRequest(
                path="src/headwing.cpp",
                change_kinds=("staged", "unstaged"),
                source_path=str(tracked),
            ),
            PatchEntryRequest(
                path="tests/reference/table.bin",
                change_kinds=("binary",),
                source_path=str(binary),
            ),
            PatchEntryRequest(
                path="scripts/submit.slurm",
                change_kinds=("required_untracked",),
                source_path=str(untracked),
            ),
            PatchEntryRequest(
                path="inputs/obsolete.in",
                change_kinds=("deleted",),
                deleted=True,
                before_sha256=deleted_before,
            ),
            PatchEntryRequest(
                path="thirdparty/LibComm",
                change_kinds=("submodule",),
                submodule_commit="b" * 40,
            ),
        ],
        actor=_actor(),
    )
    replay = capture_code_patch_manifest(
        ws,
        repo_id="librpa",
        base_commit="a" * 40,
        entries=[
            PatchEntryRequest(
                path="src/headwing.cpp",
                change_kinds=("unstaged", "staged"),
                source_path=str(tracked),
            ),
            PatchEntryRequest(
                path="tests/reference/table.bin",
                change_kinds=("binary",),
                source_path=str(binary),
            ),
            PatchEntryRequest(
                path="scripts/submit.slurm",
                change_kinds=("required_untracked",),
                source_path=str(untracked),
            ),
            PatchEntryRequest(
                path="inputs/obsolete.in",
                change_kinds=("deleted",),
                deleted=True,
                before_sha256=deleted_before,
            ),
            PatchEntryRequest(
                path="thirdparty/LibComm",
                change_kinds=("submodule",),
                submodule_commit="b" * 40,
            ),
        ],
        actor=_actor(),
    )

    assert replay.pinned_ref == capture.pinned_ref
    assert replay.write_status == "unchanged"
    assert capture.record.coverage_complete is False
    assert capture.record.coverage_basis == "declared_entries_only"
    assert capture.record.excluded_required_paths == []
    by_path = {entry["path"]: entry for entry in capture.record.entries}
    assert by_path["src/headwing.cpp"]["change_kinds"] == ["staged", "unstaged"]
    assert by_path["src/headwing.cpp"]["blob_receipt_ref"]
    assert by_path["tests/reference/table.bin"]["blob_receipt_ref"]
    assert by_path["scripts/submit.slurm"]["blob_receipt_ref"]
    assert by_path["inputs/obsolete.in"]["before_sha256"] == deleted_before
    assert by_path["inputs/obsolete.in"]["blob_receipt_ref"] == ""
    assert by_path["thirdparty/LibComm"]["submodule_commit"] == "b" * 40

    closure = build_frozen_dependency_manifest(ws, [capture.pinned_ref])
    assert len(closure.nodes) == 4
    assert len(closure.edges) == 3
    assert all(edge.field_name == "entries[].blob_receipt_ref" for edge in closure.edges)


def test_git_patch_manifest_covers_status_and_preserves_index_and_worktree_bytes(tmp_path):
    from brain.v5.code_patch_manifests import capture_git_code_patch_manifest
    from brain.v5.pinned_record_refs import build_frozen_dependency_manifest
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "workspace")
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "aitp@example.invalid")
    _git(repo, "config", "user.name", "AITP Test")
    source = repo / "src.cpp"
    source.write_text("int value = 1;\n", encoding="utf-8")
    obsolete = repo / "obsolete.in"
    obsolete.write_text("old input\n", encoding="utf-8")
    _git(repo, "add", "src.cpp", "obsolete.in")
    _git(repo, "commit", "-m", "base")
    base_commit = _git(repo, "rev-parse", "HEAD").stdout.decode("ascii").strip()

    index_bytes = b"int value = 2;\n"
    worktree_bytes = b"int value = 3;\n"
    source.write_bytes(index_bytes)
    _git(repo, "add", "src.cpp")
    source.write_bytes(worktree_bytes)
    _git(repo, "rm", "obsolete.in")
    untracked = repo / "submit.slurm"
    untracked.write_bytes(b"#!/bin/bash\nsrun librpa\n")

    capture = capture_git_code_patch_manifest(
        ws,
        repo_path=repo,
        repo_id="librpa",
        actor=_actor(),
    )

    assert capture.record.base_commit == base_commit
    assert capture.record.coverage_complete is True
    assert capture.record.coverage_basis == "git_status_porcelain_v1_z"
    assert capture.record.observed_paths == ["obsolete.in", "src.cpp", "submit.slurm"]
    by_path = {entry["path"]: entry for entry in capture.record.entries}
    source_entry = by_path["src.cpp"]
    assert source_entry["change_kinds"] == ["staged", "unstaged"]
    assert source_entry["index_byte_sha256"] == hashlib.sha256(index_bytes).hexdigest()
    assert source_entry["byte_sha256"] == hashlib.sha256(worktree_bytes).hexdigest()
    assert source_entry["index_blob_receipt_ref"]
    assert source_entry["blob_receipt_ref"]
    assert source_entry["index_blob_receipt_ref"] != source_entry["blob_receipt_ref"]
    assert by_path["obsolete.in"]["deleted"] is True
    assert by_path["obsolete.in"]["before_sha256"] == hashlib.sha256(b"old input\n").hexdigest()
    assert by_path["submit.slurm"]["change_kinds"] == ["required_untracked"]

    closure = build_frozen_dependency_manifest(ws, [capture.pinned_ref])
    assert source_entry["index_blob_receipt_ref"] in {node.record_ref for node in closure.nodes}
    assert source_entry["blob_receipt_ref"] in {node.record_ref for node in closure.nodes}
    assert {
        edge.field_name for edge in closure.edges if edge.owner_ref == capture.pinned_ref.record_ref
    } == {
        "entries[].blob_receipt_ref",
        "entries[].index_blob_receipt_ref",
    }


def test_excluded_required_bytes_make_patch_manifest_non_reproducible(tmp_path):
    from brain.v5.code_patch_manifests import PatchEntryRequest, capture_code_patch_manifest
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    capture = capture_code_patch_manifest(
        ws,
        repo_id="librpa",
        base_commit="c" * 40,
        entries=[
            PatchEntryRequest(
                path="private/generated-input.dat",
                change_kinds=("required_untracked",),
                excluded_reason="sensitive bytes were not captured",
            )
        ],
        actor=_actor(),
    )

    assert capture.record.coverage_complete is False
    assert capture.record.excluded_required_paths == ["private/generated-input.dat"]
    assert capture.record.entries[0]["blob_receipt_ref"] == ""


def test_git_patch_manifest_rejects_dirty_submodule_worktree(tmp_path):
    from brain.v5.code_patch_manifests import capture_git_code_patch_manifest
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "workspace")
    child = tmp_path / "child"
    child.mkdir()
    _git(child, "init")
    _git(child, "config", "user.email", "aitp@example.invalid")
    _git(child, "config", "user.name", "AITP Test")
    (child / "solver.cpp").write_text("int value = 1;\n", encoding="utf-8")
    _git(child, "add", "solver.cpp")
    _git(child, "commit", "-m", "child base")

    parent = tmp_path / "parent"
    parent.mkdir()
    _git(parent, "init")
    _git(parent, "config", "user.email", "aitp@example.invalid")
    _git(parent, "config", "user.name", "AITP Test")
    _git(
        parent,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        str(child),
        "deps/sub",
    )
    _git(parent, "commit", "-m", "parent base")
    (parent / "deps" / "sub" / "solver.cpp").write_text(
        "int value = 2;\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="dirty submodule"):
        capture_git_code_patch_manifest(
            ws,
            repo_path=parent,
            repo_id="parent",
            actor=_actor(),
        )

    submodule = parent / "deps" / "sub"
    _git(submodule, "config", "user.email", "aitp@example.invalid")
    _git(submodule, "config", "user.name", "AITP Test")
    _git(submodule, "add", "solver.cpp")
    _git(submodule, "commit", "-m", "advance child")
    actual_head = _git(submodule, "rev-parse", "HEAD").stdout.decode("ascii").strip()

    capture = capture_git_code_patch_manifest(
        ws,
        repo_path=parent,
        repo_id="parent",
        actor=_actor(),
    )

    assert capture.record.entries[0]["submodule_commit"] == actual_head


def test_git_patch_manifest_rechecks_submodule_after_final_parent_status(
    tmp_path,
    monkeypatch,
):
    from brain.v5 import git_patch_capture
    from brain.v5.code_patch_manifests import capture_git_code_patch_manifest
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "workspace")
    child = tmp_path / "child-race"
    child.mkdir()
    _git(child, "init")
    _git(child, "config", "user.email", "aitp@example.invalid")
    _git(child, "config", "user.name", "AITP Test")
    (child / "solver.cpp").write_text("int value = 1;\n", encoding="utf-8")
    _git(child, "add", "solver.cpp")
    _git(child, "commit", "-m", "child base")

    parent = tmp_path / "parent-race"
    parent.mkdir()
    _git(parent, "init")
    _git(parent, "config", "user.email", "aitp@example.invalid")
    _git(parent, "config", "user.name", "AITP Test")
    _git(
        parent,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        str(child),
        "deps/sub",
    )
    _git(parent, "commit", "-m", "parent base")
    submodule = parent / "deps" / "sub"
    _git(submodule, "config", "user.email", "aitp@example.invalid")
    _git(submodule, "config", "user.name", "AITP Test")
    (submodule / "solver.cpp").write_text("int value = 2;\n", encoding="utf-8")
    _git(submodule, "add", "solver.cpp")
    _git(submodule, "commit", "-m", "advance child")

    original_status = git_patch_capture._git_status
    calls = 0

    def status_then_race(repo):
        nonlocal calls
        calls += 1
        payload = original_status(repo)
        if calls == 2:
            (submodule / "solver.cpp").write_text("dirty after status\n", encoding="utf-8")
        return payload

    monkeypatch.setattr(git_patch_capture, "_git_status", status_then_race)

    with pytest.raises(RuntimeError, match="submodule changed"):
        capture_git_code_patch_manifest(
            ws,
            repo_path=parent,
            repo_id="parent-race",
            actor=_actor(),
        )


@pytest.mark.parametrize(
    "entry",
    [
        lambda: {"path": "../escape", "change_kinds": ("staged",)},
        lambda: {"path": "C:/absolute.dat", "change_kinds": ("staged",)},
        lambda: {"path": "src/file.cpp", "change_kinds": ("unknown",)},
    ],
)
def test_patch_manifest_rejects_unsafe_paths_and_unknown_states(tmp_path, entry):
    from brain.v5.code_patch_manifests import PatchEntryRequest, capture_code_patch_manifest
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    with pytest.raises(ValueError):
        capture_code_patch_manifest(
            ws,
            repo_id="librpa",
            base_commit="d" * 40,
            entries=[PatchEntryRequest(**entry())],
            actor=_actor(),
        )


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
    )
