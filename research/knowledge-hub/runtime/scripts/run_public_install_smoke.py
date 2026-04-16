#!/usr/bin/env python
"""Build a public wheel, install it into a clean venv, and smoke the installed aitp CLI."""

from __future__ import annotations

import argparse
import json
import os
import runpy
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
KERNEL_ROOT = SCRIPT_PATH.parents[2]

TOPIC_TITLE = "Jones Chapter 4 finite-dimensional backbone"
TOPIC_STATEMENT = "Start from the finite-dimensional backbone and record the first honest closure target."
LOOP_REQUEST = "Continue with the first bounded route and stop before expensive execution."
TOPIC_SLUG = "jones-chapter-4-finite-dimensional-backbone"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--json", action="store_true")
    return parser


def expected_version(package_root: Path) -> str:
    payload = runpy.run_path(str(package_root / "knowledge_hub" / "_version.py"))
    return str(payload["__version__"])


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        stdin=subprocess.DEVNULL,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")
    return completed


def build_wheel(*, package_root: Path, dist_dir: Path) -> Path:
    completed = run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--wheel-dir",
            str(dist_dir),
            str(package_root),
        ],
        cwd=package_root,
        env=os.environ.copy(),
    )
    _ = completed
    wheels = sorted(dist_dir.glob("*.whl"))
    if not wheels:
        raise FileNotFoundError("No wheel was produced by pip wheel")
    return wheels[0]


def create_virtualenv(venv_root: Path) -> None:
    venv.EnvBuilder(with_pip=True, clear=True).create(str(venv_root))


def resolve_venv_python(venv_root: Path) -> Path:
    for relative_path in (
        Path("Scripts/python.exe"),
        Path("Scripts/python"),
        Path("bin/python"),
        Path("bin/python3"),
    ):
        candidate = venv_root / relative_path
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not locate venv python under {venv_root}")


def resolve_venv_bin_dir(venv_root: Path) -> Path:
    python_path = resolve_venv_python(venv_root)
    return python_path.parent


