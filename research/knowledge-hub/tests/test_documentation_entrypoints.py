from __future__ import annotations

from pathlib import Path
import unittest


class DocumentationEntrypointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[3]

    def test_root_readme_links_to_install_index_and_public_roadmap(self) -> None:
        readme = (self.repo_root / "README.md").read_text(encoding="utf-8")
        install_doc = self.repo_root / "docs" / "INSTALL.md"
        roadmap_doc = self.repo_root / "docs" / "roadmap.md"

        self.assertTrue(install_doc.exists())
        self.assertTrue(roadmap_doc.exists())
        self.assertIn("docs/INSTALL.md", readme)
        self.assertIn("docs/roadmap.md", readme)

    def test_install_index_consolidates_runtime_paths_and_python_floor(self) -> None:
        install_doc = (self.repo_root / "docs" / "INSTALL.md").read_text(encoding="utf-8")

        self.assertIn("Python 3.10+", install_doc)
        self.assertIn("python -m pip install -e research/knowledge-hub", install_doc)
        self.assertIn("docs/INSTALL_CODEX.md", install_doc)
        self.assertIn("docs/INSTALL_OPENCODE.md", install_doc)
        self.assertIn("docs/INSTALL_CLAUDE_CODE.md", install_doc)
        self.assertIn("docs/INSTALL_OPENCLAW.md", install_doc)
        self.assertIn("docs/MIGRATE_LOCAL_INSTALL.md", install_doc)
        self.assertIn("docs/UNINSTALL.md", install_doc)

    def test_public_roadmap_doc_stays_public_facing_and_avoids_planning_noise(self) -> None:
        roadmap_doc = (self.repo_root / "docs" / "roadmap.md").read_text(encoding="utf-8")

        self.assertIn("public-facing roadmap summary", roadmap_doc)
        self.assertIn("docs/design-principles.md", roadmap_doc)
        self.assertIn("maintainer-facing planning state", roadmap_doc)
        self.assertNotIn(".planning/PROJECT.md", roadmap_doc)
        self.assertNotIn(".planning/ROADMAP.md", roadmap_doc)


if __name__ == "__main__":
    unittest.main()
