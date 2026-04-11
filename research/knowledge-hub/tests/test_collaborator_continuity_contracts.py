from __future__ import annotations

import unittest
from pathlib import Path


class CollaboratorContinuityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel_root = Path(__file__).resolve().parents[1]

    def test_runtime_docs_and_runbook_reference_continuity_surfaces_and_acceptance(self) -> None:
        kernel_readme = (self.kernel_root / "README.md").read_text(encoding="utf-8")
        runtime_readme = (self.kernel_root / "runtime" / "README.md").read_text(encoding="utf-8")
        runbook = (self.kernel_root / "runtime" / "AITP_TEST_RUNBOOK.md").read_text(encoding="utf-8")

        self.assertIn("collaborator_profile.active.json", runtime_readme)
        self.assertIn("research_trajectory.active.json", runtime_readme)
        self.assertIn("mode_learning.active.json", runtime_readme)
        self.assertIn("run_collaborator_continuity_acceptance.py", runtime_readme)
        self.assertIn("run_collaborator_continuity_acceptance.py", runbook)
        self.assertIn("collaborator_profile.active.json|md", runbook)
        self.assertIn("mode_learning.active.json|md", runbook)
        self.assertIn("session-start", kernel_readme)

    def test_continuity_acceptance_script_exists_and_exercises_cli_surfaces(self) -> None:
        script = (
            self.kernel_root / "runtime" / "scripts" / "run_collaborator_continuity_acceptance.py"
        ).read_text(encoding="utf-8")

        self.assertIn("\"focus-topic\"", script)
        self.assertIn("\"status\"", script)
        self.assertIn("\"current-topic\"", script)
        self.assertIn("\"session-start\"", script)
        self.assertIn("collaborator_profile", script)
        self.assertIn("research_trajectory", script)
        self.assertIn("mode_learning", script)


if __name__ == "__main__":
    unittest.main()
