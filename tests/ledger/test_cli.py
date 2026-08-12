from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(
        Path(__file__).parents[2]
        / "plugins"
        / "aitp-research-protocol"
        / "scripts"
        / "vendor"
    )
    return subprocess.run(
        [sys.executable, "-m", "aitp", *args],
        cwd=repo,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_cli_init_and_enter_json(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()

    initialized = run_cli(
        root,
        "init",
        "--cwd",
        ".",
        "--topic",
        "qft",
        "--title",
        "Quantum Field Theory",
        "--json",
    )
    assert initialized.returncode == 0, initialized.stderr
    assert json.loads(initialized.stdout)["status"] == "initialized"

    entered = run_cli(root, "enter", "--cwd", ".", "--json")
    assert entered.returncode == 0, entered.stderr
    payload = json.loads(entered.stdout)
    assert payload["memory_status"] == "not_established"
    assert payload["topic"]["id"] == "qft"


def test_cli_refuses_nonblank_workspace(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "existing.txt").write_text("user data", encoding="utf-8")

    result = run_cli(
        root,
        "init",
        "--cwd",
        ".",
        "--topic",
        "qft",
        "--title",
        "Quantum Field Theory",
        "--json",
    )
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["code"] == "workspace_not_blank"


def test_cli_enter_rejects_nonpositive_recent(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()

    for bad_recent in ("0", "-1", "not-a-number"):
        result = run_cli(root, "enter", "--cwd", ".", "--recent", bad_recent)
        assert result.returncode == 2, result.stderr
        assert "--recent" in result.stderr
