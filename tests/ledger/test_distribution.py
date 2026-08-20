from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from aitp.core import init_workspace, parse_markdown, prepare_entry, prepare_note


def test_using_aitp_skill_has_a_single_source() -> None:
    plugin = Path(__file__).parents[2] / "plugins" / "aitp-research-protocol"
    skill = (plugin / "skills" / "using-aitp" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    metadata = (plugin / "skills" / "using-aitp" / "agents" / "openai.yaml")
    assert "name: using-aitp" in skill
    assert "aitp enter" in skill
    assert "aitp record prepare" in skill
    assert "aitp note prepare --mode working --title" in skill
    assert "there is no\n`aitp search`" in skill
    assert "$using-aitp" in metadata.read_text(encoding="utf-8")
    assert not files("aitp").joinpath("resources/skills").is_dir()


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


def test_prepare_drafts_show_required_ref_at_key(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    init_workspace(root, "fast", "Fast consecutive records")

    entry = prepare_entry(root, "result", "agent", created_by="agent:test")
    entry_draft = (root / entry["path"]).read_text(encoding="utf-8")
    assert "- target: relative/path-or-url" in entry_draft
    assert "at: sha256:" in entry_draft
    assert "never pin" in entry_draft

    note = prepare_note(root, "working", "Current status", created_by="agent:test")
    note_draft = (root / note["path"]).read_text(encoding="utf-8")
    assert "basis_refs maps with required keys target and at" in note_draft
