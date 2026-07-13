"""Read-only AST inventory of direct production filesystem mutations."""

from __future__ import annotations

import ast
import re
import warnings
from pathlib import Path
from typing import Any, Iterable


DIRECT_MUTATION_MECHANISMS = (
    "direct_path_write",
    "direct_open_write",
    "copy_or_move",
    "rename_or_replace",
    "sqlite_mutation",
)
WRITER_SOURCE_SCOPES = (
    "v5",
    "legacy_brain",
    "host_hooks",
    "scripts",
    "reference_runtime",
    "plugins",
    "other",
)
WRITER_SCAN_SOURCE_PREFIXES = (
    "brain/",
    "hooks/",
    "deploy/hooks/",
    "scripts/",
    "reference-runtime/",
    "plugins/",
)
WRITER_SCAN_EXCLUDED_PREFIXES = ("tests/",)
_WRITER_HELPER_CALLS = {
    "write_record",
    "write_md",
    "write_text_atomic",
    "write_json_atomic",
}
_SQL_MUTATION_RE = re.compile(
    r"(?:^|;)\s*(INSERT|UPDATE|DELETE|REPLACE|CREATE|DROP|ALTER|VACUUM|ATTACH|DETACH|REINDEX)\b",
    re.IGNORECASE | re.MULTILINE,
)


