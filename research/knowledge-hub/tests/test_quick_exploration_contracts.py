from __future__ import annotations

import unittest
from pathlib import Path


class QuickExplorationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel_root = Path(__file__).resolve().parents[1]

    def test_docs_and_runbook_reference_explore_path_and_acceptance(self) -> None:
        kernel_readme = (self.kernel_root / "README.md").read_text(encoding="utf-8")
        runtime_readme = (self.kernel_root / "runtime" / "README.md").read_text(encoding="utf-8")
        runbook = (self.kernel_root / "runtime" / "AITP_TEST_RUNBOOK.md").read_text(encoding="utf-8")

        self.assertIn("aitp explore", kernel_readme)
        self.assertIn("promote-exploration", kernel_readme)
        self.assertIn("runtime/explorations/", runtime_readme)
        self.assertIn("run_quick_exploration_acceptance.py", runtime_readme)
        self.assertIn("run_quick_exploration_acceptance.py", runbook)
        self.assertIn("promote-exploration", runbook)

    def test_quick_exploration_acceptance_script_exists_and_exercises_cli_surfaces(self) -> None:
        script = (
            self.kernel_root / "runtime" / "scripts" / "run_quick_exploration_acceptance.py"
        ).read_text(encoding="utf-8")

        self.assertIn("\"explore\"", script)
        self.assertIn("\"promote-exploration\"", script)
        self.assertIn("artifact_footprint", script)
        self.assertIn("promotion_request_path", script)


if __name__ == "__main__":
    unittest.main()
