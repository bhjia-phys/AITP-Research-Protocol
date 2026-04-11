#!/usr/bin/env python
"""Build the kernel wheel and verify bounded dependency metadata."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
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
        checks = {
            "requires_dist_mcp": "Requires-Dist: mcp<2.0.0,>=1.0.0" in metadata_text,
            "requires_dist_jsonschema": "Requires-Dist: jsonschema<5.0.0,>=4.0.0" in metadata_text,
            "requires_python": "Requires-Python: >=3.10" in metadata_text,
        }
        if not all(checks.values()):
            raise RuntimeError(f"Dependency metadata check failed: {checks}")
        payload = {
            "wheel_path": str(wheels[0]),
            "checks": checks,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=True, indent=2))
        else:
            print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