def direct_mutation_rows(
    root: Path,
    source_paths: Iterable[Path],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in source_paths:
        relative = _normalize_relative_path(path.relative_to(root).as_posix())
        if not relative.startswith(WRITER_SCAN_SOURCE_PREFIXES):
            continue
        if relative.startswith(WRITER_SCAN_EXCLUDED_PREFIXES):
            continue
        try:
            tree = _parse_python(path)
        except (SyntaxError, UnicodeDecodeError):
            continue
        visitor = _DirectMutationVisitor(relative)
        visitor.visit(tree)
        rows.extend(visitor.rows)
    return sorted(
        rows,
        key=lambda row: (
            row["path"],
            row["line"],
            row["mechanism"],
            row["call"],
        ),
    )


def helper_writer_rows(
    root: Path,
    source_paths: Iterable[Path],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in source_paths:
        relative = _normalize_relative_path(path.relative_to(root).as_posix())
        if not relative.startswith(("brain/", "hooks/", "deploy/hooks/")):
            continue
        try:
            tree = _parse_python(path)
        except (SyntaxError, UnicodeDecodeError):
            continue
        visitor = _WriterHelperVisitor(relative)
        visitor.visit(tree)
        rows.extend(visitor.rows)
    return sorted(rows, key=lambda row: (row["path"], row["line"], row["call"]))


def writer_scan_policy(source_rows: Iterable[dict[str, Any]] = ()) -> dict[str, Any]:
    scanned_rows = [
        row
        for row in source_rows
        if isinstance(row, dict)
        and _path_is_in_scan_scope(str(row.get("path") or ""))
    ]
    parse_error_paths = sorted(
        str(row.get("path") or "")
        for row in scanned_rows
        if str(row.get("parse_error") or "")
    )
    scanned_count = len(scanned_rows)
    parsed_count = scanned_count - len(parse_error_paths)
    known_gaps = [
        "dynamic or aliased filesystem APIs",
        "non-literal SQL and database APIs outside execute/executemany/executescript",
        "filesystem mutation hidden behind unrecognized helpers or native extensions",
    ]
    return {
        "included_source_prefixes": list(WRITER_SCAN_SOURCE_PREFIXES),
        "excluded_source_prefixes": list(WRITER_SCAN_EXCLUDED_PREFIXES),
        "recognized_mechanisms": list(DIRECT_MUTATION_MECHANISMS),
        "known_gaps": known_gaps,
        "excluded_mechanisms": list(known_gaps),
        "closure_scope": "declared_python_source_prefixes",
        "scanned_source_file_count": scanned_count,
        "parsed_source_file_count": parsed_count,
        "parse_error_count": len(parse_error_paths),
        "parse_error_paths": parse_error_paths,
        "bounded_coverage_complete": scanned_count > 0 and not parse_error_paths,
        "coverage_complete": False,
    }


def _path_is_in_scan_scope(relative_path: str) -> bool:
    relative = _normalize_relative_path(relative_path)
    return relative.startswith(WRITER_SCAN_SOURCE_PREFIXES) and not relative.startswith(
        WRITER_SCAN_EXCLUDED_PREFIXES
    )


class _DirectMutationVisitor(ast.NodeVisitor):
    def __init__(self, relative_path: str):
        self.relative_path = relative_path
        self.function_stack: list[str] = []
        self.rows: list[dict[str, Any]] = []
        self.call_counts: dict[tuple[str, str], int] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        mutation = _direct_mutation_call(node)
        if mutation is not None:
            mechanism, call_name, mode, target_expression, detail = mutation
            function = self.function_stack[-1] if self.function_stack else "<module>"
            ordinal = self._next_ordinal(function, call_name)
            self.rows.append(
                {
                    "path": self.relative_path,
                    "function": function,
                    "line": int(getattr(node, "lineno", 0)),
                    "call": call_name,
                    "ordinal": ordinal,
                    "stable_signature": _stable_writer_signature(
                        self.relative_path, function, call_name, ordinal
                    ),
                    "mechanism": mechanism,
                    "mode": mode,
                    "target_expression": target_expression,
                    "detail": detail,
                    "source_scope": _writer_source_scope(self.relative_path),
                }
            )
        self.generic_visit(node)

    def _next_ordinal(self, function: str, call_name: str) -> int:
        key = (function, call_name)
        self.call_counts[key] = self.call_counts.get(key, 0) + 1
        return self.call_counts[key]


class _WriterHelperVisitor(ast.NodeVisitor):
    def __init__(self, relative_path: str):
        self.relative_path = relative_path
        self.function_stack: list[str] = []
        self.rows: list[dict[str, Any]] = []
        self.call_counts: dict[tuple[str, str], int] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        call_name = _call_name(node.func)
        repository_family = _repository_write_family(node)
        if repository_family is not None:
            families, dynamic = repository_family
            function = self.function_stack[-1] if self.function_stack else "<module>"
            ordinal = self._next_ordinal(function, "repository_write")
            self.rows.append(
                {
                    "path": self.relative_path,
                    "function": function,
                    "line": int(getattr(node, "lineno", 0)),
                    "call": "repository_write",
                    "ordinal": ordinal,
                    "stable_signature": _stable_writer_signature(
                        self.relative_path, function, "repository_write", ordinal
                    ),
                    "registry_families": families,
                    "dynamic_registry_family": dynamic,
                }
            )
        elif call_name in _WRITER_HELPER_CALLS:
            families, dynamic = _registry_families_in_node(node)
            function = self.function_stack[-1] if self.function_stack else "<module>"
            ordinal = self._next_ordinal(function, call_name)
            self.rows.append(
                {
                    "path": self.relative_path,
                    "function": function,
                    "line": int(getattr(node, "lineno", 0)),
                    "call": call_name,
                    "ordinal": ordinal,
                    "stable_signature": _stable_writer_signature(
                        self.relative_path, function, call_name, ordinal
                    ),
                    "registry_families": families,
                    "dynamic_registry_family": dynamic,
                }
            )
        self.generic_visit(node)

    def _next_ordinal(self, function: str, call_name: str) -> int:
        key = (function, call_name)
        self.call_counts[key] = self.call_counts.get(key, 0) + 1
        return self.call_counts[key]


def _stable_writer_signature(
    path: str,
    function: str,
    call_name: str,
    ordinal: int,
) -> str:
    return f"{path}:{function}:{call_name}:{ordinal}"


def _repository_write_family(node: ast.Call) -> tuple[list[str], bool] | None:
    if not isinstance(node.func, ast.Attribute) or node.func.attr != "write":
        return None
    owner = node.func.value
    recognized = isinstance(owner, ast.Name) and owner.id in {"repo", "repository"}
    if isinstance(owner, ast.Call):
        recognized = _call_name(owner.func) in {"RecordRepository", "_repository"}
    if not recognized:
        return None
    if not node.args:
        return [], True
    family = node.args[0]
    if isinstance(family, ast.Constant) and isinstance(family.value, str) and family.value.strip():
        return [family.value.strip()], False
    return [], True


def _direct_mutation_call(
    node: ast.Call,
) -> tuple[str, str, str, str, str] | None:
    call_name = _call_name(node.func)
    if call_name in {"write_text", "write_bytes"} and isinstance(node.func, ast.Attribute):
        return (
            "direct_path_write",
            call_name,
            "",
            _expression_text(node.func.value),
            "",
        )

    owner = _call_owner_name(node.func)
    if owner == "os" and call_name == "fdopen":
        mode = _literal_mode_argument(node, positional_index=1)
        if mode and any(flag in mode for flag in "wax+"):
            return (
                "direct_open_write",
                "fdopen",
                mode,
                _argument_text(node, 0),
                "os.fdopen",
            )

    if call_name == "NamedTemporaryFile" and owner in {"", "tempfile"}:
        mode = _literal_mode_argument(
            node,
            positional_index=0,
            default="w+b",
        )
        if any(flag in mode for flag in "wax+"):
            return (
                "direct_open_write",
                "NamedTemporaryFile",
                mode,
                _keyword_argument_text(node, "dir"),
                "tempfile.NamedTemporaryFile",
            )

    if call_name == "open":
        if owner == "os":
            flags = _os_open_write_flags(node)
            if not flags:
                return None
            return (
                "direct_open_write",
                "open",
                flags,
                _argument_text(node, 0),
                "os.open",
            )
        mode = _literal_open_mode(node)
        if not mode or not any(flag in mode for flag in "wax+"):
            return None
        target = (
            _expression_text(node.func.value)
            if isinstance(node.func, ast.Attribute)
            else _argument_text(node, 0)
        )
        return ("direct_open_write", "open", mode, target, "")

    if owner == "shutil" and call_name in {"copy", "copy2", "copyfile", "copytree", "move"}:
        return (
            "copy_or_move",
            call_name,
            "",
            _argument_text(node, 1),
            f"shutil.{call_name}",
        )

    if owner == "os" and call_name in {"replace", "rename", "renames"}:
        return (
            "rename_or_replace",
            call_name,
            "",
            _argument_text(node, 1),
            f"os.{call_name}",
        )

    if call_name in {"execute", "executemany", "executescript"}:
        sql = _literal_string_argument(node, 0)
        match = _SQL_MUTATION_RE.search(sql) if sql else None
        if match is not None:
            return (
                "sqlite_mutation",
                call_name,
                "",
                _expression_text(node.func.value) if isinstance(node.func, ast.Attribute) else "",
                match.group(1).upper(),
            )
    return None


def _call_name(value: ast.expr) -> str:
    if isinstance(value, ast.Name):
        return value.id
    if isinstance(value, ast.Attribute):
        return value.attr
    return ""


def _registry_families_in_node(node: ast.AST) -> tuple[list[str], bool]:
    families: set[str] = set()
    dynamic = False
    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.Call) or not isinstance(candidate.func, ast.Attribute):
            continue
        if candidate.func.attr != "registry_dir" or not candidate.args:
            continue
        first = candidate.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str) and first.value.strip():
            families.add(first.value.strip())
        else:
            dynamic = True
    return sorted(families), dynamic


