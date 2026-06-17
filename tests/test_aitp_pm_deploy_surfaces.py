from pathlib import Path
import importlib.util


REPO = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def _load_pm():
    spec = importlib.util.spec_from_file_location("aitp_pm_for_test", REPO / "scripts" / "aitp-pm.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_deploy_skills_keep_relation_map_recovery_boundary():
    for rel in [
        "deploy/skills/using-aitp.md",
        "deploy/skills/aitp-runtime.md",
        "deploy/codex/skills/using-aitp.md",
        "deploy/codex/skills/aitp-runtime.md",
        "deploy/templates/claude-code/using-aitp.md",
        "deploy/templates/claude-code/aitp-runtime.md",
        "deploy/templates/kimi-code/using-aitp.md",
        "deploy/templates/kimi-code/aitp-runtime.md",
    ]:
        text = _read(rel)
        assert "aitp_v5_get_claim_relation_map" in text
        assert "claim relation map" in text.lower()


def test_deploy_runtime_skills_keep_progressive_recording_trigger_policy():
    for rel in [
        "deploy/skills/aitp-runtime.md",
        "deploy/codex/skills/aitp-runtime.md",
        "deploy/templates/claude-code/aitp-runtime.md",
        "deploy/templates/kimi-code/aitp-runtime.md",
    ]:
        text = _read(rel)
        assert "AITP runtime is not a transcript logger" in text
        assert "old-knowledge answers that do not affect a topic" in text
        assert "research-relevant fact changed or became durable" in text
        assert "first navigation answer should reveal only topic/session/claim position" in text
        assert "Expand exactly one slot" in text
        assert "intentionally lightweight first-level" in text
        assert "does not replace" in text
        assert "execution_brief" in text
        assert "process_graph_slice" in text
        assert "aitp_v5_verify_recording_effect" in text


def test_deploy_using_skills_keep_lightweight_intent_matrix():
    for rel in [
        "deploy/skills/using-aitp.md",
        "deploy/codex/skills/using-aitp.md",
        "deploy/templates/claude-code/using-aitp.md",
        "deploy/templates/kimi-code/using-aitp.md",
    ]:
        text = _read(rel)
        assert "Classify request intensity" in text
        assert "lightweight recording navigation; process graph only when needed" in text
        assert "choose the read-only row first" in text
        assert "Do not create a" in text
        assert "new topic, claim, session, or binding merely because" in text


def test_protocol_and_runtime_versions_are_strict_v5_050():
    pm = _load_pm()
    assert pm._read_version() == "0.5.0"
    assert pm._strict_v5_contract_issues() == []
    assert pm._strict_v5_deploy_surface_issues() == []

    protocol = pm._read_protocol_metadata()
    assert protocol["version"] == "0.5.0"
    assert protocol["implementation_generation"] == "v5"
    assert protocol["implementation_entrypoint"] == "brain/v5/native_mcp.py"
    assert protocol["legacy_stage_model"] == "orientation-only"

    protocol_text = _read("brain/PROTOCOL.md")
    assert "replaces the old L0-L4 stage machine as the active execution contract" in protocol_text
    assert "legacy L0-L4 stage files are migration context only" in protocol_text


def test_agent_facing_templates_do_not_teach_legacy_active_wiring():
    opencode = _read("deploy/templates/opencode/aitp-plugin.js")
    assert "AITP 0.5.0 v5 adapter" in opencode
    assert "aitp_v5_get_execution_brief" in opencode
    assert "aitp_v5_build_workspace_recovery_audit" in opencode
    assert "D:/BaiduSyncdisk" not in opencode
    assert "v4.1 harness adapter" not in opencode
    assert "Stage Skills (checklist-driven" not in opencode
    assert "AITP MCP tools are available as `aitp_*`" not in opencode
    assert "aitp_get_execution_brief(topics_root=" not in opencode

    setup = _read("deploy/templates/claude-code/aitp-mcp-setup.md")
    assert "brain/v5/native_mcp.py" in setup
    assert "aitp-pm.py doctor" in setup
    assert "AITP 0.5.0/v5" in setup
    assert "claude mcp add-json" not in setup
    assert '"args":["{{REPO_ROOT}}/brain/mcp_server.py"]' not in setup


def test_deploy_hooks_guard_canonical_and_root_stores():
    guard = _read("deploy/hooks/aitp-routing-guard.py")
    assert "ROOT_AITP_FULL" in guard
    assert "workspace-root runtime store" in guard
    assert "research/aitp-topics/.aitp records" in guard
    assert "workspace-root .aitp runtime records" in guard

    keyword_router = _read("deploy/hooks/aitp-keyword-router.py")
    assert "aitp_v5_get_execution_brief" in keyword_router
    assert "aitp_v5_get_claim_relation_map" in keyword_router
    assert "canonical research/aitp-topics/.aitp store" in keyword_router


def test_claude_fallback_hooks_match_deploy_hooks():
    for name in ["aitp-keyword-router.py", "aitp-routing-guard.py"]:
        assert _read(f"deploy/templates/claude-code/{name}") == _read(f"deploy/hooks/{name}")


def test_kimi_project_install_writes_kimi_and_kimi_code_surfaces(tmp_path):
    pm = _load_pm()
    workspace = tmp_path / "Theoretical-Physics"
    topics = workspace / "research" / "aitp-topics"
    topics.mkdir(parents=True)
    variables = {
        "REPO_ROOT": str(REPO).replace("\\", "/"),
        "TOPICS_ROOT": str(topics).replace("\\", "/"),
        "TARGET_ROOT": str(workspace).replace("\\", "/"),
        "USER_HOME": str(tmp_path).replace("\\", "/"),
        "CLAUDE_USER_DIR": str(tmp_path / ".claude").replace("\\", "/"),
        "KIMI_USER_DIR": str(tmp_path / ".kimi").replace("\\", "/"),
        "CODEX_USER_DIR": str(tmp_path / ".codex").replace("\\", "/"),
        "CODEX_HOME_DIR": str(tmp_path / ".codex-home").replace("\\", "/"),
        "CODEX_SWITCHER_SKILLS_DIR": str(tmp_path / ".codex-switcher" / "skills").replace("\\", "/"),
        "AGENTS_SKILLS_DIR": str(tmp_path / ".agents" / "skills").replace("\\", "/"),
    }

    deployed = pm._deploy_kimi_code("project", workspace, variables, remove=False)

    assert any(".kimi-code" in str(item) for item in deployed)
    for root_name in [".kimi", ".kimi-code"]:
        base = workspace / root_name
        using = (base / "skills" / "using-aitp" / "SKILL.md").read_text(encoding="utf-8")
        runtime = (base / "skills" / "aitp-runtime" / "SKILL.md").read_text(encoding="utf-8")
        assert "aitp_v5_get_claim_relation_map" in using
        assert "claim relation map" in runtime.lower()
        assert "brain/v5/native_mcp.py" in (base / "mcp.json").read_text(encoding="utf-8")
        assert "brain/v5/native_mcp.py" in (base / "config.toml").read_text(encoding="utf-8")

    issues: list[str] = []
    pm._check_agent_toml(workspace / ".kimi-code" / "config.toml", issues, "kimi-code (project)")
    assert issues == []
