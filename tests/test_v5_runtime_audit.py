import warnings
from pathlib import Path

from brain.v5.runtime_audit import (
    _capability_rows,
    _execution_capability_rows,
    _layout_families,
    build_runtime_capability_audit,
    render_runtime_capability_audit_markdown,
)
from brain.v5.runtime_audit_contracts import validate_runtime_capability_audit


def _minimal_repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "brain" / "v5").mkdir(parents=True)
    (repo / "hooks").mkdir()
    (repo / "tests").mkdir()
    (repo / "brain" / "v5" / "paths.py").write_text(
        '_LAYOUT_DIRS = ["registry/claims"]\n', encoding="utf-8"
    )
    return repo


def test_runtime_audit_finds_registry_drift_and_classifies_every_file(tmp_path):
    repo = tmp_path / "repo"
    (repo / "brain" / "v5").mkdir(parents=True)
    (repo / "hooks").mkdir()
    (repo / "tests").mkdir()
    (repo / "brain" / "v5" / "paths.py").write_text(
        '_LAYOUT_DIRS = ["registry/claims"]\n', encoding="utf-8"
    )
    (repo / "brain" / "v5" / "writer.py").write_text(
        'def write(ws):\n    return ws.registry_dir("insights")\n', encoding="utf-8"
    )
    (repo / "hooks" / "host.py").write_text("pass\n", encoding="utf-8")
    (repo / "tests" / "test_v5_writer.py").write_text("pass\n", encoding="utf-8")
    plan = repo / "plan.md"
    plan.write_text("- Create: `brain/v5/writer.py`\n", encoding="utf-8")

    payload = build_runtime_capability_audit(repo, plan_path=plan)

    assert payload["record_families"]["used_not_layout"] == ["insights"]
    assert payload["inventory"]["classification_counts"]["directly_touched_by_plan"] == 1
    assert all(row["classification"] for row in payload["files"])


def test_static_layout_audit_includes_focused_m3_family_rows(tmp_path):
    root = tmp_path / "brain" / "v5"
    root.mkdir(parents=True)
    paths = root / "paths.py"
    registry = root / "record_family_registry.py"
    paths.write_text('_LAYOUT_DIRS = [*("registry/" + item for item in ())]\n', encoding="utf-8")
    registry.write_text(
        '_REGISTRY_ROWS = (("claims", "claim", "ClaimRecord", "claim_id"),)\n',
        encoding="utf-8",
    )
    (root / "record_family_m3.py").write_text(
        'M3_REGISTRY_ROWS = (("insights", "insight", "InsightRecord", "insight_id"),)\n',
        encoding="utf-8",
    )

    assert _layout_families(paths, registry_path=registry) == ["claims", "insights"]


def test_static_layout_audit_does_not_treat_four_row_container_as_a_row(tmp_path):
    root = tmp_path / "brain" / "v5"
    root.mkdir(parents=True)
    paths = root / "paths.py"
    registry = root / "record_family_registry.py"
    paths.write_text('_LAYOUT_DIRS = tuple()\n', encoding="utf-8")
    registry.write_text(
        "_REGISTRY_ROWS = (\n"
        '    ("claims", "claim", "ClaimRecord", "claim_id"),\n'
        '    ("evidence", "evidence", "EvidenceRecord", "evidence_id"),\n'
        '    ("ideas", "idea", None, "idea_id"),\n'
        '    ("outputs", "output", None, "output_id"),\n'
        ")\n",
        encoding="utf-8",
    )

    assert _layout_families(paths, registry_path=registry) == [
        "claims",
        "evidence",
        "ideas",
        "outputs",
    ]


def test_runtime_audit_reports_actual_workspace_families(tmp_path):
    repo = _minimal_repo(tmp_path)
    workspace = tmp_path / "topics"
    (workspace / ".aitp" / "registry" / "claims").mkdir(parents=True)
    (workspace / ".aitp" / "registry" / "unregistered_family").mkdir()
    (workspace / ".aitp" / "registry" / "claims" / "c1.md").write_text(
        "# Claim\n", encoding="utf-8"
    )
    (workspace / ".aitp" / "registry" / "claims" / "c2.md").write_text(
        "# Claim\n", encoding="utf-8"
    )

    payload = build_runtime_capability_audit(repo, workspace_base=workspace)

    assert payload["record_families"]["actual_workspace"] == [
        "claims",
        "unregistered_family",
    ]
    assert payload["record_families"]["actual_not_layout"] == ["unregistered_family"]
    assert payload["record_families"]["actual_workspace_counts"] == {
        "claims": 2,
        "unregistered_family": 0,
    }
    assert payload["inventory"]["actual_registry_record_count"] == 2
    rendered = render_runtime_capability_audit_markdown(payload)
    assert "| claims | 2 |" in rendered