def _call_owner_name(value: ast.expr) -> str:
    if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
        return value.value.id
    return ""


def _literal_open_mode(node: ast.Call) -> str:
    positional_index = 0 if isinstance(node.func, ast.Attribute) else 1
    return _literal_mode_argument(node, positional_index=positional_index)


def _literal_mode_argument(
    node: ast.Call,
    *,
    positional_index: int,
    default: str = "",
) -> str:
    candidate: ast.expr | None = (
        node.args[positional_index] if len(node.args) > positional_index else None
    )
    for keyword in node.keywords:
        if keyword.arg == "mode":
            candidate = keyword.value
    if isinstance(candidate, ast.Constant) and isinstance(candidate.value, str):
        return candidate.value
    return default if candidate is None else ""


def _os_open_write_flags(node: ast.Call) -> str:
    candidate = node.args[1] if len(node.args) > 1 else None
    for keyword in node.keywords:
        if keyword.arg == "flags":
            candidate = keyword.value
    if candidate is None:
        return ""
    write_flags = {"O_WRONLY", "O_RDWR", "O_CREAT", "O_TRUNC", "O_APPEND"}
    names = {
        item.id
        for item in ast.walk(candidate)
        if isinstance(item, ast.Name) and item.id in write_flags
    }
    attributes = {
        item.attr
        for item in ast.walk(candidate)
        if isinstance(item, ast.Attribute) and item.attr in write_flags
    }
    return "|".join(sorted(names | attributes))


def _literal_string_argument(node: ast.Call, index: int) -> str:
    if len(node.args) <= index:
        return ""
    value = node.args[index]
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    return ""


def _argument_text(node: ast.Call, index: int) -> str:
    if len(node.args) <= index:
        return ""
    return _expression_text(node.args[index])


def _keyword_argument_text(node: ast.Call, name: str) -> str:
    for keyword in node.keywords:
        if keyword.arg == name:
            return _expression_text(keyword.value)
    return ""


def _expression_text(value: ast.AST) -> str:
    try:
        return ast.unparse(value)
    except (AttributeError, ValueError):
        return ""


def _writer_source_scope(relative_path: str) -> str:
    if relative_path.startswith("brain/v5/"):
        return "v5"
    if relative_path.startswith("brain/"):
        return "legacy_brain"
    if relative_path.startswith(("hooks/", "deploy/hooks/")):
        return "host_hooks"
    if relative_path.startswith("scripts/"):
        return "scripts"
    if relative_path.startswith("reference-runtime/"):
        return "reference_runtime"
    if relative_path.startswith("plugins/"):
        return "plugins"
    return "other"


def _normalize_relative_path(value: str) -> str:
    return value.replace("\\", "/").removeprefix("./")


def _parse_python(path: Path) -> ast.Module:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
