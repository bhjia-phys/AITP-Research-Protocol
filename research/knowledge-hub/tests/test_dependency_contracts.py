from __future__ import annotations

import unittest
from pathlib import Path


class DependencyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.kernel_root = Path(__file__).resolve().parents[1]

    def test_runtime_requirements_use_bounded_version_ranges(self) -> None:
        requirements = (self.kernel_root / "requirements.txt").read_text(encoding="utf-8").splitlines()
        normalized = [line.strip() for line in requirements if line.strip() and not line.strip().startswith("#")]

        self.assertIn("mcp>=1.0.0,<2.0.0", normalized)
        self.assertIn("jsonschema>=4.0.0,<5.0.0", normalized)

    def test_setup_reads_runtime_requirements_file_directly(self) -> None:
        setup_text = (self.kernel_root / "setup.py").read_text(encoding="utf-8")

        self.assertIn('ROOT / "requirements.txt"', setup_text)
        self.assertIn("install_requires=REQUIREMENTS", setup_text)
        self.assertIn('python_requires=">=3.10"', setup_text)

    def test_install_docs_reference_bounded_dependency_policy_and_acceptance(self) -> None:
        kernel_readme = (self.kernel_root / "README.md").read_text(encoding="utf-8")
        codex_install = (self.kernel_root.parents[1] / "docs" / "INSTALL_CODEX.md").read_text(encoding="utf-8")
        claude_install = (self.kernel_root.parents[1] / "docs" / "INSTALL_CLAUDE_CODE.md").read_text(encoding="utf-8")
        opencode_install = (self.kernel_root.parents[1] / "docs" / "INSTALL_OPENCODE.md").read_text(encoding="utf-8")

        self.assertIn("bounded version ranges", kernel_readme)
        self.assertIn("run_dependency_contract_acceptance.py", kernel_readme)
        self.assertIn("requirements.txt", codex_install)
        self.assertIn("bounded", codex_install)
        self.assertIn("bounded", claude_install)
        self.assertIn("bounded", opencode_install)

    def test_dependency_acceptance_script_exists_and_inspects_wheel_metadata(self) -> None:
        script = (self.kernel_root / "runtime" / "scripts" / "run_dependency_contract_acceptance.py").read_text(encoding="utf-8")

        self.assertIn("pip", script)
        self.assertIn("wheel", script)
        self.assertIn("Requires-Dist", script)
        self.assertIn("Requires-Python", script)


if __name__ == "__main__":
    unittest.main()
