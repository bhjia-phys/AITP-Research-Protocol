"""Ranked cross-process advisory locks for query-index publication."""

from __future__ import annotations

import errno
import os
import threading
import time
from pathlib import Path

from brain.v5.paths import WorkspacePaths


LOCK_RANKS = {
    "base-build": 0,
    "canonical-mutation": 1,
    "canonical-record": 2,
    "delta-manifest": 3,
}


class QueryIndexLockError(RuntimeError):
    """Base class for ranked lock failures."""


class LockOrderError(QueryIndexLockError):
    """Raised when a caller attempts a later-to-earlier acquisition."""


class LockReentrancyError(QueryIndexLockError):
    """Raised when one thread reacquires the same ranked lock."""


class LockTimeoutError(QueryIndexLockError):
    """Raised when an advisory lock cannot be acquired before its deadline."""


class LockOwnershipError(QueryIndexLockError):
    """Raised when a lease is released by a foreign owner or out of order."""


_registry_guard = threading.Lock()
_process_locks: dict[str, threading.Lock] = {}
_thread_state = threading.local()


class RankedLockLease:
    """One owned advisory lock with explicit rank and lifetime."""

    def __init__(
        self,
        ws: WorkspacePaths,
        name: str,
        *,
        timeout_seconds: float = 2.0,
        lock_path: Path | None = None,
    ) -> None:
        if name not in LOCK_RANKS:
            raise ValueError(f"unknown ranked lock: {name}")
        self.ws = ws
        self.name = name
        self.rank = LOCK_RANKS[name]
        self.timeout_seconds = max(0.0, float(timeout_seconds))
        self.path = _validated_lock_path(ws, lock_path or _lock_path(ws, name))
        self.pid = os.getpid()
        self.thread_id = threading.get_ident()
        self.descriptor: int | None = None
        self._process_lock: threading.Lock | None = None
        self._active = False
        self._released = False

    @property
    def active(self) -> bool:
        return self._active and not self._released

    def __enter__(self) -> RankedLockLease:
        if self.active or self._released:
            raise LockReentrancyError(f"reentrant ranked lock lease: {self.name}")
        self._validate_order()
        process_lock = _process_lock_for(self.path)
        acquired = process_lock.acquire(timeout=self.timeout_seconds)
        if not acquired:
            raise LockTimeoutError(f"timed out acquiring ranked lock: {self.name}")
        self._process_lock = process_lock
        descriptor: int | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
            _ensure_lock_byte(descriptor)
            _acquire_os_lock(descriptor, self.timeout_seconds, self.name)
            self.descriptor = descriptor
            descriptor = None
            self._active = True
            _held_stack().append(self)
            return self
        except Exception:
            if descriptor is not None:
                os.close(descriptor)
            self._process_lock = None
            process_lock.release()
            raise

    def release(self) -> None:
        if not self.active:
            raise LockOwnershipError(f"ranked lock lease is not active: {self.name}")
        if os.getpid() != self.pid or threading.get_ident() != self.thread_id:
            raise LockOwnershipError(f"ranked lock lease has a foreign owner: {self.name}")
        stack = _held_stack()
        if not stack or stack[-1] is not self:
            raise LockOwnershipError(f"ranked lock release is not LIFO: {self.name}")
        stack.pop()
        descriptor = self.descriptor
        process_lock = self._process_lock
        self.descriptor = None
        self._process_lock = None
        self._active = False
        self._released = True
        try:
            if descriptor is not None:
                try:
                    _release_os_lock(descriptor)
                finally:
                    os.close(descriptor)
        finally:
            if process_lock is not None:
                process_lock.release()

    def __exit__(self, exc_type, exc, traceback) -> bool:
        self.release()
        return False

    def _validate_order(self) -> None:
        stack = _held_stack()
        for lease in stack:
            if lease.path == self.path:
                raise LockReentrancyError(f"reentrant ranked lock: {self.name}")
        if stack and self.rank <= stack[-1].rank:
            raise LockOrderError(
                f"lock order inversion: {stack[-1].name} -> {self.name}"
            )


def acquire_ranked_lock(
    ws: WorkspacePaths,
    name: str,
    *,
    timeout_seconds: float = 2.0,
    lock_path: Path | None = None,
) -> RankedLockLease:
    """Create a ranked lease; acquisition begins when entering the context."""

    return RankedLockLease(
        ws,
        name,
        timeout_seconds=timeout_seconds,
        lock_path=lock_path,
    )


class CanonicalMutationLease:
    """Thread-bound owner of the canonical-mutation rank."""

    def __init__(self, ws: WorkspacePaths, *, timeout_seconds: float = 2.0) -> None:
        self.ws = ws
        self._ranked = acquire_ranked_lock(
            ws,
            "canonical-mutation",
            timeout_seconds=timeout_seconds,
        )
        self._entered = False

    @property
    def active(self) -> bool:
        return self._entered and self._ranked.active

    def __enter__(self) -> CanonicalMutationLease:
        self._ranked.__enter__()
        self._entered = True
        _mutation_stack().append(self)
        return self

    def assert_active(self, ws: WorkspacePaths) -> None:
        if not self.active:
            raise LockOwnershipError("canonical mutation lease is not active")
        if (
            os.getpid() != self._ranked.pid
            or threading.get_ident() != self._ranked.thread_id
        ):
            raise LockOwnershipError("canonical mutation lease has a foreign owner")
        if self.ws.root.resolve() != ws.root.resolve():
            raise LockOwnershipError("canonical mutation lease belongs to another workspace")

    def release(self) -> None:
        self.assert_active(self.ws)
        stack = _mutation_stack()
        if not stack or stack[-1] is not self:
            raise LockOwnershipError("canonical mutation lease release is not LIFO")
        stack.pop()
        self._entered = False
        self._ranked.release()

    def __exit__(self, exc_type, exc, traceback) -> bool:
        self.release()
        return False


