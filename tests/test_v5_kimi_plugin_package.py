from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CODEX_PLUGIN = REPO_ROOT / "plugins" / "aitp-research-protocol"
KIMI_PLUGIN = REPO_ROOT / "plugins" / "aitp-research-protocol-kimi"


def _load_launcher():
    path = KIMI_PLUGIN / "scripts" / "launch_aitp_mcp_kimi.py"
    spec = importlib.util.spec_from_file_location("aitp_kimi_plugin_launcher_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_repo(path: Path) -> Path:
    entrypoint = path / "brain" / "v5" / "native_mcp.py"
    entrypoint.parent.mkdir(parents=True)
    entrypoint.write_text("# fixture\n", encoding="utf-8")
    return path


def _frontmatter_name(text: str) -> str:
    match = re.search(r"^---\n.*?^name:\s*([^\n]+)\n.*?^---$", text, re.MULTILINE | re.DOTALL)
    assert match
    return match.group(1).strip()


def _compact_calls(text: str) -> set[str]:
    return set(re.findall(r"\baitp_v5_codex_[a-z_]+\b", text))


def test_kimi_manifest_marketplace_and_packaged_paths_are_closed():
    manifest = json.loads((KIMI_PLUGIN / "kimi.plugin.json").read_text(encoding="utf-8"))
    marketplace = json.loads(
        (REPO_ROOT / "plugins" / "marketplace.kimi.json").read_text(encoding="utf-8")
    )
    codex_mcp = json.loads((CODEX_PLUGIN / ".mcp.json").read_text(encoding="utf-8"))

    assert manifest["name"] == "aitp-research-protocol"
    assert manifest["skills"] == "./skills/"
    assert manifest["sessionStart"] == {"skill": "using-aitp"}
    assert marketplace["plugins"] == [
        {
            "id": manifest["name"],
            "displayName": "AITP Research Protocol",
            "source": "./aitp-research-protocol-kimi",
        }
    ]

    kimi_mcp = manifest["mcpServers"]["aitp"]
    codex_spec = codex_mcp["mcpServers"]["aitp"]
    assert kimi_mcp["command"] == codex_spec["command"] == "uv"
    assert [value for index, value in enumerate(kimi_mcp["args"]) if kimi_mcp["args"][index - 1:index] == ["--with"]] == [
        value
        for index, value in enumerate(codex_spec["args"])
        if codex_spec["args"][index - 1:index] == ["--with"]
    ]
    launcher = KIMI_PLUGIN / kimi_mcp["args"][-1]
    assert launcher.is_file()
    assert (KIMI_PLUGIN / manifest["skills"] / manifest["sessionStart"]["skill"] / "SKILL.md").is_file()


def test_kimi_launcher_resolves_repo_and_topics_in_documented_order(tmp_path, monkeypatch):
    launcher = _load_launcher()
    env_repo = _fake_repo(tmp_path / "env-repo")
    config_repo = _fake_repo(tmp_path / "config-repo")
    install_repo = _fake_repo(tmp_path / "install-repo")
    vendor_repo = _fake_repo(tmp_path / "plugin" / "vendor" / "AITP-Research-Protocol")
    plugin_root = vendor_repo.parents[1]

    monkeypatch.setenv("AITP_REPO_ROOT", str(env_repo))
    assert launcher._resolve_repo_root(
        plugin_root,
        {"repo_root": str(config_repo)},
        {"installs": {"v5": {"variables": {"REPO_ROOT": str(install_repo)}}}},
    ) == env_repo.resolve()
    monkeypatch.delenv("AITP_REPO_ROOT")
    assert launcher._resolve_repo_root(
        plugin_root,
        {"repo_root": str(config_repo)},
        {"installs": {"v5": {"variables": {"REPO_ROOT": str(install_repo)}}}},
    ) == config_repo.resolve()
    assert launcher._resolve_repo_root(
        plugin_root,
        {},
        {"installs": {"v5": {"variables": {"REPO_ROOT": str(install_repo)}}}},
    ) == install_repo.resolve()
    assert launcher._resolve_repo_root(plugin_root, {}, {}) == vendor_repo.resolve()

    monkeypatch.setenv("AITP_TOPICS_ROOT", str(tmp_path / "env-topics"))
    assert launcher._resolve_topics_root(
        {"topics_root": str(tmp_path / "config-topics")},
        {"installs": {"v5": {"variables": {"TOPICS_ROOT": str(tmp_path / "install-topics")}}}},
    ) == tmp_path / "env-topics"
    monkeypatch.delenv("AITP_TOPICS_ROOT")
    assert launcher._resolve_topics_root(
        {"topics_root": str(tmp_path / "config-topics")}, {}
    ) == tmp_path / "config-topics"
    assert launcher.CONFIG_PATH.name == "kimi-plugin-config.json"


def test_kimi_launcher_defaults_to_compact_but_preserves_explicit_full(tmp_path, monkeypatch):
    launcher = _load_launcher()
    repo = _fake_repo(tmp_path / "repo")
    topics = tmp_path / "topics"
    calls = []

    monkeypatch.setattr(launcher, "_read_json", lambda _path: {})
    monkeypatch.setattr(launcher, "_resolve_repo_root", lambda *_args: repo)
    monkeypatch.setattr(launcher, "_resolve_topics_root", lambda *_args: topics)
    monkeypatch.setattr(launcher.os, "chdir", lambda path: calls.append(("chdir", Path(path))))
    monkeypatch.setattr(
        launcher.runpy,
        "run_path",
        lambda path, **kwargs: calls.append(("run_path", Path(path), kwargs)),
    )

    monkeypatch.delenv("AITP_MCP_SURFACE", raising=False)
    launcher.main()
    assert launcher.os.environ["AITP_MCP_SURFACE"] == "codex"
    assert topics.is_dir()
    assert any(item[0] == "run_path" for item in calls)

    monkeypatch.setenv("AITP_MCP_SURFACE", "full")
    launcher.main()
    assert launcher.os.environ["AITP_MCP_SURFACE"] == "full"


def test_kimi_packaged_skills_cover_the_compact_codex_contract():
    codex_skills = {path.parent.name: path for path in CODEX_PLUGIN.glob("skills/*/SKILL.md")}
    kimi_skills = {path.parent.name: path for path in KIMI_PLUGIN.glob("skills/*/SKILL.md")}
    assert set(kimi_skills) == set(codex_skills) == {
        "aitp-runtime",
        "configure-aitp",
        "using-aitp",
    }

    for name in sorted(codex_skills):
        codex_text = codex_skills[name].read_text(encoding="utf-8")
        kimi_text = kimi_skills[name].read_text(encoding="utf-8")
        assert _frontmatter_name(kimi_text) == name
        assert _compact_calls(codex_text) <= _compact_calls(kimi_text)

    using = kimi_skills["using-aitp"].read_text(encoding="utf-8")
    runtime = kimi_skills["aitp-runtime"].read_text(encoding="utf-8")
    configure = kimi_skills["configure-aitp"].read_text(encoding="utf-8")
    assert "AITP_MCP_SURFACE=codex" in using
    assert "AITP_MCP_SURFACE=full" in using
    assert "aitp_v5_get_execution_brief" not in using
    assert "aitp_v5_codex_record_apply" in runtime
    assert "aitp_v5_codex_closeout" in runtime
    assert "compact Kimi Code AITP surface" in using
    assert "compact Kimi Code AITP surface" in configure


def test_kimi_readme_keeps_plugin_and_project_registration_distinct():
    readme = (KIMI_PLUGIN / "README.md").read_text(encoding="utf-8")
    assert "AITP_MCP_SURFACE=codex" in readme
    assert "AITP_MCP_SURFACE=full" in readme
    assert "Do not run this plugin together with a project-scope AITP install" in readme
    assert "/plugins mcp disable aitp-research-protocol aitp" in readme
    assert "keep the skills" in readme
