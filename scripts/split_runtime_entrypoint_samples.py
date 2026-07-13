"""Split the runtime CLI sample resolver into ordered bounded functions."""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path


MAX_PART_LINES = 430


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    target = repo / "brain" / "v5" / "runtime_entrypoint_samples.py"
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source)
    sample = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "sample_args_for_template"
    )
    adapter = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "adapter_sample_args"
    )
    statements = sample.body[2:-1]
    groups: list[list[str]] = []
    current: list[str] = []
    line_count = 7
    for statement in statements:
        segment = ast.get_source_segment(source, statement)
        if not segment:
            raise RuntimeError("cannot extract sample resolver statement")
        segment = textwrap.dedent(segment).rstrip()
        size = len(segment.splitlines()) + 1
        if current and line_count + size > MAX_PART_LINES:
            groups.append(current)
            current = []
            line_count = 7
        current.append(segment)
        line_count += size
    if current:
        groups.append(current)

    package = target.parent / "runtime_entrypoint_sample_data"
    package.mkdir(parents=True, exist_ok=True)
    imports: list[str] = []
    names: list[str] = []
    for index, group in enumerate(groups, start=1):
        name = f"sample_args_part_{index:02d}"
        body = "\n".join(textwrap.indent(segment, "    ") for segment in group)
        (package / f"part_{index:02d}.py").write_text(
            f'"""Runtime CLI sample resolver part {index}."""\n\n'
            "from __future__ import annotations\n\n\n"
            f"def {name}(template: str) -> list[str] | None:\n"
            f"{body}\n"
            "    return None\n",
            encoding="utf-8",
        )
        imports.append(f"from .part_{index:02d} import {name}")
        names.append(name)
    (package / "__init__.py").write_text(
        '"""Ordered bounded runtime CLI sample resolvers."""\n\n'
        + "\n".join(imports)
        + "\n\nSAMPLE_ARG_RESOLVERS = (\n"
        + "\n".join(f"    {name}," for name in names)
        + "\n)\n",
        encoding="utf-8",
    )

    adapter_source = ast.get_source_segment(source, adapter)
    if not adapter_source:
        raise RuntimeError("cannot extract adapter sample resolver")
    facade = (
        '"""Focused sample argv helpers for runtime entrypoint validation."""\n\n'
        "from __future__ import annotations\n\n"
        "from brain.v5.runtime_entrypoint_sample_data import SAMPLE_ARG_RESOLVERS\n\n\n"
        "def sample_args_for_template(template: str) -> list[str]:\n"
        "    adapter_args = adapter_sample_args(template)\n"
        "    if adapter_args is not None:\n"
        "        return adapter_args\n"
        "    for resolver in SAMPLE_ARG_RESOLVERS:\n"
        "        result = resolver(template)\n"
        "        if result is not None:\n"
        "            return result\n"
        "    return []\n\n\n"
        + adapter_source
        + "\n"
    )
    target.write_text(facade, encoding="utf-8")
    print(f"extracted sample resolver into {len(groups)} parts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