class IndexBuildLease:
    """Hold base-build and canonical-mutation across one full publication."""

    def __init__(
        self,
        ws: WorkspacePaths,
        *,
        reason: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.ws = ws
        self.reason = str(reason or "query-index-build")
        self._base = acquire_ranked_lock(
            ws,
            "base-build",
            timeout_seconds=timeout_seconds,
        )
        self.mutation = CanonicalMutationLease(ws, timeout_seconds=timeout_seconds)
        self._active = False

    @property
    def active(self) -> bool:
        return self._active and self._base.active and self.mutation.active

    def assert_active(self, ws: WorkspacePaths) -> None:
        if not self.active:
            raise LockOwnershipError("index build lease is not active")
        if os.getpid() != self._base.pid or threading.get_ident() != self._base.thread_id:
            raise LockOwnershipError("index build lease has a foreign owner")
        if self.ws.root.resolve() != ws.root.resolve():
            raise LockOwnershipError("index build lease belongs to another workspace")

    def __enter__(self) -> IndexBuildLease:
        self._base.__enter__()
        try:
            self.mutation.__enter__()
        except Exception:
            self._base.release()
            raise
        self._active = True
        return self

    def release(self) -> None:
        self.assert_active(self.ws)
        self._active = False
        try:
            self.mutation.release()
        finally:
            self._base.release()

    def __exit__(self, exc_type, exc, traceback) -> bool:
        self.release()
        return False


def acquire_canonical_mutation_lease(
    ws: WorkspacePaths,
    *,
    timeout_seconds: float = 2.0,
) -> CanonicalMutationLease:
    return CanonicalMutationLease(ws, timeout_seconds=timeout_seconds)


def acquire_index_build_lease(
    ws: WorkspacePaths,
    *,
    reason: str,
    timeout_seconds: float = 10.0,
) -> IndexBuildLease:
    return IndexBuildLease(
        ws,
        reason=reason,
        timeout_seconds=timeout_seconds,
    )


def active_canonical_mutation_lease(
    ws: WorkspacePaths,
) -> CanonicalMutationLease | None:
    root = ws.root.resolve()
    for lease in reversed(_mutation_stack()):
        if lease.active and lease.ws.root.resolve() == root:
            return lease
    return None


def held_ranked_lock_names() -> tuple[str, ...]:
    """Expose current-thread ranks for contracts and deterministic tests."""

    return tuple(lease.name for lease in _held_stack())


def _lock_path(ws: WorkspacePaths, name: str) -> Path:
    return ws.root / "runtime" / "locks" / "query-index" / f"{name}.lock"


def _validated_lock_path(ws: WorkspacePaths, path: Path) -> Path:
    lock_root = (ws.root / "runtime" / "locks").resolve()
    candidate = path.resolve()
    try:
        candidate.relative_to(lock_root)
    except ValueError as exc:
        raise ValueError(f"ranked lock path escaped runtime locks: {candidate}") from exc
    return candidate


def _process_lock_for(path: Path) -> threading.Lock:
    key = str(path.resolve()).casefold() if os.name == "nt" else str(path.resolve())
    with _registry_guard:
        return _process_locks.setdefault(key, threading.Lock())


def _held_stack() -> list[RankedLockLease]:
    stack = getattr(_thread_state, "ranked_locks", None)
    if stack is None:
        stack = []
        _thread_state.ranked_locks = stack
    return stack


def _mutation_stack() -> list[CanonicalMutationLease]:
    stack = getattr(_thread_state, "mutation_leases", None)
    if stack is None:
        stack = []
        _thread_state.mutation_leases = stack
    return stack


def _ensure_lock_byte(descriptor: int) -> None:
    if os.fstat(descriptor).st_size >= 1:
        return
    os.lseek(descriptor, 0, os.SEEK_SET)
    os.write(descriptor, b"\0")
    os.fsync(descriptor)


def _acquire_os_lock(descriptor: int, timeout_seconds: float, name: str) -> None:
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            _try_os_lock(descriptor)
            return
        except OSError as exc:
            if exc.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK, 13, 36}:
                raise
            if time.monotonic() >= deadline:
                raise LockTimeoutError(f"timed out acquiring OS lock: {name}") from exc
            time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))


def _try_os_lock(descriptor: int) -> None:
    os.lseek(descriptor, 0, os.SEEK_SET)
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        return
    import fcntl

    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _release_os_lock(descriptor: int) -> None:
    os.lseek(descriptor, 0, os.SEEK_SET)
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(descriptor, fcntl.LOCK_UN)