def test_runtime_audit_keeps_repository_backed_semantic_writers_visible(tmp_path):
    repo = _minimal_repo(tmp_path)
    (repo / "brain" / "v5" / "writer.py").write_text(
        "from brain.v5.record_repository import RecordRepository\n\n"
        "def direct(ws, record):\n"
        "    return RecordRepository(ws, actor=None).write('claims', record)\n\n"
        "def via_local(ws, record):\n"
        "    repository = RecordRepository(ws, actor=None)\n"
        "    return repository.write('evidence', record)\n\n"
        "def unrelated(stream, data):\n"
        "    return stream.write(data)\n",
        encoding="utf-8",
    )

    writers = build_runtime_capability_audit(repo)["writers"]

    repository_rows = [row for row in writers if row["call"] == "repository_write"]
    assert [row["registry_families"] for row in repository_rows] == [["claims"], ["evidence"]]
    assert not [row for row in writers if row["function"] == "unrelated"]


def test_runtime_audit_reports_python_parse_errors(tmp_path):
    repo = _minimal_repo(tmp_path)
    broken = repo / "brain" / "v5" / "broken.py"
    broken.write_text("def broken(:\n", encoding="utf-8")

    payload = build_runtime_capability_audit(repo)

    row = next(item for item in payload["files"] if item["path"].endswith("broken.py"))
    assert row["classification"] == "requires_task_update"
    assert row["parse_error"]
    policy = payload["writer_scan_policy"]
    assert policy["bounded_coverage_complete"] is False
    assert policy["parse_error_count"] == 1
    assert policy["parse_error_paths"] == ["brain/v5/broken.py"]


def test_runtime_audit_contract_and_markdown(tmp_path):
    payload = build_runtime_capability_audit(_minimal_repo(tmp_path))

    result = validate_runtime_capability_audit(payload)
    rendered = render_runtime_capability_audit_markdown(payload)

    assert payload["truth_source"] == "static_source_and_filesystem_inventory"
    assert payload["summary_inputs_trusted"] is False
    assert result.ok
    assert "# AITP Runtime Capability Audit" in rendered
    assert "## Registry Family Drift" in rendered
    assert "## Runtime Capability Drift" in rendered
    assert "## Canonical Writer Candidates" in rendered
    assert "## Direct Filesystem Mutation Candidates" in rendered
    assert "writer_scan_coverage_complete: false" in rendered
    assert "writer_scan_bounded_coverage_complete: true" in rendered
    assert "actual_registry_record_count: `0`" in rendered
    assert "can_update_claim_trust: false" in rendered

    missing_capabilities = dict(payload)
    missing_capabilities.pop("capabilities")
    assert not validate_runtime_capability_audit(missing_capabilities).ok
    missing_writers = dict(payload)
    missing_writers.pop("writers")
    assert not validate_runtime_capability_audit(missing_writers).ok
    missing_direct_mutations = dict(payload)
    missing_direct_mutations.pop("direct_mutation_candidates")
    assert not validate_runtime_capability_audit(missing_direct_mutations).ok
    missing_scan_policy = dict(payload)
    missing_scan_policy.pop("writer_scan_policy")
    assert not validate_runtime_capability_audit(missing_scan_policy).ok
    missing_bounded_evidence = {
        **payload,
        "writer_scan_policy": dict(payload["writer_scan_policy"]),
    }
    missing_bounded_evidence["writer_scan_policy"].pop("parse_error_paths")
    assert not validate_runtime_capability_audit(missing_bounded_evidence).ok
    mismatched_mutation_total = {**payload, "inventory": dict(payload["inventory"])}
    mismatched_mutation_total["inventory"]["direct_mutation_candidate_count"] += 1
    assert not validate_runtime_capability_audit(mismatched_mutation_total).ok
    missing_counts = {**payload, "record_families": dict(payload["record_families"])}
    missing_counts["record_families"].pop("actual_workspace_counts")
    assert not validate_runtime_capability_audit(missing_counts).ok
    mismatched_total = {**payload, "inventory": dict(payload["inventory"])}
    mismatched_total["inventory"]["actual_registry_record_count"] = 1
    assert not validate_runtime_capability_audit(mismatched_total).ok


