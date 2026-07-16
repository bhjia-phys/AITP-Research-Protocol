from __future__ import annotations

import os
import re
from pathlib import Path
from unittest.mock import patch

from scripts import run_v5_test_lanes as test_lanes
from scripts.run_v5_test_lanes import (
    ARCHIVE_TEST_LANES,
    ARCHIVED_LEGACY_WRITE_TESTS,
    BLOCKING_FULL_TESTS,
    LEGACY_WRITE_GUARD_TESTS,
    M0_TEST_LANES,
    SCHEDULED_FULL_SUITE_COMMAND,
    build_pytest_command,
)


def test_m0_test_lanes_reference_existing_tests_and_required_boundaries():
    repo_root = Path(__file__).resolve().parents[1]
    required = {
        "tests/test_v5_architecture_boundaries.py",
        "tests/test_v5_runtime_audit.py",
        "tests/test_v5_record_repository.py",
        "tests/test_v5_query_index.py",
        "tests/test_v5_context_compiler.py",
        "tests/test_v5_capability_registry.py",
        "tests/test_v5_gate1_lifecycle_e2e.py",
        "tests/test_v5_test_lanes.py",
        "tests/test_v5_runtime_mcp_bridge_acceptance.py",
        "tests/test_aitp_pm_deploy_surfaces.py",
        *LEGACY_WRITE_GUARD_TESTS,
        "tests/test_v5_adapters.py",
    }
    declared = {
        test_path
        for lane in M0_TEST_LANES.values()
        for test_path in lane
    }

    assert required <= declared
    assert all(
        (repo_root / test_path.partition("::")[0]).exists()
        for test_path in declared
    )
    assert set(M0_TEST_LANES) == {
        "foundation",
        "compatibility",
        "v5-verticals",
        "slow-adapter",
        "legacy-compat",
    }
    covered_v5_files = {
        path.partition("::")[0]
        for lane in M0_TEST_LANES.values()
        for path in lane
        if path.partition("::")[0].startswith("tests/test_v5_")
    }
    assert covered_v5_files == {
        path.relative_to(repo_root).as_posix()
        for path in (repo_root / "tests").glob("test_v5_*.py")
    }
    assert set(ARCHIVE_TEST_LANES) == {"legacy-write-archive"}


def test_full_run_excludes_archive_and_isolates_host_home_without_hiding_packages(
    tmp_path,
    monkeypatch,
):
    calls = []
    monkeypatch.setenv("AITP_LEGACY_ENABLE_WRITES", "1")
    monkeypatch.setenv("AITP_TOPICS_ROOT", r"F:\real-canonical-topics")
    monkeypatch.setenv("AITP_WORKSPACE_ROOT", r"F:\real-workspace")
    monkeypatch.setenv("AITP_V5_EXPOSE_COMPAT_ALIASES", "1")
    monkeypatch.setenv("AITP_MCP_SURFACE", "codex")
    monkeypatch.setenv("APPDATA", r"C:\python-user-appdata")
    monkeypatch.setenv("LOCALAPPDATA", r"C:\python-runtime-localappdata")

    def fake_call(command, *, env):
        calls.append((command, env))
        return 0

    monkeypatch.setattr(test_lanes.subprocess, "call", fake_call)

    base = tmp_path / "suite"
    assert test_lanes.main(["full", "--basetemp", str(base)]) == 0
    assert len(calls) == 1

    command, env = calls[0]
    assert "AITP_LEGACY_ENABLE_WRITES" not in env
    assert "AITP_TOPICS_ROOT" not in env
    assert "AITP_WORKSPACE_ROOT" not in env
    assert "AITP_V5_EXPOSE_COMPAT_ALIASES" not in env
    assert "AITP_MCP_SURFACE" not in env
    isolated_home = base / "isolated-home"
    assert env["HOME"] == str(isolated_home)
    assert env["USERPROFILE"] == str(isolated_home)
    assert env["APPDATA"] == r"C:\python-user-appdata"
    assert env["LOCALAPPDATA"] == r"C:\python-runtime-localappdata"
    assert env["XDG_CONFIG_HOME"] == str(isolated_home / ".config")
    assert env["CODEX_HOME"] == str(isolated_home / ".codex")
    assert env["CLAUDE_CONFIG_DIR"] == str(isolated_home / ".claude")
    assert command[-len(BLOCKING_FULL_TESTS) :] == list(BLOCKING_FULL_TESTS)
    assert not set(ARCHIVED_LEGACY_WRITE_TESTS) & set(BLOCKING_FULL_TESTS)
    assert str(base) in command


