#!/usr/bin/env python3
"""Install the AITP OpenClaw plugin plus the minimal workspace/profile seed."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = SCRIPT_PATH.parents[4]
ADAPTER_ROOT = SCRIPT_PATH.parent.parent
MANIFEST_PATH = ADAPTER_ROOT / "OPENCLAW_PLUGIN_PROFILE.manifest.json"


@dataclass
class CopyRecord:
    kind: str
    source: str
    target: str
    action: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the AITP OpenClaw plugin into a target workspace.")
    parser.add_argument("--target-root", required=True, help="Target OpenClaw workspace root.")
    parser.add_argument("--source-root", default=str(WORKSPACE_ROOT), help="Source workspace root. Defaults to this workspace.")
    parser.add_argument("--force", action="store_true", help="Overwrite differing files and reinstall the plugin if needed.")
    parser.add_argument("--copy-mcporter", action="store_true", help="Also copy config/mcporter.json into the target workspace.")
    parser.add_argument(
        "--skip-plugin-install",
        action="store_true",
        help="Seed/copy files only; do not copy the workspace-local plugin extension.",
    )
    parser.add_argument("--skip-seeds", action="store_true", help="Do not overwrite mutable seed/state files.")
    parser.add_argument(
        "--allow-self-seed",
        action="store_true",
        help="Allow seed overwrite even when source-root and target-root are the same workspace.",
    )
    parser.add_argument(
        "--openclaw-profile",
        help="Optional OpenClaw profile name to point at the target workspace and enable the plugin there.",
    )
    parser.add_argument("--json", action="store_true", help="Print a JSON summary.")
    return parser.parse_args()


def read_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def same_file(source: Path, target: Path) -> bool:
    if not target.exists() or source.stat().st_size != target.stat().st_size:
        return False
    return source.read_bytes() == target.read_bytes()


def copy_file(source: Path, target: Path, *, force: bool, records: list[CopyRecord], kind: str) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Missing source file: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if same_file(source, target):
            records.append(CopyRecord(kind=kind, source=str(source), target=str(target), action="unchanged"))
            return
        if not force:
            raise FileExistsError(f"Refusing to overwrite existing file without --force: {target}")
        action = "overwritten"
    else:
        action = "created"
    shutil.copy2(source, target)
    records.append(CopyRecord(kind=kind, source=str(source), target=str(target), action=action))


def copy_file_if_present(source: Path, target: Path, *, force: bool, records: list[CopyRecord], kind: str) -> None:
    if not source.exists():
        records.append(CopyRecord(kind=kind, source=str(source), target=str(target), action="missing-skipped"))
        return
    copy_file(source, target, force=force, records=records, kind=kind)


def is_excluded(relative_path: Path, patterns: list[str]) -> bool:
    rel = relative_path.as_posix()
    return any(fnmatch(rel, pattern) for pattern in patterns)


def copy_tree(
    source: Path,
    target: Path,
    *,
    exclude: list[str],
    force: bool,
    records: list[CopyRecord],
    kind: str,
) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Missing source directory: {source}")
    for path in sorted(source.rglob("*")):
        if path.is_dir():
            continue
        relative_path = path.relative_to(source)
        if is_excluded(relative_path, exclude):
            continue
        copy_file(path, target / relative_path, force=force, records=records, kind=kind)


def ensure_directories(target_root: Path, directories: list[str], records: list[CopyRecord]) -> None:
    for relative in directories:
        path = target_root / relative
        existed = path.exists()
        path.mkdir(parents=True, exist_ok=True)
        records.append(
            CopyRecord(
                kind="directory",
                source="-",
                target=str(path),
                action="unchanged" if existed else "created",
            )
        )


def install_plugin(
    target_root: Path,
    plugin_id: str,
    plugin_source: Path,
    *,
    force: bool,
    records: list[CopyRecord],
) -> dict[str, Any]:
    extension_root = target_root / ".openclaw" / "extensions" / plugin_id
    extension_root.mkdir(parents=True, exist_ok=True)
    copy_tree(
        plugin_source,
        extension_root,
        exclude=["node_modules/**", ".git/**", "**/__pycache__/**", "**/*.pyc"],
        force=force,
        records=records,
        kind="plugin_extension",
    )
    return {
        "plugin_id": plugin_id,
        "plugin_source": str(plugin_source),
        "extension_root": str(extension_root),
        "method": "workspace_copy",
    }


def run_openclaw(profile: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["openclaw", "--profile", profile, *args],
        check=False,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )


def configure_profile(profile: str, target_root: Path, plugin_id: str) -> dict[str, Any]:
    setup = run_openclaw(profile, ["setup", "--workspace", str(target_root)])
    enable = run_openclaw(profile, ["plugins", "enable", plugin_id])
    return {
        "profile": profile,
        "operations": [
            {
                "step": "setup_workspace",
                "argv": ["openclaw", "--profile", profile, "setup", "--workspace", str(target_root)],
                "exit_code": setup.returncode,
                "stdout": setup.stdout.strip(),
                "stderr": setup.stderr.strip(),
            },
            {
                "step": "enable_plugin",
                "argv": ["openclaw", "--profile", profile, "plugins", "enable", plugin_id],
                "exit_code": enable.returncode,
                "stdout": enable.stdout.strip(),
                "stderr": enable.stderr.strip(),
            },
        ],
    }


def resolve_seed_policy(args: argparse.Namespace, source_root: Path, target_root: Path) -> tuple[bool, str]:
    if args.skip_seeds:
        return False, "skip-seeds"
    if source_root == target_root and not args.allow_self_seed:
        return False, "self-install-guard"
    return True, "default"


def main() -> int:
    args = parse_args()
    source_root = Path(args.source_root).expanduser().resolve()
    target_root = Path(args.target_root).expanduser().resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    manifest = read_manifest(MANIFEST_PATH)
    records: list[CopyRecord] = []

    ensure_directories(target_root, manifest.get("ensure_directories", []), records)

    for rule in manifest.get("copy_files", []):
        copy_file_if_present(
            source_root / rule["source"],
            target_root / rule["target"],
            force=args.force,
            records=records,
            kind="copy_file",
        )

    for rule in manifest.get("copy_trees", []):
        copy_tree(
            source_root / rule["source"],
            target_root / rule["target"],
            exclude=list(rule.get("exclude", [])),
            force=args.force,
            records=records,
            kind="copy_tree",
        )

    apply_seeds, seed_reason = resolve_seed_policy(args, source_root, target_root)
    if apply_seeds:
        for rule in manifest.get("seed_files", []):
            copy_file_if_present(
                source_root / rule["source"],
                target_root / rule["target"],
                force=True,
                records=records,
                kind="seed_file",
            )

    for rule in manifest.get("optional_files", []):
        flag_name = str(rule.get("flag") or "")
        enabled = bool(getattr(args, flag_name.replace("-", "_"), False))
        if not enabled:
            continue
        copy_file_if_present(
            source_root / rule["source"],
            target_root / rule["target"],
            force=args.force,
            records=records,
            kind="optional_file",
        )

    plugin_result: dict[str, Any] | None = None
    if not args.skip_plugin_install:
        plugin_source = target_root / manifest["plugin"]["source_path"]
        plugin_result = install_plugin(
            target_root,
            str(manifest["plugin"]["id"]),
            plugin_source,
            force=args.force,
            records=records,
        )

    profile_result: dict[str, Any] | None = None
    if args.openclaw_profile:
        profile_result = configure_profile(
            args.openclaw_profile,
            target_root,
            str(manifest["plugin"]["id"]),
        )

    summary = {
        "source_root": str(source_root),
        "target_root": str(target_root),
        "manifest_path": str(MANIFEST_PATH),
        "profile_version": manifest.get("profile_version"),
        "copied": [record.__dict__ for record in records],
        "seed_policy": {
            "applied": apply_seeds,
            "reason": seed_reason,
            "self_install": source_root == target_root,
        },
        "plugin_install": plugin_result,
        "openclaw_profile": profile_result,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        copied_count = len([record for record in records if record.kind != "directory"])
        skipped_missing_count = len([record for record in records if record.action == "missing-skipped"])
        print(f"Installed OpenClaw AITP profile into {target_root}")
        print(f"- profile_version: {manifest.get('profile_version')}")
        print(f"- copied_entries: {copied_count}")
        print(f"- missing_optional_entries: {skipped_missing_count}")
        print(f"- seeds_applied: {'yes' if apply_seeds else 'no'} ({seed_reason})")
        if plugin_result:
            print(f"- plugin_id: {plugin_result['plugin_id']}")
            print(f"- plugin_source: {plugin_result['plugin_source']}")
            print(f"- extension_root: {plugin_result['extension_root']}")
        if profile_result:
            print(f"- openclaw_profile: {profile_result['profile']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
