"""Read-only audit of AITP v5 runtime files and record-family usage."""

from __future__ import annotations

import ast
import re
import warnings
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from brain.v5.writer_scan import (
    direct_mutation_rows,
    helper_writer_rows,
    writer_scan_policy,
)


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
    layout = _layout_families(
        root / "brain" / "v5" / "paths.py",
        registry_path=root / "brain" / "v5" / "record_family_registry.py",
    )
    used, users = _literal_registry_families(root / "brain" / "v5")
    actual_counts = _actual_registry_counts(Path(workspace_base)) if workspace_base else {}
    actual = sorted(actual_counts)
    capabilities = _capability_inventory(root / "brain" / "v5")
    writers = helper_writer_rows(root, _source_paths(root))
    direct_mutations = direct_mutation_rows(root, _source_paths(root))
    counts = Counter(row["classification"] for row in files)
    return {
        "kind": "runtime_capability_audit",
        "repo_root": str(root),
        "workspace_base": str(Path(workspace_base).resolve()) if workspace_base else "",
        "inventory": {
            "file_count": len(files),
            "writer_count": len(writers),
            "direct_mutation_candidate_count": len(direct_mutations),
            "direct_mutation_file_count": len({row["path"] for row in direct_mutations}),
            "actual_registry_record_count": sum(actual_counts.values()),
            "classification_counts": dict(sorted(counts.items())),
        },
        "files": files,
        "capabilities": capabilities,
        "writers": writers,
        "direct_mutation_candidates": direct_mutations,
        "writer_scan_policy": writer_scan_policy(files),
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
            _parse_python(path)
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


def _layout_families(path: Path, *, registry_path: Path | None = None) -> list[str]:
    if not path.exists():
        return []
    tree = _parse_python(path)
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == "_LAYOUT_DIRS" for target in targets):
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
    rows = _literal_named_assignment(registry_path, "_REGISTRY_ROWS", default=())
    if not isinstance(rows, (list, tuple)):
        return []
    return sorted(
        row[0]
        for row in rows
        if isinstance(row, (list, tuple)) and row and isinstance(row[0], str)
    )


def _literal_registry_families(directory: Path) -> tuple[list[str], dict[str, list[str]]]:
    users: dict[str, list[str]] = {}
    if not directory.exists():
        return [], users
    for path in sorted(directory.glob("*.py")):
        try:
            tree = _parse_python(path)
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
    catalog = _runtime_catalog_mapping(directory)
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
    public_surfaces = sorted(
        {
            *(
                surface
                for path in _module_source_files(directory, "public_surfaces")
                for surface in _string_sequence_assignment(path, "_PUBLIC_SURFACE_NAMES")
            ),
            *_mapping_key_assignment(
                directory / "capability_surface_contracts.py",
                "_RULES",
            ),
            *_mapping_key_assignment(
                directory / "lifecycle_surface_contracts.py",
                "_RULES",
            ),
        }
    )
    registry_data = directory / "capability_registry_data.py"
    legacy_facade = directory / "codex_facade.py"
    facade_tools = sorted(set(_string_sequence_assignment(registry_data, "CODEX_FACADE_MCP_NAMES")) | set(_string_sequence_assignment(legacy_facade, "CODEX_FACADE_TOOLS")))
    support_tools = sorted(set(_string_sequence_assignment(registry_data, "CODEX_SUPPORT_MCP_NAMES")) | set(_string_sequence_assignment(legacy_facade, "CODEX_SUPPORT_TOOLS")))
    compact_allowlist = sorted(set(facade_tools) | set(support_tools))
    mcp_wrappers = sorted(
        {
            name
            for path in _module_source_files(directory, "mcp_tools")
            for name in _function_names(path, prefix="aitp_v5_")
        }
    )
    registry_rows = _capability_rows(registry_data, "MCP_ONLY_CAPABILITIES")
    optional_rows = _capability_rows(registry_data, "OPTIONAL_MCP_CAPABILITIES")
    registry_rows.extend(row for row in optional_rows if row[1] in mcp_wrappers)
    registry_operations = sorted({*catalog, *(row[0] for row in registry_rows)})
    registry_mcp = sorted({*catalog_mcp, *(row[1] for row in registry_rows)})
    registry_surfaces = sorted({*catalog_surfaces, *(row[3] for row in registry_rows)})
    return {
        "catalog_operations": sorted(str(key) for key in catalog),
        "catalog_mcp": catalog_mcp,
        "catalog_surfaces": catalog_surfaces,
        "registry_operations": registry_operations,
        "registry_mcp": registry_mcp,
        "registry_surfaces": registry_surfaces,
        "public_surfaces": public_surfaces,
        "mcp_wrappers": mcp_wrappers,
        "compact_allowlist": compact_allowlist,
        "catalog_mcp_not_wrapped": sorted(set(catalog_mcp) - set(mcp_wrappers)),
        "wrapped_not_catalog": sorted(set(mcp_wrappers) - set(catalog_mcp)),
        "catalog_surface_not_public": sorted(set(catalog_surfaces) - set(public_surfaces)),
        "public_not_catalog": sorted(set(public_surfaces) - set(catalog_surfaces)),
        "compact_not_wrapped": sorted(set(compact_allowlist) - set(mcp_wrappers)),
        "compact_not_catalog": sorted(set(compact_allowlist) - set(catalog_mcp)),
        "registry_mcp_not_wrapped": sorted(set(registry_mcp) - set(mcp_wrappers)),
        "wrapped_not_registry": sorted(set(mcp_wrappers) - set(registry_mcp)),
        "registry_surface_not_public": sorted(set(registry_surfaces) - set(public_surfaces)),
        "compact_not_registry": sorted(set(compact_allowlist) - set(registry_mcp)),
    }