def test_legacy_write_archive_requires_an_explicit_nonrelease_lane(
    tmp_path,
    monkeypatch,
):
    calls = []

    def fake_call(command, *, env):
        calls.append((command, env))
        return 0

    monkeypatch.setattr(test_lanes.subprocess, "call", fake_call)

    base = tmp_path / "archive"
    assert test_lanes.main(
        ["legacy-write-archive", "--basetemp", str(base)]
    ) == 0
    assert len(calls) == 1
    command, env = calls[0]
    assert env["AITP_LEGACY_ENABLE_WRITES"] == "1"
    assert env["AITP_TOPICS_ROOT"] == str(base / "isolated-topics-root")
    assert command[-len(ARCHIVED_LEGACY_WRITE_TESTS) :] == list(
        ARCHIVED_LEGACY_WRITE_TESTS
    )


def test_full_suite_command_is_explicitly_scheduled_and_uncapped():
    assert SCHEDULED_FULL_SUITE_COMMAND == (
        "python scripts/run_v5_test_lanes.py full"
    )

    repo_root = Path(__file__).resolve().parents[1]
    workflow = (repo_root / ".github" / "workflows" / "v5-test-lanes.yml").read_text(
        encoding="utf-8"
    )
    assert "schedule:" in workflow
    assert "run_v5_test_lanes.py full" in workflow
    assert "run_v5_test_lanes.py ${{ matrix.lane }}" in workflow
    assert "legacy-compat" in workflow
    assert "v5-verticals" in workflow
    assert "slow-adapter" in workflow
    assert "actions/checkout@v6" in workflow
    assert "actions/setup-python@v5" in workflow


def test_full_lane_collects_only_v5_and_read_migration_compatibility_tests():
    command = build_pytest_command("full")
    escape_hatch_test = (
        "tests/test_legacy_write_guard.py::"
        "test_legacy_write_helpers_allow_escape_hatch"
    )

    assert command[-len(BLOCKING_FULL_TESTS) :] == list(BLOCKING_FULL_TESTS)
    assert escape_hatch_test in ARCHIVED_LEGACY_WRITE_TESTS
    assert escape_hatch_test not in BLOCKING_FULL_TESTS
    assert "tests/test_legacy_write_guard.py" not in BLOCKING_FULL_TESTS
    assert set(LEGACY_WRITE_GUARD_TESTS) <= set(BLOCKING_FULL_TESTS)
    assert "tests/test_flow_notebook" in BLOCKING_FULL_TESTS
    assert all(
        path.partition("::")[0].startswith("tests/test_v5_")
        or path.partition("::")[0]
        in {
            "tests/test_aitp_pm_deploy_surfaces.py",
            "tests/test_legacy_write_guard.py",
            "tests/test_flow_notebook",
        }
        for path in BLOCKING_FULL_TESTS
    )
    assert not any("tmp" in argument for argument in command)


def test_blocking_environment_preserves_an_explicit_v5_workspace_base():
    from brain.v5.mcp_base_resolution import resolve_workspace_base

    basetemp = Path.cwd() / "__aitp_isolated_test_suite__"
    explicit = Path.cwd() / "__aitp_explicit_test_workspace__"
    env = test_lanes._test_environment("full", basetemp=str(basetemp))

    with patch.dict(os.environ, env, clear=True):
        assert resolve_workspace_base(str(explicit)) == explicit


