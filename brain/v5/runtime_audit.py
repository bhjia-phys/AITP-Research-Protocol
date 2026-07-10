"""Read-only audit of AITP v5 runtime files and record-family usage."""

from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


_CLASSIFICATIONS = (
    "directly_touched_by_plan",
    "covered_by_integration_choke_point",
    "adjacent_but_no_change_expected",
    "requires_task_update",
    "deferred_legacy_or_domain_surface",
)
_CHOKE_POINTS = {
    "brain/v5/mcp_tools.py",
    "brain/v5/public_surfaces.py",
    "brain/v5/runtime_entrypoint_catalog.py",
    "brain/v5/runtime_bridge_targets.py",
    "brain/v5/codex_facade.py",
    "brain/v5/workspace_refresh.py",
}
_PLAN_PATH_RE = re.compile(r"^- (?:Create|Modify|Test): `([^`]+)`", re.MULTILINE)
_WRITER_CALLS = {"write_record", "write_md", "write_text_atomic", "write_json_atomic"}


def build_runtime_capability_audit(
    repo_root: str | Path,
    *,
    workspace_base: str | Path | None = None,
    plan_path: str | Path | None = None,
) -> dict[str, Any]:
    """Return a trust-neutral inventory of runtime files and registry drift."""

    root = Path(repo_root).resolve()
    planned = _planned_paths(Path(plan_path)) if plan_path else set()
    files = _source_rows(root, planned)
    layout = _layout_families(root / "brain" / "v5" / "paths.py")
    used, users = _literal_registry_families(root / "brain" / "v5")
    actual_counts = _actual_registry_counts(Path(workspace_base)) if workspace_base else {}
    actual = sorted(actual_counts)
    capabilities = _capability_inventory(root / "brain" / "v5")
    writers = _writer_rows(root)
    counts = Counter(row["classification"] for row in files)
    return {
        "kind": "runtime_capability_audit",
        "repo_root": str(root),
        "workspace_base": str(Path(workspace_base).resolve()) if workspace_base else "",
        "inventory": {
            "file_count": len(files),
            "writer_count": len(writers),
            "actual_registry_record_count": sum(actual_counts.values()),
            "classification_counts": dict(sorted(counts.items())),
        },
        "files": files,
        "capabilities": capabilities,
        "writers": writers,
        "record_families": {
            "layout": layout,
            "literal_uses": used,
            "actual_workspace": actual,
            "actual_workspace_counts": actual_counts,
            "used_not_layout": sorted(set(used) - set(layout)),
            "actual_not_layout": sorted(set(actual) - set(layout)),
            "layout_not_used": sorted(set(layout) - set(used)),
            "literal_users": users,
        },
        "truth_source": "static_source_and_filesystem_inventory",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def render_runtime_capability_audit_markdown(payload: dict[str, Any]) -> str:
    """Render an audit payload through the focused Markdown renderer."""

    from brain.v5.runtime_audit_rendering import render_runtime_capability_audit_markdown as _render

    return _render(payload)


def _planned_paths(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return {_normalize_relative_path(match) for match in _PLAN_PATH_RE.findall(text)}


def _source_rows(root: Path, planned: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in _source_paths(root):
        relative = _normalize_relative_path(path.relative_to(root).as_posix())
        parse_error = ""
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            parse_error = str(exc)
        rows.append(
            {
                "path": relative,
                "classification": _classify_path(relative, planned, parse_error=parse_error),
                "parse_error": parse_error,
            }
        )
    return rows


def _source_paths(root: Path) -> list[Path]:
    patterns = (
        "brain/**/*.py",
        "hooks/**/*.py",
        "deploy/hooks/**/*.py",
        "scripts/**/*.py",
        "reference-runtime/**/*.py",
        "plugins/**/*.py",
        "tests/test*.py",
    )
    return sorted({path for pattern in patterns for path in root.glob(pattern) if path.is_file()})


def _classify_path(relative: str, planned: set[str], *, parse_error: str) -> str:
    if parse_error:
        return "requires_task_update"
    if relative in planned:
        return "directly_touched_by_plan"
    if relative in _CHOKE_POINTS:
        return "covered_by_integration_choke_point"
    if _is_legacy_or_domain_surface(relative):
        return "deferred_legacy_or_domain_surface"
    return "adjacent_but_no_change_expected"


def _is_legacy_or_domain_surface(relative: str) -> bool:
    name = Path(relative).name.lower()
    return name.startswith("legacy_") or "/domain_" in f"/{relative.lower()}"


def _layout_families(path: Path) -> list[str]:
    if not path.exists():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == "_LAYOUT_DIRS" for target in targets):
            continue
        value = ast.literal_eval(node.value)
        return sorted(
            item.removeprefix("registry/")
            for item in value
            if isinstance(item, str) and item.startswith("registry/")
        )
    return []


def _literal_registry_families(directory: Path) -> tuple[list[str], dict[str, list[str]]]:
    users: dict[str, list[str]] = {}
    if not directory.exists():
        return [], users
    for path in sorted(directory.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for family in _registry_dir_literals(tree):
            users.setdefault(family, []).append(path.name)
    normalized_users = {family: sorted(set(paths)) for family, paths in sorted(users.items())}
    return sorted(normalized_users), normalized_users


def _registry_dir_literals(tree: ast.AST) -> Iterable[str]:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "registry_dir" or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str) and first.value.strip():
            yield first.value.strip()


def _actual_registry_counts(workspace_base: Path) -> dict[str, int]:
    registry = workspace_base.resolve() / ".aitp" / "registry"
    if not registry.exists():
        return {}
    return {
        path.name: len(list(path.glob("*.md")))
        for path in sorted(registry.iterdir(), key=lambda item: item.name)
        if path.is_dir()
    }


def _capability_inventory(directory: Path) -> dict[str, list[str]]:
    catalog = _literal_named_assignment(
        directory / "runtime_entrypoint_catalog.py",
        "RUNTIME_ENTRYPOINTS",
        default={},
    )
    if not isinstance(catalog, dict):
        catalog = {}
    catalog_mcp = sorted(
        {
            str(item.get("mcp"))
            for item in catalog.values()
            if isinstance(item, dict) and isinstance(item.get("mcp"), str) and item.get("mcp")
        }
    )
    catalog_surfaces = sorted(
        {
            str(item.get("surface"))
            for item in catalog.values()
            if isinstance(item, dict)
            and isinstance(item.get("surface"), str)
            and item.get("surface")
        }
    )
    public_surfaces = _string_sequence_assignment(
        directory / "public_surfaces.py", "_PUBLIC_SURFACE_NAMES"
    )
    facade_tools = _string_sequence_assignment(directory / "codex_facade.py", "CODEX_FACADE_TOOLS")
    support_tools = _string_sequence_assignment(directory / "codex_facade.py", "CODEX_SUPPORT_TOOLS")
    compact_allowlist = sorted(set(facade_tools) | set(support_tools))
    mcp_wrappers = _function_names(directory / "mcp_tools.py", prefix="aitp_v5_")
    return {
        "catalog_operations": sorted(str(key) for key in catalog),
        "catalog_mcp": catalog_mcp,
        "catalog_surfaces": catalog_surfaces,
        "public_surfaces": public_surfaces,
        "mcp_wrappers": mcp_wrappers,
        "compact_allowlist": compact_allowlist,
        "catalog_mcp_not_wrapped": sorted(set(catalog_mcp) - set(mcp_wrappers)),
        "wrapped_not_catalog": sorted(set(mcp_wrappers) - set(catalog_mcp)),
        "catalog_surface_not_public": sorted(set(catalog_surfaces) - set(public_surfaces)),
        "public_not_catalog": sorted(set(public_surfaces) - set(catalog_surfaces)),
        "compact_not_wrapped": sorted(set(compact_allowlist) - set(mcp_wrappers)),
        "compact_not_catalog": sorted(set(compact_allowlist) - set(catalog_mcp)),
    }


def _writer_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in _source_paths(root):
        relative = _normalize_relative_path(path.relative_to(root).as_posix())
        if not relative.startswith(("brain/", "hooks/", "deploy/hooks/")):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        visitor = _WriterCallVisitor(relative)
        visitor.visit(tree)
        rows.extend(visitor.rows)
    return sorted(rows, key=lambda row: (row["path"], row["line"], row["call"]))


class _WriterCallVisitor(ast.NodeVisitor):
    def __init__(self, relative_path: str):
        self.relative_path = relative_path
        self.function_stack: list[str] = []
        self.rows: list[dict[str, Any]] = []

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
        if call_name in _WRITER_CALLS:
            families, dynamic = _registry_families_in_node(node)
            self.rows.append(
                {
                    "path": self.relative_path,
                    "function": self.function_stack[-1] if self.function_stack else "<module>",
                    "line": int(getattr(node, "lineno", 0)),
                    "call": call_name,
                    "registry_families": families,
                    "dynamic_registry_family": dynamic,
                }
            )
        self.generic_visit(node)


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


def _literal_named_assignment(path: Path, name: str, *, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return default
    for node in tree.body:
        targets: list[ast.expr]
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        else:
            continue
        if value is None or not any(
            isinstance(target, ast.Name) and target.id == name for target in targets
        ):
            continue
        try:
            return ast.literal_eval(value)
        except (ValueError, TypeError):
            return default
    return default


def _string_sequence_assignment(path: Path, name: str) -> list[str]:
    value = _literal_named_assignment(path, name, default=())
    if not isinstance(value, (list, tuple, set, frozenset)):
        return []
    return sorted({item for item in value if isinstance(item, str) and item})


def _function_names(path: Path, *, prefix: str = "") -> list[str]:
    if not path.exists():
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return []
    names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(prefix)
    }
    for node in tree.body:
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        for alias in node.names:
            exported = alias.asname or alias.name.rsplit(".", 1)[-1]
            if exported.startswith(prefix):
                names.add(exported)
    return sorted(names)


def _normalize_relative_path(value: str) -> str:
    return value.replace("\\", "/").removeprefix("./")
