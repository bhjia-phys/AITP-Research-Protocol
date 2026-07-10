from brain.v5.runtime_audit import (
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


def test_runtime_audit_reports_python_parse_errors(tmp_path):
    repo = _minimal_repo(tmp_path)
    broken = repo / "brain" / "v5" / "broken.py"
    broken.write_text("def broken(:\n", encoding="utf-8")

    payload = build_runtime_capability_audit(repo)

    row = next(item for item in payload["files"] if item["path"].endswith("broken.py"))
    assert row["classification"] == "requires_task_update"
    assert row["parse_error"]


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
    assert "actual_registry_record_count: `0`" in rendered
    assert "can_update_claim_trust: false" in rendered

    missing_capabilities = dict(payload)
    missing_capabilities.pop("capabilities")
    assert not validate_runtime_capability_audit(missing_capabilities).ok
    missing_writers = dict(payload)
    missing_writers.pop("writers")
    assert not validate_runtime_capability_audit(missing_writers).ok
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