def test_release_docs_keep_v5_runtime_and_legacy_archive_boundaries():
    repo_root = Path(__file__).resolve().parents[1]
    project_memory = (repo_root / "PROJECT_MEMORY.md").read_text(encoding="utf-8")
    architecture = (
        repo_root
        / "docs"
        / "superpowers"
        / "specs"
        / "2026-07-10-aitp-final-research-operating-memory-design.md"
    ).read_text(encoding="utf-8")
    roadmap = (
        repo_root
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-07-09-aitp-final-research-lifecycle-roadmap.md"
    ).read_text(encoding="utf-8")
    m1_plan = (
        repo_root
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-07-10-aitp-gate-1-lifecycle-context.md"
    ).read_text(encoding="utf-8")
    workflow = (
        repo_root / ".github" / "workflows" / "v5-test-lanes.yml"
    ).read_text(encoding="utf-8")

    assert "brain/v5/native_mcp.py" in project_memory
    assert "Do not extend its candidate/stage/promotion write workflow" in project_memory
    assert "preserve each\n  explicit test base" in project_memory
    assert "Main MCP server" not in project_memory
    assert "### 4.6 V5 Is The Production Runtime" in architecture
    assert "archived behavior, not" in architecture
    for level in (
        "route_hint",
        "startup_orientation",
        "normal_research",
        "exact_expansion",
    ):
        assert level in architecture
        assert level in m1_plan
    assert "legacy-write-archive" in roadmap
    assert "never invoked by" in roadmap
    assert "Do not set one global v5 topics root" in roadmap
    assert "legacy-write-archive" not in workflow

    for relative_path in (
        "brain/v5/cli_context.py",
        "brain/v5/cli_query.py",
        "brain/v5/mcp_capabilities.py",
    ):
        implementation = (repo_root / relative_path).read_text(encoding="utf-8")
        assert "Gate 0" not in implementation
        assert "M0" in implementation


def test_active_m0_progress_docs_do_not_revive_gate_numbering():
    repo_root = Path(__file__).resolve().parents[1]
    progress_root = repo_root / "docs" / "superpowers" / "progress"
    active_progress = (
        "2026-07-10-aitp-capability-registry.md",
        "2026-07-10-aitp-context-compiler.md",
        "2026-07-10-aitp-record-envelope-compatibility.md",
        "2026-07-10-aitp-record-family-registry.md",
        "2026-07-10-aitp-m0-release-audit.md",
    )

    for name in active_progress:
        text = (progress_root / name).read_text(encoding="utf-8")
        assert "Gate 0" not in text, name
        assert "M0" in text, name


def test_document_entrypoints_route_to_v5_and_label_v4_as_legacy():
    repo_root = Path(__file__).resolve().parents[1]
    specification = (repo_root / "docs" / "AITP_SPEC.md").read_text(
        encoding="utf-8"
    )
    project_index = (repo_root / "docs" / "PROJECT_INDEX.md").read_text(
        encoding="utf-8"
    )
    adapter_index = (repo_root / "adapters" / "README.md").read_text(
        encoding="utf-8"
    )

    assert "Status: legacy v4 protocol reference" in specification
    assert "brain/v5/native_mcp.py" in specification
    assert re.search(r"does not authorize legacy\s+L0-L4 writes", specification)
    assert "Legacy V4 Protocol Architecture" in project_index
    assert "brain/v5/native_mcp.py" in project_index
    assert "brain/v5/native_mcp.py" in adapter_index
    assert "Codex is the default" in adapter_index
    assert "All adapters assume an available `aitp` executable" not in adapter_index


def test_m0_5_freezes_expansion_until_classification_and_vertical_evidence():
    repo_root = Path(__file__).resolve().parents[1]
    project_memory = (repo_root / "PROJECT_MEMORY.md").read_text(encoding="utf-8")
    roadmap = (
        repo_root
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-07-09-aitp-final-research-lifecycle-roadmap.md"
    ).read_text(encoding="utf-8")
    design = (
        repo_root
        / "docs"
        / "superpowers"
        / "specs"
        / "2026-07-11-aitp-m0-5-complexity-reduction-design.md"
    ).read_text(encoding="utf-8")
    plan = (
        repo_root
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-07-11-aitp-m0-5-complexity-reduction-review.md"
    ).read_text(encoding="utf-8")

    assert "M0.5 complexity freeze" in project_memory
    assert "Writer-audit lower bound" in project_memory
    assert "M0.5: Complexity Reduction And Vertical Re-Baselining" in roadmap
    assert "candidate implementation catalogs" in roadmap
    assert "status: approved-soft-deprecation-one-release" in design
    assert "Soft deprecation for one release (recommended)" in design
    assert "Option 1 was explicitly approved by the user on 2026-07-12" in design
    assert "writer scan beyond the 111-helper-call lower bound" in design
    assert "Approved for phased implementation" in plan
    assert "Do not modify legacy candidate, stage, promotion, or graph-write business" in plan
    assert "Do not begin broad M1-M5 implementation" in plan


