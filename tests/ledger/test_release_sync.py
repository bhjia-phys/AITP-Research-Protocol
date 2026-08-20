"""Release-surface consistency smoke tests.

These catch the drift class where repo docs/tests say a feature shipped but a
published surface (plugin manifest, runtime version, Skill command map) still
runs the old protocol.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

import aitp

REPOSITORY = Path(__file__).resolve().parents[2]
PLUGIN = REPOSITORY / "plugins" / "aitp-research-protocol"


def test_published_versions_agree() -> None:
    kimi_version = json.loads(
        (PLUGIN / "kimi.plugin.json").read_text(encoding="utf-8")
    )["version"]
    codex_version = json.loads(
        (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )["version"]
    project = tomllib.loads(
        (REPOSITORY / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert codex_version.split("+", 1)[0] == kimi_version
    assert kimi_version == aitp.__version__
    assert kimi_version == project["project"]["version"]


def test_skill_command_map_covers_implemented_commands() -> None:
    skill = (PLUGIN / "skills" / "using-aitp" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "check remains absent" not in skill
    for command in (
        "init",
        "enter",
        "inventory",
        "backfill",
        "record",
        "note",
        "list",
        "show",
        "check",
    ):
        assert re.search(rf"`aitp {re.escape(command)}([ `]|$)", skill), command


def test_cli_help_lists_all_commands(capsys) -> None:
    from aitp.cli import main

    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
    output = capsys.readouterr().out
    for command in (
        "init",
        "enter",
        "list",
        "show",
        "check",
        "inventory",
        "backfill",
        "record",
        "note",
    ):
        assert re.search(
            rf"^\s+{re.escape(command)}\s", output, re.MULTILINE
        ), command
