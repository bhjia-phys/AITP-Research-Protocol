from __future__ import annotations

import unittest
from pathlib import Path


class L1MethodSpecificityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel_root = Path(__file__).resolve().parents[1]
        self.repo_root = self.kernel_root.parents[1]

    def test_method_specificity_acceptance_and_status_surface_are_documented(self) -> None:
        root_readme = (self.repo_root / "README.md").read_text(encoding="utf-8")
        kernel_readme = (self.kernel_root / "README.md").read_text(encoding="utf-8")
        runtime_readme = (self.kernel_root / "runtime" / "README.md").read_text(encoding="utf-8")
        runbook = (self.kernel_root / "runtime" / "AITP_TEST_RUNBOOK.md").read_text(encoding="utf-8")

        self.assertIn("run_l1_method_specificity_acceptance.py", root_readme)
        self.assertIn("run_l1_method_specificity_acceptance.py", kernel_readme)
        self.assertIn("run_l1_method_specificity_acceptance.py", runtime_readme)
        self.assertIn("run_l1_method_specificity_acceptance.py", runbook)
        self.assertIn("method_specificity_rows", runtime_readme)
        self.assertIn("method_specificity_rows", runbook)

    def test_acceptance_script_covers_status_runtime_surface(self) -> None:
        script = (
            self.kernel_root / "runtime" / "scripts" / "run_l1_method_specificity_acceptance.py"
        ).read_text(encoding="utf-8")

        self.assertIn("status", script)
        self.assertIn("method_specificity_rows", script)
        self.assertIn("research_question.contract.md", script)


if __name__ == "__main__":
    unittest.main()