def test_runtime_audit_reports_capability_surface_drift(tmp_path):
    repo = _minimal_repo(tmp_path)
    v5 = repo / "brain" / "v5"
    (v5 / "public_surfaces.py").write_text(
        '_PUBLIC_SURFACE_NAMES = ("brief",)\n', encoding="utf-8"
    )
    (v5 / "runtime_entrypoint_catalog.py").write_text(
        "RUNTIME_ENTRYPOINTS = {\n"
        '    "brief": {"mcp": "aitp_v5_brief", "surface": "brief"},\n'
        '    "missing": {"mcp": "aitp_v5_missing", "surface": "missing_surface"},\n'
        "}\n",
        encoding="utf-8",
    )
    (v5 / "mcp_tools.py").write_text(
        "def aitp_v5_brief():\n    pass\n\n"
        "def aitp_v5_orphan():\n    pass\n",
        encoding="utf-8",
    )
    (v5 / "codex_facade.py").write_text(
        'CODEX_FACADE_TOOLS = ("aitp_v5_brief", "aitp_v5_hidden")\n'
        "CODEX_SUPPORT_TOOLS = ()\n",
        encoding="utf-8",
    )

    capabilities = build_runtime_capability_audit(repo)["capabilities"]

    assert capabilities["catalog_mcp_not_wrapped"] == ["aitp_v5_missing"]
    assert capabilities["catalog_surface_not_public"] == ["missing_surface"]
    assert capabilities["compact_not_wrapped"] == ["aitp_v5_hidden"]
    assert capabilities["wrapped_not_catalog"] == ["aitp_v5_orphan"]


def test_static_capability_audit_expands_execution_row_provider():
    from brain.v5.capability_registry_data import MCP_ONLY_CAPABILITIES

    source = Path(__file__).resolve().parents[1] / "brain" / "v5"
    static_rows = _capability_rows(
        source / "capability_registry_data.py",
        "MCP_ONLY_CAPABILITIES",
    )
    static_rows.extend(_execution_capability_rows(source))

    assert set(static_rows) == set(MCP_ONLY_CAPABILITIES)


def test_runtime_audit_counts_explicitly_imported_mcp_exports(tmp_path):
    repo = _minimal_repo(tmp_path)
    v5 = repo / "brain" / "v5"
    (v5 / "runtime_entrypoint_catalog.py").write_text(
        'RUNTIME_ENTRYPOINTS = {"imported": '
        '{"mcp": "aitp_v5_imported", "surface": "brief"}}\n',
        encoding="utf-8",
    )
    (v5 / "public_surfaces.py").write_text(
        '_PUBLIC_SURFACE_NAMES = ("brief",)\n', encoding="utf-8"
    )
    (v5 / "mcp_tools.py").write_text(
        "from brain.v5.mcp_extra import aitp_v5_imported\n", encoding="utf-8"
    )

    capabilities = build_runtime_capability_audit(repo)["capabilities"]

    assert capabilities["mcp_wrappers"] == ["aitp_v5_imported"]
    assert capabilities["catalog_mcp_not_wrapped"] == []


def test_runtime_audit_covers_source_hook_script_and_test_trees(tmp_path):
    repo = _minimal_repo(tmp_path)
    candidates = (
        "brain/legacy_runtime.py",
        "hooks/nested/host.py",
        "deploy/hooks/router.py",
        "scripts/runtime_probe.py",
        "tests/test_runtime_host.py",
    )
    for relative in candidates:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("pass\n", encoding="utf-8")

    payload = build_runtime_capability_audit(repo)
    audited = {row["path"] for row in payload["files"]}

    assert set(candidates) <= audited
    legacy = next(row for row in payload["files"] if row["path"] == "brain/legacy_runtime.py")
    assert legacy["classification"] == "deferred_legacy_or_domain_surface"


def test_runtime_audit_lists_static_and_dynamic_record_writer_calls(tmp_path):
    repo = _minimal_repo(tmp_path)
    (repo / "brain" / "v5" / "writer.py").write_text(
        "def record_claim(ws):\n"
        '    write_record(ws.registry_dir("claims") / "c.md", {})\n\n'
        "def record_dynamic(ws, family):\n"
        '    write_md(ws.registry_dir(family) / "x.md", {}, "")\n',
        encoding="utf-8",
    )

    writers = build_runtime_capability_audit(repo)["writers"]

    claim_writer = next(row for row in writers if row["function"] == "record_claim")
    dynamic_writer = next(row for row in writers if row["function"] == "record_dynamic")
    assert claim_writer["registry_families"] == ["claims"]
    assert claim_writer["dynamic_registry_family"] is False
    assert dynamic_writer["registry_families"] == []
    assert dynamic_writer["dynamic_registry_family"] is True


