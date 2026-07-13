from __future__ import annotations

import ast
import inspect
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

from brain.v5.store import LEGACY_TOLERANT_READ_OPERATIONS, list_valid_records


@dataclass
class _LegacyItem:
    item_id: str


def test_tolerant_reads_require_a_named_legacy_or_recovery_operation():
    with pytest.raises(ValueError, match="named legacy or recovery operation"):
        list_valid_records(Path("missing"), dict)

    assert (
        list_valid_records(
            Path("missing"),
            dict,
            operation="legacy_migration_accounting",
        )
        == []
    )


def test_named_legacy_tolerant_read_skips_invalid_yaml_without_weakening_strict_reads(
    tmp_path,
):
    from brain.v5.markdown import write_md
    from brain.v5.store import list_records

    root = tmp_path / "legacy"
    write_md(root / "valid.md", {"item_id": "valid"}, "# Valid\n")
    (root / "broken.md").write_text(
        "---\nitem_id: [unterminated\n---\n# Broken\n",
        encoding="utf-8",
    )

    with pytest.raises(yaml.YAMLError, match="flow sequence|expected"):
        list_records(root, _LegacyItem)

    records = list_valid_records(
        root,
        _LegacyItem,
        operation="legacy_migration_accounting",
    )
    assert [record.item_id for record in records] == ["valid"]


def test_all_runtime_tolerant_reads_declare_an_allowed_operation():
    source_root = Path(__file__).resolve().parents[1] / "brain" / "v5"
    undeclared = []
    unknown = []

    for path in source_root.rglob("*.py"):
        if path.name == "store.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id != "list_valid_records":
                continue
            values = [
                keyword.value.value
                for keyword in node.keywords
                if keyword.arg == "operation"
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, str)
            ]
            relative = path.relative_to(source_root).as_posix()
            if not values:
                undeclared.append(f"{relative}:{node.lineno}")
            elif values[0] not in LEGACY_TOLERANT_READ_OPERATIONS:
                unknown.append(f"{relative}:{node.lineno}:{values[0]}")

    assert undeclared == []
    assert unknown == []


def test_normal_evidence_reader_does_not_catch_and_drop_malformed_records():
    from brain.v5.evidence import list_evidence_for_claim

    source = inspect.getsource(list_evidence_for_claim)
    assert "except" not in source
    assert "continue" not in source


def test_normal_canonical_readers_do_not_catch_and_drop_records():
    source_root = Path(__file__).resolve().parents[1] / "brain" / "v5"
    allowed_recovery_paths = {
        "store.py",
        "workspace_recovery_binding_repair.py",
    }
    silent_drops = []

    for path in source_root.rglob("*.py"):
        relative = path.relative_to(source_root).as_posix()
        if relative in allowed_recovery_paths:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            calls = {
                child.func.id
                for child in ast.walk(ast.Module(body=node.body, type_ignores=[]))
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
            }
            if not calls.intersection({"read_record", "list_records"}):
                continue
            drops = any(
                any(isinstance(child, (ast.Continue, ast.Pass)) for child in ast.walk(handler))
                and not any(isinstance(child, ast.Raise) for child in ast.walk(handler))
                for handler in node.handlers
            )
            if drops:
                silent_drops.append(f"{relative}:{node.lineno}")

    assert silent_drops == []
