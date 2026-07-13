"""Extract the runtime entrypoint mapping into bounded data modules."""

from __future__ import annotations

import ast
from pathlib import Path


MAX_PART_LINES = 450


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    target = repo / "brain" / "v5" / "runtime_entrypoint_catalog.py"
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "RUNTIME_ENTRYPOINTS"
    )
    if not isinstance(assignment.value, ast.Dict):
        raise RuntimeError("RUNTIME_ENTRYPOINTS must be a literal mapping")

    entries: list[str] = []
    for key_node, value_node in zip(assignment.value.keys, assignment.value.values, strict=True):
        if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
            raise RuntimeError("runtime entrypoint keys must be strings")
        value = ast.get_source_segment(source, value_node)
        if not value:
            raise RuntimeError(f"cannot extract {key_node.value}")
        entries.append(f"    {key_node.value!r}: {value},\n")

    groups: list[list[str]] = []
    current: list[str] = []
    lines = 6
    for entry in entries:
        size = len(entry.splitlines())
        if current and lines + size > MAX_PART_LINES:
            groups.append(current)
            current = []
            lines = 6
        current.append(entry)
        lines += size
    if current:
        groups.append(current)

    package = target.parent / "runtime_entrypoint_catalog_data"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text(
        '"""Bounded compatibility data for runtime entrypoints."""\n',
        encoding="utf-8",
    )
    imports: list[str] = []
    merges: list[str] = []
    for index, group in enumerate(groups, start=1):
        name = f"part_{index:02d}"
        (package / f"{name}.py").write_text(
            f'"""Runtime entrypoint catalog part {index}."""\n\n'
            "from __future__ import annotations\n\n"
            f"RUNTIME_ENTRYPOINTS_{index:02d} = {{\n"
            + "".join(group)
            + "}\n",
            encoding="utf-8",
        )
        imports.append(
            f"from brain.v5.runtime_entrypoint_catalog_data.{name} import RUNTIME_ENTRYPOINTS_{index:02d}"
        )
        merges.append(f"    **RUNTIME_ENTRYPOINTS_{index:02d},")

    facade = (
        '"""Runtime entrypoint catalog data and CLI sample arguments."""\n\n'
        "from __future__ import annotations\n\n"
        "from typing import Any\n\n"
        + "\n".join(imports)
        + "\n\nRUNTIME_ENTRYPOINTS: dict[str, dict[str, Any]] = {\n"
        + "\n".join(merges)
        + "\n}\n\n\n"
        "def capability_registry_ref() -> str:\n"
        '    """Return the authority that validates this compatibility catalog."""\n\n'
        '    return "brain.v5.capability_registry:capability_specs"\n\n\n'
        "def sample_args_for_template(template: str) -> list[str]:\n"
        "    from brain.v5.runtime_entrypoint_samples import sample_args_for_template as _sample_args\n\n"
        "    return _sample_args(template)\n"
    )
    target.write_text(facade, encoding="utf-8")
    print(f"extracted {len(entries)} entrypoints into {len(groups)} parts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
