from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


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