def _runtime_catalog_mapping(directory: Path) -> dict[str, Any]:
    paths = [directory / "runtime_entrypoint_catalog.py"]
    paths.extend(sorted((directory / "runtime_entrypoint_catalog_data").glob("part_*.py")))
    catalog: dict[str, Any] = {}
    for path in paths:
        for value in _literal_assignments_with_prefix(path, "RUNTIME_ENTRYPOINTS"):
            if isinstance(value, dict):
                catalog.update(value)
    return catalog


def _module_source_files(directory: Path, stem: str) -> list[Path]:
    paths = [directory / f"{stem}.py"]
    paths.extend(sorted((directory / "_compat_shards" / stem).glob("part_*.py")))
    return [path for path in paths if path.exists()]


def _capability_rows(path: Path, name: str) -> list[tuple[Any, ...]]:
    value = _literal_named_assignment(path, name, default=())
    if not isinstance(value, (list, tuple)):
        return []
    return [tuple(row) for row in value if isinstance(row, (list, tuple)) and len(row) >= 4]


def _literal_named_assignment(path: Path, name: str, *, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        tree = _parse_python(path)
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


def _literal_assignments_with_prefix(path: Path, prefix: str) -> list[Any]:
    if not path.exists():
        return []
    try:
        tree = _parse_python(path)
    except (SyntaxError, UnicodeDecodeError):
        return []
    values: list[Any] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign):
            targets, value = [node.target], node.value
        else:
            continue
        if value is None or not any(
            isinstance(target, ast.Name) and target.id.startswith(prefix)
            for target in targets
        ):
            continue
        try:
            values.append(ast.literal_eval(value))
        except (ValueError, TypeError):
            continue
    return values


def _mapping_key_assignment(path: Path, name: str) -> list[str]:
    if not path.exists():
        return []
    try:
        tree = _parse_python(path)
    except (SyntaxError, UnicodeDecodeError):
        return []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign):
            targets, value = [node.target], node.value
        else:
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in targets):
            continue
        if not isinstance(value, ast.Dict):
            return []
        return sorted(
            key.value
            for key in value.keys
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
        )
    return []


def _string_sequence_assignment(path: Path, name: str) -> list[str]:
    value = _literal_named_assignment(path, name, default=())
    if not isinstance(value, (list, tuple, set, frozenset)):
        return []
    return sorted({item for item in value if isinstance(item, str) and item})


def _function_names(path: Path, *, prefix: str = "") -> list[str]:
    if not path.exists():
        return []
    try:
        tree = _parse_python(path)
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


def _parse_python(path: Path) -> ast.Module:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
