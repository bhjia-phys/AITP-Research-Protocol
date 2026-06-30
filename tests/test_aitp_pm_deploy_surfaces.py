from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys


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


def _run_hook(rel: str, payload: dict, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    hook_env = {**os.environ, **env, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    return subprocess.run(
        [sys.executable, str(REPO / rel)],
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=hook_env,
        timeout=10,
    )


def test_deploy_skills_keep_relation_map_recovery_boundary():
    for rel in [
        "deploy/skills/using-aitp.md",
        "deploy/skills/aitp-runtime.md",
        "deploy/templates/claude-code/using-aitp.md",
        "deploy/templates/claude-code/aitp-runtime.md",
        "deploy/templates/kimi-code/using-aitp.md",
        "deploy/templates/kimi-code/aitp-runtime.md",
    ]:
        text = _read(rel)
        assert "aitp_v5_get_claim_relation_map" in text
        assert "claim relation map" in text.lower()
    for rel in [
        "deploy/codex/skills/using-aitp.md",
        "deploy/codex/skills/aitp-runtime.md",
    ]:
        text = _read(rel)
        assert "aitp_v5_codex_expand" in text
        assert "relation_map" in text


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


def test_protocol_and_runtime_versions_are_strict_v5_100():
    pm = _load_pm()
    assert pm._read_version() == "1.0.0"
    assert pm._strict_v5_contract_issues() == []
    assert pm._strict_v5_deploy_surface_issues() == []

    protocol = pm._read_protocol_metadata()
    assert protocol["version"] == "1.0.0"
    assert protocol["implementation_generation"] == "v5"
    assert protocol["implementation_entrypoint"] == "brain/v5/native_mcp.py"
    assert protocol["legacy_stage_model"] == "orientation-only"

    protocol_text = _read("brain/PROTOCOL.md")
    assert "replaces the old L0-L4 stage machine as the active execution contract" in protocol_text
    assert "legacy L0-L4 stage files are migration context only" in protocol_text


def test_agent_facing_templates_do_not_teach_legacy_active_wiring():
    opencode = _read("deploy/templates/opencode/aitp-plugin.js")
    assert "AITP 1.0.0 v5 adapter" in opencode
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
    assert "AITP 1.0.0/v5" in setup
    assert "claude mcp add-json" not in setup
    assert '"args":["{{REPO_ROOT}}/brain/mcp_server.py"]' not in setup


def test_deploy_hooks_guard_canonical_and_root_stores():
    guard = _read("deploy/hooks/aitp-routing-guard.py")
    assert "ROOT_AITP_FULL" in guard
    assert "workspace-root runtime store" in guard
    assert "research/aitp-topics/.aitp records" in guard
    assert "workspace-root .aitp runtime records" in guard
    assert 'WRITE_TOOLS = {"Write", "Edit", "MultiEdit"}' in guard

    keyword_router = _read("deploy/hooks/aitp-keyword-router.py")
    assert "继续科研" in keyword_router
    assert "继续研究" in keyword_router
    assert "理论物理" in keyword_router
    assert "格林函数" in keyword_router
    assert "aitp_v5_codex_enter" in keyword_router
    assert "aitp_v5_codex_expand" in keyword_router
    assert "aitp_v5_get_execution_brief" not in keyword_router
    assert "aitp_v5_get_claim_relation_map" not in keyword_router
    assert "canonical research/aitp-topics/.aitp store" in keyword_router


def test_claude_fallback_hooks_match_deploy_hooks():
    for name in ["aitp-keyword-router.py", "aitp-routing-guard.py"]:
        assert _read(f"deploy/templates/claude-code/{name}") == _read(f"deploy/hooks/{name}")


def test_keyword_router_detects_english_and_chinese_research_requests(tmp_path):
    env = {"AITP_TOPICS_ROOT": str(tmp_path / "research" / "aitp-topics")}
    cases = [
        ("continue research on LibRPA QSGW", "research"),
        ("继续科研这个课题", "继续科研"),
    ]

    for message, expected_keyword in cases:
        result = _run_hook("deploy/hooks/aitp-keyword-router.py", {"user_message": message}, env)
        assert result.returncode == 0, result.stderr
        assert result.stdout
        payload = json.loads(result.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        assert "AITP RESEARCH REQUEST DETECTED" in context
        assert expected_keyword in context


def test_routing_guard_blocks_write_edit_and_multiedit_to_aitp_state(tmp_path):
    topics_root = tmp_path / "research" / "aitp-topics"
    env = {
        "AITP_TOPICS_ROOT": str(topics_root),
        "CLAUDE_PROJECT_DIR": str(tmp_path),
        "AITP_WORKSPACE_ROOT": str(tmp_path / ".aitp"),
        "TEMP": str(tmp_path / "tmp"),
    }
    target = "research/aitp-topics/.aitp/topics/foo/topic.md"

    for tool_name in ("Write", "Edit", "MultiEdit"):
        result = _run_hook(
            "deploy/hooks/aitp-routing-guard.py",
            {"tool_name": tool_name, "tool_input": {"file_path": target}},
            env,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        output = payload["hookSpecificOutput"]
        assert output["decision"] == "block"
        assert "canonical topics store" in output["reason"]

    result = _run_hook(
        "deploy/hooks/aitp-routing-guard.py",
        {"tool_name": "Write", "tool_input": {"file_path": "notes/ordinary.md"}},
        env,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_project_hook_configs_use_stable_python_and_multiedit_matcher():
    for rel in ["deploy/config/hooks.json", "deploy/config/codex-hooks.json"]:
        config = json.loads(_read(rel))
        pre_tool = config["hooks"]["PreToolUse"][0]
        command = pre_tool["hooks"][0]["command"]
        assert pre_tool["matcher"] == "Write|Edit|MultiEdit"
        assert "{{PYTHON_EXE}}" in command
        assert "uv" not in command.lower()


def test_codex_project_install_writes_lightweight_hooks_and_hooks_json(tmp_path):
    pm = _load_pm()
    workspace = tmp_path / "Theoretical-Physics"
    topics = workspace / "research" / "aitp-topics"
    topics.mkdir(parents=True)
    variables = pm._build_variables(str(topics), str(workspace))

    deployed = pm._deploy_codex_app("project", workspace, variables, remove=False)

    hooks_dir = workspace / ".codex" / "hooks"
    hooks_json = workspace / ".codex" / "hooks.json"
    assert str(hooks_dir / "aitp-keyword-router.py") in deployed
    assert str(hooks_dir / "aitp-routing-guard.py") in deployed
    assert hooks_json.exists()
    config = json.loads(hooks_json.read_text(encoding="utf-8"))
    pre_tool = config["hooks"]["PreToolUse"][0]
    commands = [
        hook["command"]
        for entries in config["hooks"].values()
        for entry in entries
        for hook in entry["hooks"]
    ]
    assert pre_tool["matcher"] == "Write|Edit|MultiEdit"
    assert any("aitp-keyword-router.py" in command for command in commands)
    assert any("aitp-routing-guard.py" in command for command in commands)
    assert all(str(workspace).replace("\\", "/") in command for command in commands)
    assert all(".cache/codex-runtimes" not in command.replace("\\", "/").lower() for command in commands)
    mcp = json.loads((workspace / ".codex" / "mcp.json").read_text(encoding="utf-8"))
    assert mcp["mcpServers"]["aitp"]["env"]["AITP_MCP_SURFACE"] == "codex"
    config_toml = (workspace / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert 'AITP_MCP_SURFACE = "codex"' in config_toml


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
