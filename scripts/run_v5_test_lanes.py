"""Run AITP v5 release lanes without reviving legacy write workflows."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path


ARCHIVED_LEGACY_WRITE_TESTS = (
    "tests/test_legacy_write_guard.py::test_legacy_write_helpers_allow_escape_hatch",
    "tests/test_cli_path_and_source_friction.py",
    "tests/test_e2e_scenario_a.py",
    "tests/test_e2e_study_l2.py",
    "tests/test_foundation_safety.py",
    "tests/test_io_contracts.py",
    "tests/test_knowledge_base_ops.py",
    "tests/test_l3_subplanes.py",
    "tests/test_l4_l2_memory.py",
    "tests/test_legacy_cli_live_gate.py",
    "tests/test_state_model.py",
    "tests/test_study_l2_graph.py",
    "tests/test_visualization.py",
)


LEGACY_WRITE_GUARD_TESTS = (
    "tests/test_legacy_write_guard.py::test_legacy_write_helpers_block_by_default",
    "tests/test_legacy_write_guard.py::test_native_mcp_rejects_legacy_write_call_by_default",
    "tests/test_legacy_write_guard.py::test_legacy_read_only_tools_still_work",
    "tests/test_legacy_write_guard.py::test_bridge_query_is_blocked_as_a_write_tool",
)


LEGACY_COMPAT_TESTS = (
    *LEGACY_WRITE_GUARD_TESTS,
    "tests/test_flow_notebook",
    "tests/test_v5_curated_legacy_migration.py",
    "tests/test_v5_legacy_bridge.py",
    "tests/test_v5_legacy_l2_graph.py",
    "tests/test_v5_legacy_l2_obsidian_view.py",
    "tests/test_v5_legacy_l2_seed_audit.py",
    "tests/test_v5_legacy_migration_accounting.py",
    "tests/test_v5_legacy_record_materialization.py",
    "tests/test_v5_legacy_source_reconstruction.py",
    "tests/test_v5_workspace_file_migration_ledger.py",
    "tests/test_v5_workspace_migration_plan.py",
    "tests/test_v5_workspace_old_store_import.py",
    "tests/test_v5_workspace_old_store_manifest.py",
)


M0_TEST_LANES = {
    "foundation": (
        "tests/test_v5_architecture_boundaries.py",
        "tests/test_v5_m0_release.py",
        "tests/test_v5_test_lanes.py",
        "tests/test_v5_runtime_audit.py",
        "tests/test_v5_store_read_policy.py",
        "tests/test_v5_legacy_record_materialization.py",
        "tests/test_v5_kernel.py",
        "tests/test_v5_record_family_registry.py",
        "tests/test_v5_record_envelope.py",
        "tests/test_v5_record_envelope_audit.py",
        "tests/test_v5_record_repository.py",
        "tests/test_v5_reference_locations.py",
        "tests/test_v5_query_index.py",
        "tests/test_v5_research_retrieval.py",
        "tests/test_v5_context_compiler.py",
        "tests/test_v5_context_performance.py",
        "tests/test_v5_context_injection_budget.py",
        "tests/test_v5_capability_registry.py",
    ),
    "compatibility": (
        "tests/test_v5_cli.py",
        "tests/test_v5_workspace_inventory.py",
        "tests/test_v5_context_pack.py",
        "tests/test_v5_claim_relation_map.py",
        "tests/test_v5_research_timeline.py",
        "tests/test_v5_codex_facade.py",
        "tests/test_v5_public_surfaces.py",
        "tests/test_v5_runtime_entrypoints.py",
        "tests/test_v5_bridge_runtime.py",
        "tests/test_v5_runtime_mcp_bridge_acceptance.py",
        "tests/test_v5_topic_status.py",
        "tests/test_v5_workspace_refresh.py",
        "tests/test_v5_lightweight_record_router.py",
        "tests/test_aitp_pm_deploy_surfaces.py",
    ),
    "slow-adapter": (
        "tests/test_v5_adapters.py",
    ),
    "legacy-compat": LEGACY_COMPAT_TESTS,
}


def _discover_v5_vertical_tests() -> tuple[str, ...]:
    """Find blocking v5 tests not already owned by a focused lane."""

    repo_root = Path(__file__).resolve().parents[1]
    covered = {
        path.partition("::")[0].replace("\\", "/")
        for lane in M0_TEST_LANES.values()
        for path in lane
    }
    selected = {
        path.relative_to(repo_root).as_posix()
        for path in (repo_root / "tests").glob("test_v5_*.py")
    }
    return tuple(sorted(selected - covered))


M0_TEST_LANES["v5-verticals"] = _discover_v5_vertical_tests()

ARCHIVE_TEST_LANES = {
    "legacy-write-archive": ARCHIVED_LEGACY_WRITE_TESTS,
}

ISOLATION_CLEARED_ENVIRONMENT = (
    "AITP_TOPICS_ROOT",
    "AITP_WORKSPACE_ROOT",
    "AITP_OLD_TOPICS_ROOT",
    "AITP_RESEARCH_ROOT",
    "AITP_LEGACY_ENABLE_WRITES",
    "AITP_INSTALL_LEGACY_STAGE_SKILLS",
    "AITP_INSTALL_LEGACY_STAGE_HOOKS",
    "AITP_V5_EXPOSE_COMPAT_ALIASES",
    "AITP_MCP_SURFACE",
    "AITP_HOOKS",
    "AITP_HOOK_PYTHON",
    "AITP_SESSION_ID",
)


def _discover_blocking_full_tests() -> tuple[str, ...]:
    repo_root = Path(__file__).resolve().parents[1]
    tests_root = repo_root / "tests"
    selected = {
        path.relative_to(repo_root).as_posix()
        for path in tests_root.glob("test_v5_*.py")
    }
    selected.update(
        {
            "tests/test_aitp_pm_deploy_surfaces.py",
            "tests/test_flow_notebook",
            *LEGACY_WRITE_GUARD_TESTS,
        }
    )
    return tuple(sorted(selected))


BLOCKING_FULL_TESTS = _discover_blocking_full_tests()

SCHEDULED_FULL_SUITE_COMMAND = "python scripts/run_v5_test_lanes.py full"


def build_pytest_command(
    lane: str,
    *,
    basetemp: str = "",
    collect_only: bool = False,
    maxfail: int = 0,
) -> list[str]:
    known_lanes = {*M0_TEST_LANES, *ARCHIVE_TEST_LANES, "full"}
    if lane not in known_lanes:
        raise ValueError(f"unknown v5 test lane: {lane}")
    command = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider"]
    if collect_only:
        command.append("--collect-only")
    if maxfail > 0:
        command.append(f"--maxfail={maxfail}")
    if basetemp:
        command.extend(("--basetemp", basetemp))
    if lane == "full":
        command.extend(BLOCKING_FULL_TESTS)
    else:
        command.extend({**M0_TEST_LANES, **ARCHIVE_TEST_LANES}[lane])
    return command


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "lane",
        choices=(*M0_TEST_LANES, *ARCHIVE_TEST_LANES, "full"),
    )
    parser.add_argument("--basetemp", default="")
    parser.add_argument("--collect-only", action="store_true")
    parser.add_argument("--maxfail", type=int, default=0)
    args = parser.parse_args(argv)
    basetemp = args.basetemp or str(
        Path(tempfile.gettempdir()) / f"aitp-pytest-{uuid.uuid4().hex}"
    )

    return _run_lane(
        args.lane,
        basetemp=basetemp,
        collect_only=args.collect_only,
        maxfail=args.maxfail,
    )


def _run_lane(
    lane: str,
    *,
    basetemp: str = "",
    collect_only: bool = False,
    maxfail: int = 0,
) -> int:
    return subprocess.call(
        build_pytest_command(
            lane,
            basetemp=basetemp,
            collect_only=collect_only,
            maxfail=maxfail,
        ),
        env=_test_environment(lane, basetemp=basetemp),
    )


def _test_environment(lane: str, *, basetemp: str) -> dict[str, str]:
    env = os.environ.copy()
    for name in ISOLATION_CLEARED_ENVIRONMENT:
        env.pop(name, None)
    isolated_home = Path(basetemp) / "isolated-home"
    env.update(
        {
            "HOME": str(isolated_home),
            "USERPROFILE": str(isolated_home),
            "XDG_CONFIG_HOME": str(isolated_home / ".config"),
            "CODEX_HOME": str(isolated_home / ".codex"),
            "CLAUDE_CONFIG_DIR": str(isolated_home / ".claude"),
        }
    )
    # V5 tests pass explicit workspace bases. A global topics root would
    # override those bases after the first MCP call creates it, causing
    # cross-test state leakage. Only the archived legacy diagnostic needs one.
    if lane in ARCHIVE_TEST_LANES:
        env["AITP_TOPICS_ROOT"] = str(Path(basetemp) / "isolated-topics-root")
        env["AITP_LEGACY_ENABLE_WRITES"] = "1"
    return env


if __name__ == "__main__":
    raise SystemExit(main())
