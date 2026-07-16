"""Fail-closed host filesystem checks for project-local Skill replacement."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import stat
from typing import Mapping

from brain.v5.skill_install_planning import (
    EMPTY_TREE_HASH,
    files_tree_hash,
    link_like,
    snapshot_target,
    target_paths,
)


class PinnedDirectories:
    """Pin directory identities while host mutation is in progress."""

    def __init__(self, *paths: Path, share_write: bool = True):
        self.paths = tuple(sorted({Path(path) for path in paths}, key=str))
        self.share_write = share_write
        self._handles = {}

    def __enter__(self):
        try:
            for path in self.paths:
                self._handles[_path_key(path)] = _open_directory(
                    path,
                    share_write=self.share_write,
                )
            self.assert_stable()
            return self
        except Exception:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, _exc_type, _exc, _traceback):
        for handle in reversed(list(self._handles.values())):
            _close_directory(handle)
        self._handles.clear()
        return False

    def assert_stable(self) -> None:
        for path in self.paths:
            _assert_directory_identity(path, self._handle(path))

    def mkdir(self, path: Path) -> None:
        parent = Path(path).parent
        self.assert_stable()
        if os.name == "nt":
            path.mkdir()
        else:
            os.mkdir(path.name, mode=0o700, dir_fd=self._handle(parent))

    def replace(self, source: Path, target: Path) -> None:
        source, target = Path(source), Path(target)
        self.assert_stable()
        if os.name == "nt":
            os.replace(source, target)
        else:
            os.replace(
                source.name,
                target.name,
                src_dir_fd=self._handle(source.parent),
                dst_dir_fd=self._handle(target.parent),
            )

    def rmtree(self, path: Path) -> None:
        path = Path(path)
        self.assert_stable()
        if os.name == "nt":
            shutil.rmtree(path)
        else:
            shutil.rmtree(path.name, dir_fd=self._handle(path.parent))

    def write_bytes(self, base: Path, parts: tuple[str, ...], content: bytes) -> None:
        self.assert_stable()
        if os.name == "nt":
            current = Path(base)
            parent_guard = self
            child_guards = []
            try:
                for part in parts[:-1]:
                    child = current / part
                    if child.exists():
                        if link_like(child) or not child.is_dir():
                            raise ValueError(
                                "Skill staging path contains a link or non-directory"
                            )
                    else:
                        parent_guard.mkdir(child)
                    child_guard = PinnedDirectories(child, share_write=False)
                    child_guard.__enter__()
                    child_guards.append(child_guard)
                    parent_guard = child_guard
                    current = child
                target = current / parts[-1]
                flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
                descriptor = os.open(target, flags, 0o600)
                try:
                    _write_all(descriptor, content)
                finally:
                    os.close(descriptor)
            finally:
                for guard in reversed(child_guards):
                    guard.__exit__(None, None, None)
            return
        _write_relative_posix(self._handle(base), parts, content)

    def _handle(self, path: Path):
        try:
            return self._handles[_path_key(path)]
        except KeyError as exc:
            raise ValueError(f"directory is not pinned: {path}") from exc


def stage_path_for(ws, application_id: str) -> Path:
    if Path(application_id).name != application_id:
        raise ValueError("Skill install application id is not path-safe")
    root = ws.root.resolve(strict=True)
    if link_like(ws.root):
        raise ValueError("AITP runtime root cannot be a link or junction")
    return root / "runtime" / "skill_install_staging" / application_id


def ensure_stage_parent(ws, stage: Path) -> None:
    root = ws.root.resolve(strict=True)
    expected = root / "runtime" / "skill_install_staging"
    if stage.parent != expected:
        raise ValueError("Skill staging path escaped the AITP runtime")
    _ensure_descendant_directories(root, expected)


def ensure_target_parent(plan, target: Path) -> None:
    root, expected_target = target_paths(plan.target_root, plan.name)
    if expected_target != target:
        raise ValueError("Skill target parent derivation changed")
    _ensure_descendant_directories(root, target.parent)


def materialize_stage(stage: Path, files: Mapping[str, bytes]) -> None:
    if stage.exists():
        if link_like(stage):
            raise ValueError("Skill staging path cannot be a link or junction")
        staged_hash, _manifest = snapshot_target(stage)
        if staged_hash != files_tree_hash(files):
            raise ValueError("existing Skill staging bytes changed after approval")
        return
    with PinnedDirectories(stage.parent) as parent_guard:
        parent_guard.mkdir(stage)
    with PinnedDirectories(stage, share_write=False) as stage_guard:
        for relative, content in files.items():
            parts = relative.split("/")
            if any(part in {"", ".", ".."} for part in parts):
                raise ValueError("Skill package contains an unsafe path")
            stage_guard.write_bytes(stage, tuple(parts), content)
    staged_hash, _manifest = snapshot_target(stage)
    if staged_hash != files_tree_hash(files):
        raise RuntimeError("Skill staging readback failed")


def revalidate_materialization_boundary(
    plan,
    *,
    target: Path,
    stage: Path,
    expected_target_hash: str,
    expected_stage_hash: str,
    guard: PinnedDirectories | None = None,
) -> None:
    if guard is not None:
        guard.assert_stable()
    root, expected_target = target_paths(plan.target_root, plan.name)
    if root != Path(plan.target_root) or expected_target != target:
        raise ValueError("Skill install target boundary changed after approval")
    target_hash, _manifest = snapshot_target(target)
    if target_hash != expected_target_hash:
        raise ValueError("Skill install target changed during staging")
    if not stage.exists() or link_like(stage):
        raise ValueError("Skill install staging path changed during validation")
    stage_hash, _manifest = snapshot_target(stage)
    if stage_hash != expected_stage_hash:
        raise ValueError("Skill install staging bytes changed during validation")


def require_exact_backup(backup: Path, before_hash: str) -> None:
    if before_hash == EMPTY_TREE_HASH:
        if backup.exists():
            raise RuntimeError("unexpected Skill backup exists for an absent before-image")
        return
    if not backup.exists() or link_like(backup):
        raise RuntimeError("Skill backup is missing or link-like")
    backup_hash, _manifest = snapshot_target(backup)
    if backup_hash != before_hash:
        raise RuntimeError("Skill backup does not match the approved before-image")


def cleanup_backup(path: Path) -> None:
    if not path.exists():
        return
    if link_like(path):
        raise RuntimeError("Skill install backup became a link")
    with PinnedDirectories(path.parent) as guard:
        guard.rmtree(path)


def _ensure_descendant_directories(root: Path, descendant: Path) -> None:
    root = root.resolve(strict=True)
    try:
        parts = descendant.relative_to(root).parts
    except ValueError as exc:
        raise ValueError("Skill host directory escaped its approved root") from exc
    current = root
    for part in parts:
        child = current / part
        with PinnedDirectories(current) as guard:
            if child.exists():
                if link_like(child) or not child.is_dir():
                    raise ValueError("Skill host path contains a link or non-directory")
            else:
                guard.mkdir(child)
        current = child
    if current != descendant or link_like(current) or not current.is_dir():
        raise ValueError("Skill host directory identity changed during creation")


def _path_key(path: Path) -> str:
    return os.path.normcase(str(Path(path).absolute()))


def _open_directory(path: Path, *, share_write: bool):
    path = Path(path)
    if not path.is_dir() or link_like(path):
        raise ValueError(f"cannot pin link-like or missing directory: {path}")
    if os.name == "nt":
        return _open_windows_directory(path, share_write=share_write)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ValueError(f"pinned path is not a directory: {path}")
    return descriptor


def _close_directory(handle) -> None:
    if os.name == "nt":
        import ctypes

        ctypes.windll.kernel32.CloseHandle(handle)
    else:
        os.close(handle)


def _assert_directory_identity(path: Path, handle) -> None:
    if os.name == "nt":
        attributes = _windows_handle_attributes(handle)
        if attributes & 0x00000400 or not attributes & 0x00000010:
            raise ValueError(f"pinned handle is link-like or not a directory: {path}")
        if link_like(path) or not path.is_dir():
            raise ValueError(f"pinned directory path changed: {path}")
        return
    opened = os.fstat(handle)
    try:
        current = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        raise ValueError(f"pinned directory path disappeared: {path}") from exc
    if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
        raise ValueError(f"pinned directory identity changed: {path}")


def _open_windows_directory(path: Path, *, share_write: bool):
    import ctypes
    from ctypes import wintypes

    create_file = ctypes.windll.kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    handle = create_file(
        str(path),
        0x00010000 | 0x0080,
        0x00000001 | (0x00000002 if share_write else 0),
        None,
        3,
        0x02000000 | 0x00200000,
        None,
    )
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    attributes = _windows_handle_attributes(handle)
    if attributes & 0x00000400 or not attributes & 0x00000010:
        ctypes.windll.kernel32.CloseHandle(handle)
        raise ValueError(f"cannot pin a link-like or non-directory path: {path}")
    return handle


def _windows_handle_attributes(handle) -> int:
    import ctypes
    from ctypes import wintypes

    class FileInformation(ctypes.Structure):
        _fields_ = [
            ("attributes", wintypes.DWORD),
            ("creation_time", wintypes.FILETIME),
            ("access_time", wintypes.FILETIME),
            ("write_time", wintypes.FILETIME),
            ("volume_serial", wintypes.DWORD),
            ("size_high", wintypes.DWORD),
            ("size_low", wintypes.DWORD),
            ("links", wintypes.DWORD),
            ("index_high", wintypes.DWORD),
            ("index_low", wintypes.DWORD),
        ]

    information = FileInformation()
    if not ctypes.windll.kernel32.GetFileInformationByHandle(
        handle,
        ctypes.byref(information),
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return int(information.attributes)


def _write_relative_posix(root_descriptor: int, parts: tuple[str, ...], content: bytes) -> None:
    current = os.dup(root_descriptor)
    try:
        for part in parts[:-1]:
            try:
                os.mkdir(part, mode=0o700, dir_fd=current)
            except FileExistsError:
                pass
            child = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=current,
            )
            os.close(current)
            current = child
        descriptor = os.open(
            parts[-1],
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=current,
        )
        try:
            _write_all(descriptor, content)
        finally:
            os.close(descriptor)
    finally:
        os.close(current)


def _write_all(descriptor: int, content: bytes) -> None:
    view = memoryview(content)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise OSError("Skill staging write did not make progress")
        view = view[written:]
    os.fsync(descriptor)
