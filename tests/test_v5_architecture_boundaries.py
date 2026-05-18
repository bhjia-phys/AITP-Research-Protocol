from __future__ import annotations

from pathlib import Path


MAX_V5_SOURCE_MODULE_LINES = 700


def test_v5_source_modules_stay_bounded():
    repo_root = Path(__file__).resolve().parents[1]
    source_root = repo_root / "brain" / "v5"

    oversized = {}
    for module_path in sorted(source_root.glob("*.py")):
        line_count = len(module_path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_V5_SOURCE_MODULE_LINES:
            oversized[module_path.name] = line_count

    assert oversized == {}
