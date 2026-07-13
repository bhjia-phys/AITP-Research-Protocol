"""Extract built-in domain-pack literals into focused builder modules."""

from __future__ import annotations

import ast
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    target = repo / "brain" / "v5" / "domain_packs.py"
    source = target.read_text(encoding="utf-8")
    tree = ast.parse(source)
    record = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "DomainPackRecord"
    )
    builtin = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "builtin_domain_packs"
    )
    return_node = next(node for node in builtin.body if isinstance(node, ast.Return))
    if not isinstance(return_node.value, ast.Dict):
        raise RuntimeError("builtin_domain_packs must return a literal mapping")

    package = target.parent / "domain_pack_catalog"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text(
        '"""Focused built-in theoretical-physics domain-pack builders."""\n',
        encoding="utf-8",
    )
    imports: list[str] = []
    rows: list[str] = []
    for key_node, value_node in zip(return_node.value.keys, return_node.value.values, strict=True):
        if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
            raise RuntimeError("domain-pack keys must be strings")
        pack_id = key_node.value
        expression = ast.get_source_segment(source, value_node)
        if not expression:
            raise RuntimeError(f"cannot extract domain pack {pack_id}")
        module = package / f"{pack_id}.py"
        module.write_text(
            f'"""Built-in {pack_id} domain pack."""\n\n'
            "from brain.v5.domain_pack_types import DomainPackRecord\n\n\n"
            "def build_domain_pack() -> DomainPackRecord:\n"
            f"    return {expression}\n",
            encoding="utf-8",
        )
        imports.append(
            f"    from brain.v5.domain_pack_catalog.{pack_id} import build_domain_pack as build_{pack_id}"
        )
        rows.append(f'        "{pack_id}": build_{pack_id}(),')

    class_text = ast.get_source_segment(source, record)
    if not class_text:
        raise RuntimeError("cannot extract DomainPackRecord")
    (target.parent / "domain_pack_types.py").write_text(
        '"""Shared type for built-in and workspace domain packs."""\n\n'
        "from __future__ import annotations\n\n"
        "from dataclasses import dataclass, field\n\n\n"
        f"@dataclass\n{class_text}\n",
        encoding="utf-8",
    )

    replacement = (
        "def builtin_domain_packs() -> dict[str, DomainPackRecord]:\n"
        '    """Return built-in theoretical-physics domain packs."""\n\n'
        + "\n".join(imports)
        + "\n\n    return {\n"
        + "\n".join(rows)
        + "\n    }"
    )
    lines = source.splitlines()
    class_start = min(
        [record.lineno, *(decorator.lineno for decorator in record.decorator_list)]
    )
    lines[class_start - 1 : record.end_lineno] = [
        "from brain.v5.domain_pack_types import DomainPackRecord"
    ]
    delta = record.end_lineno - class_start
    builtin_start = builtin.lineno - delta - 1
    builtin_end = builtin.end_lineno - delta
    lines[builtin_start:builtin_end] = replacement.splitlines()
    rewritten = "\n".join(lines) + "\n"
    rewritten = rewritten.replace("from dataclasses import dataclass, field\n\n", "")
    target.write_text(rewritten, encoding="utf-8")
    print(f"extracted {len(rows)} domain packs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