def test_m0_5_classification_audit_covers_current_core_without_behavior_change():
    from brain.v5.capability_registry import capability_specs
    from brain.v5.record_family_registry import record_family_specs

    repo_root = Path(__file__).resolve().parents[1]
    report = (
        repo_root
        / "docs"
        / "superpowers"
        / "progress"
        / "2026-07-11-aitp-m0-5-classification-audit.md"
    ).read_text(encoding="utf-8")

    def classified_items(heading: str) -> set[str]:
        match = re.search(
            rf"^### {heading}\n\n```text\n(?P<body>.*?)\n```$",
            report,
            re.MULTILINE | re.DOTALL,
        )
        assert match, heading
        items = [line.strip() for line in match.group("body").splitlines() if line.strip()]
        assert len(items) == len(set(items)), f"duplicate items in {heading}"
        return set(items)

    capability_classes = {
        "core": classified_items(r"2\.1 Core \(59\)"),
        "vertical_extension": classified_items(r"2\.2 Vertical Extension \(112\)"),
        "maintenance": classified_items(r"2\.3 Maintenance \(43\)"),
        "migration": classified_items(r"2\.4 Migration \(43\)"),
    }
    assert {name: len(items) for name, items in capability_classes.items()} == {
        "core": 59,
        "vertical_extension": 112,
        "maintenance": 43,
        "migration": 43,
    }
    classified_capabilities = set().union(*capability_classes.values())
    assert sum(map(len, capability_classes.values())) == len(classified_capabilities)

    registered_capabilities = set(capability_specs())
    registered_capabilities.discard("harness_feedback_problem_dossier")
    assert len(registered_capabilities) == 257
    assert classified_capabilities == registered_capabilities

    family_classes = {
        "core": classified_items(r"3\.1 Core \(25\)"),
        "vertical_extension": classified_items(r"3\.2 Vertical Extension \(37\)"),
        "migration": classified_items(r"3\.3 Migration \(4\)"),
        "soft_deprecation_candidate": classified_items(
            r"3\.4 Soft-Deprecation Candidates \(4\)"
        ),
    }
    assert {name: len(items) for name, items in family_classes.items()} == {
        "core": 25,
        "vertical_extension": 37,
        "migration": 4,
        "soft_deprecation_candidate": 4,
    }
    classified_families = set().union(*family_classes.values())
    assert sum(map(len, family_classes.values())) == len(classified_families)
    assert classified_families == set(record_family_specs())

    normalized = " ".join(report.split())
    assert (
        "Status: reviewed classification baseline plus accepted vertical extensions; "
        "CR1 changed compact visibility for six maintenance capabilities, and the "
        "new-software vertical added three full-surface human-gated Skill lifecycle "
        "capabilities. M1 then added six host-neutral lifecycle capabilities and six "
        "trust-neutral core record families. M3 added reviewed physics knowledge and "
        "source-memory capabilities/families; M4 Tasks 1-3 added procedural Skill "
        "candidate, readiness, package-artifact, and proposal families without compact "
        "or install authority."
    ) in normalized
    assert "## 6. Resolved Review Decisions" in report
    assert "bounded scanner closure does not convert candidate counts into a no-bypass proof" in normalized
    assert "all 161 current named-helper rows" in normalized
    assert "all 169 current direct" in normalized
    assert "257-capability staged core" in normalized
    assert "709/709 declared production Python files" in normalized


