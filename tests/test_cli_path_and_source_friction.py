from __future__ import annotations

import importlib
import importlib.util
from argparse import Namespace
from pathlib import Path


def test_default_topics_root_discovers_workspace_layout(tmp_path, monkeypatch):
    from brain.cli import paths

    home = tmp_path / "home"
    home.mkdir()
    workspace = tmp_path / "workspace"
    topics_root = workspace / "research" / "aitp-topics"
    topics_root.mkdir(parents=True)

    monkeypatch.delenv("AITP_TOPICS_ROOT", raising=False)
    monkeypatch.setattr(paths.Path, "home", classmethod(lambda cls: home))
    monkeypatch.chdir(workspace)

    assert paths.default_topics_root() == str(topics_root)


def test_source_add_records_l3_supplemental_source(tmp_path, monkeypatch):
    from brain.cli.commands import source

    topics_root = tmp_path / "aitp-topics"
    topic_root = topics_root / "demo"
    monkeypatch.setenv("AITP_TOPICS_ROOT", str(topics_root))
    source._write_md(
        topic_root / "state.md",
        {"stage": "L3", "lane": "code_method"},
        "# State\n",
    )

    result = source.cmd_source_add(
        Namespace(
            topic="demo",
            id="new-paper",
            title="New Paper",
            path="",
            url="",
            repo="",
            branch="",
            commit="",
            type="paper",
            role="direct_dependency",
            notes="",
        )
    )

    assert result == 0
    fm, _ = source._parse_md(topic_root / "L0" / "sources" / "new-paper" / "source.md")
    assert fm["registered_from_stage"] == "L3"
    assert "[L3] Registered source: new-paper" in (topic_root / "research.md").read_text(encoding="utf-8")


def test_v5_native_mcp_keeps_legacy_discovery_aliases_disabled_by_default(monkeypatch):
    monkeypatch.delenv("AITP_V5_EXPOSE_COMPAT_ALIASES", raising=False)
    import brain.v5.native_mcp as native_mcp

    native_mcp = importlib.reload(native_mcp)

    assert "aitp_v5_get_execution_brief" in native_mcp._TOOLS
    assert "aitp_list_topics" not in native_mcp._TOOLS
    assert "aitp_get_execution_brief" not in native_mcp._TOOLS
    assert "aitp_bootstrap_topic" not in native_mcp._TOOLS


def test_v5_native_mcp_exposes_legacy_discovery_aliases_only_for_compat_mode(monkeypatch):
    monkeypatch.setenv("AITP_V5_EXPOSE_COMPAT_ALIASES", "1")
    import brain.v5.native_mcp as native_mcp

    native_mcp = importlib.reload(native_mcp)
    try:
        assert "aitp_list_topics" in native_mcp._TOOLS
        assert "aitp_get_execution_brief" in native_mcp._TOOLS
        assert "aitp_bootstrap_topic" in native_mcp._TOOLS
        assert "aitp_v5_get_execution_brief" in native_mcp._TOOLS
    finally:
        monkeypatch.delenv("AITP_V5_EXPOSE_COMPAT_ALIASES", raising=False)
        importlib.reload(native_mcp)


def test_package_manager_uses_topic_root_aitp_as_v5_surface(tmp_path):
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "aitp-pm.py"
    spec = importlib.util.spec_from_file_location("aitp_pm_for_test", module_path)
    assert spec and spec.loader
    aitp_pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(aitp_pm)

    workspace = tmp_path / "workspace"
    topics_root = workspace / "research" / "aitp-topics"

    assert aitp_pm._v5_topics_root_for(topics_root) == topics_root / ".aitp" / "topics"
    assert aitp_pm._v5_topics_root_for(topics_root) != workspace / ".aitp" / "topics"
