"""Split the two oversized v5 CLI functions into bounded named sections."""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path


TARGET_SECTION_LINES = 300
MAX_SECTION_LINES = 430


def _segment(source: str, node: ast.AST) -> str:
    value = ast.get_source_segment(source, node)
    if not value:
        raise RuntimeError(f"cannot extract {type(node).__name__}")
    return textwrap.dedent(value).rstrip()


def _assigned_names(node: ast.AST) -> set[str]:
    return {
        item.id
        for item in ast.walk(node)
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store)
    }


def _loaded_names(node: ast.AST) -> set[str]:
    return {
        item.id
        for item in ast.walk(node)
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
    }


def _safe_parser_boundary(
    group: list[ast.stmt],
    remaining: list[ast.stmt],
    local_names: set[str],
) -> bool:
    pending = set().union(*(_assigned_names(statement) for statement in group)) - {
        "parser",
        "sp",
    }
    for statement in remaining:
        loads = _loaded_names(statement) & local_names
        if pending.intersection(loads):
            return False
        pending.difference_update(_assigned_names(statement))
        if not pending:
            return True
    return True


def _parser_groups(source: str, statements: list[ast.stmt]) -> list[list[ast.stmt]]:
    local_names = set().union(*(_assigned_names(statement) for statement in statements))
    groups: list[list[ast.stmt]] = []
    current: list[ast.stmt] = []
    current_lines = 5
    for index, statement in enumerate(statements):
        size = len(_segment(source, statement).splitlines()) + 1
        current.append(statement)
        current_lines += size
        remaining = statements[index + 1 :]
        if (
            current_lines >= TARGET_SECTION_LINES
            and _safe_parser_boundary(current, remaining, local_names)
        ):
            groups.append(current)
            current = []
            current_lines = 5
        elif current_lines > MAX_SECTION_LINES:
            raise RuntimeError("could not find a safe parser section boundary")
    if current:
        groups.append(current)
    return groups


def _line_groups(source: str, statements: list[ast.stmt]) -> list[list[ast.stmt]]:
    groups: list[list[ast.stmt]] = []
    current: list[ast.stmt] = []
    lines = 6
    for statement in statements:
        size = len(_segment(source, statement).splitlines()) + 1
        if current and lines + size > TARGET_SECTION_LINES:
            groups.append(current)
            current = []
            lines = 6
        current.append(statement)
        lines += size
    if current:
        groups.append(current)
    return groups


def _function(name: str, signature: str, statements: list[ast.stmt], source: str) -> str:
    body = "\n".join(textwrap.indent(_segment(source, item), "    ") for item in statements)
    return f"def {name}({signature}):\n{body}\n"


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    target = repo / "brain" / "v5" / "cli.py"
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source)
    parser_fn = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_build_parser"
    )
    dispatch_fn = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_dispatch"
    )

    parser_setup = parser_fn.body[:3]
    parser_statements = parser_fn.body[3:-1]
    parser_sections = _parser_groups(source, parser_statements)
    parser_helpers = [
        _function(f"_add_parser_section_{index:02d}", "sp", group, source)
        for index, group in enumerate(parser_sections, start=1)
    ]
    parser_wrapper = (
        "def _build_parser() -> argparse.ArgumentParser:\n"
        + "\n".join(textwrap.indent(_segment(source, item), "    ") for item in parser_setup)
        + "\n"
        + "\n".join(
            f"    _add_parser_section_{index:02d}(sp)"
            for index in range(1, len(parser_sections) + 1)
        )
        + "\n    return parser\n\n\n"
        + "\n\n".join(parser_helpers)
    )

    workspace_index = next(
        index
        for index, statement in enumerate(dispatch_fn.body)
        if isinstance(statement, ast.Assign)
        and any(isinstance(target_node, ast.Name) and target_node.id == "ws" for target_node in statement.targets)
    )
    pre_statements = dispatch_fn.body[:workspace_index]
    workspace_statement = dispatch_fn.body[workspace_index]
    post_statements = dispatch_fn.body[workspace_index + 1 : -1]
    pre_groups = _line_groups(source, pre_statements)
    post_groups = _line_groups(source, post_statements)
    pre_helpers = [
        _function(f"_dispatch_pre_workspace_{index:02d}", "args", group, source)
        + "    return _CLI_UNHANDLED\n"
        for index, group in enumerate(pre_groups, start=1)
    ]
    post_helpers = [
        _function(f"_dispatch_workspace_{index:02d}", "args, ws", group, source)
        + "    return _CLI_UNHANDLED\n"
        for index, group in enumerate(post_groups, start=1)
    ]
    dispatch_wrapper = (
        "_CLI_UNHANDLED = object()\n\n\n"
        "def _dispatch(args: argparse.Namespace) -> dict[str, Any]:\n"
        + "\n".join(
            f"    result = _dispatch_pre_workspace_{index:02d}(args)\n"
            "    if result is not _CLI_UNHANDLED:\n"
            "        return result"
            for index in range(1, len(pre_groups) + 1)
        )
        + "\n    "
        + _segment(source, workspace_statement)
        + "\n"
        + "\n".join(
            f"    result = _dispatch_workspace_{index:02d}(args, ws)\n"
            "    if result is not _CLI_UNHANDLED:\n"
            "        return result"
            for index in range(1, len(post_groups) + 1)
        )
        + '\n    raise SystemExit(f"unsupported command: {args.command}")\n\n\n'
        + "\n\n".join(pre_helpers + post_helpers)
    )

    lines = source.splitlines()
    replacements = [
        (dispatch_fn.lineno - 1, dispatch_fn.end_lineno, dispatch_wrapper.splitlines()),
        (parser_fn.lineno - 1, parser_fn.end_lineno, parser_wrapper.splitlines()),
    ]
    for start, end, replacement in sorted(replacements, reverse=True):
        lines[start:end] = replacement
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"parser_sections={len(parser_sections)} pre_dispatch={len(pre_groups)} "
        f"workspace_dispatch={len(post_groups)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