def test_m0_5_writer_classification_covers_static_audit_without_overclaiming():
    from brain.v5.runtime_audit import build_runtime_capability_audit

    repo_root = Path(__file__).resolve().parents[1]
    report = (
        repo_root
        / "docs"
        / "superpowers"
        / "progress"
        / "2026-07-11-aitp-m0-5-classification-audit.md"
    ).read_text(encoding="utf-8")

    def writer_rows(heading: str) -> list[tuple[str, str, int, str]]:
        match = re.search(
            rf"^### {heading}\n\n~~~text\n(?P<body>.*?)\n~~~$",
            report,
            re.MULTILINE | re.DOTALL,
        )
        assert match, heading
        rows = []
        for line in match.group("body").splitlines():
            if not line.strip():
                continue
            raw = line.partition(" | ")[0].strip()
            path, function, source_line, call = raw.rsplit(":", 3)
            rows.append((path, function, int(source_line), call))
        assert len(rows) == len(set(rows)), f"duplicate writers in {heading}"
        return rows

    def stable_classes(raw_classes):
        ordinals = {}
        stable = {name: set() for name in raw_classes}
        ordered = sorted(
            (row, class_name)
            for class_name, rows in raw_classes.items()
            for row in rows
        )
        for (path, function, _line, call), class_name in ordered:
            key = (path, function, call)
            ordinals[key] = ordinals.get(key, 0) + 1
            stable[class_name].add(
                f"{path}:{function}:{call}:{ordinals[key]}"
            )
        return stable

    writer_rows_by_class = {
        "canonical_record_or_repository": writer_rows(
            r"4\.1 Canonical Record Or Repository \(84\)"
        ),
        "derived_index_or_surface": writer_rows(
            r"4\.2 Derived Index Or Surface \(29\)"
        ),
        "host_or_runtime": writer_rows(r"4\.3 Host Or Runtime \(18\)"),
        "migration_or_legacy_compat": writer_rows(
            r"4\.4 Migration Or Legacy Compatibility \(28\)"
        ),
        "shared_storage_primitive": writer_rows(
            r"4\.5 Shared Storage Primitive \(2\)"
        ),
    }
    writer_classes = stable_classes(writer_rows_by_class)
    assert {name: len(items) for name, items in writer_classes.items()} == {
        "canonical_record_or_repository": 84,
        "derived_index_or_surface": 29,
        "host_or_runtime": 18,
        "migration_or_legacy_compat": 28,
        "shared_storage_primitive": 2,
    }
    classified = set().union(*writer_classes.values())
    assert sum(map(len, writer_classes.values())) == len(classified)

    audit = build_runtime_capability_audit(repo_root)
    audited = {row["stable_signature"] for row in audit["writers"]}
    assert audit["inventory"]["writer_count"] == 161
    assert classified == audited

    direct_rows_by_class = {
        "canonical_blob_or_record": writer_rows(
            r"4\.6\.1 Canonical Blob Or Record \(7\)"
        ),
        "derived_index_or_surface": writer_rows(
            r"4\.6\.2 Derived Index Or Surface \(24\)"
        ),
        "host_runtime_or_maintenance": writer_rows(
            r"4\.6\.3 Host Runtime Or Maintenance \(57\)"
        ),
        "migration_or_archived_legacy": writer_rows(
            r"4\.6\.4 Migration Or Archived Legacy \(75\)"
        ),
        "shared_storage_primitive": writer_rows(
            r"4\.6\.5 Shared Storage Primitive \(3\)"
        ),
        "transient_external_io": writer_rows(
            r"4\.6\.6 Transient External IO \(3\)"
        ),
    }
    direct_classes = stable_classes(direct_rows_by_class)
    assert {name: len(items) for name, items in direct_classes.items()} == {
        "canonical_blob_or_record": 7,
        "derived_index_or_surface": 24,
        "host_runtime_or_maintenance": 57,
        "migration_or_archived_legacy": 75,
        "shared_storage_primitive": 3,
        "transient_external_io": 3,
    }
    classified_direct = set().union(*direct_classes.values())
    assert sum(map(len, direct_classes.values())) == len(classified_direct)
    audited_direct = {
        row["stable_signature"] for row in audit["direct_mutation_candidates"]
    }
    assert audit["inventory"]["direct_mutation_candidate_count"] == 169
    assert classified_direct == audited_direct
    assert all(
        signature in direct_classes["migration_or_archived_legacy"]
        for signature in audited_direct
        if signature.startswith("brain/") and not signature.startswith("brain/v5/")
    )
    assert (
        "brain/gates.py:evaluate_l1_stage:write_text:1"
        in direct_classes["migration_or_archived_legacy"]
    )

    normalized = " ".join(report.split())
    assert "The 111-row static audit is an under-approximation of filesystem mutation." in normalized
    assert "cannot yet prove complete writer closure" in normalized


