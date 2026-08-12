"""Benchmark for the M0.5 slim core (plain script, not collected by pytest).

Builds two fixture stores in a temp directory via the in-process API
(20 valid Entries and 1,000 valid Entries; deterministic content, unique IDs;
construction is not timed), then measures real subprocess startup and runtime
for the CLI entry points:

- ``python -m aitp --help`` and ``python -I <plugin runner> --help``;
- ``enter --json`` on both fixture sizes; report-only ``list --json`` on the 1,000-entry fixture for both runners.

The module runner's subprocess env carries the vendor directory on
``PYTHONPATH``, same as ``test_cli.py``.  One warmup plus five timed runs are
recorded per measurement (median/min/max in ms).  A single JSON object is
printed with the interpreter, platform, machine, fixture sizes, every
measurement, and PASS/FAIL against the thresholds (``--help`` < 250 ms;
1,000-Entry ``enter`` < 1 s).

Usage:
    uv run --python 3.12 python tests/ledger/benchmark.py
"""

from __future__ import annotations

import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
PLUGIN = REPOSITORY / "plugins" / "aitp-research-protocol"
VENDOR = PLUGIN / "scripts" / "vendor"
RUNNER = PLUGIN / "scripts" / "aitp.py"

sys.path.insert(0, str(VENDOR))

from aitp.core import (  # noqa: E402
    atomic_write,
    enter_workspace,
    init_workspace,
    parse_markdown,
    prepare_entry,
    render_markdown,
)

HELP_THRESHOLD_MS = 250.0
ENTER_1000_THRESHOLD_MS = 1000.0
WARMUP_RUNS = 1
TIMED_RUNS = 5


def build_store(root: Path, count: int) -> Path:
    """Build a store with `count` valid, deterministic decision Entries.

    Entries are prepared through the public API, then written directly into
    the canonical entries directory.  (save_entry re-scans and re-parses the
    whole canonical set for every save — O(n^2) — so constructing 1,000
    entries through it would take tens of minutes; construction is not timed,
    and the written entries are byte-identical to save_entry's output.)
    """
    root.mkdir(parents=True)
    init_workspace(root, "bench", "Benchmark topic")
    body = """\
## Durable Summary

Benchmark decision {n}.

## Decision And Alternatives

Recorded for the timing fixture.

## Reason, Scope, And Revisit Condition

None.
"""
    entries_dir = root / ".aitp" / "topic" / "entries"
    for n in range(count):
        prepared = prepare_entry(root, "decision", "agent", created_by="tool:benchmark")
        path = root / prepared["path"]
        frontmatter, _, _ = parse_markdown(path)
        frontmatter["summary"] = f"Benchmark decision {n}."
        atomic_write(
            entries_dir / f"{frontmatter['id']}.md",
            render_markdown(frontmatter, body.format(n=n)),
        )
    # one whole-store validation pass through the public API (O(n))
    state = enter_workspace(root)
    assert state["memory_status"] == "available", state["warnings"]
    assert state["counts"]["active"] == count, state["counts"]
    return root


def measure(command: list[str], cwd: Path, env: dict[str, str]) -> dict[str, float]:
    for _ in range(WARMUP_RUNS):
        subprocess.run(
            command, cwd=cwd, env=env, capture_output=True, text=True, timeout=300
        )
    samples: list[float] = []
    for _ in range(TIMED_RUNS):
        start = time.perf_counter()
        proc = subprocess.run(
            command, cwd=cwd, env=env, capture_output=True, text=True, timeout=300
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        if proc.returncode != 0:
            raise SystemExit(
                f"benchmark command failed: {' '.join(command)}\n{proc.stderr}"
            )
        samples.append(elapsed_ms)
    return {
        "median_ms": round(statistics.median(samples), 3),
        "min_ms": round(min(samples), 3),
        "max_ms": round(max(samples), 3),
    }


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="aitp-bench-"))
    try:
        store_20 = build_store(work / "store-20", 20)
        store_1000 = build_store(work / "store-1000", 1000)

        env_module = os.environ.copy()
        env_module["PYTHONPATH"] = str(VENDOR)
        env_plugin = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}

        measurements = {
            "module_help": measure(
                [sys.executable, "-m", "aitp", "--help"], work, env_module
            ),
            "plugin_help": measure(
                [sys.executable, "-I", str(RUNNER), "--help"], work, env_plugin
            ),
            "module_enter_20": measure(
                [sys.executable, "-m", "aitp", "enter", "--json"], store_20, env_module
            ),
            "module_enter_1000": measure(
                [sys.executable, "-m", "aitp", "enter", "--json"],
                store_1000,
                env_module,
            ),
            "plugin_enter_20": measure(
                [sys.executable, "-I", str(RUNNER), "enter", "--json"],
                store_20,
                env_plugin,
            ),
            "plugin_enter_1000": measure(
                [sys.executable, "-I", str(RUNNER), "enter", "--json"],
                store_1000,
                env_plugin,
            ),
            "module_list_1000": measure(
                [sys.executable, "-m", "aitp", "list", "--json"],
                store_1000,
                env_module,
            ),
            "plugin_list_1000": measure(
                [sys.executable, "-I", str(RUNNER), "list", "--json"],
                store_1000,
                env_plugin,
            ),
        }

        passed = (
            measurements["module_help"]["median_ms"] < HELP_THRESHOLD_MS
            and measurements["plugin_help"]["median_ms"] < HELP_THRESHOLD_MS
            and measurements["module_enter_1000"]["median_ms"] < ENTER_1000_THRESHOLD_MS
            and measurements["plugin_enter_1000"]["median_ms"] < ENTER_1000_THRESHOLD_MS
        )
        report = {
            "result": "PASS" if passed else "FAIL",
            "python_version": sys.version.split()[0],
            "platform": sys.platform,
            "machine": platform.machine(),
            "fixtures": {"small_entries": 20, "large_entries": 1000},
            "measurements": measurements,
            "thresholds": {
                "help_ms": HELP_THRESHOLD_MS,
                "enter_1000_ms": ENTER_1000_THRESHOLD_MS,
            },
            "pass": passed,
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if passed else 1
    finally:
        import shutil

        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
