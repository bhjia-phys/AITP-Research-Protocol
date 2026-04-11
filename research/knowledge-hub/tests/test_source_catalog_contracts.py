from __future__ import annotations

import unittest
from pathlib import Path


class SourceCatalogContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel_root = Path(__file__).resolve().parents[1]
        self.repo_root = self.kernel_root.parents[1]

    def test_source_catalog_commands_and_acceptance_are_documented(self) -> None:
        root_readme = (self.repo_root / "README.md").read_text(encoding="utf-8")
        kernel_readme = (self.kernel_root / "README.md").read_text(encoding="utf-8")
        runtime_readme = (self.kernel_root / "runtime" / "README.md").read_text(encoding="utf-8")
        runbook = (self.kernel_root / "runtime" / "AITP_TEST_RUNBOOK.md").read_text(encoding="utf-8")
        source_layer_readme = (self.kernel_root / "source-layer" / "README.md").read_text(encoding="utf-8")

        self.assertIn("aitp compile-source-catalog", root_readme)
        self.assertIn("aitp trace-source-citations", root_readme)
        self.assertIn("aitp compile-source-family", root_readme)
        self.assertIn("aitp export-source-bibtex", root_readme)
        self.assertIn("aitp import-bibtex-sources", root_readme)
        self.assertIn("aitp compile-source-catalog", kernel_readme)
        self.assertIn("aitp trace-source-citations", kernel_readme)
        self.assertIn("aitp compile-source-family", kernel_readme)
        self.assertIn("aitp export-source-bibtex", kernel_readme)
        self.assertIn("aitp import-bibtex-sources", kernel_readme)
        self.assertIn("run_source_catalog_acceptance.py", runtime_readme)
        self.assertIn("run_source_catalog_acceptance.py", runbook)
        self.assertIn("source_catalog.json|md", runtime_readme)
        self.assertIn("source_catalog.json|md", runbook)
        self.assertIn("citation_traversals/", source_layer_readme)
        self.assertIn("source_families/", source_layer_readme)
        self.assertIn("bibtex_exports/", source_layer_readme)
        self.assertIn("bibtex_imports/", source_layer_readme)

    def test_source_catalog_acceptance_script_covers_runtime_and_catalog_surfaces(self) -> None:
        script = (
            self.kernel_root / "runtime" / "scripts" / "run_source_catalog_acceptance.py"
        ).read_text(encoding="utf-8")

        self.assertIn("compile-source-catalog", script)
        self.assertIn("trace-source-citations", script)
        self.assertIn("compile-source-family", script)
        self.assertIn("export-source-bibtex", script)
        self.assertIn("import-bibtex-sources", script)
        self.assertIn("status", script)
        self.assertIn("fidelity_summary", script)


if __name__ == "__main__":
    unittest.main()
