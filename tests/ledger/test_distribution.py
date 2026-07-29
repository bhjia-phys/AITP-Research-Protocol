from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from aitp.core import init_workspace, parse_markdown, prepare_entry


def test_using_aitp_skill_is_packaged_and_matches_cli() -> None:
    root = files("aitp").joinpath("resources/skills/using-aitp")
    skill = root.joinpath("SKILL.md").read_text(encoding="utf-8")
    metadata = root.joinpath("agents/openai.yaml").read_text(encoding="utf-8")

    assert "name: using-aitp" in skill
    assert "aitp enter" in skill
    assert "aitp record prepare" in skill
    assert "aitp note prepare --mode working --title" in skill
    assert "there is no `aitp search`" in skill
    assert "$using-aitp" in metadata


def test_prepared_entries_have_strictly_ordered_timestamps(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    init_workspace(root, "fast", "Fast consecutive records")

    first = prepare_entry(root, "decision", "human")
    second = prepare_entry(root, "decision", "human")
    first_frontmatter, _, _ = parse_markdown(root / first["path"])
    second_frontmatter, _, _ = parse_markdown(root / second["path"])

    assert first_frontmatter["created_at"] < second_frontmatter["created_at"]
    assert "." in first_frontmatter["created_at"]
