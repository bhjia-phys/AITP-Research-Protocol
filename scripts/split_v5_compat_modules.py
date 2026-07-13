"""Mechanically split oversized v5 modules at Python top-level boundaries."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


MAX_SHARD_LINES = 480


def split_module(repo_root: Path, relative_module: str) -> tuple[Path, ...]:
    module_path = repo_root / relative_module
    source = module_path.read_text(encoding="utf-8")
    lines = source.splitlines()
    tree = ast.parse(source)
    docstring = ast.get_docstring(tree, clean=False) or f"Compatibility facade for {module_path.name}."
    units: list[str] = []
    for index, node in enumerate(tree.body):
        if index == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        starts = [node.lineno]
        starts.extend(decorator.lineno for decorator in getattr(node, "decorator_list", ()))
        start = min(starts) - 1
        end = getattr(node, "end_lineno", node.lineno)
        units.append("\n".join(lines[start:end]).rstrip() + "\n")

    groups: list[list[str]] = []
    current: list[str] = []
    current_lines = 3
    for unit in units:
        unit_lines = len(unit.splitlines()) + 1
        if unit_lines + 3 > MAX_SHARD_LINES:
            raise RuntimeError(
                f"{relative_module}: top-level unit exceeds shard limit ({unit_lines} lines)"
            )
        if current and current_lines + unit_lines > MAX_SHARD_LINES:
            groups.append(current)
            current = []
            current_lines = 3
        current.append(unit)
        current_lines += unit_lines
    if current:
        groups.append(current)

    shard_dir = module_path.parent / "_compat_shards" / module_path.stem
    shard_dir.mkdir(parents=True, exist_ok=True)
    existing = list(shard_dir.glob("part_*.py"))
    if existing:
        raise RuntimeError(f"refusing to overwrite existing shards: {shard_dir}")
    shard_paths: list[Path] = []
    for index, group in enumerate(groups, start=1):
        shard_path = shard_dir / f"part_{index:02d}.py"
        shard_path.write_text(
            f"# Compatibility shard {index} for {module_path.stem}.\n"
            "from __future__ import annotations\n\n"
            + "\n".join(group),
            encoding="utf-8",
        )
        shard_paths.append(shard_path)

    relative_shards = [path.relative_to(module_path.parent).as_posix() for path in shard_paths]
    manifest = "\n".join(f'    "{path}",' for path in relative_shards)
    facade = (
        f'{docstring!r}\n\n'
        "from __future__ import annotations\n\n"
        "from brain.v5.compat_module_loader import load_module_shards as _load_module_shards\n\n"
        "_load_module_shards(\n"
        "    globals(),\n"
        "    __file__,\n"
        "    (\n"
        f"{manifest}\n"
        "    ),\n"
        ")\n"
        "del _load_module_shards\n"
    )
    module_path.write_text(facade, encoding="utf-8")
    return tuple(shard_paths)


def main(argv: list[str]) -> int:
    if not argv:
        raise SystemExit("usage: split_v5_compat_modules.py <brain/v5/module.py> ...")
    repo_root = Path(__file__).resolve().parents[1]
    for relative in argv:
        shards = split_module(repo_root, relative)
        print(f"{relative}: {len(shards)} shards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
