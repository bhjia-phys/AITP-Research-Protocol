"""Load fixed, bounded source shards into a compatibility module namespace."""

from __future__ import annotations

from pathlib import Path
from typing import MutableMapping


def load_module_shards(
    namespace: MutableMapping[str, object],
    module_file: str,
    shard_paths: tuple[str, ...],
) -> None:
    """Execute repository-owned source shards as one compatibility module."""

    module_root = Path(module_file).resolve().parent
    for relative in shard_paths:
        shard = (module_root / relative).resolve()
        if module_root not in shard.parents or shard.suffix != ".py":
            raise RuntimeError(f"invalid compatibility shard path: {relative!r}")
        source = shard.read_text(encoding="utf-8")
        exec(compile(source, str(shard), "exec"), namespace, namespace)
