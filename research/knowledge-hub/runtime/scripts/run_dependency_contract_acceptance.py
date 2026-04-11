#!/usr/bin/env python
"""Build the kernel wheel and verify bounded dependency metadata."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import tarfile
import zipfile
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
KERNEL_ROOT = SCRIPT_PATH.parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--json", action="store_true")
    return parser


def extract_metadata_text(wheel_path: Path) -> str:
    with zipfile.ZipFile(wheel_path) as archive:
        metadata_name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        return archive.read(metadata_name).decode("utf-8")


def build_sdist(*, package_root: Path, dist_dir: Path) -> Path:
    command = [
        sys.executable,
        "setup.py",
        "sdist",
        "--dist-dir",
        str(dist_dir),
    ]
    completed = subprocess.run(
        command,
        cwd=package_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")
    sdists = sorted(dist_dir.glob("*.tar.gz"))
    if not sdists:
        raise FileNotFoundError("No sdist was produced by setup.py sdist")
    return sdists[0]


def extract_sdist_names(sdist_path: Path) -> set[str]:
    with tarfile.open(sdist_path, "r:gz") as archive:
        return {member.name for member in archive.getmembers()}


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    with tempfile.TemporaryDirectory(prefix="aitp-wheel-acceptance-") as tmpdir:
        wheel_dir = Path(tmpdir)
        command = [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--wheel-dir",
            str(wheel_dir),
            str(package_root),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
            raise RuntimeError(f"{' '.join(command)} failed: {detail}")
        wheels = sorted(wheel_dir.glob("*.whl"))
        if not wheels:
            raise FileNotFoundError("No wheel was produced by pip wheel")
        metadata_text = extract_metadata_text(wheels[0])
        with zipfile.ZipFile(wheels[0]) as archive:
            wheel_names = set(archive.namelist())
        sdist_path = build_sdist(package_root=package_root, dist_dir=wheel_dir)
        sdist_names = extract_sdist_names(sdist_path)
        checks = {
            "distribution_name": "Name: aitp-kernel" in metadata_text,
            "requires_dist_mcp": "Requires-Dist: mcp<2.0.0,>=1.0.0" in metadata_text,
            "requires_dist_jsonschema": "Requires-Dist: jsonschema<5.0.0,>=4.0.0" in metadata_text,
            "requires_python": "Requires-Python: >=3.10" in metadata_text,
            "bundle_layer_map": "knowledge_hub/_bundle/LAYER_MAP.md" in wheel_names,
            "bundle_orchestrator": "knowledge_hub/_bundle/runtime/scripts/orchestrate_topic.py" in wheel_names,
            "sdist_name": sdist_path.name.startswith("aitp_kernel-") and sdist_path.name.endswith(".tar.gz"),
            "sdist_layer_map": any(name.endswith("/LAYER_MAP.md") for name in sdist_names),
            "sdist_runtime_script": any(name.endswith("/runtime/scripts/orchestrate_topic.py") for name in sdist_names),
        }
        if not all(checks.values()):
            raise RuntimeError(f"Dependency metadata check failed: {checks}")
        payload = {
            "wheel_path": str(wheels[0]),
            "sdist_path": str(sdist_path),
            "checks": checks,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=True, indent=2))
        else:
            print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
