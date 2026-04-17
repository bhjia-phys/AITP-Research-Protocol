from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.source_bibtex_support import (
    import_bibtex_sources,
    materialize_source_bibtex_export,
)


class SourceBibtexSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.kernel_root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_source_row(
        self,
        *,
        topic_slug: str,
        source_id: str,
        source_type: str,
        title: str,
        summary: str,
        canonical_source_id: str,
        references: list[str] | None = None,
        provenance: dict[str, object] | None = None,
    ) -> None:
        path = self.kernel_root / "topics" / topic_slug / "L0" / "source_index.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        payload = {
            "source_id": source_id,
            "source_type": source_type,
            "title": title,
            "summary": summary,
            "canonical_source_id": canonical_source_id,
            "references": list(references or []),
            "provenance": provenance
            or {
                "abs_url": f"https://example.org/{topic_slug}/{source_id.replace(':', '-')}",
            },
        }
        path.write_text(existing + json.dumps(payload, ensure_ascii=True) + "\n", encoding="utf-8")

    def test_materialize_source_bibtex_export_writes_seed_and_neighbor_entries(self) -> None:
        self._write_source_row(
            topic_slug="topic-a",
            source_id="paper:shared-a",
            source_type="paper",
            title="Shared paper",
            summary="Shared source summary.",
            canonical_source_id="source_identity:doi:10-1000-shared-paper",
            references=["doi:10-1000-neighbor-paper"],
            provenance={
                "doi": "10.1000/shared-paper",
                "authors": ["Ada Lovelace", "Emmy Noether"],
                "year": "1937",
                "journal": "Journal of Shared Papers",
                "abs_url": "https://doi.org/10.1000/shared-paper",
            },
        )
        self._write_source_row(
            topic_slug="topic-b",
            source_id="paper:neighbor",
            source_type="paper",
            title="Neighbor paper",
            summary="Neighbor source summary.",
            canonical_source_id="source_identity:doi:10-1000-neighbor-paper",
            references=["doi:10-1000-shared-paper"],
            provenance={
                "doi": "10.1000/neighbor-paper",
                "authors": ["Chen Ning Yang"],
                "year": "1941",
                "journal": "Neighbor Letters",
                "abs_url": "https://doi.org/10.1000/neighbor-paper",
            },
        )

        result = materialize_source_bibtex_export(
            self.kernel_root,
            canonical_source_id="source_identity:doi:10-1000-shared-paper",
            include_neighbors=True,
        )

        payload = result["payload"]
        self.assertTrue(Path(result["json_path"]).exists())
        self.assertTrue(Path(result["markdown_path"]).exists())
        self.assertTrue(Path(result["bibtex_path"]).exists())
        self.assertEqual(payload["seed"]["canonical_source_id"], "source_identity:doi:10-1000-shared-paper")
        self.assertEqual(payload["summary"]["entry_count"], 2)
        self.assertEqual(payload["summary"]["included_neighbor_count"], 1)

        bibtex_text = Path(result["bibtex_path"]).read_text(encoding="utf-8")
        self.assertIn("@article{doi-10-1000-shared-paper,", bibtex_text)
        self.assertIn("title = {Shared paper}", bibtex_text)
        self.assertIn("doi = {10.1000/shared-paper}", bibtex_text)
        self.assertIn("@article{doi-10-1000-neighbor-paper,", bibtex_text)

    def test_import_bibtex_sources_appends_rows_and_reports_duplicates(self) -> None:
        self._write_source_row(
            topic_slug="demo-topic",
            source_id="paper:existing",
            source_type="paper",
            title="Existing paper",
            summary="Already registered source.",
            canonical_source_id="source_identity:doi:10-1000-existing-paper",
            provenance={
                "doi": "10.1000/existing-paper",
                "abs_url": "https://doi.org/10.1000/existing-paper",
            },
        )

        bib_path = self.kernel_root / "imports" / "demo-import.bib"
        bib_path.parent.mkdir(parents=True, exist_ok=True)
        bib_path.write_text(
            "\n".join(
                [
                    "@article{existing-paper,",
                    "  title = {Existing paper},",
                    "  author = {Ada Lovelace},",
                    "  year = {1936},",
                    "  doi = {10.1000/existing-paper}",
                    "}",
                    "",
                    "@article{new-paper,",
                    "  title = {New imported paper},",
                    "  author = {Chen Ning Yang and Emmy Noether},",
                    "  year = {1942},",
                    "  doi = {10.1000/new-imported-paper},",
                    "  url = {https://doi.org/10.1000/new-imported-paper},",
                    "  abstract = {Imported from BibTeX.}",
                    "}",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        result = import_bibtex_sources(
            self.kernel_root,
            topic_slug="demo-topic",
            bibtex_path=str(bib_path),
            updated_by="unit-test",
        )

        payload = result["payload"]
        self.assertTrue(Path(result["json_path"]).exists())
        self.assertTrue(Path(result["markdown_path"]).exists())
        self.assertTrue(Path(result["source_index_path"]).exists())
        self.assertEqual(payload["summary"]["total_entry_count"], 2)
        self.assertEqual(payload["summary"]["imported_entry_count"], 1)
        self.assertEqual(payload["summary"]["duplicate_entry_count"], 1)

        rows = [
            json.loads(line)
            for line in Path(result["source_index_path"]).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        imported = next(row for row in rows if row["source_id"] == "bibtex:new-paper")
        self.assertEqual(imported["canonical_source_id"], "source_identity:doi:10-1000-new-imported-paper")
        self.assertEqual(imported["provenance"]["bibtex_citekey"], "new-paper")
        self.assertEqual(imported["provenance"]["doi"], "10.1000/new-imported-paper")


if __name__ == "__main__":
    unittest.main()