def test_runtime_audit_reports_direct_production_mutations_without_test_noise(tmp_path):
    repo = _minimal_repo(tmp_path)
    direct = repo / "brain" / "v5" / "direct_mutations.py"
    direct.write_text(
        "from pathlib import Path\n"
        "import os\n"
        "import shutil\n"
        "import tempfile\n\n"
        "def mutate(path: Path, source: Path, target: Path, connection):\n"
        "    path.write_text('text', encoding='utf-8')\n"
        "    path.write_bytes(b'bytes')\n"
        "    with path.open('a', encoding='utf-8') as handle:\n"
        "        handle.write('line')\n"
        "    with open(path, 'wb') as handle:\n"
        "        handle.write(b'blob')\n"
        "    shutil.copy2(source, target)\n"
        "    os.replace(source, target)\n"
        "    descriptor = os.open(path, os.O_CREAT | os.O_WRONLY)\n"
        "    with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:\n"
        "        handle.write('descriptor')\n"
        "    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as handle:\n"
        "        handle.write('temporary')\n"
        "    connection.execute('INSERT INTO records VALUES (1)')\n"
        "    connection.execute('SELECT * FROM records')\n"
        "    path.open('r', encoding='utf-8')\n"
        "    path.open(connection.mode, encoding='utf-8')\n"
        "    return 'value'.replace('v', 'V')\n",
        encoding="utf-8",
    )
    scripts = repo / "scripts"
    scripts.mkdir()
    (scripts / "materialize.py").write_text(
        "from pathlib import Path\n\n"
        "def materialize(path: Path):\n"
        "    path.write_text('generated', encoding='utf-8')\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_noise.py").write_text(
        "def test_noise(tmp_path):\n"
        "    (tmp_path / 'fixture.txt').write_text('fixture')\n",
        encoding="utf-8",
    )

    payload = build_runtime_capability_audit(repo)
    mutations = payload["direct_mutation_candidates"]
    mechanisms = [row["mechanism"] for row in mutations]

    assert payload["inventory"]["direct_mutation_candidate_count"] == 11
    assert payload["inventory"]["direct_mutation_file_count"] == 2
    assert mechanisms.count("direct_path_write") == 3
    assert mechanisms.count("direct_open_write") == 5
    assert mechanisms.count("copy_or_move") == 1
    assert mechanisms.count("rename_or_replace") == 1
    assert mechanisms.count("sqlite_mutation") == 1
    assert {row["source_scope"] for row in mutations} == {"v5", "scripts"}
    assert not [row for row in mutations if row["path"].startswith("tests/")]
    assert all(
        row["detail"] == "os.replace"
        for row in mutations
        if row["call"] == "replace"
    )
    assert not [row for row in mutations if row["call"] == "open" and row["mode"] == "r"]
    assert not [row for row in mutations if row["detail"] == "SELECT"]
    assert payload["writer_scan_policy"]["coverage_complete"] is False
    assert payload["writer_scan_policy"]["bounded_coverage_complete"] is True
    assert payload["writer_scan_policy"]["closure_scope"] == (
        "declared_python_source_prefixes"
    )
    assert payload["writer_scan_policy"]["parse_error_count"] == 0
    assert payload["writer_scan_policy"]["parse_error_paths"] == []
    assert payload["writer_scan_policy"]["scanned_source_file_count"] > 0
    assert payload["writer_scan_policy"]["scanned_source_file_count"] == (
        payload["writer_scan_policy"]["parsed_source_file_count"]
    )
    assert payload["writer_scan_policy"]["excluded_mechanisms"] == (
        payload["writer_scan_policy"]["known_gaps"]
    )
    assert "dynamic or aliased filesystem APIs" in payload["writer_scan_policy"]["known_gaps"]
    assert validate_runtime_capability_audit(payload).ok


def test_runtime_audit_does_not_emit_syntax_warnings_for_audited_sources(tmp_path):
    repo = _minimal_repo(tmp_path)
    (repo / "brain" / "warning_source.py").write_text(
        'value = "\\$"\n', encoding="utf-8"
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        build_runtime_capability_audit(repo)

    assert not [item for item in caught if issubclass(item.category, SyntaxWarning)]


def test_runtime_audit_closes_current_registry_and_shard_inventory():
    repo_root = Path(__file__).resolve().parents[1]

    payload = build_runtime_capability_audit(repo_root)
    capabilities = payload["capabilities"]
    audited = {row["path"] for row in payload["files"]}

    assert validate_runtime_capability_audit(payload).ok
    assert len(capabilities["registry_operations"]) >= 200
    assert capabilities["registry_mcp"] == capabilities["mcp_wrappers"]
    assert capabilities["registry_mcp_not_wrapped"] == []
    assert capabilities["wrapped_not_registry"] == []
    assert capabilities["registry_surface_not_public"] == []
    assert capabilities["compact_not_registry"] == []
    assert "brain/v5/_compat_shards/process_graph/part_01.py" in audited
    assert "brain/v5/runtime_entrypoint_catalog_data/part_01.py" in audited
    assert not [row for row in payload["files"] if row["parse_error"]]
    assert payload["inventory"]["direct_mutation_candidate_count"] >= 164
    assert payload["inventory"]["direct_mutation_file_count"] >= 62
    assert not [
        row
        for row in payload["direct_mutation_candidates"]
        if row["path"].startswith("tests/")
    ]
    assert {
        "direct_path_write",
        "direct_open_write",
        "copy_or_move",
        "rename_or_replace",
    } <= {row["mechanism"] for row in payload["direct_mutation_candidates"]}
