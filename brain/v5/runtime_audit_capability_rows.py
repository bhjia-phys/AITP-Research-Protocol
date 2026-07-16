"""Static expansion of focused capability-row providers."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def execution_capability_rows(directory: Path) -> list[tuple[Any, ...]]:
    path = directory / "execution_surface_contracts.py"
    rows = []
    for mapping_name, state_effect in (("_READ", "read_only"), ("_GATED", "kernel_write")):
        for operation in _mapping_keys(path, mapping_name):
            rows.append(
                (
                    operation,
                    f"aitp_v5_{operation}",
                    f"aitp-v5 execution {operation} --payload-file <args>",
                    "execution_operation_result",
                    state_effect,
                    "full",
                )
            )
    return rows


def knowledge_capability_rows(directory: Path) -> list[tuple[Any, ...]]:
    return _facade_rows(
        directory / "knowledge_surface_contracts.py",
        command="knowledge",
        surface="knowledge_operation_result",
    )


def skill_capability_rows(directory: Path) -> list[tuple[Any, ...]]:
    return _facade_rows(
        directory / "skill_surface_contracts.py",
        command="skill",
        surface="skill_operation_result",
    )


def _facade_rows(
    path: Path,
    *,
    command: str,
    surface: str,
) -> list[tuple[Any, ...]]:
    operations = _literal_assignment(path, "_OPERATIONS", default={})
    if not isinstance(operations, dict):
        return []
    rows = []
    for operation, value in operations.items():
        if not isinstance(operation, str) or not isinstance(value, tuple) or not value:
            continue
        state_effect = value[0]
        if not isinstance(state_effect, str):
            continue
        rows.append(
            (
                operation,
                f"aitp_v5_{operation}",
                f"aitp-v5 {command} {operation} --payload-file <args>",
                surface,
                state_effect,
                "full",
            )
        )
    return rows


def _mapping_keys(path: Path, name: str) -> list[str]:
    value = _assignment_node(path, name)
    if not isinstance(value, ast.Dict):
        return []
    keys = []
    for key in value.keys:
        try:
            item = ast.literal_eval(key)
        except (ValueError, TypeError):
            continue
        if isinstance(item, str):
            keys.append(item)
    return keys


def _literal_assignment(path: Path, name: str, *, default: Any) -> Any:
    value = _assignment_node(path, name)
    if value is None:
        return default
    try:
        return ast.literal_eval(value)
    except (ValueError, TypeError):
        return default


def _assignment_node(path: Path, name: str) -> ast.expr | None:
    if not path.exists():
        return None
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign):
            targets, value = [node.target], node.value
        else:
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            return value
    return None


__all__ = [
    "execution_capability_rows",
    "knowledge_capability_rows",
    "skill_capability_rows",
]