def test_m0_5_retention_review_has_an_explicit_disposition_for_every_class():
    repo_root = Path(__file__).resolve().parents[1]
    report = (
        repo_root
        / "docs"
        / "superpowers"
        / "progress"
        / "2026-07-11-aitp-m0-5-classification-audit.md"
    ).read_text(encoding="utf-8")
    roadmap = (
        repo_root
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-07-09-aitp-final-research-lifecycle-roadmap.md"
    ).read_text(encoding="utf-8")

    match = re.search(
        r"^### 7\.1 Postponed Vertical Extensions \(12\)\n\n```text\n"
        r"(?P<body>.*?)\n```$",
        report,
        re.MULTILINE | re.DOTALL,
    )
    assert match
    postponed = {
        line.strip() for line in match.group("body").splitlines() if line.strip()
    }
    assert postponed == {
        "context_profile_draft",
        "context_profile_templates",
        "harness_feedback_seed_bundle",
        "host_agnostic_moment_policy",
        "interaction_recording_preview",
        "interaction_recording_worklist",
        "lane_exemplar_manifest",
        "qsgw_cockpit_compact",
        "record_final_output_profile",
        "record_lane_exemplar",
        "record_toy_numeric_finite_size_exemplar",
        "research_cockpit_compact",
    }
    normalized = " ".join(report.split())
    assert "77 retained vertical extensions" in normalized
    assert "four zero-record unimplemented-layout families remain soft-deprecation candidates" in normalized
    assert (
        "- [x] Retain, merge, postpone, or remove M1-M5 candidate capabilities"
        in roadmap
    )


def test_m1_through_m6_plans_have_consistent_file_ownership():
    repo_root = Path(__file__).resolve().parents[1]
    plans_root = repo_root / "docs" / "superpowers" / "plans"
    plans = sorted(plans_root.glob("2026-07-10-aitp-gate-[1-6]-*.md"))
    assert len(plans) == 6

    rows = []
    creators = {}
    for plan in plans:
        milestone = int(re.search(r"gate-([1-6])", plan.name).group(1))
        text = plan.read_text(encoding="utf-8")
        assert text.startswith(f"# AITP M{milestone} ")
        assert not re.search(r"\bGates? [0-6](?:\.[0-9]+)?", text)
        for action, path in re.findall(
            r"^- (Create|Modify): `([^`]+)`",
            text,
            re.MULTILINE,
        ):
            rows.append((milestone, action, path))
            if action == "Create":
                assert path not in creators, f"duplicate creator for {path}"
                creators[path] = milestone

    for milestone, action, path in rows:
        if action != "Modify" or (repo_root / path).exists():
            continue
        assert path in creators, f"missing creator for planned modify target {path}"
        assert creators[path] <= milestone


def test_ci_installs_the_full_repository_test_dependency_closure():
    repo_root = Path(__file__).resolve().parents[1]
    workflow = (repo_root / ".github" / "workflows" / "v5-test-lanes.yml").read_text(
        encoding="utf-8"
    )
    requirements_path = repo_root / "requirements-test.txt"

    assert "pip install -r requirements-test.txt" in workflow
    requirements = {
        re.split(r"[<>=!~;\s\[]", line.partition("#")[0].strip(), maxsplit=1)[0].lower()
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
        if line.partition("#")[0].strip()
    }
    assert {
        "fastmcp",
        "jsonschema",
        "numpy",
        "pydantic",
        "pygments",
        "pypdf",
        "pytest",
        "pyyaml",
        "sympy",
    } <= requirements
