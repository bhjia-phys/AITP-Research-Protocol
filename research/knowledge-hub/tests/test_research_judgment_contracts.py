from __future__ import annotations

import unittest
from pathlib import Path


class ResearchJudgmentContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel_root = Path(__file__).resolve().parents[1]
        self.repo_root = self.kernel_root.parents[1]

    def test_runtime_docs_and_runbook_reference_judgment_surfaces_and_acceptance(self) -> None:
        kernel_readme = (self.kernel_root / "README.md").read_text(encoding="utf-8")
        runtime_readme = (self.kernel_root / "runtime" / "README.md").read_text(encoding="utf-8")
        runbook = (self.kernel_root / "runtime" / "AITP_TEST_RUNBOOK.md").read_text(encoding="utf-8")

        self.assertIn("aitp analytical-review", kernel_readme)
        self.assertIn("research_judgment.active.json", runtime_readme)
        self.assertIn("research_judgment.active.md", runtime_readme)
        self.assertIn("run_analytical_judgment_surface_acceptance.py", runtime_readme)
        self.assertIn("run_analytical_judgment_surface_acceptance.py", runbook)
        self.assertIn("research_judgment.active.json|md", runbook)

    def test_judgment_acceptance_script_exists_and_exercises_cli_surfaces(self) -> None:
        script = (
            self.kernel_root / "runtime" / "scripts" / "run_analytical_judgment_surface_acceptance.py"
        ).read_text(encoding="utf-8")

        self.assertIn("analytical-review", script)
        self.assertIn("\"verify\"", script)
        self.assertIn("\"status\"", script)
        self.assertIn("research_judgment", script)
        self.assertIn("validation_review_bundle", script)


if __name__ == "__main__":
    unittest.main()
