from __future__ import annotations

import unittest
from pathlib import Path


class QuickstartContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel_root = Path(__file__).resolve().parents[1]
        self.repo_root = self.kernel_root.parents[1]

    def test_quickstart_docs_and_runtime_docs_reference_first_run_acceptance(self) -> None:
        install_doc = (self.repo_root / "docs" / "INSTALL.md").read_text(encoding="utf-8")
        quickstart_doc = (self.repo_root / "docs" / "QUICKSTART.md").read_text(encoding="utf-8")
        runtime_readme = (self.kernel_root / "runtime" / "README.md").read_text(encoding="utf-8")
        runbook = (self.kernel_root / "runtime" / "AITP_TEST_RUNBOOK.md").read_text(encoding="utf-8")

        self.assertIn("QUICKSTART.md", install_doc)
        self.assertIn("bootstrap", quickstart_doc)
        self.assertIn("loop", quickstart_doc)
        self.assertIn("status", quickstart_doc)
        self.assertIn("scripts\\aitp-local.cmd bootstrap", quickstart_doc)
        self.assertIn("scripts\\aitp-local.cmd loop", quickstart_doc)
        self.assertIn("scripts\\aitp-local.cmd status", quickstart_doc)
        self.assertIn("install-agent --agent codex --scope user", quickstart_doc)
        self.assertIn("run_first_run_topic_acceptance.py", runtime_readme)
        self.assertIn("run_first_run_topic_acceptance.py", runbook)
        self.assertIn("bootstrap -> loop -> status", runtime_readme)
        self.assertIn("bootstrap --json", runbook)

    def test_first_run_acceptance_script_exists_and_exercises_cli_surfaces(self) -> None:
        script = (
            self.kernel_root / "runtime" / "scripts" / "run_first_run_topic_acceptance.py"
        ).read_text(encoding="utf-8")

        self.assertIn("\"bootstrap\"", script)
        self.assertIn("\"loop\"", script)
        self.assertIn("\"status\"", script)
        self.assertIn("TOPIC_SLUG", script)
        self.assertIn("loop_state_path", script)


if __name__ == "__main__":
    unittest.main()
