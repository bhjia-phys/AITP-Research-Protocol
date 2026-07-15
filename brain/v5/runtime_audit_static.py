"""Focused AST helpers for runtime capability audit declarations."""

from __future__ import annotations

import ast
from pathlib import Path


def layout_families(path: Path, *, registry_path: Path | None = None) -> list[str]:
    """Read family declarations without importing runtime registry modules."""

    if not path.exists():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(
            isinstance(target, ast.Name) and target.id == "_LAYOUT_DIRS"
            for target in targets
        ):
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            break
        return sorted(
            item.removeprefix("registry/")
            for item in value
            if isinstance(item, str) and item.startswith("registry/")
        )
    if registry_path is None:
        return []
    rows = [
        *literal_tuple_rows(registry_path, "_REGISTRY_ROWS", arity=4),
        *literal_tuple_rows(
            registry_path.with_name("record_family_m3.py"),
            "M3_REGISTRY_ROWS",
            arity=4,
        ),
    ]
    return sorted(row[0] for row in rows)


def literal_tuple_rows(
    path: Path,
    assignment: str,
    *,
    arity: int,
) -> tuple[tuple[object, ...], ...]:
    """Return fixed-width literal tuple rows nested in one named assignment."""

    if not path.exists():
        return ()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(
            isinstance(target, ast.Name) and target.id == assignment
            for target in targets
        ):
            continue
        rows: list[tuple[object, ...]] = []
        for candidate in ast.walk(node.value):
            if not isinstance(candidate, ast.Tuple) or len(candidate.elts) != arity:
                continue
            try:
                row = ast.literal_eval(candidate)
            except (ValueError, TypeError):
                continue
            if (
                isinstance(row, tuple)
                and len(row) == arity
                and isinstance(row[0], str)
            ):
                rows.append(row)
        return tuple(rows)
    return ()
