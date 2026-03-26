from __future__ import annotations

import json
from pathlib import Path
import unittest


class AgentBootstrapAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[3]

    def test_repo_skills_expose_superpowers_style_gatekeeper(self) -> None:
        using_skill = (self.repo_root / "skills" / "using-aitp" / "SKILL.md").read_text(encoding="utf-8")
        runtime_skill = (self.repo_root / "skills" / "aitp-runtime" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("continue this topic", using_skill)
        self.assertIn("validation planning", using_skill)
        self.assertNotIn("aitp-codex", using_skill)
        self.assertIn("runtime_protocol.generated.md", runtime_skill)
        self.assertIn("session_start.generated.md", runtime_skill)

    def test_opencode_plugin_assets_exist(self) -> None:
        package_payload = json.loads((self.repo_root / "package.json").read_text(encoding="utf-8"))
        plugin_text = (self.repo_root / ".opencode" / "plugins" / "aitp.js").read_text(encoding="utf-8")

        self.assertEqual(package_payload["main"], ".opencode/plugins/aitp.js")
        self.assertIn("experimental.chat.system.transform", plugin_text)
        self.assertIn("config.skills.paths", plugin_text)
        self.assertIn("using-aitp", plugin_text)

    def test_claude_bootstrap_assets_exist(self) -> None:
        plugin_payload = json.loads((self.repo_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        hook_payload = json.loads((self.repo_root / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        hook_text = (self.repo_root / "hooks" / "session-start").read_text(encoding="utf-8")

        self.assertEqual(plugin_payload["name"], "aitp")
        self.assertIn("SessionStart", hook_payload["hooks"])
        self.assertIn("run-hook.cmd", json.dumps(hook_payload))
        self.assertIn("using-aitp", hook_text)

    def test_codex_install_doc_points_to_skill_discovery(self) -> None:
        install_doc = (self.repo_root / ".codex" / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("~/.agents/skills/aitp", install_doc)
        self.assertIn("native skill discovery", install_doc)
        self.assertNotIn("aitp-codex", install_doc)


if __name__ == "__main__":
    unittest.main()
