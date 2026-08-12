from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
PLUGIN = REPOSITORY / "plugins" / "aitp-research-protocol"
RUNNER = PLUGIN / "scripts" / "aitp.py"


def run_plugin(*arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(RUNNER), *arguments],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def test_plugin_manifest_and_marketplace_are_wired() -> None:
    manifest = json.loads(
        (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    marketplace = json.loads(
        (REPOSITORY / ".agents" / "plugins" / "marketplace.json").read_text(
            encoding="utf-8"
        )
    )

    assert manifest["name"] == "aitp-research-protocol"
    assert manifest["skills"] == "./skills/"
    assert marketplace["name"] == "aitp-protocol"
    assert marketplace["plugins"][0]["source"]["path"] == (
        "./plugins/aitp-research-protocol"
    )

    using_aitp = (PLUGIN / "skills" / "using-aitp" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "python3.12" in using_aitp
    assert "Python 3.11 or newer" in using_aitp


def test_offline_plugin_runner_initializes_and_enters_workspace(tmp_path: Path) -> None:
    root = tmp_path / "research"
    root.mkdir()

    initialized = run_plugin(
        "init",
        "--topic",
        "qft",
        "--title",
        "QFT project",
        "--json",
        cwd=root,
    )
    assert initialized.returncode == 0, initialized.stderr
    assert json.loads(initialized.stdout)["status"] == "initialized"

    entered = run_plugin("enter", "--json", cwd=root)
    assert entered.returncode == 0, entered.stderr
    assert json.loads(entered.stdout)["topic"]["id"] == "qft"

    prepared = run_plugin(
        "record",
        "prepare",
        "--kind",
        "code-change",
        "--authority",
        "agent",
        "--created-by",
        "agent:test",
        "--json",
        cwd=root,
    )
    assert prepared.returncode == 0, prepared.stderr
    assert json.loads(prepared.stdout)["status"] == "prepared"
