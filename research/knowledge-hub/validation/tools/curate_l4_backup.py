#!/usr/bin/env python3
"""Curate an AITP L4 validation run directory into a compact backup bundle.

Follows L4_TEST_DATA_BACKUP_PROTOCOL.md.  The goal is NOT "keep all small files"
— it is "keep files that carry reproducible or interpretive value."

Usage:
  python curate_l4_backup.py <run_dir> <backup_dir> [--dry-run] [--lane LANE]

  --dry-run   Report what would happen without making changes.
  --lane LANE  One of: formal_theory, toy_numeric, code_method (auto-detected
               from state.md if omitted).

Example:
  python curate_l4_backup.py \\
    topics/qho-benchmark/runs/run-2026-04-20-a \\
    backups/l4/qho-benchmark/run-2026-04-20-a
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# File classification rules
# ---------------------------------------------------------------------------

# Class 1: Test definition — always keep
CLASS1_PATTERNS = [
    "validation_plan.md",
    "validation_contract.md",
    "promotion_decisions.jsonl",
]

# Class 2: Key inputs — keep when present
CLASS2_PATTERNS = [
    "INPUT", "STRU", "KPT",
    "librpa.in",
    "run_*.sh",
    "band_kpath_info",
    "convention_snapshot.md",
    "*.upf", "*.orb", "*.abfs",
    "*_statement.lean", "*_proof.lean",
    "*_verify.py",
    "known_result_reference.json",
]

# Class 3: Final outputs — keep meaningful results
CLASS3_PATTERNS = [
    "GW_band_spin_*.dat",
    "KS_band_spin_*.dat",
    "EXX_band_spin_*.dat",
    "band_gap_data.csv",
    "convergence_check.csv",
    "benchmark_comparison.csv",
    "proof_check_result.json",
    "verification_evidence.json",
    "dimension_check_result.json",
    "algebra_verify_result.json",
    "limit_check_result.json",
]

# Class 4: Key logs — keep main stage only
CLASS4_PATTERNS = [
    "abacus*.out",
    "LibRPA*.out",
    "slurm*.out",
    "validation.log",
]

# Always delete
ALWAYS_DELETE_FILES = [
    ".DS_Store", "._*", "__pycache__",
    "running.log", "running_scf.log", "running_nscf.log",
    "warning.log", "INFO.txt",
    "LibRPA.done", "SYNC_FROM_PARALLEL",
    "jobid.txt", "*jobid*.txt",
    "*.bak", "*.tmp",
]

# Always delete directories
ALWAYS_DELETE_DIRS = [
    "*_parallel", "Out", "OUT.ABACUS", "pyatb_librpa_df",
]

# Numeric shards — delete unless referenced by kept table
NUMERIC_SHARD_PATTERNS = [
    "band_KS_eigenvalue_k_*",
    "band_KS_eigenvector_k_*",
    "band_vxc_k_*",
    "KS_eigenvector_*",
    "librpa_para_nprocs_*",
    "local_*_freq_points.dat",
    "local_*_time_points.dat",
    "*_freq2time_grid_*.txt",
    "*_time2freq_grid_*.txt",
]

# Figure-related
FIGURE_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".svg", ".eps"}
PLOT_SCRIPT_EXTS = {".py", ".sh", ".jl", ".R"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _matches_any(name: str, patterns: list[str]) -> bool:
    """Check if name matches any fnmatch pattern."""
    for pat in patterns:
        # fnmatch is too permissive for paths; do simple matching
        if pat.startswith("*") and pat.endswith("*"):
            if pat[1:-1] in name:
                return True
        elif pat.startswith("*") and name.endswith(pat[1:]):
            return True
        elif pat.endswith("*") and name.startswith(pat[:-1]):
            return True
        elif pat == name:
            return True
    return False


def _glob_match(name: str, pattern: str) -> bool:
    """Simple glob matching for file classification."""
    import fnmatch
    return fnmatch.fnmatch(name, pattern)


def classify_file(filepath: Path, run_dir: Path) -> str | None:
    """Classify a file into class1-4, 'figure', 'plot_script', 'delete', or None."""
    rel = str(filepath.relative_to(run_dir))
    name = filepath.name

    # Check always-delete first
    for pat in ALWAYS_DELETE_FILES:
        if _glob_match(name, pat):
            return "delete"

    # Check numeric shards
    for pat in NUMERIC_SHARD_PATTERNS:
        if _glob_match(name, pat):
            return "delete"

    # Class 1: test definition
    for pat in CLASS1_PATTERNS:
        if _glob_match(name, pat) or _glob_match(rel, pat):
            return "class1"

    # Class 2: key inputs
    for pat in CLASS2_PATTERNS:
        if _glob_match(name, pat):
            return "class2"

    # Class 3: final outputs
    for pat in CLASS3_PATTERNS:
        if _glob_match(name, pat):
            return "class3"

    # Class 4: key logs
    for pat in CLASS4_PATTERNS:
        if _glob_match(name, pat):
            return "class4"

    # Figures
    if filepath.suffix.lower() in FIGURE_EXTS:
        return "figure"

    # Plot scripts (heuristic: .py/.sh in a figures/ or scripts/ dir)
    if filepath.suffix.lower() in PLOT_SCRIPT_EXTS:
        if "plot" in name.lower() or "figure" in name.lower() or "fig" in name.lower():
            return "plot_script"

    # execution-tasks JSON files
    if "execution-tasks" in rel and filepath.suffix == ".json":
        return "class1"

    return None  # unclassified — will be treated as delete


def _dir_should_delete(dirpath: Path, run_dir: Path) -> bool:
    """Check if a directory matches always-delete patterns."""
    name = dirpath.name
    for pat in ALWAYS_DELETE_DIRS:
        if _glob_match(name, pat):
            return True
    return False


def _parse_md(path: Path) -> tuple[dict, str]:
    """Parse YAML frontmatter + Markdown body."""
    import yaml
    text = path.read_text(encoding="utf-8")
    fm = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                pass
            body = parts[2]
    return fm, body


def detect_lane(run_dir: Path) -> str:
    """Try to detect lane from state.md or validation_contract.md."""
    # Try state.md in parent topic directory
    state_path = run_dir.parent.parent / "state.md"
    if state_path.exists():
        fm, _ = _parse_md(state_path)
        lane = fm.get("lane", "")
        if lane:
            return lane

    # Try validation_contract.md in run directory
    vc_path = run_dir / "validation_contract.md"
    if vc_path.exists():
        fm, _ = _parse_md(vc_path)
        lane = fm.get("lane", "")
        if lane:
            return lane

    return "formal_theory"  # default


def curate_run(run_dir: str, backup_dir: str, lane: str = "",
               dry_run: bool = False) -> dict:
    """Curate a single L4 run directory. Returns a summary dict."""

    src = Path(run_dir).resolve()
    dst = Path(backup_dir).resolve()

    if not src.exists():
        print(f"ERROR: Run directory not found: {src}", file=sys.stderr)
        sys.exit(1)

    if not lane:
        lane = detect_lane(src)

    print(f"L4 Backup Curation")
    print(f"  Source: {src}")
    print(f"  Destination: {dst}")
    print(f"  Lane: {lane}")
    print(f"  Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    # Scan all files
    kept: dict[str, list[str]] = {
        "class1": [], "class2": [], "class3": [], "class4": [],
        "figure": [], "plot_script": [],
    }
    removed: dict[str, list[str]] = {}
    total_files = 0
    total_size_before = 0

    for dirpath_str, dirnames, filenames in os.walk(str(src)):
        dirpath = Path(dirpath_str)

        # Check if this directory should be deleted entirely
        rel_dir = str(dirpath.relative_to(src))
        if rel_dir != "." and _dir_should_delete(dirpath, src):
            dir_size = sum(
                (dirpath / f).stat().st_size
                for f in filenames
                if (dirpath / f).is_file()
            )
            class_name = f"dir:{dirpath.name}"
            removed.setdefault(class_name, []).append(f"{rel_dir}/ ({dir_size} bytes)")
            total_files += len(filenames)
            total_size_before += dir_size
            dirnames.clear()  # don't recurse
            continue

        for fname in filenames:
            fpath = dirpath / fname
            if not fpath.is_file():
                continue
            fsize = fpath.stat().st_size
            total_files += 1
            total_size_before += fsize

            klass = classify_file(fpath, src)
            rel_path = str(fpath.relative_to(src))

            if klass and klass != "delete":
                kept.setdefault(klass, []).append(rel_path)
                if not dry_run:
                    dest_path = dst / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(fpath, dest_path)
            else:
                removed.setdefault(klass or "unclassified", []).append(rel_path)

    # Copy execution-tasks directory if present
    exec_tasks = src / "execution-tasks"
    if exec_tasks.is_dir():
        for fpath in exec_tasks.glob("*.json"):
            rel_path = str(fpath.relative_to(src))
            kept.setdefault("class1", []).append(rel_path)
            if not dry_run:
                dest_path = dst / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(fpath, dest_path)

    # Generate manifest
    manifest = {
        "backup_version": "1.0",
        "backup_date": _now(),
        "source_dir": str(src),
        "lane": lane,
        "l4_outcome": _detect_outcome(src),
        "contents": {
            "test_definition": kept.get("class1", []),
            "key_inputs": kept.get("class2", []),
            "final_outputs": kept.get("class3", []),
            "key_logs": kept.get("class4", []),
            "figures": kept.get("figure", []),
            "plot_scripts": kept.get("plot_script", []),
        },
        "removed_classes": list(removed.keys()),
        "original_file_count": total_files,
        "kept_file_count": sum(len(v) for v in kept.values()),
        "original_size_bytes": total_size_before,
    }

    if not dry_run:
        dst.mkdir(parents=True, exist_ok=True)
        manifest_path = dst / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Write README
        readme_path = dst / "README.md"
        readme_path.write_text(
            f"# L4 Backup: {src.name}\n\n"
            f"- **Topic:** {src.parent.parent.name}\n"
            f"- **Run:** {src.name}\n"
            f"- **Lane:** {lane}\n"
            f"- **Date:** {manifest['backup_date']}\n"
            f"- **Outcome:** {manifest['l4_outcome']}\n"
            f"- **Files kept:** {manifest['kept_file_count']} / {manifest['original_file_count']}\n"
            f"- **Size:** {total_size_before / 1e6:.1f} MB (original)\n"
            f"\nSee `manifest.json` for full inventory.\n",
            encoding="utf-8",
        )

    # Report
    report = _format_report(manifest, kept, removed)
    print(report)

    return manifest


def _detect_outcome(run_dir: Path) -> str:
    """Try to detect L4 outcome from promotion_decisions.jsonl or state.md."""
    pd_path = run_dir / "promotion_decisions.jsonl"
    if pd_path.exists():
        lines = pd_path.read_text(encoding="utf-8").strip().splitlines()
        if lines:
            try:
                last = json.loads(lines[-1])
                return last.get("verdict", "unknown")
            except json.JSONDecodeError:
                pass

    state_path = run_dir.parent.parent / "state.md"
    if state_path.exists():
        fm, _ = _parse_md(state_path)
        return fm.get("l4_outcome", "unknown")

    # Check reviews
    reviews_dir = run_dir.parent.parent / "L4" / "reviews"
    if reviews_dir.is_dir():
        for review in sorted(reviews_dir.glob("*.md"), reverse=True):
            fm, _ = _parse_md(review)
            outcome = fm.get("outcome", "")
            if outcome and "_v" not in review.stem:
                return outcome
            if outcome:
                return outcome

    return "unknown"


def _format_report(manifest: dict, kept: dict, removed: dict) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("L4 Backup Summary")
    lines.append("=" * 60)
    lines.append(f"  Outcome:     {manifest['l4_outcome']}")
    lines.append(f"  Lane:        {manifest['lane']}")
    lines.append(f"  Files kept:  {manifest['kept_file_count']} / {manifest['original_file_count']}")
    lines.append(f"  Original:    {manifest['original_size_bytes'] / 1e6:.1f} MB")
    lines.append("")

    for klass, label in [
        ("class1", "Test definition"),
        ("class2", "Key inputs"),
        ("class3", "Final outputs"),
        ("class4", "Key logs"),
        ("figure", "Figures"),
        ("plot_script", "Plot scripts"),
    ]:
        items = kept.get(klass, [])
        lines.append(f"  {label}: {len(items)} files")
        if items and len(items) <= 10:
            for item in items:
                lines.append(f"    - {item}")

    lines.append("")
    lines.append("  Removed:")
    for klass, items in sorted(removed.items()):
        lines.append(f"    {klass}: {len(items)} files")
    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Curate an AITP L4 validation run directory into a compact backup."
    )
    parser.add_argument("run_dir", help="Path to the L4 run directory")
    parser.add_argument("backup_dir", help="Destination for the curated backup")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would happen without copying files")
    parser.add_argument("--lane", default="",
                        help="Lane: formal_theory, toy_numeric, code_method")
    args = parser.parse_args()

    curate_run(args.run_dir, args.backup_dir, lane=args.lane, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
