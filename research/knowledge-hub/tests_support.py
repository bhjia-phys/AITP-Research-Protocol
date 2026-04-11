from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TempKernelFixture:
    temp_root: Path
    kernel_root: Path

    def cleanup(self) -> None:
        shutil.rmtree(self.temp_root)


def make_temp_kernel(prefix: str) -> TempKernelFixture:
    temp_root = Path(tempfile.mkdtemp(prefix=prefix))
    return TempKernelFixture(temp_root=temp_root, kernel_root=temp_root / "kernel")


def copy_canonical_tree(package_root: Path, kernel_root: Path) -> None:
    shutil.copytree(package_root / "canonical", kernel_root / "canonical", dirs_exist_ok=True)


def copy_kernel_schema_files(package_root: Path, kernel_root: Path, *names: str) -> None:
    target_root = kernel_root / "schemas"
    target_root.mkdir(parents=True, exist_ok=True)
    for name in names:
        source = package_root / "schemas" / name
        target = target_root / name
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def copy_runtime_schema_files(package_root: Path, kernel_root: Path, *names: str) -> None:
    target_root = kernel_root / "runtime" / "schemas"
    target_root.mkdir(parents=True, exist_ok=True)
    for name in names:
        source = package_root / "runtime" / "schemas" / name
        target = target_root / name
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def write_protocol_placeholders(kernel_root: Path, *names: str) -> None:
    for name in names:
        (kernel_root / name).write_text(f"# {name}\n", encoding="utf-8")
