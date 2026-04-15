from __future__ import annotations

import os
import runpy
import shutil
from pathlib import Path


PACKAGE_DISTRIBUTION_NAME = "aitp-kernel"
LEGACY_PACKAGE_DISTRIBUTION_NAMES: tuple[str, ...] = ()

_PACKAGE_DIR = Path(__file__).resolve().parent
_BUNDLE_DIRNAME = "_bundle"
_DYNAMIC_TOPIC_DIRS = (
    Path("topics"),
    Path("runtime/topics"),
    Path("source-layer/topics"),
    Path("intake/topics"),
    Path("feedback/topics"),
    Path("validation/topics"),
    Path("consultation/topics"),
)
_BUNDLE_SOURCE_DIRS = (
    "canonical",
    "consultation",
    "feedback",
    "intake",
    "runtime",
    "schemas",
    "source-layer",
    "topics",
    "validation",
)
_EXCLUDED_TOP_LEVEL_DIRS = {
    "__pycache__",
    ".pytest_cache",
    "aitp_kernel.egg-info",
    "build",
    "data",
    "examples",
    "knowledge_hub",
    "tests",
}
_EXCLUDED_RELATIVE_DIRS = {
    Path("topics"),
    Path("runtime/topics"),
    Path("source-layer/topics"),
    Path("intake/topics"),
    Path("feedback/topics"),
    Path("validation/topics"),
    Path("consultation/topics"),
}
_EXCLUDED_RELATIVE_FILES = {
    Path("runtime/current_topic.json"),
    Path("runtime/current_topic.md"),
    Path("runtime/topic_index.jsonl"),
}


def package_distribution_names() -> tuple[str, ...]:
    return (PACKAGE_DISTRIBUTION_NAME, *LEGACY_PACKAGE_DISTRIBUTION_NAMES)


def package_version() -> str:
    payload = runpy.run_path(str(_PACKAGE_DIR / "_version.py"))
    return str(payload["__version__"])


def package_bundle_root() -> Path:
    return _PACKAGE_DIR / _BUNDLE_DIRNAME


def package_bundle_available() -> bool:
    return (package_bundle_root() / "runtime" / "scripts" / "orchestrate_topic.py").exists()


def default_user_home() -> Path:
    override = os.environ.get("AITP_HOME")
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / ".aitp").resolve()


def default_user_kernel_root() -> Path:
    return default_user_home() / "kernel"


def materialized_default_user_kernel_root() -> Path:
    return ensure_materialized_kernel_root(default_user_kernel_root())


def should_include_bundle_path(relative_path: Path) -> bool:
    if not relative_path.parts:
        return False

    top_level = relative_path.parts[0]
    if top_level in _EXCLUDED_TOP_LEVEL_DIRS:
        return False

    if any(relative_path == excluded or excluded in relative_path.parents for excluded in _EXCLUDED_RELATIVE_DIRS):
        return False

    if relative_path in _EXCLUDED_RELATIVE_FILES:
        return False

    if len(relative_path.parts) == 1:
        return relative_path.suffix in {".json", ".md", ".txt"} or relative_path.name in {
            "README.md",
            "requirements.txt",
            "maintainability_budgets.json",
            "exploration_window.json",
        }

    return top_level in _BUNDLE_SOURCE_DIRS


def iter_bundle_source_files(source_root: Path) -> list[tuple[Path, Path]]:
    source_root = source_root.resolve()
    rows: list[tuple[Path, Path]] = []
    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(source_root)
        if should_include_bundle_path(relative_path):
            rows.append((path, relative_path))
    return rows


def build_bundle_tree(source_root: Path, destination_root: Path) -> list[Path]:
    source_root = source_root.resolve()
    destination_root = destination_root.resolve()
    if destination_root.exists():
        shutil.rmtree(destination_root)
    destination_root.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for source_path, relative_path in iter_bundle_source_files(source_root):
        target_path = destination_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        written.append(target_path)

    for relative_dir in _DYNAMIC_TOPIC_DIRS:
        (destination_root / relative_dir).mkdir(parents=True, exist_ok=True)

    return written


def ensure_materialized_kernel_root(target_root: Path, *, bundle_root: Path | None = None) -> Path:
    target_root = target_root.expanduser().resolve()
    source_root = (bundle_root or package_bundle_root()).expanduser().resolve()

    if not package_bundle_available() and bundle_root is None:
        return target_root
    if not (source_root / "runtime" / "scripts" / "orchestrate_topic.py").exists():
        return target_root
    if (target_root / "runtime" / "scripts" / "orchestrate_topic.py").exists():
        return target_root

    target_root.mkdir(parents=True, exist_ok=True)
    for source_path, relative_path in iter_bundle_source_files(source_root):
        target_path = target_root / relative_path
        if target_path.exists():
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)

    for relative_dir in _DYNAMIC_TOPIC_DIRS:
        (target_root / relative_dir).mkdir(parents=True, exist_ok=True)

    marker_path = target_root / ".aitp_bundle_install.json"
    marker_path.write_text(
        (
            "{\n"
            f'  "distribution": "{PACKAGE_DISTRIBUTION_NAME}",\n'
            f'  "version": "{package_version()}"\n'
            "}\n"
        ),
        encoding="utf-8",
    )
    return target_root
