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
        self.assertIn("Do not expose protocol jargon", using_skill)
        self.assertIn("report the current human-control posture", using_skill)
        self.assertIn("ritual permission", using_skill)
        self.assertNotIn("aitp-codex", using_skill)
        self.assertIn("runtime_protocol.generated.md", runtime_skill)
        self.assertIn("session_start.generated.md", runtime_skill)
        self.assertIn("Do not say things like", runtime_skill)
        self.assertIn("human-control posture", runtime_skill)
        self.assertIn("iterative verify", runtime_skill.lower())
        self.assertIn("ritual permission", runtime_skill)

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
        python_hook_text = (self.repo_root / "hooks" / "session-start.py").read_text(encoding="utf-8")
        run_hook_text = (self.repo_root / "hooks" / "run-hook.cmd").read_text(encoding="utf-8")

        self.assertEqual(plugin_payload["name"], "aitp")
        self.assertEqual(plugin_payload["entry"], "skills/using-aitp/SKILL.md")
        self.assertIn("SessionStart", plugin_payload["hooks"])
        self.assertIn("SessionStart", hook_payload["hooks"])
        self.assertIn("run-hook.cmd", json.dumps(hook_payload))
        self.assertIn("using-aitp", hook_text)
        self.assertIn("hookSpecificOutput", python_hook_text)
        self.assertIn("PYTHON_HOOK", run_hook_text)

    def test_codex_install_doc_points_to_skill_discovery(self) -> None:
        install_doc = (self.repo_root / ".codex" / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("~/.agents/skills/aitp", install_doc)
        self.assertIn("native skill discovery", install_doc)
        self.assertIn("plugin-first-equivalent", install_doc)
        self.assertIn("aitp doctor", install_doc)
        self.assertIn("QUICKSTART.md", install_doc)
        self.assertIn("mklink /J", install_doc)
        self.assertIn("install-agent --agent codex --scope user", install_doc)
        self.assertIn("aitp interaction --topic-slug <topic_slug> --json", install_doc)
        self.assertIn("aitp resolve-decision", install_doc)
        self.assertIn("aitp resolve-checkpoint", install_doc)
        self.assertNotIn("aitp-codex", install_doc)

    def test_opencode_install_doc_points_to_shared_quickstart(self) -> None:
        install_doc = (self.repo_root / ".opencode" / "INSTALL.md").read_text(encoding="utf-8")
        readme_doc = (self.repo_root / "docs" / "README.opencode.md").read_text(encoding="utf-8")

        self.assertIn("aitp doctor", install_doc)
        self.assertIn("runtime_support_matrix.runtimes.opencode", install_doc)
        self.assertIn("QUICKSTART.md", install_doc)
        self.assertIn("run_runtime_parity_acceptance.py --runtime opencode --json", install_doc)
        self.assertIn("QUICKSTART.md", readme_doc)
        self.assertIn("run_runtime_parity_acceptance.py --runtime opencode --json", readme_doc)

    def test_readme_links_to_user_topic_journey(self) -> None:
        readme = (self.repo_root / "README.md").read_text(encoding="utf-8")
        journey_doc = (self.repo_root / "docs" / "USER_TOPIC_JOURNEY.md").read_text(encoding="utf-8")
        quickstart_doc = (self.repo_root / "docs" / "QUICKSTART.md").read_text(encoding="utf-8")
        publish_doc = (self.repo_root / "docs" / "PUBLISH_PYPI.md").read_text(encoding="utf-8")

        self.assertIn("docs/USER_TOPIC_JOURNEY.md", readme)
        self.assertIn("docs/QUICKSTART.md", readme)
        self.assertIn("docs/PUBLISH_PYPI.md", readme)
        self.assertIn("python -m pip install aitp-kernel", readme)
        self.assertIn("native Claude", readme)
        self.assertIn("AITP MCP registration", readme)
        self.assertIn("Lane 1: Formal theory topic", journey_doc)
        self.assertIn("Lane 2: Toy numerics topic", journey_doc)
        self.assertIn("Lane 3: Code-backed method topic", journey_doc)
        self.assertIn("python -m pip install aitp-kernel", quickstart_doc)
        self.assertIn("bootstrap", quickstart_doc)
        self.assertIn("loop", quickstart_doc)
        self.assertIn("status", quickstart_doc)
        self.assertIn("Codex", quickstart_doc)
        self.assertIn("Claude Code", quickstart_doc)
        self.assertIn("OpenCode", quickstart_doc)
        self.assertIn("python -m build research/knowledge-hub", publish_doc)

    def test_readmes_link_to_aitp_gsd_workflow_contract(self) -> None:
        root_readme = (self.repo_root / "README.md").read_text(encoding="utf-8")
        kernel_readme = (self.repo_root / "research" / "knowledge-hub" / "README.md").read_text(encoding="utf-8")
        workflow_contract = (self.repo_root / "docs" / "AITP_GSD_WORKFLOW_CONTRACT.md").read_text(encoding="utf-8")

        self.assertIn("docs/AITP_GSD_WORKFLOW_CONTRACT.md", root_readme)
        self.assertIn("../docs/AITP_GSD_WORKFLOW_CONTRACT.md", kernel_readme)
        self.assertIn("AITP governs research topics. GSD governs implementation of AITP itself.", workflow_contract)

    def test_runtime_support_docs_publish_baseline_and_parity_language(self) -> None:
        root_readme = (self.repo_root / "README.md").read_text(encoding="utf-8")
        install_index = (self.repo_root / "docs" / "INSTALL.md").read_text(encoding="utf-8")
        codex_install = (self.repo_root / "docs" / "INSTALL_CODEX.md").read_text(encoding="utf-8")
        claude_install = (self.repo_root / "docs" / "INSTALL_CLAUDE_CODE.md").read_text(encoding="utf-8")
        opencode_install = (self.repo_root / "docs" / "INSTALL_OPENCODE.md").read_text(encoding="utf-8")
        migrate_doc = (self.repo_root / "docs" / "MIGRATE_LOCAL_INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("Current baseline", root_readme)
        self.assertIn("Parity target", root_readme)
        self.assertIn("Specialized lane", root_readme)
        self.assertIn("front-door readiness only", root_readme)
        self.assertIn("deep_execution_parity", root_readme)
        self.assertIn("aitp doctor --json", root_readme)
        self.assertIn("runtime_convergence", root_readme)
        self.assertIn("full_convergence_repair", root_readme)
        self.assertIn("runtime_support_matrix.runtimes.<runtime>.remediation", root_readme)
        self.assertIn("scripts\\aitp-local.cmd bootstrap", root_readme)
        self.assertIn("scripts\\aitp-local.cmd doctor", install_index)
        self.assertIn("runtime_convergence.front_door_runtimes_converged", install_index)
        self.assertIn("runtime_support_matrix.deep_execution_parity.runtimes.<runtime>.status", install_index)
        self.assertIn("runtime_support_matrix.runtimes.<runtime>.remediation", install_index)
        self.assertIn("current baseline runtime", codex_install)
        self.assertIn("runtime_support_matrix.runtimes.codex.remediation", codex_install)
        self.assertIn("Get-ChildItem \"$env:USERPROFILE\\.agents\\skills\"", codex_install)
        self.assertIn("aitp install-agent --agent codex --scope user", codex_install)
        self.assertIn("scripts\\aitp-local.cmd install-agent --agent codex --scope project --target-root D:\\theory-workspace", codex_install)
        self.assertIn("scripts\\aitp-local.cmd install-agent --agent codex --scope user", codex_install)
        self.assertIn("aitp doctor --json", claude_install)
        self.assertIn("runtime_support_matrix.runtimes.claude_code.remediation", claude_install)
        self.assertIn("runtime_support_matrix.deep_execution_parity.runtimes.claude_code.status", claude_install)
        self.assertIn("probe_available", claude_install)
        self.assertIn("run_runtime_parity_acceptance.py --runtime claude_code --json", claude_install)
        self.assertIn("aitp install-agent --agent claude-code --scope user", claude_install)
        self.assertIn("aitp interaction --topic-slug <topic_slug> --json", claude_install)
        self.assertIn("aitp resolve-decision", claude_install)
        self.assertIn("aitp resolve-checkpoint", claude_install)
        self.assertIn("scripts\\aitp-local.cmd install-agent --agent claude-code --scope project --target-root D:\\theory-workspace", claude_install)
        self.assertIn("scripts\\aitp-local.cmd install-agent --agent claude-code --scope user", claude_install)
        self.assertIn("session-start.py", claude_install)
        self.assertIn(".claude.json", claude_install)
        self.assertIn(".mcp.json", claude_install)
        self.assertIn("claude mcp list", claude_install)
        self.assertIn("aitp doctor --json", opencode_install)
        self.assertIn("runtime_support_matrix.runtimes.opencode.remediation", opencode_install)
        self.assertIn("runtime_support_matrix.deep_execution_parity.runtimes.opencode.status", opencode_install)
        self.assertIn("probe_available", opencode_install)
        self.assertIn("run_runtime_parity_acceptance.py --runtime opencode --json", opencode_install)
        self.assertIn("%USERPROFILE%\\.config\\opencode\\opencode.json", opencode_install)
        self.assertIn("aitp install-agent --agent opencode --scope user", opencode_install)
        self.assertIn("aitp interaction --topic-slug <topic_slug> --json", opencode_install)
        self.assertIn("aitp resolve-decision", opencode_install)
        self.assertIn("aitp resolve-checkpoint", opencode_install)
        self.assertIn("scripts\\aitp-local.cmd install-agent --agent opencode --scope project --target-root D:\\theory-workspace", opencode_install)
        self.assertIn("scripts\\aitp-local.cmd install-agent --agent opencode --scope user", opencode_install)
        self.assertIn("runtime_convergence_after.front_door_runtimes_converged", migrate_doc)

    def test_runtime_parity_harness_is_documented_in_runtime_docs(self) -> None:
        runtime_readme = (self.repo_root / "research" / "knowledge-hub" / "runtime" / "README.md").read_text(encoding="utf-8")
        runbook = (self.repo_root / "research" / "knowledge-hub" / "runtime" / "AITP_TEST_RUNBOOK.md").read_text(encoding="utf-8")

        self.assertIn("run_runtime_parity_acceptance.py", runtime_readme)
        self.assertIn("run_runtime_parity_acceptance.py", runbook)
        self.assertIn("run_runtime_parity_audit.py", runtime_readme)
        self.assertIn("run_runtime_parity_audit.py", runbook)
        self.assertIn("deep-execution parity", runtime_readme)
        self.assertIn("Codex baseline", runbook)
        self.assertIn("--runtime claude_code --json", runtime_readme)
        self.assertIn("--runtime opencode --json", runtime_readme)
        self.assertIn("--live-evidence-root", runtime_readme)
        self.assertIn("--live-evidence-root", runbook)
        self.assertIn("runtime-live-first-turn-evidence.schema.json", runtime_readme)
        self.assertIn("runtime_live_first_turn_evidence", runbook)
        self.assertIn("probe_completed_with_gap", runbook)
        self.assertIn("falls_short_of_codex_baseline", runbook)
        self.assertIn("equivalent_surfaces", runbook)
        self.assertIn("open_gaps", runbook)

    def test_control_plane_docs_publish_audit_entrypoints_and_doctor_fields(self) -> None:
        root_readme = (self.repo_root / "README.md").read_text(encoding="utf-8")
        kernel_readme = (self.repo_root / "research" / "knowledge-hub" / "README.md").read_text(encoding="utf-8")
        codex_install = (self.repo_root / "docs" / "INSTALL_CODEX.md").read_text(encoding="utf-8")
        claude_install = (self.repo_root / "docs" / "INSTALL_CLAUDE_CODE.md").read_text(encoding="utf-8")
        opencode_install = (self.repo_root / "docs" / "INSTALL_OPENCODE.md").read_text(encoding="utf-8")

        self.assertIn("aitp capability-audit --topic-slug <topic_slug>", root_readme)
        self.assertIn("aitp paired-backend-audit --topic-slug <topic_slug>", root_readme)
        self.assertIn("aitp h-plane-audit --topic-slug <topic_slug>", root_readme)
        self.assertIn("aitp paired-backend-audit --topic-slug <topic_slug>", kernel_readme)
        self.assertIn("aitp h-plane-audit --topic-slug <topic_slug>", kernel_readme)
        self.assertIn("control_plane_contracts", codex_install)
        self.assertIn("control_plane_surfaces", codex_install)
        self.assertIn("control_plane_contracts", claude_install)
        self.assertIn("control_plane_surfaces", claude_install)
        self.assertIn("control_plane_contracts", opencode_install)
        self.assertIn("control_plane_surfaces", opencode_install)

    def test_kernel_boundary_docs_reference_extracted_modules(self) -> None:
        kernel_readme = (self.repo_root / "research" / "knowledge-hub" / "README.md").read_text(encoding="utf-8")
        architecture_doc = (self.repo_root / "docs" / "architecture.md").read_text(encoding="utf-8")

        self.assertIn("frontdoor_support.py", kernel_readme)
        self.assertIn("agent_install_support.py", kernel_readme)
        self.assertIn("kernel_templates.py", kernel_readme)
        self.assertIn("kernel_markdown_renderers.py", kernel_readme)
        self.assertIn("runtime_bundle_support.py", kernel_readme)
        self.assertIn("topic_shell_support.py", kernel_readme)
        self.assertIn("followup_support.py", kernel_readme)
        self.assertIn("cli_frontdoor_handler.py", kernel_readme)
        self.assertIn("control_plane_support.py", kernel_readme)
        self.assertIn("paired_backend_support.py", kernel_readme)
        self.assertIn("h_plane_support.py", kernel_readme)
        self.assertIn("frontdoor_support.py", architecture_doc)
        self.assertIn("agent_install_support.py", architecture_doc)
        self.assertIn("kernel_templates.py", architecture_doc)
        self.assertIn("kernel_markdown_renderers.py", architecture_doc)
        self.assertIn("runtime_bundle_support.py", architecture_doc)
        self.assertIn("topic_shell_support.py", architecture_doc)
        self.assertIn("followup_support.py", architecture_doc)
        self.assertIn("cli_frontdoor_handler.py", architecture_doc)
        self.assertIn("control_plane_support.py", architecture_doc)
        self.assertIn("paired_backend_support.py", architecture_doc)
        self.assertIn("h_plane_support.py", architecture_doc)

    def test_multi_topic_runtime_docs_are_linked_and_present(self) -> None:
        root_readme = (self.repo_root / "README.md").read_text(encoding="utf-8")
        kernel_readme = (self.repo_root / "research" / "knowledge-hub" / "README.md").read_text(encoding="utf-8")
        runtime_readme = (self.repo_root / "research" / "knowledge-hub" / "runtime" / "README.md").read_text(encoding="utf-8")
        multi_topic_doc = (self.repo_root / "docs" / "MULTI_TOPIC_RUNTIME.md").read_text(encoding="utf-8")
        migration_doc = (self.repo_root / "docs" / "MIGRATE_MULTI_TOPIC.md").read_text(encoding="utf-8")

        self.assertIn("docs/MULTI_TOPIC_RUNTIME.md", root_readme)
        self.assertIn("docs/MIGRATE_MULTI_TOPIC.md", root_readme)
        self.assertIn("../docs/MULTI_TOPIC_RUNTIME.md", kernel_readme)
        self.assertIn("../docs/MIGRATE_MULTI_TOPIC.md", kernel_readme)
        self.assertIn("active_topics.json", runtime_readme)
        self.assertIn("aitp focus-topic", runtime_readme)
        self.assertIn("authoritative registry", multi_topic_doc)
        self.assertIn("current_topic.json", migration_doc)

    def test_l5_publication_factory_protocol_is_linked_and_present(self) -> None:
        root_readme = (self.repo_root / "README.md").read_text(encoding="utf-8")
        kernel_readme = (self.repo_root / "research" / "knowledge-hub" / "README.md").read_text(encoding="utf-8")
        protocol_doc = (
            self.repo_root / "research" / "knowledge-hub" / "L5_PUBLICATION_FACTORY_PROTOCOL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("research/knowledge-hub/L5_PUBLICATION_FACTORY_PROTOCOL.md", root_readme)
        self.assertIn("L5_PUBLICATION_FACTORY_PROTOCOL.md", kernel_readme)
        self.assertIn("`L5` is not a new scientific-truth layer", protocol_doc)
        self.assertIn("publication_intent", protocol_doc)


if __name__ == "__main__":
    unittest.main()