def smoke_environment(*, aitp_home: Path, venv_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["AITP_HOME"] = str(aitp_home)
    env["PATH"] = str(resolve_venv_bin_dir(venv_root)) + os.pathsep + env.get("PATH", "")
    for variable in ("PYTHONPATH", "AITP_REPO_ROOT", "AITP_KERNEL_ROOT", "PWD", "OLDPWD"):
        env.pop(variable, None)
    return env


def run_aitp_json(*, args: list[str], cwd: Path, env: dict[str, str]) -> dict[str, Any]:
    completed = run_command(["aitp", *args, "--json"], cwd=cwd, env=env)
    return json.loads(completed.stdout)


def run_installed_module_json(*, python_path: Path, args: list[str], cwd: Path, env: dict[str, str]) -> dict[str, Any]:
    completed = run_command(
        [str(python_path), "-m", "knowledge_hub.aitp_cli", *args, "--json"],
        cwd=cwd,
        env=env,
    )
    return json.loads(completed.stdout)


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-public-install-smoke-")).resolve()
    )
    dist_dir = work_root / "dist"
    venv_root = work_root / "venv"
    aitp_home = work_root / "aitp-home"
    dist_dir.mkdir(parents=True, exist_ok=True)

    wheel_path = build_wheel(package_root=package_root, dist_dir=dist_dir)
    create_virtualenv(venv_root)
    venv_python = resolve_venv_python(venv_root)

    install_env = os.environ.copy()
    run_command(
        [str(venv_python), "-m", "pip", "install", str(wheel_path)],
        cwd=work_root,
        env=install_env,
    )

    cli_env = smoke_environment(aitp_home=aitp_home, venv_root=venv_root)
    version_text = run_command(["aitp", "--version"], cwd=work_root, env=cli_env).stdout.strip()
    expected = expected_version(package_root)
    check(expected in version_text, f"Expected aitp --version to include {expected!r}, got {version_text!r}")

    doctor_payload = run_aitp_json(args=["doctor"], cwd=work_root, env=cli_env)
    expected_kernel_root = (aitp_home / "kernel").resolve()
    check(
        doctor_payload["package"]["name"] == "aitp-kernel",
        "doctor should report the published distribution name",
    )
    check(
        doctor_payload["package"]["version"] == expected,
        "doctor should report the installed package version",
    )
    check(
        Path(doctor_payload["command_paths"]["aitp"]).resolve().parent == resolve_venv_bin_dir(venv_root).resolve(),
        "doctor should resolve the aitp command from the smoke virtualenv",
    )

    isolated_env = dict(cli_env)
    isolated_env["AITP_KERNEL_ROOT"] = str(expected_kernel_root)
    isolated_env["AITP_REPO_ROOT"] = str(work_root)
    isolated_doctor_payload = run_installed_module_json(
        python_path=venv_python,
        args=["doctor"],
        cwd=work_root,
        env=isolated_env,
    )
    check(
        Path(isolated_doctor_payload["kernel_root"]).resolve() == expected_kernel_root,
        "isolated doctor should materialize the installed kernel bundle into AITP_HOME/kernel",
    )
    check(
        Path(isolated_doctor_payload["repo_root"]).resolve() == work_root.resolve(),
        "isolated doctor should stay pinned to the smoke workspace rather than a host repo checkout",
    )
    check(
        isolated_doctor_payload["package"]["status"] == "installed",
        "isolated module doctor should see a non-editable installed package inside the smoke venv",
    )
    ensure_exists(expected_kernel_root / "runtime" / "scripts" / "orchestrate_topic.py")

    bootstrap_payload = run_installed_module_json(
        python_path=venv_python,
        args=[
            "bootstrap",
            "--topic",
            TOPIC_TITLE,
            "--statement",
            TOPIC_STATEMENT,
        ],
        cwd=work_root,
        env=isolated_env,
    )
    loop_payload = run_installed_module_json(
        python_path=venv_python,
        args=[
            "loop",
            "--topic-slug",
            TOPIC_SLUG,
            "--human-request",
            LOOP_REQUEST,
            "--max-auto-steps",
            "1",
        ],
        cwd=work_root,
        env=isolated_env,
    )
    status_payload = run_installed_module_json(
        python_path=venv_python,
        args=[
            "status",
            "--topic-slug",
            TOPIC_SLUG,
        ],
        cwd=work_root,
        env=isolated_env,
    )

    check(bootstrap_payload["topic_slug"] == TOPIC_SLUG, "bootstrap should create the expected topic slug")
    check(loop_payload["topic_slug"] == TOPIC_SLUG, "loop should stay on the same topic")
    check(status_payload["topic_slug"] == TOPIC_SLUG, "status should read the same topic")
    check(loop_payload["load_profile"] == "light", "first-run loop should stay in the light runtime profile")
    check(bool(status_payload.get("selected_action_id")), "status should expose the next bounded action")

    ensure_exists(Path(bootstrap_payload["files"]["topic_state"]))
    ensure_exists(Path(bootstrap_payload["files"]["runtime_protocol"]))
    ensure_exists(Path(loop_payload["loop_state_path"]))
    ensure_exists(Path(loop_payload["runtime_protocol"]["runtime_protocol_path"]))
    ensure_exists(Path(status_payload["runtime_protocol_path"]))
    ensure_exists(Path(status_payload["runtime_protocol_note_path"]))

    payload = {
        "work_root": str(work_root),
        "wheel_path": str(wheel_path),
        "venv_python": str(venv_python),
        "aitp_home": str(aitp_home),
        "expected_version": expected,
        "version_output": version_text,
        "doctor_entrypoint": doctor_payload,
        "doctor_isolated": isolated_doctor_payload,
        "bootstrap": bootstrap_payload,
        "loop": loop_payload,
        "status": status_payload,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(
            "public install smoke passed\n"
            f"wheel: {wheel_path}\n"
            f"version: {version_text}\n"
            f"topic_slug: {TOPIC_SLUG}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
