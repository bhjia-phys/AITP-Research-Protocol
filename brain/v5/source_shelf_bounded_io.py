"""Bounded byte reads for source-shelf inputs."""

from __future__ import annotations

from pathlib import Path


def read_bounded_bytes(
    path: Path,
    max_bytes: int,
    *,
    chunk_size: int = 1024 * 1024,
) -> bytes | None:
    """Return bytes within the limit, or None after reading at most limit + 1."""

    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 0:
        raise ValueError("max_bytes must be a non-negative integer")
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    data = bytearray()
    with path.open("rb") as handle:
        while len(data) <= max_bytes:
            remaining = max_bytes + 1 - len(data)
            chunk = handle.read(min(chunk_size, remaining))
            if not chunk:
                return bytes(data)
            data.extend(chunk)
    return None


__all__ = ["read_bounded_bytes"]
